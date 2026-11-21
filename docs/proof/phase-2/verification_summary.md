# Báo cáo Kiểm Chứng Tự Động — Phase 2
Thời gian thực hiện: `2026-11-21 12:10:59`

## 1. Kết quả Unit Tests (Hồi quy)
- **Trạng thái:** ✅ ĐẠT (PASS) — `1.87s`
```text
2_p2.GatherM2Phase2.test_ac_p2_m2_01_fish_swims_at_correct_speed)
AC-P2-M2-01: Cá bơi đúng tốc độ 1.5 m/s sau 60 tick (di chuyển được 1.5 m). ... ok
test_ac_p2_m2_02_fish_turns_at_tick_120 (test_gather_m2_p2.GatherM2Phase2.test_ac_p2_m2_02_fish_turns_at_tick_120)
AC-P2-M2-02: Đổi hướng ở bước bơi thứ 120. ... ok
test_ac_p2_m2_03_elastic_reflection_at_boundary (test_gather_m2_p2.GatherM2Phase2.test_ac_p2_m2_03_elastic_reflection_at_boundary)
AC-P2-M2-03: Phản xạ đàn hồi khi chạm biên x = 96. ... ok
test_ac_p2_m2_04_fish_spawn_at_interval_360 (test_gather_m2_p2.GatherM2Phase2.test_ac_p2_m2_04_fish_spawn_at_interval_360)
AC-P2-M2-04: Sinh cá theo chu kỳ 360 tick và phát event fish_spawned. ... ok
test_ac_p2_m2_05_spawn_capped_at_max (test_gather_m2_p2.GatherM2Phase2.test_ac_p2_m2_05_spawn_capped_at_max)
AC-P2-M2-05: Không sinh cá khi đã chạm trần fish_max = 12. ... ok
test_ac_p2_m2_06_spawn_clearance_greater_than_one_meter (test_gather_m2_p2.GatherM2Phase2.test_ac_p2_m2_06_spawn_clearance_greater_than_one_meter)
AC-P2-M2-06: Đàn cá mới sinh cách mọi đàn đang sống > 1.0 m. ... ok
test_ac_p2_m2_07_gather_new_keo_neo_node (test_gather_m2_p2.GatherM2Phase2.test_ac_p2_m2_07_gather_new_keo_neo_node)
AC-P2-M2-07: Hái bông kèo nèo tại nút N5 thu được keo_neo. ... ok
test_ac_p2_m2_08_catch_new_ca_keo_species (test_gather_m2_p2.GatherM2Phase2.test_ac_p2_m2_08_catch_new_ca_keo_species)
AC-P2-M2-08: Bắt cá kèo (ca_keo) thu được sản lượng yield = 2. ... ok
test_ac_p2_m2_09_random_fish_false_stays_stationary (test_gather_m2_p2.GatherM2Phase2.test_ac_p2_m2_09_random_fish_false_stays_stationary)
AC-P2-M2-09: Cờ random_fish: false giữ cá đứng yên và không sinh cá mới. ... ok
test_ac_p2_m2_10_inventory_with_new_ingredients (test_gather_m2_p2.GatherM2Phase2.test_ac_p2_m2_10_inventory_with_new_ingredients)
AC-P2-M2-10: File kho chấp nhận 6 loại nguyên liệu, bao gồm ca_keo và keo_neo. ... ok

----------------------------------------------------------------------
Ran 20 tests in 1.722s

OK

```

## 2. Kết quả Mô phỏng Headless
### Chế độ: `docs/proof/phase-2/gather_seed1_ticks600.jsonl`
- **Proof:** [`docs/proof/phase-2/gather_seed1_ticks600.jsonl`](file:///D:/Quang/VinUni-CodeLab/K5-L3B-LAB-Day12-AI-SDLC-NhomABC/docs/proof/phase-2/gather_seed1_ticks600.jsonl)
- **Trạng thái:** ✅ PASS (exit `0`, `0.13s`)
- **Snapshots:** `61` | **Events:** `0`
- **Thống kê sự kiện:**
```json
{}
```


## 3. Gợi ý điền ma trận kiểm chứng (docs/verification/phase-2.md)
| AC / Yêu cầu | Cách kiểm chứng | Bằng chứng | Kết quả |
|---|---|---|---|
| Unit tests hồi quy | unittest discover | [verification_summary.md](file:///D:/Quang/VinUni-CodeLab/K5-L3B-LAB-Day12-AI-SDLC-NhomABC/docs/proof/phase-2/verification_summary.md) | Đạt |
| Mô phỏng `docs/proof/phase-2/gather_seed1_ticks600.jsonl` | Headless (61 snapshots) | [docs/proof/phase-2/gather_seed1_ticks600.jsonl](file:///D:/Quang/VinUni-CodeLab/K5-L3B-LAB-Day12-AI-SDLC-NhomABC/docs/proof/phase-2/gather_seed1_ticks600.jsonl) | Đạt |
