"""Phép thử Nutritie 13/10/2026 (chị Thúy, tư vấn trẻ 0–12 tháng):
 (1) bé 6–12 tháng NHẸ CÂN: ra BioA+ VÀ Baby A+ (trước chỉ ra mỗi BioA+); nút Lên đơn chỉ chứa dòng ưu tiên (không lên cả 2 dòng sữa).
 (2) bé sinh non: hiện "tuổi sau hiệu chỉnh"; điểm Z cân/tuổi tính theo TUỔI HIỆU CHỈNH (trước tính theo tuổi thật, lệch với phần chọn sản phẩm).
 (3) bé đủ tháng / cân bình thường: không đổi (Baby mặc định, không dòng hiệu chỉnh).
Dùng: python tests/test_tuoi_hieu_chinh.py [thư-mục]   (chạy trên bản cũ phải ĐỎ)"""
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
def page(pg, months, w, h, preterm='', gender='Nam', needs=None):
    pg.evaluate("""([months,w,h,preterm,gender,needs])=>{S.tab='tuvan';S.user={obj:'tre_0_12',gender:gender,senior:false,postpartum:false,preterm:preterm,hist:['Không có'],cur:''};
      S.m={months:months,w:w,h:h};S.cls=classify();S.needs=needs;S.step=4;draw();}""", [months, w, h, preterm, gender, needs or ['Tăng cân']])
    pg.wait_for_timeout(150)
    return pg.evaluate("document.getElementById('view').textContent"), pg.evaluate("document.getElementById('view').innerHTML")
with sync_playwright() as p:
    for eng in ('chromium', 'webkit'):
        b = getattr(p, eng).launch(); ctx = b.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True)
        ctx.add_init_script("localStorage.setItem('nt_pg', JSON.stringify('PG01'))")
        pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:200])); pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith('http://127.0.0.1') else r.abort())
        pg.goto(URL); pg.wait_for_function("document.getElementById('splash').classList.contains('hide')", timeout=30000); pg.wait_for_timeout(500)
        T = lambda s: f'[{eng}] ' + s
        # (1) 8 tháng, 6,2 kg -> nhẹ cân
        t, h = page(pg, '8', '6.2', '66')
        check(T('bé 8 tháng nhẹ cân: ra cả BioA+ và Baby A+'), 'Nutritie BioA+' in t and 'Nutritie Baby A+' in t, t[:300])
        check(T('thẻ thứ hai ghi "Lựa chọn khác cùng độ tuổi" (không ghi "phối hợp")'), 'Lựa chọn khác cùng độ tuổi' in t and 'Phối hợp tăng hiệu quả' not in t)
        check(T('nút Lên đơn chỉ chứa dòng ưu tiên (không lên đơn cả Bio lẫn Baby)'), "orderFromRec(['bio'])" in h and "'baby'" not in h.split('orderFromRec(')[1].split(')')[0], h.split('orderFromRec(')[1][:40] if 'orderFromRec(' in h else 'khong co nut')
        # (3) 8 tháng cân bình thường -> Baby mặc định
        t3, h3 = page(pg, '8', '8.6', '70')
        check(T('bé 8 tháng bình thường: Baby A+ mặc định, không BioA+'), 'Nutritie Baby A+' in t3 and 'Nutritie BioA+' not in t3, t3[:200])
        check(T('đủ tháng: không có dòng tuổi hiệu chỉnh'), 'tuổi sau hiệu chỉnh' not in t3)
        # (2) sinh non
        t2, h2 = page(pg, '14', '8', '60', preterm='2')
        check(T('sinh non: hiện "tuổi sau hiệu chỉnh 13,5 tháng"'), 'tuổi sau hiệu chỉnh 13,5 tháng' in t2, t2[:200])
        z = pg.evaluate("[S.cls.metric, zf(whoZ('w', corrMonths(), num('w')))]")
        check(T('điểm Z đúng bằng điểm Z theo tuổi HIỆU CHỈNH'), z[0].endswith(z[1]), z)
        pg.evaluate("S.user.preterm='8';S.m={months:'3',w:'5.2',h:'58'};S.cls=classify()")
        a = pg.evaluate("S.cls.metric"); pg.evaluate("S.user.preterm=''; S.cls=classify()"); c = pg.evaluate("S.cls.metric")
        check(T('3 tháng, sinh non 8 tuần: điểm Z KHÁC so với đủ tháng (có tính hiệu chỉnh)'), a != c, (a, c))
        check(T('không lỗi JS'), not errs, errs)
        b.close()
shutil.rmtree(d, ignore_errors=True)
print(f'TỔNG {sum(res)} / {len(res)}'); sys.exit(0 if all(res) else 1)
