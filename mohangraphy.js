
/* ══════════════════════════════════════════════════════
   NAVIGATION — single source of truth
   ══════════════════════════════════════════════════════ */
var currentCat     = null;
var currentSection = null;
var currentParent  = null;
var currentFilter  = 'National'; /* Places filter pill */

var NAV_PANELS = ['tile-nav', 'sub-nav', 'gallery-container'];

function hideAll(){
  document.getElementById('hero').classList.remove('visible');
  NAV_PANELS.forEach(function(id){
    var el = document.getElementById(id);
    if(el) el.classList.remove('visible', 'page-enter');
  });
  document.getElementById('copyright-banner').classList.remove('visible');
  document.querySelectorAll('.info-page').forEach(function(p){ p.classList.remove('visible'); });
  document.querySelectorAll('.story-post').forEach(function(p){ p.classList.remove('visible'); });
  document.querySelectorAll('.sub-panel').forEach(function(p){ p.classList.remove('active'); });
  document.querySelectorAll('.section-block').forEach(function(b){ b.classList.remove('visible'); });
  /* Remove dynamically injected blocks — these use inline display:block !important
     so class removal alone won't hide them */
  ['gallery-new-photos','gallery-story-temp'].forEach(function(id){
    var el = document.getElementById(id); if(el) el.remove();
  });
  setActiveTab(null);
}

function setActiveTab(which){
  document.querySelectorAll('.hdr-tab').forEach(function(t){ t.classList.remove('active'); });
  if(which){ var t=document.getElementById('tab-'+which); if(t) t.classList.add('active'); }
}

function goHome(){
  hideAll();
  document.getElementById('hero').classList.add('visible');
  document.getElementById('tile-nav').classList.add('visible','page-enter');
  setActiveTab('home');
  window.scrollTo(0,0);
}

function openCategory(cat){
  currentCat = cat; hideAll();
  var sn = document.getElementById('sub-nav');
  if(sn) sn.classList.add('visible','page-enter');
  updateBreadcrumb([{label:'Home',fn:'goHome()'}, {label:cat}]);
  /* Panel IDs use _ and n substitutions to match Python generation */
  var panelId = 'subpanel-' + cat.replace(/ /g,'_').replace(/&/g,'n');
  var p = document.getElementById(panelId);
  if(p) p.classList.add('active');
  setActiveTab('collections');
  window.scrollTo(0,0);
}

function openSubNav(cat){ openCategory(cat); }

function showGallery(id, breadcrumbs){
  hideAll();
  var gc = document.getElementById('gallery-container');
  if(gc) gc.classList.add('visible','page-enter');
  var b = document.getElementById(id);
  if(b) b.classList.add('visible');
  document.getElementById('copyright-banner').classList.add('visible');
  if(breadcrumbs){ updateBreadcrumb(breadcrumbs); }
  else {
    /* Auto-build breadcrumb — direct-X means top-level category */
    var crumbs = [{label:'Home',fn:'goHome()'}];
    if(id.indexOf('direct-')===0){
      /* Top-level direct gallery — no parent category in breadcrumb */
      var cat = id.replace('direct-','');
      currentCat = cat;
      var block = document.getElementById(id);
      if(block){
        var titleEl = block.querySelector('.gal-title');
        if(titleEl) crumbs.push({label: titleEl.textContent});
      }
    } else {
      if(currentCat) crumbs.push({label:currentCat,fn:"openCategory('"+currentCat+"')"});
      var block = document.getElementById(id);
      if(block){
        var titleEl = block.querySelector('.gal-title');
        if(titleEl) crumbs.push({label: titleEl.textContent});
      }
    }
    updateBreadcrumb(crumbs);
  }
  setActiveTab('collections');
  window.scrollTo(0,0);
}

function showSection(targetId, parentId, breadcrumbs){
  hideAll();
  var gc = document.getElementById('gallery-container');
  if(gc) gc.classList.add('visible');
  var el = document.getElementById(targetId);
  if(el){ el.classList.add('visible'); currentSection=targetId; currentParent=parentId; }
  if(breadcrumbs) updateBreadcrumb(breadcrumbs);
  else {
    /* Auto-build breadcrumb */
    var crumbs = [{label:'Home',fn:'goHome()'}];
    if(currentCat) crumbs.push({label:currentCat,fn:"openCategory('"+currentCat+"')"});
    if(parentId){
      var parentEl = document.getElementById(parentId);
      if(parentEl){
        var parentTitle = parentEl.querySelector('.gal-title');
        var parentTxt = parentTitle ? parentTitle.textContent : parentId;
        crumbs.push({label:parentTxt, fn:"showSection('"+parentId+"',null)"});
      }
    }
    if(el){
      var titleEl = el.querySelector('.gal-title');
      if(titleEl) crumbs.push({label: titleEl.textContent});
    }
    updateBreadcrumb(crumbs);
  }
  setActiveTab('collections');
  window.scrollTo(0,0);
}

function showInfoPage(id){
  hideAll();
  var pg = document.getElementById(id);
  if(pg){ pg.classList.add('visible'); window.scrollTo(0,0); }
  if(id==='page-about') setActiveTab('about');
}

/* ── Breadcrumb ── */
function updateBreadcrumb(crumbs){
  /* crumbs: [{label:'Home', fn:'goHome()'}, {label:'Places'}, ...] */
  ['bc-bar','gal-bc-bar'].forEach(function(barId){
    var bar = document.getElementById(barId);
    if(!bar) return;
    bar.innerHTML = '';
    crumbs.forEach(function(c, i){
      if(i > 0){
        var sep = document.createElement('span');
        sep.className = 'bc-sep'; sep.textContent = '/';
        bar.appendChild(sep);
      }
      if(c.fn && i < crumbs.length-1){
        var btn = document.createElement('button');
        btn.className = 'bc-back'; btn.textContent = c.label;
        btn.setAttribute('onclick', c.fn);
        bar.appendChild(btn);
      } else {
        var sp = document.createElement('span');
        sp.className = 'bc-current'; sp.textContent = c.label;
        bar.appendChild(sp);
      }
    });
  });
}

NAV_PANELS.forEach(function(id){
  var el = document.getElementById(id);
  if(el) el.addEventListener('animationend', function(){ this.classList.remove('page-enter'); });
});

/* ── scrollToCollections: scroll down to tile-nav from hero ── */
/* ── Recently Added: mark new photos + show banner ── */
var NEW_DAYS = 14;

var _newPhotosMarked = false;
function markNewPhotos(){
  if(_newPhotosMarked) return;
  _newPhotosMarked = true;
  var now = new Date();
  var seenPaths = {};
  var uniqueCount = 0;
  document.querySelectorAll('.section-block:not(#gallery-new-photos) .grid-item[data-date-added]').forEach(function(item){
    var da   = item.getAttribute('data-date-added');
    var path = item.getAttribute('data-photo') || '';
    if(!da) return;
    var diffDays = (now - new Date(da)) / (1000 * 60 * 60 * 24);
    if(diffDays <= NEW_DAYS && diffDays >= 0){
      var photoDiv = item.querySelector('.grid-item-photo');
      if(photoDiv && !photoDiv.querySelector('.new-badge')){
        var badge = document.createElement('div');
        badge.className = 'new-badge';
        badge.textContent = 'NEW';
        photoDiv.appendChild(badge);
      }
      if(!seenPaths[path]){
        seenPaths[path] = true;
        uniqueCount++;
      }
    }
  });
  /* Always update the banner label with the correct message */
  var label  = document.getElementById('new-photos-label');
  var banner = document.getElementById('new-photos-banner');
  if(label){
    if(uniqueCount > 0){
      label.textContent = uniqueCount + (uniqueCount === 1 ? ' photo' : ' photos')
        + ' recently added — click to view';
    } else {
      label.textContent = 'No photos added in the past ' + NEW_DAYS + ' days';
      /* Tone down the button when there is nothing new */
      if(banner){
        banner.style.opacity = '0.45';
        banner.style.cursor  = 'default';
        banner.onclick = null;
      }
    }
  }
}

