"""Phép thử màn quét Nutritie (10/10/2026). Dùng: python test_nutritie_scan.py <thư-mục-tuvan.nutritie> (chạy trên BẢN CŨ phải đỏ)."""
import sys, os, json, threading, http.server, socketserver, functools, shutil, tempfile, time
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


PROBE = """()=>{const sc=document.getElementById('scan'),arc=document.getElementById('scarc'),pc=document.getElementById('scpct'),st=document.getElementById('scsteps');
 const cs=getComputedStyle(sc);
 return {cls:sc.className,vis:cs.visibility,op:parseFloat(cs.opacity),pct:pc?pc.textContent:null,off:arc?parseFloat(arc.style.strokeDashoffset):null,
  ok:st?[...st.children].filter(l=>l.className==='ok').length:-1,act:st?[...st.children].findIndex(l=>l.className==='act'):-2,
  lit:document.querySelectorAll('.sc-dot.lit').length,tx:document.getElementById('sctx').textContent,
  head:(document.getElementById('schead')||{style:{}}).style.transform||''}}"""


def prep(pg, obj='tre_1_10', m=None):
    m = m or {'age': 3, 'w': 14, 'h': 95}
    pg.evaluate("""([obj,m])=>{S.tab='tuvan';S.user.obj=obj;S.user.gender='Nam';S.m=m;S.cls=classify();S.needs=['Tăng cân'];S.step=3;
      window.__d4=0;if(!window.__wrapped){window.__wrapped=1;var _d=window.draw;window.draw=function(){if(S.step===4)window.__d4=(window.__d4||0)+1;return _d.apply(this,arguments);};}
      draw();}""", [obj, m])
    pg.wait_for_timeout(200)


