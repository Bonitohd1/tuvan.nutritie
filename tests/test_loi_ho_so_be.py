"""Phép thử Nutritie 13/10/2026 — các lỗi hồ sơ bé do agent test tìm ra (đều TÁI HIỆN được trên bản trước khi sửa):
 N1 0:00–6:59 giờ VN 'hôm nay' bị coi là tương lai · N2 ngày đo trước ngày sinh · N3/V8 2 bé cùng SĐT + tên bị gộp · V3 tên có dấu " làm hỏng ô sửa
 V4 localStorage chặn mà vẫn báo 'Đã thêm' · V5 SĐT còn trong nháp khi KHÔNG đồng ý · V6 số đo vô lý (cân 500kg, cao 0) · V2 sinh non
 V7 số đo lệch xa chuẩn · V9 số đo đã sửa rồi xoá 'sống lại' · V10 cảnh báo giảm cân theo số liền trước · ageLabel làm tròn lên
 dữ liệu localStorage hỏng · tên dài không dấu cách tràn ngang.
Dùng: python tests/test_loi_ho_so_be.py [thư-mục]   (chạy trên bản cũ phải ĐỎ)"""
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


ISO = "(a)=>{const d=new Date();d.setDate(d.getDate()-a);return d.getFullYear()+'-'+('0'+(d.getMonth()+1)).slice(-2)+'-'+('0'+d.getDate()).slice(-2)}"
ISOM = "(a)=>{const d=new Date();d.setMonth(d.getMonth()-a);return d.getFullYear()+'-'+('0'+(d.getMonth()+1)).slice(-2)+'-'+('0'+d.getDate()).slice(-2)}"


def fresh(ctx, errs, clock=None):
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errs.append(str(e)[:200]))
    pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith('http://127.0.0.1') else r.abort())
    if clock:
        pg.clock.set_fixed_time(clock)
    pg.goto(URL)
    pg.wait_for_function("document.getElementById('splash').classList.contains('hide')", timeout=30000)
    pg.wait_for_timeout(400)
    pg.evaluate("localStorage.removeItem(BB_KEY);localStorage.removeItem(MEA_KEY);window.__t=[];var __o=toast;toast=function(m){__t.push(String(m));__o(m)};window.confirm=function(){return true}")
    return pg


def add_baby(pg, ten, dob, gt='Trai', phone=None):
    pg.evaluate("""([ten,dob,gt,ph])=>{S.growth.editBaby=null;S.bf={ten:ten,ngaySinh:dob,gioiTinh:gt,consent:ph?true:false,phone:ph||''};S.growth.addingBaby=true;submitBaby();}""", [ten, dob, gt, phone])
    pg.wait_for_timeout(100)


def add_meas(pg, bid, date, w, h=''):
    pg.evaluate("""([bid,d,w,h])=>{S.growth.baby=bid;S.growth.edit=null;S.gf={ngayDo:d,canNang:String(w),chieuCao:String(h)};submitMeasure();}""", [bid, date, w, h])
    pg.wait_for_timeout(100)


def last_toast(pg):
    return pg.evaluate("__t.length?__t[__t.length-1]:''")


