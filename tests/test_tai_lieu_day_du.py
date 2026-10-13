"""Phép thử Nutritie 13/10/2026 — TÀI LIỆU ĐẦY ĐỦ (PDF Drive đã đổi thành ảnh từng trang) + banner Bộ sản phẩm.
 (1) mục Tài liệu: KHÔNG còn mục "Chờ cập nhật"; mọi mục có tệp đều mở được trình đọc, ảnh các trang tải được (200 + giải mã), số trang đúng bảng DOCPG;
 (2) trình đọc nhiều trang: không iframe, không link Drive, cuộn được, "Quay lại" + nút Back đóng được, chỉ tải trang khi cuộn tới (lazy);
 (3) trang 7 sản phẩm: khối "Hồ sơ & Chứng nhận" đủ, KHÔNG "Chờ cập nhật", bấm từng dòng mở ra ảnh;
 (4) banner Bộ sản phẩm có ở Trang chủ + tab Sản phẩm (tải được), KHÔNG có ở chế độ Trình khách;
 (5) số trang chuẩn một vài tài liệu (đối chiếu bản PDF gốc trên Drive: HSCB Baby 4 trang, Mama A+ đào tạo 22 trang, KQ KN chung 8 trang).
Dùng: python tests/test_tai_lieu_day_du.py [thư-mục]   (chạy trên bản cũ phải ĐỎ)"""
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
PRODS = ['baby', 'bio', 'pedia', 'growiq', 'mama', 'canxipro', 'colostrum']


