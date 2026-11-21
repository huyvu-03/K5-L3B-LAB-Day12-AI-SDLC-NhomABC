# K0heii — phản tư cá nhân (≤ 200 từ)

- **Tôi đã làm:**
  - `M6.1`–`M6.2` (`cab9595`): điền 6 thành viên & thỏa thuận nhóm (`TEAM.md`), đặt `team_size: 6`, khóa hợp đồng (`docs/contracts/README.md`), kế hoạch `docs/plan/phase-1.md`, `docs/clarify.md`.
  - `M6.3`: bổ sung validate mâu thuẫn mức luật quán trong `chonoi/scenario.py`, nối kiểm kho `--inventory` trong `chonoi/headless.py` và viết `tests/test_scenario_m6.py`.
  - `M6.4`–`M6.6`: viết `tests/test_integration_m6.py`, bổ sung DoD `README.md`, lập bảng kế hoạch `phase-2/3/4-task.md`, chạy xác minh SHA-256 (`docs/proof/phase-1/m6-determinism.txt`), hoàn thiện `docs/verification/phase-1.md` và gắn tag `phase-1`.
- **Tôi đã review:** Review chi tiết inline + summary cho PR #5 (`QuangNEU` — M2), góp ý dùng truy cập trực tiếp `fish_yield` (đã sửa ở commit `748ea15`) và tách gọn phạm vi PR.
- **AI sai ở đâu và tôi phát hiện thế nào:** Trước khi có `PRD0.md`, AI giả định `hand` là chuỗi mã món; đối chiếu PRD-0 mục D phát hiện là object `{order_id, dish_id, base_price}` và đã sửa lại hợp đồng + validate.
- **Điều tôi học được:** Khóa hợp đồng sớm và tách kiểm mâu thuẫn `scenario.py` giúp cả 6 module ghép mượt, đạt 96/96 test xanh ngay lần tích hợp đầu.
