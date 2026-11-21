# Nutritie — App Tư vấn & Bán hàng (PG)

Ứng dụng tư vấn dinh dưỡng & lên đơn cho PG tại điểm bán. **Frontend tĩnh (self-contained, chạy offline)** + **API serverless** trên Vercel.

## Cấu trúc
- `index.html` — toàn bộ app (engine BMI/Z-score WHO, tư vấn, lên đơn, tồn kho, thống kê, admin…). Ảnh nhúng sẵn (base64) nên chạy offline, không cần thư mục ảnh.
- `qr.min.js` — sinh QR mã đơn (offline).
- `api/` — API serverless (Node) trên Vercel:
  - `GET /api/health` — kiểm tra tình trạng.
  - `GET /api/catalog` — danh mục (để trống; sẵn để nối KiotViet).
  - `/api/orders`, `/api/stock` — **ĐÃ TẮT (410) từ 21/11/2026** (QA NT-01/NT-02): bản demo cũ lưu trong RAM (mất khi máy chủ ngủ)
    và KHÔNG kiểm quyền (ai cũng đọc được đơn kèm SĐT khách, ai cũng ghi đè tồn kho). Đơn từ app gửi thẳng máy chủ Isopharma
    `https://api.wintop.vn/api/wintop/nutritie-order` (Postgres, idempotent) từ 16/10/2026; tồn kho lưu tại máy PG cho tới khi nối kho thật.
  - CORS chỉ mở cho `https://tuvan-nutritie.vercel.app` (+ biến môi trường `NT_CORS_ORIGINS`, cách nhau dấu phẩy).
- Khu quản trị: mã PIN chỉ là cổng GIAO DIỆN trên chính máy (app không có máy chủ riêng). Máy chỉ lưu bản băm SHA-256 + muối;
  vào bằng PIN mặc định đã bàn giao thì app bắt đặt PIN riêng trước khi xem đơn / khách / xuất CSV.

## Deploy nhanh (GitHub + Vercel)
1. Push mã lên GitHub (repo đã tạo sẵn):
   ```bash
   git push -u origin main
   ```
   (chạy từ máy bạn — đã đăng nhập GitHub. Nếu bị hỏi, đăng nhập bằng tài khoản Bonitohd1.)
2. Vào https://vercel.com → **Add New… → Project** → **Import** repo `tuwvan.nutritie` → **Deploy** (không cần cấu hình gì thêm; Vercel tự nhận `index.html` + thư mục `api/`).
3. Xong: có URL dạng `https://tuwvan-nutritie.vercel.app` — gửi khách mở trên điện thoại để test.

## Nối backend thật (sau này)
- Đơn hàng: đã nối máy chủ Isopharma (`SYNC_URL` trong `index.html`).
- Kho thật (KiotViet/Sapo/…): cấu hình ở Khu quản trị > Kết nối kho & Tích hợp (gọi kho NGOÀI qua `baseUrl`), hoặc điền `STOCK_URL`.
  Khoá API thật phải nằm ở máy chủ trung gian, KHÔNG để trong mã phía trình duyệt.

## Ảnh banner ưu đãi
Bỏ ảnh vuông vào (khi có): app đọc `Ưu đãi/uudai-1.jpg…3.jpg`. Bản deploy hiện nhúng ảnh SP/CSR; banner CTKM designer làm xong sẽ nhúng bổ sung.