with sync_playwright() as p:
    b = p.chromium.launch()
    for w, h in [(390, 844), (375, 667), (360, 640)]:
        ctx = b.new_context(viewport={'width': w, 'height': h}, is_mobile=True, has_touch=True)
        ctx.add_init_script("localStorage.setItem('nt_pg', JSON.stringify('PG01'))")
        pg = ctx.new_page()
        errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)[:200]))
        pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith('http://127.0.0.1') else r.abort())
        T = lambda s: f'[{w}x{h}] ' + s
        pg.goto(URL)
        pg.wait_for_function("document.getElementById('splash').classList.contains('hide')", timeout=15000)
        pg.wait_for_timeout(500)
        prep(pg)
        check(T('trước khi quét: màn quét ẩn'), pg.evaluate(PROBE)['vis'] == 'hidden')
        # bấm ĐÚP rất nhanh vào "Xem kết quả"
        pg.evaluate("window.__fr=[];(function f(t){window.__fr.push(t);if(window.__fr.length<400)requestAnimationFrame(f);})(performance.now())")
        btn = pg.locator('button.btnN:has-text("Xem kết quả")')
        btn.click(); btn.dispatch_event('click')
        samples = []
        t0 = time.time()
        shot = {0.5: False, 1.5: False, 2.6: False}
        while time.time() - t0 < 6.0:
            s = pg.evaluate(PROBE)
            s['t'] = round(time.time() - t0, 2)
            samples.append(s)
            for k in shot:
                if not shot[k] and s['t'] >= k and w == 390:
                    pg.screenshot(path=os.path.join(_ANH, f'scan_{k}.png')); shot[k] = True
            if s['cls'].find('ok') >= 0 and not shot.get('ok') and w == 390:
                pg.screenshot(path=os.path.join(_ANH, 'scan_ok.png')); shot['ok'] = True
            pg.wait_for_timeout(60)
        pcts = [int(s['pct'].replace('%', '')) for s in samples if s['pct'] and s['vis'] == 'visible']
        check(T('% tăng đều, KHÔNG BAO GIỜ giật lùi'), pcts and all(b2 >= a for a, b2 in zip(pcts, pcts[1:])), pcts[:40])
        check(T('% đi từ ~0 tới 100'), pcts and pcts[0] <= 3 and pcts[-1] == 100, (pcts[:3], pcts[-3:]))
        check(T('số % có nhiều mức trung gian (mượt, không nhảy bậc)'), len(set(pcts)) >= 25, len(set(pcts)))
        offs = [s['off'] for s in samples if s['off'] is not None and s['vis'] == 'visible']
        check(T('vòng tiến độ chạy theo % (offset giảm dần 100 → 0)'), offs and offs[0] >= 90 and offs[-1] == 0 and all(b2 <= a + 0.01 for a, b2 in zip(offs, offs[1:])), (offs[:3], offs[-3:]))
        oks = [s['ok'] for s in samples if s['vis'] == 'visible']
        check(T('danh sách bước: tick dần từ 0 tới 5, không lùi'), oks and oks[0] <= 1 and oks[-1] == 5 and all(b2 >= a for a, b2 in zip(oks, oks[1:])), oks[:50:5])
        check(T('đủ 5 bước đều từng là "đang làm"'), len({s['act'] for s in samples if s['act'] >= 0}) == 5, sorted({s['act'] for s in samples}))
        check(T('4 biểu tượng quanh linh vật sáng dần tới đủ 4'), max(s['lit'] for s in samples) == 4)
        okstate = [s for s in samples if 'ok' in s['cls'].split()]
        check(T('hoàn tất: có trạng thái "ok" (vòng xanh + dấu tích) và chữ "Hoàn tất"'), okstate and any('Hoàn tất' in s['tx'] for s in okstate), okstate[:1])
        last = samples[-1]
        check(T('kết thúc: màn quét mờ hẳn + ẩn'), last['vis'] == 'hidden' and last['op'] <= 0.05, last)
        check(T('sang bước kết quả (bước 4)'), pg.evaluate("S.step") == 4)
        check(T('bấm đúp: kết quả chỉ vẽ MỘT lần (không chạy done() hai lần)'), pg.evaluate("window.__d4") == 1, pg.evaluate("window.__d4"))
        chips = pg.evaluate("document.getElementById('scchips').textContent")
        check(T('số đo THẬT của khách hiện ở màn quét: 3 tuổi · 14 kg · 95 cm'), '3 tuổi' in chips and '14 kg' in chips and '95 cm' in chips, chips)
        if h <= 720:
            pass
        # kích thước: mọi thứ nằm gọn trong màn hình lúc đang quét
        pg.evaluate("S.step=3;draw();window.__d4=0"); pg.wait_for_timeout(150)
        pg.locator('button.btnN:has-text("Xem kết quả")').click(); pg.wait_for_timeout(1700)
        fit = pg.evaluate("""()=>{const q=s=>document.querySelector(s).getBoundingClientRect();const st=q('#scsteps'),stage=q('.sc-stage');return {stepsBottom:Math.round(st.bottom),stageTop:Math.round(stage.top),H:innerHeight,sw:document.documentElement.scrollWidth,W:innerWidth}}""")
        check(T('lúc quét: danh sách bước + linh vật nằm gọn trong màn hình, không tràn ngang'), fit['stepsBottom'] <= fit['H'] and fit['stageTop'] >= 0 and fit['sw'] <= fit['W'], fit)
        gaps = pg.evaluate("(()=>{const f=window.__fr;let m=0;for(let i=1;i<f.length;i++)m=Math.max(m,f[i]-f[i-1]);return Math.round(m)})()")
        pg.wait_for_timeout(3600)
        check(T('không lỗi JS'), not errs, errs)
        ctx.close()

    # ---- "Giảm chuyển động" ----
    ctx = b.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True, reduced_motion='reduce')
    ctx.add_init_script("localStorage.setItem('nt_pg', JSON.stringify('PG01'))")
    pg = ctx.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:200])); pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith('http://127.0.0.1') else r.abort())
    pg.goto(URL); pg.wait_for_function("document.getElementById('splash').classList.contains('hide')", timeout=15000); pg.wait_for_timeout(500)
    prep(pg)
    t0 = time.time(); pg.locator('button.btnN:has-text("Xem kết quả")').click()
    pg.wait_for_function("S.step===4", timeout=8000); dt = time.time() - t0
    check('[giảm chuyển động] quét xong nhanh (< 3,2 giây) và vẫn sang kết quả', dt < 3.2, round(dt, 2))
    pg.evaluate("S.step=3;draw()"); pg.wait_for_timeout(200); pg.locator('button.btnN:has-text("Xem kết quả")').click(); pg.wait_for_timeout(600)
    chip_op = pg.evaluate("[...document.querySelectorAll('#scchips span')].map(e=>parseFloat(getComputedStyle(e).opacity))")
    check('[giảm chuyển động] số đo hiện đủ ngay (không kẹt ở độ mờ 0)', chip_op and all(o == 1 for o in chip_op), chip_op)
    check('[giảm chuyển động] không lỗi JS', not errs, errs)
    ctx.close()

    # ---- người lớn / bà bầu: chữ không nói "chuẩn WHO" bừa ----
    ctx = b.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True)
    ctx.add_init_script("localStorage.setItem('nt_pg', JSON.stringify('PG01'))")
    pg = ctx.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:200])); pg.route('**/*', lambda r: r.continue_() if r.request.url.startswith('http://127.0.0.1') else r.abort())
    pg.goto(URL); pg.wait_for_function("document.getElementById('splash').classList.contains('hide')", timeout=15000); pg.wait_for_timeout(500)
    prep(pg, 'adult', {'w': 62, 'h': 165})
    pg.locator('button.btnN:has-text("Xem kết quả")').click(); pg.wait_for_timeout(800)
    labels = pg.evaluate("document.getElementById('scsteps').innerText")
    check('[người lớn] bước 2 ghi "bảng chuẩn", không ghi "WHO"', 'bảng chuẩn' in labels and 'WHO' not in labels, labels)
    pg.wait_for_function("S.step===4", timeout=8000)
    check('[người lớn] vẫn sang kết quả, không lỗi JS', not errs, errs)
    ctx.close()
    b.close()
print('TỔNG', sum(res), '/', len(res))
srv.shutdown()
sys.exit(0 if all(res) else 1)
