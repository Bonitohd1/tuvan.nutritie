"""Phép thử Nutritie 13/10/2026: chỉ MỘT kiểu chữ, giống Wintop (chị Thúy: "đang 2 font").
Gốc: Space Grotesk không có glyph tiếng Việt có dấu nên bị ghép với Be Vietnam Pro -> nhìn thành 2 font.
Kiểm: (1) không còn yêu cầu mạng tới fonts.googleapis.com, (2) không phần tử nào còn khai báo Space Grotesk, (3) mọi phần tử mẫu cùng MỘT chuỗi font.
Dùng: python tests/test_mot_font.py [thư-mục-tuvan.nutritie]   (chạy trên bản cũ phải ĐỎ)"""
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
STACK = '"Be Vietnam Pro", system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif'
with sync_playwright() as p:
    for eng in ('chromium', 'webkit'):
        b = getattr(p, eng).launch(); ctx = b.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True)
        ctx.add_init_script("localStorage.setItem('nt_pg', JSON.stringify('PG01'))")
        pg = ctx.new_page(); reqs = []
        pg.on('request', lambda r: reqs.append(r.url))
        pg.route('https://**', lambda r: r.abort())
        pg.goto(URL); pg.wait_for_function("document.getElementById('splash').classList.contains('hide')", timeout=30000); pg.wait_for_timeout(500)
        T = lambda s: f'[{eng}] ' + s
        check(T('không còn nạp font từ Google Fonts'), not [u for u in reqs if 'fonts.g' in u], [u for u in reqs if 'fonts.g' in u])
        fams = {}
        for tab in ('home', 'sp', 'tuvan', 'docs'):
            pg.evaluate(f"go('{tab}')"); pg.wait_for_timeout(250)
            r = pg.evaluate("""()=>{const o={};document.querySelectorAll('#view *, #nav *, header *').forEach(e=>{const f=getComputedStyle(e).fontFamily;if(e.childNodes.length&&[...e.childNodes].some(n=>n.nodeType===3&&n.textContent.trim()))o[f]=(o[f]||0)+1});return o}""")
            for k, v in r.items(): fams[k] = fams.get(k, 0) + v
        check(T('không phần tử nào dùng Space Grotesk'), not [k for k in fams if 'Space Grotesk' in k], fams)
        check(T('mọi chữ trên 4 màn dùng ĐÚNG MỘT chuỗi font'), len(fams) == 1, fams)
        norm = lambda s: s.replace('"', '').replace("'", '').replace(' ', '')   # WebKit Windows ghi có nháy, WebKit Linux (CI) ghi không nháy
        check(T('chuỗi font giống Wintop (Be Vietnam Pro -> font hệ thống)'), norm(list(fams)[0]) == norm(STACK) if fams else False, fams)
        b.close()
shutil.rmtree(d, ignore_errors=True)
print(f'TỔNG {sum(res)} / {len(res)}'); sys.exit(0 if all(res) else 1)
