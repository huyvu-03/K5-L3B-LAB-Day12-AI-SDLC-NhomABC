# huyvu-03 — phản tư cá nhân (≤ 200 từ)

- **Tôi đã làm (kèm link commit):**
  - `M1.1` ([`d15883d`](https://github.com/huyvu-03/K5-L3B-LAB-Day12-AI-SDLC-NhomABC/commit/d15883dd33e601ced58cdac1e7933c43113a8c08)): Viết tiêu chí chấp nhận cho bơi, chặn biên, oxy, ngạt, Máu và ngất.
  - `M1.2` ([`d15883d`](https://github.com/huyvu-03/K5-L3B-LAB-Day12-AI-SDLC-NhomABC/commit/d15883dd33e601ced58cdac1e7933c43113a8c08)): Thêm bốn test headless từ tiêu chí chấp nhận.
  - `M1.3` ([`d15883d`](https://github.com/huyvu-03/K5-L3B-LAB-Day12-AI-SDLC-NhomABC/commit/d15883dd33e601ced58cdac1e7933c43113a8c08)): Triển khai `dive`, `surface`, oxy, ngạt và ngất.
  - `M1.4` ([`d15883d`](https://github.com/huyvu-03/K5-L3B-LAB-Day12-AI-SDLC-NhomABC/commit/d15883dd33e601ced58cdac1e7933c43113a8c08)): Chạy test và ghi [bằng chứng kiểm thử](../proof/phase-1/m1.md).
  - Phase 2, `M1.1–M1.4` ([`06dc915`](https://github.com/huyvu-03/K5-L3B-LAB-Day12-AI-SDLC-NhomABC/commit/06dc915d972fb7325cfa9663c6ca60d251aca671)): Triển khai Cá Sấu Năm Chèo, [5/5 test đạt](../proof/phase-2/m1.md).
  - Phase 3, `M1.1–M1.4`: Viết spec/test ([`5a4fbe8`](https://github.com/huyvu-03/K5-L3B-LAB-Day12-AI-SDLC-NhomABC/commit/5a4fbe8f1901de96ae493712fa5839b0ed974214)), nghiệm thu giỏ tươi sau ghép M2. [5/5 test đạt](../proof/phase-3/m1.md)
  - Phase 4, `M1.1`: [Kiểm clone Ubuntu, thử ZIP và bàn giao An](../proof/phase-4/m1.md).
- **Tôi đã review (kèm link):** Đối chiếu tick PRD-0 với [test M1](../../tests/test_gather_m1.py). Kiểm tra [bàn giao kho v1.2](../proof/phase-3/m1.md) sau ghép M2.
- **AI sai ở đâu và tôi phát hiện thế nào:** Lệnh `python3` AI dùng không chạy trên Windows. Tôi kiểm tra phiên bản rồi dùng Python đã cài để chạy headless.
- **Điều tôi học được:** Test theo từng tick bắt lỗi ngạt. Smoke giỏ rỗng bắt lỗi đổi schema.
