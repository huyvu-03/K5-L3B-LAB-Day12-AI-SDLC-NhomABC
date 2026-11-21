"""Nạp và kiểm scenario (Contract D). Trả về dict của đúng khối theo mode.

KHUNG: kiểm cú pháp, id trùng, bộ đếm âm, khoang vượt sức chứa, trường lạ.
TODO(nhóm): bổ sung kiểm mâu thuẫn mức luật mà nhóm cần (khách giữ chỗ quá kho, đơn assigned
phải có đúng một món, khách eating thiếu giá/tip...) — xem PRD-0 mục D và 'Mâu thuẫn -> mã 2'.
"""

import json

from .errors import BadInput
from .inventory import KINDS_P2, validate_items

GATHER_KEYS = {"player", "hold", "nodes", "fish", "monsters", "random_fish", "time_left_ticks"}
GATHER_PLAYER_KEYS = {"pos", "vel", "heading_deg", "hp", "oxygen_ticks", "zero_oxy_ticks",
                      "invuln_ticks", "catch_cd_ticks"}
NODE_KINDS = ("bong_dien_dien", "bong_sung", "keo_neo")
FISH_KINDS = ("ca_linh", "ca_loc", "ca_keo")
MONSTER_KEYS = {"id", "kind", "pos", "waypoints", "target_idx", "state", "state_ticks_left", "recoil_dir"}
MONSTER_STATES = ("patrol", "chase", "recoil", "stunned")
DAY_KEYS = {"money", "earned", "reputation", "upgrades", "day_plan"}
QUAN_PLAYER_KEYS = {"pos", "vel"}
QUAN_KEYS = {"player", "stock", "hand", "stoves", "tables", "customers", "random_customers",
             "reputation", "time_left_ticks"}
QUAN_STOVE_KEYS = {"id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks"}
QUAN_TABLE_KEYS = {"id", "pos"}
QUAN_CUSTOMER_KEYS = {"id", "table_id", "dish_id", "order_tick", "state", "patience_ticks_left",
                      "eat_ticks_left", "order_status", "reserved", "base_price", "tip"}
DISH_PAYLOAD_KEYS = {"order_id", "dish_id", "base_price"}
STOVE_STATES = ("idle", "cooking", "ready")
CUSTOMER_STATES = ("waiting", "eating")
ORDER_STATUSES = ("reserved", "assigned", "unfulfillable", "served")


def _check_ids(name, arr):
    if not isinstance(arr, list):
        raise BadInput(f"{name} phải là mảng")
    seen = set()
    for e in arr:
        if not isinstance(e, dict) or not isinstance(e.get("id"), str) or not e["id"]:
            raise BadInput(f"{name}: mỗi phần tử cần id (chuỗi khác rỗng)")
        if e["id"] in seen:
            raise BadInput(f"{name}: id trùng {e['id']}")
        seen.add(e["id"])


def _validate_mode_block(mode: str, block: dict, tuning: dict):
    if not isinstance(block, dict):
        raise BadInput(f"khối {mode} phải là object")
    allowed = GATHER_KEYS if mode == "gather" else QUAN_KEYS
    extra = set(block) - allowed
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong {mode}: {sorted(extra)}")
    dur = int(round(tuning[mode]["duration_s"] * 60))
    if "time_left_ticks" in block:
        t = block["time_left_ticks"]
        if isinstance(t, bool) or not isinstance(t, int) or not (1 <= t <= dur):
            raise BadInput(f"time_left_ticks phải là số nguyên trong [1, {dur}]")
    if mode == "gather":
        _validate_gather(block, tuning)
    else:
        _validate_quan(block, tuning)


