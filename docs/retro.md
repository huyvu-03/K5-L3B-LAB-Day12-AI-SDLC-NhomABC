# Retro nhóm

## Phase 2 (nhanh)
- Điều tốt: Tách rõ module theo sở hữu (`monsters.py`, `quan_customers.py`, `shop.py`, `day.py`) giúp ghép nhánh 6 người mượt, ít conflict; chạy đạt 110/110 test tích hợp M1–M6 trên v1.1.
- Điều tệ: Khi đổi sang v1.1 (thêm bếp `B2`, 4 bàn `T1–T4`), một số fixture test Phase 1 (tọa độ ngoài mép `B1`, giả định 1 bàn) bị vỡ tạm thời trước khi cập nhật.
- 1 hành động cho Phase 3: Trước khi đổi kho đếm → kho cá thể (`v1.2`), thống nhất ngay 1 helper đơn vị nguyên `fresh_units = fresh × 240` và giữ adapter tương thích cho đến mốc bật `v1.2` (`M6.4`).

## Phase 3 (nhanh — rút ra từ lần đổi schema kho)
- Hành động Phase 2 đã áp dụng: Thống nhất `chonoi/freshness.py` (`FRESH_SCALE = 240`) và giữ adapter song song `1.1`/`1.2` giúp `main` chạy xanh suốt quá trình M1–M4 chuyển đổi.
- Lỗi phát hiện khi bật `v1.2`: Huy (M1) phát hiện CLI với `hold: []` ghi `{"items":{}}` thay vì `{"items":[]}` do `tuning` không chứa `contract_version`; M6 đã sửa triệt để trong `chonoi/contract.py` trước khi gắn tag `phase-3`.


## Phase 4 (cuối)
- Rà lại hành động Phase 2: Đã làm trọn vẹn — thống nhất `chonoi/freshness.py` (`FRESH_SCALE = 240`) và giữ adapter song song `v1.1`/`v1.2` giúp đổi schema kho cá thể không vỡ `main` và chốt tag `phase-3` với 160/160 active tests xanh.
- Điều tốt / điều tệ:
  - Tốt: Tách rõ sở hữu module (`gather.py`, `quan_customers.py`, `quan_fresh.py`, `quan.py`, `day.py`, `shop.py`, `soak.py`, `bench.py`, `web/`); chuẩn bị sớm `soak.py` và `bench.py` giúp Phase 4 chạy mượt trên `v1.3`.
  - Tệ: Khi ghép M3–M4 ở Phase 3 từng có đoạn kho cá thể trùng nhau giữa `quan.py` và `quan_fresh.py` làm đỏ 6 test tạm thời trước khi dọn sạch.
- Số liệu: số commit (không tính merge, tại thời điểm chốt P4): `ththanh8888` (18), `NhMinh-2610` (16), `K0heii` (10), `thanhvu101` (10), `huyvu-03` (6), `QuangNEU` (5); review chéo theo cặp (M3↔M4, M1↔M2, M5↔M6); ước tính token ghi chi tiết theo từng phase tại `docs/ai-usage-log.md`.
- Một lần AI sai và cách nhóm phát hiện: Khi ghép `FreshStockMixin` (M3) với `quan.py` (M4), AI viết test M4 kỳ vọng `fresh=100` ngay tick 1 nhưng quên Bước 1 đã trừ `-1/240` trước Bước 3 `interact`; nhóm phát hiện ngay khi chạy regression chéo M3+M4 và sửa test kiểm cả biên 100 lẫn chu kỳ hao 60 tick.
- Nếu làm lại, đổi gì: Chốt interface mixin giữa các module dùng chung một file (`quan.py` ↔ `quan_fresh.py`) trước khi viết code song song để tránh trùng hàm tạm.