def check(n, ok, det=''):
    res.append(bool(ok)); print(('OK   ' if ok else 'FAIL ') + n + ('' if ok else '  ' + str(det)))


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
        pg.wait_for_timeout(500)

        # (1) mọi trang ảnh có thật
        files = pg.evaluate("[].concat.apply([],Object.values(DOCPG))")
        ok = pg.evaluate("""async(u)=>Promise.all(u.map(x=>new Promise(r=>{const i=new Image();i.onload=()=>r(i.naturalWidth>500&&i.naturalHeight>300);i.onerror=()=>r(false);i.src=x;})))""", files)
        bad = [u for u, o in zip(files, ok) if not o]
        check(T(f'DOCPG: cả {len(files)} ảnh trang tải được và giải mã được'), len(files) >= 130 and not bad, bad[:3])
        check(T('không còn đường dẫn tài liệu nào trong TAILIEU / DOSSIER mà thiếu tệp'), pg.evaluate("""(()=>{
          const miss=[];TAILIEU.forEach(g=>g.items.forEach(it=>{if(it.f&&!fileReady(it.f))miss.push(it.f)}));
          Object.values(DOSSIER).forEach(o=>Object.values(o).forEach(f=>{if(!fileReady(f))miss.push(f)}));
          [KN_CHUNG,AWARD].concat(CERT_BOT,CERT_NUOC).forEach(f=>{if(!fileReady(f))miss.push(f)});
          window.__miss=miss;return miss.length===0})()"""), pg.evaluate("window.__miss"))

        # Tài liệu
        pg.evaluate("go('docs')"); pg.wait_for_timeout(300)
        txt = pg.evaluate("document.getElementById('view').textContent")
        check(T('mục Tài liệu: KHÔNG còn nhãn "Chờ cập nhật"'), 'Chờ cập nhật' not in txt)
        rows = pg.evaluate("[...document.querySelectorAll('#view .doc-row')].map(r=>({pend:r.classList.contains('pend'),click:!!r.getAttribute('onclick'),t:r.textContent.trim().slice(0,40)}))")
        check(T(f'mọi hàng ({len(rows)}) đều bấm được, không hàng nào mờ'), len(rows) >= 28 and all(r['click'] and not r['pend'] for r in rows), [r for r in rows if r['pend'] or not r['click']][:3])
        titles = pg.evaluate("TAILIEU.map(g=>g.items.map(i=>[g.cat,i.t,i.f||''])).flat()")
        bad_open = []
        for cat, t_, f in titles:
            pg.evaluate("([c,t])=>openDoc(c,t)", [cat, t_]); pg.wait_for_timeout(120)
            info = pg.evaluate("""(()=>{const dr=document.getElementById('docreader');return {open:dr.classList.contains('open'),imgs:dr.querySelectorAll('img.dr-img').length,iframe:!!dr.querySelector('iframe'),drive:dr.innerHTML.indexOf('drive.google')>=0,pend:dr.textContent.indexOf('chờ cập nhật')>=0||dr.textContent.indexOf('đang được cập nhật')>=0,paras:dr.querySelectorAll('.dr-p').length}})()""")
            exp = len(pg.evaluate("(f)=>DOCPG[f]||null", f) or []) if f else None
            if f:
                single = pg.evaluate("(f)=>!DOCPG[f]&&!!DRIMG[f]", f)
                want = exp if exp else (1 if single else -1)
                ok_ = info['open'] and info['imgs'] == want and not info['iframe'] and not info['drive'] and not info['pend']
            else:
                ok_ = info['open'] and not info['iframe'] and not info['drive'] and not info['pend'] and info['paras'] >= 5  # bài viết: phải có nội dung thật
            if not ok_:
                bad_open.append((t_, info))
            pg.evaluate("closeDocNow()")
        check(T(f'mở lần lượt cả {len(titles)} mục: có trình đọc, đủ ảnh trang, không iframe / Drive / "chờ"'), not bad_open, bad_open[:3])

        # (2) trình đọc nhiều trang
        pg.evaluate("openDoc('Đào tạo sản phẩm','Nutritie Mama A+ — Tài liệu đào tạo')"); pg.wait_for_timeout(400)
        n = pg.evaluate("document.querySelectorAll('#docreader img.dr-pg').length")
        check(T('Mama A+ đào tạo: 22 trang xếp dọc'), n == 22, n)
        sc = pg.evaluate("(()=>{const b=document.querySelector('#docreader .dr-body');return {sh:b.scrollHeight,ch:b.clientHeight}})()")
        check(T('vùng đọc cuộn được (nội dung cao hơn khung)'), sc['sh'] > sc['ch'] * 2, sc)
        lazy = pg.evaluate("(()=>{const im=[...document.querySelectorAll('#docreader img.dr-pg')];return im.length===22&&im.every(i=>i.loading==='lazy'&&i.decoding==='async')})()")
        check(T('ảnh trang đặt tải theo nhu cầu (loading=lazy), không kéo hết 22 trang lúc mở'), lazy)
        pg.evaluate("document.querySelector('#docreader .dr-body').scrollTop=1e6"); pg.wait_for_timeout(900)
        last = pg.evaluate("(()=>{const im=[...document.querySelectorAll('#docreader img.dr-pg')].pop();return im.complete&&im.naturalWidth>500})()")
        check(T('cuộn tới cuối: trang cuối hiện ra'), last)
        check(T('liên kết "mở" ở góc trên trỏ tới ảnh trang đầu'), 'assets/docs/tt-mama/01.jpg' in pg.evaluate("document.querySelector('#docreader .dr-open').getAttribute('href')"))
        check(T('chân trang ghi số trang + hướng dẫn cuộn / phóng to'), '22 trang' in pg.evaluate("document.querySelector('#docreader .dr-foot').textContent"))
        pg.click('#docreader .dr-back'); pg.wait_for_timeout(300)
        check(T('"Quay lại" đóng trình đọc'), not pg.evaluate("document.getElementById('docreader').classList.contains('open')"))
        pg.evaluate("openDoc('Đào tạo sản phẩm','Nutritie Mama A+ — Tài liệu đào tạo')"); pg.wait_for_timeout(250)
        pg.go_back(); pg.wait_for_timeout(300)
        check(T('nút Back của điện thoại đóng trình đọc, không thoát app'), (not pg.evaluate("document.getElementById('docreader').classList.contains('open')")) and pg.url.startswith(URL))
        # (5) số trang đối chiếu Drive
        cnt = lambda f: pg.evaluate("(f)=>(DOCPG[f]||[]).length", f)
        check(T('đối chiếu số trang với PDF gốc: HSCB Baby 4 · HSCB Bio 2 · KQ KN chung 8 · Pedia đào tạo 18'),
              (cnt('Hồ sơ công bố/HS chỉnh sửa/HSCB_Nutritie Baby A+_2022-01.pdf'), cnt('Hồ sơ công bố/HS chỉnh sửa/HSCB_Nutritie BioA+_full_2024 (1).pdf'),
               cnt('Kiểm Nghiệm/KQ KN SN Nutritie (NPP Colostrum VN).pdf'), cnt('Tài liệu Training/Nutritie Pedia A+.pdf')) == (4, 2, 8, 18))

        # (3) hồ sơ trên 7 trang sản phẩm
        bad_p = []
        for pid in PRODS:
            pg.evaluate("(i)=>openP(i)", pid); pg.wait_for_timeout(200)
            st = pg.evaluate("document.getElementById('sheetin').textContent")
            rows_ = pg.evaluate("document.querySelectorAll('#sheetin .doss-row').length")
            pend = pg.evaluate("document.querySelectorAll('#sheetin .doss-row[style*=\"opacity\"]').length")
            pg.evaluate("document.querySelector('#sheetin .doss-row').click()"); pg.wait_for_timeout(250)
            imgs = pg.evaluate("document.querySelectorAll('#docreader img.dr-img').length")
            pg.evaluate("closeDocNow();closeP()")
            if 'Chờ cập nhật' in st or rows_ < 5 or pend or imgs < 1:
                bad_p.append((pid, rows_, pend, imgs))
        check(T('7 sản phẩm: hồ sơ & chứng nhận đủ dòng, không "Chờ cập nhật", dòng đầu mở ra ảnh'), not bad_p, bad_p)

        # (4) banner
        pg.evaluate("go('home')"); pg.wait_for_timeout(300)
        bn = pg.evaluate("(()=>{const i=document.querySelector('#view .bo-ban img');return i?{w:i.naturalWidth,vis:i.getBoundingClientRect().width}:null})()")
        check(T('Trang chủ có banner Bộ sản phẩm, ảnh tải được, vừa khổ màn'), bn and bn['w'] > 500 and 300 < bn['vis'] <= 390, bn)
        pg.evaluate("document.querySelector('#view .bo-ban').click()"); pg.wait_for_timeout(250)
        check(T('bấm banner ở Trang chủ -> sang tab Sản phẩm'), pg.evaluate("S.tab") == 'sp', pg.evaluate("S.tab"))
        check(T('tab Sản phẩm có banner + đủ 7 thẻ sản phẩm'), pg.evaluate("!!document.querySelector('#view .bo-ban img')&&document.querySelectorAll('#view .grid > *').length===7"), pg.evaluate("document.querySelectorAll('#view .grid > *').length"))
        ovf = pg.evaluate("document.documentElement.scrollWidth>window.innerWidth")
        check(T('không tràn ngang'), not ovf)
        pg.evaluate("openPresent()"); pg.wait_for_timeout(400)
        check(T('chế độ Trình khách KHÔNG có banner bộ sản phẩm'), pg.evaluate("document.getElementById('present').querySelector('.bo-ban')===null&&document.getElementById('present').innerHTML.indexOf('bo-nutritie')<0"))
        pg.evaluate("closePresent()")
        check(T('không lỗi JS'), not errs, errs)
        b.close()

shutil.rmtree(d, ignore_errors=True)
print(f'TỔNG {sum(res)} / {len(res)}')
sys.exit(0 if all(res) else 1)
