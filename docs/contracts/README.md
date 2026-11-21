# Hợp đồng tích hợp — Phase 1 (Test Contract v1.0)

> Chủ sở hữu: **M6 (Nguyễn Như Duy An — `K0heii`)**. Đã khóa theo `PRD0.md` (mục D, E, F, G). Mọi thay đổi hợp đồng phải báo cả nhóm và ghi lý do.

---

## 1. Schema file kho (`inventory` — PRD-0 mục G)
Khớp `chonoi/inventory.py` và [`inventory.sample.json`](inventory.sample.json):
```json
{"items":{"bong_sung":2,"ca_loc":1}}
```
- Khóa gốc duy nhất: `"items"`. Nguyên liệu hợp lệ (`KINDS_P1`): `"ca_loc"`, `"ca_linh"`, `"bong_dien_dien"`, `"bong_sung"`.
- Giá trị là số nguyên `>= 0`; kind vắng tính `0`; khi ghi bỏ khóa bằng `0`, sắp khóa tăng dần, ghi nguyên tử qua file tạm. Kho rỗng: `{"items":{}}`.
- Ghi **đúng 1 lần** khi `gather_end` (ngất `fainted` → kho rỗng). Hết `--ticks` trước khi kết thúc → không tạo/ghi đè file đích.
- Ở mode `quan`: chỉ nhận `--inventory` HOẶC `scenario.quan.stock` (cả hai → mã `2`). Thiếu cả hai → kho rỗng. Trần giỏ không áp lên kho quán.

---

## 2. Giao diện `sim/*` ↔ `client/ui` & Schema `snapshot` (PRD-0 mục D, E)
UI (`chonoi.live` / `chonoi/web/`) **chỉ đọc `snapshot`** và gửi input chuẩn:
- **Lệnh UI gửi vào (`POST /input`)**: `{"move": [a, b], "interact": bool, "catch": bool}` (`gather`: `[x, d]` với `d > 0` là xuống; `quan`: `[x, z]` với `z > 0` là bắc). `POST /restart` chơi lại cùng seed & scenario.
- **Trường chung mọi `snapshot`**:
  `type:"snapshot"`, `tick`, `sim_tick`, `mode`, `phase`, `phase_tick`, `state` (`"playing"|"finished"`), `time_left_ticks`, `money`, `earned`, `reputation`, `score` (`earned + 100 * floor(reputation)`).
- **Mode `gather`**:
  - `player`: `{pos, vel, heading_deg, oxygen_ticks, oxygen_max_ticks, hp, hp_max, zero_oxy_ticks, catch_cd_ticks, at_surface}` *(starter có thêm `invuln_ticks`)*.
  - `hold`: mảng `kind` theo thứ tự nhặt (mới nhất ở cuối — LIFO), `hold_count`, `hold_capacity`.
  - `nodes[]`: `[{id, pos, kind, ready, regrow_ticks}]` (`ready == (regrow_ticks == 0)`), sắp bằng `sort_by_id`.
  - `fish[]`: `[{id, pos, kind, heading_deg}]`, sắp bằng `sort_by_id`.
- **Mode `quan`**:
  - `player`: `{pos}` *(scenario nhận `{pos, vel}`)*.
  - `stock`: `{kind: qty}` (gồm cả phần giữ chỗ, chỉ liệt kê `> 0`, sắp theo key).
  - **Payload món** (dùng cho `hand` và `stoves[].dish`): `{"order_id": str, "dish_id": str, "base_price": int}` hoặc `null` (`order_id == customer.id`).
  - `stoves[]`: `[{id, pos, state, dish, cook_ticks_left, ready_ticks}]` (`state`: `"idle"|"cooking"|"ready"`).
  - `tables[]`: `[{id, pos, customer_id}]` (trống là `null`).
  - `customers[]` *(chỉ liệt kê khách còn ngồi, sắp bằng `sort_by_id`)*:
    `{id, table_id, dish_id, order_tick, state, patience_ticks_left, eat_ticks_left, order_status, reserved, base_price, tip}`
    - `state`: `"waiting"` (mặc định) hoặc `"eating"`.
    - `order_status`: `"reserved"` (mặc định) | `"assigned"` | `"unfulfillable"` | `"served"`.
    - `reserved`: map `{kind: qty}` (rỗng `{}` khi `assigned` hoặc `unfulfillable`).

---

## 3. Danh sách sự kiện chuẩn (PRD-0 mục E)
Mỗi dòng event: `{"type":"event","tick":<k+1>,"phase":"gather"|"quan","name":"<name>","data":{...}}`

### 3.1. Mode `gather` (M1 & M2)
| `name` | Chủ phát | `data` bắt buộc (đúng tên trường) |
|---|---|---|
| `node_regrown` | Starter / M2 | `{"node_id": str}` |
| `dive` | M1 | `{"pos": [x, d]}` (sau di chuyển, khi đổi từ mặt nước xuống dưới nước) |
| `surface` | M1 | `{"pos": [x, d]}` (sau di chuyển, khi đổi từ dưới nước lên mặt nước) |
| `oxygen_empty` | M1 | `{"oxygen_ticks": 0}` (khi từ `> 0` vừa chạm `0`) |
| `choke` | M1 | `{"hp": int}` (HP sau khi trừ 1) |
| `faint` | M1 | `{"cause": "choke", "lost": [kind, ...], "hp": 0}` (`lost` theo thứ tự LIFO) |
| `gather` | M2 | `{"node_id": str, "kind": str, "amount": int}` |
| `fish_caught` | M2 | `{"fish_id": str, "kind": str, "yield": int}` |
| `hold_full` | M2 | `{"action": "gather"|"catch", "node_id"|"fish_id": str, "required": int, "free": int}` |
| `gather_end` | Starter / M1 / M2 | `{"reason": "time"|"docked"|"fainted", "inventory": {"items": {...}}}` |

