"""Phép thử Nutritie 15/10/2026 — rà soát toàn diện (4 nhóm agent), đợt 1: correctness + pháp lý + câu chữ.
 B2 giá Thùng = số lượng × giá đơn vị cùng dung tích (trước: chọn thùng ra giá 1 lon) ·
 B3 đếm tồn theo tổng per-pack (trước: object<=số -> luôn 0 "không sắp/hết hàng") ·
 B4 đồng bộ kho giữ tồn per-pack khi server trả số phẳng ·
 B1 chốt đơn chặn khi vượt tồn theo quy cách ·
 A2 giới tính KHÔNG mặc định Nam, bắt chọn cho trẻ (chuẩn WHO khác nhau) ·
 A3 bé thừa cân + tiêu hóa kém KHÔNG đẩy BioA+ ·
 A1 tiền sản giật -> cảnh báo khám bác sĩ ·
 câu khuyến cáo sữa mẹ NGUYÊN VĂN · bỏ "Năng lượng vàng" · "Grow IQ A+" · icon schedule.
Dùng: python tests/test_ra_soat_14_10.py [thư-mục]   (bản cũ phải ĐỎ)"""
import sys, os, shutil, tempfile, threading, functools, http.server, socketserver
from playwright.sync_api import sync_playwright

SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = tempfile.mkdtemp()
for it in os.listdir(SRC):
    if it in ('.git', 'api', 'tests', 'node_modules'): continue
    sp = os.path.join(SRC, it)
    (shutil.copytree if os.path.isdir(sp) else shutil.copy)(sp, os.path.join(d, it))


class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass


srv = socketserver.TCPServer(('127.0.0.1', 0), functools.partial(Q, directory=d))
threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f'http://127.0.0.1:{srv.server_address[1]}/'
res = []


def check(n, ok, det=''):
    res.append(bool(ok)); print(('OK   ' if ok else 'FAIL ') + n + ('' if ok else '  ' + str(det)[:200]))


def result(pg, obj, m, needs=None, hist=None, gender='Nam', extra=None):
    return pg.evaluate("""([obj,m,needs,hist,g,ex])=>{startTV();S.tab='tuvan';S.user.obj=obj;S.user.gender=g;S.user.hist=hist||['Không có'];
      if(ex)Object.assign(S.user,ex);S.m=m;S.needs=needs||[];S.cls=classify();S.step=4;draw();
      var r=recommend();return {t:document.getElementById('view').innerText.replace(/\\s+/g,' '),ids:r.ids,cls:S.cls&&S.cls.label};}""",
                       [obj, m, needs, hist, gender, extra])


