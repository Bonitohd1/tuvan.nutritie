"""Phép thử Nutritie 13/10/2026 (phản hồi chị Thúy): 3 nhóm.
 1) Mục Tài liệu: tệp chưa có thì "Chờ cập nhật" (không ra trang 404, không dẫn ra Drive). Nhóm "Kỹ năng chốt sale" ẩn khi chưa có nội dung; từ 13/10 có 7 ảnh -> hiện (xem test_chot_sale.py).
 2) Nút Back của điện thoại/Zalo: lùi một màn trong app thay vì THOÁT app; nút "Quay lại" của trình đọc tài liệu đóng được.
 3) Ca chống chỉ định: vẫn phân tích chỉ số (thước đo BMI) + nói khi nào tư vấn tiếp; KHÔNG có nút lên đơn khi đang chống chỉ định.
Dùng: python tests/test_tai_lieu_back_chong_chi_dinh.py [thư-mục-tuvan.nutritie]   (chạy trên bản cũ phải ĐỎ)
"""
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


def result_page(pg, hist, obj='tre_1_10', m=None):
    m = m or {'age': 6, 'w': 14, 'h': 105}      # cân nhẹ so với tuổi -> chỉ số "thiếu"
    pg.evaluate("""([obj,m,hist])=>{S.tab='tuvan';S.user={obj:obj,gender:'Nam',senior:false,postpartum:false,preterm:'',hist:hist,cur:''};
      S.m=m;S.cls=classify();S.needs=['Tăng cân'];S.step=4;draw();}""", [obj, m, hist])
    pg.wait_for_timeout(200)
    return pg.evaluate("document.getElementById('view').textContent"), pg.evaluate("document.getElementById('view').innerHTML")