function showNewPhotos(){
  /* Collect ONLY photos added within the last NEW_DAYS days, sorted newest first.
     This is the correct intent — Recently Added is not "all photos". */
  var now = new Date();
  var seenPaths = {};
  var recentItems = [];
  document.querySelectorAll('.section-block:not(#gallery-new-photos) .grid-item[data-date-added]').forEach(function(item){
    var path = item.getAttribute('data-photo') || '';
    if(seenPaths[path]) return;
    var da = item.getAttribute('data-date-added') || '';
    if(!da) return;
    var diffDays = (now - new Date(da)) / (1000 * 60 * 60 * 24);
    if(diffDays >= 0 && diffDays <= NEW_DAYS){
      seenPaths[path] = true;
      recentItems.push({item: item, da: da});
    }
  });
  /* Sort newest first */
  recentItems.sort(function(a, b){ return b.da > a.da ? 1 : -1; });
  var uniqueItems = recentItems.map(function(x){ return x.item; });
  if(!uniqueItems.length){
    showToast('No photos added in the last ' + NEW_DAYS + ' days.');
    return;
  }

  /* Step 1: run hideAll FIRST — clears all panels */
  hideAll();

  /* Step 2: show gallery container */
  var galContainer = document.getElementById('gallery-container');
  galContainer.classList.add('visible');

  /* Step 3: remove any old clone */
  var existing = document.getElementById('gallery-new-photos');
  if(existing) existing.remove();

  /* Step 4: build tags — strip Places/ location tags, keep only content category.
     Drop parent when more-specific child present (e.g. show only People & Culture/Street). */
  var gridHTML = uniqueItems.map(function(item){
    var cats = (item.getAttribute('data-cats') || '').split(',').map(function(s){ return s.trim(); }).filter(Boolean);
    /* Remove Places/ tags — location classifiers, not content categories */
    var contentCats = cats.filter(function(cat){ return cat.indexOf('Places') !== 0; });
    /* Drop parent tag when more-specific child present */
    var filtered = contentCats.filter(function(cat){
      return !contentCats.some(function(other){ return other !== cat && other.indexOf(cat+'/') === 0; });
    });
    var displayCats = filtered.length ? filtered : (contentCats.length ? contentCats : cats);
    var tagsHTML = displayCats.length
      ? '<div class="new-photo-tags">' + displayCats.map(function(cat){
          return '<span class="new-photo-tag">' + cat.replace(/[/]/g,' / ').toUpperCase() + '</span>';
        }).join('') + '</div>'
      : '';
    return '<div class="new-photo-wrap">' + item.outerHTML + tagsHTML + '</div>';
  }).join('');

  /* Step 5: create block — hideAll will remove it by id when navigating away */
  var block = document.createElement('div');
  block.id = 'gallery-new-photos';
  block.className = 'section-block visible';
  block.style.cssText = 'padding-top:calc(var(--hdr) + 32px);';
  block.innerHTML = '<div class="gal-header">'
    + '<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;">'
    + '<div><div class="gal-title">Recently Added</div>'
    + '<div class="gal-sub">' + uniqueItems.length + ' Photo' + (uniqueItems.length > 1 ? 's' : '') + ' · Added in the last ' + NEW_DAYS + ' days · Most Recent First</div></div>'
    + '<button class="slideshow-btn" onclick="startSlideshow(\x27gallery-new-photos\x27)">'
    + '<svg width="11" height="11" viewBox="0 0 11 11" fill="none"><polygon points="1,0.5 10.5,5.5 1,10.5" fill="currentColor"/></svg>'
    + 'View Slideshow</button>'
    + '</div></div>'
    + '<div class="grid">' + gridHTML + '</div>';
  galContainer.prepend(block);
  window.scrollTo(0, 0);
}

document.addEventListener('DOMContentLoaded', function(){
  markNewPhotos();
});

function scrollToCollections(){
  var tn=document.getElementById('tile-nav');
  if(tn && tn.classList.contains('visible')){
    tn.scrollIntoView({behavior:'smooth', block:'start'});
  } else {
    /* If not on home, go home first then scroll */
    goHome();
    setTimeout(function(){
      var t=document.getElementById('tile-nav');
      if(t) t.scrollIntoView({behavior:'smooth', block:'start'});
    }, 400);
  }
}

/* ── Hero slideshow ── */
(function(){
  var thumbs = window.MOHAN_CONFIG.heroThumbs;
  var hero   = document.getElementById('hero');
  if (!thumbs.length) return;
  var caption = hero.querySelector('.hero-caption');
  var imgs = thumbs.map(function(src, i){
    var img = document.createElement('img');
    img.src=src; img.className='slide';
    img.loading= i===0 ? 'eager' : 'lazy';
    img.decoding='async'; img.alt='';
    /* Insert before caption so slides go behind text */
    hero.insertBefore(img, caption);
    return img;
  });
  var cur=0; imgs[0].classList.add('active');
  setInterval(function(){
    imgs[cur].classList.remove('active');
    cur=(cur+1)%imgs.length;
    imgs[cur].classList.add('active');
  },3000);
})();

/* ── Mobile menu ── */
function openMobileMenu(){
  document.getElementById('mobile-menu').classList.add('open');
  document.body.style.overflow='hidden';
}
function closeMobileMenu(){
  document.getElementById('mobile-menu').classList.remove('open');
  document.body.style.overflow='';
}
function mobToggleCollections(){
  var sub = document.getElementById('mob-collections-sub');
  if(sub) sub.classList.toggle('open');
}

/* ── Collections dropdown ── */
function toggleCollectionsDD(e){
  e.stopPropagation();
  var tab = document.getElementById('tab-collections');
  if(tab) tab.classList.toggle('dd-open');
}
function closeCollectionsDD(){
  var tab = document.getElementById('tab-collections');
  if(tab) tab.classList.remove('dd-open');
}
/* Close dropdown when clicking outside */
document.addEventListener('click', function(e){
  if(!e.target.closest('#tab-collections')) closeCollectionsDD();
});

/* ── Stub drawer functions (kept to avoid JS errors from any old refs) ── */
function openNavDrawer(){}
function closeNavDrawer(){}
function openAboutDrawer(){}
function closeAboutDrawer(){}
function toggleDnavCat(){}

/* ── Category India/Overseas filter pills ── */
function setCatFilter(btn, regionId){
  /* Find sibling pills in the same sub-panel and toggle active */
  var panel = btn.closest('.sub-panel');
  if(!panel) return;
  panel.querySelectorAll('.places-pill').forEach(function(p){
    p.classList.remove('active');
  });
  btn.classList.add('active');
  /* Show the matching region section, hide the other */
  panel.querySelectorAll('.cat-region-section').forEach(function(s){
    s.style.display = (s.id === regionId) ? '' : 'none';
  });
}

/* ══════════════════════════════════════════════════════
   IMAGE DETAIL MODAL
   ══════════════════════════════════════════════════════ */
var imgModalImages=[], imgModalFullImages=[], imgModalIdx=0;
var imgModal      = document.getElementById('img-modal');
var imgModalImg   = document.getElementById('img-modal-img');
var imgModalCtr   = document.getElementById('img-modal-counter');
var imgModalTitle = document.getElementById('img-modal-title');
var imgModalSub   = document.getElementById('img-modal-subtitle');
var imgModalLike  = document.getElementById('img-modal-like-btn');
var imgCurrentLoad = null;
var imgPreloadCache = {};

