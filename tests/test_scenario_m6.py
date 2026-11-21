"""Unit & black-box tests cho M6.3: kiểm tra mâu thuẫn mức luật trong scenario quán (PRD-0 mục D)."""

import os
import unittest

from helpers import Workdir, run_headless, write_json


def _run_quan(w, quan_block, inventory=None):
    sc = write_json(w.path("sc.json"), {"quan": quan_block})
    out = w.path("out.jsonl")
    args = ["--mode", "quan", "--seed", "1", "--ticks", "0", "--scenario", sc, "--out", out]
    if inventory is not None:
        inv = write_json(w.path("inv.json"), {"items": inventory})
        args.extend(["--inventory", inv])
    code, err = run_headless(*args)
    return code, err, out


class ScenarioQuanValidationM6(unittest.TestCase):
    def test_valid_reserved_with_stock_and_inventory(self):
        with Workdir() as w:
            code, err, _ = _run_quan(w, {
                "stock": [{"id": "I1", "kind": "ca_loc", "fresh": 100}],
                "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}],
            })
            self.assertEqual(code, 0, err)
            code, err, _ = _run_quan(w, {
                "customers": [{
                    "id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung",
                    "order_status": "reserved", "reserved": ["I1", "I2"],
                }],
            }, inventory=[
                {"id": "I1", "kind": "bong_sung", "fresh": 100},
                {"id": "I2", "kind": "bong_sung", "fresh": 95},
            ])
            self.assertEqual(code, 0, err)

    def test_valid_assigned_cooking_ready_hand(self):
        dish = {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60}
        cust = {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_status": "assigned"}
        cases = [
            {"customers": [cust], "stoves": [{"id": "B1", "state": "cooking", "dish": dish, "cook_ticks_left": 10}]},
            {"customers": [cust], "stoves": [{"id": "B1", "state": "ready", "dish": dish, "ready_ticks": 5}]},
            {"customers": [cust], "hand": dish},
        ]
        for block in cases:
            with Workdir() as w:
                code, err, _ = _run_quan(w, block)
                self.assertEqual(code, 0, f"{block}: {err}")

    def test_valid_eating_and_unfulfillable(self):
        with Workdir() as w:
            code, err, _ = _run_quan(w, {
                "customers": [{
                    "id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                    "state": "eating", "order_status": "served", "eat_ticks_left": 120,
                    "base_price": 60, "tip": 12,
                }],
            })
            self.assertEqual(code, 0, err)
            code, err, _ = _run_quan(w, {
                "customers": [{
                    "id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                    "order_status": "unfulfillable",
                }],
            })
            self.assertEqual(code, 0, err)

    def test_reserved_mismatch_or_exceeds_stock_exit_2(self):
        cases = [
            # giữ khác công thức
            ({"stock": {"ca_loc": 2}, "customers": [{
                "id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                "reserved": {"ca_loc": 2},
            }]}, None),
            # giữ vượt stock
            ({"stock": {"bong_sung": 1}, "customers": [{
                "id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung",
            }]}, None),
            # giữ vượt --inventory
            ({"customers": [{
                "id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung",
            }]}, {"bong_sung": 1}),
            # không có kho (rỗng) nhưng có đơn reserved
            ({"customers": [{
                "id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
            }]}, None),
        ]
        for block, inv in cases:
            with Workdir() as w:
                code, _err, out = _run_quan(w, block, inventory=inv)
                self.assertEqual(code, 2, (block, inv))
                self.assertFalse(os.path.exists(out))

    def test_assigned_stove_hand_conflicts_exit_2(self):
        dish = {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60}
        wrong_dish = {"order_id": "C1", "dish_id": "goi_bong_sung", "base_price": 40}
        cust_assigned = {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui", "order_status": "assigned"}
        cases = [
            # assigned nhưng không có món ở bếp hoặc tay
            {"customers": [cust_assigned]},
            # assigned nhưng reserved không rỗng
            {"customers": [dict(cust_assigned, reserved={"ca_loc": 1})], "hand": dish},
            # bếp và tay cùng giữ cùng 1 đơn
            {"customers": [cust_assigned], "hand": dish,
             "stoves": [{"id": "B1", "state": "ready", "dish": dish}]},
            # món không khớp đơn
            {"customers": [cust_assigned], "hand": wrong_dish},
            # order_id không tồn tại (tham chiếu id không tạo thực thể)
            {"hand": dish},
            # bếp cooking nhưng cook_ticks_left == 0
            {"customers": [cust_assigned],
             "stoves": [{"id": "B1", "state": "cooking", "dish": dish, "cook_ticks_left": 0}]},
            # bếp idle nhưng có món
            {"customers": [cust_assigned],
             "stoves": [{"id": "B1", "state": "idle", "dish": dish}]},
            # đơn unfulfillable nhưng lại có món trên tay
            {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                            "order_status": "unfulfillable"}], "hand": dish},
        ]
        for block in cases:
            with Workdir() as w:
                code, _err, out = _run_quan(w, block)
                self.assertEqual(code, 2, block)
                self.assertFalse(os.path.exists(out))

    def test_eating_and_misc_conflicts_exit_2(self):
        cases = [
            # eating thiếu base_price / tip
            {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                            "state": "eating", "order_status": "served", "eat_ticks_left": 60}]},
            # eating nhưng order_status != served
            {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                            "state": "eating", "order_status": "assigned", "eat_ticks_left": 60,
                            "base_price": 60, "tip": 0}]},
            # eating nhưng eat_ticks_left == 0
            {"customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                            "state": "eating", "order_status": "served", "eat_ticks_left": 0,
                            "base_price": 60, "tip": 0}]},
            # reputation ngoài [0, 5]
            {"reputation": 5.5},
            # random_customers không phải bool
            {"random_customers": "no"},
            # id bếp không tồn tại
            {"stoves": [{"id": "B9", "state": "idle"}]},
        ]
        for block in cases:
            with Workdir() as w:
                code, _err, out = _run_quan(w, block)
                self.assertEqual(code, 2, block)
                self.assertFalse(os.path.exists(out))


if __name__ == "__main__":
    unittest.main()
