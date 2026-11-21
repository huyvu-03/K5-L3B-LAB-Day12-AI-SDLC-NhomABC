"""Unit & black-box tests cho M4 (D): bếp, bàn, bưng, tiền, tip, uy tín, hết ca (PRD-0 mục D, E, F)."""

import os
import unittest

from chonoi.contract import load_contract
from chonoi.ids import IdAllocator
from chonoi.inputs import InputState
from chonoi.rng import Streams
from chonoi.sim.quan import QuanSim
from helpers import Workdir, events, frames, read_jsonl, run_headless, snapshots, write_json


def _run_quan(w, quan_block, input_frames=(), ticks=10, snapshot_every=1, seed=1):
    sc = write_json(w.path("sc.json"), {"quan": quan_block})
    out = w.path("out.jsonl")
    args = [
        "--mode", "quan", "--seed", str(seed), "--ticks", str(ticks),
        "--scenario", sc, "--snapshot-every", str(snapshot_every), "--out", out,
    ]
    if input_frames:
        inp = write_json(w.path("in.json"), frames(*input_frames))
        args.extend(["--inputs", inp])
    code, err = run_headless(*args)
    return code, err, read_jsonl(out) if code == 0 and os.path.exists(out) else []


class QuanM4BlackBox(unittest.TestCase):
    @unittest.skip("Contract v1.2 breaking change: counting-stock fixture replaced by v1.2 tests (see CHANGELOG.md)")
    def test_ac_m4_01_interact_edge_and_tiebreak_no_fallback(self):
        """AC-M4-01: Đúng mép interact_radius (<=), hòa ưu tiên bếp trước bàn và không fallback khi bận."""
        with Workdir() as w:
            # 1) Đúng mép interact_radius = 1.5 tới B1=[2, 8] về phía tây -> [0.5, 8] (xa B2=[5, 8] ≥ 4.5 m, tránh hòa)
            code, err, rows = _run_quan(
                w,
                {
                    "player": {"pos": [0.5, 8]},
                    "stock": {"ca_loc": 1},
                    "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}],
                    "random_customers": False,
                },
                input_frames=[{"tick": 0, "interact": True}],
                ticks=1,
            )
            self.assertEqual(code, 0, err)
            self.assertEqual(len(events(rows, "cook_started")), 1)

            # 2) Vượt mép (0.49 cách B1=[2, 8] 1.51m và xa B2=[5, 8] 4.51m theo v1.1) -> không tương tác
            code, err, rows = _run_quan(
                w,
                {
                    "player": {"pos": [0.49, 8]},
                    "stock": {"ca_loc": 1},
                    "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}],
                    "random_customers": False,
                },
                input_frames=[{"tick": 0, "interact": True}],
                ticks=1,
            )
            self.assertEqual(code, 0, err)
            self.assertEqual(len(events(rows, "cook_started")), 0)

            # 3) Cách đều B1=[4, 5] và T1=[6, 5] từ [5, 5] (dist = 1.0):
            # B1 idle nhưng không có đơn reserved -> không tương tác được; ưu tiên bếp trước bàn và KHÔNG fallback sang T1.
            dish = {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60}
            code, err, rows = _run_quan(
                w,
                {
                    "player": {"pos": [5, 5]},
                    "stoves": [{"id": "B1", "pos": [4, 5]}],
                    "tables": [{"id": "T1", "pos": [6, 5]}],
                    "hand": dish,
                    "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                   "order_status": "assigned"}],
                    "random_customers": False,
                },
                input_frames=[{"tick": 0, "interact": True}],
                ticks=1,
            )
            self.assertEqual(code, 0, err)
            self.assertEqual(len(events(rows, "served")), 0)

            # 4) Gần T1 hơn ([5.1, 5], dist T1=0.9 < dist B1=1.1) -> phục vụ thành công
            code, err, rows = _run_quan(
                w,
                {
                    "player": {"pos": [5.1, 5]},
                    "stoves": [{"id": "B1", "pos": [4, 5]}],
                    "tables": [{"id": "T1", "pos": [6, 5]}],
                    "hand": dish,
                    "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                   "order_status": "assigned"}],
                    "random_customers": False,
                },
                input_frames=[{"tick": 0, "interact": True}],
                ticks=1,
            )
            self.assertEqual(code, 0, err)
            self.assertEqual(len(events(rows, "served")), 1)

    @unittest.skip("Contract v1.2 breaking change: counting-stock fixture replaced by v1.2 tests (see CHANGELOG.md)")
    def test_ac_m4_02_cook_started_consumes_stock_and_sorts_items(self):
        """AC-M4-02: Bắt đầu nấu trừ đúng kho, items sắp theo kind, khách sang assigned và nhả reserved."""
        with Workdir() as w:
            code, err, rows = _run_quan(
                w,
                {
                    "player": {"pos": [2, 8]},
                    "stock": {"ca_linh": 3, "bong_dien_dien": 1, "ca_loc": 2},
                    "customers": [{"id": "C1", "table_id": "T1", "dish_id": "lau_ca_linh_dien_dien"}],
                    "random_customers": False,
                },
                input_frames=[{"tick": 0, "interact": True}],
                ticks=1,
            )
            self.assertEqual(code, 0, err)
            evs = events(rows, "cook_started")
            self.assertEqual(len(evs), 1)
            self.assertEqual(evs[0]["tick"], 1)
            self.assertEqual(evs[0]["data"], {
                "stove_id": "B1",
                "order_id": "C1",
                "dish_id": "lau_ca_linh_dien_dien",
                "items": ["bong_dien_dien", "ca_linh", "ca_linh", "ca_linh"],
                "base_price": 120,
            })
            snap1 = snapshots(rows)[-1]
            self.assertEqual(snap1["stock"], {"ca_loc": 2})
            self.assertEqual(snap1["stoves"][0]["state"], "cooking")
            self.assertEqual(snap1["stoves"][0]["cook_ticks_left"], 600)
            self.assertEqual(snap1["stoves"][0]["ready_ticks"], 0)
            self.assertEqual(snap1["stoves"][0]["dish"], {
                "order_id": "C1", "dish_id": "lau_ca_linh_dien_dien", "base_price": 120,
            })
            self.assertEqual(snap1["customers"][0]["order_status"], "assigned")
            self.assertEqual(snap1["customers"][0]["reserved"], {})

    def test_ac_m4_03_dish_ready_and_ready_ticks_increment(self):
        """AC-M4-03: Món chín đúng tick về 0 với ready_ticks=0, chỉ tăng ready_ticks từ tick sau, không cháy."""
        dish = {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60}
        with Workdir() as w:
            code, err, rows = _run_quan(
                w,
                {
                    "stoves": [{"id": "B1", "state": "cooking", "dish": dish, "cook_ticks_left": 3}],
                    "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                   "order_status": "assigned"}],
                    "random_customers": False,
                },
                ticks=6,
                snapshot_every=1,
            )
            self.assertEqual(code, 0, err)
            evs = events(rows, "dish_ready")
            self.assertEqual(len(evs), 1)
            self.assertEqual(evs[0]["tick"], 3)
            self.assertEqual(evs[0]["data"], {
                "stove_id": "B1", "order_id": "C1", "dish_id": "ca_loc_nuong_trui",
            })
            by_tick = {s["tick"]: s["stoves"][0] for s in snapshots(rows)}
            self.assertEqual(by_tick[2]["state"], "cooking")
            self.assertEqual(by_tick[2]["cook_ticks_left"], 1)
            self.assertEqual(by_tick[3]["state"], "ready")
            self.assertEqual(by_tick[3]["cook_ticks_left"], 0)
            self.assertEqual(by_tick[3]["ready_ticks"], 0)
            self.assertEqual(by_tick[4]["ready_ticks"], 1)
            self.assertEqual(by_tick[6]["ready_ticks"], 3)
            self.assertEqual(by_tick[6]["state"], "ready")

    def test_ac_m4_04_dish_picked_moves_to_hand_and_resets_stove(self):
        """AC-M4-04: Bưng món từ bếp ready lên hand khi tay trống, bếp về idle."""
        dish = {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60}
        with Workdir() as w:
            code, err, rows = _run_quan(
                w,
                {
                    "player": {"pos": [2, 8]},
                    "stoves": [{"id": "B1", "state": "ready", "dish": dish, "ready_ticks": 5}],
                    "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                                   "order_status": "assigned"}],
                    "random_customers": False,
                },
                input_frames=[{"tick": 0, "interact": True}],
                ticks=1,
            )
            self.assertEqual(code, 0, err)
            evs = events(rows, "dish_picked")
            self.assertEqual(len(evs), 1)
            self.assertEqual(evs[0]["data"], {
                "stove_id": "B1", "order_id": "C1", "dish_id": "ca_loc_nuong_trui",
            })
            snap1 = snapshots(rows)[-1]
            self.assertEqual(snap1["hand"], dish)
            self.assertEqual(snap1["stoves"][0]["state"], "idle")
            self.assertIsNone(snap1["stoves"][0]["dish"])
            self.assertEqual(snap1["stoves"][0]["ready_ticks"], 0)

    def test_ac_m4_05_served_tip_boundary_and_zero_patience_tick(self):
        """AC-M4-05: Tip đạt đúng biên 50% sau Bước 1, thiếu 1 tick -> tip 0, phục vụ đúng tick patience=0 vẫn hợp lệ."""
        dish = {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60}
        cases = [
            # patience ban đầu -> patience sau Bước 1 -> tip kỳ vọng
            (1801, 1800, 12),  # 1800 / 3600 == 0.5 -> có tip = floor(60 * 0.2) = 12
            (1800, 1799, 0),   # 1799 / 3600 < 0.5 -> tip = 0
            (1, 0, 0),         # đúng tick patience về 0 vẫn phục vụ hợp lệ
        ]
        for start_pat, want_pat, want_tip in cases:
            with Workdir() as w:
                code, err, rows = _run_quan(
                    w,
                    {
                        "player": {"pos": [9, 2]},
                        "hand": dish,
                        "customers": [{
                            "id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                            "order_status": "assigned", "patience_ticks_left": start_pat,
                        }],
                        "random_customers": False,
                    },
                    input_frames=[{"tick": 0, "interact": True}],
                    ticks=1,
                )
                self.assertEqual(code, 0, err)
                evs = events(rows, "served")
                self.assertEqual(len(evs), 1, start_pat)
                self.assertEqual(evs[0]["data"], {
                    "order_id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                    "patience_ticks_left": want_pat, "base_price": 60, "tip": want_tip,
                })
                self.assertEqual(len(events(rows, "customer_left")), 0)
                snap1 = snapshots(rows)[-1]
                self.assertIsNone(snap1["hand"])
                c = snap1["customers"][0]
                self.assertEqual(c["state"], "eating")
                self.assertEqual(c["order_status"], "served")
                self.assertEqual(c["eat_ticks_left"], 600)
                self.assertEqual(c["base_price"], 60)
                self.assertEqual(c["tip"], want_tip)

    def test_ac_m4_06_paid_finished_eating_reputation_clamp_and_score(self):
        """AC-M4-06: Ăn xong trả tiền, tip > 0 cộng tip_reputation (kẹp trần 5.0), tip = 0 giữ nguyên uy tín."""
        with Workdir() as w:
            # Có tip -> cộng tip_reputation = 0.2 và kẹp trần 5.0
            code, err, rows = _run_quan(
                w,
                {
                    "reputation": 4.9,
                    "customers": [{
                        "id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                        "state": "eating", "order_status": "served", "eat_ticks_left": 2,
                        "base_price": 60, "tip": 12,
                    }],
                    "random_customers": False,
                },
                ticks=2,
            )
            self.assertEqual(code, 0, err)
            evs = events(rows, "paid")
            self.assertEqual(len(evs), 1)
            self.assertEqual(evs[0]["tick"], 2)
            self.assertEqual(evs[0]["data"], {
                "order_id": "C1", "table_id": "T1", "base_price": 60,
                "tip": 12, "amount": 72, "reason": "finished_eating",
            })
            snap2 = snapshots(rows)[-1]
            self.assertEqual(snap2["money"], 72)
            self.assertEqual(snap2["earned"], 72)
            self.assertEqual(snap2["reputation"], 5.0)
            self.assertEqual(snap2["score"], 572)
            self.assertEqual(snap2["customers"], [])
            self.assertIsNone(snap2["tables"][0]["customer_id"])

            # Không tip -> uy tín không đổi
            code, err, rows = _run_quan(
                w,
                {
                    "reputation": 3.0,
                    "customers": [{
                        "id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                        "state": "eating", "order_status": "served", "eat_ticks_left": 1,
                        "base_price": 60, "tip": 0,
                    }],
                    "random_customers": False,
                },
                ticks=1,
            )
            self.assertEqual(code, 0, err)
            snap1 = snapshots(rows)[-1]
            self.assertEqual(snap1["money"], 60)
            self.assertEqual(snap1["reputation"], 3.0)
            self.assertEqual(snap1["score"], 360)

    def test_ac_m4_07_closing_served_at_last_tick_and_waiting_no_penalty(self):
        """AC-M4-07: Hết ca — khách vừa được phục vụ ở tick cuối vẫn paid(closing); khách chờ rời closing không trừ uy tín."""
        dish = {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60}
        with Workdir() as w:
            # 1) Phục vụ đúng tick cuối ca (time_left_ticks = 1)
            code, err, rows = _run_quan(
                w,
                {
                    "player": {"pos": [9, 2]},
                    "hand": dish,
                    "time_left_ticks": 1,
                    "customers": [{
                        "id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                        "order_status": "assigned", "patience_ticks_left": 3000,
                    }],
                    "random_customers": False,
                },
                input_frames=[{"tick": 0, "interact": True}],
                ticks=5,
            )
            self.assertEqual(code, 0, err)
            ev_names = [e["name"] for e in events(rows)]
            self.assertEqual(ev_names, ["served", "paid", "quan_end"])
            self.assertEqual(events(rows, "paid")[0]["data"]["reason"], "closing")
            self.assertEqual(events(rows, "quan_end")[0]["data"], {
                "reason": "time", "money": 72, "earned": 72, "shift_earned": 72, "reputation": 3.2,
            })
            self.assertEqual(rows[-1]["reason"], "time")
            self.assertEqual(rows[-1]["score"], 372)

            # 2) Khách waiting + món đang nấu trên bếp khi hết ca -> closing không trừ uy tín và hủy món trên bếp
            code, err, rows = _run_quan(
                w,
                {
                    "time_left_ticks": 1,
                    "reputation": 3.0,
                    "stoves": [{"id": "B1", "state": "cooking", "dish": dish, "cook_ticks_left": 100}],
                    "customers": [{
                        "id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                        "order_status": "assigned",
                    }],
                    "random_customers": False,
                },
                ticks=5,
            )
            self.assertEqual(code, 0, err)
            ev_names = [e["name"] for e in events(rows)]
            self.assertEqual(ev_names, ["customer_left", "quan_end"])
            self.assertEqual(events(rows, "customer_left")[0]["data"], {
                "order_id": "C1", "table_id": "T1", "reason": "closing", "reputation": 3.0,
            })
            snap1 = snapshots(rows)[-1]
            self.assertEqual(snap1["customers"], [])
            self.assertEqual(snap1["stoves"][0]["state"], "idle")
            self.assertIsNone(snap1["stoves"][0]["dish"])

    def test_ac_m4_08_patience_leave_cleans_stove_and_hand_no_refund(self):
        """AC-M4-08: Khách hết kiên nhẫn rời đi hủy món đang nấu/ready hoặc trên hand, không hoàn kho, kẹp uy tín >= 0."""
        dish = {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60}
        with Workdir() as w:
            # 1) Món đang nấu trên bếp
            code, err, rows = _run_quan(
                w,
                {
                    "reputation": 3.0,
                    "stoves": [{"id": "B1", "state": "cooking", "dish": dish, "cook_ticks_left": 100}],
                    "customers": [{
                        "id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                        "order_status": "assigned", "patience_ticks_left": 1,
                    }],
                    "random_customers": False,
                },
                ticks=2,
            )
            self.assertEqual(code, 0, err)
            evs = events(rows, "customer_left")
            self.assertEqual(len(evs), 1)
            self.assertEqual(evs[0]["tick"], 1)
            self.assertEqual(evs[0]["data"], {
                "order_id": "C1", "table_id": "T1", "reason": "patience", "reputation": 2.5,
            })
            snap = snapshots(rows)[-1]
            self.assertEqual(snap["customers"], [])
            self.assertEqual(snap["stoves"][0]["state"], "idle")
            self.assertIsNone(snap["stoves"][0]["dish"])
            self.assertEqual(snap["stoves"][0]["cook_ticks_left"], 0)
            self.assertEqual(snap["stock"], {})

            # 2) Món đang trên tay + kiểm kẹp uy tín sàn 0.0
            code, err, rows = _run_quan(
                w,
                {
                    "reputation": 0.2,
                    "hand": dish,
                    "customers": [{
                        "id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui",
                        "order_status": "assigned", "patience_ticks_left": 1,
                    }],
                    "random_customers": False,
                },
                ticks=1,
            )
            self.assertEqual(code, 0, err)
            self.assertEqual(events(rows, "customer_left")[0]["data"]["reputation"], 0.0)
            snap = snapshots(rows)[-1]
            self.assertIsNone(snap["hand"])
            self.assertEqual(snap["customers"], [])

    @unittest.skip("Contract v1.2 breaking change: counting-stock fixture replaced by v1.2 tests (see CHANGELOG.md)")
    def test_full_kitchen_loop_and_determinism(self):
        """Vòng đầy đủ: nấu -> chín -> bưng -> phục vụ -> ăn xong trả tiền, cùng seed giống từng byte."""
        with Workdir() as w:
            scenario = {
                "player": {"pos": [2, 8]},
                "tables": [{"id": "T1", "pos": [3.5, 8]}],
                "stock": {"ca_loc": 1},
                "customers": [{"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}],
                "random_customers": False,
            }
            # tick 0: interact B1 (nấu 360 tick, chín tại tick 361)
            # tick 361: interact B1 (bưng món lên tay; player ở [2, 8] cách B1=0, T1=1.5)
            # tick 362: di chuyển sang phải nhẹ? Thực tế player tại [3, 8] gần T1 hơn; đặt move [1, 0] 20 tick rồi interact T1.
            in_frames = [
                {"tick": 0, "interact": True},
                {"tick": 1, "interact": False},
                {"tick": 361, "interact": True},
                {"tick": 362, "interact": False, "move": [1, 0]},
                {"tick": 382, "move": [0, 0], "interact": True},
                {"tick": 383, "interact": False},
            ]
            sc = write_json(w.path("sc.json"), {"quan": scenario})
            inp = write_json(w.path("in.json"), frames(*in_frames))
            outs = []
            for i in (1, 2):
                out = w.path(f"run{i}.jsonl")
                code, err = run_headless(
                    "--mode", "quan", "--seed", "99", "--ticks", "1050",
                    "--scenario", sc, "--inputs", inp, "--out", out,
                )
                self.assertEqual(code, 0, err)
                outs.append(out)
            with open(outs[0], "rb") as a, open(outs[1], "rb") as b:
                self.assertEqual(a.read(), b.read())
            rows = read_jsonl(outs[0])
            self.assertEqual(
                [e["name"] for e in events(rows)],
                ["cook_started", "dish_ready", "dish_picked", "served", "paid"],
            )
            self.assertEqual(rows[-1]["money"], 72)
            self.assertEqual(rows[-1]["reputation"], 3.2)

    @unittest.skip("Contract v1.2 breaking change: counting-stock fixture replaced by v1.2 tests (see CHANGELOG.md)")
    def test_m3_m4_integrated_spawn_cook_serve_pay_loop(self):
        """Ghép M3 ↔ M4: khách tự sinh (customer_arrived) -> nấu -> chín -> bưng -> phục vụ -> ăn xong -> paid."""
        with Workdir() as w:
            scenario = {
                "player": {"pos": [2, 8]},
                "tables": [{"id": "T1", "pos": [3.5, 8]}],
                "stock": {"ca_loc": 1},
                "random_customers": True,
            }
            # tick 120: khách K1 tự sinh (first_customer_tick = 120), gọi ca_loc_nuong_trui (duy nhất đủ kho)
            # tick 121: interact B1 -> cook_started (cook_s=6 -> 360 tick, chín ở tick 482)
            # tick 482: interact B1 -> dish_picked
            # tick 483..503: đi sang phải gần T1 -> interact T1 -> served (eat_s=10 -> 600 tick)
            in_frames = [
                {"tick": 121, "interact": True},
                {"tick": 122, "interact": False},
                {"tick": 482, "interact": True},
                {"tick": 483, "interact": False, "move": [1, 0]},
                {"tick": 503, "move": [0, 0], "interact": True},
                {"tick": 504, "interact": False},
            ]
            code, err, rows = _run_quan(w, scenario, input_frames=in_frames, ticks=1200, snapshot_every=10, seed=7)
            self.assertEqual(code, 0, err)
            ev_names = [e["name"] for e in events(rows)]
            for required in ("customer_arrived", "cook_started", "dish_ready", "dish_picked", "served", "paid"):
                self.assertIn(required, ev_names, ev_names)
            idx = [ev_names.index(n) for n in ("customer_arrived", "cook_started", "dish_ready", "dish_picked", "served", "paid")]
            self.assertEqual(idx, sorted(idx), ev_names)
            self.assertEqual(rows[-1]["money"], 72)
            self.assertEqual(rows[-1]["reputation"], 3.2)


class QuanM4UnitEdges(unittest.TestCase):
    """Kiểm các luật đa bàn/đa bếp bằng QuanSim trực tiếp (vẫn giữ tuning chuẩn ở contract)."""

    def _make_multi_sim(self, scenario):
        tuning = load_contract()["tuning"]
        tuning = {
            **tuning,
            "quan": {
                **tuning["quan"],
                "stoves": [{"id": "B1", "pos": [2, 8]}, {"id": "B2", "pos": [4, 8]}],
                "tables": [{"id": "T2", "pos": [9, 2]}, {"id": "T10", "pos": [11, 2]}],
            },
        }
        return QuanSim(tuning, scenario, Streams(1), IdAllocator())

    def test_cook_picks_oldest_order_tick_then_table_id_key(self):
        """Đơn reserved cũ nhất chọn theo (order_tick, id_key(table_id)): T2 đứng trước T10."""
        sim = self._make_multi_sim({
            "player": {"pos": [2, 8]},
            "stock": {"ca_loc": 2},
            "customers": [
                {"id": "C1", "table_id": "T10", "dish_id": "ca_loc_nuong_trui", "order_tick": 5},
                {"id": "C2", "table_id": "T2", "dish_id": "ca_loc_nuong_trui", "order_tick": 5},
            ],
            "random_customers": False,
        })
        evs = sim.step(InputState((0.0, 0.0), {"interact": True}, {"interact"}))
        cook_evs = [d for n, d in evs if n == "cook_started"]
        self.assertEqual(len(cook_evs), 1)
        self.assertEqual(cook_evs[0]["order_id"], "C2")

    def test_carry_limit_blocks_pick_and_wrong_order_id_blocks_serve(self):
        """Tay đang cầm món không bưng thêm được; đưa sai order_id cho bàn bị bỏ qua."""
        dish_c1 = {"order_id": "C1", "dish_id": "ca_loc_nuong_trui", "base_price": 60}
        dish_c2 = {"order_id": "C2", "dish_id": "ca_loc_nuong_trui", "base_price": 60}
        sim = self._make_multi_sim({
            "player": {"pos": [2, 8]},
            "hand": dish_c1,
            "stoves": [{"id": "B1", "state": "ready", "dish": dish_c2, "ready_ticks": 1}],
            "customers": [
                {"id": "C1", "table_id": "T2", "dish_id": "ca_loc_nuong_trui", "order_status": "assigned"},
                {"id": "C2", "table_id": "T10", "dish_id": "ca_loc_nuong_trui", "order_status": "assigned"},
            ],
            "random_customers": False,
        })
        # Tay đang cầm C1 -> không bưng thêm C2 từ B1
        evs = sim.step(InputState((0.0, 0.0), {"interact": True}, {"interact"}))
        self.assertEqual([n for n, _ in evs if n == "dish_picked"], [])
        self.assertEqual(sim.stoves[0]["state"], "ready")

        # Đứng cạnh T10 (của C2) nhưng tay cầm C1 -> không phục vụ được
        sim.pos = [11.0, 2.0]
        evs = sim.step(InputState((0.0, 0.0), {"interact": True}, {"interact"}))
        self.assertEqual([n for n, _ in evs if n == "served"], [])
        self.assertEqual(sim.hand, dish_c1)


if __name__ == "__main__":
    unittest.main()
