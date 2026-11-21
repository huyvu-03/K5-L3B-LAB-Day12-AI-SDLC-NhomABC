# Retro nhóm

## Phase 2 (nhanh)
- Điều tốt: Tách rõ module theo sở hữu (`monsters.py`, `quan_customers.py`, `shop.py`, `day.py`) giúp ghép nhánh 6 người mượt, ít conflict; chạy đạt 110/110 test tích hợp M1–M6 trên v1.1.
- Điều tệ: Khi đổi sang v1.1 (thêm bếp `B2`, 4 bàn `T1–T4`), một số fixture test Phase 1 (tọa độ ngoài mép `B1`, giả định 1 bàn) bị vỡ tạm thời trước khi cập nhật.
- 1 hành động cho Phase 3: Trước khi đổi kho đếm → kho cá thể (`v1.2`), thống nhất ngay 1 helper đơn vị nguyên `fresh_units = fresh × 240` và giữ adapter tương thích cho đến mốc bật `v1.2` (`M6.4`).

## Phase 3 (nhanh — rút ra từ lần đổi schema kho)
- Hành động Phase 2 đã áp dụng: Thống nhất `chonoi/freshness.py` (`FRESH_SCALE = 240`) và giữ adapter song song `1.1`/`1.2` giúp `main` chạy xanh suốt quá trình M1–M4 chuyển đổi.
- Lỗi phát hiện khi bật `v1.2`: Huy (M1) phát hiện CLI với `hold: []` ghi `{"items":{}}` thay vì `{"items":[]}` do `tuning` không chứa `contract_version`; M6 đã sửa triệt để trong `chonoi/contract.py` trước khi gắn tag `phase-3`.


## Phase 4 (cuối)
- Rà lại hành động Phase 2: đã làm chưa? vì sao?
- Điều tốt / điều tệ:
- Số liệu: số commit theo người, cách đọc code của nhau, token theo người:
- Một lần AI sai và cách nhóm phát hiện:
- Nếu làm lại, đổi gì:

### Góp ý M1 (huyvu-03)

- Hành động P2 đã áp dụng. Nhóm dùng `FRESH_SCALE = 240` và adapter song song khi đổi kho. Kiểm tra hai tiến trình trên v1.3 vẫn cho JSONL và file kho khớp từng byte.
- AI ban đầu kiểm tra v1.2 với giỏ có đồ. Tôi bổ sung phép thử CLI với giỏ rỗng và phát hiện kho xuất dạng đếm. An sửa lỗi trước tag `phase-3`.
- Lần sau, đưa case giỏ rỗng vào smoke ngay khi thiết kế schema, rồi chạy lại từ clone sạch trước khi đóng gói. [Bằng chứng Phase 3](proof/phase-3/m1.md) · [Kiểm clone Phase 4](proof/phase-4/m1.md)
