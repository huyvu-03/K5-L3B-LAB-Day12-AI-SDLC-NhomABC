---
name: sdlc-code
description: >-
  Kích hoạt khi bắt đầu viết code trong chonoi/sim/gather.py hoặc chonoi/sim/quan.py
  ở BẤT KỲ Phase nào (Phase 1, 2, 3, 4). Hướng dẫn AI tuân thủ 6 quy tắc bất biến của dự án:
  không hardcode, RNG tất định qua Streams, sắp xếp ID bằng sort_by_id, không phá framework,
  tính năng sáng tạo tắt ở headless, và BẢO TOÀN TÍNH NĂNG CỦA CÁC PHASE TRƯỚC (chống hồi quy).
  Sau khi code xong tự động cập nhật docs/ai-usage-log.md.
  Dùng chung cho mọi AI: Antigravity, Claude Code, Cursor, ChatGPT, Copilot.
---

# Skill: `sdlc-code` — Triển Khai Code Mô Phỏng Chuẩn Contract Đa Phase

Skill này hướng dẫn AI đóng vai trò **Simulation Engineer**, biến Dev Spec thành code Python
chính xác ở bất kỳ Phase nào (1, 2, 3, 4), bảo đảm vượt qua Test Contract tự động, test ẩn
chấm điểm và không làm hỏng tính năng của các phase trước đó.

---

## 1. Khi nào kích hoạt?
- Sau khi đã có Dev Spec từ skill `sdlc-spec` cho Phase tương ứng.
- Khi người dùng yêu cầu:
  - *"code module M2 theo spec phase 1"*
  - *"implement tính năng phase 2 cá bơi ngẫu nhiên"*
  - *"code lát bếp và bàn ăn phase 3"*

---

## 2. Sáu Quy Tắc Bất Di Bất Dịch (vi phạm = fail test tự động)

### ❌ QT-1: KHÔNG HARDCODE SỐ LIỆU
```python
# SAI — tuyệt đối cấm:
catch_cd = 30
hold_max = 12

# ĐÚNG — luôn đọc từ contract:
catch_cd = int(round(self.t["catch_cooldown_s"] * TICK))
hold_max = self.t["hold_capacity"]
```

### ❌ QT-2: KHÔNG DÙNG RANDOM TOÀN CỤC HOẶC ĐỒNG HỒ HỆ THỐNG
```python
# SAI:
import random; x = random.random()
import time; t = time.time()

# ĐÚNG — mọi ngẫu nhiên phải đi qua self.rng (Streams từ chonoi/rng.py):
x = self.rng.stream("fish_swim").random()
```

### ❌ QT-3: SẮP XẾP THỰC THỂ BẰNG sort_by_id
```python
# SAI:
for node in self.nodes:  # thứ tự không xác định

# ĐÚNG:
from ..ids import sort_by_id
for node in sort_by_id(self.nodes):
```

### ❌ QT-4: KHÔNG SỬA FRAMEWORK LÕI & FILE NGOÀI PHẠM VI (CẤM ĐỤNG VÀO)
AI phải tuyệt đối tuân thủ danh sách đen (Blacklist) dưới đây; vi phạm sửa các file này sẽ bị trừ điểm hoặc làm gãy pipeline CI/CD:

1. **Khung lõi chấm điểm của Giảng viên (CẤM SỬA TUYỆT ĐỐI):**
   - ❌ `chonoi/headless.py` (Điểm vào CLI chạy mô phỏng)
   - ❌ `chonoi/runner.py` (Vòng lặp điều phối tick)
   - ❌ `chonoi/contract.py` (Bộ nạp và kiểm tra contract)
   - ❌ `chonoi/inputs.py` (Parser nạp khung phím bấm)
   - ❌ `chonoi/jsonl.py` (Bộ ghi log JSONL đồng bộ)
   - ❌ `chonoi/ids.py` (Khung cấp ID `IdAllocator`)
   - ❌ `tools/check_team.py` (Script kiểm tra tính toàn vẹn nhóm)

2. **File Hợp đồng & Schema toàn dự án (ĐỘC QUYỀN M6 — PO/Integrator Duy An):**
   - ❌ `game.contract.json` (Khóa hợp đồng tuning, tick_hz, schema)
   - ❌ `docs/contracts/**` (Thư mục tài liệu đặc tả contract)
   - ❌ `chonoi/scenario.py` (Bộ validate kịch bản đầu vào)
   - ❌ `chonoi/inventory.py` (Adapter đọc/ghi kho)
   - ❌ `tests/test_smoke_*.py`, `tests/test_scenario.py`, `tests/test_contract.py`, `tests/test_inventory.py`, `tests/test_freshness_*.py` (Test hợp đồng do M6 quản lý; TUYỆT ĐỐI KHÔNG sửa test contract để ép test xanh)

