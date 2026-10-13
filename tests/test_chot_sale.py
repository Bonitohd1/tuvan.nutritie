"""Phép thử Nutritie 13/10/2026 — "Hướng dẫn chốt sale" (7 ảnh chị Yến, Drive "Chốt sale theo SKU"):
 (1) 7 tệp ảnh có thật và tải được; (2) nhóm Tài liệu "Kỹ năng chốt sale" hiện đủ 7 mục, mở ra là ảnh (không 404, không "chờ cập nhật"), Back đóng được;
 (3) kết quả tư vấn có nút "Hướng dẫn chốt sale (cho tư vấn viên)" đúng sản phẩm gợi ý; (4) trang sản phẩm có khối này;
 (5) chế độ TRÌNH KHÁCH và ca chống chỉ định KHÔNG có nút này (nội dung nội bộ, có lời tư vấn cả sản phẩm trẻ dưới 24 tháng).
Dùng: python tests/test_chot_sale.py [thư-mục]   (chạy trên bản cũ phải ĐỎ)"""
import sys, os, shutil, tempfile, threading, functools, http.server, socketserver
from playwright.sync_api import sync_playwright

SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = tempfile.mkdtemp()
for it in os.listdir(SRC):
    if it in ('.git', 'api', 'tests', 'node_modules'):
        continue
    sp = os.path.join(SRC, it)
    (shutil.copytree if os.path.isdir(sp) else shutil.copy)(sp, os.path.join(d, it))


class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass


srv = socketserver.TCPServer(('127.0.0.1', 0), functools.partial(Q, directory=d))
threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f'http://127.0.0.1:{srv.server_address[1]}/'
res = []
IDS = ['baby', 'bio', 'pedia', 'growiq', 'mama', 'canxipro', 'colostrum']


def check(n, ok, det=''):
    res.append(bool(ok)); print(('OK   ' if ok else 'FAIL ') + n + ('' if ok else '  ' + str(det)))


def result(pg, obj, m, needs):
    pg.evaluate("""([obj,m,needs])=>{S.tab='tuvan';S.user={obj:obj,gender:'Nam',senior:false,postpartum:false,preterm:'',hist:['Không có'],cur:'',name:'',dob:'',consent:null,phone:''};
      S.m=m;S.cls=classify();S.needs=needs;S.step=4;draw();}""", [obj, m, needs])
    pg.wait_for_timeout(250)
    return pg.evaluate("document.getElementById('view').textContent")


