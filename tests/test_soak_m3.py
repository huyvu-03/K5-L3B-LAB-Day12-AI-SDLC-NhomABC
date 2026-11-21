"""P4-M3.1 — Kiểm `soak_cmd` (Test Contract v1.3): 10 Ngày liên tục, tất định, liên tục qua ranh giới D5→D6.

- Schema + tính lặp 2 lần cùng seed 7 (chỉ so trường gameplay, bỏ `duration_s`).
- Trạng thái xuyên Ngày (tiền, earned, uy tín, cấp nâng cấp, id cá thể) khi nạp vốn ban đầu qua scenario `day`,
  vì bot mặc định của `chonoi.soak` cập bến ngay nên earned/uy tín không đổi (xem docs/proof/phase-4/m3.md).
"""

import json
import os
import shlex
import subprocess
import sys
import unittest

from chonoi.contract import load_contract
from chonoi.runner import Session
from chonoi.soak import _bot_input, main as soak_main
from helpers import ROOT, Workdir

RESULT_KEYS = ("day", "earned", "reputation", "score")
TOP_KEYS = ("days", "days_completed", "crashes", "results", "duration_s")


def run_soak_file(seed, days):
    with Workdir() as w:
        out = w.path("soak.json")
        rc = soak_main(["--seed", str(seed), "--days", str(days), "--out", out])
        with open(out, encoding="utf-8") as f:
            return rc, json.load(f)


def gameplay(d):
    """Phần tất định của soak.json (bỏ duration_s)."""
    return {k: v for k, v in d.items() if k != "duration_s"}


class SoakSchema(unittest.TestCase):
    def test_10_days_schema_and_counts(self):
        rc, d = run_soak_file(7, 10)
        self.assertEqual(rc, 0)
        for k in TOP_KEYS:
            self.assertIn(k, d, k)
        self.assertEqual(d["days"], 10)
        self.assertEqual(d["days_completed"], d["days"])
        self.assertEqual(d["crashes"], 0)
        self.assertEqual(len(d["results"]), 10)
        self.assertEqual([r["day"] for r in d["results"]], list(range(1, 11)))
        for r in d["results"]:
            for k in RESULT_KEYS:
                self.assertIn(k, r, k)
        self.assertIsInstance(d["duration_s"], (int, float))
        self.assertGreaterEqual(d["duration_s"], 0)

    def test_repeat_same_seed_same_gameplay(self):
        _, a = run_soak_file(7, 10)
        _, b = run_soak_file(7, 10)
        self.assertEqual(gameplay(a), gameplay(b))

    def test_other_day_counts_complete(self):
        for n in (1, 5, 6, 11):
            rc, d = run_soak_file(7, n)
            self.assertEqual((rc, d["days_completed"], d["crashes"], len(d["results"])), (0, n, 0, n), n)

    def test_bad_days_exit_2(self):
        with Workdir() as w:
            self.assertEqual(soak_main(["--seed", "7", "--days", "0", "--out", w.path("x.json")]), 2)


