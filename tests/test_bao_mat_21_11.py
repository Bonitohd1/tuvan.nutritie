"""Phép thử bảo mật Nutritie 21/11/2026 — QA NT-01 / NT-02 / NT-03 (test app/QA_FEEDBACK.md).
  A. API serverless (chạy hàm Vercel bằng Node, req/res giả):
     /api/orders + /api/stock đã TẮT (410) cho mọi phương thức, KHÔNG BAO GIỜ trả dữ liệu đã lưu; kho RAM api/_store.js đã gỡ;
     CORS chỉ mở cho tên miền chính thức (+ NT_CORS_ORIGINS), không còn '*'.
  B. App (Playwright, chromium + webkit):
     - tồn kho không còn gọi /api/stock demo; máy chủ kho lỗi -> KHÔNG báo "đã đồng bộ", không ghi đè số tại máy;
     - PIN quản trị: không còn PIN mặc định nguyên văn trong mã, không lưu PIN chữ trơn (băm SHA-256 + muối),
       vào bằng PIN mặc định -> bắt đặt PIN mới trước khi thấy đơn / khách / xuất dữ liệu; PIN cũ chữ trơn tự chuyển, không khoá người dùng.
Dùng: python tests/test_bao_mat_21_11.py [thư-mục]   (bản trước 21/11 phải ĐỎ)"""
import sys, os, json, shutil, tempfile, threading, functools, http.server, socketserver, subprocess, hashlib
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding='utf-8')
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEF_PIN = '246810'   # PIN mặc định đã bàn giao — CHỈ được nằm ở phép thử (thư mục tests/ không lên Vercel)
res = []
def check(n, ok, det=''):
    res.append(bool(ok)); print(('OK   ' if ok else 'FAIL ') + n + ('' if ok else '  ' + str(det)[:220]), flush=True)
sha = lambda s: hashlib.sha256(s.encode('utf-8')).hexdigest()

# ---------------- A. API
NODE = r"""
const path=require('path');const root=process.argv[1];const out={};
function mk(method,origin,body){const req={method,headers:origin?{origin}:{},body:body||{}};
 const res={code:0,h:{},body:null,status(c){this.code=c;return this},json(o){this.body=o;return this},end(){return this},send(o){this.body=o;return this},setHeader(k,v){this.h[k.toLowerCase()]=v}};return {req,res}}
function run(f,m,o,b){const x=mk(m,o,b);try{f(x.req,x.res)}catch(e){return {err:String(e)}}return {code:x.res.code,body:JSON.stringify(x.res.body),acao:x.res.h['access-control-allow-origin']||null}}
const ld=n=>require(path.join(root,'api',n));
const orders=ld('orders.js'),stock=ld('stock.js'),health=ld('health.js');
out.postOrder=run(orders,'POST',null,{phone:'0912345678',name:'Khach Thu',items:[{sku:'baby',qty:1}]});
out.getOrder=run(orders,'GET');
out.postStock=run(stock,'POST',null,{items:{baby:999}});
out.getStock=run(stock,'GET');
out.optOk=run(orders,'OPTIONS','https://tuvan-nutritie.vercel.app');
out.getEvil=run(health,'GET','https://evil.example');
out.getExtra=run(health,'GET','https://them.example');
out.health=run(health,'GET');
console.log(JSON.stringify(out));
"""
p = subprocess.run(['node', '-e', NODE, SRC], capture_output=True, text=True, encoding='utf-8',
                   env=dict(os.environ, NT_CORS_ORIGINS='https://them.example'))
try:
    A = json.loads(p.stdout.strip().splitlines()[-1])
except Exception:
    A = {}
check('A: chạy được 3 hàm API bằng Node', bool(A), (p.stdout + p.stderr)[-300:])
g = lambda k: A.get(k) or {}
check('A: POST /api/orders -> 410 (không nhận đơn vào kho RAM)', g('postOrder').get('code') == 410, g('postOrder'))
check('A: GET /api/orders -> 410 và KHÔNG trả danh sách đơn / SĐT', g('getOrder').get('code') == 410
      and '"orders"' not in (g('getOrder').get('body') or '') and '0912345678' not in (g('getOrder').get('body') or ''), g('getOrder'))
