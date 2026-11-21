# Spec Kỹ Thuật: Module M2 (Giỏ Cá Thể, Cấp ID, Hao Độ Tươi & Xuất Kho v1.2) — Phase 3

- **Module:** M2 — Giỏ cá thể `gather.hold` dạng mảng `[{"id": "I1", "kind": "...", "fresh": 100.0}]`, Cấp ID `I1, I2...` tăng dần liên tục, Hao độ tươi giỏ `-0.5/s` (trừ 2 đơn vị/tick ở 60 Hz), Bắn event `spoiled` khi `< 30.0` sắp theo `id`, Xuất kho cá thể Contract v1.2.
- **Thành viên phụ trách:** Nguyễn Minh Quang (`QuangNEU`)
- **Tài liệu căn cứ:** [Ticket-03](../../Ticket03.md), [phase-3-task.md](../../phase-3-task.md), [Test Contract v1.2](../contracts/README.md)

---

## A. Dev Spec

### 1. Tham số Contract v1.2 sử dụng (`game.contract.json["tuning"]`)

| Key (`self.t["..."]`) | Giá trị | Ý nghĩa |
|---|---|---|
| `freshness.initial` | `100.0` | Độ tươi ban đầu của mọi nông sản vừa hái/bắt |
| `freshness.gather_decay_per_s` | `0.5` (điểm/s) | Tốc độ hao độ tươi trong giỏ ở ca lặn sáng |
| `freshness.spoiled_below` | `30.0` | Ngưỡng xác định nguyên liệu bị ươn / hỏng |
| `tick_hz` | `60` | Tần số mô phỏng (60 tick = 1 giây) |
| `gather.hold_capacity` | `12` | Sức chứa tối đa của giỏ thuyền |
| `gather.node_yield` | `1` | Sản lượng hái mỗi nút cây mặt nước |
| `gather.fish_yield` | `{"ca_linh": 3, "ca_loc": 1, "ca_keo": 2}` | Sản lượng bắt mỗi đàn cá |

---

### 2. Kỹ thuật khử sai số số thực bằng số nguyên 240 đơn vị
- Chuẩn hóa theo `chonoi/freshness.py`:
  - `FRESH_SCALE = 240` đơn vị mỗi điểm tươi.
  - Ban đầu `fresh = 100.0` $\rightarrow$ `units = 24000`.
  - Hao tươi `gather`: $0.5\text{ điểm/s} / 60\text{ Hz} = 1/120\text{ điểm/tick}$.
    Mỗi tick trừ chính xác: `decay_units = 2` đơn vị nguyên.
  - Ngưỡng ươn `30.0`: `spoiled_threshold_units = 30 * 240 = 7200` đơn vị nguyên.
  - So sánh điều kiện ươn: `units < 7200` chính xác tuyệt đối từng tick, không có sai số dấu phẩy động.

---

### 3. Cấp phát ID cá thể (`I1, I2...`) tăng dần liên tục
- Mọi cá thể sinh ra từ hái cây hoặc bắt cá đều được cấp ID duy nhất qua `self.ids.new("I")`.
- ID tăng dần liên tục xuyên suốt các ca/Ngày (Day 1 $\rightarrow$ Day 2...), không bao giờ reset về 1.
- Bắt cá có sản lượng $> 1$ (ví dụ `ca_keo` yield 2, `ca_linh` yield 3) sẽ sinh ra từng cá thể độc lập với ID riêng biệt (`I1`, `I2`...).

---

### 4. Thứ tự tick trong `step()` (Thứ tự ưu tiên xử lý)
1. **Đồng hồ & Nút mọc lại:** Giảm bộ đếm `phase_tick`, `time_left_ticks`, `invuln_ticks`, `catch_cd_ticks`; nút mọc lại bắn `node_regrown`.
2. **Hao độ tươi giỏ (ở đầu tick, trước khi lặn/ngạt/bị đánh):**
   - Lặp qua từng cá thể trong `self.hold`:
     - Lưu `old_u = it["units"]`.
     - `new_u = max(0, old_u - self.decay_units)`.
     - `it["units"] = new_u`.
     - Nếu `old_u >= 7200` và `new_u < 7200`: cá thể vừa vượt ngưỡng ươn.
   - Gom tất cả cá thể vừa ươn trong tick, **sắp xếp theo `id` tăng dần** qua `sort_by_id(spoiled_list)`.
   - Với mỗi cá thể, bắn event:
     `("spoiled", {"item_id": it["id"], "kind": it["kind"], "location": "hold"})`
   - **Lưu ý:** Không thay đổi thứ tự giỏ `self.hold` (vẫn giữ nguyên thứ tự LIFO).
