"""Test tích hợp & tính tất định byte-for-byte cho M6.4 (v1.2 kho cá thể + từ chối kho đếm mã 2)."""

import json
import unittest

from helpers import Workdir, frames, read_jsonl, run_headless, snapshots, write_json


class IntegrationAndDeterminismM6(unittest.TestCase):
    def test_gather_to_quan_inventory_pipeline_deterministic(self):
        """Chạy 2 lần cùng seed luồng gather --inventory-out -> quan --inventory (v1.2): JSONL và kho giống từng byte."""
        with Workdir() as w:
            sc_gather = write_json(w.path("dock.json"), {
                "gather": {"hold": [
                    {"id": "I1", "kind": "ca_loc", "fresh": 100},
                    {"id": "I2", "kind": "bong_sung", "fresh": 100},
                    {"id": "I3", "kind": "bong_sung", "fresh": 100},
                ]}
            })
            inp_gather = write_json(w.path("dock_in.json"), frames({"tick": 0, "interact": True}))
            inp_quan = write_json(w.path("quan_in.json"), frames(
                {"tick": 0, "move": [-1, 1]},
                {"tick": 40, "move": [0, 0]},
            ))

            for run_idx in (1, 2):
                g_out = w.path(f"gather_{run_idx}.jsonl")
                inv_out = w.path(f"inv_{run_idx}.json")
                q_out = w.path(f"quan_{run_idx}.jsonl")

                code, err = run_headless(
                    "--mode", "gather", "--seed", "42",
                    "--scenario", sc_gather, "--inputs", inp_gather,
                    "--ticks", "10", "--out", g_out, "--inventory-out", inv_out,
                )
                self.assertEqual(code, 0, err)

                with open(inv_out, encoding="utf-8") as f:
                    items = json.load(f)["items"]
                self.assertEqual([x["id"] for x in items], ["I1", "I2", "I3"])

                code, err = run_headless(
                    "--mode", "quan", "--seed", "42",
                    "--inventory", inv_out, "--inputs", inp_quan,
                    "--ticks", "120", "--out", q_out,
                )
                self.assertEqual(code, 0, err)
                snap0 = snapshots(read_jsonl(q_out))[0]
                self.assertEqual([x["id"] for x in snap0["stock"]], ["I1", "I2", "I3"])

            for prefix in ("gather", "inv", "quan"):
                ext = "json" if prefix == "inv" else "jsonl"
                with open(w.path(f"{prefix}_1.{ext}"), "rb") as a, open(w.path(f"{prefix}_2.{ext}"), "rb") as b:
                    self.assertEqual(a.read(), b.read(), f"{prefix} không tất định byte-for-byte")

            # Kho đếm v1.1 phải bị từ chối với mã thoát 2 khi chạy ở Contract v1.2
            old_inv = write_json(w.path("old_inv.json"), {"items": {"ca_loc": 1}})
            code, _ = run_headless("--mode", "quan", "--seed", "42", "--inventory", old_inv,
                                   "--ticks", "0", "--out", w.path("old_q.jsonl"))
            self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