function imgShow(src, thumbSrc){
  if(imgCurrentLoad){ imgCurrentLoad.onload=null; imgCurrentLoad.onerror=null; imgCurrentLoad=null; }
  if(thumbSrc){ imgModalImg.src=thumbSrc; imgModal.classList.remove('loading'); }
  var cached=imgPreloadCache[src];
  if(cached && cached.complete && cached.naturalWidth>0){
    imgModalImg.src=src; imgModal.classList.remove('loading');
    imgPreloadAdj(); return;
  }
  imgModal.classList.add('loading');
  var full=new Image();
  imgCurrentLoad=full;
  full.onload=function(){
    if(imgCurrentLoad!==full) return;
    imgPreloadCache[src]=full; imgCurrentLoad=null;
    imgModalImg.src=src; imgModal.classList.remove('loading');
    imgPreloadAdj();
  };
  full.onerror=function(){ if(imgCurrentLoad!==full) return; imgCurrentLoad=null; imgModal.classList.remove('loading'); };
  imgPreloadCache[src]=full; full.src=src;
}

function imgPreloadAdj(){
  [-1,1].forEach(function(d){
    var idx=(imgModalIdx+d+imgModalFullImages.length)%imgModalFullImages.length;
    var s=imgModalFullImages[idx];
    if(s&&!imgPreloadCache[s]){ var i=new Image(); i.src=s; imgPreloadCache[s]=i; }
  });
}

var imgModalItems=[];   /* current grid's .grid-item elements */

function openImgModal(el){
  var grid=el.closest('.grid'); if(!grid) return;
  imgModalItems=Array.from(grid.querySelectorAll('.grid-item'));
  var imgEls=Array.from(grid.querySelectorAll('.grid-item-photo img'));
  imgModalFullImages=imgEls.map(function(i){ return i.getAttribute('data-full')||i.src; });
  imgModalImages=imgEls.map(function(i){ return i.src; });
  imgModalIdx=imgModalItems.indexOf(el); if(imgModalIdx<0) imgModalIdx=0;
  imgModal.classList.add('open');
  document.body.style.overflow='hidden';
  updateImgModal();
}

function updateImgModal(){
  imgShow(imgModalFullImages[imgModalIdx], imgModalImages[imgModalIdx]);
  if(imgModalCtr) imgModalCtr.textContent=(imgModalIdx+1)+' / '+imgModalImages.length;
  /* Use the stored items from the current gallery — not a page-wide query */
  var item=imgModalItems[imgModalIdx];
  var key=item?item.getAttribute('data-photo'):'';
  if(imgModalLike){
    if(localLikes&&localLikes[key]){imgModalLike.classList.add('liked');}
    else{imgModalLike.classList.remove('liked');}
    imgModalLike.setAttribute('data-key', key||'');
  }
  /* Title from remarks + city of THIS photo */
  if(item){
    var rem=item.getAttribute('data-remarks')||'';
    var city=item.getAttribute('data-city')||'';
    var state=item.getAttribute('data-state')||'';
    if(imgModalTitle) imgModalTitle.textContent=rem||'Untitled';
    if(imgModalSub) imgModalSub.textContent=[city,state].filter(Boolean).join(' · ')||'';
  }
  /* Fetch live like count from Supabase */
  var countEl=document.getElementById('img-modal-like-count');
  if(countEl) countEl.textContent='';
  if(key && SUPA_URL && SUPA_URL!=='NONE'){
    supaRequest('GET','likes?photo=eq.'+encodeURIComponent(key)+'&select=photo,count')
      .then(function(rows){
        var n=rows&&rows[0]?parseInt(rows[0].count)||0:0;
        if(countEl && n>0) countEl.textContent=n;
      }).catch(function(){});
  }
}

function closeImgModal(){
  if(imgCurrentLoad){imgCurrentLoad.onload=null;imgCurrentLoad.onerror=null;imgCurrentLoad=null;}
  imgModal.classList.remove('open','loading');
  document.body.style.overflow='';
  imgModalImg.src='';
}

function imgStep(dir){
  imgModalIdx=(imgModalIdx+dir+imgModalFullImages.length)%imgModalFullImages.length;
  updateImgModal();
}

/* Touch swipe for image modal */
var imTsX=null;
imgModal.addEventListener('touchstart',function(e){
  if(e.target.closest('.img-modal-panel')) return;
  imTsX=e.touches[0].clientX;
},{passive:true});
imgModal.addEventListener('touchend',function(e){
  if(imTsX===null) return;
  var dx=e.changedTouches[0].clientX-imTsX;
  if(Math.abs(dx)>44) imgStep(dx<0?1:-1);
  imTsX=null;
});

/* Modal like button */
function imgModalToggleLike(){
  var key=imgModalLike?imgModalLike.getAttribute('data-key'):'';
  if(!key) return;
  var liked=!!localLikes[key];
  if(liked){ localLikes[key]=false; imgModalLike.classList.remove('liked'); }
  else { localLikes[key]=true; imgModalLike.classList.add('liked'); }
  localStorage.setItem('mohan_likes2',JSON.stringify(localLikes));
  /* Supabase upsert — table: likes, columns: photo(text PK), count(int) */
  if(SUPA_URL && SUPA_URL!=='NONE'){
    supaRequest('GET','likes?photo=eq.'+encodeURIComponent(key)+'&select=photo,count')
      .then(function(rows){
        var cur = rows&&rows[0] ? parseInt(rows[0].count)||0 : 0;
        var next = liked ? Math.max(0, cur-1) : cur+1;
        return supaRequest('POST','likes?on_conflict=photo',{photo:key, count:next})
          .then(function(){
            /* Refresh count display */
            var countEl=document.getElementById('img-modal-like-count');
            if(countEl) countEl.textContent = next>0 ? next : '';
          });
      }).catch(function(){});
  }
}

/* Right-click on modal image → watermarked download */
imgModalImg.addEventListener('contextmenu',function(e){
  e.preventDefault();
  var canvas=document.getElementById('lb-canvas');
  canvas.width=imgModalImg.naturalWidth; canvas.height=imgModalImg.naturalHeight;
  var ctx=canvas.getContext('2d');
  try{
    ctx.drawImage(imgModalImg,0,0);
    lbAddWatermark(ctx,canvas.width,canvas.height);
    var a=document.createElement('a');
    a.href=canvas.toDataURL('image/jpeg',0.92);
    a.download='mohangraphy-'+(imgModalIdx+1)+'.jpg';
    document.body.appendChild(a);a.click();document.body.removeChild(a);
  }catch(err){ showToast('Right-click save blocked. Contact for licensed copy.'); }
});

/* Long-press on mobile → watermark toast */
var imLpTimer=null;
imgModalImg.addEventListener('touchstart',function(){imLpTimer=setTimeout(function(){showToast('Contact info@mohangraphy.com for a licensed copy.');},800);},{passive:true});
imgModalImg.addEventListener('touchend',function(){clearTimeout(imLpTimer);},{passive:true});
imgModalImg.addEventListener('touchmove',function(){clearTimeout(imLpTimer);},{passive:true});

/* ── Slideshow image — right-click → watermarked download ──
   NOTE: uses #ss-img (the correct ID in this script, not #slideshow-img). ── */
