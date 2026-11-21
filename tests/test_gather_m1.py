import json
import unittest
from pathlib import Path

from helpers import ROOT, Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


class GatherM1(unittest.TestCase):
    def setUp(self):
        contract = json.loads((Path(ROOT) / "game.contract.json").read_text(encoding="utf-8"))
        self.tuning = contract["tuning"]["gather"]
        self.tick_hz = contract["tuning"]["tick_hz"]
        self.surface_depth = self.tuning["surface_depth"]
        self.choke_interval = self.tuning["choke_interval_ticks"]

    def run_gather(self, workdir, ticks, scenario, *inputs, inventory_out=None):
        scenario_path = write_json(workdir.path("scenario.json"), {"gather": scenario})
        out = workdir.path("out.jsonl")
        args = ["--mode", "gather", "--seed", "1", "--ticks", str(ticks), "--out", out,
                "--scenario", scenario_path, "--snapshot-every", "1"]
        if inputs:
            args.extend(["--inputs", write_json(workdir.path("inputs.json"), frames(*inputs))])
        if inventory_out:
            args.extend(["--inventory-out", inventory_out])
        code, stderr = run_headless(*args)
        self.assertEqual(code, 0, stderr)
        return read_jsonl(out)

    def test_water_crossings_use_position_after_movement(self):
        ramp = max(1, self.tuning["ramp_max_ticks"])
        dive_ticks = ramp + 1
        with Workdir() as workdir:
            rows = self.run_gather(
                workdir, dive_ticks + 2 * ramp + 2,
                {"player": {"pos": [2, self.surface_depth], "oxygen_ticks": dive_ticks}},
                {"tick": 0, "move": [0, 1]},
                {"tick": dive_ticks, "move": [0, -1]},
            )
        players = [row["player"] for row in snapshots(rows)]
        crossings = [row for row in events(rows) if row["name"] in ("dive", "surface")]
        self.assertEqual([row["name"] for row in crossings], ["dive", "surface"])
        self.assertEqual(crossings[0]["tick"], 1)
        self.assertTrue(players[0]["at_surface"])
        self.assertFalse(players[1]["at_surface"])
        self.assertEqual(players[1]["oxygen_ticks"], dive_ticks - 1)
        for row in crossings:
            self.assertEqual(row["data"], {"pos": players[row["tick"]]["pos"]})
        surface_tick = crossings[1]["tick"]
        self.assertTrue(players[surface_tick]["at_surface"])
        self.assertEqual(players[surface_tick]["oxygen_ticks"], self.tuning["oxygen_refill_per_tick"])

    def test_choking_counts_first_empty_tick_and_repeats(self):
        with Workdir() as workdir:
            rows = self.run_gather(
                workdir, 2 * self.choke_interval,
                {"player": {"pos": [2, self.surface_depth + 1], "oxygen_ticks": 1}},
            )
        players = [row["player"] for row in snapshots(rows)]
        hp = self.tuning["hp_max"]
        self.assertEqual(
            [(row["tick"], row["name"], row["data"]) for row in events(rows)],
            [(1, "oxygen_empty", {"oxygen_ticks": 0}),
             (self.choke_interval, "choke", {"hp": hp - 1}),
             (2 * self.choke_interval, "choke", {"hp": hp - 2})],
        )
        self.assertEqual(players[1]["zero_oxy_ticks"], 1)
        self.assertEqual(players[self.choke_interval - 1]["hp"], hp)
        self.assertEqual(players[self.choke_interval]["zero_oxy_ticks"], 0)
        self.assertEqual(players[-1]["oxygen_ticks"], 0)

    def test_surfacing_on_choke_tick_resets_counter_and_caps_refill(self):
        speed = self.tuning["swim_speed"]
        depth = self.surface_depth + speed / (2 * self.tick_hz)
        refill = self.tuning["oxygen_refill_per_tick"]
        oxygen_max = round(self.tuning["oxygen_max_s"] * self.tick_hz)
        with Workdir() as workdir:
            rows = self.run_gather(
                workdir, oxygen_max // refill + 2,
                {"player": {"pos": [2, depth], "vel": [0, -speed], "oxygen_ticks": 0,
                            "zero_oxy_ticks": self.choke_interval - 1}},
                {"tick": 0, "move": [0, -1]},
            )
        self.assertEqual([(row["tick"], row["name"]) for row in events(rows)], [(1, "surface")])
        players = [row["player"] for row in snapshots(rows)]
        self.assertEqual(players[1]["zero_oxy_ticks"], 0)
        self.assertEqual(players[1]["oxygen_ticks"], refill)
        self.assertEqual(players[-1]["oxygen_ticks"], oxygen_max)
        self.assertEqual(players[-1]["hp"], self.tuning["hp_max"])

    @unittest.skip("Contract v1.2 breaking change: counting-stock fixture replaced by v1.2 tests (see CHANGELOG.md)")
    def test_faint_empties_inventory_before_docking_or_timeout(self):
        hold = ["ca_loc", "bong_sung", "ca_linh"]
        with Workdir() as workdir:
            inventory_path = workdir.path("inventory.json")
            rows = self.run_gather(
                workdir, 1,
                {"player": {"pos": [self.tuning["dock_pos"][0], self.surface_depth + 0.1],
                            "oxygen_ticks": 0, "zero_oxy_ticks": self.choke_interval - 1, "hp": 1},
                 "hold": hold, "time_left_ticks": 1},
                {"tick": 0, "interact": True, "catch": True},
                inventory_out=inventory_path,
            )
            inventory = json.loads(Path(inventory_path).read_text(encoding="utf-8"))
        self.assertEqual(
            [(row["tick"], row["name"], row["data"]) for row in events(rows)],
            [(1, "choke", {"hp": 0}),
             (1, "faint", {"cause": "choke", "lost": list(reversed(hold)), "hp": 0}),
             (1, "gather_end", {"reason": "fainted", "inventory": {"items": {}}})],
        )
        self.assertEqual(inventory, {"items": {}})
        final = snapshots(rows)[-1]
        self.assertEqual(final["hold"], [])
        self.assertEqual(final["hold_count"], 0)
        self.assertEqual(final["player"]["hp"], 0)
        self.assertEqual(rows[-1]["reason"], "fainted")
