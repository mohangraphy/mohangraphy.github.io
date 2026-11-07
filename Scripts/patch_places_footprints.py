#!/usr/bin/env python3
"""Footprints place search (final version).
 - 'Search' button at the RIGHT edge of the India / World tab row on the Footprints page.
 - The list follows the active tab: India tab -> Indian cities (City, State);
   World tab -> international places (City, State, Country). Alphabetical.
   Gold dot = gallery uploaded, gold circle = coming soon.
 - New cities are picked up automatically from the galleries the build creates.
 - Nothing is added to the main header or the mobile menu.
Works from any earlier state (original, patch_city_search.py, patch_places_search.py,
or the previous patch_places_footprints.py). Aborts without changes if anchors are missing."""
import sys
path = sys.argv[1] if len(sys.argv) > 1 else "/Users/ncm/Pictures/Mohangraphy/Scripts/Claude_mohangraphy.py"
src = open(path, encoding="utf-8").read()
if "PLACES SEARCH v3" in src:
    sys.exit("Already patched - nothing to do.")

JS = r"""/* ══════════════════════════════════════════════════════
   PLACES SEARCH v3 — pull-down on the Footprints page (follows the India / World tab)
   International (City, State, Country) then National (City, State),
   alphabetical. Gold dot = gallery uploaded, gold circle = coming soon.
   New cities are picked up automatically from the galleries the build creates.
   ══════════════════════════════════════════════════════ */
(function(){
  var st = document.createElement('style');
  st.id = 'places-style';
  st.textContent =
    '#places-dd{position:fixed;z-index:2002;display:none;flex-direction:column;background:rgba(10,10,10,0.985);' +
    'border:1px solid rgba(201,169,110,0.22);border-top:2px solid #c9a96e;box-shadow:0 12px 40px rgba(0,0,0,0.7);}' +
    '#places-dd.open{display:flex;}' +
    '.pl-top{display:flex;gap:8px;align-items:center;padding:12px 14px 8px;}' +
    '.pl-input{flex:1;min-width:0;background:rgba(255,255,255,0.05);border:1px solid rgba(201,169,110,0.3);color:#fff;' +
    'padding:10px 12px;font-family:Montserrat,sans-serif;font-size:16px;outline:none;border-radius:3px;-webkit-appearance:none;}' +
    '.pl-input:focus{border-color:#c9a96e;}' +
    '.pl-close{background:none;border:none;color:rgba(255,255,255,0.5);font-size:18px;cursor:pointer;width:32px;height:32px;}' +
    '.pl-close:hover{color:#c9a96e;}' +
    '.pl-legend{display:flex;gap:16px;flex-wrap:wrap;padding:2px 16px 10px;font-family:Montserrat,sans-serif;font-size:9px;' +
    'letter-spacing:2px;text-transform:uppercase;color:rgba(255,255,255,0.5);}' +
    '.pl-list{overflow-y:auto;-webkit-overflow-scrolling:touch;border-top:1px solid rgba(255,255,255,0.06);}' +
    '.pl-head{position:sticky;top:0;background:#0a0a0a;padding:10px 16px;font-family:Montserrat,sans-serif;font-size:9px;' +
    'font-weight:700;letter-spacing:3px;text-transform:uppercase;color:#c9a96e;border-bottom:1px solid rgba(201,169,110,0.15);}' +
    '.pl-item{display:flex;align-items:center;gap:12px;width:100%;text-align:left;background:none;border:none;' +
    'border-bottom:1px solid rgba(255,255,255,0.04);padding:11px 16px;cursor:pointer;font-family:Montserrat,sans-serif;' +
    'font-size:11px;letter-spacing:1px;color:rgba(255,255,255,0.8);transition:background .15s,color .15s;}' +
    '.pl-item:hover{background:rgba(201,169,110,0.07);color:#c9a96e;}' +
    '.pl-item.soon{color:rgba(255,255,255,0.5);}' +
    '.pl-dot{flex:0 0 auto;width:10px;height:10px;border-radius:50%;box-sizing:border-box;border:2px solid #c9a96e;}' +
    '.pl-dot.up{background:#c9a96e;box-shadow:0 0 5px rgba(201,169,110,0.5);}' +
    '.pl-empty{padding:20px 16px;font-family:Montserrat,sans-serif;font-size:11px;letter-spacing:2px;' +
    'color:rgba(255,255,255,0.4);text-transform:uppercase;}' +
    '#jtab-world{border-right-width:1px;border-right-style:solid;}' +
    '#fp-search-btn:hover{background:rgba(201,169,110,0.1);}' +
    '@media (max-width:480px){#fp-search-btn{padding:10px 12px !important;letter-spacing:2px !important;}}';
  document.head.appendChild(st);
})();

var _plOpen = false;
var _plList = [];
var _PL_BLOCKS = '.section-block[id*="-india-"], .section-block[id*="-overseas-"]';

function _plNorm(s){ return (s || '').toLowerCase().replace(/[^a-z0-9]/g, ''); }
function _plCityParts(s){ var a = (s || '').split('/'); return { name: a[0].trim(), extra: (a[1] || '').trim() }; }
function _plCityKey(s){ return _plNorm((s || '').split('/')[0]); }
function _plEsc(s){ return String(s).replace(/[&<>"]/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }

/* Cities that actually have photo galleries in the page */
function _plScan(){
  var info = {};
  document.querySelectorAll(_PL_BLOCKS).forEach(function(b){
    var region = b.id.indexOf('-overseas-') > -1 ? 'world' : 'india';
    var first = b.querySelector('.grid-item[data-city]');
    if(!first) return;
    var cp = _plCityParts(first.getAttribute('data-city'));
    if(!cp.name) return;
    var key = region + ':' + _plNorm(cp.name);
    var st = (first.getAttribute('data-state') || '').trim();
    var country = '';
    if(region === 'world'){
      var sub = b.querySelector('.gal-sub');
      if(sub) country = (sub.textContent.split('\u00b7')[1] || '').trim();
    }
    var state = (region === 'india')
      ? (st || cp.extra)
      : ((st && _plNorm(st) !== _plNorm(country) && _plNorm(st) !== _plNorm(cp.name)) ? st : cp.extra);
    if(!info[key]) info[key] = { name: cp.name, region: region, state: state, country: country, ids: [] };
    info[key].ids.push(b.id);
    if(!info[key].state && state) info[key].state = state;
    if(!info[key].country && country) info[key].country = country;
  });
  return info;
}

/* Journeys places + any gallery city not already on that list */
function _plGather(){
  var info = _plScan();
  var out = [], claimed = {}, used = {};
  function add(list, region){
    (list || []).forEach(function(p){
      var key = region + ':' + _plNorm(p.name);
      var ci = info[key];
      var rec = {
        name: p.name, region: region,
        state: p.state || (ci ? ci.state : '') || '',
        country: region === 'india' ? 'India' : (p.country || (ci ? ci.country : '') || ''),
        uploaded: !!p.uploaded || !!ci,
        galleries: p.galleries || []
      };
      rec.galleries.forEach(function(g){ claimed[g] = true; });
      if(ci) used[key] = true;
      out.push(rec);
    });
  }
  add(JOURNEYS_INDIA, 'india');
  add(JOURNEYS_WORLD, 'world');
  Object.keys(info).forEach(function(key){
    var ci = info[key];
    if(used[key]) return;
    if(ci.ids.some(function(id){ return claimed[id]; })) return;
    out.push({ name: ci.name, region: ci.region, state: ci.state,
               country: ci.region === 'india' ? 'India' : ci.country,
               uploaded: true, galleries: ci.ids });
  });
  out.forEach(function(p){
    var parts = [p.name];
    if(p.state && _plNorm(p.state) !== _plNorm(p.name)) parts.push(p.state);
    if(p.region === 'world' && p.country && _plNorm(p.country) !== _plNorm(p.name)) parts.push(p.country);
    p.label = parts.join(', ');
  });
  out.sort(function(a, b){
    var x = a.name.toLowerCase(), y = b.name.toLowerCase();
    return x < y ? -1 : (x > y ? 1 : 0);
  });
  return out;
}

function _plEnsureDD(){
  var dd = document.getElementById('places-dd');
  if(dd) return dd;
  dd = document.createElement('div');
  dd.id = 'places-dd';
  dd.innerHTML =
    '<div class="pl-top"><input class="pl-input" id="pl-input" type="search" placeholder="Search a place..." ' +
    'autocomplete="off" autocapitalize="off" spellcheck="false">' +
    '<button class="pl-close" type="button" aria-label="Close" onclick="closePlacesDD()">&#x2715;</button></div>' +
    '<div class="pl-legend">' +
    '<span><span class="pl-dot up" style="display:inline-block;vertical-align:middle;margin-right:6px"></span>Gallery uploaded</span>' +
    '<span><span class="pl-dot" style="display:inline-block;vertical-align:middle;margin-right:6px"></span>Coming soon</span></div>' +
    '<div class="pl-list" id="pl-list"></div>';
  document.body.appendChild(dd);
  document.getElementById('pl-input').addEventListener('input', function(){ _plRender(this.value); });
  return dd;
}

function _plRender(filter){
  var box = document.getElementById('pl-list');
  if(!box) return;
  box.innerHTML = '';
  var q = (filter || '').toLowerCase().trim();
  var tab = (typeof _journeysTab !== 'undefined' && _journeysTab === 'world') ? 'world' : 'india';
  [[tab, tab === 'india' ? 'India' : 'International']].forEach(function(sec){
    var rows = _plList.filter(function(p){
      return p.region === sec[0] && (!q || p.label.toLowerCase().indexOf(q) > -1);
    });
    if(!rows.length) return;
    var h = document.createElement('div');
    h.className = 'pl-head';
    h.textContent = sec[1] + ' \u00b7 ' + rows.length;
    box.appendChild(h);
    rows.forEach(function(p){
      var b = document.createElement('button');
      b.type = 'button';
      b.className = 'pl-item' + (p.uploaded ? '' : ' soon');
      var dot = document.createElement('span');
      dot.className = 'pl-dot' + (p.uploaded ? ' up' : '');
      var lbl = document.createElement('span');
      lbl.textContent = p.label;
      b.appendChild(dot);
      b.appendChild(lbl);
      b.onclick = function(){ _plOpenPlace(p); };
      box.appendChild(b);
    });
  });
  if(!box.children.length){
    var e = document.createElement('div');
    e.className = 'pl-empty';
    e.textContent = 'No places match';
    box.appendChild(e);
  }
}

function _plPosition(dd){
  var hdr = document.querySelector('header');
  var hdrH = hdr ? hdr.offsetHeight : 80;
  if(window.innerWidth <= 1024){
    dd.style.top = hdrH + 'px';
    dd.style.left = '0'; dd.style.right = '0'; dd.style.width = 'auto';
    dd.style.maxHeight = (window.innerHeight - hdrH) + 'px';
  } else {
    var btn = document.getElementById('fp-search-btn');
    var w = 380, left = 8, top = hdrH;
    if(btn){
      var r = btn.getBoundingClientRect();
      top = Math.max(hdrH, r.bottom + 6);
      left = Math.min(Math.max(8, r.right - w), window.innerWidth - w - 8);
    }
    dd.style.top = top + 'px';
    dd.style.left = left + 'px'; dd.style.right = 'auto'; dd.style.width = w + 'px';
    dd.style.maxHeight = Math.max(200, Math.min(window.innerHeight - top - 16, 560)) + 'px';
  }
}

function openPlacesDD(){
  _plOpen = true;
  var tab = document.getElementById('fp-search-btn');
  if(tab) tab.classList.add('dd-open');
  var dd = _plEnsureDD();
  loadJourneysData(function(){
    if(!_plOpen) return;
    _plList = _plGather();
    var inp = document.getElementById('pl-input');
    if(inp){
      inp.value = '';
      inp.placeholder = (typeof _journeysTab !== 'undefined' && _journeysTab === 'world')
        ? 'Search a city, state or country...' : 'Search a city or state in India...';
    }
    _plRender('');
    _plPosition(dd);
    dd.classList.add('open');
    if(window.innerWidth > 1024 && inp){ try{ inp.focus(); }catch(e){} }
  });
}

function closePlacesDD(){
  _plOpen = false;
  var dd = document.getElementById('places-dd');
  if(dd) dd.classList.remove('open');
  var tab = document.getElementById('fp-search-btn');
  if(tab) tab.classList.remove('dd-open');
}

function togglePlacesDD(e){
  if(e && e.stopPropagation) e.stopPropagation();
  if(_plOpen) closePlacesDD(); else openPlacesDD();
}

function _plOpenPlace(p){
  closePlacesDD();
  if(!p.uploaded){ showToast(p.name + ' \u2014 photos coming soon'); return; }
  var key = _plNorm(p.name), seen = {}, items = [];
  document.querySelectorAll(_PL_BLOCKS).forEach(function(b){
    var region = b.id.indexOf('-overseas-') > -1 ? 'world' : 'india';
    if(region !== p.region) return;
    b.querySelectorAll('.grid-item[data-photo]').forEach(function(it){
      var path = it.getAttribute('data-photo') || '';
      if(seen[path]) return;
      if(_plCityKey(it.getAttribute('data-city')) !== key) return;
      seen[path] = true;
      items.push(it);
    });
  });
  if(!items.length){
    if(p.galleries && p.galleries.length){ showGallery(p.galleries[0]); return; }
    showToast(p.name + ' \u2014 photos coming soon');
    return;
  }
  hideAll();
  var gc = document.getElementById('gallery-container');
  if(!gc) return;
  gc.classList.add('visible');
  var old = document.getElementById('gallery-place');
  if(old) old.remove();
  var where = [];
  if(p.state && _plNorm(p.state) !== _plNorm(p.name)) where.push(p.state);
  if(p.region === 'world' && p.country) where.push(p.country);
  var sub = where.concat([items.length + ' Photo' + (items.length > 1 ? 's' : '')]).join(' \u00b7 ');
  var block = document.createElement('div');
  block.id = 'gallery-place';
  block.className = 'section-block visible';
  block.style.cssText = 'padding-top:calc(var(--hdr) + 32px);';
  block.innerHTML =
    '<div class="gal-header"><div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;">' +
    '<div><div class="gal-title">' + _plEsc(p.name) + '</div><div class="gal-sub">' + _plEsc(sub) + '</div></div>' +
    '<button class="slideshow-btn" onclick="startSlideshow(\x27gallery-place\x27)">' +
    '<svg width="11" height="11" viewBox="0 0 11 11" fill="none"><polygon points="1,0.5 10.5,5.5 1,10.5" fill="currentColor"/></svg>' +
    'View Slideshow</button></div></div>' +
    '<div class="grid">' + items.map(function(it){ return it.outerHTML; }).join('') + '</div>';
  gc.prepend(block);
  setActiveTab('journeys');
  if(typeof updateBreadcrumb === 'function') updateBreadcrumb([{label:'Footprints',fn:'showJourneys()'},{label:p.name}]);
  syncUrl('');
  window.scrollTo(0, 0);
}

/* close on outside click / Escape / resize (plain listeners — no DOMContentLoaded) */
document.addEventListener('click', function(e){
  if(!_plOpen) return;
  if(e.target.closest('#places-dd') || e.target.closest('#fp-search-btn') || e.target.closest('#mobile-menu')) return;
  closePlacesDD();
});
document.addEventListener('keydown', function(e){ if(e.key === 'Escape' && _plOpen) closePlacesDD(); });
document.addEventListener('scroll', function(e){
  if(!_plOpen || window.innerWidth <= 1024) return;
  var t = e.target;
  if(t && t.nodeType === 1 && t.closest('#places-dd')) return;
  var dd = document.getElementById('places-dd');
  if(dd) _plPosition(dd);
}, true);
window.addEventListener('resize', function(){
  if(!_plOpen) return;
  var dd = document.getElementById('places-dd');
  if(dd) _plPosition(dd);
});

"""

