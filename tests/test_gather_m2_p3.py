"""Unit tests cho Module M2 Phase 3 (Test Contract v1.2 — Giỏ cá thể, Cấp ID, Hao độ tươi).

10 tiêu chí kiểm thử (AC-P3-M2-01 đến AC-P3-M2-10):
1. Cấp ID I1, I2... tăng dần khi hái hoặc bắt cá.
2. Chuỗi ID I1, I2... tăng liên tục xuyên ca/Ngày, không reset về 1.
3. Hàng mới hái/bắt có đúng fresh = 100.0 ở tick thu hoạch.
4. Tốc độ hao tươi giỏ đúng 0.5 điểm/giây (sau 60 tick giảm từ 100.0 xuống 99.50).
5. Độ tươi rơi xuống < 30.0 bắn event spoiled (location: 'hold') đúng 1 lần.
6. Nhiều cá thể cùng ươn thì bắn event spoiled theo thứ tự ID tăng dần.
7. Hàng ươn (fresh < 30) vẫn chiếm 1 ô giỏ, giỏ đủ 12 cá thể ươn sẽ bắn hold_full khi hái.
8. Bắt cá có yield > 1 (ca_keo yield 2) sinh đủ các cá thể riêng biệt kèm ID riêng.
9. Ngất do ngạt làm rỗng giỏ và xuất file kho rỗng {"items": []}.
10. Cập bến xuất file kho mảng cá thể đúng schema Contract v1.2.
"""

import copy
import json
import unittest

from chonoi.contract import load_contract
from chonoi.freshness import FRESH_SCALE, from_units, to_units
from chonoi.headless import main
from chonoi.ids import IdAllocator
from chonoi.inventory import read_inventory
from chonoi.rng import Streams
from chonoi.sim.gather import GatherSim
from unittest.mock import patch
from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


class FakeInput:
    def __init__(self, move=(0.0, 0.0), interact=False, catch=False):
        self.move = move
        self._interact = interact
        self._catch = catch

    def pressed(self, action):
        if action == "interact":
            return self._interact
        if action == "catch":
            return self._catch
        return False


