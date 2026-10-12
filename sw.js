/* 토플 단어 - 오프라인 캐시 */
var VERSION = "26.10.12-1";
var CACHE = "toefl-voca-v" + VERSION;
var CORE = ["./", "./index.html", "./manifest.webmanifest",
            "./apple-touch-icon.png", "./icon-192.png", "./icon-512.png"];

self.addEventListener("install", function(e){
  e.waitUntil(
    caches.open(CACHE)
      .then(function(c){
        return c.addAll(CORE.map(function(u){ return new Request(u, { cache:"reload" }); }));
      })
      .catch(function(){})
      .then(function(){ return self.skipWaiting(); })
  );
});

self.addEventListener("activate", function(e){
  e.waitUntil(
    caches.keys()
      .then(function(ks){ return Promise.all(ks.map(function(k){ return k === CACHE ? null : caches.delete(k); })); })
      .then(function(){ return self.clients.claim(); })
  );
});

self.addEventListener("fetch", function(e){
  if (e.request.method !== "GET") return;
  if (e.request.url.indexOf("version.json") >= 0) return;
  e.respondWith(
    caches.match(e.request, { ignoreSearch:true }).then(function(hit){
      if (hit) return hit;
      return fetch(e.request).then(function(res){
        var copy = res.clone();
        caches.open(CACHE).then(function(c){ c.put(e.request, copy); }).catch(function(){});
        return res;
      }).catch(function(){ return caches.match("./index.html"); });
    })
  );
});
