"""Phép thử Nutritie 13/10/2026: app PHẢI khởi động được khi trang tải CHẬM theo từng mảnh.

VÌ SAO có phép thử này: chị Thúy chụp màn hình trên Zalo: "Không khởi động được ứng dụng: TypeError: null is not an object
(evaluating 'document.getElementById('scmc').src=MASCOT')". Nguyên nhân: ảnh #scmc có src="" + onerror="this.remove()". Trình duyệt coi
src rỗng là LỖI và bắn sự kiện onerror NGAY khi phân tích tới thẻ ảnh. Khi mạng tải trang thành nhiều mảnh (Zalo in-app, 4G yếu), sự kiện đó
chạy trước đoạn mã khởi động ở cuối tệp -> phần tử đã bị gỡ -> getElementById trả null -> cả app chết. Máy nhà phát triển tải một lượt
nên KHÔNG BAO GIỜ lộ (phép thử cũ xanh hết). Phép thử này cố tình gửi nửa đầu trang, NGHỈ 1 giây, rồi gửi nửa sau.

Dùng: python tests/test_khoi_dong_tai_cham.py [thư-mục-tuvan.nutritie]
"""
import sys, os, re, shutil, tempfile, threading, http.server, socketserver, time
from playwright.sync_api import sync_playwright

SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
res = []
def check(n, ok, det=''):
    res.append(bool(ok)); print(('OK   ' if ok else 'FAIL ') + n + ('' if ok else '  ' + str(det)))

tmp = tempfile.mkdtemp(prefix='nt_slow_')
shutil.copytree(SRC, os.path.join(tmp, 's'), ignore=shutil.ignore_patterns('.git', 'tests', 'node_modules', '_anh', '.github'))
root = os.path.join(tmp, 's')
html = open(os.path.join(root, 'index.html'), 'rb').read()

# điểm cắt: ngay SAU thẻ ảnh của màn quét (#scmc) — trước đoạn mã khởi động ở cuối tệp
m = re.search(rb'<img[^>]*id="scmc"[^>]*>', html)
cut = (m.end() + 40) if m else len(html) // 2
DELAY = float(os.environ.get('CHUNK_DELAY', '1.2'))


class Slow(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=root, **k)
    def log_message(self, *a): pass
    def do_GET(self):
        if self.path.split('?')[0] in ('/', '/index.html'):
            self.send_response(200); self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(html))); self.send_header('Cache-Control', 'no-store'); self.end_headers()
            try:
                self.wfile.write(html[:cut]); self.wfile.flush(); time.sleep(DELAY)
                self.wfile.write(html[cut:]); self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass
        else:
            super().do_GET()


class Srv(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True

srv = Srv(('127.0.0.1', 0), Slow); threading.Thread(target=srv.serve_forever, daemon=True).start()
base = f'http://127.0.0.1:{srv.server_address[1]}/'
check('tìm được điểm cắt sau thẻ #scmc (nếu FAIL: cấu trúc trang đổi, sửa phép thử)', bool(m))

with sync_playwright() as p:
    for eng in ('chromium', 'webkit'):
        b = getattr(p, eng).launch()
        ctx = b.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True); pg = ctx.new_page()
        errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)[:200]))
        pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith('http://127.0.0.1') else r.abort())      # chặn mọi lời gọi ra ngoài
        pg.goto(base, wait_until='commit')
        try:
            pg.wait_for_function("document.getElementById('splash') && document.getElementById('splash').classList.contains('hide')", timeout=30000)
            hid = True
        except Exception as e:
            hid = False
        txt = pg.evaluate("(document.getElementById('spslow')||{}).textContent||''") if hid is False else ''
        check(f'[{eng}] tải chậm {DELAY}s giữa trang: màn mở đầu VẪN tắt (app vào được)', hid, txt[:160])
        check(f'[{eng}] không có lỗi "null" lúc khởi động', not [e for e in errs if 'null' in e or 'getElementById' in e], errs)
        if hid:
            pg.wait_for_timeout(700)
            check(f'[{eng}] sau màn mở đầu thấy màn đăng nhập', pg.evaluate("getComputedStyle(document.getElementById('login')).display") == 'flex')
        b.close()

shutil.rmtree(tmp, ignore_errors=True)
print(f'TỔNG {sum(res)} / {len(res)}')
sys.exit(0 if all(res) else 1)
