"""Phép thử Nutritie 13/10/2026 — biểu đồ tăng trưởng NGAY TRONG buổi tư vấn (chị Thúy: "chưa có biểu đồ tăng trưởng theo SĐT + tên người dùng như Wintop").
Đi đúng đường người dùng: bước 1 (tên bé, ngày sinh, hỏi đồng ý, SĐT) -> bước 2 (số đo) -> kết quả: thước đo BMI -> BIỂU ĐỒ -> tư vấn khoa học -> sản phẩm.
Kiểm: hồ sơ bé + số đo được LƯU (có SĐT + dấu đồng ý), vẽ lại màn kết quả KHÔNG nhân đôi, tìm được theo SĐT, ca chống chỉ định vẫn có biểu đồ,
không có ngày sinh thì không lưu gì, chưa hỏi đồng ý thì chặn. Dùng: python tests/test_bieu_do_tu_van.py [thư-mục]  (bản cũ phải ĐỎ)"""
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


ISO = "(a)=>{const d=new Date();d.setFullYear(d.getFullYear()-a[0]);d.setMonth(d.getMonth()-a[1]);return d.toISOString().slice(0,10)}"


def txt(pg):
    return pg.evaluate("document.getElementById('view').textContent")


def store(pg):
    return pg.evaluate("({b:JSON.parse(localStorage.getItem(BB_KEY)||'[]'),m:JSON.parse(localStorage.getItem(MEA_KEY)||'[]')})")


def fresh(ctx, errs):
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errs.append(str(e)[:200]))
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith('http://127.0.0.1') else r.abort())
    pg.goto(URL)
    pg.wait_for_function("document.getElementById('splash').classList.contains('hide')", timeout=30000)
    pg.wait_for_timeout(500)
    pg.evaluate("localStorage.removeItem(BB_KEY);localStorage.removeItem(MEA_KEY);startTV()")
    pg.wait_for_timeout(200)
    return pg


def step1(pg, obj, dob, name='', consent=None, phone='', hist=None):
    pg.evaluate("go('tuvan')")
    pg.wait_for_timeout(150)
    pg.evaluate(f"setObj('{obj}')")
    pg.evaluate("if(!S.user.gender)S.user.gender='Nam';draw()")  # 15/10: bắt chọn giới tính cho trẻ
    pg.wait_for_timeout(100)
    if name:
        pg.fill("input[placeholder='VD: Bé Bo']", name)
    if dob:
        pg.evaluate("(v)=>setKidDob(v)", dob)
        pg.wait_for_timeout(100)
    if consent is True:
        pg.click(".chip:text-is('Khách đồng ý')")
        pg.wait_for_timeout(100)
    if consent is False:
        pg.click(".chip:text-is('Khách không đồng ý')")
        pg.wait_for_timeout(100)
    if phone:
        pg.fill('#kid_phone', phone)
    if hist:
        pg.evaluate("(h)=>{S.user.hist=h}", hist)


def goto_result(pg, w, h):
    pg.click("button:has-text('Tiếp tục')")
    pg.wait_for_timeout(200)
    if pg.evaluate("S.step") != 2:
        return False
    pg.evaluate("([w,h])=>{S.m.w=String(w);S.m.h=String(h)}", [w, h])
    pg.evaluate("next2()")
    pg.wait_for_timeout(150)
    pg.evaluate("S.needs=['Tăng cân'];S.step=4;draw()")
    pg.wait_for_timeout(250)
    return True


