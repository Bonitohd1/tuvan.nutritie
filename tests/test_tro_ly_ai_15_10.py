"""Phep thu Nutritie 15/10/2026 — Tro ly AI hoi dap (phan hoi chi Duong Yen).
 - Be <12 thang KHONG bi goi y SP tu 1 tuoi (be 9 thang tung ra Pedia -> sai tuoi + NĐ100).
 - Be <6 thang -> bu me hoan toan (khong day SP).
 - Be 12-24 thang: goi y duoc theo nhu cau + KEM cau sua me.
 - Be >=24 thang / nguoi lon: goi y binh thuong, KHONG kem cau sua me.
 - Nhan dien "nen uong gi / bo sung sua" (truoc roi vao "chua ro y").
 - Me bau KHONG bi nham thanh be theo so thang thai.
 - Colostrum (sua bot pha san): da bo cau "Dung theo huong dan tren nhan hoac cua can bo y te".
Dung: python tests/test_tro_ly_ai_15_10.py [thu-muc]   (ban cu phai DO: dat REV=1)
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
    old = os.path.join(os.environ.get('TEMP', '/tmp'), 'index_before_ai.html')
    if os.path.exists(old):
        shutil.copy(old, os.path.join(d, 'index.html')); print('*** REV: dung ban CU', old)


class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass


srv = socketserver.TCPServer(('127.0.0.1', 0), functools.partial(Q, directory=d))
threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f'http://127.0.0.1:{srv.server_address[1]}/'
res = []


def check(n, ok, det=''):
    res.append(bool(ok)); print(('OK   ' if ok else 'FAIL ') + n + ('' if ok else '  ' + str(det)[:260]))


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

        def ask(q):
            return pg.evaluate("(q)=>asstReply(q)", q)

        r = ask('bé 9 tháng nhẹ cân nên uống gì')
        check(T('bé 9 tháng nhẹ cân: KHÔNG gợi ý Pedia/Grow IQ'), ('Pedia' not in r) and ('Grow IQ' not in r), r)
        check(T('bé 9 tháng: nhắc nhóm dưới 12 tháng + khám chuyên gia'), ('dưới 12 tháng' in r) and ('Sữa mẹ' in r), r)

        r = ask('bé 3 tháng nên uống gì')
        check(T('bé 3 tháng: bú mẹ hoàn toàn, KHÔNG "chưa rõ ý", KHÔNG đẩy SP'),
              ('bú mẹ hoàn toàn' in r) and ('chưa rõ ý' not in r) and ('Pedia' not in r), r)

        r = ask('bé 3 tháng muốn bổ sung sữa công thức thì nên uống loại nào')
        check(T('bé 3 tháng bổ sung sữa công thức: nhận diện được (không "chưa rõ ý")'),
              ('chưa rõ ý' not in r) and ('dưới 6 tháng' in r or 'bú mẹ' in r), r)

        r = ask('bé 18 tháng nhẹ cân nên uống gì')
        check(T('bé 18 tháng nhẹ cân: ĐƯỢC gợi ý Pedia + KÈM câu sữa mẹ (dưới 24 tháng)'),
              ('Pedia' in r) and ('Sữa mẹ' in r), r)

        r = ask('bé 5 tuổi biếng ăn nên uống gì')
        check(T('bé 5 tuổi biếng ăn: gợi ý Pedia, KHÔNG kèm câu sữa mẹ (>=24 tháng)'),
              ('Pedia' in r) and ('Sữa mẹ' not in r), r)

        r = ask('mẹ bầu nên uống gì')
        check(T('mẹ bầu: gợi ý Mama (không nhầm tuổi bé)'), 'Mama' in r, r)

        r = ask('nên uống sữa loại nào')
        check(T('hỏi chung chưa rõ tuổi: hỏi lại tuổi + nhu cầu (không "chưa rõ ý")'),
              ('mấy tháng' in r) and ('chưa rõ ý' not in r), r)

        r = ask('bé 9 tháng uống Pedia được không')
        check(T('bé 9 tháng + hỏi Pedia đích danh: cảnh báo SP từ 1 tuổi'),
              ('từ 1 tuổi' in r.lower()) or ('dưới 12 tháng' in r), r)

        # câu bôi vàng Colostrum đã bỏ
        cu = pg.evaluate("()=>{var p=P('colostrum');return p?p.usage:''}")
        check(T('Colostrum usage: đã bỏ câu "Dùng theo hướng dẫn trên nhãn hoặc của cán bộ y tế"'),
              'hướng dẫn trên nhãn hoặc của cán bộ y tế' not in cu, cu)

        errs[:] = [e for e in errs if 'Response served by service worker' not in e]
        check(T('không lỗi JS'), not errs, errs)
        pg.close(); b.close()

shutil.rmtree(d, ignore_errors=True)
print(f'TỔNG {sum(res)} / {len(res)}')
sys.exit(0 if all(res) else 1)
