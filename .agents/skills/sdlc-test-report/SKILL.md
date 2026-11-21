---
name: sdlc-test-report
description: >-
  Kích hoạt sau khi code xong ở BẤT KỲ Phase nào (Phase 1, 2, 3, 4) để chạy kiểm thử hồi quy
  (unit tests), chạy headless mô phỏng thu hoạch/quán ăn, trích xuất bằng chứng JSONL vào
  docs/proof/phase-N/, phân tích snapshots/events, tự động cập nhật bảng ma trận kiểm chứng
  docs/verification/phase-N.md và nhật ký docs/ai-usage-log.md.
  Script kèm theo hỗ trợ cả Windows (python) và Linux/macOS (python3).
  Dùng chung cho mọi AI: Antigravity, Claude Code, Cursor, ChatGPT, Copilot.
---

# Skill: `sdlc-test-report` — Kiểm Thử Đa Phase, Xuất Bằng Chứng & Lập Báo Cáo

Skill này hướng dẫn AI đóng vai trò **QA Automation Engineer**, thực hiện kiểm thử tự động,
thu thập log JSONL làm bằng chứng nghiệm thu cho **Phase hiện tại (1, 2, 3 hoặc 4)**,
bảo đảm hệ thống không bị lỗi hồi quy (regression) và điền các báo cáo phục vụ chấm điểm Lab (15đ).

---

## 1. Khi nào kích hoạt?
- Sau khi hoàn thành code một Module/Task ở bất kỳ Phase nào.
- Trước khi tạo Git tag `phase-1`, `phase-2`, `phase-3`, `phase-4` hoặc mở PR.
- Khi người dùng yêu cầu:
  - *"chạy test và sinh báo cáo cho phase 2"*
  - *"xuất bằng chứng nghiệm thu phase 1"*
  - *"chạy test tích hợp gather sang quán"*

---

## 2. Ranh Giới An Toàn & Danh Sách Đen (CẤM ĐỤNG VÀO)

Khi chạy kiểm thử, sinh bằng chứng và lập báo cáo:

### ❌ Những Điều TUYỆT ĐỐI CẤM (Blacklist)
1. **CẤM SỬA TEST CONTRACT CỦA GIẢNG VIÊN / M6 ĐỂ LÀM XANH BÀI:**
   - ❌ Tuyệt đối không sửa `tests/test_smoke_*.py`, `tests/test_scenario.py`, `tests/test_contract.py`, `tests/test_inventory.py`, `tests/test_freshness_*.py`.
   - Nếu test fail $\rightarrow$ lỗi nằm ở code sim hoặc kịch bản input của module mình. Phải sửa code sim trong phạm vi được phân công, không sửa test mẫu.
2. **CẤM SỬA FRAMEWORK ĐỂ "HỖ TRỢ" TEST:**
   - ❌ Không sửa `chonoi/headless.py`, `chonoi/runner.py`, `chonoi/contract.py`, `chonoi/inputs.py`, `chonoi/jsonl.py`, `chonoi/ids.py`, `chonoi/scenario.py`, `chonoi/inventory.py`.
   - Mọi mock contract cho test suite riêng phải được định nghĩa cục bộ bên trong file test của module đó (ví dụ: dùng `unittest.mock.patch` trong `tests/test_gather_m2_p3.py`).
3. **CẤM GHI ĐÈ FILE BẰNG CHỨNG & PROFILE CỦA THÀNH VIÊN KHÁC:**
   - ❌ Không ghi đè hoặc sửa file trong `docs/proof/` của module khác.
   - ❌ Không sửa hồ sơ phản tư cá nhân `docs/members/<handle_khác>.md`.

### ✅ File ĐƯỢC PHÉP TẠO / CẬP NHẬT (Whitelist)
- **Test suite module mình:** `tests/test_<module>_p<N>.py` (ví dụ `tests/test_gather_m2_p3.py`).
- **File bằng chứng module mình:** `docs/proof/phase-<N>/m<X>*.json*`, `docs/proof/phase-<N>/m<X>.md`.
- **Ma trận nghiệm thu chung:** Cập nhật các dòng thuộc module mình trong `docs/verification/phase-<N>.md`.
- **Nhật ký:** `docs/ai-usage-log.md` (append dòng mới), `docs/standup.md`.

---

## 3. Cách chạy kiểm thử cho Phase bất kỳ

