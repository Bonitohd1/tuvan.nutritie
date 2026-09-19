// Kho lưu tạm dùng chung giữa các lần gọi trong cùng instance (demo). Nâng cấp: dùng @vercel/kv.
const g = globalThis;
if (!g.__NT_STORE) g.__NT_STORE = { orders: [], stock: {} };
module.exports = g.__NT_STORE;
