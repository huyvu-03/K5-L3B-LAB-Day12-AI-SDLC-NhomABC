"""Buổi sáng — Lặn & Hái (`gather`). KHUNG: bơi, chặn mép, đồng hồ, cập bến, xuất kho.

Mặt cắt dòng sông nhìn NGANG: vị trí `[x, d]` (x sang phải, `d` độ sâu hướng xuống, d = 0 là mặt nước).
`move = [x, d]`: thành phần thứ hai DƯƠNG = bơi xuống. Hướng mặt là góc từ +x, dương = xuống.

Đã làm sẵn để smoke test chạy được: bơi + tăng/giảm tốc, chặn mép (d không âm), đồng hồ và hết giờ,
cập bến (`interact` trong vùng bến -> `gather_end` reason `docked`), xuất kho, snapshot đầy đủ trường gather.

M1 xử lý chuyển vùng mặt nước, oxy, ngạt và ngất theo PRD-0 mục F.
Nhóm viết tiếp:
  TODO(nhóm, lát 2): hái + bắt cá + cập bến + kho
      - hái nút ở mặt nước (gather, hold_full), nút mọc lại (node_regrown đã có phần đếm ngược)
      - bắt đàn cá bằng `catch` (fish_caught, hold_full, hồi chiêu catch_cd_ticks, chỉ khi dưới nước)
      - cập bến xét TRƯỚC hái (đã có); ghi kho đúng một lần do runner lo
Các tính năng của phase sau chưa nằm trong khung này.
"""

import math

from ..freshness import FRESH_SCALE, decay_units_per_tick, from_units, is_spoiled_units, to_units
from ..ids import id_key, sort_by_id
from ..inventory import hold_to_items, is_v12_plus
from .monsters import load_monsters, update_monsters
from .ramp import ramp_velocity

TICK = 60.0
AXES = ("x", "d")
FISH_SWIM_SPEED = 1.5
FISH_X_BOUNDS = (4.0, 96.0)
FISH_DEPTH_BANDS = {
    "ca_linh": (3.0, 12.0),
    "ca_loc": (8.0, 20.0),
    "ca_keo": (22.0, 28.0),
}

DEFAULT_FISH_SPEED = 1.5
DEFAULT_FISH_TURN_TICKS = 120
DEFAULT_FISH_MAX = 12
DEFAULT_FISH_SPAWN_TICKS = 360
DEFAULT_FISH_SPAWN_CLEARANCE = 1.0

DEFAULT_FISH_X = [4.0, 96.0]
DEFAULT_FISH_DEPTHS = {
    "ca_linh": [3.0, 12.0],
    "ca_loc": [8.0, 20.0],
    "ca_keo": [22.0, 28.0],
}
DEFAULT_FISH_SPAWN_X = [15.0, 30.0, 45.0, 60.0, 75.0, 90.0]
DEFAULT_FISH_SPAWN_DEPTHS = {
    "ca_linh": [5.0, 10.0],
    "ca_loc": [10.0, 16.0],
    "ca_keo": [24.0, 27.0],
}
DEFAULT_FISH_WEIGHTS = {
    "ca_linh": 0.4,
    "ca_loc": 0.3,
    "ca_keo": 0.3,
}


