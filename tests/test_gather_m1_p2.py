import json
import unittest
from pathlib import Path

from helpers import ROOT, Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


class GatherMonstersPhase2(unittest.TestCase):
    def setUp(self):
        tuning = json.loads((Path(ROOT) / "game.contract.json").read_text(encoding="utf-8"))["tuning"]
        self.gather = tuning["gather"]
        self.monsters = self.gather["monsters"]
        self.species = self.monsters["species"]["ca_sau"]
        self.tick_hz = tuning["tick_hz"]
        self.shop_ticks = tuning["shop"]["max_ticks"]
        self.pos = self.monsters["spawns"][0]["pos"]

    def monster(self, ident, pos):
        x, depth = pos
        return {"id": ident, "kind": "ca_sau", "pos": pos, "waypoints": [pos, [x + 4, depth]]}

    def simulate(self, workdir, ticks, gather, *args, inputs=(), days=None):
        mode = "day" if days else "gather"
        scenario = {"gather": {"random_fish": False, **gather}}
        command = ["--mode", mode, "--seed", "1", "--ticks", str(ticks), "--snapshot-every", "1"]
        if days:
            scenario["quan"] = {"random_customers": False, "time_left_ticks": 1}
            command.extend(["--days", str(days)])
        if inputs:
            command.extend(["--inputs", write_json(workdir.path("inputs.json"), frames(*inputs))])
        out = workdir.path("out.jsonl")
        command.extend(["--scenario", write_json(workdir.path("scenario.json"), scenario), "--out", out])
        code, stderr = run_headless(*command, *args)
        self.assertEqual(code, 0, stderr)
        return read_jsonl(out)

    def test_default_population_is_selected_by_day(self):
        with Workdir() as workdir:
            default_rows = self.simulate(workdir, 0, {})
            override_rows = self.simulate(workdir, 0, {"monsters": []})
            day_rows = self.simulate(workdir, 2 * (self.shop_ticks + 2), {"time_left_ticks": 1}, days=3)
        self.assertEqual([m["id"] for m in snapshots(default_rows)[0]["monsters"]], ["M1"])
        self.assertEqual(snapshots(override_rows)[0]["monsters"], [])
        first_gather_snapshots = [row for row in snapshots(day_rows)
                                  if row["phase"] == "gather" and row["phase_tick"] == 0]
        self.assertEqual(
            [(row["day"], [m["id"] for m in row["monsters"]]) for row in first_gather_snapshots],
            [(1, ["M1"]), (2, ["M1"]), (3, ["M1", "M2"])],
        )

    def test_patrol_switches_waypoint_after_arriving(self):
        monster = {**self.monster("M1", self.pos), "target_idx": 0}
        with Workdir() as workdir:
            rows = self.simulate(workdir, 2, {"monsters": [monster]})
        _, arrival, next_step = [row["monsters"][0] for row in snapshots(rows)]
        self.assertEqual((arrival["state"], arrival["pos"], arrival["target_idx"]), ("patrol", self.pos, 1))
        self.assertAlmostEqual(next_step["pos"][0], self.pos[0] + self.species["patrol_speed"] / self.tick_hz,
                               delta=0.001)

    def test_chase_at_detection_boundary_and_exit_in_shallow_water(self):
        x = self.pos[0]
        depth = self.species["depths"][0]
        with Workdir() as workdir:
            rows = self.simulate(
                workdir, 2, {"player": {"pos": [x + self.species["detect_radius"], depth]},
                             "monsters": [self.monster("M1", [x, depth])]},
                inputs=({"tick": 1, "move": [0, -1]},),
            )
        monsters = [row["monsters"][0] for row in snapshots(rows)]
        self.assertEqual([monster["state"] for monster in monsters], ["patrol", "chase", "patrol"])
        self.assertAlmostEqual(monsters[1]["pos"][0], x + self.species["chase_speed"] / self.tick_hz,
                               delta=0.001)
        self.assertTrue(all(monster["pos"][1] >= depth for monster in monsters))

    @unittest.skip("Contract v1.2 breaking change: counting-stock fixture replaced by v1.2 tests (see CHANGELOG.md)")
    def test_hit_tie_break_lifo_recoil_and_invulnerability(self):
        hold = ["ca_loc", "bong_sung", "ca_linh"]
        immunity = self.monsters["invuln_ticks"]
        recoil = self.species["recoil_ticks"]
        with Workdir() as workdir:
            rows = self.simulate(
                workdir, immunity + 1,
                {"player": {"pos": self.pos}, "hold": hold,
                 "monsters": [self.monster("M10", self.pos), self.monster("M2", self.pos)]},
            )
        hits = events(rows, "monster_hit")
        self.assertEqual([row["tick"] for row in hits], [1, 1 + immunity])
        self.assertEqual(hits[0]["data"], {"monster_id": "M2", "hp": self.gather["hp_max"] - 1,
                                          "lost": hold[-1:], "pos": self.pos})
        states = snapshots(rows)
        self.assertEqual(states[1]["hold"], hold[:-1])
        self.assertEqual(states[1]["player"]["invuln_ticks"], immunity)
        first, other = states[1]["monsters"]
        self.assertEqual((first["id"], first["state"], first["state_ticks_left"]), ("M2", "recoil", recoil))
        self.assertEqual(first["pos"], self.pos)
        self.assertEqual(other["state"], "chase")
        self.assertEqual(states[recoil]["monsters"][0]["state_ticks_left"], 1)
        last = states[recoil + 1]["monsters"][0]
        self.assertEqual((last["state"], last["state_ticks_left"]), ("patrol", 0))
        self.assertAlmostEqual(last["pos"][0], self.pos[0] + self.species["recoil_dist"], delta=0.001)

    @unittest.skip("Contract v1.2 breaking change: counting-stock fixture replaced by v1.2 tests (see CHANGELOG.md)")
    def test_lethal_hit_drops_remaining_hold_and_opens_quan(self):
        hold = ["ca_loc", "bong_sung", "ca_linh"]
        scenario = {"player": {"pos": self.pos, "hp": 1}, "hold": hold, "time_left_ticks": 1,
                    "monsters": [self.monster("M1", self.pos)]}
        with Workdir() as workdir:
            inventory = workdir.path("inventory.json")
            gather_rows = self.simulate(workdir, 1, scenario, "--inventory-out", inventory)
            day_rows = self.simulate(workdir, 1, scenario, days=1)
            written = json.loads(Path(inventory).read_text(encoding="utf-8"))
        event_rows = events(gather_rows)
        self.assertEqual([row["name"] for row in event_rows], ["monster_hit", "faint", "gather_end"])
        self.assertEqual(event_rows[1]["data"], {"cause": "monster", "lost": hold[-2::-1], "hp": 0})
        self.assertEqual(event_rows[2]["data"], {"reason": "fainted", "inventory": {"items": {}}})
        self.assertEqual(written, {"items": {}})
        self.assertEqual(gather_rows[-1]["reason"], "fainted")
        self.assertEqual(snapshots(gather_rows)[-1]["hold"], [])
        self.assertEqual(snapshots(day_rows)[-1]["phase"], "quan")
        self.assertEqual(snapshots(day_rows)[-1]["stock"], {})
