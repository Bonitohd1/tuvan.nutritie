const cors = require('./_cors'); const store = require('./_store');
const DEFAULT = { baby: 48, bio: 36, growiq: 24, colostrum: 12, canxipro: 30, mama: 20 };
module.exports = (req, res) => {
  if (cors(req, res)) return;
  if (req.method === 'POST') { // cập nhật tồn (demo)
    let b = req.body; if (typeof b === 'string') { try { b = JSON.parse(b); } catch (e) { b = {}; } }
    if (b && b.items) store.stock = Object.assign({}, store.stock, b.items);
    return res.status(200).json({ ok: true });
  }
  res.status(200).json({ ok: true, items: Object.assign({}, DEFAULT, store.stock), area: 'Kho demo Nutritie', at: Date.now() });
};
