# Kế hoạch Phase 2 (1:00 – 1:55 · Test Contract v1.1)

- **Mục tiêu:** Nâng cấp sang `contract_version: "1.1"` với số liệu chuẩn (6 nguyên liệu, 6 món, 2 bếp, 4 bàn), cá bơi & sinh theo lịch, Cá Sấu Năm Chèo, vòng ngày `--mode day --days 1..5`, Shop (`oxygen`/`hp`), Pause 3 mode, Menu & HUD v1.1; đạt smoke tích hợp phút 20, regression P1 xanh, retro P2 và đẩy tag `phase-2` trước **1:55**.
- **Phân công chi tiết:** xem [`phase-2-task.md`](../../phase-2-task.md):
  - **M6 (`K0heii`):** `M6.1`–`M6.3` nâng `game.contract.json` (`1.1`), `contract.py`, `inventory.py`, `inputs.py`, `headless.py`, `scenario.py`; smoke tích hợp phút 20, regression P1, `verification/phase-2.md`, retro P2, gắn tag `phase-2`.
  - **M1 (`huyvu-03`):** Cá Sấu Năm Chèo (`M1`, `M2`), `patrol`/`chase`/`recoil`, `monster_hit`, rơi 1/2 giỏ LIFO, `invuln_ticks`, `faint cause:"monster"`.
  - **M2 (`QuangNEU`):** Cá bơi 1.5 m/s, phản xạ mép/góc, đổi hướng 120 tick, sinh cá 360 tick (`fish_spawned`, trần 12), nút N5/N6, `ca_keo`/`keo_neo`.
  - **M3 (`ththanh8888`):** Quán 2 bếp B1–B2, 4 bàn T1–T4, 6 món, lọc menu theo `day_plan` trong `day`.
  - **M4 (`NhMinh-2610`):** Đã hoàn thiện phần lớn `day.py`, `shop.py`, Pause trong `runner.py`; ghép với M1/M2/M3 bản v1.1 và chạy test nhiều ngày.
  - **M5 (`thanhvu101`):** Menu chính, `DayIntro`/`EveningIntro`/`DayResult`/`Summary`, Pause overlay, HUD v1.1 (`"Thủy quái!"`, `"Hết hơi!"`, Shop UI).
- **Rủi ro & giảm thiểu:**
  - `gather.py` dùng chung giữa M1 (Cá Sấu) & M2 (cá bơi/sinh) → tách helper riêng (`monsters.py`/`fish.py`) hoặc merge tuần tự nhanh.
  - Test P1 cũ kiểm cứng `fish_initial == 6` và `--mode day` trả mã `2` → đã cập nhật theo số chuẩn v1.1 và ghi rõ lý do trong `docs/clarify.md`.
