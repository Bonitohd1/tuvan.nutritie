const cors = require('./_cors');
module.exports = (req, res) => {
  if (cors(req, res)) return;
  // Catalog để trống: app dùng PRODUCTS nội bộ. Có thể trả SKU map khi nối KiotViet thật.
  res.status(200).json({ ok: true, items: [], note: 'App dùng Product Master nội bộ; endpoint sẵn để nối KiotViet.' });
};
