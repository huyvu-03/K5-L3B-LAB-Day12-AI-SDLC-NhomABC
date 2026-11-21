# Ma trận truy vết Phase 2

| AC | Module | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-2/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|---|
| AC-P2-CON-01: Headless CLI (`--mode day`, `--days 1..5`, contract v1.1) | M6 | `unittest` (`test_smoke_p2.py`) | *Chờ M6 nộp bằng chứng Đợt 4* | Chờ bàn giao M6 |
| AC-P2-CON-02: Tất định byte-for-byte chế độ `day` và độc lập | M6 | Chạy 2 lần so khớp hash | *Chờ M6 nộp bằng chứng Đợt 4* | Chờ bàn giao M6 |
| AC-P2-M1-01: Cá Sấu (`M1`, `M2`), patrol/chase/recoil, `monster_hit`, rơi 1/2 giỏ LIFO, bất tử 90 tick | M1 | Unit test M1 (`test_gather_m1_p2.py`) | *Chờ M1 nộp bằng chứng Đợt 4* | Chờ bàn giao M1 |
| AC-P2-M2-01: Cá bơi 1.5 m/s, đổi hướng 120 tick, phản xạ mép [4,96], sinh cá 360 tick (`fish_spawned`, trần 12) | M2 | Unit test M2 (`test_gather_m2_p2.py`) | [m2.md](../proof/phase-2/m2.md) | **Đạt** (10/10 AC pass) |
| AC-P2-M2-02: Thu hoạch nút N5/N6 (`keo_neo`), bắt cá kèo (`ca_keo` yield 2), xuất file kho 6 nguyên liệu v1.1 | M2 | Unit test M2 + headless smoke 2 tiến trình | [m2.md](../proof/phase-2/m2.md), [m2_catch_p2.json](../proof/phase-2/m2_catch_p2.json) | **Đạt** (bàn giao kho 6 món thành công) |
| AC-P2-M3-01: Quán v1.1 (2 bếp B1–B2, 4 bàn T1–T4, 6 món), lọc thực đơn theo `day_plan` trong `day` | M3 | Unit test M3 (`test_quan_m3_p2.py`) | *Chờ M3 nộp bằng chứng Đợt 4* | Chờ bàn giao M3 |
| AC-P2-M4-01: Vòng ngày `day` (`gather → quan → shop → ngày kế`), chuyển kho, Shop (`oxygen`/`hp`), Pause | M4 | Unit test M4 (`test_day_m4.py`) | *Chờ M4 nộp bằng chứng Đợt 4* | Chờ bàn giao M4 |
| AC-P2-M5-01: Chơi thử v1.1 trên `chonoi.live` (Menu → Gather → Quan → Shop → Pause), HUD hiển thị quái/cá/bếp/bàn | M5 | Chạy `chonoi.live`, chụp ảnh màn hình | *Chờ M5 nộp ảnh Đợt 4* | Chờ bàn giao M5 |

## Đánh giá ngắn (cập nhật ở `M6.5` trước khi gắn tag `phase-2`)
- **Yêu cầu nào đạt / chưa đạt:** Module M2 (Nguyễn Minh Quang) đã hoàn thành 100% các tiêu chí (10/10 AC đạt, kiểm thử 2 tiến trình xuất kho 6 nguyên liệu thành công, bảo toàn 100% test Phase 1).
- **Điều cần chỉnh cho phase sau:** Các module M1, M3, M4, M5, M6 tiếp tục hoàn thiện và nộp bằng chứng nghiệm thu Đợt 4.
