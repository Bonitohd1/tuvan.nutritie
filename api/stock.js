// Đã tắt — xem api/_gone.js (QA NT-01/NT-02, 21/11/2026). Số tồn DEMO cũ ({baby:48,…}) từng GHI ĐÈ số thật trên máy PG
// khi bấm "Đồng bộ tồn kho ngay" kèm câu "Đã đồng bộ tồn kho từ hệ thống" — số giả. Nay tồn kho lưu tại máy cho tới khi nối kho thật.
module.exports = require('./_gone')('API tồn kho',
  'Tồn kho đang lưu tại máy PG; nối kho thật ở Khu quản trị > Kết nối kho & Tích hợp.');
