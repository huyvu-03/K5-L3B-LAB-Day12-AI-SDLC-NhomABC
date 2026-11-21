# Spec Kỹ Thuật: Module M2 (Cá Bơi, Sinh Cá & Tài Nguyên Mới) — Phase 2

- **Module:** M2 — Đàn cá bơi, Đổi hướng, Phản xạ mép, Sinh cá theo lịch, Nguyên liệu mới (`ca_keo`, `keo_neo`, nút `N5`, `N6`)
- **Thành viên phụ trách:** Nguyễn Minh Quang (`QuangNEU`)
- **Tài liệu căn cứ:** [TICKET-02](../../Ticket02.md) (mục 1.1, 4.1, 4.4, 4.5), [phase-2-task.md](../../phase-2-task.md), [Test Contract v1.1](../contracts/README.md)

---

## A. Dev Spec

### 1. Tham số Contract v1.1 sử dụng (`game.contract.json["tuning"]["gather"]`)

| Key | Giá trị chuẩn | Ý nghĩa |
|---|---|---|
| `fish_speed` | `1.5` (m/s) | Tốc độ bơi đều của đàn cá |
| `fish_turn_ticks` | `120` (tick = 2.0 s) | Chu kỳ đổi góc hướng ngẫu nhiên |
| `fish_max` | `12` | Trần số lượng đàn cá tối đa cùng tồn tại trong sông |
| `fish_spawn_ticks` | `360` (tick = 6.0 s) | Chu kỳ xét sinh thêm đàn cá mới (`phase_tick = 360 * k`) |
| `fish_spawn_clearance` | `1.0` (m) | Khoảng cách tối thiểu từ điểm sinh đến mọi đàn cá đang sống |
| `fish_x` | `[4, 96]` | Biên bơi ngang của đàn cá |
| `fish_depths` | `{"ca_linh": [3, 12], "ca_loc": [8, 20], "ca_keo": [22, 28]}` | Dải độ sâu bơi của từng loài cá |
| `fish_spawn_x` | `[15, 30, 45, 60, 75, 90]` | Các tọa độ x ứng viên để sinh cá |
| `fish_spawn_depths` | `{"ca_linh": [5, 10], "ca_loc": [10, 16], "ca_keo": [24, 27]}` | Các tọa độ d ứng viên để sinh cá của từng loài |
| `fish_weights` | `{"ca_linh": 0.4, "ca_loc": 0.3, "ca_keo": 0.3}` | Trọng số xác suất chọn loài khi sinh cá |
| `fish_yield` | `{"ca_linh": 3, "ca_loc": 1, "ca_keo": 2}` | Sản lượng thu được khi bắt từng loài |
| `nodes` | Thêm `N5 [76, 0]`, `N6 [90, 0]` (`keo_neo`) | Nút cây mới hái bông kèo nèo ở mặt nước |

---

### 2. Kiến trúc Module tách biệt (`chonoi/sim/fish.py`)
Để tránh xung đột code giữa M2 (cá bơi/sinh) và M1 (Huy làm Cá Sấu) trên file [gather.py](../../chonoi/sim/gather.py), toàn bộ logic quản lý đàn cá được đóng gói vào module helper [chonoi/sim/fish.py](../../chonoi/sim/fish.py):
- `init_fish(...)`: Khởi tạo đàn cá đầu ca (8 đàn cố định hoặc từ scenario fixture).
- `step_fish_movement(...)`: Xử lý đổi hướng, bơi, phản xạ mép.
- `step_fish_spawning(...)`: Xử lý kiểm tra chu kỳ 360 tick, lọc điểm sinh hợp lệ, chọn loài, bắn event `fish_spawned`.

---

### 3. Logic chi tiết từng cơ chế

