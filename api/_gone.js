/* QA NT-01 + NT-02 (21/11/2026): /api/orders và /api/stock là API DEMO cũ (lưu trong RAM của hàm serverless -> mất khi máy chủ
   ngủ, KHÔNG kiểm quyền: ai cũng GET được toàn bộ đơn kèm SĐT khách, ai cũng POST ghi đè tồn kho).
   Đã đối chiếu 21/11: app KHÔNG còn dùng 2 đường này — đơn gửi thẳng máy chủ Isopharma (api.wintop.vn/api/wintop/nutritie-order,
   lưu Postgres, idempotent) từ 16/10/2026; Studio không gọi tới. Nên TẮT HẲN (410) thay vì vá khoá cho một kho RAM vô dụng.
   Trả 410 cho MỌI phương thức và KHÔNG BAO GIỜ trả dữ liệu đã lưu. */
const cors = require('./_cors');
module.exports = function gone(what, where) {
  return (req, res) => {
    if (cors(req, res)) return;
    res.setHeader('Cache-Control', 'no-store');
    res.status(410).json({
      ok: false, err: 'gone',
      msg: what + ' demo của app Nutritie đã tắt (không kiểm quyền, lưu tạm trong RAM nên mất dữ liệu). ' + where
    });
  };
};