class GatherM2Phase3(unittest.TestCase):
    def setUp(self):
        self.contract = copy.deepcopy(load_contract())
        self.contract["contract_version"] = "1.2"
        self.tuning = self.contract["tuning"]
        self.tuning["contract_version"] = "1.2"
        self.gather = self.tuning["gather"]

    def _make_sim(self, scenario, ids=None):
        streams = Streams(1)
        if ids is None:
            ids = IdAllocator()
        return GatherSim(self.tuning, scenario, streams, ids)

    def test_ac_p3_m2_01_id_allocation_on_gather_and_catch(self):
        """AC-P3-M2-01: Cấp ID cá thể I1, I2... tăng dần khi hái nút mặt nước hoặc bắt cá."""
        node = self.gather["nodes"][0]
        fish = {"id": "F1", "kind": "ca_linh", "pos": [10.0, 5.0], "heading_deg": 0.0, "age_ticks": 0}
        sc = {
            "player": {"pos": [node["pos"][0], 0.0]},
            "nodes": [node],
            "fish": [fish],
            "random_fish": False,
            "monsters": [],
        }
        ids = IdAllocator()
        sim = self._make_sim(sc, ids)

        # 1. Hái nút mặt nước
        evs = sim.step(FakeInput(interact=True))
        self.assertTrue(any(e[0] == "gather" for e in evs))
        self.assertEqual(len(sim.hold), 1)
        self.assertEqual(sim.hold[0]["id"], "I1")
        self.assertEqual(sim.hold[0]["kind"], node["kind"])

        # 2. Bơi xuống gần cá và bắt cá
        sim.pos = [10.0, 5.0]
        evs = sim.step(FakeInput(catch=True))
        self.assertTrue(any(e[0] == "fish_caught" for e in evs))
        # ca_linh có yield = 3 -> tổng cộng giỏ có 1 + 3 = 4 con, id I1, I2, I3, I4
        self.assertEqual(len(sim.hold), 4)
        ids_in_hold = [it["id"] for it in sim.hold]
        self.assertEqual(ids_in_hold, ["I1", "I2", "I3", "I4"])

    def test_ac_p3_m2_02_id_sequence_persistent_across_phases_days(self):
        """AC-P3-M2-02: Chuỗi ID I1, I2... tăng liên tục xuyên ca/Ngày, không reset về 1."""
        ids = IdAllocator()
        node = self.gather["nodes"][0]
        sc1 = {"player": {"pos": node["pos"]}, "nodes": [node], "random_fish": False, "monsters": []}

        # Ca 1: hái 1 lần -> cấp I1
        sim1 = self._make_sim(sc1, ids)
        sim1.step(FakeInput(interact=True))
        self.assertEqual(sim1.hold[0]["id"], "I1")

        # Ca 2 (ngày kế tiếp dùng chung id allocator): hái tiếp -> cấp I2
        sim2 = self._make_sim(sc1, ids)
        sim2.step(FakeInput(interact=True))
        self.assertEqual(sim2.hold[0]["id"], "I2")

    def test_ac_p3_m2_03_freshness_starts_at_100(self):
        """AC-P3-M2-03: Hàng mới hái/bắt có đúng fresh = 100.0 ở tick thu hoạch."""
        node = self.gather["nodes"][0]
        sc = {"player": {"pos": node["pos"]}, "nodes": [node], "random_fish": False, "monsters": []}
        sim = self._make_sim(sc)

        # Hái ở tick này
        sim.step(FakeInput(interact=True))
        self.assertEqual(len(sim.hold), 1)
        # Tại tick vừa hái, units phải là 24000 (đúng 100.0)
        self.assertEqual(sim.hold[0]["units"], 24000)
        snap = sim.snapshot()
        self.assertEqual(snap["hold"][0]["fresh"], 100.0)

    def test_ac_p3_m2_04_decay_rate_half_point_per_second(self):
        """AC-P3-M2-04: Tốc độ hao tươi giỏ đúng 0.5 điểm/giây (sau 60 tick giảm từ 100.0 xuống 99.5)."""
        node = self.gather["nodes"][0]
        sc = {"player": {"pos": node["pos"]}, "nodes": [node], "random_fish": False, "monsters": []}
        sim = self._make_sim(sc)
        sim.step(FakeInput(interact=True))  # Hái ở tick 1

        # Chạy thêm 60 tick (1 giây ở 60 Hz)
        for _ in range(60):
            sim.step(FakeInput())

        # Mỗi tick giảm 2 đơn vị, sau 60 tick giảm 120 đơn vị = 0.5 điểm tươi
        expected_units = 24000 - 120
        self.assertEqual(sim.hold[0]["units"], expected_units)
        self.assertAlmostEqual(from_units(sim.hold[0]["units"]), 99.5, places=2)

    def test_ac_p3_m2_05_spoiled_event_at_threshold_30(self):
        """AC-P3-M2-05: Độ tươi rơi xuống < 30.0 bắn event spoiled (location: 'hold') đúng 1 lần."""
        # 30.0 điểm = 7200 đơn vị. Ngay tick sau sẽ còn 7198 (< 7200) -> ươn
        sc = {
            "hold": [{"id": "I1", "kind": "ca_linh", "fresh": 30.0}],
            "random_fish": False,
            "monsters": [],
        }
        sim = self._make_sim(sc)

        # Tick 1: từ 7200 giảm xuống 7198 -> phát event spoiled
        evs1 = sim.step(FakeInput())
        spoiled1 = [e for e in evs1 if e[0] == "spoiled"]
        self.assertEqual(len(spoiled1), 1)
        name, payload = spoiled1[0]
        self.assertEqual(payload["item_id"], "I1")
        self.assertEqual(payload["kind"], "ca_linh")
        self.assertEqual(payload["location"], "hold")

        # Tick 2: tiếp tục giảm xuống 7196 nhưng đã ươn từ trước -> KHÔNG bắn lại
        evs2 = sim.step(FakeInput())
        spoiled2 = [e for e in evs2 if e[0] == "spoiled"]
        self.assertEqual(len(spoiled2), 0)

    def test_ac_p3_m2_06_multiple_spoiled_ordered_by_id(self):
        """AC-P3-M2-06: Nhiều cá thể cùng ươn thì bắn event spoiled theo thứ tự ID tăng dần."""
        sc = {
            "hold": [
                {"id": "I10", "kind": "ca_linh", "fresh": 30.0},
                {"id": "I2", "kind": "ca_loc", "fresh": 30.0},
                {"id": "I1", "kind": "ca_keo", "fresh": 30.0},
            ],
            "random_fish": False,
            "monsters": [],
        }
        sim = self._make_sim(sc)

        evs = sim.step(FakeInput())
        spoiled_ids = [e[1]["item_id"] for e in evs if e[0] == "spoiled"]
        # Thứ tự phải sắp theo id tăng dần: I1, I2, I10
        self.assertEqual(spoiled_ids, ["I1", "I2", "I10"])

    def test_ac_p3_m2_07_spoiled_items_occupy_hold_capacity(self):
        """AC-P3-M2-07: Hàng ươn (fresh < 30) vẫn chiếm 1 ô giỏ, giỏ đủ 12 cá thể ươn sẽ bắn hold_full khi hái."""
        spoiled_hold = [{"id": f"I{i}", "kind": "ca_linh", "fresh": 10.0} for i in range(1, 13)]
        node = self.gather["nodes"][0]
        sc = {
            "player": {"pos": node["pos"]},
            "hold": spoiled_hold,
            "nodes": [node],
            "random_fish": False,
            "monsters": [],
        }
        sim = self._make_sim(sc)
        self.assertEqual(len(sim.hold), 12)

        evs = sim.step(FakeInput(interact=True))
        self.assertTrue(any(e[0] == "hold_full" for e in evs))
        self.assertEqual(len(sim.hold), 12)  # Không thêm được

    def test_ac_p3_m2_08_multi_yield_creates_distinct_items(self):
        """AC-P3-M2-08: Bắt cá có yield > 1 (ca_keo yield 2) sinh đủ các cá thể riêng biệt kèm ID riêng."""
        fish = {"id": "F1", "kind": "ca_keo", "pos": [10.0, 25.0], "heading_deg": 0.0, "age_ticks": 0}
        sc = {
            "player": {"pos": [10.0, 25.0]},
            "fish": [fish],
            "random_fish": False,
            "monsters": [],
        }
        sim = self._make_sim(sc)
        evs = sim.step(FakeInput(catch=True))
        self.assertTrue(any(e[0] == "fish_caught" for e in evs))
        self.assertEqual(len(sim.hold), 2)
        # 2 cá thể riêng biệt: I1, I2
        self.assertEqual(sim.hold[0]["id"], "I1")
        self.assertEqual(sim.hold[1]["id"], "I2")
        self.assertEqual(sim.hold[0]["kind"], "ca_keo")
        self.assertEqual(sim.hold[1]["kind"], "ca_keo")

    def test_ac_p3_m2_09_faint_empties_hold_and_writes_empty_inventory(self):
        """AC-P3-M2-09: Ngất do ngạt làm rỗng giỏ và xuất file kho rỗng {"items": []}."""
        sc = {
            "player": {
                "pos": [10.0, 10.0],
                "oxygen_ticks": 0,
                "zero_oxy_ticks": self.gather["choke_interval_ticks"] - 1,
                "hp": 1,
            },
            "hold": [{"id": "I1", "kind": "ca_linh", "fresh": 80.0}],
            "random_fish": False,
            "monsters": [],
        }
        sim = self._make_sim(sc)
        evs = sim.step(FakeInput())
        self.assertTrue(sim.done)
        self.assertEqual(sim.reason, "fainted")
        # Giỏ đã bị làm rỗng
        self.assertEqual(sim.hold, [])
        end_ev = [e for e in evs if e[0] == "gather_end"][0]
        self.assertEqual(end_ev[1]["inventory"], {"items": []})

    def test_ac_p3_m2_10_dock_writes_individual_items_inventory(self):
        """AC-P3-M2-10: Cập bến xuất file kho mảng cá thể đúng schema Contract v1.2."""
        with Workdir() as workdir:
            inv_out = workdir.path("kho_p3.json")
            sc_path = workdir.path("sc.json")
            out_path = workdir.path("out.jsonl")

            write_json(sc_path, {
                "gather": {
                    "player": {"pos": [2.0, 0.0]},  # trong bến
                    "hold": [
                        {"id": "I2", "kind": "ca_loc", "fresh": 85.0},
                        {"id": "I1", "kind": "ca_linh", "fresh": 95.0},
                    ],
                    "random_fish": False,
                    "monsters": [],
                }
            })
            inp_path = workdir.path("inps.json")
            write_json(inp_path, frames({"tick": 0, "interact": True}))

            args = [
                "--mode", "gather",
                "--seed", "1",
                "--ticks", "1",
                "--scenario", sc_path,
                "--inputs", inp_path,
                "--out", out_path,
                "--inventory-out", inv_out,
            ]
            with patch("chonoi.headless.load_contract", return_value=self.contract):
                ret = main(args)
            self.assertEqual(ret, 0)

            # Đọc lại bằng read_inventory với contract_version="1.2"
            items = read_inventory(inv_out, contract_version="1.2")
            self.assertEqual(len(items), 2)
            # Sắp theo id: I1 trước, I2 sau
            self.assertEqual(items[0]["id"], "I1")
            self.assertEqual(items[0]["kind"], "ca_linh")
            self.assertAlmostEqual(items[0]["fresh"], 95.0, delta=0.1)
            self.assertEqual(items[1]["id"], "I2")
            self.assertEqual(items[1]["kind"], "ca_loc")
            self.assertAlmostEqual(items[1]["fresh"], 85.0, delta=0.1)


if __name__ == "__main__":
    unittest.main()
