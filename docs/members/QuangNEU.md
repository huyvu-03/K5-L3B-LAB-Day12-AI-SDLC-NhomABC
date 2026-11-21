# QuangNEU — phản tư cá nhân (≤ 200 từ)

- **Tôi đã làm (kèm link commit):**
  - **Phase 1 (`M2.1`–`M2.4`):** Lập đặc tả [phase-1-m2.md](../specs/phase-1-m2.md), viết 10 unit test [test_gather_m2.py](../../tests/test_gather_m2.py), code thu hoạch cây mặt nước, bắt đàn cá dưới nước, giỏ LIFO, cập bến và xuất file kho [m2_catch.json](../proof/phase-1/m2_catch.json) khớp 100% từng byte với contract.
  - **Phase 2 (`M2.1`–`M2.4`):** Lập đặc tả [phase-2-m2.md](../specs/phase-2-m2.md), viết 10 unit test [test_gather_m2_p2.py](../../tests/test_gather_m2_p2.py), triển khai cá bơi 1.5 m/s, đổi hướng 120 tick, phản xạ đàn hồi ở biên sông [4,96] và dải độ sâu theo loài, sinh đàn cá 360 tick (trần 12 đàn, clearance > 1m), hái bông kèo nèo (`keo_neo`), bắt cá kèo (`ca_keo` yield 2), xuất kho 6 nguyên liệu v1.1 [m2_catch_p2.json](../proof/phase-2/m2_catch_p2.json).
  - **Phase 3 (`M2.1`–`M2.4`):** Lập đặc tả [phase-3-m2.md](../specs/phase-3-m2.md), viết 10 unit test [test_gather_m2_p3.py](../../tests/test_gather_m2_p3.py), triển khai giỏ cá thể `{id, kind, fresh}`, cấp ID `I1, I2...` tăng dần liên tục xuyên Ngày, hao tươi 0.5/s bằng đơn vị nguyên 240, bắt event `spoiled` khi `< 30.0` sắp theo `id`, xuất kho cá thể v1.2 [m2_catch_p3.json](../proof/phase-3/m2_catch_p3.json).
- **Tôi đã review (kèm link):**
  - Đối chiếu logic chuyển vùng `dive`/`surface`, oxy và ngạt của M1 trong `gather.py` để bảo đảm tích hợp mượt mà với giỏ cá thể và rơi hàng LIFO.
  - Phối hợp chéo với Huy (`huyvu-03` — M1) giúp bộ test `test_gather_m1_p3.py` của M1 đạt 5/5 test xanh ngay khi có giỏ cá thể.
- **AI sai ở đâu và tôi phát hiện thế nào:**
  - AI ban đầu dùng `.get(fish["kind"], 1)` để lấy sản lượng cá; tôi phát hiện vi phạm nguyên lý Fail-Fast và yêu cầu đổi sang `self.t["fish_yield"][fish["kind"]]` để báo lỗi ngay nếu thiếu khai báo trong contract.
  - Khi triển khai Phase 3, cần tránh làm gãy các test cũ của Phase 1 & 2 nên tôi đã yêu cầu thêm adapter tự động nhận diện schema để bảo toàn 100% test cũ.
- **Điều tôi học được:**
  - Kỹ thuật khử sai số số thực: biểu diễn độ tươi bằng số nguyên (240 đơn vị cho 1 điểm) giúp kiểm tra ngưỡng 30 và trừ độ tươi chính xác tuyệt đối từng tick.
  - Quản lý Breaking Change trong SDLC: việc thiết kế adapter tương thích ngược giúp quá trình chuyển đổi schema kho diễn ra an toàn mà không làm nghẽn các thành viên khác.