def swap(old, new):
    global src
    assert src.count(old) == 1, "anchor not found exactly once: " + old[:70]
    src = src.replace(old, new)

END = "function scrollToCollections(){"

# A) older city-search patch: magnifier tab, mobile entry, JS block
if "function showSearch" in src:
    swap(r"""        '    <button class="hdr-tab" id="tab-search" onclick="showSearch()" aria-label="Search photos" title="Search photos">'
        '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">'
        '<circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/></svg></button>\n'
""", "")
    swap(r"""        '  <button class="mob-menu-item" onclick="showSearch();closeMobileMenu()">Search</button>\n'
""", "")
    marker = "/* \u2500\u2500 CITY / PLACE SEARCH \u2500\u2500 */"
    assert src.count(marker) == 1, "city-search JS block not found"
    cs, ce = src.index(marker), src.index(END)
    assert cs < ce
    src = src[:cs] + src[ce:]
    swap("['gallery-new-photos','gallery-story-temp','gallery-search'].forEach(function(id){",
         "['gallery-new-photos','gallery-story-temp'].forEach(function(id){")

# B) patch_places_search.py version: header tab + mobile entry
if 'id="tab-search" onclick="togglePlacesDD(event)"' in src:
    swap(r"""        '    <button class="hdr-tab" id="tab-search" onclick="togglePlacesDD(event)">Search <span class="hdr-tab-chevron">&#9662;</span></button>\n'
""", "")
    swap(r"""        '  <button class="mob-menu-item" onclick="closeMobileMenu();openPlacesDD()">Search</button>\n'
""", "")

