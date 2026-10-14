"""Phép thử Nutritie 14/10/2026 — các mục phản hồi của khách (file "Check lỗi", 3 tab 19/9 · 23/9 · 13/10) mà bản trước CHƯA sửa:
 · Lên đơn: ảnh lon trong giỏ + thêm nhanh · ô SĐT khách KHÔNG bị nút "Chốt đơn" đè lên (bấm được, gõ được)
 · Trình khách: ảnh sản phẩm không bị icon (emoji) đè
 · tên điểm bán "Bi's Mart" (không phải "Bi_s Mart")
 · mẹ SAU SINH có đoạn tư vấn khoa học riêng (không dùng đoạn mang thai) + gợi ý kết hợp + nhắc tư vấn cho con
 · bé 6–12 tháng LUÔN có 2 lựa chọn Baby A+ / BioA+ · bé >1 tuổi suy dinh dưỡng: Pedia A+ và BioA+ (không còn "Bio + sbps")
 · màn chờ: logo thật (ảnh), không có chữ báo lỗi
 · bỏ bài "Tuân thủ NĐ100/2014" khỏi Tài liệu; bỏ chữ "Luật 1 / Luật 2" (luật nội bộ) khỏi giao diện
 · "Sữa non IgG" (cụm từ không có nghĩa) -> "Sữa non giàu kháng thể"
 · trang sản phẩm: LỢI ÍCH đầy đủ (≥5 ý), có THÀNH PHẦN NGUYÊN LIỆU, Baby có bảng Lượng ăn đề nghị, không còn khối cảnh báo tư vấn
Dùng: python tests/test_phan_hoi_14_10.py [thư-mục]   (chạy trên bản cũ phải ĐỎ)"""
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
HTML = open(os.path.join(d, 'index.html'), encoding='utf-8').read()
HTML_NOIMG = re.sub(r'data:[a-z/+-]+;base64,[A-Za-z0-9+/=]+', 'B64', HTML)
res = []


def check(n, ok, det=''):
    res.append(bool(ok)); print(('OK   ' if ok else 'FAIL ') + n + ('' if ok else '  ' + str(det)[:300]))


def result(pg, obj, m, needs=None, hist=None, gender='Nam', extra=None):
    return pg.evaluate("""([obj,m,needs,hist,g,ex])=>{startTV();S.tab='tuvan';S.user.obj=obj;S.user.gender=g;S.user.hist=hist||['Không có'];S.user.name='';S.user.dob='';
      if(ex)Object.assign(S.user,ex);S.m=m;S.needs=needs||[];S.cls=classify();S.step=4;draw();
      var r=recommend();return {t:document.getElementById('view').innerText.replace(/\\s+/g,' '),ids:r.ids,why:r.why.join(' '),cls:S.cls&&S.cls.label,sci:sciAdvice()};}""",
                       [obj, m, needs, hist, gender, extra])


# ---- kiểm tra trên mã nguồn
check('mã nguồn: không còn chữ "Luật 1" / "Luật 2" (luật tư vấn nội bộ) trong giao diện', not re.search(r'Luật [12]\b', HTML_NOIMG), re.findall(r'.{30}Luật [12]\b.{10}', HTML_NOIMG)[:2])
check('mã nguồn: không còn "Sữa non IgG" / "Sữa non/IgG" / "(IgG)"', not re.search(r'[Ss]ữa non[ /]IgG|\(IgG\)|IgG…', HTML_NOIMG), re.findall(r'.{25}IgG.{15}', HTML_NOIMG)[:3])
check('mã nguồn: bỏ bài "Tuân thủ NĐ100/2014" khỏi Tài liệu', 't:"Tuân thủ NĐ100/2014"' not in HTML_NOIMG)
check('mã nguồn: không còn chữ báo lỗi ở màn chờ ("Không khởi động được", "mạng đang chậm")', 'Không khởi động được' not in HTML_NOIMG and 'mạng đang chậm' not in HTML_NOIMG)
check('mã nguồn: câu quiz không còn "cao nhất dòng trẻ em"', 'cao nhất dòng trẻ em' not in HTML_NOIMG)