check('A: POST /api/stock -> 410 (không ai ghi đè tồn kho)', g('postStock').get('code') == 410, g('postStock'))
check('A: GET /api/stock -> 410, không trả số tồn demo', g('getStock').get('code') == 410 and '"items"' not in (g('getStock').get('body') or ''), g('getStock'))
check('A: CORS mở cho tên miền chính thức', g('optOk').get('acao') == 'https://tuvan-nutritie.vercel.app', g('optOk'))
check('A: CORS KHÔNG mở cho tên miền lạ (không còn "*")', g('getEvil').get('acao') is None, g('getEvil'))
check('A: NT_CORS_ORIGINS thêm được tên miền', g('getExtra').get('acao') == 'https://them.example', g('getExtra'))
check('A: /api/health 200, không còn báo số đơn trong RAM', g('health').get('code') == 200 and '"orders":' not in (g('health').get('body') or ''), g('health'))
api_dir = os.path.join(SRC, 'api')
api_src = ''.join(open(os.path.join(api_dir, f), encoding='utf-8').read() for f in os.listdir(api_dir) if f.endswith('.js'))
check('A: kho RAM api/_store.js đã gỡ, không còn globalThis.__NT_STORE', not os.path.exists(os.path.join(api_dir, '_store.js')) and '__NT_STORE' not in api_src)

# ---------------- B. App
html = open(os.path.join(SRC, 'index.html'), encoding='utf-8').read()
check('B: PIN mặc định KHÔNG còn nguyên văn trong index.html', DEF_PIN not in html)
d = tempfile.mkdtemp()
for it in os.listdir(SRC):
    if it in ('.git', 'api', 'tests', 'node_modules', 'test app'): continue
    sp = os.path.join(SRC, it); (shutil.copytree if os.path.isdir(sp) else shutil.copy)(sp, os.path.join(d, it))
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = socketserver.TCPServer(('127.0.0.1', 0), functools.partial(Q, directory=d)); threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f'http://127.0.0.1:{srv.server_address[1]}/'
SHA_CASES = ['', 'abc', 'nt-def-2026:' + DEF_PIN, 'Mẹ bé 🍼 Nutritie', 'a' * 55, 'a' * 56, 'a' * 64, 'x' * 1000]

def open_ctx(b, init=None):
    # chặn service worker: yêu cầu đi qua SW thì page.route không thấy -> đếm lời gọi /api/stock sai
    ctx = b.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True, service_workers='block')
    ctx.add_init_script("localStorage.setItem('nt_pg', JSON.stringify('PG01'));" + (init or ''))
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:150]))
    api_hits = []
    def route(r):
        if '/api/stock' in r.request.url or '/api/orders' in r.request.url: api_hits.append(r.request.url)
        return r.continue_() if r.request.url.startswith('http://127.0.0.1') else r.abort()
    pg.route('**/*', route)
    pg.goto(URL); pg.wait_for_function("document.getElementById('splash').classList.contains('hide')", timeout=30000); pg.wait_for_timeout(400)
    return ctx, pg, errs, api_hits

def view(pg): return pg.evaluate("document.getElementById('view').innerText")
def toast(pg): return pg.evaluate("document.getElementById('toast').textContent")
def login(pg, pin):
    pg.evaluate("go('admin');draw()"); pg.wait_for_timeout(120)
    pg.evaluate("(v)=>{var e=document.getElementById('adminpin');if(e){e.value=v;adminLogin();}}", pin); pg.wait_for_timeout(200)
    return pg.evaluate("S.adminAuthed===true")
def storage_values(pg): return pg.evaluate("(()=>{var o={};for(var i=0;i<localStorage.length;i++){var k=localStorage.key(i);o[k]=localStorage.getItem(k);}return o;})()")