def _validate_day(d: dict, tuning: dict):
    if not isinstance(d, dict):
        raise BadInput("khối day phải là object")
    extra = set(d) - DAY_KEYS
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong day: {sorted(extra)}")
    money = d.get("money", 0)
    earned = d.get("earned", 0)
    _nonneg_int("day.money", money)
    _nonneg_int("day.earned", earned)
    if money > earned:
        raise BadInput("day: cần 0 <= money <= earned")
    if "reputation" in d:
        q = tuning["quan"]
        rep = d["reputation"]
        if not _num(rep) or not (q["reputation_min"] <= rep <= q["reputation_max"]):
            raise BadInput(f"day.reputation phải trong [{q['reputation_min']}, {q['reputation_max']}]")
    if "upgrades" in d:
        up = d["upgrades"]
        if not isinstance(up, dict):
            raise BadInput("day.upgrades phải là object")
        shop_up = tuning.get("shop", {}).get("upgrades", {})
        for k, lv in up.items():
            if k not in shop_up:
                raise BadInput(f"day.upgrades: nâng cấp không hợp lệ: {k}")
            _nonneg_int(f"day.upgrades.{k}", lv)
            max_lv = max((x["level"] for x in shop_up[k]), default=0)
            if lv > max_lv:
                raise BadInput(f"day.upgrades.{k} vượt cấp tối đa ({max_lv})")
    if "day_plan" in d:
        dp = d["day_plan"]
        if not isinstance(dp, list):
            raise BadInput("day.day_plan phải là mảng")
        menu = tuning["menu"]
        for item in dp:
            if not isinstance(item, dict) or "day" not in item or "dishes" not in item:
                raise BadInput("day.day_plan: mỗi mục cần 'day' và 'dishes'")
            _pos_int("day.day_plan.day", item["day"])
            dishes = item["dishes"]
            if not isinstance(dishes, dict) or not dishes:
                raise BadInput("day.day_plan.dishes phải là object không rỗng")
            calc = {}
            for dish_id, cnt in dishes.items():
                if dish_id not in menu:
                    raise BadInput(f"day.day_plan: món không tồn tại: {dish_id}")
                _pos_int(f"day.day_plan.dishes.{dish_id}", cnt)
                for k, qty in menu[dish_id]["recipe"].items():
                    calc[k] = calc.get(k, 0) + qty * cnt
            if "ingredients" in item:
                ing = validate_items(item["ingredients"])
                if ing != calc:
                    raise BadInput(f"day.day_plan ngày {item['day']}: ingredients không khớp tổng công thức")


def load_scenario(path, mode: str, tuning: dict) -> dict:
    if path is None:
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được scenario {path}: {e}")
    if mode == "day":
        if not isinstance(data, dict) or not set(data) <= {"day", "gather", "quan"}:
            raise BadInput("scenario --mode day chỉ được có các khối 'day', 'gather', 'quan'")
        if "day" in data:
            _validate_day(data["day"], tuning)
        if "gather" in data:
            _validate_mode_block("gather", data["gather"], tuning)
        if "quan" in data:
            qb = data["quan"]
            if isinstance(qb, dict) and ("stock" in qb or "reputation" in qb):
                raise BadInput("cấm khai quan.stock và quan.reputation khi chạy --mode day")
            _validate_mode_block("quan", qb, tuning)
        return data
    if not isinstance(data, dict) or not set(data) <= {"gather", "quan"}:
        raise BadInput("scenario chỉ được có khối 'gather' hoặc 'quan'")
    if set(data) - {mode}:
        raise BadInput(f"khối sai mode: chạy --mode {mode} chỉ nhận khối '{mode}'")
    block = data.get(mode, {})
    _validate_mode_block(mode, block, tuning)
    return block


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _nonneg_int(name, v):
    if isinstance(v, bool) or not isinstance(v, int) or v < 0:
        raise BadInput(f"{name} phải là số nguyên không âm")


def _pos(name, pos, bounds, axes=("x", "d")):
    if not (isinstance(pos, list) and len(pos) == 2 and all(_num(c) for c in pos)):
        raise BadInput(f"{name} phải là [{axes[0]}, {axes[1]}]")
    for c, axis in zip(pos, axes):
        lo, hi = bounds[axis]
        if not (lo <= c <= hi):
            raise BadInput(f"{name} nằm ngoài vùng nước ({axis} ∈ [{lo}, {hi}])")


