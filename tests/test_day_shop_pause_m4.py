"""Unit tests cho Phase 2 · M4: Pause (3 mode), Shop (oxygen/hp), và DaySim (1 & nhiều ngày).

Dùng fixture tuning v1.1 độc lập nên chạy xanh ngay cả khi game.contract.json vẫn ở v1.0 (Phase 1).
"""

import time
import unittest

from chonoi.contract import load_contract
from chonoi.inputs import InputState
from chonoi.jsonl import dumps
from chonoi.runner import Session


def _inp(move=(0.0, 0.0), edges=(), buy=None):
    st = InputState(move, {b: True for b in edges}, set(edges))
    st.buy = buy
    return st


def _tuning_v11():
    base = load_contract()["tuning"]
    return {
        **base,
        "day_plan": [
            {
                "day": 1,
                "dishes": {"ca_loc_nuong_trui": 3, "goi_bong_sung": 3},
                "ingredients": {"ca_loc": 3, "bong_sung": 6},
            },
            {
                "day": 2,
                "dishes": {"ca_loc_nuong_trui": 2, "lau_ca_linh_dien_dien": 2},
                "ingredients": {"ca_loc": 2, "ca_linh": 6, "bong_dien_dien": 2},
            },
        ],
        "shop": {
            "max_ticks": 600,
            "upgrades": {
                "oxygen": [
                    {"level": 1, "price": 200, "oxygen_max_s": 45},
                    {"level": 2, "price": 400, "oxygen_max_s": 60},
                ],
                "hp": [
                    {"level": 1, "price": 250, "hp_max": 4},
                    {"level": 2, "price": 500, "hp_max": 5},
                ],
            },
        },
    }


class PauseM4Tests(unittest.TestCase):
    def test_ac_p2_m4_01_02_pause_and_resume_in_gather_and_quan(self):
        """AC-P2-M4-01/02: Pause đóng băng sim_tick/timer và bỏ qua hành động; Resume chạy ngay trong bước đó."""
        tuning = _tuning_v11()
        for mode in ("gather", "quan"):
            sess = Session(mode, tuning, {"time_left_ticks": 100}, seed=1)
            # Tick 1: pause + đồng thời bấm interact (phải bị bỏ qua)
            evs = sess.step(_inp(edges=("pause", "interact")))
            self.assertEqual([e["name"] for e in evs], ["paused"])
            snap = sess.snapshot()
            self.assertEqual(snap["state"], "paused")
            self.assertEqual(snap["tick"], 1)
            self.assertEqual(snap["sim_tick"], 0)
            self.assertEqual(snap["time_left_ticks"], 100)

            # Tick 2: vẫn đang pause -> bỏ qua hành động, không tăng sim_tick
            evs = sess.step(_inp(edges=("interact",)))
            self.assertEqual(evs, [])
            snap = sess.snapshot()
            self.assertEqual(snap["tick"], 2)
            self.assertEqual(snap["sim_tick"], 0)
            self.assertEqual(snap["time_left_ticks"], 100)

            # Tick 3: cạnh lên pause lần 2 -> phát resumed và chạy ngay gameplay bước đó
            evs = sess.step(_inp(edges=("pause",)))
            self.assertEqual([e["name"] for e in evs], ["resumed"])
            snap = sess.snapshot()
            self.assertEqual(snap["state"], "playing")
            self.assertEqual(snap["tick"], 3)
            self.assertEqual(snap["sim_tick"], 1)
            self.assertEqual(snap["time_left_ticks"], 99)


