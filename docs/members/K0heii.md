# K0heii — phản tư cá nhân (≤ 200 từ)

- **Tôi đã làm (Module M6 — PO / Integrator / Release):**
  - **Phase 1 (`cab9595`, `0f3c7f1`)**: Setup `TEAM.md` (6 người), khóa hợp đồng `v1.0`, bổ sung validate mâu thuẫn `scenario.py` + `test_scenario_m6.py`, kiểm tất định SHA-256 & gắn tag `phase-1`.
  - **Phase 2 (`238d752`)**: Nâng Contract `v1.1`, mở `--mode day --days`, `BUTTONS_V11`, `scenario.py` v1.1, smoke `day` & gắn tag `phase-2`.
  - **Phase 3 (`c76204d`, `5d69601`)**: Tạo `chonoi/freshness.py` (`FRESH_SCALE=240`), adapter `v1.2`, fix bug giỏ rỗng `{"items":[]}` trong `contract.py`, viết `CHANGELOG.md` & gắn tag `phase-3`.
  - **Phase 4 (`d413708` + Release `v1.0.0`)**: Nâng Contract `v1.3` (`bench_cmd`, `soak_cmd`), rà lỗi merge `soak.json`, chạy chốt `bench.json` 30 s, bổ sung `LICENSE`, đóng gói ZIP, tag `phase-4` & Release `v1.0.0`.
- **Tôi đã review & hỗ trợ:** Review inline + summary PR #5 (`QuangNEU`, góp ý sửa `fish_yield` ở `748ea15`); điều phối 4 bảng `phase-1..4-task.md` và sửa lỗi giỏ rỗng từ báo cáo của `huyvu-03`.
- **AI sai ở đâu & phát hiện thế nào:** Trước khi có `PRD0.md`, AI đoán `hand` là chuỗi thay vì object payload; lúc bật `v1.1` AI gọi nhầm `ids.next("F")` thay vì `ids.new("F")`. Đều phát hiện nhờ đối chiếu PRD và chạy `unittest`.
- **Bài học:** Khóa hợp đồng rõ, giữ adapter tương thích khi đổi schema và chạy kiểm chứng thật toàn repo trước mỗi tag giúp 6 người tích hợp mượt cả 4 phase.