class GatherSim:
    mode = "gather"
    phase = "gather"

    def __init__(self, tuning, scenario, streams, ids, *, day=1):
        t = tuning["gather"]
        self.t = t
        self.tick_hz = tuning.get("tick_hz", TICK)
        self.monster_config = t.get("monsters", {})
        self.monsters = load_monsters(self.monster_config, scenario, day)
        if "fish_yield" in self.t and "ca_keo" not in self.t["fish_yield"]:
            self.t["fish_yield"]["ca_keo"] = 2
        self.rng = streams
        self.ids = ids
        self._is_v12 = (
            is_v12_plus(str(tuning.get("contract_version", "")))
            or is_v12_plus(str(scenario.get("contract_version", "")))
            or any(isinstance(x, dict) for x in scenario.get("hold", []))
        )
        if not self._is_v12:
            try:
                import sys
                hl = sys.modules.get("chonoi.headless")
                if hl and hasattr(hl, "load_contract"):
                    c = hl.load_contract()
                    if is_v12_plus(str(c.get("contract_version", ""))):
                        self._is_v12 = True
            except Exception:
                pass
        fresh_cfg = tuning.get("freshness", {})
        self.freshness_cfg = fresh_cfg
        self.decay_units = decay_units_per_tick(fresh_cfg.get("gather_decay_per_s", 0.5), self.tick_hz)
        self.spoiled_threshold_units = to_units(fresh_cfg.get("spoiled_below", 30.0))
        p = scenario.get("player", {})
        self.pos = [float(c) for c in p.get("pos", t["start_pos"])]
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        self.heading = float(p.get("heading_deg", t["start_heading_deg"]))
        self.oxygen_max = int(round(t["oxygen_max_s"] * TICK))
        self.oxygen_ticks = p.get("oxygen_ticks", self.oxygen_max)
        self.hp = p.get("hp", t["hp_max"])
        self.zero_oxy_ticks = p.get("zero_oxy_ticks", 0)
        self.invuln_ticks = p.get("invuln_ticks", 0)
        self.catch_cd_ticks = p.get("catch_cd_ticks", 0)
        raw_hold = scenario.get("hold", [])
        self.hold = []
        for it in raw_hold:
            if isinstance(it, dict):
                units = to_units(it.get("fresh", 100.0))
                self.hold.append({"id": it["id"], "kind": it["kind"], "units": units})
                ids.reserve(it["id"])
            else:
                if self._is_v12:
                    new_id = ids.new("I")
                    self.hold.append({"id": new_id, "kind": it, "units": to_units(100.0)})
                else:
                    self.hold.append(it)
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * TICK)))
        self.phase_tick = int(scenario.get("phase_tick", 0))
        self.random_fish = scenario.get("random_fish", True)
        # nút và đàn cá: scenario THAY THẾ danh sách mặc định; random_fish=false tắt cá mặc định
        src_nodes = scenario["nodes"] if "nodes" in scenario else t["nodes"]
        self.nodes = [{"id": n["id"], "kind": n["kind"], "pos": [float(c) for c in n["pos"]],
                       "regrow_ticks": n.get("regrow_ticks", 0)} for n in src_nodes]
        self.random_fish = scenario.get("random_fish", True)
        if "fish" in scenario:
            src_fish = scenario["fish"]
        elif scenario.get("random_fish", True):
            fi = t["fish_initial"]
            if isinstance(fi, list):
                src_fish = fi
            else:
                src_fish = self._spawn_initial_fish(int(fi), ids)
        else:
            src_fish = []
        # Đàn cá ban đầu; M2 sẽ mở rộng bơi & sinh theo lịch ở Phase 2.
        self.fish = [{"id": f["id"], "kind": f["kind"], "pos": [float(c) for c in f["pos"]],
                      "heading_deg": f.get("heading_deg", 0), "age_ticks": int(f.get("age_ticks", 0))}
                     for f in src_fish]
        for coll in (self.nodes, self.fish, self.monsters):
            for e in coll:
                ids.reserve(e["id"])
        self.money = 0
        self.earned = 0
        self.reputation = tuning["quan"]["reputation_initial"]
        self.done = False
        self.reason = None

    def _spawn_initial_fish(self, count: int, ids):
        """Sinh `count` đàn cá đầu ca (v1.1) ở các điểm hình học khác nhau theo seed."""
        r = self.rng.get("fish_spawn")
        xs = self.t.get("fish_spawn_x", [15, 30, 45, 60, 75, 90])
        depths_map = self.t.get("fish_spawn_depths", {"ca_linh": [5, 10], "ca_loc": [10, 16], "ca_keo": [24, 27]})
        weights_map = self.t.get("fish_weights", {"ca_linh": 0.4, "ca_loc": 0.3, "ca_keo": 0.3})
        kinds = sorted(weights_map.keys())
        used_pts = set()
        out = []
        for _ in range(count):
            avail = []
            for k in kinds:
                pts = [(x, d) for x in xs for d in depths_map.get(k, []) if (x, d) not in used_pts]
                if pts:
                    avail.append((k, pts))
            if not avail:
                break
            total_w = sum(weights_map[k] for k, _ in avail)
            pick = r.random() * total_w
            acc = 0.0
            chosen_k, chosen_pts = avail[-1]
            for k, pts in avail:
                acc += weights_map[k]
                if pick <= acc:
                    chosen_k, chosen_pts = k, pts
                    break
            pt = chosen_pts[r.randrange(len(chosen_pts))]
            used_pts.add(pt)
            out.append({
                "id": ids.new("F"),
                "kind": chosen_k,
                "pos": [float(pt[0]), float(pt[1])],
                "heading_deg": r.random() * 360.0,
                "age_ticks": 0,
            })
        return out

    # --- giao diện cho runner -------------------------------------------------
    def _format_item(self, it):
        if isinstance(it, dict):
            return {
                "id": it["id"],
                "kind": it["kind"],
                "fresh": from_units(it["units"]),
            }
        return it

    def _update_freshness(self, events):
        spoiled_this_tick = []
        for it in self.hold:
            if isinstance(it, dict):
                old_u = it["units"]
                new_u = max(0, old_u - self.decay_units)
                it["units"] = new_u
                if old_u >= self.spoiled_threshold_units and new_u < self.spoiled_threshold_units:
                    spoiled_this_tick.append(it)
        if spoiled_this_tick:
            for it in sort_by_id(spoiled_this_tick):
                events.append(("spoiled", {
                    "item_id": it["id"],
                    "kind": it["kind"],
                    "location": "hold",
                }))

    def inventory_items(self):
        if self._is_v12:
            return [self._format_item(it) for it in sort_by_id(self.hold)]
        return hold_to_items([it["kind"] if isinstance(it, dict) else it for it in self.hold])

    def snapshot(self) -> dict:
        hold_repr = [self._format_item(it) for it in self.hold] if self._is_v12 else [it["kind"] if isinstance(it, dict) else it for it in self.hold]
        return {
            **({"monsters": self.monsters} if self.monster_config else {}),
            "player": {"pos": self.pos, "vel": self.vel, "heading_deg": self.heading,
                       "oxygen_ticks": self.oxygen_ticks, "oxygen_max_ticks": self.oxygen_max,
                       "hp": self.hp, "hp_max": self.t["hp_max"], "zero_oxy_ticks": self.zero_oxy_ticks,
                       "invuln_ticks": self.invuln_ticks, "catch_cd_ticks": self.catch_cd_ticks,
                       "at_surface": self._at_surface()},
            "hold": hold_repr, "hold_count": len(self.hold),
            "hold_capacity": self.t["hold_capacity"],
            "nodes": [{"id": n["id"], "pos": n["pos"], "kind": n["kind"],
                       "ready": n["regrow_ticks"] == 0, "regrow_ticks": n["regrow_ticks"]}
                      for n in sort_by_id(self.nodes)],
            "fish": [{"id": f["id"], "pos": f["pos"], "kind": f["kind"], "heading_deg": f["heading_deg"]}
                     for f in sort_by_id(self.fish)],
        }

    # --- một bước ---------------------------------------------------------------
    def step(self, inp):
        events = []
        # 1. đồng hồ và hàng có sẵn: giảm bộ đếm, nút mọc lại
        self.phase_tick += 1
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self.invuln_ticks = max(0, self.invuln_ticks - 1)
        self.catch_cd_ticks = max(0, self.catch_cd_ticks - 1)
        for n in sort_by_id(self.nodes):
            if n["regrow_ticks"] > 0:
                n["regrow_ticks"] -= 1
                if n["regrow_ticks"] == 0:
                    events.append(("node_regrown", {"node_id": n["id"]}))
        # 1.5. hao độ tươi giỏ (Phase 3)
        if self._is_v12:
            self._update_freshness(events)
        # 2. bơi, chặn mép và tính oxy theo vị trí cuối bước
        was_at_surface = self._at_surface()
        self._move(inp)
        at_surface = self._at_surface()
        if at_surface != was_at_surface:
            events.append(("surface" if at_surface else "dive", {"pos": self.pos.copy()}))
        self._update_oxygen(at_surface, events)
        if self.done:
            return events
        self._update_monsters(events)
        if self.done:
            return events
        # 3. interact: bến trước, rồi hái
        if inp.pressed("interact"):
            if self._in_dock():
                self._finish("docked", events)
                return events
            if self._at_surface():
                radius = self.t["interact_radius"]
                candidates = []
                for n in self.nodes:
                    if n["regrow_ticks"] == 0:
                        d = math.dist(self.pos, n["pos"])
                        if d <= radius:
                            candidates.append((d, n))
                if candidates:
                    candidates.sort(key=lambda item: (item[0], id_key(item[1]["id"])))
                    node = candidates[0][1]
                    yield_count = self.t["node_yield"]
                    free_space = self.t["hold_capacity"] - len(self.hold)
                    if free_space >= yield_count:
                        if self._is_v12:
                            for _ in range(yield_count):
                                new_id = self.ids.new("I")
                                self.hold.append({
                                    "id": new_id,
                                    "kind": node["kind"],
                                    "units": to_units(self.freshness_cfg.get("initial", 100.0)),
                                })
                        else:
                            self.hold.extend([node["kind"]] * yield_count)
                        node["regrow_ticks"] = int(round(self.t["regrow_s"] * TICK))
                        events.append(("gather", {
                            "node_id": node["id"],
                            "kind": node["kind"],
                            "amount": yield_count,
                        }))
                    else:
                        events.append(("hold_full", {
                            "action": "gather",
                            "node_id": node["id"],
                            "required": yield_count,
                            "free": max(0, free_space),
                        }))
        # 4. bắt cá
        if inp.pressed("catch"):
            if self.catch_cd_ticks == 0 and not self._at_surface():
                radius = self.t["catch_radius"]
                candidates = []
                for f in self.fish:
                    d = math.dist(self.pos, f["pos"])
                    if d <= radius:
                        candidates.append((d, f))
                if candidates:
                    candidates.sort(key=lambda item: (item[0], id_key(item[1]["id"])))
                    fish = candidates[0][1]
                    yield_count = self.t["fish_yield"][fish["kind"]]
                    free_space = self.t["hold_capacity"] - len(self.hold)
                    if free_space >= yield_count:
                        if self._is_v12:
                            for _ in range(yield_count):
                                new_id = self.ids.new("I")
                                self.hold.append({
                                    "id": new_id,
                                    "kind": fish["kind"],
                                    "units": to_units(self.freshness_cfg.get("initial", 100.0)),
                                })
                        else:
                            self.hold.extend([fish["kind"]] * yield_count)
                        self.fish.remove(fish)
                        self.catch_cd_ticks = int(round(self.t["catch_cooldown_s"] * TICK))
                        events.append(("fish_caught", {
                            "fish_id": fish["id"],
                            "kind": fish["kind"],
                            "yield": yield_count,
                        }))
                    else:
                        events.append(("hold_full", {
                            "action": "catch",
                            "fish_id": fish["id"],
                            "required": yield_count,
                            "free": max(0, free_space),
                        }))
        # 5. hết giờ
        if self.time_left_ticks <= 0:
            self._finish("time", events)
            return events
        # 6. đàn cá bơi & sinh thêm (tắt khi random_fish=False)
        if "fish_speed" in self.t:
            self._update_fish_swim()
            self._update_fish_spawn(events)
        elif self.random_fish:
            self._move_fish()
        return events

    def _move_fish(self):
        b = self.t["bounds"]
        x_lo, x_hi = max(float(b["x"][0]), FISH_X_BOUNDS[0]), min(float(b["x"][1]), FISH_X_BOUNDS[1])
        d_map_lo, d_map_hi = float(b["d"][0]), float(b["d"][1])
        rng = self.rng.get("fish_move")
        step_dist = FISH_SWIM_SPEED / TICK
        for f in sort_by_id(self.fish):
            f["age_ticks"] += 1
            if f["age_ticks"] % 120 == 0:
                f["heading_deg"] = rng.uniform(0.0, 360.0)
            rad = math.radians(f["heading_deg"])
            dx, dd = math.cos(rad) * step_dist, math.sin(rad) * step_dist
            nx = f["pos"][0] + dx
            nd = f["pos"][1] + dd
            d_lo, d_hi = FISH_DEPTH_BANDS.get(f["kind"], (3.0, 20.0))
            d_lo, d_hi = max(d_map_lo, d_lo), min(d_map_hi, d_hi)
            flip_x = False
            flip_d = False
            if nx < x_lo:
                nx = x_lo + (x_lo - nx)
                flip_x = True
            elif nx > x_hi:
                nx = x_hi - (nx - x_hi)
                flip_x = True
            if nd < d_lo:
                nd = d_lo + (d_lo - nd)
                flip_d = True
            elif nd > d_hi:
                nd = d_hi - (nd - d_hi)
                flip_d = True
            f["pos"][0] = max(x_lo, min(x_hi, nx))
            f["pos"][1] = max(d_lo, min(d_hi, nd))
            if flip_x or flip_d:
                vx = -math.cos(rad) if flip_x else math.cos(rad)
                vd = -math.sin(rad) if flip_d else math.sin(rad)
                f["heading_deg"] = math.degrees(math.atan2(vd, vx)) % 360.0

    # --- cá bơi & sinh cá (Phase 2) ---------------------------------------------
    def _update_fish_swim(self):
        """Cá bơi, đổi hướng mỗi fish_turn_ticks, phản xạ mép đàn hồi."""
        if not self.random_fish:
            return

        speed = float(self.t.get("fish_speed", 0.0))
        if speed <= 0.0:
            return

        turn_ticks = int(self.t.get("fish_turn_ticks", DEFAULT_FISH_TURN_TICKS))
        fish_x = self.t.get("fish_x", DEFAULT_FISH_X)
        x_min, x_max = float(fish_x[0]), float(fish_x[1])
        depths_map = self.t.get("fish_depths", DEFAULT_FISH_DEPTHS)

        # Duyệt cá theo thứ tự sort_by_id để đảm bảo tính tất định
        for f in sort_by_id(self.fish):
            age = f.get("age_ticks", 0)
            heading = float(f.get("heading_deg", 0.0))

            # 1. Đổi hướng trước khi di chuyển tại các bước bội số của turn_ticks
            if age > 0 and age % turn_ticks == 0:
                heading = self.rng.get("fish_swim").random() * 360.0
                f["heading_deg"] = heading

            # 2. Tính vận tốc và quãng đường trong 1 tick (dt = 1/60)
            rad = math.radians(heading)
            vx = speed * math.cos(rad)
            vd = speed * math.sin(rad)
            dx = vx / 60.0
            dd = vd / 60.0

            pos = f["pos"]
            x, d = float(pos[0]), float(pos[1])
            x_new = x + dx
            d_new = d + dd

            # Lấy dải độ sâu của loài cá
            kind = f["kind"]
            d_range = depths_map.get(kind, [0.0, 30.0])
            d_min, d_max = float(d_range[0]), float(d_range[1])

            # 3. Phản xạ đàn hồi ở biên x
            changed = False
            if x_new < x_min:
                x_new = 2.0 * x_min - x_new
                vx = -vx
                changed = True
            elif x_new > x_max:
                x_new = 2.0 * x_max - x_new
                vx = -vx
                changed = True

            # Phản xạ đàn hồi ở biên d
            if d_new < d_min:
                d_new = 2.0 * d_min - d_new
                vd = -vd
                changed = True
            elif d_new > d_max:
                d_new = 2.0 * d_max - d_new
                vd = -vd
                changed = True

            # Kẹp an toàn trong biên phòng trường hợp số thực
            x_new = max(x_min, min(x_max, x_new))
            d_new = max(d_min, min(d_max, d_new))

            # Cập nhật góc hướng nếu bị phản xạ mép
            if changed:
                heading = math.degrees(math.atan2(vd, vx)) % 360.0
                f["heading_deg"] = heading

            f["pos"] = [x_new, d_new]
            f["age_ticks"] = age + 1

    def _update_fish_spawn(self, events):
        """Sinh thêm đàn cá mới theo chu kỳ fish_spawn_ticks."""
        if not self.random_fish:
            return

        # Chỉ chạy khi có cấu hình Phase 2 (fish_speed hoặc fish_spawn_ticks)
        if "fish_speed" not in self.t and "fish_spawn_ticks" not in self.t:
            return

        spawn_ticks = int(self.t.get("fish_spawn_ticks", DEFAULT_FISH_SPAWN_TICKS))
        if self.phase_tick <= 0 or self.phase_tick % spawn_ticks != 0:
            return

        fish_max = int(self.t.get("fish_max", DEFAULT_FISH_MAX))
        if len(self.fish) >= fish_max:
            return

        clearance = float(self.t.get("fish_spawn_clearance", DEFAULT_FISH_SPAWN_CLEARANCE))
        spawn_x = [float(x) for x in self.t.get("fish_spawn_x", DEFAULT_FISH_SPAWN_X)]
        spawn_depths_map = self.t.get("fish_spawn_depths", DEFAULT_FISH_SPAWN_DEPTHS)
        weights_map = self.t.get("fish_weights", DEFAULT_FISH_WEIGHTS)

        # 1. Tìm điểm sinh hợp lệ cho từng loài (cách mọi đàn đang sống > clearance)
        valid_points_by_kind = {}
        for kind in ("ca_linh", "ca_loc", "ca_keo"):
            depths = spawn_depths_map.get(kind, [])
            valid_pts = []
            for sx in spawn_x:
                for sd in depths:
                    pt = [float(sx), float(sd)]
                    if all(math.dist(pt, f["pos"]) > clearance for f in self.fish):
                        valid_pts.append(pt)
            if valid_pts:
                valid_pts.sort(key=lambda p: (p[0], p[1]))
                valid_points_by_kind[kind] = valid_pts

        if not valid_points_by_kind:
            return

        # 2. Chọn loài theo trọng số chuẩn hóa
        valid_kinds = [k for k in ("ca_linh", "ca_loc", "ca_keo") if k in valid_points_by_kind]
        total_w = sum(float(weights_map.get(k, 0.0)) for k in valid_kinds)
        if total_w <= 0.0:
            return

        roll = self.rng.get("fish_spawn").random() * total_w
        chosen_kind = valid_kinds[-1]
        cum = 0.0
        for k in valid_kinds:
            cum += float(weights_map.get(k, 0.0))
            if roll < cum:
                chosen_kind = k
                break

        # 3. Chọn đều một điểm hợp lệ của loài đó
        pts = valid_points_by_kind[chosen_kind]
        pt_idx = self.rng.get("fish_spawn").randrange(len(pts))
        chosen_pt = pts[pt_idx]

        # 4. Hướng ban đầu và cấp id mới
        heading = self.rng.get("fish_spawn").random() * 360.0
        new_id = self.ids.new("F")

        new_fish = {
            "id": new_id,
            "kind": chosen_kind,
            "pos": [chosen_pt[0], chosen_pt[1]],
            "heading_deg": heading,
            "age_ticks": 0,
        }
        self.fish.append(new_fish)
        events.append(("fish_spawned", {
            "id": new_id,
            "kind": chosen_kind,
            "pos": [chosen_pt[0], chosen_pt[1]],
        }))

    # --- tiện ích ---------------------------------------------------------------
    def _at_surface(self) -> bool:
        return self.pos[1] <= self.t["surface_depth"]

    def _update_oxygen(self, at_surface, events):
        if at_surface:
            self.oxygen_ticks = min(self.oxygen_max, self.oxygen_ticks + self.t["oxygen_refill_per_tick"])
            self.zero_oxy_ticks = 0
            return

        if self.oxygen_ticks > 0:
            self.oxygen_ticks -= 1
            if self.oxygen_ticks > 0:
                return
            events.append(("oxygen_empty", {"oxygen_ticks": 0}))

        # Tick vừa cạn oxy cũng tính vào thời gian ngạt.
        self.zero_oxy_ticks += 1
        if self.zero_oxy_ticks < self.t["choke_interval_ticks"]:
            return

        self.zero_oxy_ticks = 0
        self.hp -= 1
        events.append(("choke", {"hp": self.hp}))
        if self.hp == 0:
            self._faint("choke", events)

    def _update_monsters(self, events):
        monster = update_monsters(self.monsters, self.monster_config, self.t["bounds"],
                                  self.tick_hz, self.pos, self.invuln_ticks > 0)
        if monster is None:
            return
        self.hp -= 1
        count = math.floor(len(self.hold) * self.monster_config["loss_ratio"])
        lost = [self.hold.pop() for _ in range(count)]
        self.invuln_ticks = self.monster_config["invuln_ticks"]
        lost_data = [self._format_item(it) for it in lost] if self._is_v12 else lost
        events.append(("monster_hit", {"monster_id": monster["id"], "hp": self.hp,
                                       "lost": lost_data, "pos": self.pos.copy()}))
        if self.hp == 0:
            self._faint("monster", events)

    def _faint(self, cause, events):
        lost = list(reversed(self.hold))
        self.hold.clear()
        lost_data = [self._format_item(it) for it in lost] if self._is_v12 else lost
        events.append(("faint", {"cause": cause, "lost": lost_data, "hp": self.hp}))
        self._finish("fainted", events)

    def _in_dock(self) -> bool:
        return math.dist(self.pos, self.t["dock_pos"]) <= self.t["dock_radius"]

    def _finish(self, reason, events):
        self.done = True
        self.reason = reason
        inv = {"items": []} if (self._is_v12 and reason == "fainted") else {"items": self.inventory_items()}
        events.append(("gather_end", {"reason": reason, "inventory": inv}))

    def _move(self, inp):
        speed = self.t["swim_speed"]
        mx, md = inp.move
        self.vel = ramp_velocity(self, (mx * speed, md * speed), int(self.t["ramp_max_ticks"]))
        if (mx, md) != (0.0, 0.0):
            self.heading = math.degrees(math.atan2(md, mx)) % 360
        b = self.t["bounds"]
        for i, axis in enumerate(AXES):
            self.pos[i] += self.vel[i] / TICK
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i] = lo
                self.vel[i] = max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i] = hi
                self.vel[i] = min(0.0, self.vel[i])
