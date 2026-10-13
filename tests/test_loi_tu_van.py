"""Phép thử Nutritie 13/10/2026 — các lỗi LUỒNG TƯ VẤN do agent test tìm ra (đều tái hiện được trên bản trước khi sửa):
 thước đo dùng bảng WHO thật (khớp biểu đồ ngay dưới) · trẻ thừa cân/béo phì KHÔNG bị gợi ý Pedia · tiểu đường chặn ở mọi nhóm (mẹ bầu, trẻ)
 · người lớn thừa cân / ăn kiêng không bị đẩy 'tăng cân' · tuổi / số đo vô lý bị chặn · ngày sinh lệch nhóm bị chặn
 · đổi đối tượng xoá dữ liệu cũ · thước đo mẹ bầu theo BMI · thước đo không làm tràn ngang · tên bé dài không phá bố cục.
Dùng: python tests/test_loi_tu_van.py [thư-mục]   (chạy trên bản cũ phải ĐỎ)"""
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


ISOM = "(a)=>{const d=new Date();d.setMonth(d.getMonth()-a);return d.getFullYear()+'-'+('0'+(d.getMonth()+1)).slice(-2)+'-'+('0'+d.getDate()).slice(-2)}"


def result(pg, obj, m, needs=None, hist=None, gender='Nam', extra=None):
    """Đặt state rồi vẽ màn kết quả; trả (text, rec)."""
    return pg.evaluate("""([obj,m,needs,hist,g,ex])=>{startTV();S.tab='tuvan';S.user.obj=obj;S.user.gender=g;S.user.hist=hist||['Không có'];S.user.name='';S.user.dob='';S.user.consent=null;S.user.phone='';S.user.preterm='';
      if(ex)Object.assign(S.user,ex);S.m=m;S.needs=needs||[];S.cls=classify();S.step=4;draw();
      var r=recommend();return {t:document.getElementById('view').textContent,ids:r.ids,why:r.why.join(' '),cls:S.cls,order:/orderFromRec/.test(document.getElementById('view').innerHTML),sci:sciAdvice()};}""",
                       [obj, m, needs, hist, gender, extra])