document.addEventListener('DOMContentLoaded', function(){
  var ssImg = document.getElementById('ss-img');
  if(!ssImg) return;
  ssImg.addEventListener('contextmenu', function(e){
    e.preventDefault();
    var canvas = document.getElementById('lb-canvas');
    canvas.width  = ssImg.naturalWidth  || ssImg.offsetWidth  || 1200;
    canvas.height = ssImg.naturalHeight || ssImg.offsetHeight || 800;
    var ctx = canvas.getContext('2d');
    try{
      ctx.drawImage(ssImg, 0, 0, canvas.width, canvas.height);
      lbAddWatermark(ctx, canvas.width, canvas.height);
      var a = document.createElement('a');
      a.href = canvas.toDataURL('image/jpeg', 0.92);
      a.download = 'mohangraphy-slideshow.jpg';
      document.body.appendChild(a); a.click(); document.body.removeChild(a);
    }catch(err){ showToast('Right-click save blocked. Contact for licensed copy.'); }
  });
});

/* ══════════════════════════════════════════════════════
   REQUEST QUOTE MODAL
   ══════════════════════════════════════════════════════ */
var rqStep=1, rqSelectedSize='', rqPhotoKey='';
var rqModal=document.getElementById('rq-modal');
var rqSizes=[];

function openRqModal(){
  var key=imgModalLike?imgModalLike.getAttribute('data-key'):'';
  rqPhotoKey=key; rqStep=1; rqSelectedSize='';
  rqRender();
  rqModal.classList.add('open');
  document.body.style.overflow='hidden';
}
function closeRqModal(){
  rqModal.classList.remove('open');
  document.body.style.overflow='hidden'; /* keep img modal scroll locked */
}
function rqSelectSize(size, el){
  rqSelectedSize=size;
  document.querySelectorAll('.rq-size-card').forEach(function(c){c.classList.remove('selected');});
  if(el) el.classList.add('selected');
}
function rqNext(){
  if(rqStep===1&&!rqSelectedSize){ showToast('Please select a print size'); return; }
  rqStep=2; rqRender();
}
function rqBack(){ rqStep=1; rqRender(); }
function rqRender(){
  var s1=document.getElementById('rq-step1'), s2=document.getElementById('rq-step2');
  var st1=document.getElementById('rq-st1'), st2=document.getElementById('rq-st2');
  if(rqStep===1){
    if(s1) s1.style.display=''; if(s2) s2.style.display='none';
    if(st1){st1.className='rq-step active';} if(st2){st2.className='rq-step';}
  } else {
    if(s1) s1.style.display='none'; if(s2) s2.style.display='';
    if(st1){st1.className='rq-step done';} if(st2){st2.className='rq-step active';}
  }
}
function rqSubmit(){
  var name=(document.getElementById('rq-name')||{}).value||'';
  var email=(document.getElementById('rq-email')||{}).value||'';
  if(!name.trim()||!email.trim()){ showToast('Please fill your name and email'); return; }
  var photo=rqPhotoKey?rqPhotoKey.split('/').pop().replace(/[.][^.]+$/,''):'(see image)';
  var subject=encodeURIComponent('Print Quote Request — '+rqSelectedSize);
  var bodyStr='Name: '+name+'\nEmail: '+email+'\n\nPhoto: '+photo+'\nPrint size: '+rqSelectedSize+'\n\nPlease send me a quote.';
  window.location.href='mailto:'+window.MOHAN_CONFIG.contactEmail+'?subject='+subject+'&body='+encodeURIComponent(bodyStr);
  closeRqModal(); closeImgModal();
  showToast('Quote request sent!');
}

/* ══════════════════════════════════════════════════════
   LIKES — Supabase + localStorage
   ══════════════════════════════════════════════════════ */
var SUPA_URL  = window.MOHAN_CONFIG.supaUrl;
var SUPA_KEY  = window.MOHAN_CONFIG.supaKey;
var localLikes = JSON.parse(localStorage.getItem('mohan_likes2') || '{}');

function getPhotoKey(item){ return item.getAttribute('data-photo')||''; }

function supaRequest(method, path, body){
  if(!SUPA_URL || SUPA_URL==='NONE') return Promise.reject('no-supabase');
  return fetch(SUPA_URL+'/rest/v1/'+path, {
    method: method,
    headers: {
      'apikey': SUPA_KEY,
      'Authorization': 'Bearer '+SUPA_KEY,
      'Content-Type': 'application/json',
      'Prefer': 'resolution=merge-duplicates,return=representation'
    },
    body: body ? JSON.stringify(body) : undefined
  }).then(function(r){ return r.json(); });
}

/* Legacy barLike kept for context menu */
function barLike(btn){
  var item=btn?btn.closest('.grid-item'):null;
  if(!item) return;
  var key=getPhotoKey(item);
  if(!key) return;
  var liked=!!localLikes[key];
  if(liked){ localLikes[key]=false; if(btn) btn.classList.remove('liked'); }
  else { localLikes[key]=true; if(btn) btn.classList.add('liked'); }
  localStorage.setItem('mohan_likes2',JSON.stringify(localLikes));
}

/* ── Copy protection — intercept any text selection/copy on protected content ── */
document.addEventListener('copy', function(e){
  var sel = window.getSelection();
  if(!sel || sel.isCollapsed) return;
  var node = sel.anchorNode;
  /* Walk up the DOM to see if the selected text is inside protected content */
  var el = node && node.nodeType === 3 ? node.parentElement : node;
  while(el && el !== document.body){
    var cls = el.className || '';
    if(typeof cls === 'string' && (
        cls.indexOf('story-body') >= 0 ||
        cls.indexOf('story-post-title') >= 0 ||
        cls.indexOf('story-post-dates') >= 0 ||
        cls.indexOf('info-page-body') >= 0
    )){
      e.preventDefault();
      e.clipboardData && e.clipboardData.setData('text/plain',
        '\u00a9 N C Mohan \u00b7 mohangraphy.com \u00b7 All rights reserved');
      showToast('\u00a9 Content is copyright protected \u00b7 mohangraphy.com');
      return;
    }
    el = el.parentElement;
  }
});

// Owner mode — set automatically when admin unlocks, or manually via ?owner=yes
if(new URLSearchParams(window.location.search).get('owner')==='yes'){
  localStorage.setItem('mohan_owner','yes');
  alert('Owner mode activated — your visits will not be counted!');
}

function initVisits(){
  if(!SUPA_URL || SUPA_URL==='NONE') return;
  if(localStorage.getItem('mohan_owner')==='yes'){
    // Show count but don't increment
    supaRequest('GET','visits?id=eq.total&select=id,count')
      .then(function(rows){
        var cur=rows&&rows[0]?parseInt(rows[0].count)||0:0;
        var el=document.getElementById('visit-count');
        if(el&&cur>0) el.textContent=' \u00b7 '+cur.toLocaleString()+' visits';
      }).catch(function(){});
    return;
  }
  supaRequest('GET','visits?id=eq.total&select=id,count')
    .then(function(rows){
      var cur=rows&&rows[0]?parseInt(rows[0].count)||0:0;
      var next=cur+1;
      return supaRequest('POST','visits?on_conflict=id',{id:'total',count:next})
        .then(function(){
          var el=document.getElementById('visit-count');
          if(el&&next>0) el.textContent=' \u00b7 '+next.toLocaleString()+' visits';
        });
    }).catch(function(){});
}
document.addEventListener('DOMContentLoaded', initVisits);

function initLikes(){
  /* No grid bars — only sync state for modal */
}
document.addEventListener('DOMContentLoaded', initLikes);

