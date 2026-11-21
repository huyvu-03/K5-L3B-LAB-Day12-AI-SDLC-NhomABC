"""M3.4 — Ghép khách (M3) ↔ bếp/tiền (M4), nhìn từ phía vòng đời khách và kho.

Vòng đầy đủ do M4 đã kiểm ở test_quan_m4.test_m3_m4_integrated_spawn_cook_serve_pay_loop; ở đây thêm
các điểm ghép chỉ lộ ra khi chạy nhiều lượt khách: tồn kho sau khi nấu, giữ chỗ lượt sau, bàn được trả lại.
"""

import unittest

from helpers import Workdir, events, read_jsonl, run_headless, snapshots, write_json

CA_LOC = "ca_loc_nuong_trui"
# Cùng kịch bản người chơi với test M4: bếp B1 (2,8), bàn T1 dời sát bếp để khỏi phải đi xa.
FRAMES = [
    {"tick": 121, "interact": True}, {"tick": 122, "interact": False},          # cook_started
    {"tick": 482, "interact": True},                                              # dish_picked
    {"tick": 483, "interact": False, "move": [1, 0]},
    {"tick": 503, "move": [0, 0], "interact": True}, {"tick": 504, "interact": False},  # served
]


def run_cycle(w, stock, ticks, seed=7):
    sc = write_json(w.path("sc.json"), {"quan": {"player": {"pos": [2, 8]},
                                                  "tables": [{"id": "T1", "pos": [3.5, 8]}],
                                                  "stock": stock}})
    inp = write_json(w.path("in.json"), {"frames": FRAMES})
    code, err = run_headless("--mode", "quan", "--seed", str(seed), "--scenario", sc, "--inputs", inp,
                             "--ticks", str(ticks), "--out", w.path("o.jsonl"), "--snapshot-every", "10")
    assert code == 0, err
    return read_jsonl(w.path("o.jsonl"))


class CustomerKitchenIntegration(unittest.TestCase):
    @unittest.skip("Contract v1.2 breaking change: counting-stock fixture replaced by v1.2 tests (see CHANGELOG.md)")
    def test_stock_is_consumed_once_and_next_round_sees_empty_stock(self):
        with Workdir() as w:
            rows = run_cycle(w, {"ca_loc": 1}, 1930)
            names = [(e["tick"], e["name"]) for e in events(rows)]
            self.assertEqual([n for _, n in names if n != "no_dish"],  # no_dish xen vào giữa vòng nấu (v1.1: 4 bàn)
                             ["customer_arrived", "cook_started", "dish_ready", "dish_picked", "served", "paid"])
            cook = events(rows, "cook_started")[0]
            self.assertEqual(cook["data"]["items"], ["ca_loc"])
            # nguyên liệu đã dùng không hoàn lại -> kho rỗng; v1.1 có 4 bàn nên mọi lượt sau đều có bàn mà hết món
            self.assertEqual(snapshots(rows)[-1]["stock"], {})
            self.assertEqual([e["tick"] for e in events(rows, "no_dish")], [1020, 1920])
            self.assertEqual(len(events(rows, "customer_arrived")), 1)

    @unittest.skip("Contract v1.2 breaking change: counting-stock fixture replaced by v1.2 tests (see CHANGELOG.md)")
    def test_second_customer_takes_next_free_table_and_holds_leftover_stock(self):  # v1.1: 4 bàn
        with Workdir() as w:
            rows = run_cycle(w, {"ca_loc": 2}, 1930)
            arr = events(rows, "customer_arrived")
            self.assertEqual([(e["tick"], e["data"]["order_id"], e["data"]["table_id"]) for e in arr],
                             [(120, "K1", "T1"), (1020, "K2", "T2")])
            self.assertEqual(events(rows, "paid")[0]["data"]["order_id"], "K1")
            k2 = next(c for c in snapshots(rows)[-1]["customers"] if c["id"] == "K2")
            self.assertEqual((k2["state"], k2["order_status"], k2["reserved"]), ("waiting", "reserved", {"ca_loc": 1}))
            self.assertEqual(snapshots(rows)[-1]["stock"], {"ca_loc": 1})  # tồn còn 1 và đang được K2 giữ
            self.assertEqual([e["tick"] for e in events(rows, "no_dish")], [1920])  # K2 giữ hết, lượt 1920 không còn món

    @unittest.skip("Contract v1.2 breaking change: counting-stock fixture replaced by v1.2 tests (see CHANGELOG.md)")
    def test_served_customer_never_penalised_and_score_matches_formula(self):
        with Workdir() as w:
            rows = run_cycle(w, {"ca_loc": 1}, 1300)
            self.assertEqual(events(rows, "customer_left"), [])
            end = rows[-1]
            self.assertEqual((end["money"], end["earned"], end["reputation"]), (72, 72, 3.2))
            self.assertEqual(end["score"], 72 + 100 * 3)

    @unittest.skip("Contract v1.2 breaking change: counting-stock fixture replaced by v1.2 tests (see CHANGELOG.md)")
    def test_full_cycle_is_deterministic(self):
        with Workdir() as w:
            run_cycle(w, {"ca_loc": 2, "bong_sung": 2}, 2000, seed=11)
            with open(w.path("o.jsonl"), "rb") as f:
                first = f.read()
            run_cycle(w, {"ca_loc": 2, "bong_sung": 2}, 2000, seed=11)
            with open(w.path("o.jsonl"), "rb") as f:
                self.assertEqual(first, f.read())


if __name__ == "__main__":
    unittest.main()