def _validate_gather(b, tuning):
    g = tuning["gather"]
    bounds = g["bounds"]
    for arr in ("nodes", "fish", "monsters"):
        if arr in b:
            _check_ids(arr, b[arr])
    if "random_fish" in b and not isinstance(b["random_fish"], bool):
        raise BadInput("random_fish phải là boolean")
    if "hold" in b:
        h = b["hold"]
        if not isinstance(h, list) or any(k not in KINDS_P2 for k in h):
            raise BadInput("hold phải là mảng id nguyên liệu hợp lệ")
        if len(h) > g["hold_capacity"]:
            raise BadInput("hold vượt sức chứa")
    p = b.get("player", {})
    if not isinstance(p, dict):
        raise BadInput("player phải là object")
    extra = set(p) - GATHER_PLAYER_KEYS
    if extra:
        raise BadInput(f"trường lạ/chưa hỗ trợ trong gather.player: {sorted(extra)}")
    if "pos" in p:
        _pos("player.pos", p["pos"], bounds)
    if "vel" in p and not (isinstance(p["vel"], list) and len(p["vel"]) == 2 and all(_num(c) for c in p["vel"])):
        raise BadInput("player.vel phải là [x, d]")
    if "heading_deg" in p and not _num(p["heading_deg"]):
        raise BadInput("player.heading_deg phải là số")
    for key in ("invuln_ticks", "catch_cd_ticks", "zero_oxy_ticks", "oxygen_ticks", "hp"):
        if key in p:
            _nonneg_int(f"player.{key}", p[key])
    omax = int(round(g["oxygen_max_s"] * 60))
    if "oxygen_ticks" in p and p["oxygen_ticks"] > omax:
        raise BadInput("player.oxygen_ticks vượt oxy tối đa")
    if "hp" in p and not (1 <= p["hp"] <= g["hp_max"]):
        raise BadInput("player.hp phải trong [1, hp_max]")
    if "zero_oxy_ticks" in p:
        pos = p.get("pos", g["start_pos"])
        oxy = p.get("oxygen_ticks", omax)
        if p["zero_oxy_ticks"] > 59:
            raise BadInput("player.zero_oxy_ticks phải trong [0, 59]")
        if p["zero_oxy_ticks"] > 0 and not (oxy == 0 and pos[1] > g["surface_depth"]):
            raise BadInput("player.zero_oxy_ticks > 0 chỉ khi oxy = 0 và đang dưới nước")
    for n in b.get("nodes", []):
        if n.get("kind") not in NODE_KINDS:
            raise BadInput(f"nodes.{n['id']}: kind phải là một trong {NODE_KINDS}")
        _pos(f"nodes.{n['id']}.pos", n.get("pos"), bounds)
        if n["pos"][1] != 0:
            raise BadInput(f"nodes.{n['id']}: nút hái nằm ở mặt nước (d = 0)")
        if "regrow_ticks" in n:
            _nonneg_int(f"nodes.{n['id']}.regrow_ticks", n["regrow_ticks"])
    for f in b.get("fish", []):
        if f.get("kind") not in FISH_KINDS:
            raise BadInput(f"fish.{f['id']}: kind phải là một trong {FISH_KINDS}")
        _pos(f"fish.{f['id']}.pos", f.get("pos"), bounds)
        if f["pos"][1] <= g["surface_depth"]:
            raise BadInput(f"fish.{f['id']}: đàn cá phải ở dưới nước")
        if "heading_deg" in f and not _num(f["heading_deg"]):
            raise BadInput(f"fish.{f['id']}.heading_deg phải là số")
        if "age_ticks" in f:
            _nonneg_int(f"fish.{f['id']}.age_ticks", f["age_ticks"])
    species_cfg = g.get("monsters", {}).get("species", {"ca_sau": {"depths": [10, 30]}})
    for m in b.get("monsters", []):
        mid = m["id"]
        extra = set(m) - MONSTER_KEYS
        if extra:
            raise BadInput(f"monsters.{mid}: trường lạ {sorted(extra)}")
        kind = m.get("kind")
        if kind not in species_cfg:
            raise BadInput(f"monsters.{mid}: kind không hợp lệ: {kind!r}")
        _pos(f"monsters.{mid}.pos", m.get("pos"), bounds)
        wps = m.get("waypoints")
        if not isinstance(wps, list) or len(wps) != 2:
            raise BadInput(f"monsters.{mid}.waypoints phải có đúng 2 điểm")
        for idx, wp in enumerate(wps):
            _pos(f"monsters.{mid}.waypoints[{idx}]", wp, bounds)
        tidx = m.get("target_idx", 1)
        if isinstance(tidx, bool) or tidx not in (0, 1):
            raise BadInput(f"monsters.{mid}.target_idx phải là 0 hoặc 1")
        st = m.get("state", "patrol")
        if st not in MONSTER_STATES:
            raise BadInput(f"monsters.{mid}.state không hợp lệ: {st!r}")
        ticks_left = m.get("state_ticks_left", 0)
        _nonneg_int(f"monsters.{mid}.state_ticks_left", ticks_left)
        rdir = m.get("recoil_dir")
        if st in ("recoil", "stunned") and ticks_left <= 0:
            raise BadInput(f"monsters.{mid}: trạng thái {st} cần state_ticks_left > 0")
        if st == "recoil":
            if not (isinstance(rdir, list) and len(rdir) == 2 and all(_num(c) for c in rdir)):
                raise BadInput(f"monsters.{mid}: recoil cần recoil_dir [x, d]")
        elif rdir is not None:
            raise BadInput(f"monsters.{mid}: recoil_dir phải là null khi state != 'recoil'")