3. **File thuộc phân công Module của thành viên khác (TRÁNH XUNG ĐỘT GIT):**
   - ❌ `chonoi/sim/quan.py`, `chonoi/sim/quan_customers.py` (Thuộc M3 — Cao & M4 — Minh)
   - ❌ `chonoi/sim/day.py`, `chonoi/sim/shop.py` (Thuộc M4 — Minh)
   - ❌ `chonoi/web/**`, `chonoi/live.py` (Thuộc M5 — Thanh)
   - ❌ `tests/test_quan*.py`, `tests/test_live.py` (Test của module khác)
   - ❌ `docs/specs/phase-*-m{1,3,4,5,6}.md` (Spec của module khác)
   - ❌ `docs/proof/phase-*/m{1,3,4,5,6}*` (Bằng chứng của module khác)
   - ❌ `docs/members/<handle_khác>.md` (Hồ sơ phản tư của bạn khác)

4. **PHẠM VI ĐƯỢC PHÉP SỬA THEO MODULE (WHITELIST):**
   - **Khi làm M1 (Huy):**
     - Code: `chonoi/sim/gather.py` (logic sinh tồn, lặn, ngạt, máu).
     - Test: `tests/test_gather_m1*.py`.
   - **Khi làm M2 (Quang):**
     - Code: **CHỈ DUY NHẤT** `chonoi/sim/gather.py` (logic giỏ LIFO, thu hoạch, bắt cá, cập bến, xuất kho). Mọi adapter tương thích phiên bản (như `_is_v12`) phải gói gọn bên trong `GatherSim.__init__`, tuyệt đối không chèn cờ vào `headless.py` hay `scenario.py`.
     - Test: `tests/test_gather_m2*.py`.
   - **Tài liệu & Bằng chứng của M1/M2:**
     - `docs/specs/phase-*-m1.md` / `m2.md`, `docs/proof/phase-*/m1*` / `m2*`.
     - Cập nhật ma trận `docs/verification/phase-*.md`.
     - Thêm dòng vào `docs/ai-usage-log.md`, `docs/standup.md`, và phản tư cá nhân `docs/members/<handle>.md`.

### ❌ QT-5: TÍNH NĂNG SÁNG TẠO TẮT Ở HEADLESS
UI, âm thanh, spritesheet chỉ được kích hoạt ở `chonoi/web/` hoặc `chonoi/live.py`.
Ở chế độ `headless`, mô phỏng phải chạy thuần logic và output JSONL giữ nguyên cấu trúc schema.

### ❌ QT-6: BẢO TOÀN TÍNH NĂNG PHASE TRƯỚC (CHỐNG HỒI QUY — REGRESSION GUARD)
> **Trọng số 25 điểm Test Ẩn:** Giảng viên sẽ chạy lại toàn bộ test của Phase $1 \dots N-1$ trên code của Phase $N$.
- Khi thêm cơ chế mới ở Phase 2, 3, 4: Các tham số/state mới **luôn phải có giá trị mặc định (fallback)**.
- Ví dụ: Scenario Phase 1 không có trường `weather` hoặc `fish_movement`, code Phase 2 phải xử lý mặc định an toàn (`scenario.get("weather", "calm")`).
- Tuyệt đối không làm gãy các test contract cũ đã pass.

---

## 3. Quy trình thực hiện

### Bước 1: Đọc Spec và Code Hiện Tại
- Mở Dev Spec tại `docs/specs/phase-<N>-<module>.md`.
- Mở `chonoi/sim/gather.py` hoặc `quan.py`, xác định vị trí cần bổ sung/chỉnh sửa.

### Bước 2: Implement từng lát logic
Viết code theo thứ tự từng bước mô tả trong Dev Spec:
- Cập nhật biến state (luôn dùng `.get(key, default)` nếu là trường mới).
- Xử lý điều kiện logic và tính toán.
- Sinh sự kiện: `events.append(("tên_event", {"key": value}))`.

### Bước 3: Tự kiểm tra Checklist (trước khi kết thúc)
- [ ] Không có hằng số cứng nào trong logic?
- [ ] Không import `random` hay dùng `time.time()`?
- [ ] Danh sách thực thể đã qua `sort_by_id`?
- [ ] ID mới được cấp qua `self.ids` (`IdAllocator`)?
- [ ] Code mới có làm hỏng kịch bản của các phase trước không?
- [ ] Chạy thử smoke test toàn bộ: `python -m unittest discover -s tests -p "test_smoke_*.py" -v` đạt OK!

### Bước 4: Ghi nhật ký AI (BẮT BUỘC)
Sau khi code xong, **ngay lập tức** thêm 1 dòng vào `docs/ai-usage-log.md`:
```
| <N> | <Tên/handle> | <Tên AI & Model> | <Mã Task>: Code <tính năng> Phase <N> | ~<Tokens>k | <AI đúng/sai chỗ nào, đã sửa thế nào> |
```
