"""M3 — Quán: Khách. Test hộp đen qua headless (AC-P1-C1 … C8, xem docs/plan/phase-1.md).

Chạy: PYTHONPATH=tests:. python3 -m unittest tests.test_quan_customers_m3 -v
"""

import unittest

from helpers import Workdir, close, events, read_jsonl, run_headless, snapshots, write_json

CA_LOC = "ca_loc_nuong_trui"
PATIENCE = 60 * 60  # patience_s × 60


def run_quan(w, block, ticks, seed=1, name="o.jsonl"):
    sc = write_json(w.path("sc.json"), {"quan": block})
    code, err = run_headless("--mode", "quan", "--seed", str(seed), "--scenario", sc,
                             "--ticks", str(ticks), "--out", w.path(name), "--snapshot-every", "1")
    assert code == 0, err
    return read_jsonl(w.path(name))


def cust(**kw):
    base = {"id": "K1", "table_id": "T1", "dish_id": CA_LOC}
    base.update(kw)
    return base


def snap_at(rows, tick):
    return next(s for s in snapshots(rows) if s["tick"] == tick)


class DefaultsAndReservation(unittest.TestCase):
    @unittest.skip("Contract v1.2 breaking change: counting-stock fixture replaced by v1.2 tests (see CHANGELOG.md)")
    def test_c1_customer_defaults(self):  # AC-P1-C1
        with Workdir() as w:
            rows = run_quan(w, {"random_customers": False, "stock": {"ca_loc": 1},
                                "customers": [cust()]}, 0)
            c = snapshots(rows)[0]["customers"][0]
            self.assertEqual(c["state"], "waiting")
            self.assertEqual(c["order_tick"], 0)
            self.assertEqual(c["patience_ticks_left"], PATIENCE)
            self.assertEqual(c["eat_ticks_left"], 0)
            self.assertEqual(c["order_status"], "reserved")
            self.assertEqual(c["reserved"], {"ca_loc": 1})
            self.assertEqual(snapshots(rows)[0]["tables"][0]["customer_id"], "K1")

    @unittest.skip("Contract v1.2 breaking change: counting-stock fixture replaced by v1.2 tests (see CHANGELOG.md)")
    def test_c1_reserved_follows_recipe_for_each_dish(self):  # AC-P1-C1
        with Workdir() as w:
            rows = run_quan(w, {"random_customers": False, "stock": {"ca_linh": 3, "bong_dien_dien": 1},
                                "customers": [cust(dish_id="lau_ca_linh_dien_dien")]}, 0)
            self.assertEqual(snapshots(rows)[0]["customers"][0]["reserved"],
                             {"bong_dien_dien": 1, "ca_linh": 3})


class Patience(unittest.TestCase):
    @unittest.skip("Contract v1.2 breaking change: counting-stock fixture replaced by v1.2 tests (see CHANGELOG.md)")
    def test_c3_patience_counts_down(self):  # AC-P1-C3
        with Workdir() as w:
            rows = run_quan(w, {"random_customers": False, "stock": {"ca_loc": 1},
                                "customers": [cust(patience_ticks_left=10)]}, 4)
            self.assertEqual(snap_at(rows, 4)["customers"][0]["patience_ticks_left"], 6)

    @unittest.skip("Contract v1.2 breaking change: counting-stock fixture replaced by v1.2 tests (see CHANGELOG.md)")
    def test_c4_leaves_when_patience_runs_out(self):  # AC-P1-C4
        with Workdir() as w:
            rows = run_quan(w, {"random_customers": False, "stock": {"ca_loc": 1},
                                "customers": [cust(patience_ticks_left=3)]}, 10)
            left = events(rows, "customer_left")
            self.assertEqual(len(left), 1)
            self.assertEqual(left[0]["tick"], 3)
            self.assertEqual(left[0]["data"], {"order_id": "K1", "table_id": "T1",
                                               "reason": "patience", "reputation": 2.5})
            s = snap_at(rows, 3)
            self.assertEqual(s["customers"], [])
            self.assertIsNone(s["tables"][0]["customer_id"])
            self.assertTrue(close(s["reputation"], 2.5, 0.01))

    @unittest.skip("Contract v1.2 breaking change: counting-stock fixture replaced by v1.2 tests (see CHANGELOG.md)")
    def test_c4_reputation_clamped_at_min(self):  # AC-P1-C4
        with Workdir() as w:
            rows = run_quan(w, {"random_customers": False, "reputation": 0.2, "stock": {"ca_loc": 1},
                                "customers": [cust(patience_ticks_left=1)]}, 2)
            self.assertEqual(events(rows, "customer_left")[0]["data"]["reputation"], 0)

    @unittest.skip("Contract v1.2 breaking change: counting-stock fixture replaced by v1.2 tests (see CHANGELOG.md)")
    def test_c4_leaving_drops_dish_of_that_order(self):  # AC-P1-C4: bỏ món đang nấu của đơn
        with Workdir() as w:
            dish = {"order_id": "K1", "dish_id": CA_LOC, "base_price": 60}
            rows = run_quan(w, {"random_customers": False,
                                "stoves": [{"id": "B1", "state": "cooking", "dish": dish, "cook_ticks_left": 100}],
                                "customers": [cust(patience_ticks_left=1, order_status="assigned", reserved={})]}, 2)
            stove = snap_at(rows, 2)["stoves"][0]
            self.assertEqual(stove["state"], "idle")
            self.assertIsNone(stove["dish"])