def _pos_int(name, v):
    if isinstance(v, bool) or not isinstance(v, int) or v <= 0:
        raise BadInput(f"{name} phải là số nguyên dương")


def _validate_dish_payload(name, dish, menu):
    if not isinstance(dish, dict) or set(dish.keys()) != DISH_PAYLOAD_KEYS:
        raise BadInput(f"{name} phải có đúng các khóa {sorted(DISH_PAYLOAD_KEYS)}")
    if not isinstance(dish["order_id"], str) or not dish["order_id"]:
        raise BadInput(f"{name}.order_id phải là chuỗi khác rỗng")
    if dish["dish_id"] not in menu:
        raise BadInput(f"{name}.dish_id ngoài menu: {dish['dish_id']!r}")
    _pos_int(f"{name}.base_price", dish["base_price"])


def validate_quan_stock(block: dict, stock: dict, tuning: dict):
    """Kiểm tổng nguyên liệu giữ chỗ của các đơn `reserved` không vượt tồn kho `stock`."""
    menu = tuning["menu"]
    need = {}
    for c in block.get("customers", []):
        state = c.get("state", "waiting")
        status = c.get("order_status", "served" if state == "eating" else "reserved")
        if status != "reserved":
            continue
        res = c.get("reserved")
        if res is None:
            res = menu[c["dish_id"]]["recipe"]
        for k, qty in res.items():
            if qty > 0:
                need[k] = need.get(k, 0) + qty
    for k, qty in need.items():
        if qty > stock.get(k, 0):
            raise BadInput(f"nguyên liệu giữ chỗ '{k}' ({qty}) vượt tồn kho ({stock.get(k, 0)})")