#### 3.1. Cơ chế Cá bơi & Đổi hướng (`fish_swim`)
- Mỗi đàn cá có: `id`, `kind`, `pos = [x, d]`, `heading_deg`, `age_ticks`.
- **Thứ tự tick:**
  1. Kiểm tra đổi hướng: Nếu `age_ticks > 0` và `age_ticks % 120 == 0`, rút góc hướng mới từ luồng RNG:
     $$\text{heading\_deg} = \text{self.rng.stream("fish_swim").random()} \times 360.0$$
  2. Tính vector di chuyển trong 1 tick ($\Delta t = 1/60\text{ s}$):
     $$vx = v \cdot \cos(\text{rad}), \quad vd = v \cdot \sin(\text{rad}) \quad (\text{với } v = 1.5)$$
     $$x_{\text{new}} = x + vx / 60, \quad d_{\text{new}} = d + vd / 60$$
  3. **Phản xạ mép (Elastic Reflection):**
     - Biên di chuyển của loài: $x \in [4, 96]$, $d \in [d_{\min}, d_{\max}]$.
     - Nếu $x_{\text{new}} < 4$: phản xạ $x_{\text{new}} = 4 + (4 - x_{\text{new}})$, đảo vận tốc $vx = -vx$, cập nhật lại góc hướng $\text{heading\_deg}$.
     - Nếu $x_{\text{new}} > 96$: phản xạ $x_{\text{new}} = 96 - (x_{\text{new}} - 96)$, đảo $vx = -vx$.
     - Tương tự cho trục độ sâu $d$ với $[d_{\min}, d_{\max}]$.
     - Nếu chạm góc (cả 2 trục cùng vượt biên): đảo cả $vx$ và $vd$.
  4. Tăng số bước đã tham gia bơi: `age_ticks += 1`.

#### 3.2. Cơ chế Sinh cá (`fish_spawn`)
- **Điều kiện kích hoạt:**
  - `phase_tick > 0` và `phase_tick % 360 == 0`.
  - Tổng số đàn cá hiện tại $\text{len}(\text{self.fish}) < 12$.
- **Lọc điểm sinh hợp lệ:**
  - Điểm sinh hợp lệ của một loài là điểm $(x, d)$ từ bảng `fish_spawn_x` $\times$ `fish_spawn_depths[kind]` thỏa mãn:
    $$\forall f \in \text{self.fish}: \text{dist}((x, d), f[\text{"pos"}]) > 1.0\text{ m}$$
- **Chọn loài & Điểm:**
  - Lọc các loài còn ít nhất 1 điểm sinh hợp lệ. Nếu không còn loài nào: bỏ lượt sinh (không làm gì).
  - Chuẩn hóa lại trọng số xác suất giữa các loài hợp lệ từ `fish_weights` (ví dụ nếu thiếu `ca_linh`, chia lại giữa `ca_loc` và `ca_keo` theo tỷ lệ 50/50).
  - Chọn loài qua luồng RNG `self.rng.stream("fish_spawn")`.
  - Chọn đều một điểm trong các điểm hợp lệ của loài đó.
  - Rút góc hướng ban đầu ngẫu nhiên trong $[0, 360)$.
  - Cấp ID mới qua `self.ids.new("F")`.
  - Thêm đàn cá mới vào `self.fish` với `age_ticks = 0`.
  - Bắn event: `("fish_spawned", {"id": new_id, "kind": kind, "pos": [round(x, 3), round(d, 3)]})`.
  - *Lưu ý:* Đàn cá vừa sinh không tham gia bơi hay bắt trong tick hiện tại; bắt đầu tham gia từ tick kế tiếp.

#### 3.3. Thu hoạch cây mới (`keo_neo`) & Bắt cá kèo (`ca_keo`)
- Bông kèo nèo tại `N5 [76, 0]`, `N6 [90, 0]`: áp dụng toàn bộ logic hái cây của Phase 1 (`node_yield: 1`, `regrow_s: 20`, sản vật `"keo_neo"`).
- Cá kèo (`ca_keo`): sản lượng bắt đàn `yield = 2`, bắt ở độ sâu dưới nước trong bán kính $2.0\text{ m}$.
- File kho: chấp nhận thêm 2 nguyên liệu mới: `"ca_keo"`, `"keo_neo"` nâng tổng danh mục lên 6 nguyên liệu (`KINDS_P2`).

---

