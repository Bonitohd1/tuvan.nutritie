"""Phep thu Nutritie 16/10/2026 — noi Data Hub (phien tu van) + XP/Leaderboard that.
 - sendTvSession: ket thuc tu van -> xep hang doi phien (1 lan/phien); SDT chi gui khi khach dong y (NĐ100).
 - _ntOnline(): KHONG goi may chu khi chay localhost (test) -> khong loi mang gia.
 - renderLeaderboard: offline -> demo (co "mo phong"); ham pushNtXp/fetchNtLb ton tai.
Dung: python tests/test_datahub_xp_16_10.py [thu-muc]   (ban cu phai DO: dat REV=1)
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
    old = os.path.join(os.environ.get('TEMP', '/tmp'), 'index_before_dhub.html')
    if os.path.exists(old):
        shutil.copy(old, os.path.join(d, 'index.html')); print('*** REV: dung ban CU', old)


class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass


srv = socketserver.TCPServer(('127.0.0.1', 0), functools.partial(Q, directory=d))
threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f'http://127.0.0.1:{srv.server_address[1]}/'
res = []


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
        pg.goto(URL); pg.wait_for_function("document.getElementById('splash').classList.contains('hide')", timeout=30000); pg.wait_for_timeout(400)

        fx = pg.evaluate("[typeof pushNtXp,typeof fetchNtLb,typeof sendTvSession,typeof _ntOnline]")
        check(T('có hàm pushNtXp / fetchNtLb / sendTvSession / _ntOnline'), fx == ['function'] * 4, fx)
        check(T('_ntOnline() = false trên localhost (không gọi máy chủ trong test)'), pg.evaluate("_ntOnline()") is False)

        # tư vấn bé 2 tuổi, CÓ đồng ý + SĐT -> queue 1 phiên, có SĐT
        q = pg.evaluate("""(()=>{localStorage.removeItem('nt_sess_queue_v1');startTV();S.tab='tuvan';
          S.user.obj='tre_1_10';S.user.gender='Nam';S.user.consent=true;S.user.phone='0912345678';S.user.name='Bé Na';
          S.m={age:'2',w:'11',h:'85'};S.cls=classify();S.step=4;draw();
          var a=JSON.parse(localStorage.getItem('nt_sess_queue_v1')||'[]');return {n:a.length,rec:a[a.length-1]};})()""")
        check(T('kết thúc tư vấn -> xếp 1 phiên vào hàng đợi'), q['n'] == 1, q)
        r = q.get('rec') or {}
        check(T('phiên có clientId + objective + payload'), bool(r.get('clientId')) and r.get('objective') == 'tre_1_10' and bool(r.get('payload')), r)
        check(T('khách ĐỒNG Ý -> phiên CÓ SĐT'), r.get('phone') == '0912345678', r.get('phone'))

        # vẽ lại cùng phiên -> KHÔNG xếp thêm (1 lần/phiên)
        n2 = pg.evaluate("(()=>{draw();return (JSON.parse(localStorage.getItem('nt_sess_queue_v1')||'[]')).length})()")
        check(T('vẽ lại cùng phiên -> không gửi trùng (vẫn 1)'), n2 == 1, n2)

        # phiên mới KHÔNG đồng ý -> SĐT rỗng
        q2 = pg.evaluate("""(()=>{startTV();S.tab='tuvan';S.user.obj='tre_1_10';S.user.gender='Nữ';S.user.consent=false;S.user.phone='0912345679';
          S.m={age:'3',w:'14',h:'95'};S.cls=classify();S.step=4;draw();
          var a=JSON.parse(localStorage.getItem('nt_sess_queue_v1')||'[]');return {n:a.length,phone:a[a.length-1].phone};})()""")
        check(T('phiên mới -> queue tăng (2); KHÔNG đồng ý -> SĐT RỖNG (NĐ100)'), q2['n'] == 2 and q2['phone'] == '', q2)

        # leaderboard offline -> demo
        pg.evaluate("S.tab='rank';draw()"); pg.wait_for_timeout(150)
        lb = pg.evaluate("document.getElementById('view').innerText")
        check(T('leaderboard offline -> hiện bảng + ghi "mô phỏng"'), 'Xếp hạng' in lb and 'mô phỏng' in lb, lb[:0])

        errs[:] = [e for e in errs if 'Response served by service worker' not in e]
        check(T('không lỗi JS (gate localhost chặn gọi máy chủ)'), not errs, errs)
        pg.close(); b.close()

shutil.rmtree(d, ignore_errors=True)
print(f'TỔNG {sum(res)} / {len(res)}')
sys.exit(0 if all(res) else 1)
