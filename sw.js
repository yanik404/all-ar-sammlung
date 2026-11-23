const CACHE='all-ar-v23';
const CORE=['./','./index.html','./styles.css?v=16','./missing-state.css?v=1','./app.js?v=19','./manifest.webmanifest','./icons/icon-192.png','./icons/icon-512.png','./data/cards.json?images=20'];
self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(CORE)).then(()=>self.skipWaiting())));
self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(key=>key!==CACHE).map(key=>caches.delete(key)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',e=>{
  if(e.request.method!=='GET')return;
  const url=new URL(e.request.url);
  if(url.origin!==self.location.origin)return;
  const shell=e.request.mode==='navigate'||/\/(?:index\.html|app\.js|styles\.css|missing-state\.css|manifest\.webmanifest)$/.test(url.pathname);
  if(shell||url.pathname.endsWith('/data/cards.json')){
    e.respondWith(fetch(e.request,{cache:'no-store'}).then(r=>{
      if(r.ok)caches.open(CACHE).then(c=>c.put(e.request,r.clone()));
      return r;
    }).catch(()=>caches.match(e.request).then(r=>r||(e.request.mode==='navigate'?caches.match('./index.html'):Response.error()))));
    return;
  }
  e.respondWith(caches.match(e.request).then(r=>r||fetch(e.request)));
});