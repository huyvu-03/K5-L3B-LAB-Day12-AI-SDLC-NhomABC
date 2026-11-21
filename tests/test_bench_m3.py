"""P4-M3.1 — Kiểm `bench_cmd` (Test Contract v1.3): đủ 5 trường số, hợp lệ, tính lặp cấu trúc.

- Test nhanh (chạy mặc định): bench ngắn (`--duration 1 --warmup 0.2`) qua `chonoi.bench.main`.
- Test dài (đặt `P4_FULL=1`): đúng lệnh chuẩn `--seed 42 --duration 30` qua `bench_cmd` khai trong contract.
- Kiểm file bằng chứng `docs/proof/phase-4/bench.json` (đặt `P4_STRICT_PROOF=1` để bắt buộc đo ≈ 30 s).
"""

import json
import os
import shlex
import subprocess
import sys
import unittest

from chonoi.bench import main as bench_main
from helpers import ROOT, Workdir

KEYS = ("avg_fps", "p1_low_fps", "frames", "measured_s", "load_ms")
PROOF = os.path.join(ROOT, "docs", "proof", "phase-4", "bench.json")


def check_bench_schema(tc, d, expected_s=None, tol=1.0):
    """Đủ 5 khóa, kiểu số, giá trị hợp lệ; nếu cho `expected_s` thì measured_s ≈ expected_s."""
    tc.assertIsInstance(d, dict)
    for k in KEYS:
        tc.assertIn(k, d, f"thiếu khóa {k}")
        tc.assertIsInstance(d[k], (int, float), k)
        tc.assertNotIsInstance(d[k], bool, k)
    tc.assertGreater(d["avg_fps"], 0)
    tc.assertGreater(d["p1_low_fps"], 0)
    tc.assertLessEqual(d["p1_low_fps"], d["avg_fps"] + 1e-6)
    tc.assertIsInstance(d["frames"], int)
    tc.assertGreater(d["frames"], 0)
    tc.assertGreater(d["measured_s"], 0)
    tc.assertGreaterEqual(d["load_ms"], 0)
    # avg_fps phải khớp frames / measured_s (sai số làm tròn)
    tc.assertAlmostEqual(d["avg_fps"], d["frames"] / d["measured_s"], delta=max(1.0, d["avg_fps"] * 0.01))
    if expected_s is not None:
        tc.assertAlmostEqual(d["measured_s"], expected_s, delta=tol)


class BenchSchemaUnit(unittest.TestCase):
    """Chạy được trên JSON mẫu, không cần bench thật."""

    def test_valid_sample_passes(self):
        check_bench_schema(self, {"avg_fps": 60.0, "p1_low_fps": 48.5, "frames": 1800, "measured_s": 30.0, "load_ms": 120.5},
                           expected_s=30)

    def test_missing_key_detected(self):
        for k in KEYS:
            d = {"avg_fps": 60.0, "p1_low_fps": 48.5, "frames": 1800, "measured_s": 30.0, "load_ms": 120.5}
            del d[k]
            with self.assertRaises(AssertionError):
                check_bench_schema(self, d)

    def test_wrong_type_detected(self):
        d = {"avg_fps": "60", "p1_low_fps": 48.5, "frames": 1800, "measured_s": 30.0, "load_ms": 1.0}
        with self.assertRaises(AssertionError):
            check_bench_schema(self, d)

    def test_wrong_duration_detected(self):
        d = {"avg_fps": 60.0, "p1_low_fps": 48.5, "frames": 300, "measured_s": 5.0, "load_ms": 1.0}
        with self.assertRaises(AssertionError):
            check_bench_schema(self, d, expected_s=30)


class BenchShort(unittest.TestCase):
    def test_short_bench_writes_five_keys(self):
        with Workdir() as w:
            out = w.path("b.json")
            self.assertEqual(bench_main(["--seed", "42", "--duration", "1", "--warmup", "0.2", "--out", out]), 0)
            with open(out, encoding="utf-8") as f:
                d = json.load(f)
        self.assertEqual(sorted(d), sorted(KEYS), "không được thừa/thiếu khóa")
        check_bench_schema(self, d, expected_s=1.0, tol=0.5)

    def test_bad_args_exit_2(self):
        with Workdir() as w:
            self.assertEqual(bench_main(["--duration", "0", "--out", w.path("x.json")]), 2)

    def test_out_dir_is_created(self):
        with Workdir() as w:
            out = w.path(os.path.join("sub", "dir", "b.json"))
            self.assertEqual(bench_main(["--duration", "0.2", "--warmup", "0", "--out", out]), 0)
            self.assertTrue(os.path.exists(out))


class BenchContract(unittest.TestCase):
    def test_bench_cmd_declared_in_contract(self):
        with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
            c = json.load(f)
        self.assertEqual(c["contract_version"], "1.3")
        self.assertTrue(c.get("bench_cmd"))

    @unittest.skipUnless(os.environ.get("P4_FULL") == "1", "đặt P4_FULL=1 để chạy bench chuẩn 30 s")
    def test_bench_cmd_full_30s(self):
        with open(os.path.join(ROOT, "game.contract.json"), encoding="utf-8") as f:
            cmd = shlex.split(json.load(f)["bench_cmd"])
        if cmd[0] == "python3" and sys.platform == "win32":
            cmd[0] = sys.executable
        with Workdir() as w:
            out = w.path("bench.json")
            p = subprocess.run([*cmd, "--seed", "42", "--duration", "30", "--out", out], cwd=ROOT,
                               capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            with open(out, encoding="utf-8") as f:
                check_bench_schema(self, json.load(f), expected_s=30, tol=1.0)


class BenchProof(unittest.TestCase):
    @unittest.skipUnless(os.path.exists(PROOF), "chưa có docs/proof/phase-4/bench.json")
    def test_proof_file_schema(self):
        with open(PROOF, encoding="utf-8") as f:
            d = json.load(f)
        check_bench_schema(self, d)

    @unittest.skipUnless(os.environ.get("P4_STRICT_PROOF") == "1" and os.path.exists(PROOF),
                         "đặt P4_STRICT_PROOF=1 để bắt buộc bằng chứng đo ≈ 30 s")
    def test_proof_file_measured_30s(self):
        with open(PROOF, encoding="utf-8") as f:
            check_bench_schema(self, json.load(f), expected_s=30, tol=1.0)


if __name__ == "__main__":
    unittest.main()
