const cors = require('./_cors'); const store = require('./_store');
module.exports = (req, res) => {
  if (cors(req, res)) return;
  if (req.method === 'POST') {
    let b = req.body; if (typeof b === 'string') { try { b = JSON.parse(b); } catch (e) { b = {}; } }
    b = b || {};
    const o = Object.assign({}, b, {
      serverId: 'NT' + Date.now().toString(36).toUpperCase(),
      tenant: req.headers['x-tenant'] || 'nutritie',
      receivedAt: Date.now(), status: 'received'
    });
    store.orders.push(o);
    return res.status(200).json({ ok: true, ref: o.serverId, kiotvietId: o.serverId });
  }
  if (req.method === 'GET') {
    return res.status(200).json({ ok: true, count: store.orders.length, orders: store.orders });
  }
  return res.status(405).json({ ok: false, err: 'method_not_allowed' });
};