### 3.2. Mode `quan` (M3 & M4)
| `name` | Chủ phát | `data` bắt buộc (đúng tên trường) |
|---|---|---|
| `customer_arrived` | M3 | `{"order_id": str, "table_id": str, "dish_id": str}` |
| `no_dish` | M3 | `{}` (khi có bàn trống mà không món nào đủ nguyên liệu khả dụng) |
| `cook_started` | M4 | `{"stove_id": str, "order_id": str, "dish_id": str, "items": [kind, ...], "base_price": int}` (`items` sắp theo `kind`) |
| `dish_ready` | M4 | `{"stove_id": str, "order_id": str, "dish_id": str}` |
| `dish_picked` | M4 | `{"stove_id": str, "order_id": str, "dish_id": str}` |
| `served` | M4 | `{"order_id": str, "table_id": str, "dish_id": str, "patience_ticks_left": int, "base_price": int, "tip": int}` |
| `paid` | M4 | `{"order_id": str, "table_id": str, "base_price": int, "tip": int, "amount": int, "reason": "finished_eating"|"closing"}` |
| `customer_left` | M3 / M4 | `{"order_id": str, "table_id": str, "reason": "patience"|"closing", "reputation": float}` |
| `quan_end` | Starter / M4 | `{"reason": "time", "money": int, "earned": int, "shift_earned": int, "reputation": float}` |

---

## 4. Ràng buộc Scenario & Mâu thuẫn → Mã thoát `2` (PRD-0 mục D, cho `M6.3`)
- Khối sai mode, trường lạ/sai kiểu, id trùng trong mảng, id bếp/bàn cập nhật không tồn tại, tọa độ ngoài miền, bộ đếm âm/mâu thuẫn, giỏ vượt `hold_capacity`, khai cả `quan.stock` và `--inventory`, nguyên liệu/món ngoài phạm vi, khách trùng bàn.
- **Ràng buộc đơn hàng & món ở `quan`**:
  - Đơn `reserved`: `reserved` phải khớp công thức món (nếu thiếu thì tự cấp theo công thức theo thứ tự `order_tick` rồi `table_id`); tổng giữ chỗ không vượt tồn kho `stock`.
  - Đơn `assigned`: có **đúng 1 món** ở bếp (`cooking`/`ready`) hoặc trên `hand`, phần `reserved` rỗng `{}`.
  - Đơn `unfulfillable`: `state == "waiting"`, `reserved` rỗng `{}`, không có món ở bếp hay tay.
  - Khách `eating`: `order_status == "served"`, `eat_ticks_left > 0`, bắt buộc khai `base_price` và `tip` đã chốt.
  - Bếp `cooking`: `cook_ticks_left > 0` và `dish` khớp đơn hợp lệ. Bếp và `hand` không được giữ cùng 1 `order_id`, hoặc món không khớp đơn của khách.

## 5. Quy ước chung
- Mọi số liệu đọc từ `game.contract.json` (`tuning`), không hard-code.
- Ngẫu nhiên đi qua `Streams` (`chonoi/rng.py`), không dùng `random` toàn cục / đồng hồ hệ thống.
- Sắp thực thể bằng `ids.sort_by_id` (tiền tố, hậu tố số, id gốc: `F2` trước `F10`), cấp id bằng `IdAllocator`.
- Mọi tọa độ xuất tối đa 3 chữ số thập phân (do `jsonl.py` định dạng); tính khoảng cách/giá trước khi định dạng.

---

## 6. Nâng cấp Contract v1.1 (Phase 2 — `Ticket02.md`)
- **Manifest**: `contract_version: "1.1"`, bổ sung 2 nguyên liệu mới (`ca_keo`, `keo_neo` → `KINDS_P2` 6 loại), nút `N5/N6`, 3 món mới (`canh_chua_ca_loc`, `ca_keo_nuong`, `lau_mam` → 6 món), bếp `B2`, bàn `T2–T4`, `fish_initial: 8` + tham số cá bơi/sinh, `monsters` (`ca_sau` `M1`, `M2`), `day_plan` D1–D5, `shop` (`max_ticks: 600`, nâng cấp `oxygen`/`hp`).
- **CLI**: mở `--mode day` kèm `--days <1..5>` (mặc định `1`, chỉ dùng với `day`).
- **Inputs (`BUTTONS_V11`)**: thêm nút boolean `pause`, `shop_done` (cạnh lên) và chuỗi `buy` (chỉ chạy tại đúng frame khai báo, không kế thừa).
- **Scenario v1.1**:
  - Mode `day` nhận các khối `day`, `gather`, `quan`. Khối `day` nhận `{money, earned, reputation, upgrades, day_plan}` (`0 <= money <= earned`). **Cấm** khai `quan.stock` và `quan.reputation` trong `day`.
  - `gather.fish[]` thêm `age_ticks`; `gather.monsters[]` nhận `{id, kind, pos, waypoints, target_idx, state, state_ticks_left, recoil_dir}`.
- **Events mới v1.1**: `monster_hit`, `fish_spawned`, `faint` (`cause: "monster"`), `day_start`, `day_plan`, `phase_start`, `paused`, `resumed`, `bought`, `buy_failed`, `shop_end`.
- **Snapshot mới v1.1**: thêm `state: "paused"`, `monsters[]` trong `gather`; chế độ `day` thêm `day`, `day_plan`, `upgrades`, `active_upgrades` và `days_completed` trong dòng `end`.

