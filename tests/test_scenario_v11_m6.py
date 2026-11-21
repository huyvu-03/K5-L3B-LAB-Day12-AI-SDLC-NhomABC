"""Unit & black-box tests cho Phase 2 (M6.1-M6.3): Contract v1.1, CLI --mode day/--days, inputs v1.1 & scenario v1.1."""

import os
import unittest

from helpers import Workdir, frames, read_jsonl, run_headless, snapshots, write_json


class ContractV11AndScenarioM6(unittest.TestCase):
    def test_cli_day_mode_and_days_flag(self):
        with Workdir() as w:
            out = w.path("day.jsonl")
            code, err = run_headless("--mode", "day", "--seed", "1", "--days", "2", "--ticks", "0", "--out", out)
            self.assertEqual(code, 0, err)
            rows = read_jsonl(out)
            snaps = snapshots(rows)
            self.assertEqual(snaps[0]["mode"], "day")
            self.assertEqual(snaps[0]["day"], 1)
            self.assertEqual(rows[-1]["type"], "end")
            self.assertEqual(rows[-1]["days_completed"], 0)

            # --days sai mode hoặc ngoài [1, 5] -> mã 2
            for args in (
                ("--mode", "gather", "--seed", "1", "--days", "1", "--ticks", "0", "--out", w.path("bad1.jsonl")),
                ("--mode", "day", "--seed", "1", "--days", "0", "--ticks", "0", "--out", w.path("bad2.jsonl")),
                ("--mode", "day", "--seed", "1", "--days", "6", "--ticks", "0", "--out", w.path("bad3.jsonl")),
            ):
                code, _ = run_headless(*args)
                self.assertEqual(code, 2, args)

    def test_inputs_v11_pause_shop_done_buy(self):
        with Workdir() as w:
            inp = write_json(w.path("in.json"), frames(
                {"tick": 0, "pause": True},
                {"tick": 1, "pause": False},
                {"tick": 2, "pause": True},
                {"tick": 3, "pause": False, "buy": "oxygen", "shop_done": True},
            ))
            out = w.path("day.jsonl")
            code, err = run_headless("--mode", "day", "--seed", "1", "--ticks", "5", "--inputs", inp, "--out", out)
            self.assertEqual(code, 0, err)

            # buy rỗng -> mã 2
            bad_inp = write_json(w.path("bad_in.json"), frames({"tick": 0, "buy": ""}))
            bad_out = w.path("bad.jsonl")
            code, _ = run_headless("--mode", "day", "--seed", "1", "--ticks", "5", "--inputs", bad_inp, "--out", bad_out)
            self.assertEqual(code, 2)
            self.assertFalse(os.path.exists(bad_out))

    def test_day_scenario_valid_and_conflicts_exit_2(self):
        with Workdir() as w:
            # Hợp lệ theo ví dụ Ticket02 mục 4.3
            sc_ok = write_json(w.path("ok.json"), {
                "day": {"money": 200, "earned": 200},
                "gather": {"hold": ["ca_loc", "bong_sung", "keo_neo"], "random_fish": False},
            })
            code, err = run_headless("--mode", "day", "--seed", "1", "--ticks", "0", "--scenario", sc_ok,
                                     "--out", w.path("ok.jsonl"))
            self.assertEqual(code, 0, err)

            # Các case mâu thuẫn -> mã 2
            bad_cases = [
                # money > earned
                {"day": {"money": 300, "earned": 200}},
                # cấm quan.stock trong day
                {"quan": {"stock": {"ca_loc": 1}}},
                # cấm quan.reputation trong day
                {"quan": {"reputation": 4.0}},
                # day_plan ingredients sai tổng công thức
                {"day": {"day_plan": [{"day": 1, "dishes": {"ca_loc_nuong_trui": 2}, "ingredients": {"ca_loc": 1}}]}},
                # monster recoil nhưng state_ticks_left == 0
                {"gather": {"monsters": [{
                    "id": "M1", "kind": "ca_sau", "pos": [60, 24],
                    "waypoints": [[60, 24], [64, 24]], "state": "recoil",
                    "state_ticks_left": 0, "recoil_dir": [1, 0],
                }]}},
                # monster patrol nhưng recoil_dir != null
                {"gather": {"monsters": [{
                    "id": "M1", "kind": "ca_sau", "pos": [60, 24],
                    "waypoints": [[60, 24], [64, 24]], "state": "patrol",
                    "recoil_dir": [1, 0],
                }]}},
            ]
            for i, payload in enumerate(bad_cases):
                sc = write_json(w.path(f"bad_{i}.json"), payload)
                out = w.path(f"bad_{i}.jsonl")
                code, _ = run_headless("--mode", "day", "--seed", "1", "--ticks", "0", "--scenario", sc, "--out", out)
                self.assertEqual(code, 2, payload)
                self.assertFalse(os.path.exists(out))


if __name__ == "__main__":
    unittest.main()
