# Phép thử của Nutritie

Chạy hết bằng một lệnh (từ gốc kho): `python tests/chay_het.py`

Cần Python 3, Node.js, và `pip install playwright` rồi `playwright install chromium`. Mỗi phép thử tự dựng máy chủ tĩnh tạm và **chặn mọi lời gọi ra ngoài**: không ghi gì vào hệ thống thật.

| File | Kiểm gì |
|---|---|
| `test_man_mo_dau.py` | Màn mở đầu không đứng im (tách ảnh ra tệp, báo mạng chậm, hiện lỗi thật) |
| `test_ho_so_be.py` | Hồ sơ bé có SĐT + câu đồng ý + tìm bé theo SĐT |
| `test_man_quet.py` | Màn quét "Đang phân tích chỉ số" (tiến độ mượt, 5 bước, hoàn tất, chống bấm đúp, giảm chuyển động) |

Phép thử đồng bộ hồ sơ bé với máy chủ Studio nằm ở kho Studio (`backend/tests/thu_dong_bo_nutritie.py`) vì cần máy chủ thật + Postgres tạm.

Ảnh chụp sinh ra ở `tests/_anh/` (không đưa lên Git). Muốn kiểm ngược: sửa tạm một chỗ trong `index.html` và xem phép thử có đỏ không.
