"""Phép thử Nutritie giống Wintop (09/10/2026): đồng ý nêu lý do + SĐT trong hồ sơ bé + tìm bé theo SĐT.
Dùng: python test_nutritie_fb.py <thư-mục-tuvan.nutritie>   (chạy trên BẢN CŨ phải đỏ). Mọi lời gọi ra ngoài bị chặn."""
import sys, os, json, threading, http.server, socketserver, functools, shutil, tempfile
from playwright.sync_api import sync_playwright

_ANH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_anh'); os.makedirs(_ANH, exist_ok=True)
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = tempfile.mkdtemp()
for it in os.listdir(SRC):
    if it in ('.git', 'api', 'tests'):
        continue
    sp = os.path.join(SRC, it)
    (shutil.copytree if os.path.isdir(sp) else shutil.copy)(sp, os.path.join(d, it))


class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


srv = socketserver.TCPServer(('127.0.0.1', 0), functools.partial(Q, directory=d))
threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f'http://127.0.0.1:{srv.server_address[1]}/'
res = []


def check(n, ok, det=''):
    res.append(bool(ok))
    print(('OK   ' if ok else 'FAIL ') + n + ('' if ok else '  ' + str(det)))


with sync_playwright() as p:
    b = p.chromium.launch()
    for w, h in [(390, 844), (320, 640)]:
        ctx = b.new_context(viewport={'width': w, 'height': h}, is_mobile=True, has_touch=True)
        ctx.add_init_script("localStorage.setItem('nt_pg', JSON.stringify('PG01'))")
        pg = ctx.new_page()
        errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)[:200]))
        pg.route('https://**', lambda r: r.abort())
        T = lambda s: f'[{w}x{h}] ' + s
        pg.goto(URL)
        pg.wait_for_function("document.getElementById('splash').classList.contains('hide')", timeout=15000)
        pg.wait_for_timeout(600)
        pg.evaluate("localStorage.removeItem('nt_babies');localStorage.removeItem('nt_measures');S.tab='growth';draw()")
        pg.wait_for_timeout(300)
        check(T('chưa có bé nào: vẫn có ô tìm theo SĐT'), pg.evaluate("!!document.getElementById('gq')"))
        # --- form hồ sơ bé: câu đồng ý nêu lý do ---
        pg.evaluate("S.growth.addingBaby=true;S.bf={};draw()")
        pg.wait_for_timeout(200)
        txt = pg.evaluate("document.getElementById('view').innerText")
        check(T('form hồ sơ bé có câu đồng ý nêu lý do theo dõi biểu đồ + đánh giá hiệu quả dinh dưỡng'),
              'theo dõi biểu đồ tăng trưởng' in txt and 'đánh giá hiệu quả của tình trạng dinh dưỡng' in txt, txt[:400])
        check(T('câu đồng ý có thêm mục đích "chăm sóc và nhắc lịch cân đo" (khách chốt 10/10)'), 'chăm sóc và nhắc lịch cân đo' in txt)
        check(T('câu đồng ý KHÔNG hứa "ưu đãi / khuyến mại" (NĐ 100 với sữa trẻ nhỏ)'), 'ưu đãi' not in txt.split('Anh/chị đồng ý')[0][-420:] and 'khuyến mại' not in txt.split('Anh/chị đồng ý')[0][-420:])
        check(T('mã câu đồng ý nt-v4-2026-10-10'), pg.evaluate("CONSENT_V") == 'nt-v4-2026-10-10')
        check(T('chưa chọn đồng ý: ô SĐT chưa hiện'), not pg.evaluate("!!document.getElementById('bf_phone')"))

        def fill_baby(name, dob, gender='Trai'):
            pg.evaluate(f"S.bf.ten={json.dumps(name)};S.bf.ngaySinh={json.dumps(dob)};S.bf.gioiTinh={json.dumps(gender)}")

        def save():
            pg.evaluate("submitBaby()")
            pg.wait_for_timeout(150)

        # chưa hỏi khách -> không lưu
        fill_baby('In', '2021-01-10')
        save()
        check(T('chưa hỏi khách đồng ý: KHÔNG lưu bé'), pg.evaluate("babies().length") == 0, pg.evaluate("babies().length"))
        # chọn đồng ý bằng bấm thật
        pg.click('.chip:text-is("Khách đồng ý")'); pg.wait_for_timeout(200)
        check(T('bấm "Khách đồng ý": ô SĐT hiện ra'), pg.evaluate("!!document.getElementById('bf_phone')"))
        check(T('bấm chọn không làm mất tên bé đã nhập'), pg.evaluate("S.bf.ten") == 'In')
        pg.fill('#bf_phone', '12345'); save()
        check(T('đồng ý nhưng SĐT sai: KHÔNG lưu'), pg.evaluate("babies().length") == 0)
        pg.fill('#bf_phone', '0912 345 678'); save()
        bb = pg.evaluate("babies()")
        check(T('SĐT đúng: lưu bé kèm SĐT chuẩn hoá + mã câu đồng ý + giờ đồng ý'),
              len(bb) == 1 and bb[0].get('phone') == '0912345678' and bb[0].get('cv') == 'nt-v4-2026-10-10' and bb[0].get('ca'), bb)
        # bé thứ 2 cùng SĐT
        pg.evaluate("S.growth.addingBaby=true;S.bf={};draw()"); fill_baby('Na', '2024-02-20', 'Gái')
        pg.click('.chip:text-is("Khách đồng ý")'); pg.fill('#bf_phone', '0912345678'); save()
        # bé thứ 3 khác SĐT, rồi bé thứ 4 KHÔNG đồng ý
        pg.evaluate("S.growth.addingBaby=true;S.bf={};draw()"); fill_baby('Tí', '2023-05-05')
        pg.click('.chip:text-is("Khách đồng ý")'); pg.fill('#bf_phone', '0987654321'); save()
        pg.evaluate("S.growth.addingBaby=true;S.bf={};draw()"); fill_baby('Bo', '2022-03-03')
        pg.click('.chip:text-is("Khách không đồng ý")'); pg.wait_for_timeout(150)
        check(T('"Khách không đồng ý": không có ô SĐT, có lời giải thích'), not pg.evaluate("!!document.getElementById('bf_phone')") and 'Không lưu SĐT' in pg.evaluate("document.getElementById('view').innerText"))
        save()
        bb = pg.evaluate("babies()")
        bo = [x for x in bb if x['ten'] == 'Bo']
        check(T('không đồng ý: bé vẫn lưu nhưng KHÔNG có SĐT'), len(bb) == 4 and bo and 'phone' not in bo[0] and 'cv' not in bo[0], bb)
        # --- đo thử cho 2 bé để có biểu đồ ---
        ids = {x['ten']: x['id'] for x in bb}
        pg.evaluate("""(ids)=>{saveMeasures([{id:'M1',babyId:ids['In'],ngayDo:'2026-09-01',canNang:21.5,chieuCao:116},{id:'M2',babyId:ids['Na'],ngayDo:'2026-09-01',canNang:12.8,chieuCao:90}]);S.growth.baby=ids['Tí'];draw();}""", ids)
        pg.wait_for_timeout(250)
        # --- tìm ---
        pg.fill('#gq', '12345'); pg.click('#gq ~ button'); pg.wait_for_timeout(150)
        check(T('SĐT sai: báo rõ'), 'chưa đúng' in pg.evaluate("document.getElementById('gqres').innerText"))
        pg.fill('#gq', '0912 345 678'); pg.click('#gq ~ button'); pg.wait_for_timeout(200)
        chips = pg.evaluate("[...document.querySelectorAll('#gqres .gchip')].map(e=>e.innerText.trim())")
        check(T('1 SĐT ra đúng 2 bé (In, Na), không lẫn bé SĐT khác / bé không SĐT'), len(chips) == 2 and any(c.startswith('In') for c in chips) and any(c.startswith('Na') for c in chips) and not any(c.startswith('Tí') or c.startswith('Bo') for c in chips), chips)
        check(T('gõ và tìm KHÔNG làm ô nhập mất nội dung'), pg.input_value('#gq') == '0912 345 678')
        check(T('nói rõ "chỉ tìm trên máy này"'), 'Chỉ tìm trên máy này' in pg.evaluate("document.getElementById('gqres').innerText"))
        pg.click('#gqres .gchip:has-text("In")'); pg.wait_for_timeout(400)
        cur = pg.evaluate("babyById(S.growth.baby).ten")
        check(T('chọn bé "In" -> hiện biểu đồ của In'), cur == 'In' and pg.evaluate("!!document.querySelector('svg.gchart')"), cur)
        check(T('sau khi chọn: ô tìm giữ SĐT, chip In được tô sáng'), pg.input_value('#gq') == '0912 345 678' and pg.evaluate("[...document.querySelectorAll('#gqres .gchip.on')].map(e=>e.innerText).join('').includes('In')"))
        gtxt = pg.evaluate("document.getElementById('view').innerText")
        check(T('nhận định chỉ so với chuẩn WHO, không có "bạn cùng tuổi / hầu hết"'), 'chuẩn WHO' in gtxt and 'bạn cùng tuổi' not in gtxt and 'hầu hết' not in gtxt and 'trẻ cùng tuổi' not in gtxt)
        pg.fill('#gq', '0399999999'); pg.click('#gq ~ button'); pg.wait_for_timeout(150)
        check(T('SĐT hợp lệ nhưng chưa có bé: nói "chưa thấy bé nào", không báo lỗi'), 'Chưa thấy bé nào' in pg.evaluate("document.getElementById('gqres').innerText"))
        # --- hồ sơ bé cũ (chưa có SĐT): sửa mà chưa chọn đồng ý thì giữ nguyên; thêm SĐT thì cần đồng ý ---
        pg.evaluate("saveBabies(babies().concat([{id:'BOLD',ten:'Cũ',ngaySinh:'2020-05-05',gioiTinh:'Trai'}]));editBaby('BOLD')")
        pg.wait_for_timeout(150)
        pg.evaluate("S.bf.ten='Cũ sửa'"); save()
        old = pg.evaluate("babyById('BOLD')")
        check(T('sửa hồ sơ bé cũ khi chưa chọn đồng ý: lưu được, vẫn không SĐT'), old['ten'] == 'Cũ sửa' and 'phone' not in old, old)
        pg.evaluate("editBaby('BOLD')"); pg.wait_for_timeout(100); pg.click('.chip:text-is("Khách đồng ý")'); pg.fill('#bf_phone', '0912345678'); save()
        check(T('thêm SĐT cho bé cũ (có đồng ý): tìm ra đủ 3 bé của số đó'), pg.evaluate("kidsOfPhone('0912345678').length") == 3)
        pg.evaluate("editBaby('BOLD')"); pg.wait_for_timeout(100); pg.click('.chip:text-is("Khách không đồng ý")'); save()
        check(T('đổi sang không đồng ý khi sửa: SĐT bị xoá khỏi hồ sơ'), 'phone' not in pg.evaluate("babyById('BOLD')") and pg.evaluate("kidsOfPhone('0912345678').length") == 2)
        sw = pg.evaluate("document.documentElement.scrollWidth")
        check(T('không tràn ngang'), sw <= w, sw)
        check(T('không lỗi JS'), not errs, errs)
        if w == 390:
            pg.evaluate("S.growth.addingBaby=true;S.bf={ten:'X',consent:true,phone:'0912345678'};draw();window.scrollTo(0,0)")
            pg.wait_for_timeout(250); pg.screenshot(path=os.path.join(_ANH, 'fb_nut_form.png'))
            pg.evaluate("S.growth.addingBaby=false;draw()"); pg.wait_for_timeout(200); pg.screenshot(path=os.path.join(_ANH, 'fb_nut_search.png'))
        ctx.close()
    b.close()
print('TỔNG', sum(res), '/', len(res))
srv.shutdown()
sys.exit(0 if all(res) else 1)