with sync_playwright() as p:
    for eng in ('chromium', 'webkit'):
        b = getattr(p, eng).launch()
        ctx = b.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True, timezone_id='Asia/Ho_Chi_Minh')
        ctx.add_init_script("localStorage.setItem('nt_pg', JSON.stringify('PG01'))")
        errs = []
        T = lambda s: f'[{eng}] ' + s

        # ===== N1: 03:00 giờ VN, ngày hôm nay =====
        pg = fresh(ctx, errs, '2026-10-13T03:00:00+07:00')
        today = pg.evaluate("nowISO()")
        check(T('đồng hồ giả 03:00 13/10 giờ VN: nowISO = 2026-10-13'), today == '2026-10-13', today)
        add_baby(pg, 'Bo', today)
        check(T('N1: lưu được bé sinh HÔM NAY lúc 03:00'), pg.evaluate("babies().length") == 1, last_toast(pg))
        bid = pg.evaluate("babies()[0]&&babies()[0].id")
        add_meas(pg, bid, today, 3.4, 50)
        check(T('N1: lưu được số đo HÔM NAY lúc 03:00'), pg.evaluate("measures().length") == 1, last_toast(pg))
        pg.evaluate("S.user={obj:'tre_1_10',dob:nowISO(),consent:false,hist:[]}")
        check(T('N1: tư vấn — ngày sinh hôm nay hợp lệ lúc 03:00'), pg.evaluate("kidDobOK()"))
        pg.evaluate("S.user.dob='2026-10-14'")
        check(T('ngày MAI vẫn bị chặn'), not pg.evaluate("kidDobOK()"))
        pg.close()

        pg = fresh(ctx, errs)
        # ===== N2: ngày đo trước ngày sinh + sửa ngày sinh =====
        add_baby(pg, 'Mi', pg.evaluate(ISOM, 6))
        bid = pg.evaluate("babies()[0].id")
        add_meas(pg, bid, pg.evaluate(ISOM, 7), 6)
        check(T('N2: ngày đo TRƯỚC ngày sinh bị chặn, có lời báo'), pg.evaluate("measures().length") == 0 and 'trước ngày sinh' in last_toast(pg), last_toast(pg))
        add_meas(pg, bid, pg.evaluate(ISOM, 3), 6.5)
        pg.evaluate("([id,dob])=>{S.growth.editBaby=id;S.bf={ten:'Mi',ngaySinh:dob,gioiTinh:'Trai'};S.growth.addingBaby=true;submitBaby();}", [bid, pg.evaluate(ISOM, 1)])
        check(T('N2: dời ngày sinh SAU số đo đã có bị chặn'), 'TRƯỚC ngày sinh' in last_toast(pg) and pg.evaluate("babies()[0].ngaySinh") == pg.evaluate(ISOM, 6), last_toast(pg))
        far = pg.evaluate("(()=>{S.growth.editBaby=null;S.bf={ten:'Cu',ngaySinh:'1900-01-01',gioiTinh:'Trai',consent:false};submitBaby();return babies().length})()")
        check(T('ngày sinh 1900 bị chặn'), far == 1 and 'quá xa' in last_toast(pg), last_toast(pg))

        # ===== N3/V8: trùng SĐT + tên =====
        pg.evaluate("localStorage.removeItem(BB_KEY);localStorage.removeItem(MEA_KEY)")
        add_baby(pg, 'Bo', pg.evaluate(ISOM, 8), 'Trai', '0912345678')
        add_baby(pg, 'bé BO', pg.evaluate(ISOM, 30), 'Gái', '0912345678')
        check(T('V8: bé thứ 2 cùng SĐT + cùng tên (khác ngày sinh) bị chặn, báo cách phân biệt'), pg.evaluate("babies().length") == 1 and 'KHÁC TÊN' in last_toast(pg), last_toast(pg))
        add_baby(pg, 'Bo nhỏ', pg.evaluate(ISOM, 30), 'Gái', '0912345678')
        check(T('khác tên thì cho tạo (2 bé cùng SĐT)'), pg.evaluate("babies().length") == 2)
        add_baby(pg, 'bo', pg.evaluate(ISOM, 8), 'Trai', '0912345678')
        check(T('đúng cùng bé (tên + ngày sinh + SĐT) cũng không tạo trùng'), pg.evaluate("babies().length") == 2, last_toast(pg))
        # tư vấn: 2 khách cùng SĐT, tên trống
        pg.evaluate("localStorage.removeItem(BB_KEY);localStorage.removeItem(MEA_KEY)")
        pg.evaluate("""([d1,d2])=>{startTV();S.user.obj='tre_0_12';S.user.gender='Nam';S.user.dob=d1;S.user.consent=true;S.user.phone='0912345678';S.user.name='';S.step=1;next1();
          S.m.w='8.4';S.m.h='';S._gSaved=false;consultSaveGrowth();
          startTV();S.user.obj='tre_1_10';S.user.gender='Nam';S.user.dob=d2;S.user.consent=true;S.user.phone='0912345678';S.user.name='';S.step=1;next1();}""", [pg.evaluate(ISOM, 8), pg.evaluate(ISOM, 30)])
        check(T('N3: tư vấn khách thứ 2 cùng SĐT, tên trống, bé khác ngày sinh: bị chặn ở bước 1 (không đè hồ sơ bé 1)'),
              pg.evaluate("S.step") == 1 and pg.evaluate("babies().length") == 1 and pg.evaluate("babies()[0].gioiTinh") == 'Trai' and 'KHÁC TÊN' in last_toast(pg), last_toast(pg))

        # ===== V3: tên có dấu nháy =====
        pg.evaluate("localStorage.removeItem(BB_KEY)")
        pg.evaluate("window.__xss=0")
        add_baby(pg, 'Bo" autofocus onfocus="window.__xss=1" x="', pg.evaluate(ISOM, 5))
        pg.evaluate("go('growth');editBaby(babies()[0].id)"); pg.wait_for_timeout(250)
        val = pg.evaluate("(()=>{const i=[...document.querySelectorAll('#view input')].find(x=>x.getAttribute('placeholder')==='VD: Bé Bo');return i?i.value:null})()")
        check(T('V3: ô sửa tên hiện ĐỦ tên có dấu "'), val == 'Bo" autofocus onfocus="window.__xss=1" x="', val)
        check(T('V3: không chèn được thuộc tính (onfocus) qua tên bé'), pg.evaluate("window.__xss") == 0 and pg.evaluate("!document.querySelector('#view input[onfocus]')"))
        pg.evaluate("S.growth.addingBaby=false;S.growth.editBaby=null")

        # ===== V4: localStorage bị chặn =====
        pg.evaluate("localStorage.removeItem(BB_KEY)")
        pg.evaluate("(()=>{const o=Storage.prototype.setItem;Storage.prototype.setItem=function(k,v){if(String(k).indexOf('nt_')===0)throw new DOMException('quota','QuotaExceededError');return o.call(this,k,v)};return 1})()")
        add_baby(pg, 'Ti', pg.evaluate(ISOM, 5))
        check(T('V4: không lưu được thì báo RÕ "CHƯA được lưu", không báo thành công'), 'CHƯA được lưu' in last_toast(pg), last_toast(pg))
        pg.close()

        # ===== V5: SĐT trong nháp khi không đồng ý =====
        pg = fresh(ctx, errs)
        pg.evaluate("""([d])=>{startTV();S.user.obj='tre_1_10';S.user.gender='Nam';S.user.dob=d;S.user.consent=true;S.user.phone='0912345678';S.step=1;draw();S.user.consent=false;draw();}""", [pg.evaluate(ISOM, 60)])
        pg.wait_for_timeout(100)
        sess = pg.evaluate("localStorage.getItem(SESS_KEY)||''")
        check(T('V5: khách KHÔNG đồng ý -> nháp phiên không còn SĐT'), '0912345678' not in sess and 'nt_session' != '', sess[:120])

        # ===== V6: số đo vô lý =====
        for lbl, obj, m in [('cân 500kg', 'tre_0_12', {'months': '8', 'w': '500', 'h': '70'}), ('cân 0', 'tre_0_12', {'months': '8', 'w': '0', 'h': '70'}),
                            ('cao 0 (6 tuổi)', 'tre_1_10', {'age': '6', 'w': '20', 'h': '0'}), ('cao 300', 'tre_1_10', {'age': '6', 'w': '20', 'h': '300'})]:
            pg.evaluate("([o,m])=>{startTV();S.user.obj=o;S.user.hist=['Không có'];S.m=m;S.step=2;draw();next2();}", [obj, m])
            check(T(f'V6: tư vấn {lbl} bị chặn ở bước 2, có lời báo'), pg.evaluate("S.step") == 2 and ('phải trong khoảng' in last_toast(pg)), (pg.evaluate("S.step"), last_toast(pg)))
        pg.evaluate("S.user.obj='tre_0_12';S.m={months:'8',w:'8.5',h:'70'};next2()")
        check(T('V6: số đo hợp lý vẫn qua bước 3'), pg.evaluate("S.step") == 3)

        # ===== V2: sinh non =====
        pg.evaluate("startTV();S.user.obj='tre_0_12';S.step=1;draw()"); pg.wait_for_timeout(100)
        el = pg.evaluate("(()=>{const i=[...document.querySelectorAll('#view input[type=number]')].find(x=>/VD: 4/.test(x.placeholder));return !!i})()")
        check(T('V2: có ô "tuần sinh sớm" với gợi ý rõ'), el)
        pg.evaluate("(()=>{const i=[...document.querySelectorAll('#view input[type=number]')].find(x=>/VD: 4/.test(x.placeholder));i.value='32';i.dispatchEvent(new Event('input'));i.dispatchEvent(new Event('change'));})()")
        check(T('V2: nhập 32 (tuổi thai) bị từ chối + giải thích, không áp dụng'), pg.evaluate("pretermWeeks()") == 0 and 'TUẦN SINH SỚM' in last_toast(pg), last_toast(pg))
        pg.evaluate("S.user.preterm='8'")
        check(T('V2: 8 tuần hợp lệ'), pg.evaluate("pretermWeeks()") == 8)
        dobp = pg.evaluate(ISOM, 3)
        pg.evaluate("""([d])=>{S.user.dob=d;S.user.consent=true;S.user.phone='0911222333';S.user.name='Su';S.user.gender='Nam';S.user.hist=['Không có'];syncKidAge();S.m.w='5.2';S.m.h='';S._gSaved=false;S._gBabyId='';consultSaveGrowth();}""", [dobp])
        check(T('V2: số tuần sinh non được LƯU vào hồ sơ bé (và gửi máy chủ qua preterm_weeks)'), pg.evaluate("(babies()[0]||{}).snt") == 8, pg.evaluate("babies()[0]"))
        z1 = pg.evaluate("(()=>{const b=babies()[0];return babyAgeC(b,nowISO())})()")
        z0 = pg.evaluate("(()=>{const b=babies()[0];return ageMo(b.ngaySinh,nowISO())})()")
        check(T('V2: biểu đồ dùng tuổi hiệu chỉnh (nhỏ hơn tuổi thật ~1,8 tháng)'), 1.5 < (z0 - z1) < 2.1, (z0, z1))
        pg.evaluate("(()=>{const b=babies()[0];b.ngaySinh=ISO25();})".replace('ISO25()', "(function(){const d=new Date();d.setMonth(d.getMonth()-25);return d.toISOString().slice(0,10)})()"))
        z25 = pg.evaluate("(()=>{const b={ngaySinh:(function(){const d=new Date();d.setMonth(d.getMonth()-25);return d.toISOString().slice(0,10)})(),snt:8};return [babyAgeC(b,nowISO()),ageMo(b.ngaySinh,nowISO())]})()")
        check(T('V2: quá 24 tháng tuổi thật thì HẾT hiệu chỉnh'), abs(z25[0] - z25[1]) < 1e-9, z25)
        pg.close()

        # ===== V7, V9, V10 =====
        pg = fresh(ctx, errs)
        add_baby(pg, 'Ly', pg.evaluate(ISOM, 3))
        bid = pg.evaluate("babies()[0].id")
        add_meas(pg, bid, pg.evaluate(ISO, 0), 95)
        check(T('V7: bé 3 tháng 95kg (gõ nhầm 9,5): hỏi lại, chưa lưu'), pg.evaluate("measures().length") == 0 and 'lệch rất xa' in last_toast(pg), last_toast(pg))
        pg.evaluate("submitMeasure()")
        check(T('V7: bấm Lưu lần nữa (xác nhận đúng) thì lưu'), pg.evaluate("measures().length") == 1)
        pg.evaluate("localStorage.removeItem(MEA_KEY)")
        add_meas(pg, bid, pg.evaluate(ISO, 20), 6.0)
        add_meas(pg, bid, pg.evaluate(ISO, 10), 6.6)
        add_meas(pg, bid, pg.evaluate(ISO, 40), 5.0)
        check(T('V10: thêm số đo CŨ hơn (nhẹ hơn lần mới nhất) KHÔNG bị báo giảm cân'), pg.evaluate("measures().length") == 3, (pg.evaluate("measures().length"), last_toast(pg)))
        add_meas(pg, bid, pg.evaluate(ISO, 0), 5.0)
        check(T('V10: giảm >10% so số LIỀN TRƯỚC: cảnh báo, chưa lưu'), pg.evaluate("measures().length") == 3 and 'Cân giảm' in last_toast(pg), last_toast(pg))
        pg.evaluate("S.gf.canNang='4.2';submitMeasure()")
        check(T('V10: sửa cân thấp hơn nữa -> hỏi lại (xác nhận không "dính" sang số khác)'), pg.evaluate("measures().length") == 3 and 'Cân giảm' in last_toast(pg), last_toast(pg))
        pg.evaluate("localStorage.removeItem(MEA_KEY)")
        add_meas(pg, bid, pg.evaluate(ISO, 5), 6.0)
        mid = pg.evaluate("measures()[0].id")
        pg.evaluate("([id])=>{const m=measures();m[0].sv=1;saveMeasures(m);}", [mid])
        pg.evaluate("([id])=>{editMeasure(id);S.gf.canNang='6.2';submitMeasure();}", [mid])
        pg.evaluate("([id])=>{delMeasure(id)}", [mid])
        check(T('V9: số đo đã đồng bộ -> sửa -> xoá: vẫn ghi dấu xoá để máy chủ gỡ (không "sống lại")'), mid in (pg.evaluate("babies()[0].del") or []), pg.evaluate("babies()[0]"))

        # ===== ageLabel, dữ liệu hỏng, tên dài =====
        labs = pg.evaluate("[ageLabel(23.5),ageLabel(11.5),ageLabel(59.5),ageLabel(11.95),ageLabel(24),ageLabel(0.4)]")
        check(T('ageLabel cắt xuống: 23,5->23 tháng; 11,5->11 tháng; 59,5->4 tuổi 11 tháng; 11,95->12 tháng'), labs == ['23 tháng tuổi', '11 tháng tuổi', '4 tuổi 11 tháng', '12 tháng tuổi', '2 tuổi', '0 tháng tuổi'], labs)
        for k, v in [('nt_babies', 'null'), ('nt_babies', '{}'), ('nt_babies', '[null]'), ('nt_measures', 'null'), ('nt_measures', '[{"babyId":"x","canNang":"9.5","ngayDo":"2026-01-01"}]')]:
            pg.evaluate("([k,v])=>localStorage.setItem(k,v)", [k, v])
            pg.evaluate("go('home')"); pg.evaluate("go('growth')"); pg.wait_for_timeout(150)
        check(T('dữ liệu localStorage hỏng (null, {}, [null], cân dạng chuỗi) không làm trắng màn Tăng trưởng'), not [e for e in errs if 'toFixed' in e or 'null' in e or 'forEach' in e], errs)
        pg.evaluate("localStorage.removeItem(BB_KEY);localStorage.removeItem(MEA_KEY)")
        pg.set_viewport_size({'width': 320, 'height': 700})
        add_baby(pg, 'A' * 58, pg.evaluate(ISOM, 6))
        pg.evaluate("go('growth')"); pg.wait_for_timeout(250)
        ov = pg.evaluate("document.documentElement.scrollWidth-window.innerWidth")
        check(T('tên bé dài 58 ký tự không dấu cách: không tràn ngang ở 320px'), ov <= 0, ov)
        check(T('không lỗi JS'), not errs, errs)
        pg.close()
        b.close()

shutil.rmtree(d, ignore_errors=True)
print(f'TỔNG {sum(res)} / {len(res)}')
sys.exit(0 if all(res) else 1)
