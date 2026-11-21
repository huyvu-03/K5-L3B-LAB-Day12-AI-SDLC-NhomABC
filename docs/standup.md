# Standup giữa phase (mỗi người một dòng, 2–3 phút)

| Phase | Người | Đã xong | Sắp làm | Vướng gì |
|---|---|---|---|---|
| Phase 1 | Nguyễn Như Duy An (`K0heii` — M6) | Xong `M6.1`–`M6.3` (`TEAM.md`, `contracts`, `scenario.py` + test), chuẩn bị sẵn `verification/phase-1.md`, `README.md`, `test_integration_m6.py` | Chờ M1–M5 merge để chạy `M6.4`–`M6.6` và gắn tag `phase-1` | Không |
| Phase 1 | Nguyễn Nhật Minh (`NhMinh-2610` — M4) | Xong `M4.1`–`M4.4` (spec/AC, 12 test M4 + ghép `CustomerMixin` của M3 vào `quan.py`, toàn bộ test M3 + M4 + M6 xanh) | Review chéo C ↔ D, hỗ trợ M6 chốt `verification/phase-1.md` | Không |
| 1 | Vũ Quang Huy (M1) | Hoàn thành M1.1–M1.4, 42 test đạt, lưu [bằng chứng M1](proof/phase-1/m1.md) | Review chéo với B và chuyển bằng chứng cho F | Không |
| Phase 1 | Phùng Văn Thanh Cao (`ththanh8888` — M3) | Xong `M3.1`–`M3.4` (spec/AC, 18 test khách, `quan_customers.py`, test ghép M3 ↔ M4, bằng chứng `proof/phase-1/m3.md`); đã review chéo code M4 của Minh | Hoàn thiện hồ sơ cá nhân, hỗ trợ M6 duyệt bằng chứng, nhận việc dự phòng nếu nhóm cần | Chưa thấy bàn giao M2 (gather lát 2) nên chưa chạy được smoke gather → quán bằng kho thật |
| Phase 1 | Nguyễn Minh Quang (`QuangNEU` — M2) | Hoàn thành `M2.1`–`M2.4` (10 AC, 10 unit test, giỏ LIFO, cập bến, xuất kho [m2_catch.json](proof/phase-1/m2_catch.json) khớp 100% contract, lưu [m2.md](proof/phase-1/m2.md)) | Bàn giao kho cho Quán, chuyển sang Phase 2 | Không |
| Phase 2 | Nguyễn Minh Quang (`QuangNEU` — M2) | Hoàn thành `M2.1`–`M2.4` (10 AC Phase 2, 10 test `test_gather_m2_p2.py`, cá bơi 1.5 m/s, đổi hướng 120 tick, phản xạ mép, sinh đàn 360 tick, hái `keo_neo`, bắt `ca_keo`, bàn giao kho 6 nguyên liệu [m2.md](proof/phase-2/m2.md)) | Bàn giao nền `gather.py` cho Huy (M1) làm Cá Sấu (M1.3), review chéo M1 ↔ M2 | Không |
