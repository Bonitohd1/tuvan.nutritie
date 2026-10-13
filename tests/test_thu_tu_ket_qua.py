"""Phép thử Nutritie 13/10/2026 (chị Thúy, màn kết quả tư vấn):
 (1) THỨ TỰ cố định: chỉ số BMI/thước đo -> TƯ VẤN KHOA HỌC -> sản phẩm (trước đó sản phẩm đứng trước tư vấn khoa học).
 (2) thẻ sản phẩm phụ dùng ẢNH thật khi có (trước chỉ vẽ biểu tượng), và BẤM vào thẻ (cả thẻ chính) mở trang sản phẩm.
 Pedia A+ có ảnh từ 13/10/2026 (Drive 'Ảnh sản phẩm' → DIMG.pedia); mất ảnh là đỏ.
Dùng: python tests/test_thu_tu_ket_qua.py [thư-mục]   (chạy trên bản cũ phải ĐỎ)"""
import sys, os, shutil, tempfile, threading, functools, http.server, socketserver
from playwright.sync_api import sync_playwright
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = tempfile.mkdtemp()
for it in os.listdir(SRC):
    if it in ('.git', 'api', 'tests', 'node_modules'): continue
    sp = os.path.join(SRC, it); (shutil.copytree if os.path.isdir(sp) else shutil.copy)(sp, os.path.join(d, it))
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = socketserver.TCPServer(('127.0.0.1', 0), functools.partial(Q, directory=d)); threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f'http://127.0.0.1:{srv.server_address[1]}/'
res = []
def check(n, ok, det=''):
    res.append(bool(ok)); print(('OK   ' if ok else 'FAIL ') + n + ('' if ok else '  ' + str(det)))
def page(pg, obj, m, needs, preterm=''):
    pg.evaluate("""([obj,m,needs,preterm])=>{S.tab='tuvan';S.user={obj:obj,gender:'Nam',senior:false,postpartum:false,preterm:preterm,hist:['Không có'],cur:''};
      S.m=m;S.cls=classify();S.needs=needs;S.step=4;draw();}""", [obj, m, needs, preterm])
    pg.wait_for_timeout(200)
    return pg.evaluate("document.getElementById('view').textContent")
with sync_playwright() as p:
    for eng in ('chromium', 'webkit'):
        b = getattr(p, eng).launch(); ctx = b.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True)
        ctx.add_init_script("localStorage.setItem('nt_pg', JSON.stringify('PG01'))")
        pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:200])); pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith('http://127.0.0.1') else r.abort())
        pg.goto(URL); pg.wait_for_function("document.getElementById('splash').classList.contains('hide')", timeout=30000); pg.wait_for_timeout(500)
        T = lambda s: f'[{eng}] ' + s
        # trẻ 7 tuổi gầy, hay ốm (đúng ca chị Thúy chụp): Pedia A+ + Colostrum DHA
        t = page(pg, 'tre_1_10', {'age': 7, 'w': 16, 'h': 116}, ['Tăng cân', 'Hay ốm / miễn dịch kém'])
        a, s, pr = t.find('Thước đo tăng trưởng'), t.find('TƯ VẤN KHOA HỌC'), t.find('Nutritie Pedia A+')
        check(T('thứ tự: Thước đo (BMI) -> Tư vấn khoa học -> Sản phẩm'), -1 < a < s < pr, (a, s, pr))
        check(T('Pedia A+ (thẻ chính) có ảnh sản phẩm thật, không còn biểu tượng bát cơm'), pg.evaluate("(()=>{const i=document.querySelector('.sku-img img');return !!i&&i.src.indexOf('data:image/jpeg')===0})()"))
        check(T('khối Cảnh báo/Lên đơn nằm SAU sản phẩm'), 0 < pr < t.find('Lên đơn sản phẩm gợi ý'))
        check(T('thẻ phụ Colostrum DHA có ẢNH sản phẩm (không chỉ biểu tượng)'), pg.evaluate("(()=>{const r=document.querySelector('.rec-mini .e');return !!(r&&r.querySelector('img'))})()"))
        pg.evaluate("document.querySelector('.rec-mini').click()"); pg.wait_for_timeout(300)
        st = pg.evaluate("document.getElementById('sheetin').textContent")
        check(T('bấm vào thẻ phụ -> mở trang sản phẩm Colostrum'), 'Colostrum' in st, st[:100])
        pg.evaluate("closeSheet&&closeSheet()") if pg.evaluate("typeof closeSheet==='function'") else None
        t = page(pg, 'tre_1_10', {'age': 7, 'w': 16, 'h': 116}, ['Tăng cân'])
        pg.evaluate("document.querySelector('.sku-body').click()"); pg.wait_for_timeout(300)
        st = pg.evaluate("document.getElementById('sheetin').textContent")
        check(T('bấm vào thẻ chính (ảnh + tên) -> mở trang sản phẩm Pedia A+'), 'Pedia' in st, st[:100])
        # bé 0-12 tháng nhẹ cân: Bio (chính) + Baby (phụ) — cả hai đều có ảnh
        t = page(pg, 'tre_0_12', {'months': 8, 'w': 6.2, 'h': 66}, ['Tăng cân'])
        a, s, pr = t.find('Thước đo tăng trưởng'), t.find('TƯ VẤN KHOA HỌC'), t.find('Nutritie BioA+')
        check(T('bé 0–12 tháng: cũng đúng thứ tự BMI -> khoa học -> sản phẩm'), -1 < a < s < pr, (a, s, pr))
        check(T('Bio (chính) và Baby (phụ) đều có ảnh'), pg.evaluate("!!document.querySelector('.sku-img img')&&!!document.querySelector('.rec-mini .e img')"))
        check(T('không lỗi JS'), not errs, errs)
        b.close()
shutil.rmtree(d, ignore_errors=True)
print(f'TỔNG {sum(res)} / {len(res)}'); sys.exit(0 if all(res) else 1)
