const cors = require('./_cors'); const store = require('./_store');
module.exports = (req, res) => {
  if (cors(req, res)) return;
  res.status(200).json({ ok: true, name: 'Nutritie API', env: 'demo (in-memory)', orders: store.orders.length, time: Date.now() });
};
