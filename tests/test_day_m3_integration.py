"""M3.4a (Phase 2) — Ghép khách (M3) với vòng ngày `day` (M4): thực đơn bị lọc theo kế hoạch ngày.

Chạy CLI thật: `--mode day --days 1`. Ngày 1 chỉ có ca_loc_nuong_trui và goi_bong_sung (Ticket02 mục 2).
Kho dựng bằng gather.hold có thêm bong_dien_dien nên canh_chua_ca_loc (NGOÀI kế hoạch) vẫn nấu được về nguyên liệu:
nếu lọc kế hoạch hỏng thì khách sẽ gọi nó.
"""

import unittest

from helpers import Workdir, events, frames, read_jsonl, run_headless, write_json

PLAN_D1 = {"ca_loc_nuong_trui", "goi_bong_sung"}
HOLD = ["ca_loc"] * 3 + ["bong_sung"] * 6 + ["bong_dien_dien"] + ["ca_linh"] * 2  # 12 = hold_capacity


def run_day(w, seed, scenario, ticks, name="d.jsonl", mode="day"):
    sc = write_json(w.path("sc.json"), scenario)
    inp = write_json(w.path("in.json"), frames({"tick": 0, "interact": True}, {"tick": 1, "interact": False}))
    out = w.path(name)
    args = ["--mode", mode, "--seed", str(seed), "--ticks", str(ticks), "--scenario", sc,
            "--inputs", inp, "--snapshot-every", "100", "--out", out]
    if mode == "day":
        args[2:2] = ["--days", "1"]
    code, err = run_headless(*args)
    assert code == 0, err
    return read_jsonl(out)


def day_scenario():
    return {"gather": {"hold": HOLD, "random_fish": False}}


class DayPlanFilterWithCustomers(unittest.TestCase):
    @unittest.skip("Contract v1.2 breaking change: counting-stock fixture replaced by v1.2 tests (see CHANGELOG.md)")
    def test_day1_customers_only_order_planned_dishes(self):
        seen = set()
        with Workdir() as w:
            for seed in range(1, 13):
                rows = run_day(w, seed, day_scenario(), 1100)
                arr = events(rows, "customer_arrived")
                self.assertGreaterEqual(len(arr), 1, f"seed {seed}: quán không có khách")
                for e in arr:
                    self.assertIn(e["data"]["dish_id"], PLAN_D1, f"seed {seed}")
                    self.assertEqual(e["day"], 1)  # vỏ event của day có thêm trường day
                seen |= {e["data"]["dish_id"] for e in arr}
        self.assertEqual(seen, PLAN_D1)  # cả hai món của kế hoạch đều có lúc được gọi

    @unittest.skip("Contract v1.2 breaking change: counting-stock fixture replaced by v1.2 tests (see CHANGELOG.md)")
    def test_control_standalone_quan_with_same_stock_can_order_out_of_plan_dish(self):
        # đối chứng: cùng kho nhưng quán chạy riêng (cả 6 món) thì canh_chua_ca_loc có lúc được gọi
        seen = set()
        with Workdir() as w:
            for seed in range(1, 30):
                rows = run_day(w, seed, {"quan": {"stock": {"ca_loc": 3, "bong_sung": 6, "bong_dien_dien": 1,
                                                            "ca_linh": 2}}}, 125, mode="quan")
                seen |= {e["data"]["dish_id"] for e in events(rows, "customer_arrived")}
        self.assertIn("canh_chua_ca_loc", seen)

    @unittest.skip("Contract v1.2 breaking change: counting-stock fixture replaced by v1.2 tests (see CHANGELOG.md)")
    def test_day1_quan_opens_with_handover_stock_and_first_customer_at_120(self):
        with Workdir() as w:
            rows = run_day(w, 3, day_scenario(), 200)
            start_quan = next(e for e in events(rows, "phase_start") if e["phase"] == "quan")
            first = events(rows, "customer_arrived")[0]
            self.assertEqual(first["tick"] - start_quan["tick"], 120)  # lịch tính theo phase_tick của quán

    @unittest.skip("Contract v1.2 breaking change: counting-stock fixture replaced by v1.2 tests (see CHANGELOG.md)")
    def test_day_is_deterministic_with_customers(self):
        with Workdir() as w:
            run_day(w, 5, day_scenario(), 1100, name="a.jsonl")
            run_day(w, 5, day_scenario(), 1100, name="b.jsonl")
            with open(w.path("a.jsonl"), "rb") as a, open(w.path("b.jsonl"), "rb") as b:
                self.assertEqual(a.read(), b.read())


if __name__ == "__main__":
    unittest.main()
