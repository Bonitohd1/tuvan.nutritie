"""Phép thử Nutritie 15/10/2026 — tính năng đợt 3 (4 nhóm agent): F8 hồ sơ công bố Trình khách · F14 khẩu phần/số lon · F5 câu chốt · F4 khách cũ · F13 nhắc tái mua · F1 trình kết quả cho khách.
Dùng: python tests/test_tinh_nang_15_10.py [thư-mục]   (bản cũ phải ĐỎ)"""
import sys, os, shutil, tempfile, threading, functools, http.server, socketserver
from playwright.sync_api import sync_playwright
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = tempfile.mkdtemp()
for it in os.listdir(SRC):
    if it in ('.git','api','tests','node_modules'): continue
    sp=os.path.join(SRC,it); (shutil.copytree if os.path.isdir(sp) else shutil.copy)(sp,os.path.join(d,it))
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a): pass
srv=socketserver.TCPServer(('127.0.0.1',0),functools.partial(Q,directory=d)); threading.Thread(target=srv.serve_forever,daemon=True).start()
URL=f'http://127.0.0.1:{srv.server_address[1]}/'
res=[]
def check(n,ok,det=''):
    res.append(bool(ok)); print(('OK   ' if ok else 'FAIL ')+n+('' if ok else '  '+str(det)[:180]))
def setup(pg,obj,m,needs=None,hist=None,gender='Nam'):
    pg.evaluate("""([obj,m,needs,hist,g])=>{startTV();S.tab='tuvan';S.user.obj=obj;S.user.gender=g;S.user.hist=hist||['Không có'];S.m=m;S.needs=needs||[];S.cls=classify();S.step=4;draw();}""",[obj,m,needs,hist,gender])
with sync_playwright() as p:
    for eng in ('chromium','webkit'):
        b=getattr(p,eng).launch(); T=lambda s:f'[{eng}] '+s
        ctx=b.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
        ctx.add_init_script("localStorage.setItem('nt_pg', JSON.stringify('PG01'))")
        pg=ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)[:150]))
        pg.route('**/*',lambda r: r.continue_() if r.request.url.startswith('http://127.0.0.1') else r.abort())
        pg.goto(URL); pg.wait_for_function("document.getElementById('splash').classList.contains('hide')",timeout=30000); pg.wait_for_timeout(500)
        # F8
        pg.evaluate("openPresent();presProduct('pedia')"); pg.wait_for_timeout(400)
        tp=pg.evaluate("document.getElementById('present').innerText")
        check(T('F8: Trình khách > Pedia có "Hồ sơ & Chứng nhận chính hãng" (Giấy công bố + Giải thưởng)'),'Hồ sơ & Chứng nhận chính hãng' in tp and 'Giấy công bố sản phẩm' in tp and 'Giải thưởng' in tp, tp[:0])
        pg.evaluate("presProduct('baby')"); pg.wait_for_timeout(250)
        check(T('F8: Baby (<24th) KHÔNG hiện khối hồ sơ ở Trình khách'),'Hồ sơ & Chứng nhận chính hãng' not in pg.evaluate("document.getElementById('present').innerText"))
        pg.evaluate("closePresent()"); pg.wait_for_timeout(200)
        # F14 + F5 ở màn kết quả
        setup(pg,'tre_1_10',{'age':4,'w':12,'h':98})
        t=pg.evaluate("document.getElementById('view').innerText")
        check(T('F14: kết quả có "Khẩu phần & số lượng gợi ý" + "lon/tháng"'),'Khẩu phần & số lượng gợi ý' in t and 'lon/tháng' in t)
        check(T('F5: kết quả có "Gợi ý câu tư vấn / chốt (cho tư vấn viên)"'),'Gợi ý câu tư vấn / chốt' in t)
        check(T('F1: kết quả có nút "Trình kết quả cho khách"'),'Trình kết quả cho khách' in t)
        # F1
        pg.evaluate("presResult()"); pg.wait_for_timeout(300)
        pt=pg.evaluate("document.getElementById('present').innerText")
        check(T('F1: present có thước đo + Nhận định + SẢN PHẨM PHÙ HỢP (Pedia)'),'Nhận định dinh dưỡng' in pt and 'SẢN PHẨM PHÙ HỢP' in pt.upper() and 'Pedia' in pt)
        check(T('F1: present KHÔNG lộ nội bộ (câu chốt / đưa đi khám)'),'Gợi ý câu tư vấn' not in pt and 'đưa đi khám' not in pt)
        pg.evaluate("closePresent()"); pg.wait_for_timeout(150)
        setup(pg,'tre_0_12',{'months':8,'w':8.6,'h':70})
        pg.evaluate("presResult()"); pg.wait_for_timeout(300)
        pt=pg.evaluate("document.getElementById('present').innerText")
        check(T('F1: bé <24th present KHÔNG nêu tên/công dụng SP + có câu sữa mẹ'),'Baby' not in pt and 'Sữa mẹ là thức ăn tốt nhất' in pt and 'tư vấn viên sẽ tư vấn' in pt.lower())
        pg.evaluate("closePresent()"); pg.wait_for_timeout(150)
        # F4 + F13
        pg.evaluate("""(()=>{var os=[{id:'NTOLD',phone:'0912345678',name:'Chị Lan',items:[{sku:'pedia',name:'Nutritie Pedia A+',qty:2,pack:'Lon 800g'}],total:910000,at:Date.now()-25*86400000,status:'da_xac_nhan'}];localStorage.setItem('nt_order_queue',JSON.stringify(os));})()""")
        pg.evaluate("startTV();S.tab='tuvan';S.user.obj='tre_1_10';S.user.gender='Nam';S.user.dob='2022-01-10';syncKidAge&&syncKidAge();S.user.consent=true;S.user.phone='0912345678';go('tuvan');draw()"); pg.wait_for_timeout(400)
        ch=pg.evaluate("(document.getElementById('cust_hist')||{}).innerText||''")
        check(T('F4: bước tư vấn hiện "Khách cũ · N đơn trước" khi SĐT có lịch sử'),'Khách cũ' in ch and '1 đơn' in ch, ch[:80])
        pg.evaluate("S.user.phone='0900000000';custHistPaint()"); pg.wait_for_timeout(120)
        check(T('F4: SĐT lạ -> không hiện khách cũ'),(pg.evaluate("(document.getElementById('cust_hist')||{}).innerText||''")).strip()=='')
        pg.evaluate("go('home');draw()"); pg.wait_for_timeout(250)
        hm=pg.evaluate("document.getElementById('view').innerText")
        check(T('F13: Home có "Khách nên nhắc tái mua" (đơn 25 ngày trước)'),'Khách nên nhắc tái mua' in hm)
        pg.evaluate("""(()=>{var os=JSON.parse(localStorage.getItem('nt_order_queue'));os[0].at=Date.now()-5*86400000;localStorage.setItem('nt_order_queue',JSON.stringify(os));})()""")
        pg.evaluate("go('home');draw()"); pg.wait_for_timeout(200)
        check(T('F13: đơn mới 5 ngày -> KHÔNG nhắc tái mua'),'Khách nên nhắc tái mua' not in pg.evaluate("document.getElementById('view').innerText"))
        pg.evaluate("localStorage.removeItem('nt_order_queue')")
        errs[:]=[e for e in errs if 'Response served by service worker' not in e]
        check(T('không lỗi JS'),not errs,errs)
        pg.close(); b.close()
shutil.rmtree(d,ignore_errors=True)
print(f'TỔNG {sum(res)} / {len(res)}')
sys.exit(0 if all(res) else 1)
