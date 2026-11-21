"""P2-M4.3a — Shop cuối ngày (Ticket02 / Test Contract v1.1).

Đọc bảng nâng cấp (`oxygen`, `hp`, ...) và `max_ticks` (600) từ `tuning["shop"]`.
Thứ tự trong một bước: giảm `time_left_ticks` -> xử lý 1 lệnh `buy` -> kiểm `shop_done` hoặc hết giờ.
"""


class ShopSim:
    mode = "shop"
    phase = "shop"

    def __init__(self, tuning, money=0, earned=0, reputation=3.0, upgrades=None, stock=None):
        shop_cfg = tuning.get("shop", {})
        self.t = shop_cfg
        self.upgrades_cfg = shop_cfg.get("upgrades", {})
        self.time_left_ticks = int(shop_cfg.get("max_ticks", 600))
        self.money = int(money)
        self.earned = int(earned)
        self.reputation = float(reputation)
        self.upgrades = dict(upgrades or {})
        self.stock = {k: v for k, v in (stock or {}).items() if v > 0}
        self.done = False
        self.reason = None

    def snapshot(self) -> dict:
        return {
            "stock": {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0},
        }

    def step(self, inp):
        events = []
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        buy = getattr(inp, "buy", None)
        if buy:
            self._handle_buy(buy, events)
        if inp.pressed("shop_done"):
            self.done = True
            self.reason = "done"
            events.append(("shop_end", {"reason": "done"}))
        elif self.time_left_ticks <= 0:
            self.done = True
            self.reason = "time"
            events.append(("shop_end", {"reason": "time"}))
        return events

    def _handle_buy(self, action: str, events):
        if action not in self.upgrades_cfg:
            events.append(("buy_failed", {"action": action, "reason": "unknown"}))
            return
        levels = self.upgrades_cfg[action]
        cur_level = int(self.upgrades.get(action, 0))
        next_spec = next((lv for lv in levels if lv["level"] == cur_level + 1), None)
        if next_spec is None:
            events.append(("buy_failed", {"action": action, "reason": "max_level"}))
            return
        price = int(next_spec["price"])
        if self.money < price:
            events.append(("buy_failed", {"action": action, "reason": "funds"}))
            return
        self.money -= price
        self.upgrades[action] = int(next_spec["level"])
        events.append(("bought", {
            "upgrade": action,
            "level": int(next_spec["level"]),
            "price": price,
            "money": self.money,
        }))
