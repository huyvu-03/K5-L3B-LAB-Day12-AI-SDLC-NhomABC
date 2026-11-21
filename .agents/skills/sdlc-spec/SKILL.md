---
name: sdlc-spec
description: >-
  Kích hoạt khi cần sinh bản Spec Dev và Spec Test cho một Module/Task ở BẤT KỲ Phase nào
  (Phase 1, 2, 3, 4). Skill tự động nhận diện Phase hiện tại, đọc file task (phase-N-task.md
  hoặc docs/plan/phase-N.md), đối chiếu game.contract.json và xuất tài liệu kỹ thuật vào
  docs/specs/phase-N-<module>.md, đồng thời tự động cập nhật docs/ai-usage-log.md.
  Dùng chung cho mọi AI: Antigravity, Claude Code, Cursor, ChatGPT, Copilot.
---

# Skill: `sdlc-spec` — Sinh Dev Spec & Test Spec Đa Phase (Phase 1–4)

Skill này hướng dẫn AI đóng vai trò **Software Architect & QA Lead**: phân tích yêu cầu
từ bảng phân công của nhóm ở **Phase hiện tại (1, 2, 3 hoặc 4)** và hợp đồng kỹ thuật
để sản xuất tài liệu đặc tả rõ ràng *trước khi* viết bất kỳ dòng code nào.

---

## 1. Khi nào kích hoạt?
- Bắt đầu một Phase mới (Phase 1, Phase 2, Phase 3, Phase 4) hoặc một Module/Task mới (`M1.1`, `M2.1`, `M3.1`...).
- Khi người dùng yêu cầu:
  - *"sinh spec cho module M2 phase 1"*
  - *"lập spec Dev + Test cho phase 2 tính năng cá di chuyển"*
  - *"phân tích yêu cầu phase 3 module M4"*

---

## 2. Ranh Giới Tác Vụ & Danh Sách Đen (CẤM ĐỤNG VÀO)

Khi phân tích yêu cầu và sinh tài liệu đặc tả (Spec), AI phải tuân thủ tuyệt đối ranh giới kiến trúc:

### ❌ File CẤM ĐỤNG VÀO (Blacklist)
1. **Khung lõi chấm điểm của Giảng viên:**
   - ❌ `chonoi/headless.py`, `chonoi/runner.py`, `chonoi/contract.py`, `chonoi/inputs.py`, `chonoi/jsonl.py`, `chonoi/ids.py`, `tools/check_team.py`.
2. **Hợp đồng & Schema hệ thống (Độc quyền M6 — PO/Integrator Duy An):**
   - ❌ `game.contract.json`, `docs/contracts/**`, `chonoi/scenario.py`, `chonoi/inventory.py`.
   - ❌ Toàn bộ test suite mẫu/hợp đồng của M6: `tests/test_smoke_*.py`, `tests/test_scenario.py`, `tests/test_contract.py`, `tests/test_inventory.py`, `tests/test_freshness_*.py`.
3. **Module và hồ sơ của thành viên khác:**
   - ❌ `chonoi/sim/quan.py`, `chonoi/sim/quan_customers.py`, `chonoi/sim/day.py`, `chonoi/sim/shop.py` (M3, M4).
   - ❌ `chonoi/web/**`, `chonoi/live.py` (M5).
   - ❌ `docs/specs/phase-*-m{khác}.md`, `docs/proof/phase-*/m{khác}*`.
   - ❌ `docs/members/<handle_khác>.md`.
4. **Không đề xuất kiến trúc vi phạm ranh giới:**
   - Spec **KHÔNG ĐƯỢC PHÉP** đề xuất sửa đổi các file ngoài module mình (ví dụ không đề xuất sửa `headless.py`, không thêm cờ vào `scenario.py`). Mọi adapter tương thích phiên bản phải được thiết kế gói gọn trong module của mình (`gather.py` hoặc `quan.py`).

### ✅ File ĐƯỢC PHÉP TẠO / SỬA (Whitelist)
- **Tài liệu đặc tả:** `docs/specs/phase-<N>-<module>.md` (ví dụ `docs/specs/phase-3-m2.md`).
- **Nhật ký AI:** Append dòng mới vào `docs/ai-usage-log.md`.

---

## 3. Quy trình thực hiện (5 bước bắt buộc)

