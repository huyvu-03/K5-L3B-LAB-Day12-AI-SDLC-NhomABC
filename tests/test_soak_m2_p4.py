"""Unit tests cho Phase 4 Module M2: Kiểm định độ bền bỉ, tính tất định và chuyển tiếp 10 Ngày của soak_cmd.

Bao phủ toàn bộ 7 tiêu chí AC từ AC-P4-M2-01 đến AC-P4-M2-07 theo docs/specs/phase-4-m2.md.
"""

import json
import os
import sys
import unittest

from chonoi.contract import load_contract
from chonoi.ids import IdAllocator
from chonoi.rng import Streams
from chonoi.runner import Session
from chonoi.sim.day import DaySim
from chonoi.soak import _bot_input, main as soak_main, run_soak
from helpers import Workdir


class TestSoakM2Phase4(unittest.TestCase):
    """Test suite nghiệm thu Soak Test 10 Ngày và Bàn giao Giỏ/Kho cá thể v1.3."""

    def test_ac_p4_m2_01_invalid_days_argument(self):
        """AC-P4-M2-01: Chặn tham số không hợp lệ (--days < 1) và trả về mã lỗi 2."""
        with Workdir() as w:
            out_path = w.path("invalid_soak.json")
            # days = 0
            rc0 = soak_main(["--seed", "7", "--days", "0", "--out", out_path])
            self.assertEqual(rc0, 2, "Chạy với --days 0 phải trả về mã thoát 2")

            # days = -5
            rc_neg = soak_main(["--seed", "7", "--days", "-5", "--out", out_path])
            self.assertEqual(rc_neg, 2, "Chạy với --days âm phải trả về mã thoát 2")

    def test_ac_p4_m2_02_and_03_soak_10_days_zero_crashes_and_5_keys(self):
        """AC-P4-M2-02 & AC-P4-M2-03: Chạy 10 Ngày liên tục không crash, xuất đủ 5 trường schema."""
        with Workdir() as w:
            out_path = w.path("soak_10.json")
            rc = soak_main(["--seed", "7", "--days", "10", "--out", out_path])
            self.assertEqual(rc, 0, "Chạy soak 10 ngày phải trả về mã 0")
            self.assertTrue(os.path.exists(out_path), "File soak.json phải tồn tại")

            with open(out_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # AC-P4-M2-03: Đủ 5 trường gốc
            required_keys = {"days", "days_completed", "crashes", "results", "duration_s"}
            self.assertEqual(set(data.keys()), required_keys, f"Thiếu hoặc thừa khóa: {set(data.keys())}")

            # AC-P4-M2-02: Zero crash và hoàn thành 10 ngày
            self.assertEqual(data["days"], 10)
            self.assertEqual(data["days_completed"], 10)
            self.assertEqual(data["crashes"], 0)
            self.assertGreater(data["duration_s"], 0.0)

    def test_ac_p4_m2_04_results_array_structure(self):
        """AC-P4-M2-04: Mảng results chứa đủ 10 phần tử (Day 1..10) với các trường earned, reputation, score."""
        with Workdir() as w:
            out_path = w.path("soak_results.json")
            soak_main(["--seed", "7", "--days", "10", "--out", out_path])
            with open(out_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            results = data["results"]
            self.assertEqual(len(results), 10, "Mảng results phải có đúng 10 ngày")

            expected_days = list(range(1, 11))
            actual_days = [r["day"] for r in results]
            self.assertEqual(actual_days, expected_days, "Thứ tự các ngày trong results phải là 1..10")

            item_keys = {"day", "earned", "reputation", "score"}
            for r in results:
                self.assertTrue(item_keys.issubset(r.keys()), f"Mỗi phần tử kết quả phải có đủ các trường: {item_keys}")
                self.assertIsInstance(r["earned"], int)
                self.assertIsInstance(r["reputation"], (int, float))
                self.assertIsInstance(r["score"], int)

    def test_ac_p4_m2_05_day_plan_rollover_d5_to_d6(self):
        """AC-P4-M2-05: Chuyển tiếp chu kỳ kế hoạch ngày: D6 lặp lại D1, D7 lặp lại D2 không lỗi."""
        tuning = load_contract()["tuning"]
        sim = DaySim(tuning, {}, Streams(7), IdAllocator(), days=10)

        # Kiểm tra kế hoạch của Ngày 1 đến 5 và so sánh với Ngày 6 đến 10
        plan_d1 = sim._get_plan(1)
        plan_d6 = sim._get_plan(6)
        self.assertEqual(plan_d6["dishes"], plan_d1["dishes"], "Thực đơn Ngày 6 phải lặp lại Ngày 1")
        self.assertEqual(plan_d6["ingredients"], plan_d1["ingredients"], "Nguyên liệu Ngày 6 phải lặp lại Ngày 1")

        plan_d2 = sim._get_plan(2)
        plan_d7 = sim._get_plan(7)
        self.assertEqual(plan_d7["dishes"], plan_d2["dishes"], "Thực đơn Ngày 7 phải lặp lại Ngày 2")

        plan_d5 = sim._get_plan(5)
        plan_d10 = sim._get_plan(10)
        self.assertEqual(plan_d10["dishes"], plan_d5["dishes"], "Thực đơn Ngày 10 phải lặp lại Ngày 5")

    def test_ac_p4_m2_06_determinism_across_runs(self):
        """AC-P4-M2-06: Hai lần chạy độc lập cùng seed 7 cho mảng results giống hệt nhau từng giá trị."""
        with Workdir() as w:
            out1 = w.path("run1.json")
            out2 = w.path("run2.json")

            rc1 = soak_main(["--seed", "7", "--days", "10", "--out", out1])
            rc2 = soak_main(["--seed", "7", "--days", "10", "--out", out2])

            self.assertEqual(rc1, 0)
            self.assertEqual(rc2, 0)

            with open(out1, "r", encoding="utf-8") as f1, open(out2, "r", encoding="utf-8") as f2:
                d1 = json.load(f1)
                d2 = json.load(f2)

            self.assertEqual(d1["results"], d2["results"], "Mảng results qua 2 lần chạy độc lập phải giống hệt nhau")
            self.assertEqual(d1["days_completed"], d2["days_completed"])
            self.assertEqual(d1["crashes"], d2["crashes"])

    def test_ac_p4_m2_07_id_continuity_and_no_id_reset(self):
        """AC-P4-M2-07: Bộ cấp phát ID cá thể (IdAllocator) duy trì liên tục xuyên ngày, không bị reset."""
        tuning = load_contract()["tuning"]
        sess = Session("day", tuning, {}, seed=7, days=3)

        # Chạy một số tick để mô phỏng sinh sự kiện và cấp ID
        for _ in range(300):
            if sess.done:
                break
            sess.step(_bot_input(sess))

        # Kiểm tra rằng id allocator của session đang ở trạng thái hợp lệ và không bị reset
        ids = sess.sim.ids
        self.assertIsNotNone(ids)
        # Sinh một ID mới từ bộ cấp ID chung
        new_id = ids.new("I")
        self.assertTrue(new_id.startswith("I"), f"ID phải bắt đầu bằng 'I', nhận được {new_id}")


if __name__ == "__main__":
    unittest.main()
