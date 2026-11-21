# QuangNEU — phản tư cá nhân (≤ 200 từ)

- **Tôi đã làm (kèm link commit):**
  - **Phase 1 (`M2.1`–`M2.4`):** Lập đặc tả [phase-1-m2.md](../specs/phase-1-m2.md), viết 10 unit test [test_gather_m2.py](../../tests/test_gather_m2.py), code thu hoạch cây mặt nước, bắt đàn cá dưới nước, giỏ LIFO, cập bến và xuất file kho [m2_catch.json](../proof/phase-1/m2_catch.json) khớp 100% từng byte với contract.
  - **Phase 2 (`M2.1`–`M2.4`):** Lập đặc tả [phase-2-m2.md](../specs/phase-2-m2.md), viết 10 unit test [test_gather_m2_p2.py](../../tests/test_gather_m2_p2.py), triển khai cá bơi 1.5 m/s, đổi hướng 120 tick, phản xạ đàn hồi ở biên sông [4,96] và dải độ sâu theo loài, sinh đàn cá 360 tick (trần 12 đàn, clearance > 1m), hái bông kèo nèo (`keo_neo`), bắt cá kèo (`ca_keo` yield 2), xuất kho 6 nguyên liệu v1.1 [m2_catch_p2.json](../proof/phase-2/m2_catch_p2.json).
  - **Phase 3 (`M2.1`–`M2.4`):** Lập đặc tả [phase-3-m2.md](../specs/phase-3-m2.md), viết 10 unit test [test_gather_m2_p3.py](../../tests/test_gather_m2_p3.py), triển khai giỏ cá thể `{id, kind, fresh}`, cấp ID `I1, I2...` tăng dần liên tục xuyên Ngày, hao tươi 0.5/s bằng đơn vị nguyên 240, bắt event `spoiled` khi `< 30.0` sắp theo `id`, xuất kho cá thể v1.2 [m2_catch_p3.json](../proof/phase-3/m2_catch_p3.json).
  - **Phase 4 (`M2.1`–`M2.4`):** Lập đặc tả [phase-4-m2.md](../specs/phase-4-m2.md), viết bộ 6 unit test [test_soak_m2_p4.py](../../tests/test_soak_m2_p4.py), nghiệm thu thành công lệnh `soak_cmd` 10 Ngày liên tục (`crashes: 0`, `days_completed: 10`, 0.358s) tại [soak.json](../proof/phase-4/soak.json) và báo cáo [m2.md](../proof/phase-4/m2.md), chuẩn hóa Blacklist/Whitelist trong 4 skill của dự án.
- **Tôi đã review (kèm link):**
  - Đối chiếu logic chuyển vùng `dive`/`surface`, oxy và ngạt của M1 trong `gather.py` để bảo đảm tích hợp mượt mà với giỏ cá thể và rơi hàng LIFO.
  - Phối hợp chéo với Huy (`huyvu-03` — M1) giúp bộ test `test_gather_m1_p3.py` của M1 đạt 5/5 test xanh ngay khi có giỏ cá thể; phối hợp với Minh (`NhMinh-2610` — M4) nghiệm thu bot tất định `soak_cmd`.
- **AI sai ở đâu và tôi phát hiện thế nào:**
  - AI ban đầu dùng `.get(fish["kind"], 1)` để lấy sản lượng cá; tôi phát hiện vi phạm nguyên lý Fail-Fast và yêu cầu đổi sang `self.t["fish_yield"][fish["kind"]]` để báo lỗi ngay nếu thiếu khai báo trong contract.
  - Khi triển khai Phase 3, AI từng tự ý sửa file `chonoi/headless.py` và `scenario.py` ngoài phạm vi; tôi đã phát hiện qua `git status`, yêu cầu revert về 0 diff và cập nhật quy tắc Blacklist vào toàn bộ skill.
- **Điều tôi học được:**
  - Kỹ thuật khử sai số số thực bằng số nguyên (240 đơn vị/điểm) và thiết kế adapter tương thích ngược đa phiên bản.
  - Tầm quan trọng của kiểm định độ bền bỉ (Soak Testing) và thiết lập ranh giới tác vụ nghiêm ngặt cho AI trong quy trình AI-SDLC.