class Arrivals(unittest.TestCase):
    @unittest.skip("Contract v1.2 breaking change: counting-stock fixture replaced by v1.2 tests (see CHANGELOG.md)")
    def test_c5_first_customer_at_tick_120(self):  # AC-P1-C5, C6
        with Workdir() as w:
            rows = run_quan(w, {"stock": {"ca_loc": 1}}, 125)
            arr = events(rows, "customer_arrived")
            self.assertEqual([e["tick"] for e in arr], [120])
            self.assertEqual(arr[0]["data"], {"order_id": "K1", "table_id": "T1", "dish_id": CA_LOC})
            c = snap_at(rows, 120)["customers"][0]
            self.assertEqual((c["order_tick"], c["state"], c["order_status"]), (120, "waiting", "reserved"))
            self.assertEqual(c["reserved"], {"ca_loc": 1})
            self.assertEqual(c["patience_ticks_left"], PATIENCE)  # bắt đầu giảm từ bước sau
            self.assertEqual(snap_at(rows, 121)["customers"][0]["patience_ticks_left"], PATIENCE - 1)

    # v1.1 có 4 bàn (T1–T4): bản Phase 1 giả định 1 bàn nên được viết lại, xem docs/plan/phase-2.md mục M3.
    @unittest.skip("Contract v1.2 breaking change: counting-stock fixture replaced by v1.2 tests (see CHANGELOG.md)")
    def test_c5_all_tables_busy_skips_round(self):  # AC-P1-C5
        with Workdir() as w:
            full = [cust(id=f"C{i}", table_id=f"T{i}") for i in range(1, 5)]
            rows = run_quan(w, {"random_customers": True, "stock": {"ca_loc": 4}, "customers": full}, 1100)
            self.assertEqual(events(rows, "customer_arrived"), [])  # lượt 120 và 1020 đều hết bàn
            self.assertEqual(events(rows, "no_dish"), [])

    @unittest.skip("Contract v1.2 breaking change: counting-stock fixture replaced by v1.2 tests (see CHANGELOG.md)")
    def test_c5_reservation_released_by_patience_lets_next_round_order(self):  # AC-P1-C5, C4
        with Workdir() as w:
            rows = run_quan(w, {"stock": {"ca_loc": 1}}, 3730)
            arr = events(rows, "customer_arrived")
            # K1 giữ cá lóc duy nhất suốt 3600 tick nên các lượt 1020/1920/2820 là no_dish; K1 rời lúc 3720 thì K2 được gọi
            self.assertEqual([(e["tick"], e["data"]["order_id"], e["data"]["table_id"]) for e in arr],
                             [(120, "K1", "T1"), (3720, "K2", "T1")])
            self.assertEqual([e["tick"] for e in events(rows, "no_dish")], [1020, 1920, 2820])
            left = events(rows, "customer_left")
            self.assertEqual([(e["tick"], e["data"]["reason"]) for e in left], [(3720, "patience")])

    def test_c6_no_dish_when_stock_empty(self):  # AC-P1-C6
        with Workdir() as w:
            rows = run_quan(w, {}, 1030)
            nd = events(rows, "no_dish")
            self.assertEqual([e["tick"] for e in nd], [120, 1020])
            self.assertEqual(nd[0]["data"], {})
            self.assertEqual(events(rows, "customer_arrived"), [])
            self.assertEqual(snap_at(rows, 130)["customers"], [])

    @unittest.skip("Contract v1.2 breaking change: counting-stock fixture replaced by v1.2 tests (see CHANGELOG.md)")
    def test_c6_reserved_stock_is_not_available(self):  # AC-P1-C6: tồn trừ phần giữ chỗ
        with Workdir() as w:
            # K1 giữ ca_loc duy nhất và rời lúc tick 5; sau khi nhả, tick 120 lại có món
            rows = run_quan(w, {"stock": {"ca_loc": 1}, "customers": [cust(patience_ticks_left=5)]}, 125)
            self.assertEqual([e["tick"] for e in events(rows, "customer_arrived")], [120])

    @unittest.skip("Contract v1.2 breaking change: counting-stock fixture replaced by v1.2 tests (see CHANGELOG.md)")
    def test_c6_picks_only_cookable_dishes(self):  # AC-P1-C6
        with Workdir() as w:
            for seed in range(1, 8):
                rows = run_quan(w, {"stock": {"bong_sung": 2, "ca_loc": 1}}, 121, seed=seed)
                dish = events(rows, "customer_arrived")[0]["data"]["dish_id"]
                self.assertIn(dish, (CA_LOC, "goi_bong_sung"))

    @unittest.skip("Contract v1.2 breaking change: counting-stock fixture replaced by v1.2 tests (see CHANGELOG.md)")
    def test_c8_random_customers_false(self):  # AC-P1-C8
        with Workdir() as w:
            rows = run_quan(w, {"random_customers": False, "stock": {"ca_loc": 1}}, 1100)
            self.assertEqual(events(rows, "customer_arrived"), [])
            self.assertEqual(events(rows, "no_dish"), [])

    @unittest.skip("Contract v1.2 breaking change: counting-stock fixture replaced by v1.2 tests (see CHANGELOG.md)")
    def test_c8_deterministic_same_seed(self):  # AC-P1-C8
        with Workdir() as w:
            blk = {"stock": {"bong_sung": 2, "ca_loc": 1}}
            run_quan(w, blk, 2000, seed=5, name="a.jsonl")
            run_quan(w, blk, 2000, seed=5, name="b.jsonl")
            with open(w.path("a.jsonl"), "rb") as a, open(w.path("b.jsonl"), "rb") as b:
                self.assertEqual(a.read(), b.read())


