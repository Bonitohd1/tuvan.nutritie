"""Phep thu Nutritie 16/10/2026 — anh san pham CO NEN (background) trong Trinh khach.
 Khach Duong Yen: "anh san pham de background cho noi bat". 7 lon chup co nen hoa anh dao (assets/bg/*.jpg),
 cung 1 tong. Luoi + hero chi tiet Trinh khach dung anh nen (cover); fallback ve anh cat nen neu loi.
Dung: python tests/test_anh_nen_16_10.py [thu-muc]   (ban cu phai DO: dat REV=1)
"""
import sys, os, shutil, tempfile, threading, functools, http.server, socketserver
from playwright.sync_api import sync_playwright

SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = tempfile.mkdtemp()
for it in os.listdir(SRC):
    if it in ('.git', 'api', 'tests', 'node_modules'): continue
    sp = os.path.join(SRC, it)
    (shutil.copytree if os.path.isdir(sp) else shutil.copy)(sp, os.path.join(d, it))
if os.environ.get('REV') == '1':
    old = os.path.join(os.environ.get('TEMP', '/tmp'), 'index_before_bg.html')
    if os.path.exists(old):
        shutil.copy(old, os.path.join(d, 'index.html')); print('*** REV: dung ban CU', old)


class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass


srv = socketserver.TCPServer(('127.0.0.1', 0), functools.partial(Q, directory=d))
threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f'http://127.0.0.1:{srv.server_address[1]}/'
res = []
BG = ['baby', 'bio', 'pedia', 'growiq', 'canxipro', 'mama', 'colostrum']


def check(n, ok, det=''):
    res.append(bool(ok)); print(('OK   ' if ok else 'FAIL ') + n + ('' if ok else '  ' + str(det)[:220]))


with sync_playwright() as p:
    for eng in ('chromium', 'webkit'):
        b = getattr(p, eng).launch()
        T = lambda s: f'[{eng}] ' + s
        ctx = b.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True)
        ctx.add_init_script("localStorage.setItem('nt_pg', JSON.stringify('PG01'))")
        pg = ctx.new_page(); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)[:200]))
        pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith('http://127.0.0.1') else r.abort())
        pg.goto(URL); pg.wait_for_function("document.getElementById('splash').classList.contains('hide')", timeout=30000); pg.wait_for_timeout(300)

        # 7 file anh nen co that
        for k in BG:
            r = pg.evaluate("(u)=>fetch(u).then(x=>x.ok).catch(()=>false)", 'assets/bg/' + k + '.jpg')
            check(T(f'có file ảnh nền assets/bg/{k}.jpg'), r, k)

        pg.evaluate("openPresent(); presGo('sanpham')"); pg.wait_for_timeout(700)
        grid = pg.evaluate("""(()=>[...document.querySelectorAll('#present .pr-pcard .pr-pimg img.bgi')]
          .map(i=>({src:i.getAttribute('src'),ok:i.complete&&i.naturalWidth>0})))()""")
        check(T('lưới Trình khách: cả 7 lon dùng ảnh NỀN (class bgi, assets/bg/*.jpg) + load được'),
              len(grid) == 7 and all(g['ok'] and g['src'].startswith('assets/bg/') for g in grid), grid)

        pg.evaluate("presProduct('pedia')"); pg.wait_for_timeout(600)
        hero = pg.evaluate("""(()=>{var i=document.querySelector('#present .pr-phero.bg img.bgi');
          return i?{ok:i.complete&&i.naturalWidth>0,src:i.getAttribute('src')}:null})()""")
        check(T('hero chi tiết Trình khách: ảnh nền vuông (pr-phero.bg img.bgi) load được'),
              hero and hero['ok'] and hero['src'] == 'assets/bg/pedia.jpg', hero)

        # fallback: SP không có ảnh nền -> không vỡ (dùng BG_PRODUCTS; giả 1 id lạ)
        safe = pg.evaluate("typeof bgimg==='function' && bgimg('khong_co')===''")
        check(T('bgimg(id lạ) trả rỗng -> rơi về ảnh cắt nền (không vỡ)'), safe)

        errs[:] = [e for e in errs if 'Response served by service worker' not in e]
        check(T('không lỗi JS'), not errs, errs)
        pg.close(); b.close()

shutil.rmtree(d, ignore_errors=True)
print(f'TỔNG {sum(res)} / {len(res)}')
sys.exit(0 if all(res) else 1)