/* ── Watermark helper (used for right-click download) ── */
function lbAddWatermark(ctx, w, h){
  var fontSize = Math.max(32, Math.floor(w * 0.09));
  ctx.save();
  ctx.translate(w/2, h/2); ctx.rotate(-Math.PI / 5);
  ctx.font = 'bold ' + fontSize + 'px "Cormorant Garamond", Georgia, serif';
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.shadowColor='rgba(0,0,0,0.2)'; ctx.shadowBlur=fontSize*0.15;
  ctx.shadowOffsetX=fontSize*0.03; ctx.shadowOffsetY=fontSize*0.03;
  ctx.fillStyle='rgba(255,255,255,0.18)';
  ctx.fillText('MOHANGRAPHY', 0, 0);
  ctx.restore();
}

/* ══════════════════════════════════════════════════════
   CONTEXT MENU — right-click / long-press on grid items
   ══════════════════════════════════════════════════════ */
var ctxMenu   = document.getElementById('ctx-menu');
var ctxTarget = null;

function showCtxMenu(el, x, y){
  ctxTarget=el;
  ctxMenu.style.left=Math.min(x,window.innerWidth-190)+'px';
  ctxMenu.style.top=Math.min(y,window.innerHeight-170)+'px';
  ctxMenu.style.display='block';
}
function hideCtxMenu(){ ctxMenu.style.display='none'; ctxTarget=null; }

document.addEventListener('click', function(e){ if(!e.target.closest('#ctx-menu')) hideCtxMenu(); });
document.addEventListener('contextmenu', function(e){
  /* Always block browser's native save menu on any image right-click */
  if(e.target.tagName === 'IMG') e.preventDefault();
  var item=e.target.closest('.grid-item');
  if(item){ showCtxMenu(item,e.clientX,e.clientY); }
  else hideCtxMenu();
});

var lpTimer=null, lpEl=null;
document.addEventListener('touchstart',function(e){
  var item=e.target.closest('.grid-item'); if(!item) return;
  lpEl=item; lpTimer=setTimeout(function(){ showCtxMenu(lpEl,e.touches[0].clientX,e.touches[0].clientY); },600);
},{passive:true});
document.addEventListener('touchend', function(){ clearTimeout(lpTimer); },{passive:true});
document.addEventListener('touchmove', function(){ clearTimeout(lpTimer); },{passive:true});

function ctxLike(){ var t=ctxTarget; hideCtxMenu(); if(t) openImgModal(t); }
function ctxBuy(){  var t=ctxTarget; hideCtxMenu(); if(t){ openImgModal(t); setTimeout(openRqModal,100); } }

/* ══════════════════════════════════════════════════════
   ADMIN TAG EDITOR
   ══════════════════════════════════════════════════════ */
var ADMIN_UNLOCKED = false;
var ADMIN_PASS     = window.MOHAN_CONFIG.adminPass;
var adminItems     = [];
var adminLastSaved = {state:'', city:'', cats:[]};
var CATEGORIES     = window.MOHAN_CONFIG.categories;

function ctxAdminEdit(){
  var target=ctxTarget; hideCtxMenu(); if(!target) return;
  adminItems=[target]; openAdminModal();
}

function openAdminModal(){
  var first=adminItems[0];
  var photo=first?first.getAttribute('data-photo'):'';
  var state=first?first.getAttribute('data-state'):'';
  var city=first?first.getAttribute('data-city'):'';
  var rem=first?first.getAttribute('data-remarks'):'';
  var cats=first?(first.getAttribute('data-cats')||'').split(',').filter(Boolean):[];
  if(!state&&!city&&!rem&&adminLastSaved.state) state=adminLastSaved.state;
  if(!state&&!city&&!rem&&adminLastSaved.city)  city=adminLastSaved.city;
  if(!cats.length&&adminLastSaved.cats.length)  cats=adminLastSaved.cats.slice();
  var catDiv=document.getElementById('admin-cats');
  catDiv.innerHTML='';
  CATEGORIES.forEach(function(c){
    var btn=document.createElement('button');
    btn.className='admin-cat'; btn.textContent=c.split('/').pop();
    btn.title=c; btn.setAttribute('data-cat',c);
    if(cats.indexOf(c)>-1) btn.classList.add('selected');
    btn.onclick=function(){ btn.classList.toggle('selected'); };
    catDiv.appendChild(btn);
  });
  document.getElementById('admin-photo-ref').textContent=photo.split('/').pop();
  document.getElementById('admin-count').textContent=adminItems.length+' photo(s)';
  document.getElementById('admin-state').value=state;
  document.getElementById('admin-city').value=city;
  document.getElementById('admin-remarks').value=rem;
  if(!ADMIN_UNLOCKED){
    document.getElementById('admin-pw-screen').style.display='block';
    document.getElementById('admin-edit-screen').style.display='none';
    document.getElementById('admin-pw-input').value='';
    document.getElementById('admin-pw-error').style.display='none';
  } else {
    document.getElementById('admin-pw-screen').style.display='none';
    document.getElementById('admin-edit-screen').style.display='block';
  }
  document.getElementById('admin-modal').classList.add('open');
}

function adminCheckPassword(){
  var pw=document.getElementById('admin-pw-input').value;
  if(pw!==ADMIN_PASS){ document.getElementById('admin-pw-error').style.display='block'; return; }
  ADMIN_UNLOCKED=true; document.body.classList.add('admin-unlocked');
  /* Auto-set owner mode — admin visits should never count */
  localStorage.setItem('mohan_owner','yes');
  document.getElementById('admin-pw-screen').style.display='none';
  document.getElementById('admin-choice-screen').style.display='block';
}

function adminOpenTagEditor(){
  document.getElementById('admin-choice-screen').style.display='none';
  document.getElementById('admin-edit-screen').style.display='block';
}

function adminBackToChoice(){
  document.getElementById('admin-edit-screen').style.display='none';
  document.getElementById('admin-choice-screen').style.display='block';
}

function closeAdminModal(){ document.getElementById('admin-modal').classList.remove('open'); adminItems=[]; }

function saveAdminTags(){
  var cats=Array.from(document.querySelectorAll('.admin-cat.selected')).map(function(b){return b.getAttribute('data-cat');});
  var state=document.getElementById('admin-state').value.trim();
  var city=document.getElementById('admin-city').value.trim();
  var remarks=document.getElementById('admin-remarks').value.trim();
  var photos=adminItems.map(function(item){return item.getAttribute('data-photo');});
  var payload={categories:cats,state:state,city:city,remarks:remarks,photos:photos};
  adminLastSaved={state:state,city:city,cats:cats.slice()};
  adminItems.forEach(function(item){
    item.setAttribute('data-state',state); item.setAttribute('data-city',city);
    item.setAttribute('data-remarks',remarks); item.setAttribute('data-cats',cats.join(','));
  });
  fetch('http://localhost:9393/patch',{
    method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)
  }).then(function(r){return r.json();})
    .then(function(){showToast('✓ Saved. Run deploy to publish.');})
    .catch(function(){
      navigator.clipboard.writeText(JSON.stringify(payload,null,2))
        .then(function(){showToast('Server offline. JSON copied to clipboard.');})
        .catch(function(){showToast('Start patch_tags.py, then try again.');});
    });
  closeAdminModal();
}

function toggleAdminMode(){
  /* Double-click MOHANGRAPHY logo to open admin unlock */
  if(ADMIN_UNLOCKED){
    /* Already unlocked — toggle off */
    ADMIN_UNLOCKED=false;
    document.body.classList.remove('admin-unlocked');
    showToast('Admin mode off');
  } else {
    /* Prompt for password via admin modal (with a dummy target) */
    adminItems=[document.querySelector('.grid-item')||document.body];
    openAdminModal();
    /* After unlock, dismiss and show toast */
  }
}

