# Kế hoạch Phase 4 (2:30 – 3:00 · Test Contract v1.3 — Phát hành `v1.0.0`)

- **Mục tiêu:** Chốt `contract_version: "1.3"` với `bench_cmd` và `soak_cmd`, xác minh 3 cảnh báo + chế độ tương phản cao, kiểm clone sạch ≤ 3 lệnh, hoàn thiện `README.md`, `CHANGELOG.md`, `CREDITS.md`, `docs/verification/phase-4.md`, retro tổng kết (`docs/retro.md`), phản tư 6/6 người (`docs/members/`), **đẩy tag `phase-4` và công bố GitHub Release `v1.0.0`** trước **3:00**.
- **Phân công chi tiết:** xem [`phase-4-task.md`](../../phase-4-task.md):
  - **M6 (`K0heii` — Release/Integrator/PO):** Nâng `game.contract.json` (`1.3`, `bench_cmd`, `soak_cmd`), chạy `soak.json`, rà `README.md`/`CHANGELOG.md`/`CREDITS.md`, chốt `docs/verification/phase-4.md`, gắn tag `phase-4` & công bố GitHub Release `v1.0.0`.
  - **M5 (`thanhvu101` — Bench/UI/Demo):** Đã có `chonoi/bench.py` + 3 cảnh báo + High Contrast `[H]` + SFX captions `[C]`; chạy chốt `bench_cmd --seed 42 --duration 30 --out docs/proof/phase-4/bench.json`, chụp ảnh chế độ tương phản cao, chuẩn bị Demo < 5 phút.
  - **M4 (`NhMinh-2610` — Soak/Ext):** Đã có `chonoi/soak.py` + `test_soak_m4.py`; xác nhận `soak` chạy chuẩn trên `v1.3` (kho cá thể) và rà mục Mở rộng.
  - **M2 (`QuangNEU` — Soak QA):** Kiểm tra `soak_cmd --seed 7 --days 10` (lặp D1–D5 cho D6–D10, id cá thể xuyên suốt, `crashes: 0`, lặp 2 lần khớp gameplay).
  - **M1 (`huyvu-03` — Đóng gói):** Thử clone sạch & chạy trong ≤ 3 lệnh theo `README.md`, tạo bản đóng gói (`.zip`) đính kèm Release `v1.0.0`.
  - **M3 (`ththanh8888` — Regression QA):** Chạy regression P1–P3 trên `v1.3` và rà link bằng chứng ở `docs/verification/phase-1..4.md`.
  - **Cả 6 người:** Retro tổng kết vào `docs/retro.md` (rà lại hành động P2) và chốt `docs/members/<handle>.md` (≤ 200 từ).
