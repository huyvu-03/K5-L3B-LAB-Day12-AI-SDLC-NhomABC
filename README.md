# Day 12 — AI SDLC: Quán Ăn Chợ Nổi

> **Làm theo nhóm 4–6 người** · Dùng AI để xây game 2D qua **4 phase** trong **3 giờ**: Út Sen lặn bắt cá, hái rau trên mặt nước rồi tối mở quán phục vụ khách.
> **Yêu cầu từng phase mở đúng mốc giờ tại lab board:** **[Chợ Nổi Lab](https://claude.ai/artifact/E35v787wSx2wDgPTNhMVDg)** (cần đăng nhập claude.ai; có trợ giảng AI cho từng phase).

## Bắt buộc (chỉ có thế)

Cách làm việc kỹ thuật là **tự do** (push thẳng, nhánh + PR, pair, có hay không CI…). Cái bắt buộc:

1. **Một repo chung:** trưởng nhóm **fork** repo này, đặt tên `K5-L3B-LAB-Day12-AI-SDLC-<ten-nhom>`, thêm mọi thành viên làm collaborator (*Settings → Collaborators*, quyền Write) và để repo **public** (giảng viên xem được, không cần mời).
2. **Cả nhóm cùng commit** bằng tài khoản GitHub của mình, mỗi người **≥ 3 commit có nội dung** (làm cặp thì ghi `Co-authored-by:`).
3. **Điền [`TEAM.md`](TEAM.md):** danh sách thành viên + thỏa thuận làm việc nhóm; sửa `team_size` trong [`game.contract.json`](game.contract.json). Commit của người không có trong `TEAM.md` không được tính.
4. **Gắn tag** `phase-1` … `phase-4` đúng hạn; chạy được tại từng tag.
5. **Ghi chép tối thiểu:** `docs/verification/phase-n.md`, `docs/clarify.md`, `docs/ai-usage-log.md`, `docs/retro.md`, `docs/members/<handle>.md`.

## Bắt đầu nhanh (≤ 3 lệnh từ clone sạch)

Trên macOS hoặc Linux, cần Git, Python 3.12 hoặc mới hơn và trình duyệt hỗ trợ Canvas 2D. Game dùng thư viện chuẩn Python. Nếu dùng bản ZIP, giải nén và chạy hai lệnh cuối từ thư mục chứa `game.contract.json`.

```bash
git clone https://github.com/huyvu-03/K5-L3B-LAB-Day12-AI-SDLC-NhomABC.git && cd K5-L3B-LAB-Day12-AI-SDLC-NhomABC
PYTHONPATH=tests:. python3 -m unittest discover -s tests -v        # chạy toàn bộ test bằng 1 lệnh
python3 -m chonoi.live --mode gather                                # chơi thử buổi sáng (đổi --mode quan cho buổi tối)
```

Mở địa chỉ server in ra, mặc định `http://127.0.0.1:8000/`. Dùng `--mode day --days 1` để chơi trọn một ngày.

### Điều khiển (trên trình duyệt `chonoi.live`)
- **WASD / Phím mũi tên**: Bơi (buổi sáng `[x, d]`) hoặc đi lại trong quán (buổi tối `[x, z]`).
- **E**: Tương tác (`interact`) — cập bến hoặc hái rau ở buổi sáng; nấu, bưng hoặc phục vụ ở buổi tối.
- **Space**: Bắt cá (`catch`) khi đang lặn dưới nước.
- **R**: Chơi lại từ đầu.
- **P / Esc**: Tạm dừng hoặc tiếp tục.
- **M / H / C**: Bật hoặc tắt âm thanh / tương phản cao / phụ đề hiệu ứng.

### Cách tính điểm & Hợp đồng tích hợp
- **Điểm số**: `score = earned + 100 × floor(reputation)` (trong đó `earned` là tổng thu gồm tiền món và tiền boa, đơn vị nghìn đồng; `reputation` khởi đầu `3.0`, kẹp trong `[0, 5]`).
- **Hợp đồng file kho, snapshot & sự kiện**: xem [`docs/contracts/README.md`](docs/contracts/README.md) và kho mẫu [`docs/contracts/inventory.sample.json`](docs/contracts/inventory.sample.json).

Game cần chế độ **headless** theo Test Contract (`python3 -m chonoi.headless --mode gather|quan …`) để được chạy và chấm tự động. **Công nghệ không ràng buộc**: khung Python trong `chonoi/` chỉ là gợi ý, chi tiết ở [`docs/STARTER.md`](docs/STARTER.md).

### Headless, benchmark và soak

```bash
printf '%s\n' '{"frames":[{"tick":0,"interact":true}]}' > dock-inputs.json
python3 -m chonoi.headless --mode gather --seed 1 --ticks 1 --inputs dock-inputs.json --out gather.jsonl --inventory-out kho.json
python3 -m chonoi.headless --mode quan --seed 1 --ticks 600 --inventory kho.json --out quan.jsonl
python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json
python3 -m chonoi.soak --seed 7 --days 10 --out soak.json
```

Ví dụ headless cập bến ngay tick 1 để sinh file kho cho quán. Benchmark hiện tại đo xử lý cảnh bằng Python, gồm tọa độ, lọc đối tượng và mã hóa snapshot. Trường `avg_fps` là số lần xử lý workload này mỗi giây.

## Tự do sáng tạo

Ngoài phần đề yêu cầu, nhóm được **thêm** nhân vật, loài cá/cây, sinh vật, món, bản đồ, cơ chế, câu chuyện, đồ họa, âm nhạc… với ba điều kiện: **không phá phần cố định** (tắt ở headless), ghi mục **"Sáng tạo của nhóm"** trong README của nhóm, và **làm lõi đúng trước**.

## Lịch 3 giờ

| Mốc | Phase | Hạn tag |
|---|---|---|
| 0:00 | Phase 1 (PRD-0) | `phase-1` trước 1:00 |
| 1:00 | Phase 2 | `phase-2` trước 1:55 |
| 1:55 | Phase 3 | `phase-3` trước 2:30 |
| 2:30 | Phase 4 | `phase-4` + Release `v1.0.0` trước 3:00 |

Hết giờ mỗi phase thì gắn tag rồi đi tiếp; chỗ chưa xong ghi trung thực trong bằng chứng.

## Đánh giá (100 điểm)

| Hạng mục | Điểm |
|---|---|
| Test tự động ẩn (headless, gồm kiểm tra lại phase trước) | 25 |
| Làm việc nhóm (một repo chung, chia việc, tích hợp, đổi yêu cầu) | 25 |
| Kiểm chứng & bằng chứng | 15 |
| Harness AI (AGENTS.md, skill, nhật ký dùng AI) | 10 |
| Đánh giá & retro | 10 |
| Chất lượng sản phẩm (đúng yêu cầu, mở rộng/sáng tạo) | 10 |
| Demo | 5 |

## Quy định

- Dùng AI thoải mái; **không sao chép repo của nhóm khác**; bằng chứng phải thật.
- Nhân vật, bối cảnh là bản gốc của lab; asset ngoài chỉ dùng CC0/CC-BY/MIT hoặc tự tạo, ghi nguồn trong `CREDITS.md`. Không commit API key, token, `.env`.
