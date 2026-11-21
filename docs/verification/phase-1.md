# Ma trận truy vết Phase 1

| AC | Module | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-1/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|---|
| AC-P1-CON-01: Headless CLI (`--mode gather\|quan`, `--ticks 0`, dòng `end` cuối) | M6 | `unittest` (`test_smoke_p1.Contract`) | [m6-determinism.txt](../proof/phase-1/m6-determinism.txt) | Đạt (96/96 tests OK) |
| AC-P1-CON-02: Tất định byte-for-byte (cùng seed → JSONL & file kho giống từng byte) | M6 | `unittest` (`test_integration_m6.py`) + SHA-256 2 lần chạy độc lập | [m6-determinism.txt](../proof/phase-1/m6-determinism.txt) | Đạt (SHA-256 khớp 100%) |
| AC-P1-CON-03: Đầu vào / scenario mâu thuẫn thoát mã `2` trước khi ghi output | M6 | `unittest` (`test_smoke_p1.py`, `test_scenario_m6.py`) | [test_scenario_m6.py](../../tests/test_scenario_m6.py) | Đạt (6/6 test suite OK) |
| AC-P1-INV-01: Tích hợp 2 tiến trình `gather --inventory-out` → `quan --inventory` | M2 / M6 | `unittest` (`test_smoke_p1.Integration`, `test_integration_m6.py`) | [m6-determinism.txt](../proof/phase-1/m6-determinism.txt), [m2_catch.json](../proof/phase-1/m2_catch.json) | Đạt (khớp từng byte) |
| AC-P1-M1-01: Bơi, tăng/giảm tốc (`ramp_max_ticks`), chặn biên `[0,100]×[0,30]`, `dive`/`surface` | M1 | `unittest` (`test_gather_m1.py`) | [m1.md](../proof/phase-1/m1.md) | Đạt |
| AC-P1-M1-02: Oxy (dưới nước -1, mặt nước +6), `oxygen_empty`, ngạt (`choke`), ngất (`faint` mất giỏ LIFO + kho rỗng) | M1 | `unittest` (`test_gather_m1.py`) | [m1.md](../proof/phase-1/m1.md) | Đạt |
| AC-P1-M2-01: Hái nút ở mặt nước (`gather`, `node_regrown`, `hold_full`), bắt cá (`catch`, `fish_caught`, cooldown) | M2 | `unittest` (`test_gather_m2.py`) | [m2.md](../proof/phase-1/m2.md), [test_gather_m2.py](../../tests/test_gather_m2.py) | Đạt (10/10 AC pass) |
| AC-P1-M2-02: Giỏ LIFO (`hold_capacity`), cập bến (`docked`), hết giờ (`time`), xuất kho khớp `inventory.sample.json` | M2 | `unittest` (`test_gather_m2.py`) | [m2.md](../proof/phase-1/m2.md), [m2_catch.json](../proof/phase-1/m2_catch.json) | Đạt (khớp từng byte) |
| AC-P1-M3-01: Khách đến theo lịch (`customer_arrived`, `no_dish`), giữ chỗ nguyên liệu (`reserved`), kiên nhẫn, rời đi (`customer_left`) | M3 | `unittest` (`test_quan_m3.py`, `test_quan_m4.py`) | [m3.md](../proof/phase-1/m3.md) | Đạt |
| AC-P1-M4-01: `interact` bếp/bàn (`cook_started`, `dish_ready`, `dish_picked`, `served`), trả tiền (`paid`), boa, uy tín, `quan_end` | M4 | `unittest` (`test_quan_m4.py`) | [m4-test-log.txt](../proof/phase-1/m4-test-log.txt) | Đạt |
| AC-P1-M5-01: Chơi thử được cả 2 buổi trên `chonoi.live`, HUD đọc được các chỉ số tối thiểu | M5 | Chạy `python3 -m chonoi.live --mode gather\|quan`, `test_live_m5.py` | [m5.md](../proof/phase-1/m5.md), [ui-contract.md](../ui-contract.md) | Đạt |
| AC-P1-TEAM-01: `TEAM.md` đủ 6 thành viên, `team_size: 6`, `check_team.py` xanh, hợp đồng kho trong `docs/contracts/` | M6 | `python tools/check_team.py` | [TEAM.md](../../TEAM.md), [contracts/README.md](../contracts/README.md) | Đạt (6/6 thành viên, mỗi người ≥ 3 commit) |

## Đánh giá ngắn
- **Yêu cầu nào đạt / chưa đạt:** Toàn bộ 12/12 AC Phase 1 (lõi `gather`, lõi `quan`, tích hợp 2 tiến trình, kiểm mâu thuẫn `scenario.py`, HUD `chonoi.live`, kiểm tất định SHA-256, `check_team.py`, 96/96 `unittest`) đều **Đạt**. Duy nhất còn thiếu file phản tư cá nhân `docs/members/QuangNEU.md` (sẽ bổ sung ở đầu Phase 2 / chốt trước Phase 4).
- **Điều cần chỉnh cho phase sau:** Giữ PR nhỏ tập trung 1 module (≤ 400 dòng), điền đầy đủ PR body trước khi gửi review, và đồng bộ sớm khi nâng `game.contract.json` lên `v1.1` (Phase 2) để không ảnh hưởng các test cũ.
