/* Nutritie — Service Worker (online-first + cache offline).
   NHÂN từ app Wintop (sw.js, đã chạy thật): network-first CÓ TIMEOUT -> không bao giờ kẹt bản cũ khi còn mạng,
   chỉ dùng cache khi mạng treo/mất. ĐỔI 'nutritie-vN' mỗi lần deploy để dọn cache cũ. */
var CACHE = "nutritie-v1";
var CORE = ["./", "./index.html", "./assets/icon-192.png", "./assets/icon-512.png"];
self.addEventListener("install", function(e){ self.skipWaiting(); e.waitUntil(caches.open(CACHE).then(function(c){ return c.addAll(CORE).catch(function(){}); })); });
self.addEventListener("activate", function(e){ e.waitUntil(caches.keys().then(function(ks){ return Promise.all(ks.map(function(k){ if(k!==CACHE) return caches.delete(k); })); })); self.clients.claim(); });
self.addEventListener("fetch", function(e){
  if(e.request.method!=="GET") return;
  // Âm thanh / video KHÔNG đi qua SW: trình duyệt gửi yêu cầu từng đoạn (Range) — Safari/iPhone lỗi khi SW trả thay;
  // và tệp vài MB không nên nhét vào bộ nhớ đệm máy PG.
  var d=e.request.destination;
  if(d==="audio"||d==="video"||e.request.headers.has("range")) return;
  /* network-first CÓ TIMEOUT 4 giây: mạng treo thì dùng bản đã lưu. Chỉ lưu phản hồi 200. */
  e.respondWith(new Promise(function(resolve){
    var done=false;
    // Chỉ TRANG (navigate) mới được thay bằng index.html khi mất mạng. Ảnh/script khác trả index.html -> ảnh hỏng.
    var isNav=(e.request.mode==="navigate");
    var fromCache=function(){ return caches.match(e.request).then(function(m){ return m || (isNav?caches.match("./index.html"):undefined); }); };
    var timer=setTimeout(function(){ fromCache().then(function(m){ if(m&&!done){ done=true; resolve(m); } }); }, 4000);
    fetch(e.request).then(function(res){
      clearTimeout(timer);
      if(res&&res.ok){ var cp=res.clone(); caches.open(CACHE).then(function(c){ c.put(e.request, cp).catch(function(){}); }); }
      if(!done){ done=true; resolve(res); }
    }).catch(function(){
      clearTimeout(timer);
      fromCache().then(function(m){ if(!done){ done=true; resolve(m||Response.error()); } });
    });
  }));
});