class ShopAndDayM4Tests(unittest.TestCase):
    def _enter_shop(self, money=600, earned=600, days=1, seed=1):
        tuning = _tuning_v11()
        sc = {
            "day": {"money": money, "earned": earned},
            "gather": {"hold": ["ca_loc"]},
            "quan": {"time_left_ticks": 1, "random_customers": False},
        }
        sess = Session("day", tuning, sc, seed=seed, days=days)
        # Tick 1: interact tại bến -> gather_end(docked) + phase_start(quan)
        evs1 = sess.step(_inp(edges=("interact",)))
        self.assertEqual([e["name"] for e in evs1], ["gather_end", "phase_start"])
        self.assertEqual(sess.snapshot()["phase"], "quan")
        self.assertEqual(sess.snapshot()["phase_tick"], 0)
        # Tick 2: quan hết giờ -> quan_end + phase_start(shop)
        evs2 = sess.step(_inp())
        self.assertEqual([e["name"] for e in evs2], ["quan_end", "phase_start"])
        self.assertEqual(sess.snapshot()["phase"], "shop")
        self.assertEqual(sess.snapshot()["phase_tick"], 0)
        return sess

    def test_ac_p2_m4_03_pause_in_shop_freezes_timer_and_ignores_buy(self):
        """AC-P2-M4-03: Pause trong Shop đóng băng 600 tick và bỏ qua buy/shop_done."""
        sess = self._enter_shop(money=200, earned=200)
        evs = sess.step(_inp(edges=("pause", "shop_done"), buy="oxygen"))
        self.assertEqual([e["name"] for e in evs], ["paused"])
        self.assertEqual(evs[0]["day"], 1)
        snap = sess.snapshot()
        self.assertEqual(snap["state"], "paused")
        self.assertEqual(snap["time_left_ticks"], 600)
        self.assertEqual(snap["money"], 200)
        # Đang pause: buy bị bỏ qua
        self.assertEqual(sess.step(_inp(buy="oxygen")), [])
        self.assertEqual(sess.snapshot()["time_left_ticks"], 600)
        # Resume + buy ngay bước đó -> phát resumed rồi bought
        evs = sess.step(_inp(edges=("pause",), buy="oxygen"))
        self.assertEqual([e["name"] for e in evs], ["resumed", "bought"])
        self.assertEqual(sess.snapshot()["money"], 0)
        self.assertEqual(sess.snapshot()["time_left_ticks"], 599)

    def test_ac_p2_m4_04_05_06_shop_upgrades_failures_and_closing_order(self):
        """AC-P2-M4-04/05/06: Mua oxygen/hp, giữ earned/score, buy_failed, buy trước shop_done ở bước cuối."""
        sess = self._enter_shop(money=600, earned=600)
        # Mua oxygen cấp 1 (200) -> còn 400, earned vẫn 600
        evs = sess.step(_inp(buy="oxygen"))
        self.assertEqual(evs[0]["name"], "bought")
        self.assertEqual(evs[0]["data"], {"upgrade": "oxygen", "level": 1, "price": 200, "money": 400})
        snap = sess.snapshot()
        self.assertEqual(snap["earned"], 600)
        self.assertEqual(snap["upgrades"], {"oxygen": 1})
        self.assertEqual(snap["active_upgrades"], {})

        # Mua oxygen cấp 2 đúng giá (400) -> còn 0
        evs = sess.step(_inp(buy="oxygen"))
        self.assertEqual(evs[0]["data"], {"upgrade": "oxygen", "level": 2, "price": 400, "money": 0})

        # Đã max level -> buy_failed(max_level)
        evs = sess.step(_inp(buy="oxygen"))
        self.assertEqual(evs[0]["name"], "buy_failed")
        self.assertEqual(evs[0]["data"], {"action": "oxygen", "reason": "max_level"})

        # Thiếu tiền mua hp -> buy_failed(funds)
        evs = sess.step(_inp(buy="hp"))
        self.assertEqual(evs[0]["data"], {"action": "hp", "reason": "funds"})

        # Lệnh lạ -> buy_failed(unknown)
        evs = sess.step(_inp(buy="weapon"))
        self.assertEqual(evs[0]["data"], {"action": "weapon", "reason": "unknown"})

        # Đóng shop bằng shop_done cùng tick với buy (buy xử lý trước shop_done)
        evs = sess.step(_inp(edges=("shop_done",), buy="hp"))
        self.assertEqual([e["name"] for e in evs], ["buy_failed", "shop_end"])
        self.assertEqual(evs[1]["data"], {"reason": "done"})
        self.assertTrue(sess.done)
        end = sess.end_row()
        self.assertEqual(end["reason"], "days_complete")
        self.assertEqual(end["days_completed"], 1)

    def test_ac_p2_m4_06_shop_auto_closes_after_600_ticks(self):
        """AC-P2-M4-06: Shop tự đóng sau đúng 600 tick với shop_end(reason:'time')."""
        sess = self._enter_shop(money=0, earned=0)
        last_evs = []
        for _ in range(600):
            last_evs = sess.step(_inp())
        self.assertEqual([e["name"] for e in last_evs], ["shop_end"])
        self.assertEqual(last_evs[0]["data"], {"reason": "time"})
        self.assertTrue(sess.done)
        self.assertEqual(sess.end_row()["days_completed"], 1)

    def test_ac_p2_m4_07_08_multiday_upgrades_apply_on_day_2_and_clear_stock(self):
        """AC-P2-M4-07/08: Mua oxygen+hp ở Ngày 1 -> có hiệu lực đúng ở Ngày 2 (2700 oxy, 4 HP), bỏ kho dư."""
        sess = self._enter_shop(money=450, earned=450, days=2)
        # Kiểm tra initial_event_rows của Ngày 1
        init = sess.initial_event_rows()
        self.assertEqual([e["name"] for e in init], ["day_start", "day_plan", "phase_start"])
        self.assertEqual(init[1]["data"]["dishes"], {"ca_loc_nuong_trui": 3, "goi_bong_sung": 3})

        # Mua oxygen cấp 1 (200) và hp cấp 1 (250) + shop_done ở bước 2
        sess.step(_inp(buy="oxygen"))
        evs = sess.step(_inp(edges=("shop_done",), buy="hp"))
        self.assertEqual([e["name"] for e in evs], ["bought", "shop_end", "day_start", "day_plan", "phase_start"])
        self.assertEqual(evs[2]["day"], 2)
        self.assertFalse(sess.done)

        snap = sess.snapshot()
        self.assertEqual(snap["day"], 2)
        self.assertEqual(snap["phase"], "gather")
        self.assertEqual(snap["phase_tick"], 0)
        self.assertEqual(snap["active_upgrades"], {"hp": 1, "oxygen": 1})
        self.assertEqual(snap["player"]["oxygen_max_ticks"], 2700)
        self.assertEqual(snap["player"]["oxygen_ticks"], 2700)
        self.assertEqual(snap["player"]["hp_max"], 4)
        self.assertEqual(snap["player"]["hp"], 4)
        self.assertEqual(snap["money"], 0)
        self.assertEqual(snap["earned"], 450)

    def test_ac_p2_m4_09_determinism_and_full_day_performance(self):
        """AC-P2-M4-09: Một Ngày trọn vẹn (≤ 22.200 tick) chạy nhanh << 20 s và tất định từng byte."""
        tuning = _tuning_v11()
        sc = {"gather": {"random_fish": False}, "quan": {"random_customers": False}}
        t0 = time.perf_counter()
        outs = []
        for _ in range(2):
            sess = Session("day", tuning, sc, seed=42, days=1)
            lines = [dumps(r) for r in sess.initial_event_rows()]
            lines.append(dumps(sess.snapshot()))
            while not sess.done:
                for ev in sess.step(_inp()):
                    lines.append(dumps(ev))
            lines.append(dumps(sess.snapshot()))
            lines.append(dumps(sess.end_row()))
            outs.append("\n".join(lines))
        elapsed = time.perf_counter() - t0
        self.assertEqual(outs[0], outs[1])
        self.assertLess(elapsed, 10.0, f"2 lần chạy full day mất {elapsed:.2f}s")


if __name__ == "__main__":
    unittest.main()
