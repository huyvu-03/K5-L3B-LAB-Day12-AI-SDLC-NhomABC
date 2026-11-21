"""P2-M4.3b — Vòng ngày `--mode day` (Ticket02 / Test Contract v1.1).

Điều phối: day_start -> day_plan -> gather -> quan (kho trong bộ nhớ) -> shop -> ngày kế / days_complete.
"""

from .gather import GatherSim
from .quan import QuanSim
from .shop import ShopSim


def _apply_active_upgrades(tuning: dict, active_upgrades: dict) -> dict:
    """Áp cấp nâng cấp đang có hiệu lực (`oxygen`, `hp`) vào bản sao `tuning["gather"]`."""
    shop_upgrades = tuning.get("shop", {}).get("upgrades", {})
    gather = dict(tuning["gather"])
    oxy_lv = int(active_upgrades.get("oxygen", 0))
    if oxy_lv > 0 and "oxygen" in shop_upgrades:
        spec = next((x for x in shop_upgrades["oxygen"] if x["level"] == oxy_lv), None)
        if spec is not None and "oxygen_max_s" in spec:
            gather["oxygen_max_s"] = spec["oxygen_max_s"]
    hp_lv = int(active_upgrades.get("hp", 0))
    if hp_lv > 0 and "hp" in shop_upgrades:
        spec = next((x for x in shop_upgrades["hp"] if x["level"] == hp_lv), None)
        if spec is not None and "hp_max" in spec:
            gather["hp_max"] = spec["hp_max"]
    return {**tuning, "gather": gather}


def _compute_ingredients(dishes: dict, menu: dict) -> dict:
    ing = {}
    for dish_id, count in dishes.items():
        for kind, qty in menu[dish_id]["recipe"].items():
            ing[kind] = ing.get(kind, 0) + qty * count
    return {k: ing[k] for k in sorted(ing) if ing[k] > 0}


class DaySim:
    mode = "day"

    def __init__(self, tuning, scenario, streams, ids, days=1):
        self.tuning = tuning
        self.rng = streams
        self.ids = ids
        self.days = int(days)
        self._gather_template = dict(scenario.get("gather", {}))
        self._quan_template = dict(scenario.get("quan", {}))
        day_cfg = scenario.get("day", {})
        self.money = int(day_cfg.get("money", 0))
        self.earned = int(day_cfg.get("earned", 0))
        self.reputation = float(day_cfg.get("reputation", tuning["quan"]["reputation_initial"]))
        self.upgrades = {k: int(v) for k, v in day_cfg.get("upgrades", {}).items() if int(v) > 0}
        self.active_upgrades = dict(self.upgrades)
        self._plans = self._build_plans(tuning, day_cfg.get("day_plan"))
        self.day = 1
        self.days_completed = 0
        self.phase = "gather"
        self.phase_tick = 0
        self.done = False
        self.reason = None
        self._sub = None
        self.initial_events = self._start_day(1)

    def _build_plans(self, tuning, overrides):
        menu = tuning["menu"]
        plans = {}
        for item in tuning.get("day_plan", []):
            d = int(item["day"])
            dishes = dict(item["dishes"])
            ingredients = dict(item.get("ingredients") or _compute_ingredients(dishes, menu))
            plans[d] = {"dishes": dishes, "ingredients": ingredients}
        if overrides:
            for item in overrides:
                d = int(item["day"])
                dishes = dict(item["dishes"])
                ingredients = dict(item.get("ingredients") or _compute_ingredients(dishes, menu))
                plans[d] = {"dishes": dishes, "ingredients": ingredients}
        return plans

    def _get_plan(self, day_num: int) -> dict:
        if day_num in self._plans:
            p = self._plans[day_num]
            return {
                "dishes": {k: p["dishes"][k] for k in sorted(p["dishes"])},
                "ingredients": {k: p["ingredients"][k] for k in sorted(p["ingredients"])},
            }
        return {"dishes": {}, "ingredients": {}}

    @property
    def time_left_ticks(self) -> int:
        return self._sub.time_left_ticks

    def _start_day(self, day_num: int):
        self.day = day_num
        self.day_plan = self._get_plan(day_num)
        eff_tuning = _apply_active_upgrades(self.tuning, self.active_upgrades)
        gather_sc = dict(self._gather_template)
        self._sub = GatherSim(eff_tuning, gather_sc, self.rng, self.ids)
        self._sub.money = self.money
        self._sub.earned = self.earned
        self._sub.reputation = self.reputation
        self.phase = "gather"
        self.phase_tick = 0
        return [
            ("day_start", {}, "gather", self.day),
            ("day_plan", {"dishes": dict(self.day_plan["dishes"]),
                          "ingredients": dict(self.day_plan["ingredients"])}, "gather", self.day),
            ("phase_start", {}, "gather", self.day),
        ]

    def _start_quan(self, inventory_items: dict):
        quan_sc = dict(self._quan_template)
        quan_sc["reputation"] = self.reputation
        # Lọc thực đơn theo kế hoạch ngày (khi chạy day)
        plan_dishes = self.day_plan["dishes"]
        if plan_dishes:
            filtered_menu = {k: v for k, v in self.tuning["menu"].items() if k in plan_dishes}
            eff_tuning = {**self.tuning, "menu": filtered_menu}
        else:
            eff_tuning = self.tuning
        quan = QuanSim(eff_tuning, quan_sc, self.rng, self.ids, inventory=dict(inventory_items))
        quan.money = self.money
        quan.earned = self.earned
        quan.reputation = self.reputation
        self._sub = quan
        self.phase = "quan"
        self.phase_tick = 0
        return [("phase_start", {}, "quan", self.day)]

    def _start_shop(self, remaining_stock: dict):
        self._sub = ShopSim(
            self.tuning,
            money=self.money,
            earned=self.earned,
            reputation=self.reputation,
            upgrades=self.upgrades,
            stock=remaining_stock,
        )
        self.phase = "shop"
        self.phase_tick = 0
        return [("phase_start", {}, "shop", self.day)]

    def snapshot(self) -> dict:
        snap = self._sub.snapshot()
        snap.update({
            "day": self.day,
            "day_plan": {
                "dishes": dict(self.day_plan["dishes"]),
                "ingredients": dict(self.day_plan["ingredients"]),
            },
            "upgrades": {k: self.upgrades[k] for k in sorted(self.upgrades)},
            "active_upgrades": {k: self.active_upgrades[k] for k in sorted(self.active_upgrades)},
        })
        return snap

    def step(self, inp):
        old_phase = self.phase
        old_day = self.day
        raw_events = self._sub.step(inp)
        self.phase_tick += 1
        out = [(name, data, old_phase, old_day) for name, data in raw_events]

        if old_phase == "gather" and self._sub.done:
            inv_items = self._sub.inventory_items()
            out.extend(self._start_quan(inv_items))
        elif old_phase == "quan":
            self.money = self._sub.money
            self.earned = self._sub.earned
            self.reputation = self._sub.reputation
            if self._sub.done:
                rem_stock = {k: v for k, v in self._sub.stock.items() if v > 0}
                out.extend(self._start_shop(rem_stock))
        elif old_phase == "shop":
            self.money = self._sub.money
            self.upgrades = dict(self._sub.upgrades)
            if self._sub.done:
                self.days_completed += 1
                if self.days_completed >= self.days:
                    self.done = True
                    self.reason = "days_complete"
                else:
                    self.active_upgrades = dict(self.upgrades)
                    out.extend(self._start_day(self.day + 1))
        return out
