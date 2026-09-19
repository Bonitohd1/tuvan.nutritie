# Nutritie — App Tư vấn & Bán hàng (PG)

Ứng dụng tư vấn dinh dưỡng & lên đơn cho PG tại điểm bán. **Frontend tĩnh (self-contained, chạy offline)** + **API serverless** trên Vercel.

## Cấu trúc
- `index.html` — toàn bộ app (engine BMI/Z-score WHO, tư vấn, lên đơn, tồn kho, thống kê, admin…). Ảnh nhúng sẵn (base64) nên chạy offline, không cần thư mục ảnh.
- `qr.min.js` — sinh QR mã đơn (offline).
- `api/` — API serverless (Node) trên Vercel:
  - `GET /api/health` — kiểm tra tình trạng.
  - `POST /api/orders` — nhận đơn từ app; `GET /api/orders` — xem đơn đã nhận.
  - `GET /api/stock` — tồn kho (demo); `POST /api/stock` — cập nhật tồn.
  - `GET /api/catalog` — danh mục (để trống; sẵn để nối KiotViet).
- Lưu trữ: **in-memory (demo)** — dữ liệu reset khi server ngủ. Nâng cấp bền vững: dùng Vercel KV/Postgres (xem cuối file).

## Deploy nhanh (GitHub + Vercel)
1. Push mã lên GitHub (repo đã tạo sẵn):
   ```bash
   git push -u origin main
   ```
   (chạy từ máy bạn — đã đăng nhập GitHub. Nếu bị hỏi, đăng nhập bằng tài khoản Bonitohd1.)
2. Vào https://vercel.com → **Add New… → Project** → **Import** repo `tuwvan.nutritie` → **Deploy** (không cần cấu hình gì thêm; Vercel tự nhận `index.html` + thư mục `api/`).
3. Xong: có URL dạng `https://tuwvan-nutritie.vercel.app` — gửi khách mở trên điện thoại để test.

## Nối backend thật (sau này)
- KiotViet/kho thật: sửa `api/orders.js`, `api/stock.js` để gọi hệ thống thật; app đã trỏ sẵn `SYNC_URL=/api/orders`, `STOCK_URL=/api/stock`.
- Lưu bền: cài `@vercel/kv`, bật Vercel KV, thay mảng in-memory trong `api/_store.js` bằng KV.

## Ảnh banner ưu đãi
Bỏ ảnh vuông vào (khi có): app đọc `Ưu đãi/uudai-1.jpg…3.jpg`. Bản deploy hiện nhúng ảnh SP/CSR; banner CTKM designer làm xong sẽ nhúng bổ sung.
