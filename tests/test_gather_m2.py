import json
import unittest
from pathlib import Path

from helpers import ROOT, Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


class GatherM2(unittest.TestCase):
    def setUp(self):
        contract = json.loads((Path(ROOT) / "game.contract.json").read_text(encoding="utf-8"))
        self.tuning = contract["tuning"]["gather"]
        self.tick_hz = contract["tuning"]["tick_hz"]
        self.surface_depth = self.tuning["surface_depth"]

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

    @unittest.skip("Contract v1.2 breaking change: counting-stock fixture replaced by v1.2 tests (see CHANGELOG.md)")
    def test_ac_m2_01_gather_surface_node_success(self):
        """AC-M2-01: Hái nút mặt nước thành công."""
        with Workdir() as workdir:
            rows = self.run_gather(
                workdir, 2,
                {
                    "player": {"pos": [12, 0]},
                    "nodes": [{"id": "N1", "kind": "bong_dien_dien", "pos": [12, 0], "regrow_ticks": 0}],
                    "fish": [],
                    "hold": [],
                },
                {"tick": 0, "interact": True},
            )
        snaps = snapshots(rows)
        evs = events(rows, "gather")
        self.assertEqual(len(evs), 1)
        self.assertEqual(evs[0]["tick"], 1)
        self.assertEqual(evs[0]["data"], {"node_id": "N1", "kind": "bong_dien_dien", "amount": 1})
        self.assertEqual(snaps[1]["hold"], ["bong_dien_dien"])
        self.assertEqual(snaps[1]["hold_count"], 1)
        self.assertFalse(snaps[1]["nodes"][0]["ready"])
        # Tick 1: regrow_ticks = 1200. Tick 2: regrow_ticks = 1199.
        self.assertEqual(snaps[1]["nodes"][0]["regrow_ticks"], 1200)
        self.assertEqual(snaps[2]["nodes"][0]["regrow_ticks"], 1199)

    def test_ac_m2_02_node_regrown_event(self):
        """AC-M2-02: Nút mọc lại phát event node_regrown."""
        with Workdir() as workdir:
            rows = self.run_gather(
                workdir, 3,
                {
                    "player": {"pos": [20, 0]},
                    "nodes": [{"id": "N1", "kind": "bong_dien_dien", "pos": [12, 0], "regrow_ticks": 2}],
                    "fish": [],
                },
            )
        evs = events(rows, "node_regrown")
        self.assertEqual(len(evs), 1)
        self.assertEqual(evs[0]["tick"], 2)
        self.assertEqual(evs[0]["data"], {"node_id": "N1"})
        snaps = snapshots(rows)
        self.assertTrue(snaps[2]["nodes"][0]["ready"])
        self.assertEqual(snaps[2]["nodes"][0]["regrow_ticks"], 0)

    @unittest.skip("Contract v1.2 breaking change: counting-stock fixture replaced by v1.2 tests (see CHANGELOG.md)")
    def test_ac_m2_03_hold_full_on_gather(self):
        """AC-M2-03: Giỏ đầy khi hái phát event hold_full."""
        cap = self.tuning["hold_capacity"]
        with Workdir() as workdir:
            rows = self.run_gather(
                workdir, 1,
                {
                    "player": {"pos": [12, 0]},
                    "nodes": [{"id": "N1", "kind": "bong_dien_dien", "pos": [12, 0], "regrow_ticks": 0}],
                    "fish": [],
                    "hold": ["ca_loc"] * cap,
                },
                {"tick": 0, "interact": True},
            )
        evs = events(rows, "hold_full")
        self.assertEqual(len(evs), 1)
        self.assertEqual(evs[0]["data"], {"action": "gather", "node_id": "N1", "required": 1, "free": 0})
        self.assertEqual(events(rows, "gather"), [])
        snaps = snapshots(rows)
        self.assertEqual(len(snaps[1]["hold"]), cap)
        self.assertTrue(snaps[1]["nodes"][0]["ready"])

    @unittest.skip("Contract v1.2 breaking change: counting-stock fixture replaced by v1.2 tests (see CHANGELOG.md)")
    def test_ac_m2_04_dock_priority_over_gather(self):
        """AC-M2-04: Ưu tiên cập bến trước hái khi trong dock."""
        with Workdir() as workdir:
            rows = self.run_gather(
                workdir, 2,
                {
                    "player": {"pos": [2, 0]},
                    "nodes": [{"id": "N1", "kind": "bong_dien_dien", "pos": [2.5, 0], "regrow_ticks": 0}],
                    "fish": [],
                    "hold": ["ca_loc"],
                },
                {"tick": 0, "interact": True},
            )
        end_evs = events(rows, "gather_end")
        self.assertEqual(len(end_evs), 1)
        self.assertEqual(end_evs[0]["data"]["reason"], "docked")
        self.assertEqual(events(rows, "gather"), [])

    def test_ac_m2_05_underwater_cannot_gather_surface_nodes(self):
        """AC-M2-05: Ở dưới nước không hái được nút mặt nước."""
        with Workdir() as workdir:
            rows = self.run_gather(
                workdir, 1,
                {
                    "player": {"pos": [12, 2.0]},  # dưới nước
                    "nodes": [{"id": "N1", "kind": "bong_dien_dien", "pos": [12, 0], "regrow_ticks": 0}],
                    "fish": [],
                    "hold": [],
                },
                {"tick": 0, "interact": True},
            )
        self.assertEqual(events(rows, "gather"), [])
        self.assertEqual(events(rows, "hold_full"), [])

    @unittest.skip("Contract v1.2 breaking change: counting-stock fixture replaced by v1.2 tests (see CHANGELOG.md)")
    def test_ac_m2_06_catch_fish_success(self):
        """AC-M2-06: Bắt đàn cá dưới nước thành công."""
        with Workdir() as workdir:
            rows = self.run_gather(
                workdir, 2,
                {
                    "player": {"pos": [15, 5]},
                    "nodes": [],
                    "fish": [{"id": "F1", "kind": "ca_linh", "pos": [15, 5], "heading_deg": 0}],
                    "hold": [],
                },
                {"tick": 0, "catch": True},
            )
        evs = events(rows, "fish_caught")
        self.assertEqual(len(evs), 1)
        self.assertEqual(evs[0]["tick"], 1)
        self.assertEqual(evs[0]["data"], {"fish_id": "F1", "kind": "ca_linh", "yield": 3})
        snaps = snapshots(rows)
        self.assertEqual(snaps[1]["hold"], ["ca_linh", "ca_linh", "ca_linh"])
        self.assertEqual(snaps[1]["fish"], [])
        self.assertEqual(snaps[1]["player"]["catch_cd_ticks"], 30)
        self.assertEqual(snaps[2]["player"]["catch_cd_ticks"], 29)

    @unittest.skip("Contract v1.2 breaking change: counting-stock fixture replaced by v1.2 tests (see CHANGELOG.md)")
    def test_ac_m2_07_hold_full_on_catch(self):
        """AC-M2-07: Bắt cá thiếu chỗ phát event hold_full, giữ đàn cá, không hồi chiêu."""
        with Workdir() as workdir:
            rows = self.run_gather(
                workdir, 1,
                {
                    "player": {"pos": [15, 5]},
                    "nodes": [],
                    "fish": [{"id": "F1", "kind": "ca_linh", "pos": [15, 5], "heading_deg": 0}],
                    "hold": ["ca_loc"] * 10,  # còn trống 2, ca_linh cần 3
                },
                {"tick": 0, "catch": True},
            )
        evs = events(rows, "hold_full")
        self.assertEqual(len(evs), 1)
        self.assertEqual(evs[0]["data"], {"action": "catch", "fish_id": "F1", "required": 3, "free": 2})
        self.assertEqual(events(rows, "fish_caught"), [])
        snaps = snapshots(rows)
        self.assertEqual(len(snaps[1]["fish"]), 1)
        self.assertEqual(snaps[1]["player"]["catch_cd_ticks"], 0)

    def test_ac_m2_08_surface_or_cd_cannot_catch(self):
        """AC-M2-08: Ở mặt nước hoặc đang cooldown thì không bắt cá."""
        with Workdir() as workdir:
            # Ở mặt nước: pos[1] = 0.4 <= surface_depth
            rows_surface = self.run_gather(
                workdir, 1,
                {
                    "player": {"pos": [15, 0.4]},
                    "nodes": [],
                    "fish": [{"id": "F1", "kind": "ca_loc", "pos": [15, 1.0], "heading_deg": 0}],
                },
                {"tick": 0, "catch": True},
            )
            # Dưới nước nhưng đang cooldown
            rows_cd = self.run_gather(
                workdir, 1,
                {
                    "player": {"pos": [15, 5], "catch_cd_ticks": 10},
                    "nodes": [],
                    "fish": [{"id": "F1", "kind": "ca_loc", "pos": [15, 5], "heading_deg": 0}],
                },
                {"tick": 0, "catch": True},
            )
        self.assertEqual(events(rows_surface, "fish_caught"), [])
        self.assertEqual(events(rows_cd, "fish_caught"), [])

    def test_ac_m2_09_tie_break_smallest_id(self):
        """AC-M2-09: Khi bằng khoảng cách, chọn ID nhỏ nhất."""
        with Workdir() as workdir:
            # Hai nút N1 và N2 cùng khoảng cách 1.0 đến player
            rows = self.run_gather(
                workdir, 1,
                {
                    "player": {"pos": [30, 0]},
                    "nodes": [
                        {"id": "N2", "kind": "bong_dien_dien", "pos": [31, 0], "regrow_ticks": 0},
                        {"id": "N1", "kind": "bong_sung", "pos": [29, 0], "regrow_ticks": 0},
                    ],
                    "fish": [],
                },
                {"tick": 0, "interact": True},
            )
        evs = events(rows, "gather")
        self.assertEqual(len(evs), 1)
        self.assertEqual(evs[0]["data"]["node_id"], "N1")

    @unittest.skip("Contract v1.2 breaking change: counting-stock fixture replaced by v1.2 tests (see CHANGELOG.md)")
    def test_ac_m2_10_inventory_output_file(self):
        """AC-M2-10: Ghi file kho đúng format, sắp xếp key, bỏ count 0."""
        with Workdir() as workdir:
            inv_path = workdir.path("out_kho.json")
            self.run_gather(
                workdir, 1,
                {
                    "player": {"pos": [2, 0]},
                    "hold": ["ca_loc", "ca_linh", "bong_sung", "ca_linh"],
                    "nodes": [],
                    "fish": [],
                },
                {"tick": 0, "interact": True},  # dock
                inventory_out=inv_path,
            )
            data = json.loads(Path(inv_path).read_text(encoding="utf-8"))
        self.assertEqual(data, {
            "items": {
                "bong_sung": 1,
                "ca_linh": 2,
                "ca_loc": 1,
            }
        })
