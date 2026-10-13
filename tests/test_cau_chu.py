"""Phép thử Nutritie 13/10/2026 — CÁCH DIỄN ĐẠT an toàn (khách tự xem, không có Pháp chế):
 Trình khách không còn ảnh lon + lợi ích của Baby/Bio (NĐ 100), Pedia/Grow IQ/Colostrum có câu sữa mẹ chuẩn · không còn lời khách / đánh giá sao /
 giá gạch MẪU · không còn 'ngừa / phòng / tái tạo', 'cao nhất / duy nhất', 'tin dùng' trong dữ liệu sản phẩm · chân trang đúng nhóm sản phẩm
 · cảnh báo dị ứng đậu nành / dầu cá · bệnh thận + thuốc chống đông là 'cần hỏi bác sĩ' · giải thưởng ghi đúng giấy chứng nhận · MỘT câu sữa mẹ.
Dùng: python tests/test_cau_chu.py [thư-mục]   (chạy trên bản cũ phải ĐỎ)"""
import sys, os, re, shutil, tempfile, threading, functools, http.server, socketserver
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
SME = 'Sữa mẹ là thức ăn tốt nhất cho sức khỏe và sự phát triển toàn diện của trẻ nhỏ'


def check(n, ok, det=''):
    res.append(bool(ok)); print(('OK   ' if ok else 'FAIL ') + n + ('' if ok else '  ' + str(det)))


html = open(os.path.join(d, 'index.html'), encoding='utf-8').read()
html_nob64 = re.sub(r'data:image/[a-z]+;base64,[A-Za-z0-9+/=]+', 'IMG', html)   # bỏ ảnh nhúng cho khỏi nhiễu
check('MỘT câu sữa mẹ chuẩn: không còn 2 biến thể cũ ("tốt nhất cho sức khỏe trẻ sơ sinh…", "…sức khỏe của trẻ sơ sinh…")',
      'Sữa mẹ là tốt nhất cho sức khỏe trẻ sơ sinh' not in html_nob64 and 'thức ăn tốt nhất cho sức khỏe của trẻ sơ sinh' not in html_nob64)

