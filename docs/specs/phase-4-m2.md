# Spec Kỹ Thuật: Nghiệm Thu Độ Ổn Định Soak Test 10 Ngày & Bàn Giao Giỏ Cá Thể (`soak_cmd`) — Phase 4

> **Tài liệu đặc tả (Dev Spec & Test Spec) Module M2 — Phase 4**
>
> - **Người thực hiện:** Nguyễn Minh Quang (`QuangNEU` — M2)
> - **Phối hợp:** Nguyễn Nhật Minh (`NhMinh-2610` — M4) & Nguyễn Như Duy An (`K0heii` — M6 / PO)
> - **Phiên bản Hợp đồng:** Test Contract v1.3 (`game.contract.json`)
> - **Mục tiêu:** Kiểm định độ bền bỉ, tính tất định và chuyển tiếp chu kỳ 10 Ngày không crash của `soak_cmd`, bảo toàn trạng thái giỏ cá thể và bộ cấp ID.

---

## A. Dev Spec

### 1. Tham số & Định dạng Hợp đồng (`game.contract.json`)

| Khóa Contract | Kiểu | Giá trị quy định | Ý nghĩa |
|---|---|---|---|
| `contract_version` | `str` | `"1.3"` | Phiên bản hợp đồng Phase 4 phát hành `v1.0.0` |
| `soak_cmd` | `str` | `"python3 -m chonoi.soak"` | Lệnh chạy soak test chính thức của dự án |
| `--seed` | `int` | `7` (hoặc số nguyên dương) | Hạt giống RNG tất định cho toàn bộ mô phỏng |
| `--days` | `int` | `10` | Số ngày chạy liên tục trong 1 tiến trình |
| `--out` | `str` | Đường dẫn file JSON xuất ra | File lưu kết quả kiểm định soak (ví dụ: `docs/proof/phase-4/soak.json`) |

#### Schema File Output JSON (`soak.json`):
```json
{
  "days": 10,
  "days_completed": 10,
  "crashes": 0,
  "results": [
    {
      "day": 1,
      "earned": 0,
      "reputation": 50.0,
      "score": 0
    },
    ...
  ],
  "duration_s": 0.85
}
```

---

### 2. Kiến Trúc & Vòng Đời Điều Phối 10 Ngày Headless

1. **Tiến trình đơn (Single Process Runner):**
   - Khởi tạo duy nhất một `Session("day", tuning, {}, seed=seed, days=days)`.
   - Vòng lặp `while not sess.done and sess.tick < max_ticks:` điều phối từng bước với `_bot_input(sess)`.
2. **Ba Phase mỗi Ngày (Gather $\rightarrow$ Quan $\rightarrow$ Shop):**
   - **Phase Gather:** Bắt đầu tại bến `[2, 0]`. Bot tất định thực hiện cập bến ngay tại `phase_tick == 0` bằng action `interact: True` để bàn giao kho cá thể an toàn sang Quán.
   - **Phase Quan:** Vận hành quán ăn với kho cá thể nhận từ Gather. Bot chờ hết thời gian ca để phục vụ khách tối đa trong khuôn khổ menu.
   - **Phase Shop:** Mua nâng cấp có thể (`oxygen`, `hp`) khi tích lũy đủ `money`, sau đó phát `shop_done: True` để chuyển sang Ngày kế tiếp.
3. **Chuyển tiếp Chu kỳ (Day Plan Rollover D1–D5 $\rightarrow$ D6–D10):**
   - Bộ kế hoạch ngày `day_plan` được định nghĩa cho 5 Ngày đầu tiên.
   - Khi chuyển sang Ngày thứ 6 ($d \ge 6$), hệ thống tự động ánh xạ tuần hoàn theo công thức:
     $$\text{plan\_index} = (d - 1) \pmod{\text{len}(ordered\_plans)}$$
   - Đảm bảo Ngày 6 lặp lại thực đơn Ngày 1, Ngày 7 lặp lại Ngày 2... mà không gây ngoại lệ `BadInput` hoặc treo tiến trình.
4. **Bảo toàn ID Cá thể & Trạng thái tích lũy:**
   - Bộ cấp phát ID `ids = IdAllocator()` được duy trì xuyên suốt toàn bộ 10 Ngày.
   - Mọi thực thể cá thể mới được cấp ID duy nhất tăng dần `I1, I2, I3...` không bị reset, không xung đột.
   - Tài sản kinh tế (`money`, `earned`, `reputation`, `upgrades`) được kế thừa liên tục giữa các ngày.

---

### 3. Quy Tắc Bất Biến & Chống Hồi Quy

- **Tất định 100%:** Toàn bộ chuỗi RNG đi qua `self.rng` (`Streams`). Cùng `--seed 7`, hai lần chạy độc lập phải sinh mảng `results` trùng khớp từng giá trị số.
- **Zero Crash:** Bộ đếm `crashes` bắt buộc bằng `0`, và `days_completed` bắt buộc bằng `days` (10).
- **Tuân thủ Ranh giới (Blacklist):**
  - Không sửa `chonoi/headless.py`, `chonoi/runner.py`, `chonoi/contract.py`, `chonoi/inputs.py`, `chonoi/jsonl.py`, `chonoi/ids.py`.
  - Không sửa `game.contract.json` hay test contract của M6.

---

## B. Test Spec (Ma trận AC)

| Mã AC | Tiêu chí nghiệm thu | Kịch bản kiểm thử | Kết quả mong đợi |
|---|---|---|---|
| **AC-P4-M2-01** | Kiểm tra tham số CLI | Chạy `chonoi.soak` với `--days 0` hoặc `--days -1` | Trả về mã lỗi thoát `2` (BadInput) |
| **AC-P4-M2-02** | Chạy 10 Ngày không crash | Chạy `python3 -m chonoi.soak --seed 7 --days 10 --out soak.json` | Thoát mã `0`, `crashes == 0`, `days_completed == 10` |
| **AC-P4-M2-03** | Đầy đủ 5 trường schema | Đọc file `soak.json` sinh ra từ lệnh trên | Có đủ 5 khóa: `days`, `days_completed`, `crashes`, `results`, `duration_s` |
| **AC-P4-M2-04** | Cấu trúc mảng `results` | Kiểm tra độ dài và thuộc tính từng phần tử trong `results` | Đúng 10 phần tử (tương ứng Day 1..10), mỗi phần tử chứa đủ: `day`, `earned`, `reputation`, `score` |
| **AC-P4-M2-05** | Chuyển tiếp D5 $\rightarrow$ D6 | Kiểm tra phase transition từ ngày 5 sang ngày 6 | Không ném lỗi `BadInput`, menu và nguyên liệu Ngày 6 khớp Ngày 1 |
| **AC-P4-M2-06** | Tính tất định qua nhiều lần chạy | Chạy 2 lần độc lập cùng `--seed 7 --days 10` ra 2 file `soak1.json` và `soak2.json` | Mảng `results` của 2 file giống hệt nhau 100% |
| **AC-P4-M2-07** | Bảo toàn cấp ID cá thể | Theo dõi chuỗi ID cá thể sinh ra xuyên suốt 10 Ngày | ID được sinh theo định dạng `I{k}`, không bị trùng lặp, không bị reset về `I1` ở giữa ca |
