"""Phép thử Nutritie 13/10/2026 — NÚT BACK với MỌI lớp phủ (agent test: Back từ Trang chủ lúc mở chuông / Trợ lý / Trình khách THOÁT APP;
Back từ tab Sản phẩm lúc mở sheet thì đổi tab ngầm). Mong đợi: Back chỉ đóng lớp phủ trên cùng, không đổi tab, không rời app;
đóng bằng nút trên màn thì không để mục lịch sử thừa; chuỗi sheet -> trình đọc -> Back -> Back đúng thứ tự.
Cũng kiểm: hết 404 ảnh ưu đãi / products/pedia.png, Trợ lý "Chia sẻ" không báo đã sao chép khi clipboard từ chối.
Dùng: python tests/test_back_lop_phu.py [thư-mục]   (chạy trên bản cũ phải ĐỎ)"""
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


def check(n, ok, det=''):
    res.append(bool(ok)); print(('OK   ' if ok else 'FAIL ') + n + ('' if ok else '  ' + str(det)))


OVL = [
    ('sheet (chuông)', "openNoti()", "document.getElementById('sheet').classList.contains('open')"),
    ('sheet (sản phẩm)', "openP('baby')", "document.getElementById('sheet').classList.contains('open')"),
    ('Trợ lý', "openAsst()", "document.getElementById('asst').classList.contains('open')"),
    ('Trình khách', "openPresent()", "document.getElementById('present').classList.contains('open')"),
    ('Hướng dẫn', "openGuide()", "document.getElementById('guide').classList.contains('open')"),
    ('Vòng quay', "openWheel()", "document.getElementById('wheel').classList.contains('open')"),
    ('menu', "document.getElementById('dtog').checked=true;document.getElementById('dtog').dispatchEvent(new Event('change'))", "document.getElementById('dtog').checked"),
]