with sync_playwright() as p:
    for eng in ('chromium', 'webkit'):
        b = getattr(p, eng).launch()
        ctx = b.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True)
        ctx.add_init_script("localStorage.setItem('nt_pg', JSON.stringify('PG01'))")
        errs = []
        T = lambda s: f'[{eng}] ' + s

        # ===== A. đồng ý + SĐT =====
        pg = fresh(ctx, errs)
        dob = pg.evaluate(ISO, [7, 0])
        step1(pg, 'tre_1_10', dob, name='Bo', consent=True, phone='0912345678')
        s1 = txt(pg)
        check(T('bước 1 có Tên bé + Ngày sinh + câu đồng ý + SĐT'), 'Tên bé' in s1 and 'Ngày sinh của bé' in s1 and 'Khách đồng ý' in s1 and pg.evaluate("!!document.getElementById('kid_phone')"))
        age = pg.evaluate("parseFloat(S.m.age)")
        check(T('có ngày sinh: tuổi tự tính (~7 tuổi), không bắt gõ lại'), 6.9 <= age <= 7.1, age)
        check(T('qua bước 1 -> bước 2'), goto_result(pg, 15, 112))
        t = txt(pg)
        check(T('kết quả có thẻ "Tăng trưởng của Bo" + biểu đồ (svg)'), 'Tăng trưởng của Bo' in t and pg.evaluate("!!document.querySelector('#view svg')"), t[:200])
        a, g, s = t.find('Thước đo tăng trưởng'), t.find('Tăng trưởng của Bo'), t.find('TƯ VẤN KHOA HỌC')
        check(T('thứ tự: Thước đo (BMI) -> Biểu đồ tăng trưởng -> Tư vấn khoa học'), -1 < a < g < s, (a, g, s))
        st = store(pg)
        check(T('đã LƯU 1 hồ sơ bé: có SĐT + dấu đồng ý + tên + ngày sinh'),
              len(st['b']) == 1 and st['b'][0].get('phone') == '0912345678' and st['b'][0].get('cv') and st['b'][0].get('ten') == 'Bo' and st['b'][0].get('ngaySinh') == dob, st['b'])
        check(T('đã LƯU số đo hôm nay (15kg, 112cm)'), len(st['m']) == 1 and st['m'][0]['canNang'] == 15 and st['m'][0]['chieuCao'] == 112, st['m'])
        pg.evaluate("draw();draw();draw()")
        pg.wait_for_timeout(200)
        st2 = store(pg)
        check(T('vẽ lại màn kết quả nhiều lần KHÔNG nhân đôi hồ sơ / số đo'), len(st2['b']) == 1 and len(st2['m']) == 1, (len(st2['b']), len(st2['m'])))
        check(T('tìm được bé theo SĐT (như Wintop)'), pg.evaluate("kidsOfPhone('0912345678').length") == 1)
        # tư vấn lần 2 cùng ngày, cân khác -> cập nhật số đo, không tạo bé mới
        pg.evaluate("startTV()")
        pg.wait_for_timeout(150)
        step1(pg, 'tre_1_10', dob, name='Bo', consent=True, phone='0912 345 678')
        goto_result(pg, 15.6, 113)
        st3 = store(pg)
        check(T('tư vấn lần 2 (cùng SĐT + tên): vẫn 1 bé, số đo hôm nay được cập nhật'), len(st3['b']) == 1 and len(st3['m']) == 1 and st3['m'][0]['canNang'] == 15.6, st3)

        # ===== B. không đồng ý =====
        pg = fresh(ctx, errs)
        step1(pg, 'tre_1_10', dob, name='Na', consent=False)
        goto_result(pg, 15, 112)
        st = store(pg)
        check(T('không đồng ý: vẫn vẽ biểu đồ, hồ sơ lưu trên máy KHÔNG có SĐT'),
              'Tăng trưởng của Na' in txt(pg) and len(st['b']) == 1 and not st['b'][0].get('phone') and not st['b'][0].get('cv'), st['b'])

        # ===== C. chưa hỏi đồng ý -> chặn; SĐT sai -> chặn =====
        pg = fresh(ctx, errs)
        step1(pg, 'tre_1_10', dob, name='Mi')
        pg.click("button:has-text('Tiếp tục')")
        pg.wait_for_timeout(200)
        check(T('đã nhập ngày sinh mà chưa hỏi đồng ý: không cho qua bước 1'), pg.evaluate("S.step") == 1)
        pg.click(".chip:text-is('Khách đồng ý')")
        pg.fill('#kid_phone', '123')
        pg.click("button:has-text('Tiếp tục')")
        pg.wait_for_timeout(200)
        check(T('đồng ý nhưng SĐT sai: không cho qua'), pg.evaluate("S.step") == 1)

        # ===== D. không có ngày sinh =====
        pg = fresh(ctx, errs)
        step1(pg, 'tre_1_10', '')
        pg.evaluate("S.user.hist=['Không có']")
        pg.click("button:has-text('Tiếp tục')")
        pg.wait_for_timeout(200)
        pg.evaluate("S.m.age='5';S.m.w='16';S.m.h='105'")
        pg.evaluate("next2()")
        pg.evaluate("S.needs=['Tăng cân'];S.step=4;draw()")
        pg.wait_for_timeout(250)
        st = store(pg)
        check(T('không ngày sinh: KHÔNG lưu hồ sơ nào, có lời nhắc nhập ngày sinh'), len(st['b']) == 0 and len(st['m']) == 0 and 'không có ngày sinh' in txt(pg))

        # ===== E. ca chống chỉ định vẫn có biểu đồ =====
        pg = fresh(ctx, errs)
        step1(pg, 'tre_1_10', dob, name='Ti', consent=True, phone='0987654321', hist=['Viêm loét dạ dày - tá tràng'])
        goto_result(pg, 15, 112)
        t = txt(pg)
        check(T('chống chỉ định: vẫn có thước đo + BIỂU ĐỒ + "Khi nào tư vấn tiếp"'),
              'Chống chỉ định' in t and 'Thước đo tăng trưởng' in t and 'Tăng trưởng của Ti' in t and 'Khi nào tư vấn tiếp' in t)

        # ===== F. bé 0-12 tháng =====
        pg = fresh(ctx, errs)
        dob8 = pg.evaluate(ISO, [0, 8])
        step1(pg, 'tre_0_12', dob8, name='Be', consent=True, phone='0911222333')
        goto_result(pg, 7.9, 69)
        t = txt(pg)
        st = store(pg)
        mo = pg.evaluate("parseFloat(S.m.months)")
        check(T('bé 8 tháng: có biểu đồ + hồ sơ, tuổi tự tính ~8 tháng'), 'Tăng trưởng của Be' in t and len(st['b']) == 1 and 7.5 <= mo <= 8.5, mo)
        check(T('không lỗi JS'), not errs, errs)
        b.close()

shutil.rmtree(d, ignore_errors=True)
print(f'TỔNG {sum(res)} / {len(res)}')
sys.exit(0 if all(res) else 1)
