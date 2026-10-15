"""Phep thu Nutritie 15/10/2026 — logic nho A4 + A5.
 A4: sinh non HIEU CHINH tuoi cho nhom 1-10 khi be 12-24 thang (truoc: chi nhom 0-12);
     chuyen doi tuong 0-12 -> 1-10 GIU so tuan sinh non; o 'sinh non' hien o ca nhom 1-10.
 A5: soi them CHIEU CAO/TUOI (tha'p coi) — canh bao khi chieu cao thap du can nang dat.
Dung: python tests/test_logic_a45_15_10.py [thu-muc]   (ban cu phai DO: dat REV=1)
"""
import sys, os, shutil, tempfile, threading, functools, http.server, socketserver
from playwright.sync_api import sync_playwright

SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = tempfile.mkdtemp()
for it in os.listdir(SRC):
    if it in ('.git', 'api', 'tests', 'node_modules'): continue
    sp = os.path.join(SRC, it)
    (shutil.copytree if os.path.isdir(sp) else shutil.copy)(sp, os.path.join(d, it))
# Kiem nguoc: thay index.html bang ban truoc khi va
if os.environ.get('REV') == '1':
    old = os.path.join(os.environ.get('TEMP', '/tmp'), 'index_before_a45.html')
    shutil.copy(old, os.path.join(d, 'index.html'))
    print('*** REV: dung ban CU', old)


class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass


srv = socketserver.TCPServer(('127.0.0.1', 0), functools.partial(Q, directory=d))
threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f'http://127.0.0.1:{srv.server_address[1]}/'
res = []


def check(n, ok, det=''):
    res.append(bool(ok)); print(('OK   ' if ok else 'FAIL ') + n + ('' if ok else '  ' + str(det)[:220]))


def result(pg, obj, m, gender='Nam', extra=None):
    # Tra ve {text, cls label, stunt, hfaZ, pct}
    return pg.evaluate("""([obj,m,g,ex])=>{startTV();S.tab='tuvan';S.user.obj=obj;S.user.gender=g;S.user.hist=['Không có'];
      if(ex)Object.assign(S.user,ex);S.m=m;S.cls=classify();S.step=4;draw();
      return {t:document.getElementById('view').innerText.replace(/\\s+/g,' '),
              label:S.cls&&S.cls.label,stunt:!!(S.cls&&S.cls.stunt),hfaZ:S.cls&&S.cls.hfaZ,pct:S.cls&&S.cls.pct};}""",
                       [obj, m, gender, extra])


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

        # ---- A4.1: setObj GIU preterm khi 0-12 -> 1-10, nhung XOA khi sang nguoi lon
        keep = pg.evaluate("""(()=>{startTV();S.user.obj='tre_0_12';S.user.preterm='8';setObj('tre_1_10');var a=S.user.preterm;
          setObj('adult');var bb=S.user.preterm;return {a:a,b:bb};})()""")
        check(T('A4: doi 0-12 -> 1-10 GIU so tuan sinh non (8); sang nguoi lon thi XOA'), keep['a'] == '8' and keep['b'] == '', keep)

        # ---- A4.2: o "sinh non" hien o buoc 1 cho nhom 1-10
        has_pt = pg.evaluate("""(()=>{startTV();S.tab='tuvan';S.user.obj='tre_1_10';S.user.gender='Nam';S.step=1;draw();
          return /Số TUẦN SINH SỚM/.test(document.getElementById('view').innerText);})()""")
        check(T('A4: o nhap "sinh non" HIEN cho nhom 1-10 o buoc chon doi tuong'), has_pt)

        # ---- A4.3: be 1-10, 18 thang, sinh non 8 tuan -> tuoi hieu chinh tre hon -> Z cao hon (cung can nang)
        r_no = result(pg, 'tre_1_10', {'age': 1.5, 'w': 9.0, 'h': 80}, extra={'preterm': ''})
        r_pt = result(pg, 'tre_1_10', {'age': 1.5, 'w': 9.0, 'h': 80}, extra={'preterm': '8'})
        check(T('A4: be 18 thang sinh non 8 tuan -> Z can/tuoi CAO hon so voi khong hieu chinh (pct lon hon)'),
              r_pt['pct'] is not None and r_no['pct'] is not None and r_pt['pct'] > r_no['pct'], (r_no['pct'], r_pt['pct']))

        # ---- A5.1: nhom 1-10 (2 tuoi) CAN DAT nhung CHIEU CAO THAP -> canh bao thap coi
        r = result(pg, 'tre_1_10', {'age': 2, 'w': 12, 'h': 80}, extra={'preterm': ''})
        check(T('A5: be 2 tuoi chieu cao 80cm (thap) + can dat -> co co thap coi + chu "thấp còi" o man ket qua'),
              r['stunt'] and r['hfaZ'] is not None and r['hfaZ'] < -2 and 'thấp còi' in r['t'], (r['stunt'], r['hfaZ'], 'thấp còi' in r['t']))

        # ---- A5.2: chieu cao BINH THUONG -> KHONG canh bao thap coi
        r2 = result(pg, 'tre_1_10', {'age': 2, 'w': 12, 'h': 88}, extra={'preterm': ''})
        check(T('A5: be 2 tuoi chieu cao 88cm (dat) -> KHONG co thap coi'), (not r2['stunt']) and 'thấp còi' not in r2['t'], (r2['stunt'], r2['hfaZ']))

        # ---- A5.3: nhom 0-12 cung soi thap coi (10 thang, cao thap)
        r3 = result(pg, 'tre_0_12', {'months': 10, 'w': 8.5, 'h': 64}, extra={'preterm': ''})
        check(T('A5: be 10 thang chieu cao 64cm (thap) -> co thap coi o nhom 0-12'), r3['stunt'] and r3['hfaZ'] is not None and r3['hfaZ'] < -2, (r3['stunt'], r3['hfaZ']))
        r3b = result(pg, 'tre_0_12', {'months': 10, 'w': 8.5, 'h': 74}, extra={'preterm': ''})
        check(T('A5: be 10 thang chieu cao 74cm (dat) -> KHONG thap coi'), not r3b['stunt'], (r3b['stunt'], r3b['hfaZ']))

        # ---- Khong hoi quy: nhom 1-10 >=5 tuoi (BMI) van chay, khong vo
        r4 = result(pg, 'tre_1_10', {'age': 6, 'w': 20, 'h': 115})
        check(T('khong hoi quy: be 6 tuoi (BMI) van ra nhan'), bool(r4['label']), r4['label'])

        errs[:] = [e for e in errs if 'Response served by service worker' not in e]
        check(T('khong loi JS'), not errs, errs)
        pg.close(); b.close()

shutil.rmtree(d, ignore_errors=True)
print(f'TỔNG {sum(res)} / {len(res)}')
sys.exit(0 if all(res) else 1)