/* ── Toast ── */
function showToast(msg){
  var t=document.getElementById('toast');
  t.textContent=msg; t.classList.add('show');
  setTimeout(function(){ t.classList.remove('show'); },3000);
}

/* ── Contact form (Get In Touch page) ── */
function submitContact(){
  var name=(document.getElementById('cf-name')||{}).value||'';
  var email=(document.getElementById('cf-email')||{}).value||'';
  var subject=(document.getElementById('cf-subject')||{}).value||'';
  var msg=(document.getElementById('cf-msg')||{}).value||'';
  if(!name.trim()||!email.trim()||!msg.trim()){ showToast('Please fill all required fields.'); return; }
  var body=encodeURIComponent('Name: '+name+'\nEmail: '+email+'\n\n'+msg);
  window.location.href='mailto:'+window.MOHAN_CONFIG.contactEmail+'?subject='+encodeURIComponent(subject)+'&body='+body;
}

/* ── Keyboard shortcuts ── */
document.addEventListener('keydown', function(e){
  if(e.key==='Escape'){
    if(rqModal.classList.contains('open')){ closeRqModal(); return; }
    if(imgModal.classList.contains('open')){ closeImgModal(); return; }
    var am=document.getElementById('admin-modal');
    if(am&&am.classList.contains('open')){ closeAdminModal(); return; }
    closeMobileMenu();
  }
  if(imgModal.classList.contains('open')){
    if(e.key==='ArrowRight') imgStep(1);
    if(e.key==='ArrowLeft')  imgStep(-1);
  }
});

async function subscribeVisitor(){
  var name  = (document.getElementById('sub-name')  || {}).value || '';
  var email = (document.getElementById('sub-email') || {}).value || '';
  var msg   = document.getElementById('subscribe-msg');
  if(!email.trim()){ msg.textContent='Please enter your email.'; return; }
  var emailOk = email.indexOf('@') > 0 && email.lastIndexOf('.') > email.indexOf('@');
  if(!emailOk){ msg.textContent='Please enter a valid email address.'; return; }
  msg.textContent='Subscribing…';
  try{
    var res = await fetch(SUPA_URL+'/rest/v1/subscribers',{
      method:'POST',
      headers:{'apikey':SUPA_KEY,'Authorization':'Bearer '+SUPA_KEY,'Content-Type':'application/json','Prefer':'return=minimal'},
      body: JSON.stringify({name: name.trim()||null, email: email.trim().toLowerCase()})
    });
    if(res.status===201||res.status===200){
      msg.textContent='✓ Subscribed! You’ll be notified when new photos arrive.';
      document.getElementById('sub-name').value='';
      document.getElementById('sub-email').value='';
    } else if(res.status===409){
      msg.textContent='You’re already subscribed — thank you!';
    } else { msg.textContent='Something went wrong. Please try again.'; }
  } catch(err){ msg.textContent='Connection error. Please try again.'; }
}

/* ── DOM LOAD INITIALIZATION ─────────────────────────────────────────── */
/* ══════════════════════════════════════════════════════
   BLOG NOTIFICATION PANEL (FIXED)
   - No DOMContentLoaded
   - Safe UI handling
   - Proper feedback messages
   ══════════════════════════════════════════════════════ */

var BLOG_POSTS = (window.MOHAN_CONFIG && window.MOHAN_CONFIG.blogPosts) || [];

/* ── Open / close panel ── */
function openNotifyPanel(type) {
  type = type || 'blog';

  /* ── Update title ── */
  var titleEl = document.getElementById('notify-panel-title');
  if(titleEl) titleEl.textContent = type === 'photos' ? 'Photo Notification' : 'Blog Notification';

  /* ── Show/hide blog row ── */
  var blogRow = document.getElementById('notify-blog-row');
  if(blogRow) blogRow.style.display = type === 'photos' ? 'none' : 'block';

  /* ── Populate blog dropdown automatically from BLOG_POSTS ── */
  if(type === 'blog') {
    var sel = document.getElementById('notify-post-select');
    if(sel) {
      sel.innerHTML = '<option value="">-- Select a blog post --</option>';
      (BLOG_POSTS || []).forEach(function(p) {
        var opt = document.createElement('option');
        opt.value = p.id;
        opt.textContent = p.title + (p.place ? ' — ' + p.place : '') + (p.dates ? ' (' + p.dates + ')' : '');
        sel.appendChild(opt);
      });
    }
    /* ── Auto-navigate to Travel Stories page so user sees the blog ── */
    if(typeof showStoriesIndex === 'function') showStoriesIndex();
  }

  /* ── Wire up correct send/confirm buttons ── */
  var testBtn = document.getElementById('notify-test-btn');
  var sendBtn = document.getElementById('notify-send-btn');
  if(testBtn) testBtn.onclick = type === 'photos' ? notifyPhotosTest  : notifyBlogTest;
  if(sendBtn) sendBtn.onclick = type === 'photos' ? notifyPhotosConfirm : notifyBlogConfirm;

  /* ── Store type on panel for other functions ── */
  var panel = document.getElementById('notify-panel');
  if(panel) {
    panel.setAttribute('data-notify-type', type);
    panel.classList.add('open');
  }
  notifySetStatus('', '');
}

function closeNotifyPanel() {
  var panel = document.getElementById('notify-panel');
  if(panel) panel.classList.remove('open');
}

/* ── Photo notification functions ── */
function notifyPhotosTest() {
  notifyOpenGitHub({type:'photos', testOnly:true});
}

function notifyPhotosConfirm() {
  notifySetStatus(
    'This will email ALL subscribers about new photos.\n\nClick Notify All Subscribers again to confirm.',
    ''
  );
  var btn = document.getElementById('notify-send-btn');
  if(btn) {
    btn.onclick = function() {
      notifyPhotosSend();
      btn.onclick = notifyPhotosConfirm;
    };
  }
}

function notifyPhotosSend() {
  notifyOpenGitHub({type:'photos', testOnly:false});
}

function notifyOpenGitHub(opts) {
  var url = 'https://github.com/mohangraphy/mohangraphy.github.io/actions/workflows/notify.yml';
  window.open(url, '_blank');
  var lines = [
    'GitHub Actions page opened in a new tab.',
    '',
    '1. Click "Run workflow" dropdown (right side)',
    '2. Fill in:',
  ];
  if(opts.type === 'blog' && opts.post) {
    lines.push('   blog_post_title  : ' + opts.post.title);
    lines.push('   blog_post_place  : ' + (opts.post.place || ''));
    lines.push('   blog_post_summary: ' + (opts.post.summary || ''));
  }
  lines.push('   test_only : ' + (opts.testOnly ? 'true' : 'false'));
  if(opts.testOnly) lines.push('   test_email: ' + (window.MOHAN_CONFIG.contactEmail || ''));
  lines.push('');
  lines.push('3. Click the green "Run workflow" button.');
  lines.push('   Email arrives in ~60 seconds.');
  notifySetStatus(lines.join('\n'), 'ok');
}

/* ── Status display ── */
function notifySetStatus(msg, state){
  var el = document.getElementById('notify-status');
  if(!el) return;

  el.textContent = msg;
  el.className = 'notify-status' +
                 (msg ? ' visible' : '') +
                 (state ? ' ' + state : '');
}

/* ── Busy state ── */
function notifySetBusy(busy){
  ['notify-test-btn','notify-send-btn'].forEach(function(id){
    var el = document.getElementById(id);
    if(el) el.disabled = busy;
  });
}

