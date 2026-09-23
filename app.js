'use strict';
const $ = id => document.getElementById(id);
const KEY = 'all-ar-owned-v1', CAPACITY = 1280, PROMO_START = 1116;
let cards = [], states = {}, filter = 'all', newest = false, spread = 0, selectedCard = null;
let slots = Array(CAPACITY).fill(null);
try { const saved = JSON.parse(localStorage.getItem(KEY) || '{}'); if (saved && typeof saved === 'object' && !Array.isArray(saved)) states = saved; }
catch { notify('Deine gespeicherten Markierungen konnten nicht gelesen werden.'); }
function notify(message) { $('notice').hidden = false; $('notice').textContent = message; }
const owned = id => states[id] === 'owned';
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function setState(id, state) {
  const next = {...states, [id]:state};
  try { localStorage.setItem(KEY, JSON.stringify(next)); states = next; }
  catch { notify('Die Markierung konnte auf diesem Gerät nicht gespeichert werden.'); return; }
  renderCollection(); renderBinder(); if (selectedCard) updateZoomButton();
}
function filteredCards() {
  const query = $('q').value.trim().toLowerCase();
  const result = cards.filter(c => {
    if (filter === 'owned' && !owned(c.id) || filter === 'missing' && owned(c.id) || filter === 'promo' && c.kind !== 'AR Promo') return false;
    return !query || [c.name,c.name_ja,c.set_name,c.set_code,c.number_display].join(' ').toLowerCase().includes(query);
  });
  return newest ? result.reverse() : result;
}
function tile(c) {
  const has = owned(c.id);
  return `<article class="card ${has?'owned':'missing'}" data-id="${esc(c.id)}">
  <button class="card-visual" data-zoom="${esc(c.id)}" aria-label="${esc(c.name)} vergrößern"><img loading="lazy" decoding="async" src="${esc(c.image)}" alt="${esc(c.name)}"><span class="badge ${c.kind==='AR Promo'?'promo':''}">${c.kind==='AR Promo'?'PROMO':'AR'}</span>${has?'<span class="owned-check" aria-hidden="true">✓</span>':''}</button>
  <div class="card-info"><div class="card-kicker"><span>${esc(c.set_code)}</span><span>${esc(c.number_display)}</span></div><h3>${esc(c.name)}</h3><p class="card-set" title="${esc(c.set_name)}">${esc(c.set_name)}</p><div class="actions"><button data-state="owned" class="${has?'selected':''}" aria-pressed="${has}">✓ Habe ich</button><button data-state="missing" class="${!has?'selected':''}" aria-pressed="${!has}">Fehlt</button></div></div></article>`;
}
function renderCollection() {
  const list = filteredCards(), count = cards.filter(c => owned(c.id)).length;
  $('cards').innerHTML = list.map(tile).join('');
  $('emptyResults').hidden = list.length !== 0;
  $('resultCount').textContent = list.length + ' Karten';
  $('allN').textContent = cards.length; $('ownedN').textContent = count; $('missN').textContent = cards.length-count;
  const percent = cards.length ? Math.round(count/cards.length*100) : 0;
  $('percent').textContent = percent + ' %'; $('progress').value = percent;
}
function spreadStart(n) { return n === 0 ? 0 : 20+(n-1)*40; }
const LAST_SPREAD = 32;
function buildBinder() {
  const normal = cards.filter(c=>c.kind==='AR'), promos=cards.filter(c=>c.kind==='AR Promo');
  slots = Array(CAPACITY).fill(null);
  normal.slice(0,PROMO_START).forEach((c,i)=>slots[i]=c);
  promos.slice(0,CAPACITY-PROMO_START).forEach((c,i)=>slots[PROMO_START+i]=c);
  $('normalFree').textContent = Math.max(0,PROMO_START-normal.length)+' freie Plätze';
  $('promoFree').textContent = Math.max(0,CAPACITY-PROMO_START-promos.length)+' freie Plätze';
  if (normal.length>PROMO_START || promos.length>CAPACITY-PROMO_START) notify('Ein Binderbereich ist voll. Alle Karten findest du weiterhin in der Sammlung.');
  $('pageSelect').innerHTML = Array.from({length:LAST_SPREAD+1},(_,n)=>{
    const start=spreadStart(n),end=n===0?20:Math.min(start+40,CAPACITY);
    return `<option value="${n}">${n===0?'Startseite':n===LAST_SPREAD?'Letzte Seite':'Doppelseite '+n} · ${start+1}–${end}</option>`;
  }).join('');
  renderBinder();
}
function page(start) {
  if (start>=CAPACITY) return '<div class="binder-blank" aria-hidden="true">ALL AR</div>';
  return '<div class="binder-page">'+Array.from({length:Math.min(20,CAPACITY-start)},(_,i)=>{
    const n=start+i,c=slots[n],reserved=n>=PROMO_START;
    if(!c) return `<div class="slot empty ${reserved?'reserved':''}" title="Platz ${n+1} · ${reserved?'Promo-Reserve':'AR-Reserve'}">${n+1}</div>`;
    return `<button class="slot ${owned(c.id)?'owned':'missing'} ${reserved?'reserved':''}" data-zoom="${esc(c.id)}" aria-label="Platz ${n+1}: ${esc(c.name)} vergrößern"><img loading="lazy" src="${esc(c.image)}" alt="${esc(c.name)}"><span class="slot-n">${n+1}</span></button>`;
  }).join('')+'</div>';
}
function renderBinder() {
  const start=spreadStart(spread),end=spread===0?20:Math.min(start+40,CAPACITY);
  $('spreadTitle').textContent = spread===0?'Die erste Seite':spread===LAST_SPREAD?'Die letzte Seite':start>=PROMO_START?'Deine AR-Promos':end>PROMO_START?'Hier beginnen die Promos':'Deine Art Rares';
  $('spreadRange').textContent = 'Plätze '+(start+1)+'–'+end;
  $('binderPages').innerHTML = spread===0?'<div class="binder-blank" aria-hidden="true">ALL AR</div>'+page(0):page(start)+page(start+20);
  $('pageInfo').textContent=(spread+1)+' / '+(LAST_SPREAD+1);
  $('pageSelect').value=String(spread); $('prevPage').disabled=spread===0; $('nextPage').disabled=spread===LAST_SPREAD;
}
function show(view) {
  const isBinder=view==='binder';
  $('collectionView').hidden=isBinder; $('binderView').hidden=!isBinder;
  $('navBinder').classList.toggle('active',isBinder); $('navCollection').classList.toggle('active',!isBinder);
  $('navBinder').toggleAttribute('aria-current',isBinder); $('navCollection').toggleAttribute('aria-current',!isBinder);
  (isBinder?$('navBinder'):$('navCollection')).setAttribute('aria-current','page');
  if(isBinder)renderBinder();
}
function updateZoomButton(){ $('zoomOwned').textContent=owned(selectedCard.id)?'✓ Habe ich · als fehlend markieren':'+ Zu meiner Sammlung hinzufügen'; }
function zoom(id) {
  selectedCard=cards.find(c=>c.id===id); if(!selectedCard)return;
  $('zoomImage').src=selectedCard.image; $('zoomImage').alt=selectedCard.name;
  $('zoomName').textContent=selectedCard.name; $('zoomMeta').textContent=selectedCard.set_code+' · '+selectedCard.number_display;
  updateZoomButton(); $('zoomDialog').showModal();
}
$('cards').addEventListener('click',e=>{
  const stateButton=e.target.closest('[data-state]'),zoomButton=e.target.closest('[data-zoom]');
  if(stateButton)setState(stateButton.closest('[data-id]').dataset.id,stateButton.dataset.state);
  else if(zoomButton)zoom(zoomButton.dataset.zoom);
});
$('binderPages').addEventListener('click',e=>{const b=e.target.closest('[data-zoom]');if(b)zoom(b.dataset.zoom)});
document.querySelectorAll('[data-filter]').forEach(b=>b.addEventListener('click',()=>{
  filter=b.dataset.filter;document.querySelectorAll('[data-filter]').forEach(x=>{x.classList.toggle('active',x===b);x.setAttribute('aria-pressed',String(x===b))});renderCollection();
}));
$('q').addEventListener('input',renderCollection);
$('order').onclick=()=>{newest=!newest;$('order').textContent=newest?'↓ Neueste zuerst':'↑ Älteste zuerst';renderCollection()};
$('navCollection').onclick=()=>show('collection');$('navBinder').onclick=()=>show('binder');
$('prevPage').onclick=()=>{spread=Math.max(0,spread-1);renderBinder()};
$('nextPage').onclick=()=>{spread=Math.min(LAST_SPREAD,spread+1);renderBinder()};
$('pageSelect').onchange=()=>{spread=Number($('pageSelect').value);renderBinder()};
$('jumpStart').onclick=()=>{spread=0;renderBinder()};
$('jumpPromo').onclick=()=>{spread=1+Math.floor((PROMO_START-20)/40);renderBinder()};
$('closeZoom').onclick=()=>$('zoomDialog').close();
$('zoomDialog').addEventListener('click',e=>{if(e.target===$('zoomDialog')){const r=e.target.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)e.target.close()}});
$('zoomOwned').onclick=()=>setState(selectedCard.id,owned(selectedCard.id)?'missing':'owned');
fetch('data/cards.json').then(r=>{if(!r.ok)throw Error(r.status);return r.json()}).then(d=>{
  cards=d.cards||[];renderCollection();buildBinder();
  const featured=cards.find(c=>c.name==='Mew')||cards[0];if(featured)$('heroImage').src=featured.image;
}).catch(()=>notify('Die Kartendaten konnten nicht geladen werden. Bitte lade die App erneut.'));
if('serviceWorker' in navigator)navigator.serviceWorker.register('sw.js').catch(()=>{});
