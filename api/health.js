const cors = require('./_cors');
module.exports = (req, res) => {
  if (cors(req, res)) return;
  // Không còn kho RAM (api/_store.js đã gỡ 21/11/2026) -> không báo số đơn.
  res.status(200).json({ ok: true, name: 'Nutritie API', orders_api: 'off (410)', stock_api: 'off (410)', time: Date.now() });
};