# C) previous Footprints version: old button beside Copy Link
old_btn = r"""        '    <button class="copy-link-btn" id="fp-search-btn" onclick="togglePlacesDD(event)" style="cursor:pointer;background:none;border:1px solid rgba(201,169,110,0.6);color:var(--gold);padding:4px 10px;font-size:10px;letter-spacing:1px;margin-top:12px;margin-left:8px;border-radius:3px;" title="Search places">&#128269; Search Places &#9662;</button>\n'
"""
if src.count(old_btn) == 1:
    src = src.replace(old_btn, "")

# D) remove any earlier places JS block, then insert the current one
pm = "   PLACES SEARCH"
if src.count(pm) == 1:
    start = src.rfind("/* \u2550", 0, src.index(pm))
    end = src.index(END)
    assert 0 < start < end, "could not locate earlier places JS block"
    src = src[:start] + src[end:]
swap(END, JS + END)

# E) hideAll must clear the place page
if "'gallery-place'" not in src.split("function hideAll")[1].split("}")[0] + src.split("function hideAll")[1][:900]:
    swap("['gallery-new-photos','gallery-story-temp'].forEach(function(id){",
         "['gallery-new-photos','gallery-story-temp','gallery-place'].forEach(function(id){")

# F) Search button at the right edge of the India / World tab row
w = r"""onclick="switchJourneysTab(\'world\')">World</button>\n"""
btn = (r"""'
        '    <button id="fp-search-btn" onclick="togglePlacesDD(event)" """
       r"""style="margin-left:auto;cursor:pointer;background:none;border:1px solid rgba(201,169,110,0.5);color:var(--gold);padding:10px 18px;"""
       r"""font-family:Montserrat,sans-serif;font-size:10px;font-weight:600;letter-spacing:3px;text-transform:uppercase;" title="Search places">"""
       r"""&#128269; Search &#9662;</button>\n""")
swap(w, w + btn)

# G) close the list when the India / World tab is switched
swap("function switchJourneysTab(tab){\n  _journeysTab = tab;\n",
     "function switchJourneysTab(tab){\n  _journeysTab = tab;\n  if(typeof closePlacesDD === 'function') closePlacesDD();\n")

open(path, "w", encoding="utf-8").write(src)
print("Patched OK:", path)
