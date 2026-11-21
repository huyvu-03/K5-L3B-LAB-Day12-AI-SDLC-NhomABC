#!/usr/bin/env python3
"""P4-M3.1 — chạy 1 lần: regression P1–P3 + bench + soak, gom log vào docs/proof/phase-4/.

Cách dùng (Windows: dùng `python`):
    python tools/m3_phase4_proof.py                 # đủ: regression, determinism, bench 30 s, soak x2
    python tools/m3_phase4_proof.py --bench-duration 3   # bench ngắn để chạy thử
    python tools/m3_phase4_proof.py --skip bench    # bỏ qua bước (regression|determinism|bench|soak)

Ghi ra (mặc định dưới docs/proof/phase-4/): regression-unittest.txt, check-team.txt, determinism-p1-p3.txt,
m3-bench.json, m3-bench-run2.json, m3-soak.json, m3-soak-run2.json, m3-summary.txt.
Không ghi đè `bench.json` / `soak.json` (bằng chứng chính của M5.3 / M6.2).
Thoát mã 0 nếu mọi bước chạy đều đạt, 1 nếu có bước lỗi.
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BENCH_KEYS = ("avg_fps", "p1_low_fps", "frames", "measured_s", "load_ms")


def sh(args, env=None, **kw):
    e = os.environ.copy()
    e["PYTHONIOENCODING"] = "utf-8"
    e["PYTHONPATH"] = os.pathsep.join([os.path.join(ROOT, "tests"), ROOT])
    if env:
        e.update(env)
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", env=e, **kw)


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def step_regression(out, summary):
    p = sh([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"])
    write(os.path.join(out, "regression-unittest.txt"), p.stdout + p.stderr)
    last = [ln for ln in (p.stderr or p.stdout).splitlines() if ln.strip()][-2:]
    summary.append(f"regression: rc={p.returncode} | {' / '.join(last)}")
    c = sh([sys.executable, "tools/check_team.py"])
    write(os.path.join(out, "check-team.txt"), c.stdout + c.stderr + f"exit={c.returncode}\n")
    summary.append(f"check_team: rc={c.returncode} | {c.stdout.strip()}")
    return p.returncode == 0 and c.returncode == 0


def step_determinism(out, summary):
    ok = True
    lines = ["# Tính tất định P1–P3 (cùng seed, chạy 2 lần, so sánh từng byte)"]
    with tempfile.TemporaryDirectory() as d:
        for run in "ab":
            sh([sys.executable, "-m", "chonoi.headless", "--mode", "gather", "--seed", "1", "--ticks", "11000",
                "--out", f"{d}/g_{run}.jsonl", "--inventory-out", f"{d}/kho_{run}.json"])
            sh([sys.executable, "-m", "chonoi.headless", "--mode", "quan", "--seed", "1", "--inventory",
                f"{d}/kho_{run}.json", "--ticks", "600", "--out", f"{d}/q_{run}.jsonl"])
            sh([sys.executable, "-m", "chonoi.headless", "--mode", "day", "--seed", "1", "--ticks", "3000",
                "--out", f"{d}/d_{run}.jsonl"])
        for name, ext in (("g", "jsonl"), ("q", "jsonl"), ("d", "jsonl"), ("kho", "json")):
            try:
                a = open(f"{d}/{name}_a.{ext}", "rb").read()
                b = open(f"{d}/{name}_b.{ext}", "rb").read()
                same = a == b and len(a) > 0
            except OSError:
                a, same = b"", False
            ok &= same
            lines.append(f"{name}: {'IDENTICAL' if same else 'DIFFERENT'} ({len(a)} bytes)")
    write(os.path.join(out, "determinism-p1-p3.txt"), "\n".join(lines) + "\n")
    summary.append("determinism: " + ("OK" if ok else "FAIL"))
    return ok


def step_bench(out, duration, summary):
    ok = True
    for run in ("", "-run2"):
        path = os.path.join(out, f"m3-bench{run}.json")
        p = sh([sys.executable, "-m", "chonoi.bench", "--seed", "42", "--duration", str(duration), "--out", path])
        try:
            d = load(path)
            miss = [k for k in BENCH_KEYS if k not in d]
            good = p.returncode == 0 and not miss and abs(d["measured_s"] - duration) <= 1.0 and d["frames"] > 0
        except (OSError, ValueError):
            d, miss, good = {}, list(BENCH_KEYS), False
        ok &= good
        summary.append(f"bench{run or '-run1'}: {'OK' if good else 'FAIL'} missing={miss} {d}")
    return ok


def step_soak(out, summary):
    ok = True
    res = []
    for run in ("", "-run2"):
        path = os.path.join(out, f"m3-soak{run}.json")
        p = sh([sys.executable, "-m", "chonoi.soak", "--seed", "7", "--days", "10", "--out", path])
        try:
            d = load(path)
            good = p.returncode == 0 and d["days_completed"] == d["days"] == 10 and d["crashes"] == 0 \
                and len(d["results"]) == 10
        except (OSError, ValueError, KeyError):
            d, good = {}, False
        res.append(d)
        ok &= good
        summary.append(f"soak{run or '-run1'}: {'OK' if good else 'FAIL'} days_completed={d.get('days_completed')} "
                       f"crashes={d.get('crashes')} duration_s={d.get('duration_s')}")
    same = bool(res[0]) and {k: v for k, v in res[0].items() if k != "duration_s"} == \
        {k: v for k, v in res[1].items() if k != "duration_s"}
    summary.append(f"soak repeatable (bỏ duration_s): {'OK' if same else 'FAIL'}")
    return ok and same


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=os.path.join("docs", "proof", "phase-4"))
    ap.add_argument("--bench-duration", type=float, default=30.0)
    ap.add_argument("--skip", action="append", default=[], choices=["regression", "determinism", "bench", "soak"])
    a = ap.parse_args(argv)
    out = a.out if os.path.isabs(a.out) else os.path.join(ROOT, a.out)
    os.makedirs(out, exist_ok=True)
    summary, results = [], {}
    if "regression" not in a.skip:
        results["regression"] = step_regression(out, summary)
    if "determinism" not in a.skip:
        results["determinism"] = step_determinism(out, summary)
    if "bench" not in a.skip:
        results["bench"] = step_bench(out, a.bench_duration, summary)
    if "soak" not in a.skip:
        results["soak"] = step_soak(out, summary)
    commit = sh(["git", "rev-parse", "--short", "HEAD"]).stdout.strip()
    text = f"commit: {commit}\n" + "\n".join(summary) + "\n" + \
        "RESULT: " + ("ALL OK" if all(results.values()) else "FAIL " + ",".join(k for k, v in results.items() if not v)) + "\n"
    write(os.path.join(out, "m3-summary.txt"), text)
    sys.stdout.buffer.write(text.encode("utf-8"))
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