def _validate_quan(b, tuning):
    q = tuning["quan"]
    menu = tuning["menu"]
    qb = q["bounds"]
    for arr in ("stoves", "tables", "customers"):
        if arr in b:
            _check_ids(arr, b[arr])
    if "stock" in b:
        validate_items(b["stock"])
    if "random_customers" in b and not isinstance(b["random_customers"], bool):
        raise BadInput("random_customers phải là boolean")
    if "reputation" in b:
        rep = b["reputation"]
        if not _num(rep) or not (q["reputation_min"] <= rep <= q["reputation_max"]):
            raise BadInput(f"reputation phải nằm trong [{q['reputation_min']}, {q['reputation_max']}]")

    p = b.get("player", {})
    if not isinstance(p, dict) or set(p) - QUAN_PLAYER_KEYS:
        raise BadInput("quan.player chỉ có pos và vel")
    if "pos" in p:
        _pos("player.pos", p["pos"], qb, axes=("x", "z"))
    if "vel" in p and not (isinstance(p["vel"], list) and len(p["vel"]) == 2 and all(_num(c) for c in p["vel"])):
        raise BadInput("player.vel phải là [x, z]")

    known_stoves = {s["id"] for s in q["stoves"]}
    known_tables = {t["id"] for t in q["tables"]}
    for tb in b.get("tables", []):
        extra = set(tb) - QUAN_TABLE_KEYS
        if extra:
            raise BadInput(f"tables.{tb['id']}: trường lạ {sorted(extra)}")
        if tb["id"] not in known_tables:
            raise BadInput(f"tables: id bàn không tồn tại: {tb['id']}")
        if "pos" in tb:
            _pos(f"tables.{tb['id']}.pos", tb["pos"], qb, axes=("x", "z"))

    held_dishes = {}  # order_id -> (source, dish_payload)
    for st in b.get("stoves", []):
        extra = set(st) - QUAN_STOVE_KEYS
        if extra:
            raise BadInput(f"stoves.{st['id']}: trường lạ {sorted(extra)}")
        if st["id"] not in known_stoves:
            raise BadInput(f"stoves: id bếp không tồn tại: {st['id']}")
        if "pos" in st:
            _pos(f"stoves.{st['id']}.pos", st["pos"], qb, axes=("x", "z"))
        state = st.get("state", "idle")
        if state not in STOVE_STATES:
            raise BadInput(f"stoves.{st['id']}.state không hợp lệ: {state!r}")
        dish = st.get("dish")
        cook_left = st.get("cook_ticks_left", 0)
        ready_ticks = st.get("ready_ticks", 0)
        _nonneg_int(f"stoves.{st['id']}.cook_ticks_left", cook_left)
        _nonneg_int(f"stoves.{st['id']}.ready_ticks", ready_ticks)
        if state == "idle":
            if dish is not None or cook_left != 0 or ready_ticks != 0:
                raise BadInput(f"stoves.{st['id']}: bếp idle không được có món hoặc timer dương")
        elif state == "cooking":
            _validate_dish_payload(f"stoves.{st['id']}.dish", dish, menu)
            if cook_left <= 0 or ready_ticks != 0:
                raise BadInput(f"stoves.{st['id']}: bếp cooking phải có cook_ticks_left > 0 và ready_ticks == 0")
        elif state == "ready":
            _validate_dish_payload(f"stoves.{st['id']}.dish", dish, menu)
            if cook_left != 0:
                raise BadInput(f"stoves.{st['id']}: bếp ready phải có cook_ticks_left == 0")
        if dish is not None:
            oid = dish["order_id"]
            if oid in held_dishes:
                raise BadInput(f"đơn {oid} xuất hiện ở nhiều bếp/tay")
            held_dishes[oid] = (f"stove:{st['id']}", dish)

    hand = b.get("hand")
    if hand is not None:
        _validate_dish_payload("hand", hand, menu)
        oid = hand["order_id"]
        if oid in held_dishes:
            raise BadInput(f"bếp và tay cùng giữ đơn {oid}")
        held_dishes[oid] = ("hand", hand)

    patience_max = int(round(q["patience_s"] * 60))
    eat_max = int(round(q["eat_s"] * 60))
    customers_by_id = {}
    table_ids = []
    for c in b.get("customers", []):
        cid = c["id"]
        extra = set(c) - QUAN_CUSTOMER_KEYS
        if extra:
            raise BadInput(f"customers.{cid}: trường lạ {sorted(extra)}")
        tid = c.get("table_id")
        if not isinstance(tid, str) or tid not in known_tables:
            raise BadInput(f"customers.{cid}: table_id phải là bàn có thật")
        table_ids.append(tid)
        dish_id = c.get("dish_id")
        if dish_id not in menu:
            raise BadInput(f"customers.{cid}: dish_id không hợp lệ: {dish_id!r}")
        if "order_tick" in c:
            _nonneg_int(f"customers.{cid}.order_tick", c["order_tick"])
        state = c.get("state", "waiting")
        if state not in CUSTOMER_STATES:
            raise BadInput(f"customers.{cid}.state không hợp lệ: {state!r}")
        status = c.get("order_status", "reserved")
        if status not in ORDER_STATUSES:
            raise BadInput(f"customers.{cid}.order_status không hợp lệ: {status!r}")
        if "patience_ticks_left" in c:
            _nonneg_int(f"customers.{cid}.patience_ticks_left", c["patience_ticks_left"])
            if c["patience_ticks_left"] > patience_max:
                raise BadInput(f"customers.{cid}.patience_ticks_left vượt patience tối đa")
        if "eat_ticks_left" in c:
            _nonneg_int(f"customers.{cid}.eat_ticks_left", c["eat_ticks_left"])
            if c["eat_ticks_left"] > eat_max:
                raise BadInput(f"customers.{cid}.eat_ticks_left vượt eat_s tối đa")
        res = None
        if "reserved" in c:
            res = validate_items(c["reserved"])
        if "base_price" in c and c["base_price"] is not None:
            _pos_int(f"customers.{cid}.base_price", c["base_price"])
        if "tip" in c and c["tip"] is not None:
            _nonneg_int(f"customers.{cid}.tip", c["tip"])

        if state == "eating":
            if status != "served":
                raise BadInput(f"customers.{cid}: khách eating phải có order_status='served'")
            if c.get("eat_ticks_left", 0) <= 0:
                raise BadInput(f"customers.{cid}: khách eating phải có eat_ticks_left > 0")
            if c.get("base_price") is None or c.get("tip") is None:
                raise BadInput(f"customers.{cid}: khách eating phải khai base_price và tip")
            if res:
                raise BadInput(f"customers.{cid}: khách eating phải có reserved rỗng")
        else:
            if status == "served":
                raise BadInput(f"customers.{cid}: khách waiting không thể có order_status='served'")
            if c.get("eat_ticks_left", 0) != 0:
                raise BadInput(f"customers.{cid}: khách waiting phải có eat_ticks_left == 0")
            if status == "reserved":
                expected = menu[dish_id]["recipe"]
                if res is not None and res != expected:
                    raise BadInput(f"customers.{cid}: reserved khác công thức món {dish_id}")
            elif status in ("assigned", "unfulfillable"):
                if res:
                    raise BadInput(f"customers.{cid}: đơn {status} phải có reserved rỗng")
        customers_by_id[cid] = (c, state, status)

    if len(table_ids) != len(set(table_ids)):
        raise BadInput("hai khách cùng bàn")

    for oid, (src, dish) in held_dishes.items():
        if oid not in customers_by_id:
            raise BadInput(f"{src}: tham chiếu order_id không tồn tại: {oid}")
        c, _state, status = customers_by_id[oid]
        if status != "assigned":
            raise BadInput(f"{src}: đơn {oid} có trạng thái '{status}', chỉ đơn 'assigned' mới có món ở bếp/tay")
        if dish["dish_id"] != c["dish_id"]:
            raise BadInput(f"{src}: món {dish['dish_id']} không khớp đơn {oid} ({c['dish_id']})")

    for cid, (_c, _state, status) in customers_by_id.items():
        if status == "assigned" and cid not in held_dishes:
            raise BadInput(f"customers.{cid}: đơn assigned phải có đúng một món ở bếp hoặc tay")

    if "stock" in b:
        validate_quan_stock(b, validate_items(b["stock"]), tuning)
