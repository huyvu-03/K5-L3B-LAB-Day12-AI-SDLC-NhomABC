# NhMinh-2610 — phản tư cá nhân (≤ 200 từ)

- **Tôi đã làm (kèm commit):**
  - **Phase 1** (`7a57f3b`, `7f31375`, `06d8ef5`): Chốt AC, viết 12 test `test_quan_m4.py`, cài luật bếp/bàn/bưng/tiền/tip/uy tín/hết ca trong `chonoi/sim/quan.py` và ghép M3.
  - **Phase 2** (`0f46a50`, `55a66fb`, `12c98f5`, `41d199a`): Viết `spec-p2-m4.md`, cài `shop.py`, `day.py`, Pause 3 mode (`runner.py`) và test CLI `test_day_shop_pause_m4.py`.
  - **Phase 3** (`b194801`, `ef5d53f`, `5bf1839`, `53b8301`): Chốt `spec-p3-m4.md`, viết `test_freshness_m4_v12.py`, nối `quan.py`/`day.py`/`shop.py` với `FreshStockMixin` của M3 tính giá theo `avg_fresh` (`FRESH_SCALE = 240`).
  - **Phase 4** (`2cc5a8f` + chốt `v1.3`): Code `chonoi/soak.py` (bot tất định 10 Ngày lặp `D1–D5`), `test_soak_m4.py`, chạy chốt `docs/proof/phase-4/soak.json` (`10/10` ngày, `0` crash).
- **Review chéo:** Rà `quan_customers.py`, `quan_fresh.py`, `test_quan_m3_v12.py` với Cao (`ththanh8888`) và luồng `day` với Huy (`huyvu-03`).
- **AI sai & phát hiện:** Khi nối `FreshStockMixin`, 3 test M4 bị đỏ do AI chưa tính 1 tick hao tươi `-1/240` ở Bước 1 trước `interact` Bước 3; chạy regression phát hiện ngay và sửa test kiểm cả biên 100 lẫn chu kỳ 60 tick.
- **Bài học:** Tách sạch module theo sở hữu và chạy regression sau mỗi lần pull giúp 6 người ghép code nhanh, gần như không conflict.