with sync_playwright() as p:
    for eng in ('chromium', 'webkit'):
        b = getattr(p, eng).launch()
        ctx = b.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True)
        ctx.add_init_script("localStorage.setItem('nt_pg', JSON.stringify('PG01'));localStorage.setItem('nt_guided','1')")
        pg = ctx.new_page(); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)[:200]))
        pg.route('https://**', lambda r: r.abort())
        T = lambda s: f'[{eng}] ' + s
        pg.goto(URL)
        pg.wait_for_function("document.getElementById('splash').classList.contains('hide')", timeout=30000)
        pg.wait_for_timeout(500)

        # ---- Trình khách ----
        pg.evaluate("openPresent();presGo('sanpham')"); pg.wait_for_timeout(250)
        grid = pg.evaluate("""(()=>{const c=[...document.querySelectorAll('#present .pr-pcard')];return c.map(x=>({n:x.querySelector('.pr-pn').textContent,img:!!x.querySelector('img'),tl:x.querySelector('.pr-ptl').textContent}))})()""")
        hid = [g for g in grid if 'Baby' in g['n'] or 'Bio' in g['n']]
        check(T('Trình khách, lưới sản phẩm: Baby + Bio KHÔNG có ảnh lon / lợi ích (chỉ "hỏi tư vấn viên")'), len(hid) == 2 and all((not g['img']) and 'Hỏi tư vấn viên' in g['tl'] for g in hid), hid)
        check(T('Trình khách: 5 sản phẩm còn lại vẫn có ảnh'), len([g for g in grid if g['img']]) == 5, [g['n'] for g in grid if g['img']])
        for pid in ('baby', 'bio'):
            pg.evaluate("(i)=>presProduct(i)", pid); pg.wait_for_timeout(200)
            v = pg.evaluate("(()=>{const e=document.querySelector('#present .pr-body');return {t:e.textContent,img:!!e.querySelector('img'),claims:e.querySelectorAll('.pr-claims li').length}})()")
            check(T(f'Trình khách, trang {pid}: không ảnh lon, không lợi ích, có câu sữa mẹ chuẩn + hướng dẫn hỏi tư vấn viên'), (not v['img']) and v['claims'] == 0 and SME in v['t'] and 'tư vấn viên' in v['t'], v)
        for pid in ('pedia', 'growiq', 'colostrum'):
            pg.evaluate("(i)=>presProduct(i)", pid); pg.wait_for_timeout(200)
            v = pg.evaluate("document.querySelector('#present .pr-body').textContent")
            check(T(f'Trình khách, trang {pid} (từ 1 tuổi, có thể 12–24 tháng): có câu sữa mẹ chuẩn'), SME in v, v[-120:])
        pg.evaluate("presGo('camnhan')"); pg.wait_for_timeout(200)
        cn = pg.evaluate("document.querySelector('#present .pr-body').textContent")
        check(T('Trình khách, tab Cảm nhận: KHÔNG còn lời khách mẫu ("tăng 0.8kg", "Chị Lan"), không "tin dùng"'), 'tăng 0.8kg' not in cn and 'Chị Lan' not in cn and 'tin dùng' not in cn and 'Điểm bán' in cn, cn[:160])
        pg.evaluate("closePresent()")
        pg.evaluate("go('feedback')"); pg.wait_for_timeout(250)
        fb = pg.evaluate("document.getElementById('view').textContent")
        check(T('màn Cảm nhận khách hàng (PG): không lời khách mẫu; nói rõ chưa có phản hồi thật'), 'tăng 0.8kg' not in fb and 'Chưa có phản hồi thật' in fb, fb[:160])

        # ---- không còn số liệu / đánh giá / giá gạch MẪU ----
        pg.evaluate("go('sp')"); pg.wait_for_timeout(250)
        spt = pg.evaluate("[document.getElementById('view').textContent,document.querySelectorAll('#view .combadge,#view .prate').length]")
        check(T('tab Sản phẩm: không còn sao đánh giá, nhãn "Bán chạy / Ưa chuộng / Mới" mẫu'), spt[1] == 0 and not re.search(r'Bán chạy|Ưa chuộng', spt[0]), spt[1])
        pg.evaluate("openP('baby')"); pg.wait_for_timeout(250)
        sh = pg.evaluate("[document.getElementById('sheetin').textContent,document.querySelectorAll('#sheetin .pl,#sheetin .off,#sheetin .rt').length]")
        check(T('sheet sản phẩm: không giá gạch, "-% OFF", "(… đánh giá)" mẫu'), sh[1] == 0 and 'OFF' not in sh[0] and 'đánh giá' not in sh[0], sh[1])

        # ---- chân trang theo nhóm sản phẩm (theo HSCB) ----
        want = {'baby': 'Sản phẩm dinh dưỡng công thức', 'bio': 'Sản phẩm dinh dưỡng công thức', 'pedia': 'Sản phẩm dinh dưỡng,', 'growiq': 'Sản phẩm dinh dưỡng,',
                'mama': 'chế độ ăn đặc biệt', 'canxipro': 'Thực phẩm bổ sung', 'colostrum': 'Thực phẩm bổ sung'}
        bad = []
        for pid, key in want.items():
            pg.evaluate("(i)=>openP(i)", pid); pg.wait_for_timeout(150)
            dis = pg.evaluate("document.querySelector('#sheetin .dis').textContent")
            if key not in dis or 'không phải là thuốc' not in dis or ((pid in ('baby', 'bio', 'pedia', 'growiq', 'colostrum')) != (SME in dis)):
                bad.append((pid, dis))
        check(T('chân trang đúng nhóm công bố của từng SP; câu sữa mẹ chuẩn chỉ ở nhóm trẻ nhỏ; luôn "không phải là thuốc"'), not bad, bad[:2])

        # ---- dữ liệu sản phẩm: từ ngữ ----
        txt = pg.evaluate("(()=>{var o=[];PRODUCTS.forEach(function(p){o.push([p.id,(p.claims||[]).join(' | ')+' | '+(p.facts||'')+' | '+(p.tl||'')+' | '+(p.gold||'')])});return o})()")
        BAN = [r'ngừa', r'phòng thiếu máu', r'tái tạo', r'cao nhất', r'duy nhất', r'DUY NHẤT', r'Bứt phá', r'giàu kháng thể', r'tin dùng', r'QĐ 776']
        bad = [(pid, w) for pid, s in txt for w in BAN if re.search(w, s)]
        check(T('dữ liệu 7 sản phẩm: không còn "ngừa / phòng thiếu máu / tái tạo / cao nhất / duy nhất / Bứt phá / giàu kháng thể / tin dùng / QĐ 776"'), not bad, bad[:4])
        sci = pg.evaluate("Object.values(SCI).join(' ')")
        check(T('lời tư vấn khoa học (SCI): không "ngừa / tái tạo / 2–3×"'), not re.search(r'ngừa|tái tạo|2–3×', sci), re.findall(r'.{20}(?:ngừa|tái tạo|2–3×).{10}', sci)[:2])
        al = pg.evaluate("[P('growiq').facts,P('colostrum').facts]")
        check(T('Grow IQ + Colostrum: cảnh báo "chứa sữa, đậu nành, dầu cá" (theo hồ sơ công bố)'), all('đậu nành' in x and 'dầu cá' in x for x in al), al)
        tr = pg.evaluate("TRUST.map(function(x){return x[1]+' / '+x[2]}).join(' || ')")
        check(T('giải thưởng ghi đúng giấy: "Top 10 Thương hiệu Việt Nam Xuất sắc 2024", số 379/VNA-TCDNTM/2024; không "hàng nghìn cha mẹ tin dùng"'),
              'Xuất sắc 2024' in tr and '379/VNA-TCDNTM/2024' in tr and 'hàng nghìn' not in tr and 'Dinh dưỡng vàng' not in tr, tr[:200])

        # ---- tiền sử bệnh mới ----
        h = pg.evaluate("HISTS")
        check(T('tiền sử bệnh có thêm "Bệnh thận / sỏi thận" + "Đang dùng thuốc chống đông"'), 'Bệnh thận / sỏi thận' in h and 'Đang dùng thuốc chống đông' in h, h)
        for hist, key in [('Bệnh thận / sỏi thận', 'thận'), ('Đang dùng thuốc chống đông', 'chống đông')]:
            r = pg.evaluate("""([hh])=>{startTV();S.tab='tuvan';S.user.obj='adult';S.user.hist=[hh];S.m={w:60,h:165};S.needs=[];S.cls=classify();S.step=4;draw();var v=document.getElementById('view');return {t:v.textContent,order:/orderFromRec/.test(v.innerHTML)}}""", [hist])
            check(T(f'"{hist}": hiện "Cần hỏi bác sĩ", KHÔNG nút lên đơn'), 'Cần hỏi bác sĩ' in r['t'] and key in r['t'] and not r['order'], r['t'][:160])
        r = pg.evaluate("""()=>{startTV();S.tab='tuvan';S.user.obj='tre_1_10';S.user.hist=['Đang bị tiêu chảy cấp / Viêm ruột cấp'];S.m={age:4,w:16,h:100};S.cls=classify();S.step=4;draw();return document.getElementById('view').textContent}""")
        check(T('tiêu chảy cấp: không còn câu "uống sữa lúc này làm tiêu chảy nặng hơn"; nói hỏi bác sĩ về chế độ bú/ăn'), 'làm tiêu chảy nặng hơn' not in r and 'hỏi bác sĩ' in r, r[:200])
        check(T('không lỗi JS'), not errs, errs)
        b.close()

shutil.rmtree(d, ignore_errors=True)
print(f'TỔNG {sum(res)} / {len(res)}')
sys.exit(0 if all(res) else 1)