class SoakCrossDayState(unittest.TestCase):
    """Chạy Session ngày thật với vốn ban đầu; ghi trạng thái tại mỗi `shop_end`, kiểm tính liên tục D5→D6."""

    SCENARIO = {"day": {"money": 400, "earned": 120, "reputation": 4.0}}

    @classmethod
    def setUpClass(cls):
        tuning = load_contract()["tuning"]
        sess = Session("day", tuning, cls.SCENARIO, seed=7, days=10)
        cls.snaps = []
        cls.plans = {}
        for ev in sess.initial_event_rows():  # day_plan của D1 phát ở tick 0
            if ev["name"] == "day_plan":
                cls.plans[ev["day"]] = ev["data"]
        guard = 0
        while not sess.done and guard < 10 * 25000:
            guard += 1
            for ev in sess.step(_bot_input(sess)):
                if ev["name"] == "day_plan":
                    cls.plans[ev["day"]] = ev["data"]
                if ev["name"] == "shop_end":
                    sim = sess.sim
                    cls.snaps.append({
                        "day": ev["day"], "money": sim.money, "earned": sim.earned,
                        "reputation": sim.reputation, "upgrades": dict(sim.upgrades),
                        "days_completed": sim.days_completed,
                        "id_counters": dict(sim.ids._next),
                    })
        cls.sess = sess

    def test_ran_all_10_days(self):
        self.assertTrue(self.sess.done)
        self.assertEqual(self.sess.sim.days_completed, 10)
        self.assertEqual([s["day"] for s in self.snaps], list(range(1, 11)))

    def test_initial_state_carried_into_day1(self):
        # D1 bắt đầu từ 400/120/4.0: earned và uy tín không được reset ở D1
        s1 = self.snaps[0]
        self.assertGreaterEqual(s1["earned"], 120)
        self.assertAlmostEqual(s1["reputation"], 4.0, delta=1.0 + 1e-9)

    def test_earned_and_upgrades_never_decrease(self):
        for prev, cur in zip(self.snaps, self.snaps[1:]):
            self.assertGreaterEqual(cur["earned"], prev["earned"], f"earned giảm ở D{cur['day']}")
            for k, lv in prev["upgrades"].items():
                self.assertGreaterEqual(cur["upgrades"].get(k, 0), lv, f"cấp {k} giảm ở D{cur['day']}")

    def test_money_never_negative(self):
        for s in self.snaps:
            self.assertGreaterEqual(s["money"], 0, f"D{s['day']}")

    def test_day5_to_day6_no_reset(self):
        d5, d6 = self.snaps[4], self.snaps[5]
        self.assertGreaterEqual(d6["earned"], d5["earned"])
        for k, lv in d5["upgrades"].items():
            self.assertGreaterEqual(d6["upgrades"].get(k, 0), lv)
        self.assertEqual(d5["days_completed"], 5)
        self.assertEqual(d6["days_completed"], 6)

    def test_day6_to_10_repeat_day_plan_1_to_5(self):
        self.assertEqual(sorted(self.plans), list(range(1, 11)))
        for d in range(6, 11):
            self.assertEqual(self.plans[d], self.plans[d - 5], f"D{d} phải lặp D{d - 5}")

    def test_id_counters_monotonic_no_reuse(self):
        """Bộ cấp id không lùi về 1 sau D5→D6 (id cá thể xuyên suốt, không cấp lại)."""
        for prev, cur in zip(self.snaps, self.snaps[1:]):
            for prefix, n in prev["id_counters"].items():
                self.assertGreaterEqual(cur["id_counters"].get(prefix, 0), n, f"{prefix} lùi ở D{cur['day']}")

    def test_deterministic_across_two_runs(self):
        tuning = load_contract()["tuning"]
        sess = Session("day", tuning, self.SCENARIO, seed=7, days=10)
        snaps = []
        while not sess.done:
            for ev in sess.step(_bot_input(sess)):
                if ev["name"] == "shop_end":
                    snaps.append((ev["day"], sess.sim.money, sess.sim.earned, sess.sim.reputation,
                                  tuple(sorted(sess.sim.upgrades.items()))))
        ref = [(s["day"], s["money"], s["earned"], s["reputation"], tuple(sorted(s["upgrades"].items())))
               for s in self.snaps]
        self.assertEqual(snaps, ref)


class SoakContract(unittest.TestCase):
    def test_soak_cmd_declared(self):
        with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
            c = json.load(f)
        self.assertEqual(c["contract_version"], "1.3")
        self.assertTrue(c.get("soak_cmd"))

    def test_soak_cmd_via_subprocess(self):
        with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
            cmd = shlex.split(json.load(f)["soak_cmd"])
        if cmd[0] == "python3" and sys.platform == "win32":
            cmd[0] = sys.executable
        with Workdir() as w:
            out = w.path("soak.json")
            p = subprocess.run([*cmd, "--seed", "7", "--days", "10", "--out", out], cwd=ROOT,
                               capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            with open(out, encoding="utf-8") as f:
                d = json.load(f)
        self.assertEqual((d["days"], d["days_completed"], d["crashes"]), (10, 10, 0))


class SoakProof(unittest.TestCase):
    PROOF = os.path.join(ROOT, "docs", "proof", "phase-4", "soak.json")

    @unittest.skipUnless(os.path.exists(PROOF), "chưa có docs/proof/phase-4/soak.json")
    def test_proof_file(self):
        with open(self.PROOF, encoding="utf-8") as f:
            d = json.load(f)
        self.assertEqual((d["days"], d["days_completed"], d["crashes"]), (10, 10, 0))
        self.assertEqual(len(d["results"]), 10)


if __name__ == "__main__":
    unittest.main()