with sync_playwright() as p:
    for eng in ('chromium', 'webkit'):
        b = getattr(p, eng).launch()
        ctx = b.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True)
        ctx.add_init_script("localStorage.setItem('nt_pg', JSON.stringify('PG01'))")
        pg = ctx.new_page(); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)[:200]))
        pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith('http://127.0.0.1') else r.abort())
        T = lambda s: f'[{eng}] ' + s
        pg.goto(URL)
        pg.wait_for_function("document.getElementById('splash').classList.contains('hide')", timeout=30000)
        pg.wait_for_timeout(600)

        # ---------- 1. TÀI LIỆU ----------
        pg.evaluate("go('docs')"); pg.wait_for_timeout(200)
        # 13/10 chiều: mọi PDF đã vào kho (DOCPG) nên không còn mục "chờ" thật -> MÔ PHỎNG tệp chưa có bằng cách bỏ DOCPG, để vẫn canh cơ chế "không 404"
        pg.evaluate("Object.keys(DOCPG).forEach(k=>delete DOCPG[k]);draw()"); pg.wait_for_timeout(200)
        txt = pg.evaluate("document.getElementById('view').textContent")
        check(T('mục Tài liệu: có nhãn "Chờ cập nhật" cho tệp chưa có'), 'Chờ cập nhật' in txt)
        check(T('nhóm "Kỹ năng chốt sale" hiện (đã có 7 ảnh hướng dẫn)'), 'Kỹ năng chốt sale' in txt, txt[:200])
        n_click = pg.evaluate("[...document.querySelectorAll('#view .doc-row')].filter(r=>r.getAttribute('onclick')).length")
        n_pend = pg.evaluate("document.querySelectorAll('#view .doc-row.pend').length")
        check(T('hàng chưa có tệp KHÔNG bấm được (không onclick)'), n_pend >= 10 and pg.evaluate("[...document.querySelectorAll('#view .doc-row.pend')].every(r=>!r.getAttribute('onclick'))"), n_pend)
        check(T('chỉ còn mục có nội dung thật bấm mở được (2 bài kiến thức + 2 ảnh Aiwado + 7 ảnh chốt sale = 11; bài NĐ100 đã bỏ theo khách 14/10)'), n_click == 11, n_click)
        pg.evaluate("document.querySelector('#view .doc-row:not(.pend)').click()"); pg.wait_for_timeout(250)
        rd = pg.evaluate("document.getElementById('docreader').innerHTML")
        check(T('trình đọc bài viết mở ra'), pg.evaluate("document.getElementById('docreader').classList.contains('open')"))
        check(T('trình đọc KHÔNG có link Drive và KHÔNG có iframe (404)'), 'drive.google' not in rd and '<iframe' not in rd, rd[:200])
        check(T('trình đọc bài viết có NỘI DUNG THẬT (không còn "đang được cập nhật")'), 'Z-score' in rd and 'đang được cập nhật' not in rd, rd[:120])
        pg.click('#docreader .dr-back'); pg.wait_for_timeout(300)
        check(T('nút "Quay lại" đóng được trình đọc'), not pg.evaluate("document.getElementById('docreader').classList.contains('open')"))
        check(T('sau khi đóng vẫn ở mục Tài liệu (không văng app)'), pg.evaluate("S.tab")=='docs')

        # ---------- 2. NÚT BACK ----------
        pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:200])); pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith('http://127.0.0.1') else r.abort())
        pg.goto(URL); pg.wait_for_function("document.getElementById('splash').classList.contains('hide')", timeout=30000); pg.wait_for_timeout(500)
        pg.evaluate("go('docs')"); pg.wait_for_timeout(150)
        pg.evaluate("document.querySelector('#view .doc-row:not(.pend)').click()"); pg.wait_for_timeout(200)
        pg.go_back(); pg.wait_for_timeout(300)
        check(T('Back khi đang đọc tài liệu: đóng trình đọc, KHÔNG thoát app'), (not pg.evaluate("document.getElementById('docreader').classList.contains('open')")) and pg.url.startswith(URL) and pg.evaluate("S.tab")=='docs', pg.url)
        pg.go_back(); pg.wait_for_timeout(300)
        check(T('Back lần nữa: về Trang chủ (vẫn trong app)'), pg.url.startswith(URL) and pg.evaluate("S.tab")=='home', (pg.url, pg.evaluate("S.tab")))
        pg.evaluate("go('tuvan')"); pg.evaluate("go('sp')"); pg.wait_for_timeout(150)
        pg.go_back(); pg.wait_for_timeout(250)
        check(T('Tư vấn -> Sản phẩm rồi Back: về Tư vấn'), pg.evaluate("S.tab")=='tuvan', pg.evaluate("S.tab"))

        # ---------- 3. CHỐNG CHỈ ĐỊNH ----------
        t1, h1 = result_page(pg, ['Viêm loét dạ dày - tá tràng'])
        check(T('viêm loét: vẫn có cảnh báo chống chỉ định'), 'Chống chỉ định' in t1)
        check(T('viêm loét: VẪN phân tích chỉ số (thước đo tăng trưởng)'), 'Thước đo tăng trưởng' in t1, t1[:200])
        check(T('viêm loét: có mục "Khi nào tư vấn tiếp" + sản phẩm chỉ để tham khảo sau khi hết bệnh'), 'Khi nào tư vấn tiếp' in t1 and 'SAU khi hết bệnh' in t1)
        check(T('viêm loét: KHÔNG có nút lên đơn / xem chi tiết sản phẩm'), 'orderFromRec' not in h1 and 'Lên đơn sản phẩm gợi ý' not in t1)
        t2, h2 = result_page(pg, ['Dị ứng đạm bò'])
        check(T('dị ứng đạm bò: có thước đo + nói tình trạng không tự hết, KHÔNG gợi ý sản phẩm'), 'Thước đo tăng trưởng' in t2 and 'không tự hết' in t2 and 'SAU khi hết bệnh' not in t2 and 'orderFromRec' not in h2)
        t3, h3 = result_page(pg, ['Đang bị tiêu chảy cấp / Viêm ruột cấp'], obj='tre_0_12', m={'months': 8, 'w': 7.5, 'h': 70})
        check(T('tiêu chảy cấp trẻ nhỏ: gợi ý tham khảo kèm khuyến cáo bắt buộc "Sữa mẹ là thức ăn tốt nhất"'), 'SAU khi hết bệnh' in t3 and 'Sữa mẹ là thức ăn tốt nhất' in t3)
        t4, h4 = result_page(pg, ['Không có'])
        check(T('không chống chỉ định: vẫn có nút Lên đơn (không hồi quy)'), 'orderFromRec' in h4 and 'Thước đo tăng trưởng' in t4)
        check(T('không lỗi JS'), not errs, errs)
        b.close()

shutil.rmtree(d, ignore_errors=True)
print(f'TỔNG {sum(res)} / {len(res)}')
sys.exit(0 if all(res) else 1)
