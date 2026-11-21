# Ma trận truy vết Phase 3

| AC | Module | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-3/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|---|
| AC-P3-CON-01: Contract `v1.2`, freshness helper (240 đơn vị nguyên), kho cá thể `{id, kind, fresh}`, từ chối kho đếm mã 2 khi bật v1.2 | M6 | `unittest` (`test_freshness_v12_m6.py`) | [test_freshness_v12_m6.py](../../tests/test_freshness_v12_m6.py) | **Đạt** (4/4 test suite OK) |
| AC-P3-M1-01: Hao tươi giỏ (-0.5/s), `spoiled` theo id, rơi cá thể LIFO khi trúng quái/ngạt, pause đóng băng hao tươi | M1 | Headless (`test_gather_m1_p3.py`) và smoke hai tiến trình | [m1.md](../proof/phase-3/m1.md), [JSONL](../proof/phase-3/m1-handoff-jsonl.txt) | **Đạt** (5/5 test M1) |
| AC-P3-M2-01: Giỏ cá thể, cấp ID `I1, I2...` tăng dần xuyên ca/Ngày, hao tươi 240 đơn vị, xuất kho cá thể v1.2 | M2 | Unit test M2 (`test_gather_m2_p3.py`) | [m2.md](../proof/phase-3/m2.md), [m2_catch_p3.json](../proof/phase-3/m2_catch_p3.json) | **Đạt** (10/10 AC pass) |
| AC-P3-M3-01: Hao tươi kho quán (-0.25/s), `spoiled`, giữ chỗ theo id tươi nhất, nhả & giữ lại 1 lần khi ươn | M3 | Unit test M3 (`test_quan_m3_v12.py`) | [test_quan_m3_v12.py](../../tests/test_quan_m3_v12.py) | Đang kiểm chứng |
| AC-P3-M4-01: Chốt giá theo `avg_fresh`, boa trên giá đã chốt, bàn giao kho cá thể trong `day`/Shop | M4 | Unit test M4 (`test_freshness_m4_v12.py`) | [test_freshness_m4_v12.py](../../tests/test_freshness_m4_v12.py) | Đang kiểm chứng |
| AC-P3-REG-01: Bảo toàn toàn bộ test Phase 1 & 2 khi chạy trên nền code Phase 3 | M2 | `unittest` test hồi quy Phase 1, 2 và smoke | [test_gather_m2.py](../../tests/test_gather_m2.py), [test_gather_m2_p2.py](../../tests/test_gather_m2_p2.py) | **Đạt** (34/34 test OK) |

## Đánh giá ngắn
- **Module M2:** Hoàn thành 100% các yêu cầu Phase 3 (cấp ID, giỏ cá thể, hao tươi, xuất kho Contract v1.2). Hỗ trợ M1 vượt qua toàn bộ 5/5 test `test_gather_m1_p3.py`.
