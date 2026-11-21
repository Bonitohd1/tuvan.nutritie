/* CORS cho /api — QA NT-01 (21/11/2026). TỪNG SAI: 'Access-Control-Allow-Origin: *' + khai báo header X-Bridge-Key mà KHÔNG
   endpoint nào kiểm khoá -> trang bất kỳ đọc được GET /api/orders. App gọi /api cùng tên miền (không cần CORS), nên chỉ mở
   cho tên miền chính thức + danh sách thêm qua biến môi trường NT_CORS_ORIGINS (cách nhau bằng dấu phẩy). */
const BASE = ['https://tuvan-nutritie.vercel.app'];
function allowed() {
  const extra = String(process.env.NT_CORS_ORIGINS || '').split(',').map(s => s.trim()).filter(Boolean);
  return BASE.concat(extra);
}
module.exports = function cors(req, res) {
  const origin = (req.headers && req.headers.origin) || '';
  res.setHeader('Vary', 'Origin');
  if (origin && allowed().indexOf(origin) >= 0) {
    res.setHeader('Access-Control-Allow-Origin', origin);
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, X-Tenant');
    res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  }
  if (req.method === 'OPTIONS') { res.status(204).end(); return true; }
  return false;
};
module.exports.allowed = allowed;