### Cách 1: Script tự động trọn gói (Khuyên dùng ⭐)
Script tự động nhận diện phase qua cờ `--phase <N>`:
```bash
# Chạy cho Phase 1:
python .agents/skills/sdlc-test-report/scripts/verify_and_report.py --phase 1 --mode gather --seed 1 --ticks 600 --log-ai --author "QuangNEU" --task-name "M2.4 Nghiệm thu Phase 1"

# Chạy cho Phase 2 (tương tự cho Phase 3, 4):
python .agents/skills/sdlc-test-report/scripts/verify_and_report.py --phase 2 --mode gather --seed 1 --ticks 600 --log-ai --author "QuangNEU" --task-name "Nghiệm thu Phase 2"

# Chạy tích hợp chuỗi 2 tiến trình (Gather -> xuất kho.json -> Quán nạp kho):
python .agents/skills/sdlc-test-report/scripts/verify_and_report.py --phase 1 --two-process --seed 1 --ticks 600 --log-ai --author "QuangNEU"
```

Script sẽ tự động:
1. Chạy Unit Tests toàn bộ (bảo đảm cả test cũ của Phase trước lẫn test mới đều PASS).
2. Chạy headless simulation và lưu log vào đúng thư mục `docs/proof/phase-<N>/`.
3. Phân tích snapshots và events.
4. Sinh file tóm tắt `docs/proof/phase-<N>/verification_summary.md`.
5. Nếu có cờ `--log-ai`: tự động append một dòng vào `docs/ai-usage-log.md`.

### Cách 2: Lệnh CLI thủ công (Theo AGENTS.md)
```bash
# 1. Chạy unit tests hồi quy (áp dụng cho mọi Phase):
python -m unittest discover -s tests -p "test_smoke_*.py" -v

# 2. Chạy headless buổi sáng (gather):
python -m chonoi.headless --mode gather --seed 1 --ticks 600 --out docs/proof/phase-<N>/gather_seed1.jsonl --inventory-out docs/proof/phase-<N>/kho.json

# 3. Chạy headless buổi tối (quán đọc kho từ gather):
python -m chonoi.headless --mode quan --seed 1 --inventory docs/proof/phase-<N>/kho.json --ticks 600 --out docs/proof/phase-<N>/quan_seed1.jsonl
```

---

## 3. Quy trình cập nhật Báo cáo Nghiệm thu Phase N

### Bước 1: Lưu trữ bằng chứng vào đúng thư mục
Mọi file log JSONL và file kho JSON của Phase $N$ phải nằm trong:
`docs/proof/phase-<N>/` (ví dụ: `docs/proof/phase-1/`, `docs/proof/phase-2/`...).

### Bước 2: Cập nhật Ma trận truy vết (`docs/verification/phase-<N>.md`)
Mở file `docs/verification/phase-<N>.md` tương ứng và điền kết quả từng AC:
```markdown
# Ma trận truy vết Phase <N>

| AC | Cách kiểm chứng | Bằng chứng (link docs/proof/phase-<N>/...) | Kết quả |
|---|---|---|---|
| AC-01: ... | Headless gather 600 ticks | [gather_seed1.jsonl](file:///docs/proof/phase-<N>/gather_seed1.jsonl) | Đạt |
| AC-02: ... | Headless quan đọc kho | [quan_seed1.jsonl](file:///docs/proof/phase-<N>/quan_seed1.jsonl) | Đạt |

## Đánh giá ngắn
- Yêu cầu nào đạt / chưa đạt: ...
- Điều cần chỉnh cho phase sau: ...
```

### Bước 3: Ghi Nhật ký AI (`docs/ai-usage-log.md`)
Đảm bảo dòng nhật ký được ghi vào `docs/ai-usage-log.md` (tự động qua cờ `--log-ai` hoặc ghi tay):
```
| <N> | <Tên/handle> | <Tên AI & Model> | Kiểm thử & xuất bằng chứng Phase <N> | ~<Tokens>k | Tất cả test pass, bằng chứng hợp lệ |
```

---

## 4. Checklist nghiệm thu trước khi gắn Tag `phase-<N>`
- [ ] Toàn bộ smoke test và unit test đều **OK** (bao gồm cả test của các phase trước).
- [ ] Chạy tích hợp 2 tiến trình: `gather` xuất kho $\rightarrow$ `quan` đọc kho thành công (exit code 0).
- [ ] Kiểm tra tính tất định: Chạy 2 lần cùng seed cho ra output JSONL và file kho giống hệt từng byte.
- [ ] File log đã lưu vào `docs/proof/phase-<N>/`.
- [ ] Ma trận kiểm chứng `docs/verification/phase-<N>.md` đã được điền trung thực.
