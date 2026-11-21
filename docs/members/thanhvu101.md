# thanhvu101 — phản tư cá nhân (≤ 200 từ)

- **Tôi đã làm (kèm link commit):**
  - Đợt 1 (`M5.1`, commit `6b1e327`): Cập nhật `AGENTS.md` với bảng phân công 6 module và quy tắc làm việc với AI, xây dựng 2 skill nhóm (`.agents/skills/verify-phase/SKILL.md` và `.agents/skills/ui-contract-sync/SKILL.md`), khởi tạo nhật ký `docs/ai-usage-log.md`.
  - Đợt 2 (`M5.2`, commit `69c6f31`): Chốt tài liệu giao diện `docs/ui-contract.md` liệt kê đầy đủ lệnh UI gửi (`POST /input`, `POST /restart`) và các trường UI đọc từ `GET /state` cho cả 2 chế độ `gather` và `quan`.
  - Đợt 3 (`M5.3`, commit `4237aff`): Nâng cấp HUD `chonoi/web/index.html` cho buổi sáng (`gather`) và quán nhỏ nhà bè (`quan`), mở rộng `chonoi/live.py` phục vụ tài nguyên tĩnh `/assets/` kèm cơ chế fallback Canvas 2D.
  - Đợt 4 (`M5.4`): Tích hợp hình nền `chonoi/web/assets/gather_bg.png`, chạy kiểm thử trực tiếp `chonoi.live` ở cả 2 chế độ và ghi nhận bằng chứng `docs/proof/phase-1/m5.md`.
- **Tôi đã review (kèm link):** Review chéo với `M6` (`K0heii`) về hợp đồng `snapshot` và `ui-contract.md`.
- **AI sai ở đâu và tôi phát hiện thế nào:** Khi vẽ HUD quán ăn, cần tính rõ "Kho khả dụng" bằng tồn kho vật lý trừ đi tổng nguyên liệu đang giữ chỗ (`reserved`) của khách và canh đúng đường chân trời của `gather_bg.png` khớp mặt nước `d = 0`.
- **Điều tôi học được:** Tách biệt tuyệt đối tầng hiển thị `chonoi.live` (chỉ đọc `snapshot`) khỏi lớp mô phỏng `sim` giúp thêm đồ họa, hình nền và âm thanh mà không bao giờ làm lệch tính tất định byte-for-byte của `headless`.