class Closing(unittest.TestCase):
    @unittest.skip("Contract v1.2 breaking change: counting-stock fixture replaced by v1.2 tests (see CHANGELOG.md)")
    def test_c7_waiting_customer_leaves_at_closing_without_penalty(self):  # AC-P1-C7
        with Workdir() as w:
            rows = run_quan(w, {"random_customers": False, "stock": {"ca_loc": 1},
                                "customers": [cust()], "time_left_ticks": 5}, 20)
            names = [e["name"] for e in events(rows)]
            self.assertEqual(names, ["customer_left", "quan_end"])
            left = events(rows, "customer_left")[0]
            self.assertEqual(left["tick"], 5)
            self.assertEqual(left["data"]["reason"], "closing")
            self.assertEqual(left["data"]["reputation"], 3.0)
            self.assertEqual(rows[-1]["reputation"], 3.0)

    @unittest.skip("Contract v1.2 breaking change: counting-stock fixture replaced by v1.2 tests (see CHANGELOG.md)")
    def test_c7_no_new_customer_on_last_step(self):  # AC-P1-C7: "nếu còn giờ" mới xét lượt khách
        with Workdir() as w:
            rows = run_quan(w, {"stock": {"ca_loc": 1}, "time_left_ticks": 120}, 130)
            self.assertEqual(events(rows, "customer_arrived"), [])

    def test_eating_customer_pays_when_done_with_tip_reputation(self):  # phần nối với M4
        with Workdir() as w:
            eating = cust(state="eating", order_status="served", eat_ticks_left=2, base_price=60, tip=12)
            rows = run_quan(w, {"random_customers": False, "customers": [eating]}, 5)
            paid = events(rows, "paid")
            self.assertEqual(len(paid), 1)
            self.assertEqual(paid[0]["tick"], 2)
            self.assertEqual(paid[0]["data"], {"order_id": "K1", "table_id": "T1", "base_price": 60,
                                               "tip": 12, "amount": 72, "reason": "finished_eating"})
            s = snap_at(rows, 2)
            self.assertEqual((s["money"], s["earned"]), (72, 72))
            self.assertTrue(close(s["reputation"], 3.2, 0.01))
            self.assertEqual(s["customers"], [])

    def test_eating_customer_pays_immediately_at_closing(self):  # AC-P1-C7
        with Workdir() as w:
            eating = cust(state="eating", order_status="served", eat_ticks_left=100, base_price=60, tip=0)
            rows = run_quan(w, {"random_customers": False, "customers": [eating], "time_left_ticks": 3}, 10)
            paid = events(rows, "paid")
            self.assertEqual((paid[0]["tick"], paid[0]["data"]["reason"]), (3, "closing"))
            self.assertEqual([e["name"] for e in events(rows)], ["paid", "quan_end"])


if __name__ == "__main__":
    unittest.main()