/* ── Get selected post ── */
function notifyGetPost(){
  var sel = document.getElementById('notify-post-select');

  if(!sel || !sel.value){
    notifySetStatus('Please select a blog post first.', 'err');
    return null;
  }

  return BLOG_POSTS.find(function(p){
    return p.id === sel.value;
  }) || null;
}

/* ── TEST EMAIL ── */
function notifyBlogTest(){
  var panel = document.getElementById('notify-panel');
  var type  = panel ? (panel.getAttribute('data-notify-type') || 'blog') : 'blog';
  if(type === 'photos'){ notifyPhotosTest(); return; }
  var post = notifyGetPost();
  if(!post) return;
  notifyOpenGitHub({type:'blog', testOnly:true, post:post});
}

/* ── CONFIRM SEND ── */
function notifyBlogConfirm(){

  var post = notifyGetPost();
  if(!post) return;

  notifySetStatus(
    'This will email ALL subscribers about:\n"' +
    post.title +
    '"\n\nClick Notify again to confirm.',
    ''
  );

  var sendBtn = document.getElementById('notify-send-btn');

  if(sendBtn){
    sendBtn.onclick = function(){
      notifyBlogSend(post);
      sendBtn.onclick = notifyBlogConfirm;
    };
  }
}

/* ── SEND TO ALL ── */
function notifyBlogSend(post){
  notifyOpenGitHub({type:'blog', testOnly:false, post:post});
}

/* ── WORKFLOW TRIGGER (SAFE VERSION) ── */
function notifyCallWorkflow(post, testOnly){

  return new Promise(function(resolve){

    var url = 'https://github.com/mohangraphy/mohangraphy.github.io/actions/workflows/notify.yml';

    // Open GitHub Actions
    window.open(url, '_blank');

    var msg = [
      'GitHub Actions page opened.',
      '',
      'Run workflow with:',
      'notification_type : blog',
      'test_only         : ' + (testOnly ? 'true' : 'false'),
      (testOnly
        ? 'test_email        : ' + (window.MOHAN_CONFIG.contactEmail || '')
        : 'test_email        : (leave blank)'),
      'blog_post_id      : ' + post.id,
      'blog_post_title   : ' + post.title,
      'blog_post_place   : ' + (post.place || ''),
      'blog_post_summary : ' + (post.summary || ''),
      '',
      'Click "Run workflow". Email arrives in ~60 sec.'
    ].join('\n');

    resolve({ ok: true, msg: msg });
  });
}

/* ── Unsubscribe handler ─────────────────────────────────────────────── */
async function handleUnsubscribe(email){
  
  // Show processing overlay
  showUnsubscribePage(email, 'processing');

  try{
    var res = await fetch(
      SUPA_URL + '/rest/v1/subscribers?email=eq.' + encodeURIComponent(email),
      {
        method: 'DELETE',
        headers: {
          'apikey': SUPA_KEY,
          'Authorization': 'Bearer ' + SUPA_KEY,
          'Content-Type': 'application/json'
        }
      }
    );

    if(res.ok || res.status === 204){
      showUnsubscribePage(email, 'ok');
    } else {
      console.error('Unsubscribe failed:', res.status);
      showUnsubscribePage(email, 'err');
    }

  } catch(e){
    console.error('Fetch error:', e);
    showUnsubscribePage(email, 'err');
  }
}


/* ── Unsubscribe UI ──────────────────────────────────────────────────── */
function showUnsubscribePage(email, state){

  // Remove existing overlay if any
  var existing = document.getElementById('unsub-page');
  if(existing) existing.remove();

  var pg = document.createElement('div');
  pg.id = 'unsub-page';

  pg.style.cssText = 'position:fixed;inset:0;background:var(--dark);z-index:9999;'
    + 'display:flex;flex-direction:column;align-items:center;justify-content:center;'
    + 'padding:40px;text-align:center;gap:20px;';

  var title, msg;

  if(state === 'processing'){
    title = 'Unsubscribing…';
    msg   = 'Please wait a moment.';

  } else if(state === 'ok'){
    title = 'Unsubscribed';
    msg   = email + ' has been removed.<br>You will no longer receive notifications.';

  } else {
    title = 'Something went wrong';
    msg   = 'Could not remove ' + email + '.<br>Please email '
          + '<a href="mailto:info@mohangraphy.com" style="color:var(--gold)">info@mohangraphy.com</a>.';
  }

  var d1 = document.createElement('div');
  d1.style.cssText = 'font-family:Georgia,serif;font-size:clamp(24px,4vw,44px);'
    + 'letter-spacing:6px;text-transform:uppercase;color:#fff;';
  d1.textContent = title;

  var d2 = document.createElement('div');
  d2.style.cssText = 'font-family:Montserrat,sans-serif;font-size:13px;letter-spacing:1px;'
    + 'color:rgba(255,255,255,0.5);max-width:440px;line-height:1.8;';
  d2.innerHTML = msg;

  pg.appendChild(d1);
  pg.appendChild(d2);

  // Add button only after processing
  if(state !== 'processing'){
    var btn = document.createElement('button');
    btn.textContent = 'Back to Site';

    btn.style.cssText = 'margin-top:12px;background:none;border:1px solid rgba(201,169,110,0.5);'
      + 'color:var(--gold);padding:0 28px;height:42px;font-family:Montserrat,sans-serif;'
      + 'font-size:9px;letter-spacing:4px;text-transform:uppercase;cursor:pointer;';

    btn.onclick = function(){
      pg.remove();
      if (typeof goHome === 'function') {
        goHome();
      }
    };

    pg.appendChild(btn);
  }

  document.body.appendChild(pg);
}

/* TRAVEL STORIES — navigation */
var BLOG_PHOTO_MAP = window.MOHAN_CONFIG.blogPhotoMap;

function showStoriesIndex(){
  hideAll();
  var pg=document.getElementById('page-stories');
  if(pg){pg.classList.add('visible');pg.scrollTop=0;window.scrollTo(0,0);}
  setActiveTab('stories');
}
function showStoryPost(id){
  hideAll();
  var pg=document.getElementById(id);
  if(pg){
    pg.classList.add('visible');
    pg.scrollTop=0;
    window.scrollTo(0,0);
  }
  setActiveTab('stories');
}
function closeStoryPost(){
  document.querySelectorAll('.story-post.visible').forEach(function(p){p.classList.remove('visible');});
  showStoriesIndex();
}
function showStoryGallery(postId,placeTag){
  var paths=BLOG_PHOTO_MAP[postId]||[];
  if(!paths.length){showToast('No photos tagged yet.');return;}
  hideAll();
  var gc=document.getElementById('gallery-container');
  if(gc)gc.classList.add('visible');
  var old=document.getElementById('gallery-story-temp');
  if(old)old.remove();
  var pset={};
  paths.forEach(function(p){pset[p]=true;});
  var all=Array.from(document.querySelectorAll('.grid-item[data-photo]'));
  var matched=[],seen={};
  all.forEach(function(item){
    var p=item.getAttribute('data-photo');
    if(pset[p]&&!seen[p]){seen[p]=true;matched.push(item.outerHTML);}
  });
  var blk=document.createElement('div');
  blk.id='gallery-story-temp';
  blk.className='section-block visible';
  blk.style.cssText='padding-top:calc(var(--hdr)+32px);';
  blk.innerHTML='<div class="gal-header">'
    +'<div class="gal-title">'+placeTag+'</div>'
    +'<div class="gal-sub">'+matched.length+' Photo'
    +(matched.length!==1?'s':'')+' from '+placeTag+'</div>'
    +'</div>'
    +'<div class="grid">'+matched.join('')+'</div>'
    +'<div style="padding:20px clamp(14px,4vw,44px)">'
    +'<button id="story-back-btn" class="story-cta-btn-ghost" style="cursor:pointer">'
    +'&#8249; Back to Story</button></div>';
  gc.prepend(blk);
  var backBtn=document.getElementById('story-back-btn');
  if(backBtn){backBtn.addEventListener('click',function(){showStoryPost(postId);});}
  setActiveTab('stories');
  window.scrollTo(0,0);
}