with sync_playwright() as p:
    for eng in ('chromium', 'webkit'):
        b = getattr(p, eng).launch()
        ctx = b.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True)
        ctx.add_init_script("localStorage.setItem('nt_pg', JSON.stringify('PG01'))")
        pg = ctx.new_page(); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)[:200]))
        pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith('http://127.0.0.1') else r.abort())
        T = lambda s: f'[{eng}] ' + s
        pg.goto(URL)
        pg.wait_for_function("document.getElementById('splash').classList.contains('hide')", timeout=30000)
        pg.wait_for_timeout(500)

        # (1) tệp có thật, giải mã được
        ok = pg.evaluate("""async(ids)=>Promise.all(ids.map(i=>new Promise(r=>{const m=new Image();m.onload=()=>r(m.naturalWidth>300&&m.naturalHeight>400);m.onerror=()=>r(false);m.src='assets/chotsale/'+i+'.jpg';})))""", IDS)
        check(T('7 ảnh chốt sale có thật và giải mã được'), all(ok), ok)
        check(T('mọi sản phẩm đều có hướng dẫn trong CHOT_SALE'), pg.evaluate("(ids)=>ids.every(i=>!!CHOT_SALE[i]&&fileReady(CHOT_SALE[i]))", IDS))

        # (2) Tài liệu
        pg.evaluate("go('docs')"); pg.wait_for_timeout(250)
        txt = pg.evaluate("document.getElementById('view').textContent")
        check(T('mục Tài liệu hiện nhóm "Kỹ năng chốt sale"'), 'Kỹ năng chốt sale' in txt)
        rows = pg.evaluate("[...document.querySelectorAll('#view .doc-row')].filter(r=>/Chốt sale —/.test(r.textContent))")
        n_rows = pg.evaluate("[...document.querySelectorAll('#view .doc-row')].filter(r=>/Chốt sale —/.test(r.textContent)).length")
        n_ok = pg.evaluate("[...document.querySelectorAll('#view .doc-row')].filter(r=>/Chốt sale —/.test(r.textContent)&&!r.classList.contains('pend')&&r.getAttribute('onclick')).length")
        check(T('đủ 7 mục chốt sale, cả 7 đều mở được (không "chờ cập nhật")'), n_rows == 7 and n_ok == 7, (n_rows, n_ok))
        pg.evaluate("[...document.querySelectorAll('#view .doc-row')].find(r=>/Chốt sale — Pedia/.test(r.textContent)).click()")
        pg.wait_for_timeout(500)
        img = pg.evaluate("(()=>{const i=document.querySelector('#docreader .dr-img');return i?{src:i.getAttribute('src'),w:i.naturalWidth}:null})()")
        check(T('mở mục Pedia: trình đọc hiện ẢNH chốt sale Pedia (không 404)'), img and 'chotsale/pedia' in img['src'] and img['w'] > 300, img)
        check(T('trình đọc không có link Drive, không iframe'), pg.evaluate("(()=>{const h=document.getElementById('docreader').innerHTML;return h.indexOf('drive.google')<0&&h.indexOf('<iframe')<0})()"))
        pg.click('#docreader .dr-back'); pg.wait_for_timeout(300)
        check(T('"Quay lại" đóng trình đọc'), not pg.evaluate("document.getElementById('docreader').classList.contains('open')"))

        # (3) kết quả tư vấn
        t = result(pg, 'tre_1_10', {'age': 7, 'w': 16, 'h': 116}, ['Tăng cân'])
        check(T('kết quả tư vấn (Pedia) có nút "Hướng dẫn chốt sale (cho tư vấn viên)"'), 'Hướng dẫn chốt sale (cho tư vấn viên)' in t)
        pg.evaluate("[...document.querySelectorAll('#view button')].find(b=>/Hướng dẫn chốt sale/.test(b.textContent)).click()"); pg.wait_for_timeout(500)
        img = pg.evaluate("(()=>{const i=document.querySelector('#docreader .dr-img');return i?{src:i.getAttribute('src'),w:i.naturalWidth}:null})()")
        sub = pg.evaluate("document.querySelector('#docreader .dr-tt').textContent")
        check(T('bấm nút: mở đúng ảnh Pedia, tiêu đề ghi "Dành cho tư vấn viên"'), img and 'chotsale/pedia' in img['src'] and img['w'] > 300 and 'Dành cho tư vấn viên' in sub, (img, sub))
        pg.click('#docreader .dr-back'); pg.wait_for_timeout(300)
        t = result(pg, 'tre_0_12', {'months': 3, 'w': 5.6, 'h': 60}, ['Tăng cân'])
        pg.evaluate("[...document.querySelectorAll('#view button')].find(b=>/Hướng dẫn chốt sale/.test(b.textContent)).click()"); pg.wait_for_timeout(400)
        check(T('bé 3 tháng (Baby A+): nút mở đúng ảnh Baby'), 'chotsale/baby' in (pg.evaluate("(()=>{const i=document.querySelector('#docreader .dr-img');return i?i.getAttribute('src'):''})()")))
        pg.click('#docreader .dr-back'); pg.wait_for_timeout(300)

        # (4) trang sản phẩm
        pg.evaluate("openP('mama')"); pg.wait_for_timeout(300)
        st = pg.evaluate("document.getElementById('sheetin').textContent")
        check(T('trang sản phẩm Mama có khối "Chốt sale (cho tư vấn viên)"'), 'Chốt sale (cho tư vấn viên)' in st and 'Hướng dẫn chốt sale' in st)
        pg.evaluate("closeP()")

        # (5) KHÔNG lộ cho khách
        pg.evaluate("openPresent()"); pg.wait_for_timeout(400)
        pr = pg.evaluate("document.getElementById('present').textContent")
        check(T('chế độ Trình khách KHÔNG có hướng dẫn chốt sale'), 'chốt sale' not in pr.lower(), pr[:100])
        pg.evaluate("closePresent()")
        pg.evaluate("""S.tab='tuvan';S.user={obj:'tre_1_10',gender:'Nam',senior:false,postpartum:false,preterm:'',hist:['Viêm loét dạ dày - tá tràng'],cur:'',name:'',dob:'',consent:null,phone:''};S.m={age:7,w:16,h:116};S.cls=classify();S.needs=['Tăng cân'];S.step=4;draw();""")
        pg.wait_for_timeout(250)
        check(T('ca chống chỉ định KHÔNG có nút chốt sale (không bán lúc đang chống chỉ định)'), 'Hướng dẫn chốt sale' not in pg.evaluate("document.getElementById('view').textContent"))
        check(T('không lỗi JS'), not errs, errs)
        b.close()

shutil.rmtree(d, ignore_errors=True)
print(f'TỔNG {sum(res)} / {len(res)}')
sys.exit(0 if all(res) else 1)