### Bước 1: Nhận diện Phase & Nắm rõ phạm vi công việc
1. **Xác định Phase $N$:** Lấy từ yêu cầu của người dùng (1, 2, 3 hoặc 4). Nếu không nêu rõ, tự động tìm file task mới nhất trong workspace (`phase-4-task.md` $\rightarrow$ `phase-3-task.md` $\rightarrow$ `phase-2-task.md` $\rightarrow$ `phase-1-task.md` hoặc `docs/plan/phase-N.md`).
2. **Đọc tài liệu đầu vào của Phase đó:**
   - `phase-<N>-task.md` hoặc `docs/plan/phase-<N>.md`: Xác định mã task, người phụ trách, việc cần làm, phụ thuộc.
   - `AGENTS.md`: Xác định module & file phạm vi phụ trách của thành viên (`M1`..`M6`).
   - Đề bài / PRD của phase tương ứng (`PRD0.md` hoặc thông báo mới mở tại lab board).

### Bước 2: Khóa tham số hợp đồng & Nhận diện thay đổi (Delta)
- Đọc `game.contract.json["tuning"]` và liệt kê **toàn bộ key** mà module này sẽ sử dụng.
- **Nếu là Phase 2, 3, 4:** Đối chiếu xem có trường mới, loài cá mới, món mới hay tham số mới nào được bổ sung so với phase trước không.
> **Quy tắc bất biến:** Mọi hằng số phải đọc từ `self.t` (tuning object), tuyệt đối không hardcode số trong code logic.

### Bước 3: Đọc code hiện tại & Bảo đảm tương thích
Mở `chonoi/sim/gather.py` hoặc `chonoi/sim/quan.py`:
- Xác định vị trí `TODO(nhóm)` cần hoàn thiện ở Phase này.
- Kiểm tra các hàm và state đã có từ phase trước để đảm bảo **không làm thay đổi hoặc phá vỡ các tính năng cũ đã pass test**.

### Bước 4: Soạn tài liệu và lưu
Tạo file `docs/specs/phase-<N>-<module>.md` với 2 phần rõ ràng:

**Phần A — Dev Spec:**
- Danh sách tham số contract sử dụng (key $\rightarrow$ giá trị từ file).
- Mô tả logic từng bước trong `step()` theo thứ tự tick.
- Công thức tính (kẹp biên `clamp`, hồi chiêu, sản lượng, di chuyển, kinh tế...).
- Danh sách event cần bắn ra: `("tên_event", {"payload": ...})`.
- Quy tắc deterministic: hàm nào dùng `self.rng` (`Streams`), hàm nào dùng `sort_by_id`.
- **Lưu ý tương thích ngược (Backward Compatibility):** Trường mới phải có giá trị mặc định để không làm gãy kịch bản cũ.

**Phần B — Test Spec (Ma trận AC):**

| Mã AC | Tiêu chí nghiệm thu | Kịch bản kiểm thử | Kết quả mong đợi |
|---|---|---|---|
| AC-M?-01 | ... | Headless / Unit test scenario | ... |

Mỗi AC phải có: điều kiện đầu vào cụ thể (pos, hold, ticks, scenario), lệnh headless kiểm chứng,
và trường JSONL cần đối soát.

### Bước 5: Ghi nhật ký AI (BẮT BUỘC)
Sau khi lưu spec, **ngay lập tức** thêm 1 dòng vào `docs/ai-usage-log.md`:
```
| <N> | <Tên/handle> | <Tên AI & Model> | <Mã Task>: Lập Dev Spec + Test Spec Phase <N> | ~<Tokens>k | <Ghi chú nếu có> |
```

---

## 3. Template output chuẩn

```markdown
# Spec Kỹ Thuật: [Tên Module / Task] — Phase [N]

## A. Dev Spec
### 1. Tham số contract sử dụng (`game.contract.json["tuning"]`)
| Key (`self.t["..."]`) | Giá trị | Ý nghĩa |
|---|---|---|
| `...` | ... | ... |

### 2. Logic step() — theo thứ tự tick
1. Giảm bộ đếm / hồi chiêu: `self.xxx = max(0, self.xxx - 1)`.
2. Xử lý logic tính năng mới của Phase N.
3. Sinh event: `events.append(("tên_event", {...}))`.

### 3. Bảo toàn tính năng cũ
- Các scenario không có tham số mới vẫn chạy bình thường với giá trị mặc định.

## B. Test Spec (Ma trận AC)
| Mã AC | Tiêu chí | Kịch bản | Kết quả mong đợi |
|---|---|---|---|
| AC-M?-01 | ... | `--mode ... --ticks ...` | ... |
```