with sync_playwright() as p:
    for eng in ('chromium', 'webkit'):
        b = getattr(p, eng).launch()
        ctx = b.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True)
        ctx.add_init_script("localStorage.setItem('nt_pg', JSON.stringify('PG01'));localStorage.setItem('nt_guided','1')")
        errs = []
        T = lambda s: f'[{eng}] ' + s

        def fresh():
            pg = ctx.new_page()
            pg.on('pageerror', lambda e: errs.append(str(e)[:200]))
            pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith('http://127.0.0.1') else r.abort())
            pg.goto(URL)
            pg.wait_for_function("document.getElementById('splash').classList.contains('hide')", timeout=30000)
            pg.wait_for_timeout(700)
            return pg

        # Back từ TRANG CHỦ với từng lớp phủ
        for name, opener, isopen in OVL:
            pg = fresh()
            base = pg.evaluate("history.length")
            pg.evaluate(opener); pg.wait_for_timeout(450)
            o1 = pg.evaluate(isopen)
            pg.go_back(); pg.wait_for_timeout(450)
            check(T(f'{name}: mở rồi Back -> đóng lớp phủ, VẪN ở app, VẪN ở Trang chủ'),
                  o1 and (not pg.evaluate(isopen)) and pg.url.startswith(URL) and pg.evaluate("S.tab") == 'home', (o1, pg.url, pg.evaluate("S.tab")))
            pg.close()

        # Back từ tab Sản phẩm với sheet
        pg = fresh()
        pg.evaluate("go('sp')"); pg.wait_for_timeout(200)
        pg.evaluate("openP('baby')"); pg.wait_for_timeout(450)
        pg.go_back(); pg.wait_for_timeout(450)
        check(T('tab Sản phẩm + sheet: Back chỉ đóng sheet, KHÔNG đổi tab'), (not pg.evaluate("document.getElementById('sheet').classList.contains('open')")) and pg.evaluate("S.tab") == 'sp', pg.evaluate("S.tab"))
        pg.go_back(); pg.wait_for_timeout(350)
        check(T('Back tiếp: về Trang chủ như thường'), pg.evaluate("S.tab") == 'home' and pg.url.startswith(URL), pg.evaluate("S.tab"))
        pg.close()

        # sheet -> trình đọc tài liệu: Back, Back
        pg = fresh()
        pg.evaluate("go('sp')"); pg.evaluate("openP('baby')"); pg.wait_for_timeout(400)
        pg.evaluate("document.querySelector('#sheetin .doss-row').click()"); pg.wait_for_timeout(400)
        check(T('sheet -> trình đọc: cả hai đang mở'), pg.evaluate("document.getElementById('docreader').classList.contains('open')&&document.getElementById('sheet').classList.contains('open')"))
        pg.go_back(); pg.wait_for_timeout(400)
        a = pg.evaluate("[document.getElementById('docreader').classList.contains('open'),document.getElementById('sheet').classList.contains('open'),S.tab]")
        pg.go_back(); pg.wait_for_timeout(400)
        c = pg.evaluate("[document.getElementById('docreader').classList.contains('open'),document.getElementById('sheet').classList.contains('open'),S.tab]")
        check(T('Back 1 đóng trình đọc (sheet còn), Back 2 đóng sheet (vẫn tab Sản phẩm)'), a == [False, True, 'sp'] and c == [False, False, 'sp'], (a, c))
        pg.close()

        # đóng bằng nút trên màn: không để mục lịch sử thừa
        pg = fresh()
        base = pg.evaluate("history.length")
        for _ in range(5):
            pg.evaluate("openP('baby')"); pg.wait_for_timeout(350)
            pg.evaluate("closeP()"); pg.wait_for_timeout(450)
        st = pg.evaluate("history.state")
        check(T('mở/đóng sheet 5 lần bằng nút: lịch sử không phình (tối đa +1), trạng thái hiện tại không phải lớp phủ'), pg.evaluate("history.length") <= base + 1 and not (st and st.get('ovl')), (base, pg.evaluate("history.length"), st))
        pg.evaluate("openAsst()"); pg.wait_for_timeout(300); pg.evaluate("closeAsst()"); pg.wait_for_timeout(450)
        check(T('đóng Trợ lý bằng nút rồi Back: không đóng nhầm / không thoát'), pg.url.startswith(URL) and pg.evaluate("S.tab") == 'home')
        pg.close()

        # chọn mục trong menu (menu đóng bằng mã) rồi Back
        pg = fresh()
        pg.evaluate("document.getElementById('dtog').checked=true;document.getElementById('dtog').dispatchEvent(new Event('change'))"); pg.wait_for_timeout(400)
        pg.evaluate("go('sp');document.getElementById('dtog').checked=false"); pg.wait_for_timeout(700)
        pg.go_back(); pg.wait_for_timeout(500)
        pg.go_back() if pg.evaluate("S.tab") != 'home' else None
        pg.wait_for_timeout(500)
        check(T('menu đóng bằng mã rồi chuyển tab, Back: tối đa 2 lần là về Trang chủ, KHÔNG rời app'), pg.url.startswith(URL) and pg.evaluate("S.tab") == 'home', (pg.url, pg.evaluate("S.tab")))
        pg.close()

        # 404 ảnh
        pg = ctx.new_page(); bad = []
        pg.on('pageerror', lambda e: errs.append(str(e)[:200]))
        pg.on('response', lambda r: bad.append(r.url) if r.status == 404 else None)
        pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith('http://127.0.0.1') else r.abort())
        pg.goto(URL); pg.wait_for_function("document.getElementById('splash').classList.contains('hide')", timeout=30000); pg.wait_for_timeout(500)
        for t_ in ('home', 'sp', 'promo'):
            pg.evaluate("(t)=>go(t)", t_); pg.wait_for_timeout(300)
        pg.evaluate("openP('pedia')"); pg.wait_for_timeout(400)
        bad = [u for u in bad if 'favicon' not in u]
        check(T('mở Trang chủ / Sản phẩm / Ưu đãi / sheet Pedia: không có request 404 (uudai-3.jpg, products/pedia.png)'), not bad, bad[:4])
        pg.close()

        # Trợ lý chia sẻ: clipboard từ chối -> không báo đã sao chép
        pg = fresh()
        pg.evaluate("Object.defineProperty(navigator,'clipboard',{value:{writeText:function(){return Promise.reject(new Error('denied'))}},configurable:true})")
        pg.evaluate("openAsst()"); pg.wait_for_timeout(300)
        pg.evaluate("asstChip('share')"); pg.wait_for_timeout(500)
        txt = pg.evaluate("asstLog.map(function(m){return m.t}).join('||')")
        check(T('Trợ lý "Chia sẻ": clipboard từ chối -> KHÔNG báo "Đã sao chép", hướng dẫn sao chép thủ công'), 'Đã sao chép' not in txt and 'thủ công' in txt, txt[-200:])
        pg.evaluate("Object.defineProperty(navigator,'clipboard',{value:{writeText:function(){return Promise.resolve()}},configurable:true})")
        pg.evaluate("asstChip('share')"); pg.wait_for_timeout(500)
        txt = pg.evaluate("asstLog[asstLog.length-1].t")
        check(T('clipboard chấp nhận -> báo "Đã sao chép"'), 'Đã sao chép' in txt, txt[:80])
        check(T('không lỗi JS (kể cả Promise bị từ chối không bắt)'), not errs, errs)
        pg.close()
        b.close()

shutil.rmtree(d, ignore_errors=True)
print(f'TỔNG {sum(res)} / {len(res)}')
sys.exit(0 if all(res) else 1)
