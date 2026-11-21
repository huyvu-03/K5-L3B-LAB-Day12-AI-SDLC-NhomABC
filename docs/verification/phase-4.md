# Ma trận truy vết Phase 4 (Contract v1.3 · Release `v1.0.0`)

| AC | Module | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-4/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|---|
| AC-P4-CON-01: `contract_version: "1.3"`, khai báo `bench_cmd` & `soak_cmd` ở gốc `game.contract.json` | M6 | Kiểm `game.contract.json` + chạy `load_contract()` | [game.contract.json](../../game.contract.json) | **Đạt** |
| AC-P4-BENCH-01: `bench_cmd --seed 42 --duration 30 --out bench.json` xuất đủ 5 trường (`avg_fps`, `p1_low_fps`, `frames`, `measured_s`, `load_ms`) | M5 | Chạy `python3 -m chonoi.bench` + `test_live_m5.py` | [bench.json](../proof/phase-4/bench.json), [m5.md](../proof/phase-4/m5.md) | *Chờ M5 chốt run 30s* |
| AC-P4-SOAK-01: `soak_cmd --seed 7 --days 10 --out soak.json` đạt `days_completed=10`, `crashes=0`, lặp D1–D5 cho D6–D10, lặp lại khớp gameplay | M2 / M4 / M6 | Chạy `python3 -m chonoi.soak` + `test_soak_m4.py` & `test_soak_m2_p4.py` | [soak.json](../proof/phase-4/soak.json), [m2.md](../proof/phase-4/m2.md) | **Đạt** (10 ngày, 0 crash, tất định 100%) |
| AC-P4-A11Y-01: 3 cảnh báo bằng chữ/biểu tượng (thủy quái gần, oxy sắp hết, khách sắp giận) + chế độ tương phản cao hoạt động | M5 | Chơi thử `chonoi.live` ở chế độ tương phản cao `[H]`, chụp ảnh | [m5.md](../proof/phase-4/m5.md) | *Chờ M5 bổ sung ảnh* |
| AC-P4-PKG-01: Clone sạch chạy bản có giao diện trong ≤ 3 lệnh theo `README.md`; bản đóng gói đính kèm GitHub Release `v1.0.0` | M1 / M6 | Clone sạch trên Ubuntu, kiểm ZIP và mở bằng Chrome | [Bằng chứng M1](../proof/phase-4/m1.md) | Clone và ZIP thử đạt. Chờ M6 tạo ZIP từ tag và đính kèm Release. |
| AC-P4-REG-01: Regression P1–P3 còn hiệu lực đạt; `check_team.py` xanh | M3 / M6 | `python tools/check_team.py` + `unittest discover -s tests -v` | *Chờ lưu log ở bước chốt tag* | *Chờ chạy chốt* |
| AC-P4-DOCS-01: `CHANGELOG.md` đủ 4 phase, `CREDITS.md`, Release notes, retro P4 (đã rà hành động P2), đủ 6/6 `docs/members/<handle>.md`, `docs/ai-usage-log.md` | M6 + cả nhóm | Rà soát từng file & link | `CHANGELOG.md`, `docs/retro.md`, `docs/members/` | *Chờ tổng hợp cuối phase* |
| AC-P4-REL-01: Tag `phase-4` và GitHub Release `v1.0.0` cùng trỏ tới commit bàn giao trên `main` | M6 | `git tag` + trang GitHub Releases | *Chờ chốt cuối phase* | *Chờ gắn tag* |

## Đánh giá ngắn (cập nhật trước khi gắn tag `phase-4`)
- **Module M2 / Soak:** Hoàn thành 100% nghiệm thu `soak_cmd` 10 Ngày không lỗi (`crashes: 0`, `days_completed: 10`, hoàn thành trong 0.358s). Toàn bộ 6/6 test `test_soak_m2_p4.py` đạt chuẩn.
- **Yêu cầu nào đạt / chưa đạt:** *(Cập nhật ở `M6.2`–`M6.3`)*
- **Ghi chú phát hành `v1.0.0`:** *(Cập nhật ở `M6.3`)*
