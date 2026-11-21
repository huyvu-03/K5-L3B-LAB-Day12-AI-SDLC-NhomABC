"""Buổi tối — Mở Quán. KHUNG + M3 (Khách) + M4 (Bếp, Bàn, Bưng, Tiền, Tip, Uy tín, Hết ca).

Phân chia module (PRD-0 mục F, Quán):
  - M3 (`quan_customers.py` / `CustomerMixin`): dựng khách từ scenario, giữ chỗ, kiên nhẫn,
    khách đến theo lịch (`customer_arrived`, `no_dish`), khách rời (`customer_left`).
  - M4 (`quan.py`): interact tại bếp/bàn (`cook_started`, `dish_ready`, `dish_picked`, `served`),
    ăn xong trả tiền (`paid`), boa, uy tín, dọn món mồ côi, hết ca (`quan_end`).
"""

import math

from ..freshness import calc_fresh_base_price
from ..ids import id_key, sort_by_id
from .quan_customers import CustomerMixin
from .quan_fresh import FreshStockMixin
from .ramp import ramp_velocity

TICK = 60.0


class QuanSim(CustomerMixin, FreshStockMixin):
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, inventory=None, allowed_dishes=None):
        t = tuning["quan"]
        self.t = t
        self.menu = tuning["menu"]
        self.rng = streams
        self.ids = ids
        p = scenario.get("player", {})
        self.pos = [float(c) for c in p.get("pos", t["start_pos"])]
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        # kho: --inventory HOẶC scenario.stock (cả hai -> cli đã báo mã 2)
        # v1.2: kho là mảng cá thể {id, kind, fresh}; v1.0/v1.1: object đếm (M3: quan_fresh.py)
        self._init_stock(inventory if inventory is not None else scenario.get("stock", {}), tuning)
        if self.item_mode:
            for it in self.stock:
                ids.reserve(it["id"])
        hand = scenario.get("hand")
        self.hand = dict(hand) if hand is not None else None
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * 60)))
        self.reputation = float(scenario.get("reputation", t["reputation_initial"]))
        self.stoves = [
            dict(
                s,
                state=s.get("state", "idle"),
                dish=dict(s["dish"]) if s.get("dish") is not None else None,
                cook_ticks_left=s.get("cook_ticks_left", 0),
                ready_ticks=s.get("ready_ticks", 0),
            )
            for s in self._merge(t["stoves"], scenario.get("stoves", []))
        ]
        self.tables = self._merge(t["tables"], scenario.get("tables", []))
        self._init_customers(scenario, allowed_dishes)  # M3: khách dựng sẵn từ scenario + giữ chỗ (quan_customers.py)
        self.money = 0
        self.earned = 0
        self.shift_earned = 0
        self.done = False
        self.reason = None

    @staticmethod
    def _merge(defaults, updates):
        by_id = {d["id"]: dict(d) for d in defaults}
        for u in updates:
            if u["id"] not in by_id:
                from ..errors import BadInput
                raise BadInput(f"id bếp/bàn không tồn tại: {u['id']}")
            by_id[u["id"]].update(u)
        return sort_by_id(list(by_id.values()))

    def snapshot(self) -> dict:
        occupied = {c["table_id"]: c["id"] for c in self.customers}
        return {
            "player": {"pos": self.pos},
            "stock": self._stock_snapshot(),
            "hand": self.hand,
            "stoves": [{k: s.get(k) for k in ("id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks")}
                       for s in self.stoves],
            "tables": [{"id": tb["id"], "pos": tb["pos"], "customer_id": occupied.get(tb["id"])} for tb in self.tables],
            "customers": self._customers_snapshot(),
        }

    def step(self, inp):
        events = []
        # Bước 1: đồng hồ, giảm timer ca, bếp (ready_ticks chỉ tăng cho món đã ready đầu bước), ăn, kiên nhẫn.
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self.phase_tick += 1
        self._tick_stove_timers()
        self._tick_customer_timers()  # M3
        self._decay_stock(events)  # M3 (v1.2): hao tươi kho thô, spoiled theo id, giữ lại 1 lần
        # Bước 2: xét bếp theo id — món nấu xong chuyển ready với ready_ticks = 0.
        self._tick_stoves(events)
        # Bước 3: di chuyển rồi xét tối đa một interact theo (khoảng cách, bếp trước bàn, id).
        self._move(inp)
        if inp.pressed("interact"):
            self._try_interact(events)
        # Bước 4: khách ăn xong trả tiền, khách hết kiên nhẫn rời đi, hoặc dọn cuối ca + quan_end.
        closing = self.time_left_ticks <= 0
        self._resolve_customers(events, closing)  # M3 + M4 hooks (_pay_customer, _release_order)
        # Bước 5: nếu còn giờ, sinh khách mới theo lịch (first_customer_tick, customer_interval_s).
        if not closing:
            self._spawn_customer(events)  # M3
        if closing:
            self.done = True
            self.reason = "time"
            events.append(("quan_end", {
                "reason": "time",
                "money": self.money,
                "earned": self.earned,
                "shift_earned": self.shift_earned,
                "reputation": self.reputation,
            }))
        return events

    # ---- M4: bếp, bưng, phục vụ, tiền & uy tín ---------------------------------------------------
    def _tick_stove_timers(self):
        for s in self.stoves:
            if s["state"] == "ready":
                s["ready_ticks"] += 1
            elif s["state"] == "cooking":
                s["cook_ticks_left"] = max(0, s["cook_ticks_left"] - 1)

    def _tick_stoves(self, events):
        for s in self.stoves:
            if s["state"] == "cooking" and s["cook_ticks_left"] == 0:
                s["state"] = "ready"
                s["ready_ticks"] = 0
                dish = s["dish"]
                events.append(("dish_ready", {
                    "stove_id": s["id"],
                    "order_id": dish["order_id"],
                    "dish_id": dish["dish_id"],
                }))

    def _try_interact(self, events):
        radius = self.t["interact_radius"]
        candidates = []
        for s in self.stoves:
            d = math.dist(self.pos, s["pos"])
            if d <= radius:
                candidates.append(((d, 0, id_key(s["id"])), "stove", s))
        for tb in self.tables:
            d = math.dist(self.pos, tb["pos"])
            if d <= radius:
                candidates.append(((d, 1, id_key(tb["id"])), "table", tb))
        if not candidates:
            return
        _, kind, target = min(candidates, key=lambda x: x[0])
        if kind == "stove":
            if target["state"] == "idle":
                self._cook_on_stove(target, events)
            elif target["state"] == "ready":
                self._pick_from_stove(target, events)
        else:
            self._serve_table(target, events)

    def _cook_on_stove(self, stove, events):
        reserved_orders = [
            c for c in self.customers
            if c["state"] == "waiting" and c["order_status"] == "reserved"
        ]
        if not reserved_orders:
            return
        cust = min(reserved_orders, key=lambda c: (c["order_tick"], id_key(c["table_id"])))
        dish_id = cust["dish_id"]
        spec = self.menu[dish_id]
        if self.item_mode:
            # v1.2: tiêu đúng các id cá thể đang giữ (M3 `_consume_reserved`), chốt giá theo avg_fresh nguyên (scale 240)
            taken = self._consume_reserved(cust)
            base_price = calc_fresh_base_price(spec["price"], [it["units"] for it in taken])
            items = [{"id": it["id"], "kind": it["kind"], "fresh": it["fresh"]} for it in taken]
        else:
            items = []
            for k in sorted(cust["reserved"]):
                qty = cust["reserved"][k]
                if qty > 0:
                    self.stock[k] = self.stock.get(k, 0) - qty
                    if self.stock[k] <= 0:
                        self.stock.pop(k, None)
                    items.extend([k] * qty)
            cust["reserved"] = {}
            base_price = spec["price"]
        cust["order_status"] = "assigned"
        stove["state"] = "cooking"
        stove["dish"] = {"order_id": cust["id"], "dish_id": dish_id, "base_price": base_price}
        stove["cook_ticks_left"] = int(round(spec["cook_s"] * 60))
        stove["ready_ticks"] = 0
        events.append(("cook_started", {
            "stove_id": stove["id"],
            "order_id": cust["id"],
            "dish_id": dish_id,
            "items": items,
            "base_price": base_price,
        }))

    def _pick_from_stove(self, stove, events):
        if self.hand is not None or self.t.get("carry_limit", 1) < 1:
            return
        dish = stove["dish"]
        self.hand = dish
        stove["state"] = "idle"
        stove["dish"] = None
        stove["cook_ticks_left"] = 0
        stove["ready_ticks"] = 0
        events.append(("dish_picked", {
            "stove_id": stove["id"],
            "order_id": dish["order_id"],
            "dish_id": dish["dish_id"],
        }))

    def _serve_table(self, table, events):
        if self.hand is None:
            return
        cust = next((c for c in self.customers if c["table_id"] == table["id"]), None)
        if cust is None or cust["state"] != "waiting" or cust["id"] != self.hand["order_id"]:
            return
        base_price = self.hand["base_price"]
        patience_max = int(round(self.t["patience_s"] * 60))
        ratio = cust["patience_ticks_left"] / patience_max if patience_max > 0 else 0.0
        if ratio + 1e-12 >= self.t["tip_min_patience_ratio"]:
            tip = math.floor(base_price * self.t["tip_rate"] + 1e-12)
        else:
            tip = 0
        cust["state"] = "eating"
        cust["order_status"] = "served"
        cust["eat_ticks_left"] = int(round(self.t["eat_s"] * 60))
        cust["base_price"] = base_price
        cust["tip"] = tip
        self.hand = None
        events.append(("served", {
            "order_id": cust["id"],
            "table_id": table["id"],
            "dish_id": cust["dish_id"],
            "patience_ticks_left": cust["patience_ticks_left"],
            "base_price": base_price,
            "tip": tip,
        }))

    def _clamp_rep(self, v):
        lo = float(self.t["reputation_min"])
        hi = float(self.t["reputation_max"])
        return max(lo, min(hi, round(v, 10)))

    def _move(self, inp):
        speed = self.t["walk_speed"]
        mx, mz = inp.move
        self.vel = ramp_velocity(self, (mx * speed, mz * speed), int(self.t.get("ramp_max_ticks", 6)))
        b = self.t["bounds"]
        for i, axis in enumerate(("x", "z")):
            self.pos[i] += self.vel[i] / TICK
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i], self.vel[i] = lo, max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i], self.vel[i] = hi, min(0.0, self.vel[i])
