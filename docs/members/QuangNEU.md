# QuangNEU — phản tư cá nhân (≤ 200 từ)

- **Tôi đã làm (kèm link commit):**
  - **Phase 1 (`M2.1`–`M2.4`):** Lập đặc tả [phase-1-m2.md](../specs/phase-1-m2.md), viết 10 unit test [test_gather_m2.py](../../tests/test_gather_m2.py), code thu hoạch cây mặt nước, bắt đàn cá dưới nước, giỏ LIFO, cập bến và xuất file kho [m2_catch.json](../proof/phase-1/m2_catch.json) khớp 100% từng byte với contract.
  - **Phase 2 (`M2.1`–`M2.4`):** Lập đặc tả [phase-2-m2.md](../specs/phase-2-m2.md), viết 10 unit test [test_gather_m2_p2.py](../../tests/test_gather_m2_p2.py), triển khai cá bơi 1.5 m/s, đổi hướng 120 tick, phản xạ đàn hồi ở biên sông [4,96] và dải độ sâu theo loài, sinh đàn cá 360 tick (trần 12 đàn, clearance > 1m), hái bông kèo nèo (`keo_neo`), bắt cá kèo (`ca_keo` yield 2), xuất kho 6 nguyên liệu v1.1 [m2_catch_p2.json](../proof/phase-2/m2_catch_p2.json).
- **Tôi đã review (kèm link):**
  - Đối chiếu logic chuyển vùng `dive`/`surface`, tính oxy và ngạt của M1 trong [chonoi/sim/gather.py](../../chonoi/sim/gather.py) để bảo đảm không xung đột với logic hái/bắt cá và cá bơi.
  - Review chéo với Huy (`huyvu-03` — M1) để sẵn sàng bàn giao nền `gather.py` cho Huy cài đặt Cá Sấu Năm Chèo (`monsters`).
- **AI sai ở đâu và tôi phát hiện thế nào:**
  - AI ban đầu tách helper `fish.py` để tránh xung đột; tôi đã yêu cầu gộp trực tiếp toàn bộ vào `chonoi/sim/gather.py` để giữ cấu trúc file chuẩn của dự án.
  - AI giả định gọi `sim.rng.stream()`, trong khi thực tế method của `Streams` là `get()`; tôi đã khắc phục bằng cách bổ sung alias method an toàn trong `chonoi/rng.py`.
- **Điều tôi học được:**
  - Quy tắc bất biến chống hồi quy: khi nâng cấp v1.1 vẫn phải giữ cờ fallback `random_fish: false` và `fish_speed` để 100% test của Phase 1 luôn PASS.
  - Xử lý va chạm biên bằng phản xạ đàn hồi và tính toán toán học góc hướng giúp cá bơi mượt mà và tất định qua seed.
