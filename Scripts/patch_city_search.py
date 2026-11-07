#!/usr/bin/env python3
"""Adds a Search page: visitors type a city, state, country or keyword (or tap a
city chip) and see every matching photo. Adds a magnifier tab in the header and a
'Search' entry in the mobile menu. No new DOMContentLoaded blocks.
Aborts without changes if any anchor is missing. Safe to run once."""
import sys
path = sys.argv[1] if len(sys.argv) > 1 else "/Users/ncm/Pictures/Mohangraphy/Scripts/Claude_mohangraphy.py"
src = open(path, encoding="utf-8").read()
if "function showSearch" in src:
    sys.exit("Already patched - nothing to do.")

# 1) hideAll must clear the search block --------------------------------------
a = "['gallery-new-photos','gallery-story-temp'].forEach(function(id){"
assert src.count(a) == 1, "hideAll anchor not found exactly once"
src = src.replace(a, "['gallery-new-photos','gallery-story-temp','gallery-search'].forEach(function(id){")

# 2) JS (goes into the raw JS block, so no escaping needed) -------------------
JS = r'''/* ── CITY / PLACE SEARCH ── */
function _searchStyle(){
  if(document.getElementById('search-style')) return;
  var st = document.createElement('style');
  st.id = 'search-style';
  st.textContent =
    '.srch-wrap{padding:0 clamp(14px,4vw,44px) 8px;max-width:900px;}' +
    '.srch-input{width:100%;background:rgba(255,255,255,0.05);border:1px solid rgba(201,169,110,0.35);' +
    'color:#fff;padding:14px 16px;font-family:Montserrat,sans-serif;font-size:16px;letter-spacing:1px;' +
    'outline:none;border-radius:3px;-webkit-appearance:none;}' +
    '.srch-input:focus{border-color:var(--gold);}' +
    '.srch-chips{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px;max-height:170px;overflow-y:auto;}' +
    '.srch-chip{background:none;border:1px solid rgba(255,255,255,0.18);color:rgba(255,255,255,0.65);' +
    'padding:6px 12px;border-radius:18px;font-family:Montserrat,sans-serif;font-size:10px;' +
    'letter-spacing:1.5px;text-transform:uppercase;cursor:pointer;transition:all .2s;}' +
    '.srch-chip:hover,.srch-chip.on{color:var(--gold);border-color:var(--gold);background:rgba(201,169,110,0.08);}' +
    '.srch-count{padding:14px clamp(14px,4vw,44px) 10px;font-family:Montserrat,sans-serif;font-size:10px;' +
    'letter-spacing:3px;text-transform:uppercase;color:var(--gold);opacity:.85;}';
  document.head.appendChild(st);
}

var _searchIdx = [];

function _buildSearchIndex(){
  var seen = {};
  _searchIdx = [];
  document.querySelectorAll('.section-block:not(#gallery-search) .grid-item[data-photo]').forEach(function(item){
    var path = item.getAttribute('data-photo') || '';
    if(!path || seen[path]) return;
    seen[path] = true;
    var blk = item.closest('.section-block');
    var sub = blk ? blk.querySelector('.gal-sub') : null;
    var subTxt = sub ? sub.textContent.replace(/[0-9]+\s*Photos?/i, '') : '';
    var city  = item.getAttribute('data-city')    || '';
    var state = item.getAttribute('data-state')   || '';
    var rem   = item.getAttribute('data-remarks') || '';
    var cats  = (item.getAttribute('data-cats') || '').replace(/Places[/][A-Za-z]+/g, '').replace(/,/g, ' ');
    _searchIdx.push({
      item: item, city: city,
      hay: (city + ' ' + state + ' ' + rem + ' ' + subTxt + ' ' + cats).toLowerCase()
    });
  });
}

function showSearch(){
  hideAll();
  var gc = document.getElementById('gallery-container');
  if(!gc) return;
  gc.classList.add('visible');
  _searchStyle();
  _buildSearchIndex();

  /* city chips with photo counts */
  var counts = {};
  _searchIdx.forEach(function(e){ if(e.city) counts[e.city] = (counts[e.city] || 0) + 1; });
  var cities = Object.keys(counts).sort(function(a, b){ return a.toLowerCase() < b.toLowerCase() ? -1 : 1; });

  var block = document.createElement('div');
  block.id = 'gallery-search';
  block.className = 'section-block visible';
  block.style.cssText = 'padding-top:calc(var(--hdr) + 32px);';
  block.innerHTML =
    '<div class="gal-header"><div class="gal-title">Search</div>' +
    '<div class="gal-sub">Find photos by city, state, country or keyword</div></div>' +
    '<div class="srch-wrap" style="padding-top:18px;">' +
    '<input class="srch-input" id="srch-input" type="search" placeholder="e.g. Coimbatore, Kerala, Canada, sunset..." ' +
    'autocomplete="off" autocapitalize="off" spellcheck="false">' +
    '<div class="srch-chips" id="srch-chips"></div></div>' +
    '<div class="srch-count" id="srch-count"></div>' +
    '<div class="grid" id="srch-grid"></div>';
  gc.prepend(block);

  var chipBox = document.getElementById('srch-chips');
  cities.forEach(function(c){
    var b = document.createElement('button');
    b.type = 'button';
    b.className = 'srch-chip';
    b.textContent = c + ' (' + counts[c] + ')';
    b.onclick = function(){
      var inp = document.getElementById('srch-input');
      inp.value = c;
      runSearch();
    };
    b.setAttribute('data-city', c);
    chipBox.appendChild(b);
  });

  var input = document.getElementById('srch-input');
  input.addEventListener('input', runSearch);
  runSearch();
  setActiveTab('search');
  syncUrl('');
  window.scrollTo(0, 0);
  setTimeout(function(){ try{ input.focus(); }catch(e){} }, 150);
}

function runSearch(){
  var inp = document.getElementById('srch-input');
  var grid = document.getElementById('srch-grid');
  var cnt = document.getElementById('srch-count');
  if(!inp || !grid || !cnt) return;
  var q = inp.value.toLowerCase().trim();
  var tokens = q.split(/\s+/).filter(Boolean);

  document.querySelectorAll('.srch-chip').forEach(function(ch){
    ch.classList.toggle('on', !!q && ch.getAttribute('data-city').toLowerCase() === q);
  });

  if(!tokens.length){
    grid.innerHTML = '';
    cnt.textContent = 'Type a place or tap a city above';
    return;
  }
  var matches = _searchIdx.filter(function(e){
    return tokens.every(function(t){ return e.hay.indexOf(t) !== -1; });
  });
  var MAXR = 200;
  grid.innerHTML = matches.slice(0, MAXR).map(function(m){ return m.item.outerHTML; }).join('');
  cnt.textContent = matches.length
    ? matches.length + ' photo' + (matches.length > 1 ? 's' : '') + ' found' +
      (matches.length > MAXR ? ' · showing first ' + MAXR : '')
    : 'No photos found for "' + inp.value.trim().replace(/[<>&"]/g, '') + '"';
}

'''
b = "function scrollToCollections(){"
assert src.count(b) == 1, "JS anchor not found exactly once"
src = src.replace(b, JS + b)

# 3) header tab + mobile menu item (python source lines, so mind the quotes) --
h = '''        '    <button class="hdr-tab" id="tab-journeys" onclick="showJourneys()">Footprints</button>\\n'''
assert src.count(h) == 1, "header tab anchor not found exactly once"
tab = ('''\'\n        '    <button class="hdr-tab" id="tab-search" onclick="showSearch()" aria-label="Search photos" title="Search photos">'
        '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">'
        '<circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/></svg></button>\\n''')
src = src.replace(h, h + tab)

m = '''        '  <button class="mob-menu-item" onclick="showJourneys();closeMobileMenu()">Footprints</button>\\n'''
assert src.count(m) == 1, "mobile menu anchor not found exactly once"
src = src.replace(m, m + '''\'\n        '  <button class="mob-menu-item" onclick="showSearch();closeMobileMenu()">Search</button>\\n''')

open(path, "w", encoding="utf-8").write(src)
print("Patched OK:", path)