with sync_playwright() as p:
    for eng in ('chromium', 'webkit'):
        b = getattr(p, eng).launch(); T = lambda s: f'[{eng}] ' + s
        # ---- tồn kho + PIN trên máy mới
        ctx, pg, errs, hits = open_ctx(b)
        try:
            out = pg.evaluate("(a)=>a.map(function(s){return sha256Hex(s);})", SHA_CASES)
        except Exception as e:
            out = [str(e)]
        check(T('sha256Hex khớp hashlib (8 chuỗi: rỗng, tiếng Việt + emoji, biên khối 55/56/64, 1000 ký tự)'), out == [sha(s) for s in SHA_CASES], out[:2])
        check(T('đơn vẫn gửi về máy chủ Isopharma (SYNC_URL api.wintop.vn)'), pg.evaluate("SYNC_URL").startswith('https://api.wintop.vn/'))
        check(T('tồn kho: không tích hợp -> stockUrl() rỗng (không gọi /api/stock demo)'), pg.evaluate("stockUrl()") == '', pg.evaluate("stockUrl()"))
        before = pg.evaluate("JSON.stringify(stockData().items)")
        pg.evaluate("syncStock()"); pg.wait_for_timeout(300)
        check(T('tồn kho: bấm đồng bộ khi chưa nối kho -> nói rõ "chưa nối hệ thống", không gọi /api/stock'), 'chưa nối hệ thống' in toast(pg) and not hits, (toast(pg), hits))
        pg.evaluate("(u)=>saveInteg({enabled:true,baseUrl:u,provider:'KiotViet'})", URL + 'kho-khong-co')
        pg.evaluate("document.getElementById('toast').textContent='';syncStock()"); pg.wait_for_timeout(1200)
        tt = toast(pg)
        check(T('tồn kho: máy chủ kho trả 404 -> báo "Không kết nối được kho", KHÔNG "Đã đồng bộ"'), 'Không kết nối được kho' in tt and 'Đã đồng bộ' not in tt, tt)
        check(T('tồn kho: kho lỗi -> số tại máy giữ nguyên'), pg.evaluate("JSON.stringify(stockData().items)") == before)
        pg.evaluate("saveInteg({enabled:false,baseUrl:''})")
        # PIN
        check(T('PIN: máy mới -> đang ở PIN mặc định'), pg.evaluate("adminPinIsDefault()") is True)
        check(T('PIN: sai PIN -> không vào được'), login(pg, '000000') is False)
        check(T('PIN: PIN mặc định vẫn vào được (không khoá người dùng)'), login(pg, DEF_PIN) is True)
        v = view(pg)
        check(T('PIN mặc định -> chỉ hiện ô "đặt mã PIN mới", KHÔNG hiện đơn / xuất dữ liệu / kết nối kho'),
              'đang dùng mã PIN mặc định' in v and 'Xuất đơn hàng' not in v and 'Kết nối kho' not in v and 'Tất cả đơn hàng' not in v, v[:200])
        pg.evaluate("document.getElementById('toast').textContent='';adminExportOrders();adminExportCustomers()"); pg.wait_for_timeout(150)
        check(T('PIN mặc định -> gọi thẳng hàm xuất CSV cũng bị chặn'), 'Đã xuất' not in toast(pg), toast(pg))
        def first(a, c):
            pg.evaluate("([a,c])=>{document.getElementById('admpin_first').value=a;document.getElementById('admpin_first2').value=c;adminSetFirstPin();}", [a, c]); pg.wait_for_timeout(120)
            return pg.evaluate("adminPinIsDefault()")
        check(T('đặt PIN: dãy liên tiếp 123456 bị từ chối'), first('123456', '123456') is True)
        check(T('đặt PIN: lặp 111111 bị từ chối'), first('111111', '111111') is True)
        check(T('đặt PIN: dùng lại PIN mặc định bị từ chối'), first(DEF_PIN, DEF_PIN) is True)
        check(T('đặt PIN: ngắn hơn 6 ký tự bị từ chối'), first('4829', '4829') is True)
        check(T('đặt PIN: 2 lần nhập không khớp bị từ chối'), first('482913', '482914') is True)
        check(T('đặt PIN: PIN hợp lệ được lưu'), first('482913', '482913') is False)
        v = view(pg)
        check(T('sau khi đặt PIN -> mở đầy đủ khu quản trị'), 'Xuất đơn hàng' in v and 'Kết nối kho' in v, v[:160])
        st = storage_values(pg)
        rec = json.loads(st.get('nt_admin_pin_h') or '{}')
        check(T('PIN lưu dạng băm SHA-256 + muối (khớp sha256(muối:PIN))'), len(rec.get('s', '')) == 32 and rec.get('h') == sha(rec.get('s', '') + ':482913'), rec)
        check(T('KHÔNG còn PIN chữ trơn trong localStorage'), 'nt_admin_pin' not in st and not any('482913' in (x or '') for x in st.values()))
        pg.evaluate("adminLogout()"); pg.wait_for_timeout(120)
        check(T('PIN mặc định hết hiệu lực sau khi đổi'), login(pg, DEF_PIN) is False)
        check(T('PIN mới vào được, vào thẳng khu đầy đủ'), login(pg, '482913') is True and 'Xuất đơn hàng' in view(pg))
        check(T('đổi PIN: sai PIN hiện tại -> từ chối'), pg.evaluate("adminChangePin('999999','739102')") is False)
        check(T('đổi PIN: đúng PIN hiện tại -> đổi được, PIN cũ hết hiệu lực'),
              pg.evaluate("adminChangePin('482913','739102')") is True and pg.evaluate("adminPinOk('739102')") and not pg.evaluate("adminPinOk('482913')"))
        errs[:] = [e for e in errs if 'Response served by service worker' not in e]
        check(T('không lỗi JS (máy mới)'), not errs, errs)
        ctx.close()
        # ---- máy đã đặt PIN riêng ở bản cũ (chữ trơn qua lsSet) -> tự chuyển băm, vẫn vào được, không bị bắt đổi
        ctx, pg, errs, _ = open_ctx(b, "if(!sessionStorage.getItem('_seed')){sessionStorage.setItem('_seed','1');localStorage.setItem('nt_admin_pin',JSON.stringify('1357'));}")
        st = storage_values(pg)
        check(T('PIN cũ chữ trơn tự chuyển sang băm ngay khi mở app, khoá cũ bị xoá'), 'nt_admin_pin' not in st and 'nt_admin_pin_h' in st and not any(x in ('"1357"', '1357') for x in st.values()), list(st.keys()))
        check(T('PIN cũ (4 số) vẫn vào được, không bị bắt đổi'), login(pg, '1357') is True and 'Xuất đơn hàng' in view(pg))
        errs[:] = [e for e in errs if 'Response served by service worker' not in e]
        check(T('không lỗi JS (máy PIN cũ)'), not errs, errs)
        ctx.close()
        # ---- máy đặt tay PIN mặc định dạng thô + đang nhớ đăng nhập -> không bị khoá, phải đặt PIN mới
        ctx, pg, errs, _ = open_ctx(b, "if(!sessionStorage.getItem('_seed')){sessionStorage.setItem('_seed','1');localStorage.setItem('nt_admin_pin','" + DEF_PIN + "');localStorage.setItem('nt_admin_on','true');}")
        pg.evaluate("go('admin');draw()"); pg.wait_for_timeout(150)
        v = view(pg)
        check(T('đang nhớ đăng nhập + PIN mặc định thô -> hiện ô đặt PIN mới (không khoá ngoài, không lộ đơn)'), 'đang dùng mã PIN mặc định' in v and 'Xuất đơn hàng' not in v, v[:160])
        check(T('khoá PIN thô cũ đã bị xoá'), 'nt_admin_pin' not in storage_values(pg))
        pg.evaluate("document.getElementById('admpin_first').value='605182';document.getElementById('admpin_first2').value='605182';adminSetFirstPin()"); pg.wait_for_timeout(150)
        check(T('đặt PIN mới không cần nhớ PIN mặc định -> vào khu đầy đủ'), 'Xuất đơn hàng' in view(pg))
        errs[:] = [e for e in errs if 'Response served by service worker' not in e]
        check(T('không lỗi JS (máy PIN thô)'), not errs, errs)
        ctx.close(); b.close()
srv.shutdown(); shutil.rmtree(d, ignore_errors=True)
print(f'TỔNG {sum(res)} / {len(res)}')
sys.exit(0 if all(res) else 1)