with sync_playwright() as p:
    for eng in ('chromium', 'webkit'):
        b = getattr(p, eng).launch()
        T = lambda s: f'[{eng}] ' + s
        ctx = b.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True)
        ctx.add_init_script("localStorage.setItem('nt_pg', JSON.stringify('PG01'))")
        pg = ctx.new_page(); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)[:200]))
        pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith('http://127.0.0.1') else r.abort())
        pg.goto(URL); pg.wait_for_function("document.getElementById('splash').classList.contains('hide')", timeout=30000); pg.wait_for_timeout(500)

        # B2 giá thùng
        pr = pg.evaluate("[unitPrice('pedia','Lon 800g'),unitPrice('pedia','Thùng 12 lon x 800g'),unitPrice('colostrum','Lốc 110ml'),unitPrice('colostrum','Thùng 110ml x 48 hộp')]")
        check(T('B2: giá Thùng = SL × giá đơn vị cùng dung tích (Pedia thùng = 12 × lon 800g), KHÔNG bằng giá 1 lon'), pr[1] == pr[0] * 12 and pr[1] != pr[0] and pr[3] == pr[2] * 48, pr)
        # B3 đếm tồn per-pack
        pg.evaluate("localStorage.removeItem('nt_stock')")
        okcount = pg.evaluate("""(()=>{try{var out=0,low=0;PRODUCTS.forEach(function(p){packs(p.id).forEach(function(pk){var q=stockLevel(p.id,pk);if(q==null)return;if(q<=0)out++;else if(q<=5)low++;});});return {ok:true,out:out,low:low};}catch(e){return {ok:false,e:String(e)}}})()""")
        check(T('B3: đếm tồn theo stockLevel tổng per-pack chạy được (không còn so object<=số)'), okcount['ok'] and okcount['low'] >= 1, okcount)
        # B4 tồn SỐ phẳng (server/bản cũ) -> packStock gán vào quy cách đầu, quy cách khác = chưa thiết lập
        kept = pg.evaluate("""(()=>{localStorage.setItem('nt_stock',JSON.stringify({items:{pedia:99},at:Date.now()}));
          return {lon800:stockLevel('pedia','Lon 800g'),lon400:stockLevel('pedia','Lon 400g'),total:stockLevel('pedia')};})()""")
        check(T('B4: tồn là SỐ phẳng -> gán vào quy cách đầu (Lon 800g=99), quy cách khác = null; tổng = 99'), kept['lon800'] == 99 and kept['lon400'] is None and kept['total'] == 99, kept)
        pg.evaluate("localStorage.removeItem('nt_stock')")
        # B1 chốt đơn chặn vượt tồn
        blocked = pg.evaluate("""(()=>{localStorage.removeItem('nt_stock');var pk='Thùng 24 lon x 400g';var lv=stockLevel('bio',pk);
          S.cart={bio:(lv||0)+5};S.orderVar={bio:pk};S.orderPhone='0912345678';S.orderName='T';var n0=orders().length;chotDon();return {made:orders().length-n0,lv:lv};})()""")
        check(T('B1: đặt vượt tồn quy cách -> KHÔNG tạo đơn (chặn + báo)'), blocked['made'] == 0, blocked)
        pg.evaluate("localStorage.removeItem('nt_stock')")

        # A2 gender gate
        pg.evaluate("startTV();S.tab='tuvan';S.user.obj='tre_0_12';S.user.dob='';S.user.consent=false;S.m={};go('tuvan');draw();next1()")
        check(T('A2: chưa chọn giới tính -> KHÔNG sang bước 2 (bé trai/gái chuẩn WHO khác nhau)'), pg.evaluate("S.step") == 1 and pg.evaluate("S.user.gender") == '', pg.evaluate("S.user.gender"))
        pg.evaluate("S.user.gender='Nữ';next1()")
        check(T('A2: chọn giới tính xong -> sang bước 2'), pg.evaluate("S.step") == 2)
        # A3 thừa cân + tiêu hóa kém
        r = result(pg, 'tre_1_10', {'age': 2, 'w': 16, 'h': 85}, needs=['Tiêu hóa kém'])
        check(T('A3: bé 2 tuổi THỪA CÂN + tiêu hóa kém -> KHÔNG gợi BioA+ đậm độ cao hơn'), 'bio' not in r['ids'] and 'chuẩn' in (r['cls'] or '') and 'cao hơn' in (r['cls'] or '').lower(), (r['cls'], r['ids']))
        r = result(pg, 'tre_1_10', {'age': 2, 'w': 11.5, 'h': 87}, needs=['Tiêu hóa kém'])
        check(T('A3: bé 2 tuổi bình thường + tiêu hóa kém -> VẪN BioA+ (giữ đúng)'), r['ids'] == ['bio'], (r['cls'], r['ids']))
        # A1 tiền sản giật
        r = result(pg, 'pregnant', {'pw': 55, 'h': 160}, hist=['Tiền sản giật'], gender='Nữ')
        check(T('A1: tiền sản giật -> hiện cảnh báo khám bác sĩ chuyên khoa sản'), 'Tiền sản giật' in r['t'] and 'khám bác sĩ' in r['t'], r['t'][:120])

        # câu chữ / icon
        check(T('câu khuyến cáo sữa mẹ NGUYÊN VĂN trong SCI.infant'), 'Sữa mẹ là thức ăn tốt nhất cho sức khỏe và sự phát triển toàn diện của trẻ nhỏ' in pg.evaluate("SCI.infant"))
        check(T('bỏ mỹ từ "Năng lượng vàng" (hiện cho khách)'), 'Năng lượng vàng' not in pg.evaluate("JSON.stringify(PRODUCTS)"))
        check(T('không còn "server"/"endpoint" tiếng Anh trong câu cho PG'), pg.evaluate("""(()=>{var s=document.documentElement.innerHTML;return !/Đã gửi server|từ server|endpoint\\/mạng/.test(s)})()"""))
        check(T('icon schedule thay event_available (không còn chấm tròn vô nghĩa)'), pg.evaluate("typeof ICONS==='undefined' || !!ICONS.schedule"))

        errs[:] = [e for e in errs if 'Response served by service worker' not in e]
        check(T('không lỗi JS'), not errs, errs)
        pg.close(); b.close()

shutil.rmtree(d, ignore_errors=True)
print(f'TỔNG {sum(res)} / {len(res)}')
sys.exit(0 if all(res) else 1)
