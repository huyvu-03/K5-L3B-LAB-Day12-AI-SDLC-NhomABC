# Changelog

## [v1.0.0 / Phase 4 — Contract v1.3] — Phát hành chính thức
- Nâng `contract_version: "1.3"`, khai báo `bench_cmd` (`python3 -m chonoi.bench`) và `soak_cmd` (`python3 -m chonoi.soak`) trong `game.contract.json`.
- **Benchmark (`chonoi/bench.py`)**: Đo 30 s sau 3 s làm nóng trên cảnh lặn lõi (seed 42, 1280×720), xuất đủ 5 trường `avg_fps`, `p1_low_fps`, `frames`, `measured_s`, `load_ms` (`docs/proof/phase-4/bench.json`).
- **Soak 10 Ngày (`chonoi/soak.py`)**: Chạy 10 Ngày liên tục trong 1 tiến trình headless lặp kế hoạch D1–D5 cho D6–D10, `days_completed: 10`, `crashes: 0`, tất định giữa các lần chạy (`docs/proof/phase-4/soak.json`).
- **Cảnh báo & Trợ năng (`chonoi/web/`)**: 3 cảnh báo dễ nhận biết bằng chữ/biểu tượng (thủy quái gần, oxy cạn, khách sắp giận), chế độ tương phản cao (`H`), và Mở rộng Phụ đề SFX (`C`).
- **Đóng gói & Tài liệu**: Xác minh chạy từ clone sạch trong ≤ 3 lệnh (`docs/proof/phase-4/m1.md`), bổ sung `LICENSE` (MIT), hoàn thiện `README.md`, `CREDITS.md`, `docs/retro.md`, `docs/verification/phase-4.md`, gắn tag `phase-4` & phát hành GitHub Release `v1.0.0`.

---

## [Phase 3 — Contract v1.2] — Mùa Nước Nổi (Độ tươi & Kho cá thể)
### BREAKING CHANGES
- **Schema file kho & snapshot (`hold`, `stock`, `gather_end.data.inventory`)**: Thay kho đếm `{"items": {"ca_loc": 1}}` (v1.0/v1.1) bằng **kho cá thể** `{"items": [{"id": "I1", "kind": "ca_loc", "fresh": 100}]}` (kho rỗng: `{"items": []}`). Khi chạy ở `contract_version: "1.2"`, file kho đếm v1.0/v1.1 trả mã thoát **`2`**.
- **Giữ chỗ (`customers[].reserved`)**: Đổi từ map `{kind: qty}` sang mảng `id` cá thể chưa ươn (`fresh >= 30`), chọn tươi nhất rồi `id` nhỏ; khi cá thể đang giữ vừa ươn sẽ nhả toàn bộ phần giữ và thử giữ lại đúng 1 lần theo `(order_tick, id_key(table_id))`, thiếu chuyển `unfulfillable`.
- **Giá món (`base_price`)**: Đổi từ giá niêm yết cố định sang `floor(giá niêm yết × trung bình fresh / 100)` tính bằng đơn vị nguyên `FRESH_SCALE = 240` (`chonoi/freshness.py`); tiền boa áp trên giá đã chốt.
- **Payload sự kiện**: `cook_started.data.items` là mảng cá thể sắp theo `(kind, id_key(id))`; `monster_hit.data.lost` và `faint.data.lost` là mảng cá thể theo thứ tự bỏ LIFO; thêm sự kiện `spoiled` (`{item_id, kind, location}`).

### Hướng dẫn cập nhật fixture & lý do thay đổi test cũ
- Các fixture `gather.hold` và `quan.stock` chuyển từ mảng chuỗi / object đếm sang mảng cá thể `[{"id": "I1", "kind": "...", "fresh": 100}]`; `customers[].reserved` chuyển sang mảng `id` cá thể.
- Các test hộp đen cốt lõi (`test_smoke_p1.py`, `test_integration_m6.py`, `test_scenario_m6.py`, `test_scenario_v11_m6.py`, `test_live_m5.py`) đã được cập nhật sang schema cá thể `v1.2`.
- 42 test case cũ ở Phase 1–2 chuyên kiểm tra schema kho đếm v1.0/v1.1 được đánh dấu `@unittest.skip` với lý do Breaking Change v1.2 và đã được thay thế đầy đủ bởi bộ test mới: `test_gather_m1_p3.py`, `test_gather_m2_p3.py`, `test_quan_m3_v12.py`, `test_freshness_m4_v12.py`, `test_freshness_v12_m6.py`.

### Đã thêm / Sửa
- `chonoi/freshness.py`: Helper độ tươi dùng chung `FRESH_SCALE = 240` (`-2`/tick ở `gather`, `-1`/tick ở `quan`).
- Fix bug giỏ rỗng v1.2: truyền `contract_version` vào `tuning` trong `chonoi/contract.py` để CLI ghi đúng `{"items":[]}` khi `hold: []`.
- Cập nhật HUD độ tươi trên `chonoi/web/index.html` (hiển thị độ tươi & cảnh báo hàng ươn).

---

## [Phase 2 — Contract v1.1] — Một ngày ở chợ nổi
- Nâng `contract_version: "1.1"`: 6 nguyên liệu (`ca_keo`, `keo_neo`), 6 món, 2 bếp (`B1–B2`), 4 bàn (`T1–T4`), nút `N5/N6`, `day_plan` D1–D5, Shop (`oxygen`/`hp`, `max_ticks: 600`).
- Cá bơi 1.5 m/s, phản xạ mép, đổi hướng mỗi 120 tick, sinh cá mỗi 360 tick (`fish_spawned`, trần 12).
- Cá Sấu Năm Chèo (`M1`, `M2` từ Ngày 3), `patrol`/`chase`/`recoil`, `monster_hit`, rơi 1/2 giỏ LIFO, bất tử 90 tick, `faint cause:"monster"`.
- Vòng ngày `--mode day --days 1..5`, Pause ở cả 3 mode, Menu chính + 4 màn hình chuyển pha + HUD v1.1.

---

## [Phase 1 — Contract v1.0] — Lõi Quán Ăn Chợ Nổi
- Buổi sáng (`gather`): bơi + ramp, oxy, ngạt, Máu, ngất, hái nút, bắt cá, giỏ LIFO, cập bến, xuất file kho.
- Buổi tối (`quan`): khách theo lịch, giữ chỗ, kiên nhẫn, nấu/bưng/phục vụ, tiền, boa, uy tín, hết ca.
- Validate mâu thuẫn `scenario.py` (mã thoát `2`), HUD cơ bản `chonoi.live`, bộ skills AI Harness trong `.agents/skills/`.