3. **Bơi & Kiểm tra bề mặt (`_move`):** Cập nhật vị trí, bắn `surface` hoặc `dive`.
4. **Oxy & Ngạt (`_update_oxygen`):** Nếu ngạt $\rightarrow$ bắn `choke`, nếu ngất $\rightarrow$ rơi giỏ theo LIFO và kết thúc.
5. **Quái vật Cá Sấu (`_update_monsters`):** Nếu trúng đòn $\rightarrow$ rơi số lượng cá thể theo LIFO, bắn `monster_hit`.
6. **Tương tác Cập bến / Hái cây (`interact`):**
   - Ưu tiên cập bến: trong bến $\rightarrow$ `docked`, xuất kho cá thể v1.2.
   - Hái mặt nước: nếu còn chỗ $\rightarrow$ cấp ID mới `self.ids.new("I")`, thêm vào `hold` với `units = 24000` (chưa bị hao ở tick vừa hái).
7. **Bắt cá (`catch`):** Nếu dưới nước và hết cooldown $\rightarrow$ cấp các ID mới cho từng con trong sản lượng, thêm vào `hold` với `units = 24000`.
8. **Hết giờ:** Hết giờ $\rightarrow$ `time`, giữ nguyên giỏ.
9. **Cá bơi & Sinh cá Phase 2:** Bơi 1.5 m/s, phản xạ mép, sinh đàn cá 360 tick.

---

### 5. Định dạng Snapshot và Xuất kho v1.2
- **Snapshot `hold`:**
  - Nếu `_is_v12`: `[{"id": it["id"], "kind": it["kind"], "fresh": round(from_units(it["units"]), 6)} for it in self.hold]`
  - Nếu v1.1/v1.0: `[it["kind"] for it in self.hold]` (bảo toàn tương thích ngược 100%).
- **Xuất kho cập bến (`gather_end.inventory`):**
  - Mảng cá thể `items`: `[{"id": it["id"], "kind": it["kind"], "fresh": round(from_units(it["units"]), 6)} for it in sort_by_id(self.hold)]`
  - Nếu ngất (`fainted`): `{"items": []}`.

---

## B. Test Spec (Ma trận AC — 10 tiêu chí nghiệm thu)

| Mã AC | Tiêu chí nghiệm thu | Kịch bản kiểm thử | Kết quả mong đợi |
|---|---|---|---|
| **AC-P3-M2-01** | Cấp ID `I1, I2...` tăng dần khi hái nút hoặc bắt cá | Hái nút N1 (`bong_dien_dien`) rồi bắt cá F1 (`ca_linh`) | `hold[0].id == "I1"`, `hold[1].id == "I2"` |
| **AC-P3-M2-02** | Chuỗi ID `I1, I2...` duy nhất và liên tục xuyên pha/ngày | Cấp ID ở ngày 1, chuyển ngày 2 cấp tiếp | Không reset về 1, ID tiếp theo là `I3, I4...` |
| **AC-P3-M2-03** | Độ tươi ban đầu đúng 100.0 tại tick thu hoạch | Hái nút N1 ở tick 0 | Snapshot tick 1 có `fresh == 100.0` (chưa bị hao) |
| **AC-P3-M2-04** | Tốc độ hao tươi giỏ đúng 0.5 điểm/giây (2 đơn vị/tick) | Chạy 60 tick sau khi hái | Độ tươi giảm từ 100.0 xuống đúng 99.50 |
| **AC-P3-M2-05** | Ngưỡng ươn `< 30.0` bắn event `spoiled` đúng 1 lần | Fixture `hold` có item fresh = 30.0 | Sau 1 tick hao bắn `spoiled` (`location: "hold"`), tick kế không bắn lại |
| **AC-P3-M2-06** | Nhiều cá thể cùng ươn bắn event theo thứ tự `id` tăng dần | Fixture `hold` chứa `I10` và `I2` cùng fresh = 30.0 | Event `spoiled` của `I2` phát trước `I10` |
| **AC-P3-M2-07** | Hàng ươn vẫn chiếm 1 ô giỏ, đủ 12 ô bắn `hold_full` | Giỏ chứa 12 cá thể ươn (fresh < 30), thực hiện hái | Bắn event `hold_full` (`action: "gather"`), không nhặt thêm |
| **AC-P3-M2-08** | Bắt cá có yield > 1 sinh đủ cá thể với ID riêng | Bắt cá kèo `ca_keo` (yield = 2) | Sinh 2 cá thể riêng biệt trong giỏ với 2 ID khác nhau |
| **AC-P3-M2-09** | Ngất do ngạt làm rỗng giỏ và xuất file kho rỗng | Để nhân vật cạn oxy ngất ở tick ngạt cuối | Event `faint` có `lost` mảng cá thể LIFO, file kho `{"items": []}` |
| **AC-P3-M2-10** | Cập bến xuất file kho mảng cá thể đúng Contract v1.2 | Nhân vật cập bến sau khi thu hoạch | File kho JSON có dạng `{"items": [{"id": ..., "kind": ..., "fresh": ...}]}` sắp theo `id` |