with sync_playwright() as p:
    for eng in ('chromium', 'webkit'):
        b = getattr(p, eng).launch()
        T = lambda s: f'[{eng}] ' + s
        ctx = b.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True)
        ctx.add_init_script("localStorage.setItem('nt_pg', JSON.stringify('PG01'))")
        pg = ctx.new_page(); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)[:200]))
        pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith('http://127.0.0.1') else r.abort())
        pg.goto(URL); pg.wait_for_timeout(500)
        # ---- màn chờ
        sp = pg.evaluate("""()=>{var s=document.getElementById('splash');var im=[...s.querySelectorAll('img')].filter(i=>/logo/i.test(i.getAttribute('src')||'')&&i.getBoundingClientRect().width>40);
          return {logo:im.length?[Math.round(im[0].getBoundingClientRect().width),im[0].naturalWidth]:null,fakeText:!!s.querySelector('.sp-w2'),txt:s.innerText.replace(/\\s+/g,' ')}}""")
        check(T('màn chờ: hiện LOGO THẬT (ảnh logo.png), không còn chữ "Nutritie" giả bằng font'), sp['logo'] and sp['logo'][1] > 0 and not sp['fakeText'], sp)
        check(T('màn chờ: không có chữ báo lỗi'), 'lỗi' not in sp['txt'].lower() and 'chậm' not in sp['txt'].lower(), sp['txt'])
        pg.wait_for_function("document.getElementById('splash').classList.contains('hide')", timeout=30000); pg.wait_for_timeout(600)

        # ---- điểm bán
        sh = pg.evaluate("go('feedback');draw();[...document.querySelectorAll('.fb-shop .sc')].map(e=>e.textContent).join(' | ')")
        check(T("Cảm nhận khách hàng > Điểm bán chính hãng: ghi Bi's Mart, không còn Bi_s"), "Bi's Mart" in sh and 'Bi_s' not in sh, sh[:200])

        # ---- Lên đơn
        pg.evaluate("S.cart={baby:1,pedia:2};go('makeorder');draw();"); pg.wait_for_timeout(600)
        rowimg = pg.evaluate("[...document.querySelectorAll('#view .mo-item .mo-th img')].filter(i=>i.naturalWidth>0).length")
        check(T('Lên đơn: mỗi sản phẩm trong giỏ có ẢNH lon (không chỉ emoji)'), rowimg == 2, rowimg)
        chip = pg.evaluate("[...document.querySelectorAll('#view .mo-add .chip img')].filter(i=>i.naturalWidth>0).length")
        check(T('Lên đơn: các nút "Thêm nhanh" có ảnh sản phẩm'), chip == 7, chip)
        pg.evaluate("document.getElementById('mo_phone').scrollIntoView({block:'center'})"); pg.wait_for_timeout(300)
        cov = pg.evaluate("""()=>{var i=document.getElementById('mo_phone').getBoundingClientRect();var pts=[[.5,.5],[.15,.5],[.85,.5],[.5,.2],[.5,.8]];var bad=[];pts.forEach(p=>{var e=document.elementFromPoint(i.left+i.width*p[0],i.top+i.height*p[1]);if(e&&e.id!=='mo_phone')bad.push((e.className||e.tagName)+'')});return bad}""")
        check(T('Lên đơn: ô "SĐT khách" KHÔNG bị nút Chốt đơn / thanh dưới đè lên'), not cov, cov)
        try:
            pg.click('#mo_phone', timeout=4000)
            for ch in '0912345678':
                pg.keyboard.type(ch); pg.wait_for_timeout(30)
            v = pg.evaluate("[document.getElementById('mo_phone').value, S.orderPhone, document.activeElement&&document.activeElement.id]")
            check(T('Lên đơn: gõ được SĐT 10 số liền, con trỏ giữ nguyên trong ô'), v == ['0912345678', '0912345678', 'mo_phone'], v)
        except Exception as e:
            check(T('Lên đơn: gõ được SĐT khách (bấm vào ô)'), False, str(e)[:120])
        ov = pg.evaluate("""()=>{window.scrollTo(0,document.documentElement.scrollHeight);var c=document.querySelector('.mo-cta').getBoundingClientRect(),n=document.getElementById('nav').getBoundingClientRect(),i=document.getElementById('mo_phone').getBoundingClientRect();return {ctaBelowPhone:c.top>=i.bottom-1,ctaAboveNav:c.bottom<=n.top+1}}""")
        check(T('Lên đơn: kéo tới cuối — nút Chốt đơn nằm DƯỚI ô SĐT và không chui dưới thanh điều hướng'), ov['ctaBelowPhone'] and ov['ctaAboveNav'], ov)

        # ---- ảnh sản phẩm "cùng 1 nền" (khách 13/10 + 23/9: Pedia + ảnh cùng nền)
        pg.evaluate("go('sp');draw()"); pg.wait_for_timeout(300)
        gr = pg.evaluate("""async()=>{document.querySelectorAll('img').forEach(i=>i.loading='eager');await new Promise(r=>setTimeout(r,700));var im=[...document.querySelectorAll('#view .sku-img img, #view .pcard img')];return {n:im.length,broken:im.filter(i=>!(i.complete&&i.naturalWidth>0)).length,allPng:im.every(i=>/products\/\w+\.png/.test(i.getAttribute('src')||'')),base64:im.some(i=>/^data:/.test(i.getAttribute('src')||''))}}""")
        check(T('lưới SP: cả 7 lon có ảnh, tất cả dùng products/*.png (cùng kiểu cắt nền), KHÔNG còn ảnh base64 nền cảnh'), gr['n']>=7 and gr['broken']==0 and gr['allPng'] and not gr['base64'], gr)
        pd = pg.evaluate("""async()=>{openP('pedia');await new Promise(r=>setTimeout(r,600));var im=document.querySelector('#sheetin .hero-cut, #sheetin .phero img');var ok=im&&im.complete&&im.naturalWidth>0&&/products\/pedia\.png/.test(im.getAttribute('src')||'');closeP();return ok}""")
        check(T('Pedia: trang chi tiết có ảnh lon (products/pedia.png), không còn bắt cơm'), pd, pd)
        check(T('mã nguồn: đã gỡ ảnh nhúng base64 nền cảnh (DIMG rỗng) để nhẹ file + đồng bộ nền'), pg.evaluate("Object.keys(DIMG).length")==0, pg.evaluate("Object.keys(DIMG).length"))

        # ---- Trình khách
        pg.evaluate("openPresent()"); pg.wait_for_timeout(500)
        lst = pg.evaluate("""async()=>{presGo('sanpham');await new Promise(r=>setTimeout(r,600));var bad=[];document.querySelectorAll('#present .pr-pcard').forEach(c=>{var im=c.querySelector('img');if(!im)return;var r=im.getBoundingClientRect();[[.5,.5],[.25,.25],[.75,.75]].forEach(p=>{var e=document.elementFromPoint(r.left+r.width*p[0],r.top+r.height*p[1]);if(e&&e!==im)bad.push((c.getAttribute('onclick')||'')+':'+(e.className||e.tagName))})});return bad}""")
        check(T('Trình khách > danh sách sản phẩm: ảnh không bị emoji đè'), not lst, lst)
        for pid in ('pedia', 'growiq', 'colostrum', 'canxipro', 'mama'):
            cv = pg.evaluate("""async(id)=>{presProduct(id);await new Promise(r=>setTimeout(r,450));var im=document.querySelector('#present .pr-phero img');if(!im)return ['noimg'];var r=im.getBoundingClientRect();var bad=[];[[.5,.5],[.3,.3],[.7,.7]].forEach(p=>{var e=document.elementFromPoint(r.left+r.width*p[0],r.top+r.height*p[1]);if(e&&e!==im)bad.push(e.className||e.tagName)});return bad}""", pid)
            check(T(f'Trình khách > {pid}: ảnh lớn không bị icon đè'), not cv, cv)
        pg.evaluate("(typeof closePresent==='function')?closePresent():document.getElementById('present').classList.remove('open')"); pg.wait_for_timeout(700)

        # ---- ngày sinh ở bước tư vấn (khách 13/10: "ngày sinh chỗ tư vấn ko nhập đc") + SĐT không nhảy (19/9)
        pg.evaluate("startTV();S.tab='tuvan';S.user.obj='tre_0_12';go('tuvan');draw();"); pg.wait_for_timeout(300)
        has_dob = pg.query_selector("#view input[type=date]") is not None
        pg.eval_on_selector("#view input[type=date]", "el=>{el.value='2026-02-16';el.dispatchEvent(new Event('input',{bubbles:true}))}"); pg.wait_for_timeout(150)
        dobcap = pg.evaluate("S.user.dob")
        check(T('bước tư vấn: ô ngày sinh của bé NHẬP ĐƯỢC (oninput bắt giá trị ngay, kể cả WebKit/Safari)'), has_dob and dobcap == '2026-02-16', (has_dob, dobcap))
        pg.evaluate("startTV();S.tab='tuvan';S.user.obj='tre_0_12';S.user.dob='2026-02-16';syncKidAge();S.user.consent=true;go('tuvan');draw();"); pg.wait_for_timeout(300)
        jumped = False
        if pg.query_selector('#kid_phone'):
            pg.evaluate("document.getElementById('kid_phone').scrollIntoView({block:'center'})"); pg.wait_for_timeout(150)
            pg.click('#kid_phone')
            for ch in '0912345678':
                pg.keyboard.type(ch); pg.wait_for_timeout(30)
                if pg.evaluate("document.activeElement&&document.activeElement.id") != 'kid_phone':
                    jumped = True; break
            v = pg.evaluate("[document.getElementById('kid_phone').value, S.user.phone]")
            check(T('bước tư vấn: gõ SĐT 10 số không nhảy lên đầu trang, con trỏ giữ trong ô'), (not jumped) and v == ['0912345678', '0912345678'], (jumped, v))
        else:
            check(T('bước tư vấn: có ô SĐT khi khách đồng ý'), False)

        # ---- mẹ sau sinh
        r = result(pg, 'pregnant', {'w': 58, 'h': 160}, needs=['Lợi sữa'], extra={'postpartum': True})
        check(T('mẹ SAU SINH: đoạn tư vấn khoa học nói về sau sinh / cho con bú, không phải "mang thai" + nhắc tư vấn cho con'),
              'sau sinh' in r['sci'].lower() and 'Baby A+' in r['sci'] and 'thai nhi' not in r['sci'] and r['ids'][0] == 'mama', r['sci'][:200])
        check(T('mẹ sau sinh chọn "Lợi sữa": có đoạn riêng, không hứa chắc kết quả'), 'lợi sữa' in r['sci'].lower() and 'chỉ hỗ trợ' in r['sci'].lower(), r['sci'][:300])
        r = result(pg, 'pregnant', {'w': 58, 'h': 160}, needs=['Chuột rút / đau xương khớp'], extra={'postpartum': True})
        check(T('mẹ sau sinh bị chuột rút / đau xương khớp: Mama A+ + kết hợp Canxi Pro A+'), r['ids'] == ['mama', 'canxipro'], r['ids'])
        r = result(pg, 'pregnant', {'pw': 55, 'h': 160}, needs=['Bổ sung DHA'])
        check(T('mẹ ĐANG MANG THAI vẫn giữ đoạn mang thai'), 'thai' in r['sci'].lower() and r['ids'] == ['mama'], r['sci'][:150])

        # ---- bé 0-12 tháng
        r = result(pg, 'tre_0_12', {'months': 8, 'w': 8.6, 'h': 70})
        check(T('bé 8 tháng BÌNH THƯỜNG: 2 lựa chọn Baby A+ và BioA+ (Baby mặc định)'), r['ids'] == ['baby', 'bio'] and 'BioA+' in r['t'] and 'Baby A+' in r['t'], r['ids'])
        r = result(pg, 'tre_0_12', {'months': 8, 'w': 6.9, 'h': 68})
        check(T('bé 8 tháng NHẸ CÂN: vẫn 2 lựa chọn, BioA+ lên trước'), r['ids'] == ['bio', 'baby'], r['ids'])
        r = result(pg, 'tre_0_12', {'months': 3, 'w': 5.8, 'h': 60})
        check(T('bé 3 tháng: chỉ Baby A+ (quy tắc cứng 0–6 tháng)'), r['ids'] == ['baby'], r['ids'])
        # ---- trên 1 tuổi suy dinh dưỡng
        r = result(pg, 'tre_1_10', {'age': 2, 'w': 9.0, 'h': 82})
        check(T('bé 2 tuổi nhẹ cân: Pedia A+ và BioA+ (Pedia đứng đầu)'), r['ids'][:2] == ['pedia', 'bio'], r['ids'])
        r = result(pg, 'tre_1_10', {'age': 2, 'w': 9.0, 'h': 82}, needs=['Tiêu hóa kém'])
        check(T('bé 2 tuổi nhẹ cân + tiêu hóa kém: vẫn Pedia A+ trước (không chỉ BioA+), có BioA+'), r['ids'][:2] == ['pedia', 'bio'], r['ids'])
        r = result(pg, 'tre_1_10', {'age': 2, 'w': 9.0, 'h': 82}, needs=['Hay ốm / miễn dịch kém'])
        check(T('bé 2 tuổi nhẹ cân + hay ốm: Pedia + BioA+ + Colostrum, cả 3 hiện thành thẻ'), r['ids'] == ['pedia', 'bio', 'colostrum'] and 'Colostrum DHA' in r['t'], r['ids'])
        r = result(pg, 'tre_1_10', {'age': 4, 'w': 12.0, 'h': 98})
        check(T('bé 4 tuổi nhẹ cân: chỉ Pedia A+ (BioA+ chỉ đến 36 tháng)'), r['ids'] == ['pedia'], r['ids'])
        r = result(pg, 'tre_1_10', {'age': 2, 'w': 12.4, 'h': 87}, needs=['Tiêu hóa kém'])
        check(T('bé 2 tuổi bình thường + tiêu hóa kém: BioA+ (giữ như cũ)'), r['ids'] == ['bio'], r['ids'])

        # ---- tồn kho theo TỪNG quy cách (khách 19/9: link tồn kho real từng tab)
        pg.evaluate("localStorage.removeItem('nt_stock')")
        sk = pg.evaluate("[stockLevel('pedia','Lon 800g'),stockLevel('pedia','Lon 400g'),stockLevel('pedia','Thùng 12 lon x 800g'),stockLevel('pedia')]")
        check(T('tồn kho tách theo quy cách: Pedia Lon800/Lon400/Thùng khác nhau, tổng = cộng dồn'), sk[0]!=sk[1] and sk[0]==30 and sk[1]==14 and sk[3]==sk[0]+sk[1]+sk[2]+pg.evaluate("stockLevel('pedia','Thùng 24 lon x 400g')"), sk)
        pg.evaluate("openP('pedia')"); pg.wait_for_timeout(400)
        d1 = pg.evaluate("document.getElementById('sheetin').innerText")
        pg.evaluate("setDetailPack('pedia','Lon 400g')"); pg.wait_for_timeout(400)
        d2 = pg.evaluate("document.getElementById('sheetin').innerText")
        check(T('trang chi tiết: đổi tab quy cách thì SỐ TỒN đổi theo (Lon 800g=30 → Lon 400g=14)'), 'Còn 30 Lon 800g' in d1 and 'Còn 14 Lon 400g' in d2, (('30' in d1), ('14' in d2)))
        pg.evaluate("closeP()")
        # đặt đơn trừ đúng quy cách
        b0 = pg.evaluate("stockLevel('baby','Thùng 12 lon x 800g')"); l0 = pg.evaluate("stockLevel('baby','Lon 800g')")
        pg.evaluate("S.cart={baby:2};S.orderVar={baby:'Thùng 12 lon x 800g'};S.orderPhone='0912345678';S.orderName='T';chotDon()"); pg.wait_for_timeout(300)
        b1 = pg.evaluate("stockLevel('baby','Thùng 12 lon x 800g')"); l1 = pg.evaluate("stockLevel('baby','Lon 800g')")
        check(T('đặt đơn 2 Thùng: trừ đúng kho Thùng (3→1), kho Lon 800g GIỮ NGUYÊN'), b1==b0-2 and l1==l0, (b0,b1,l0,l1))
        # tab tồn kho liệt kê từng quy cách
        pg.evaluate("go('stock');draw()"); pg.wait_for_timeout(300)
        stx = pg.evaluate("document.getElementById('view').innerText")
        check(T('tab Tồn kho: liệt kê từng quy cách của mỗi SKU'), 'Lon 800g' in stx and 'Lon 400g' in stx and 'Thùng 12 lon x 800g' in stx and 'Lốc 110ml' in stx, stx[:60])
        pg.evaluate("localStorage.removeItem('nt_stock')")

        # ---- số liệu pha theo NHÃN (bảng thành phần): Pedia 205ml/247kcal, Grow IQ 230ml
        us = pg.evaluate("Object.fromEntries(PRODUCTS.map(p=>[p.id,p.usage||'']))")
        check(T('Pedia: cách pha đúng nhãn 55,5g + 170ml → 205ml, 247 kcal (trước sai 195ml/238kcal)'), '205ml' in us['pedia'] and '247 kcal' in us['pedia'] and '195ml' not in us['pedia'], us['pedia'][:90])
        check(T('Grow IQ: cách pha đúng nhãn 44g + 200ml → 230ml (trước sai 220ml)'), '230ml' in us['growiq'] and '200ml' in us['growiq'], us['growiq'][:90])
        check(T('Canxi Pro giữ đúng nhãn 190ml; Mama 210ml'), '190ml' in us['canxipro'] and '210ml' in us['mama'], (us['canxipro'][:40], us['mama'][:40]))

        # ---- trang sản phẩm
        for pid in ('baby', 'bio', 'pedia', 'growiq', 'colostrum', 'canxipro', 'mama'):
            pr = pg.evaluate("""async(id)=>{go('sp');openP(id);await new Promise(r=>setTimeout(r,500));var s=document.getElementById('sheetin');var t=s.innerText.replace(/\\s+/g,' ');
              return {n:s.querySelectorAll('.bul .b').length,ing:t.includes('THÀNH PHẦN NGUYÊN LIỆU')||t.includes('Thành phần nguyên liệu'),warn:s.querySelectorAll('.warn').length,t:t}}""", pid)
            check(T(f'{pid}: LỢI ÍCH ≥ 5 ý + có mục Thành phần nguyên liệu + không còn khối cảnh báo tư vấn'), pr['n'] >= 5 and pr['ing'] and pr['warn'] == 0, (pr['n'], pr['ing'], pr['warn']))
            if pid == 'baby':
                bb = pg.evaluate("[...document.querySelectorAll('#sheetin img')].filter(i=>/luongan/i.test(i.getAttribute('src')||'')&&i.complete&&i.naturalWidth>0).length")
                check(T('Baby A+: có BẢNG LƯỢNG ĂN ĐỀ NGHỊ (ảnh) + đúng câu hướng dẫn pha'), bb == 1 and '1 muỗng gạt (tương đương 4,6g) pha với 30ml nước (50°C), pha với nước chín ấm.' in pr['t'] and 'Bảng lượng ăn đề nghị chỉ mang tính chất tham khảo, có thể điều chỉnh lượng ăn theo nhu cầu thực tế của mỗi bé.' in pr['t'], (bb, pr['t'][pr['t'].find('Cách dùng'):pr['t'].find('Cách dùng') + 200]))
            if pid == 'pedia':
                check(T('Pedia: không còn chữ "Luật 1/2", "IgG" trong trang sản phẩm'), not re.search(r'Luật \d|IgG', pr['t']), pr['t'][:100])
        pg.evaluate("closeP()")
        # ---- kết quả tư vấn vẫn còn cảnh báo (chỉ bỏ ở trang sản phẩm)
        r = result(pg, 'tre_1_10', {'age': 6, 'w': 17, 'h': 112})
        check(T('kết quả tư vấn: VẪN còn cảnh báo dị ứng đạm bò (chỉ bỏ ở trang sản phẩm)'), 'Dị ứng đạm bò' in r['t'], r['t'][:80])
        errs[:] = [e for e in errs if 'Response served by service worker' not in e]
        check(T('không lỗi JS'), not errs, errs)
        pg.close(); b.close()

shutil.rmtree(d, ignore_errors=True)
print(f'TỔNG {sum(res)} / {len(res)}')
sys.exit(0 if all(res) else 1)