/* ═══════════════════════════════════════════════════════
   SLIDESHOW ENGINE  —  3 s per slide, stops at last photo
   Click to pause · arrows/swipe to step · Esc to close
   ═══════════════════════════════════════════════════════ */
var _ssPhotos = [];
var _ssIdx    = 0;
var _ssTimer  = null;
var _ssFade   = null;
var _ssDur    = 3000;
var _ssPaused = false;

function startSlideshow(blockId){
  var block = document.getElementById(blockId);
  if(!block) return;
  var items = Array.from(block.querySelectorAll('.grid-item'));
  if(!items.length){ if(typeof showToast!=='undefined') showToast('No photos to show.'); return; }
  _ssPhotos = items.map(function(item){
    var img  = item.querySelector('.grid-item-photo img');
    var full = img ? (img.getAttribute('data-full') || img.src) : '';
    var th   = img ? img.src : '';
    var rem  = item.getAttribute('data-remarks') || '';
    var city = item.getAttribute('data-city') || '';
    return { thumb: th, full: full, caption: [rem,city].filter(Boolean).join('  ·  ') };
  });
  _ssIdx    = 0;
  _ssPaused = false;
  var ov = document.getElementById('ss-overlay');
  if(ov){ ov.classList.remove('ss-paused'); ov.classList.add('open'); }
  document.body.style.overflow = 'hidden';
  _ssShow(0);
  _ssSchedule();
}

function _ssShow(idx){
  if(!_ssPhotos.length) return;
  idx = (idx + _ssPhotos.length) % _ssPhotos.length;
  _ssIdx = idx;
  var entry = _ssPhotos[idx];
  var img = document.getElementById('ss-img');
  if(img) img.classList.add('ss-fade');
  clearTimeout(_ssFade);
  _ssFade = setTimeout(function(){
    var img2 = document.getElementById('ss-img');
    if(!img2) return;
    if(entry.thumb) img2.src = entry.thumb;
    img2.classList.remove('ss-fade');
    if(entry.full && entry.full !== entry.thumb){
      var hi = new Image();
      var cap = idx;
      hi.onload = function(){
        if(_ssIdx === cap){ var i3 = document.getElementById('ss-img'); if(i3) i3.src = entry.full; }
      };
      hi.src = entry.full;
    }
  }, 300);
  var ctr = document.getElementById('ss-counter');
  if(ctr) ctr.textContent = (idx+1) + ' / ' + _ssPhotos.length;
  var cap = document.getElementById('ss-caption');
  if(cap) cap.textContent = entry.caption;
  var pr = document.getElementById('ss-progress');
  if(pr){
    pr.style.transition = 'none';
    pr.style.width = '0%';
    setTimeout(function(){
      var pr2 = document.getElementById('ss-progress');
      if(pr2 && !_ssPaused){
        pr2.style.transition = 'width ' + _ssDur + 'ms linear';
        pr2.style.width = '100%';
      }
    }, 50);
  }
}

function _ssSchedule(){
  clearTimeout(_ssTimer);
  if(!_ssPaused && _ssIdx < _ssPhotos.length - 1){
    _ssTimer = setTimeout(function(){ _ssShow(_ssIdx + 1); _ssSchedule(); }, _ssDur);
  }
}

function ssPrev(){ clearTimeout(_ssTimer); _ssShow(_ssIdx - 1); if(!_ssPaused) _ssSchedule(); }
function ssNext(){ clearTimeout(_ssTimer); _ssShow(_ssIdx + 1); if(!_ssPaused) _ssSchedule(); }

function ssPauseToggle(){
  _ssPaused = !_ssPaused;
  var ov = document.getElementById('ss-overlay');
  if(ov) ov.classList.toggle('ss-paused', _ssPaused);
  var pr = document.getElementById('ss-progress');
  if(_ssPaused){
    clearTimeout(_ssTimer);
    if(pr) pr.style.transition = 'none';
  } else {
    var cur = pr ? parseFloat(pr.style.width) || 0 : 0;
    var remain = _ssDur * (1 - cur / 100);
    if(pr){ pr.style.transition = 'width '+remain+'ms linear'; pr.style.width = '100%'; }
    clearTimeout(_ssTimer);
    if(_ssIdx < _ssPhotos.length - 1){
      _ssTimer = setTimeout(function(){ _ssShow(_ssIdx + 1); _ssSchedule(); }, remain);
    }
  }
}

function ssClose(){
  clearTimeout(_ssTimer); clearTimeout(_ssFade);
  var ov = document.getElementById('ss-overlay');
  if(ov) ov.classList.remove('open','ss-paused');
  var img = document.getElementById('ss-img');
  if(img) img.src = '';
  document.body.style.overflow = '';
  _ssPaused = false;
}

document.addEventListener('DOMContentLoaded', function(){
  var wrap = document.getElementById('ss-img-wrap');
  if(!wrap) return;
  wrap.addEventListener('click', function(e){
    if(e.target.closest('#ss-prev') || e.target.closest('#ss-next') || e.target.closest('#ss-close')) return;
    ssPauseToggle();
  });
  var tsx = null;
  wrap.addEventListener('touchstart', function(e){ tsx = e.touches[0].clientX; }, {passive:true});
  wrap.addEventListener('touchend', function(e){
    if(tsx === null) return;
    var dx = e.changedTouches[0].clientX - tsx; tsx = null;
    if(Math.abs(dx) > 44){ dx < 0 ? ssNext() : ssPrev(); }
  }, {passive:true});
});

document.addEventListener('keydown', function(e){
  var ov = document.getElementById('ss-overlay');
  if(!ov || !ov.classList.contains('open')) return;
  if(e.key === 'Escape')      { ssClose();       e.preventDefault(); return; }
  if(e.key === 'ArrowRight')  { ssNext();        e.preventDefault(); return; }
  if(e.key === 'ArrowLeft')   { ssPrev();        e.preventDefault(); return; }
  if(e.key === ' ')           { ssPauseToggle(); e.preventDefault(); return; }
});

/* ══════════════════════════════════════════════════════
   DEEP-LINKING (Master Script)
   ══════════════════════════════════════════════════════ */
window.addEventListener('load', function() {
    // We wait 500ms to ensure the gallery/blog images have started loading 
    // so the scroll position is accurate.
    setTimeout(() => {
        const hash = window.location.hash;
        if (!hash) return;

        let targetId = '';

        // 1. Handle Travel Stories (Blog)
        if (hash === '#travel-stories') {
            if (typeof showStoriesIndex === 'function') showStoriesIndex();
            targetId = 'travel-stories';
        } 
        // 2. Handle Recently Added (Gallery)
        else if (hash === '#recently-added') {
            if (typeof showNewPhotos === 'function') showNewPhotos();
            targetId = 'new-photos-banner';
        }

        // 3. Precision Scroll Logic
        if (targetId) {
            const el = document.getElementById(targetId);
            if (el) {
                const headerOffset = 100; // Adjust this number to move the view up/down
                const elementPosition = el.getBoundingClientRect().top + window.pageYOffset;
                const offsetPosition = elementPosition - headerOffset;

                window.scrollTo({
                    top: offsetPosition,
                    behavior: 'smooth'
                });
            }
        }
    }, 500); 
});