with sync_playwright() as p:
    for eng in ('chromium', 'webkit'):
        b = getattr(p, eng).launch()
        ctx = b.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True)
        ctx.add_init_script("localStorage.setItem('nt_pg', JSON.stringify('PG01'))")
        pg = ctx.new_page(); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)[:200]))
        pg.route('https://**', lambda r: r.abort())
        T = lambda s: f'[{eng}] ' + s
        pg.goto(URL)
        pg.wait_for_function("document.getElementById('splash').classList.contains('hide')", timeout=30000)
        pg.wait_for_timeout(500)
        pg.evaluate("window.__t=[];var __o=toast;toast=function(m){__t.push(String(m));__o(m)}")

        # ---- thước đo = WHO thật ----
        r = result(pg, 'tre_0_12', {'months': 12, 'w': 6.8, 'h': 70})
        check(T('bé trai 12 tháng 6,8kg: WHO Z -3,2 -> "Suy dinh dưỡng nặng" + banner đi khám (trước: "Nhẹ cân Z≈-2,4")'), r['cls']['label'] == 'Suy dinh dưỡng nặng' and 'Cần đưa đi khám' in r['t'], r['cls'])
        r = result(pg, 'tre_1_10', {'age': 6, 'w': 24, 'h': 112})
        check(T('bé trai 6 tuổi 24kg 112cm (BMI 19,1): WHO "Béo phì" (trước: "Bình thường")'), r['cls']['label'] == 'Béo phì' and r['cls']['status'] == 'high', r['cls'])
        r = result(pg, 'tre_1_10', {'age': 5, 'w': 15.5, 'h': 103})
        check(T('bé 5 tuổi BMI 14,6 (WHO bình thường) không còn bị gọi "Gầy"'), r['cls']['status'] != 'low' and r['cls']['label'] == 'Bình thường', r['cls'])
        sweep = pg.evaluate("""(()=>{startTV();S.user.obj='tre_0_12';var bad=[],n=0;for(var g of ['Nam','Nữ'])for(var mo=0;mo<=12;mo+=1)for(var w=2.5;w<=14;w+=0.25){S.user.gender=g;S.user.preterm='';S.m={months:mo,w:w};var c=classify(),z=whoZ('w',mo,w),zc=zClass(z,'w').lb;n++;
          var ok=(c.label===zc)||(c.label==='Nguy cơ nhẹ cân'&&zc==='Bình thường')||(c.label==='Cân nặng cao hơn chuẩn'&&zc==='Cao hơn chuẩn');if(!ok)bad.push([g,mo,w,c.label,zc]);}return {n:n,bad:bad.slice(0,3),nb:bad.length}})()""")
        check(T(f'quét {sweep["n"]} ca (giới × tháng × cân): nhãn tư vấn LUÔN khớp nhãn biểu đồ WHO'), sweep['nb'] == 0, sweep)

        # ---- trẻ thừa cân không bị gợi ý Pedia ----
        for lbl, obj, m, needs in [('7 tuổi 34kg 120cm', 'tre_1_10', {'age': 7, 'w': 34, 'h': 120}, []), ('7 tuổi 34kg + Tăng cân', 'tre_1_10', {'age': 7, 'w': 34, 'h': 120}, ['Tăng cân']),
                                   ('3 tuổi 20kg + Tăng cân', 'tre_1_10', {'age': 3, 'w': 20, 'h': 95}, ['Tăng cân'])]:
            r = result(pg, obj, m, needs)
            check(T(f'trẻ {lbl} (trên chuẩn): KHÔNG gợi ý Pedia, KHÔNG nút lên đơn'), 'pedia' not in r['ids'] and not r['order'], (r['ids'], r['cls']['label']))
        r = result(pg, 'tre_1_10', {'age': 4, 'w': 11, 'h': 100})
        check(T('trẻ nhẹ cân vẫn gợi ý Pedia (không hồi quy)'), r['ids'][:1] == ['pedia'] and r['order'], r['ids'])
        r = result(pg, 'tre_1_10', {'age': 7, 'w': 34, 'h': 120}, ['Tăng chiều cao'])
        check(T('trẻ trên chuẩn muốn tăng chiều cao -> Grow IQ, không Pedia'), r['ids'] == ['growiq'], r['ids'])

        # ---- tiểu đường ở MỌI nhóm ----
        r = result(pg, 'pregnant', {'pw': 50, 'h': 160}, [], ['Tiểu đường'], 'Nữ')
        check(T('mẹ bầu + tiểu đường: KHÔNG Mama A+, KHÔNG nút lên đơn, giải thích rõ'), r['ids'] == [] and not r['order'] and 'KHÔNG' in r['why'] and 'GI thấp' in r['sci'], (r['ids'], r['order'], r['why'][:100]))
        r = result(pg, 'tre_1_10', {'age': 4, 'w': 16, 'h': 100}, [], ['Tiểu đường'])
        check(T('trẻ 4 tuổi + tiểu đường: không gợi ý sữa, không nút lên đơn'), r['ids'] == [] and not r['order'], (r['ids'], r['order']))
        r = result(pg, 'tre_0_12', {'months': 8, 'w': 8.5, 'h': 70}, [], ['Tiểu đường'])
        check(T('bé 0–12 tháng + tiểu đường: không nút lên đơn'), r['ids'] == [] and not r['order'], (r['ids'], r['order']))
        r = result(pg, 'pregnant', {'pw': 50, 'h': 160}, [], ['Tiền sản giật'], 'Nữ')
        check(T('mẹ bầu + tiền sản giật (không tiểu đường): vẫn Mama (chỉ cảnh báo khám bác sĩ như cũ)'), r['ids'] == ['mama'], r['ids'])

        # ---- người lớn ----
        r = result(pg, 'adult', {'w': 95, 'h': 165}, ['Ăn kiêng / kiểm soát cân nặng'])
        check(T('người lớn BMI 34,9 + ăn kiêng: không "Người lớn gầy / tăng cân", không đẩy Canxi Pro'), r['ids'] == [] and 'gầy' not in r['sci'] and 'BMI trên chuẩn' in r['sci'] and not r['order'], (r['ids'], r['sci'][:80]))
        r = result(pg, 'adult', {'w': 95, 'h': 165}, ['Loãng xương'])
        check(T('người lớn thừa cân nhưng khách chọn Loãng xương: vẫn Canxi Pro (nhu cầu thật)'), r['ids'] == ['canxipro'], r['ids'])
        r = result(pg, 'adult', {'w': 45, 'h': 165})
        check(T('người lớn gầy (BMI 16,5): vẫn Canxi Pro + lời khuyên tăng cân'), r['ids'] == ['canxipro'] and 'gầy' in r['sci'], (r['ids'], r['sci'][:60]))
        r = result(pg, 'adult', {'w': 58, 'h': 165})
        check(T('người lớn BMI chuẩn: Canxi Pro, lời khuyên KHÔNG nói "gầy / cần tăng cân"'), r['ids'] == ['canxipro'] and 'gầy' not in r['sci'], (r['ids'], r['sci'][:80]))

        # ---- kiểm khoảng tuổi / số đo / ngày sinh ----
        def try_next2(obj, m):
            return pg.evaluate("""([o,m])=>{startTV();S.user.obj=o;S.user.hist=['Không có'];S.m=m;S.step=2;draw();window.__t=[];next2();return [S.step,__t.length?__t[__t.length-1]:'']}""", [obj, m])
        for lbl, obj, m, key in [('trẻ 25 tuổi', 'tre_1_10', {'age': 25, 'w': 20, 'h': 110}, '1 đến 10 tuổi'), ('trẻ -3 tuổi', 'tre_1_10', {'age': -3, 'w': 20, 'h': 110}, '1 đến 10 tuổi'),
                                 ('bé 30 tháng ở nhóm 0–12', 'tre_0_12', {'months': 30, 'w': 8}, '0 đến 12 tháng'), ('bé -2 tháng', 'tre_0_12', {'months': -2, 'w': 8}, '0 đến 12 tháng'),
                                 ('mẹ bầu pw 0', 'pregnant', {'pw': 0, 'h': 0}, '30–200'), ('người lớn cao 500', 'adult', {'w': 60, 'h': 500}, 'phải trong khoảng')]:
            st = try_next2(obj, m)
            check(T(f'{lbl}: bị chặn ở bước 2 kèm lời giải thích'), st[0] == 2 and key in st[1], st)
        st = try_next2('pregnant', {'pw': 55, 'h': 160})
        check(T('mẹ bầu số liệu hợp lý: qua bước 3'), st[0] == 3, st)
        quet = pg.evaluate("""(()=>{var bad=[];[['tre_1_10',{age:6,w:20,h:0}],['adult',{w:0,h:170}],['pregnant',{pw:0,h:0}],['tre_0_12',{months:8,w:0}]].forEach(function(x){startTV();S.user.obj=x[0];S.user.hist=['Không có'];S.m=x[1];S.step=2;next2();if(S.step!==2)bad.push(x[0])});return bad})()""")
        check(T('không còn đường nào ra "Infinity" / "NaN" từ số đo vô lý'), quet == [], quet)

        # ngày sinh lệch nhóm
        for obj, mo, key in [('tre_0_12', 36, 'Trẻ trên 1 tuổi'), ('tre_1_10', 4, 'chưa tròn 1 tuổi'), ('tre_1_10', 15 * 12, 'trên 11 tuổi')]:
            dob = pg.evaluate(ISOM, mo)
            st = pg.evaluate("""([o,dob])=>{startTV();S.user.obj=o;S.user.dob=dob;S.user.consent=false;S.user.hist=['Không có'];S.step=1;window.__t=[];next1();return [S.step,__t.length?__t[__t.length-1]:'']}""", [obj, dob])
            check(T(f'{obj}, ngày sinh cách {mo} tháng: chặn ở bước 1 ("{key}")'), st[0] == 1 and key in st[1], st)

        # ---- đổi đối tượng giữa chừng ----
        st = pg.evaluate("""()=>{startTV();S.user.obj='tre_0_12';S.user.name='Bo';S.user.preterm='6';S.user.dob=(function(){var d=new Date();d.setMonth(d.getMonth()-5);return d.toISOString().slice(0,10)})();S.user.consent=true;S.user.phone='0912345678';S.m={months:5,w:6.5,h:62};S.needs=['Tăng chiều cao'];
          setObj('adult');S.m={w:60,h:170};S.cls=classify();S.step=4;draw();var t=document.getElementById('view').textContent;return {name:S.user.name,dob:S.user.dob,phone:S.user.phone,needs:S.needs.length,t:t}}""")
        check(T('đổi từ bé 0–12 tháng sang người lớn: xoá tên bé, ngày sinh, SĐT, sinh non, nhu cầu cũ'),
              st['name'] == '' and st['dob'] == '' and st['phone'] == '' and st['needs'] == 0 and 'sinh non' not in st['t'] and 'Tăng chiều cao' not in st['t'], {k: st[k] for k in ('name', 'dob', 'phone', 'needs')})
        st = pg.evaluate("""()=>{startTV();S.user.obj='tre_0_12';S.m={months:5,w:6.5};setObj('tre_1_10');return JSON.stringify(S.m)}""")
        check(T('đổi giữa 2 nhóm trẻ: ô số đo bước 2 được làm trống'), st == '{}', st)

        # ---- thước đo mẹ bầu theo BMI ----
        for lbl, pw, h, cls_ in [('BMI 13,7 (gầy)', 35, 160, 'b-low'), ('BMI 21 (chuẩn)', 54, 160, 'b-ok'), ('BMI 35 (béo phì)', 90, 160, 'b-high')]:
            r = pg.evaluate("""([pw,h])=>{startTV();S.user.obj='pregnant';S.user.hist=['Không có'];S.m={pw:pw,h:h};S.cls=classify();S.step=4;draw();var b=document.querySelector('#view .gauge .badge');return [b?b.className:'',document.querySelector('#view .gauge .ginterp p').textContent]}""", [pw, h])
            check(T(f'mẹ bầu {lbl}: thước đo tô màu theo BMI, không luôn "Đạt chuẩn"'), cls_ in r[0] and 'Đạt chuẩn' not in r[1], r)

        # ---- không tràn ngang ----
        for vw in (320, 360, 390, 430):
            pg.set_viewport_size({'width': vw, 'height': 760})
            worst = 0
            for obj, m in [('tre_1_10', {'age': 3, 'w': 20, 'h': 95}), ('tre_0_12', {'months': 6, 'w': 12}), ('tre_1_10', {'age': 2, 'w': 18, 'h': 85}), ('tre_0_12', {'months': 3, 'w': 3.2})]:
                result(pg, obj, m)
                worst = max(worst, pg.evaluate("document.documentElement.scrollWidth-window.innerWidth"))
            check(T(f'thước đo ở Z cực đoan (Z>3 / Z<-3) không tràn ngang ở {vw}px'), worst <= 0, worst)
        pg.set_viewport_size({'width': 320, 'height': 700})
        r = result(pg, 'tre_1_10', {'age': 5, 'w': 18, 'h': 105}, extra={'name': 'B' * 120})
        check(T('tên bé 120 ký tự liền ở bước kết quả: không tràn ngang ở 320px'), pg.evaluate("document.documentElement.scrollWidth-window.innerWidth") <= 0, pg.evaluate("document.documentElement.scrollWidth-window.innerWidth"))
        facts = pg.evaluate("(()=>{var o={};PRODUCTS.forEach(function(p){o[p.id]=(p.facts||'')+' '+(p.claims||[]).join(' ')});o.sci=SCI.infant;return o})()")
        check(T('số liệu sản phẩm khớp ẢNH BẢNG THÀNH PHẦN (đã đối chiếu từng con số): Baby ARA 11,5 / Choline 52 / HMO 10,8 / Canxi 406, không Lactoferrin'),
              all(x in facts['baby'] for x in ('ARA 11,5mg', 'Choline 52mg', "HMO 10,8mg", 'Canxi 406mg')) and 'Lactoferrin' not in facts['baby'] and 'Lactoferrin' not in facts['sci'], facts['baby'][:160])
        check(T('Grow IQ: D3 116IU (không 248), không còn "cao nhất dòng" cho Canxi/DHA (Bio có Canxi 676mg; Colostrum DHA cao hơn)'), 'D3 116IU' in facts['growiq'] and '248' not in facts['growiq'] and 'cao nhất' not in facts['growiq'], facts['growiq'])
        check(T('Pedia: Canxi 386mg/100g (không 453)'), 'Canxi 386mg' in facts['pedia'] and '453' not in facts['pedia'], facts['pedia'][:120])
        check(T('lời khuyên 0–12 tháng không còn con số "60–70 kcal/kg/ngày" sai'), '60–70 kcal/kg' not in facts['sci'], facts['sci'][:80])
        check(T('không lỗi JS'), not errs, errs)
        b.close()

shutil.rmtree(d, ignore_errors=True)
print(f'TỔNG {sum(res)} / {len(res)}')
sys.exit(0 if all(res) else 1)