### 4. Thứ tự xử lý trong `step()` (Contract v1.1 mục 4.5)
1. Giảm bộ đếm (hồi chiêu bắt cá, mọc lại cây).
2. Di chuyển người chơi, tính oxy, ngạt (M1).
3. Người chơi tương tác `interact` (bến trước, hái sau gồm cả `N5`, `N6`).
4. **Bắt cá (`catch`):** Xét bắt cá theo **vị trí của đàn cá TRƯỚC KHI cá bơi** trong tick này.
5. Kiểm tra kết thúc sớm (ngất `fainted`, cập bến `docked`, hết giờ `time`).
6. **Nếu chưa kết thúc và `random_fish != False`:**
   - Đàn cá thực hiện bơi, phản xạ mép, cập nhật hướng.
   - Xét sinh cá mới nếu chạm mốc $360\text{ tick}$ $\rightarrow$ bắn `fish_spawned`.

---

## B. Test Spec (Ma trận AC)

| Mã AC | Tiêu chí kiểm thử | Kịch bản / Fixture đầu vào | Lệnh kiểm chứng & Trường đối soát | Kết quả mong đợi |
|---|---|---|---|---|
| **AC-P2-M2-01** | **Cá bơi đúng vận tốc 1.5 m/s** | Fixture: Đàn cá `F1` tại `[15, 5]`, `heading_deg: 0` (+x). Chạy 60 tick. | `--mode gather --scenario ... --ticks 60` | Sau 60 tick cá di chuyển được $1.5\text{ m}$ sang phải $\rightarrow \text{pos}[0] \approx 16.5$. |
| **AC-P2-M2-02** | **Đổi hướng ở tick 120** | Fixture: Đàn cá `F1` tại `[50, 10]`, `heading_deg: 0`. Chạy 121 ticks. | So sánh `heading_deg` tại tick 119 và tick 121. | Tại tick 120, cá đổi sang góc hướng mới từ RNG `fish_swim`. |
| **AC-P2-M2-03** | **Phản xạ mép biên** | Fixture: Đàn cá `F1` tại `[95.9, 10]`, hướng bơi $0^\circ$ (tiến về mép $x=96$). Chạy 6 tick. | Kiểm tra tọa độ $x$ sau khi chạm mép $96$. | Tọa độ bật ngược lại trong $[4, 96]$, thành phần $vx$ bị đảo chiều. |
| **AC-P2-M2-04** | **Sinh cá theo chu kỳ 360 tick** | Chạy headless với `--ticks 361 --seed 1`. | Đối soát events tại tick 360. | Bắn event `fish_spawned` với `id`, `kind`, `pos`. Tổng đàn cá tăng từ 8 lên 9. |
| **AC-P2-M2-05** | **Không sinh cá khi chạm trần 12 đàn** | Fixture: 12 đàn cá đã tồn tại. Chạy qua tick 360. | Kiểm tra event tại tick 360. | Không bắn event `fish_spawned`. Tổng đàn cá giữ nguyên 12. |
| **AC-P2-M2-06** | **Khoảng cách sinh $> 1\text{ m}$** | Đàn cá mới sinh không được trùng hoặc cách bất kỳ đàn đang sống $\le 1.0\text{ m}$. | Kiểm tra khoảng cách Euclid từ `pos` đàn mới đến mọi đàn cũ. | Khoảng cách $> 1.0\text{ m}$. |
| **AC-P2-M2-07** | **Hái bông kèo nèo (`N5`, `N6`)** | Fixture: Player tại `[76, 0]`, nút `N5` sẵn sàng. Nhấn `interact`. | Đối soát event `gather`. | Bắn event `gather` với `node_id: "N5", kind: "keo_neo", amount: 1`. |
| **AC-P2-M2-08** | **Bắt cá kèo (`ca_keo`)** | Fixture: Player dưới nước tại `[15, 25]`, đàn cá kèo `F1`. Nhấn `catch`. | Đối soát event `fish_caught`. | Bắn `fish_caught` với `kind: "ca_keo", yield: 2`. Thêm 2 cá kèo vào `hold`. |
| **AC-P2-M2-09** | **Cờ `random_fish: false`** | Fixture có `random_fish: false`. Chạy 600 ticks. | So sánh vị trí đàn cá qua các tick. | Cá đứng yên, không bơi, không sinh thêm đàn mới (tương thích Phase 1). |
| **AC-P2-M2-10** | **Xuất file kho 6 nguyên liệu** | Thu hoạch đủ 6 loại nguyên liệu, cập bến xuất file kho. | Đối soát nội dung file kho JSON. | File kho hợp lệ chứa đủ các khóa nguyên liệu mới, sắp xếp key Unicode. |
