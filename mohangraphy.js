
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
  history.replaceState(null,'','#category-'+cat.replace(/ /g,'_').replace(/&/g,'n'));
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
  history.replaceState(null,'','#gallery-'+id);
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
  history.replaceState(null,'','#recently-added');
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
  history.replaceState(null,'','#travel-stories');
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
  history.replaceState(null,'','#story-'+id);
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

/* ── COMMENTS — Supabase-backed per-post comments ── */
function loadComments(postId){
  var listEl = document.getElementById('cmt-list-' + postId);
  if(!listEl) return;
  if(!SUPA_URL || SUPA_URL==='NONE'){ listEl.innerHTML='<div class="story-comments-empty">Comments unavailable.</div>'; return; }
  fetch(SUPA_URL + '/rest/v1/comments?post_id=eq.' + encodeURIComponent(postId) + '&order=created_at.asc&select=id,name,comment,created_at', {
    headers: { 'apikey': SUPA_KEY, 'Authorization': 'Bearer ' + SUPA_KEY }
  })
  .then(function(r){ return r.json(); })
  .then(function(rows){
    if(!rows || !rows.length){
      listEl.innerHTML = '<div class="story-comments-empty">No comments yet — be the first!</div>';
      return;
    }
    listEl.innerHTML = rows.map(function(c){
      var d = new Date(c.created_at);
      var dateStr = d.toLocaleDateString('en-IN', {day:'numeric', month:'short', year:'numeric'});
      return '<div class="story-comment-item" data-id="' + c.id + '">'
        + '<div class="story-comment-header">'
        + '<span class="story-comment-name">' + c.name.replace(/</g,'&lt;') + '</span>'
        + '<span style="display:flex;align-items:center;gap:12px">'
        + '<span class="story-comment-date">' + dateStr + '</span>'
        + '<button class="story-comment-delete" onclick="deleteComment(this)">&#10005; Delete</button>'
        + '</span>'
        + '</div>'
        + '<div class="story-comment-text">' + c.comment.replace(/</g,'&lt;').replace(/\n/g,'<br>') + '</div>'
        + '</div>';
    }).join('');
  })
  .catch(function(){ listEl.innerHTML='<div class="story-comments-empty">Could not load comments.</div>'; });
}

function submitComment(postId){
  var nameEl  = document.getElementById('cmt-name-'  + postId);
  var emailEl = document.getElementById('cmt-email-' + postId);
  var textEl  = document.getElementById('cmt-text-'  + postId);
  var msgEl   = document.getElementById('cmt-msg-'   + postId);
  var subEl   = document.getElementById('cmt-subscribe-' + postId);
  /* Clear placeholder feel when typing starts */
  if(textEl) textEl.style.borderColor = 'rgba(201,169,110,0.4)';
  if(!nameEl||!emailEl||!textEl||!msgEl) return;
  var name    = nameEl.value.trim();
  var email   = emailEl.value.trim();
  var comment = textEl.value.trim();
  var doSub   = subEl ? subEl.checked : false;
  if(!name){ msgEl.textContent='Please enter your name.'; return; }
  var emailRegex = /^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$/;
  if(!email || !emailRegex.test(email)){ msgEl.textContent='Please enter a valid email address (e.g. name@example.com).'; return; }
  if(!comment){ msgEl.textContent='Please write a comment.'; return; }
  msgEl.textContent = 'Posting...';
  fetch(SUPA_URL + '/rest/v1/comments', {
    method: 'POST',
    headers: {
      'apikey': SUPA_KEY, 'Authorization': 'Bearer ' + SUPA_KEY,
      'Content-Type': 'application/json', 'Prefer': 'return=minimal'
    },
    body: JSON.stringify({ post_id: postId, name: name, email: email, comment: comment })
  })
  .then(function(r){
    if(r.status===201||r.status===200){
      /* Also subscribe if checkbox is ticked */
      if(doSub && SUPA_URL && SUPA_URL!=='NONE'){
        fetch(SUPA_URL + '/rest/v1/subscribers', {
          method: 'POST',
          headers: {
            'apikey': SUPA_KEY, 'Authorization': 'Bearer ' + SUPA_KEY,
            'Content-Type': 'application/json', 'Prefer': 'return=minimal'
          },
          body: JSON.stringify({ name: name, email: email.toLowerCase() })
        }).catch(function(){});
      }
      msgEl.textContent = doSub
        ? '✓ Comment posted and you are now subscribed — thank you!'
        : '✓ Comment posted — thank you!';
      nameEl.value=''; emailEl.value=''; textEl.value='';
      setTimeout(function(){ msgEl.textContent=''; }, 5000);
      loadComments(postId);
    } else { msgEl.textContent='Something went wrong. Please try again.'; }
  })
  .catch(function(){ msgEl.textContent='Connection error. Please try again.'; });
}

function deleteComment(btn){
  var item = btn.closest('.story-comment-item');
  var commentId = item ? item.getAttribute('data-id') : null;
  /* Find postId from the comment list container */
  var listEl = item ? item.closest('[id^="cmt-list-"]') : null;
  var postId = listEl ? listEl.id.replace('cmt-list-','') : null;
  if(!commentId || !postId) return;
  if(!confirm('Delete this comment permanently?')) return;
  fetch(SUPA_URL + '/rest/v1/comments?id=eq.' + commentId, {
    method: 'DELETE',
    headers: {
      'apikey': SUPA_KEY, 'Authorization': 'Bearer ' + SUPA_KEY
    }
  })
  .then(function(r){
    if(r.status===204||r.status===200){
      showToast('Comment deleted.');
      loadComments(postId);
    } else { showToast('Could not delete. Try again.'); }
  })
  .catch(function(){ showToast('Connection error.'); });
}

/* ── COMMENT NUDGE — slides up at 75% scroll through a blog post ── */
var _nudgeSeen = {};
var _nudgeTimer = null;

function dismissNudge(scrollToComments){
  var el = document.getElementById('comment-nudge');
  if(el){ el.classList.remove('visible'); setTimeout(function(){ el.style.display='none'; }, 500); }
  clearTimeout(_nudgeTimer);
  if(scrollToComments){
    var post = document.querySelector('.story-post.visible');
    if(post){
      var comments = post.querySelector('.story-comments');
      if(comments){ comments.scrollIntoView({behavior:'smooth', block:'start'}); }
    }
  }
}

function initNudge(postId){
  /* Clear any previous timer */
  clearTimeout(_nudgeTimer);
  /* Reset seen flag */
  _nudgeSeen[postId] = false;
  /* Hide any existing nudge immediately */
  var el = document.getElementById('comment-nudge');
  if(el){
    el.classList.remove('visible');
    el.style.display = 'none';
  }
  /* Show nudge after 20 seconds */
  _nudgeTimer = setTimeout(function(){
    if(_nudgeSeen[postId]) return;
    var nudge = document.getElementById('comment-nudge');
    if(!nudge) return;
    _nudgeSeen[postId] = true;
    nudge.style.cssText = 'display:block !important; opacity:1 !important; transform:translateX(-50%) translateY(0) !important;';
    nudge.classList.add('visible');
  }, 25000);
}


/* ═══════════════════════════════════════════════════════
   JOURNEYS — Interactive map of photographic travels
   ═══════════════════════════════════════════════════════ */

var JOURNEYS_INDIA = [
  {name:'Tawang',state:'Arunachal Pradesh',lat:27.5859,lng:91.8678,uploaded:false},
  {name:'Kaziranga National Park',state:'Assam',lat:26.5775,lng:93.1711,uploaded:false},
  {name:'Bodh Gaya',state:'Bihar',lat:24.6967,lng:84.9912,uploaded:false},
  {name:'Goa',state:'Goa',lat:15.2993,lng:74.1240,uploaded:false},
  {name:'Bhuj',state:'Gujarat',lat:23.2420,lng:69.6669,uploaded:false},
  {name:'Little Rann of Kutch',state:'Gujarat',lat:23.4100,lng:71.3800,uploaded:false},
  {name:'Modhera Sun Temple',state:'Gujarat',lat:23.5833,lng:72.1300,uploaded:false},
  {name:'Dholavira',state:'Gujarat',lat:23.8877,lng:70.2165,uploaded:false},
  {name:'Rani Ki Vav',state:'Gujarat',lat:23.8579,lng:72.1011,uploaded:false},
  {name:'Sultanpur National Park',state:'Haryana',lat:28.4300,lng:76.8900,uploaded:false},
  {name:'Pilani',state:'Haryana',lat:28.3675,lng:75.6042,uploaded:false},
  {name:'Shimla',state:'Himachal Pradesh',lat:31.1048,lng:77.1734,uploaded:false},
  {name:'Narkanda',state:'Himachal Pradesh',lat:31.2636,lng:77.4470,uploaded:false},
  {name:'Fagu',state:'Himachal Pradesh',lat:31.1500,lng:77.2833,uploaded:false},
  {name:'Chail',state:'Himachal Pradesh',lat:30.9700,lng:77.2000,uploaded:false},
  {name:'Chandigarh',state:'Himachal Pradesh',lat:30.7333,lng:76.7794,uploaded:false},
  {name:'Chindi',state:'Himachal Pradesh',lat:31.5500,lng:76.9500,uploaded:false},
  {name:'Sarahan',state:'Himachal Pradesh',lat:31.5100,lng:77.7900,uploaded:false},
  {name:'Sangla',state:'Himachal Pradesh',lat:31.4154,lng:78.2374,uploaded:false},
  {name:'Chitkul',state:'Himachal Pradesh',lat:31.3500,lng:78.4400,uploaded:false},
  {name:'Dharamshala',state:'Himachal Pradesh',lat:32.2190,lng:76.3234,uploaded:false},
  {name:'McLeod Ganj',state:'Himachal Pradesh',lat:32.2427,lng:76.3234,uploaded:false},
  {name:'Dalhousie',state:'Himachal Pradesh',lat:32.5387,lng:75.9735,uploaded:false},
  {name:'Sach Pass',state:'Himachal Pradesh',lat:32.4700,lng:76.5800,uploaded:false},
  {name:'Bharmour',state:'Himachal Pradesh',lat:32.4483,lng:76.5346,uploaded:false},
  {name:'Manali',state:'Himachal Pradesh',lat:32.2396,lng:77.1887,uploaded:false},
  {name:'Keylong',state:'Himachal Pradesh',lat:32.5544,lng:77.0353,uploaded:false},
  {name:'Baralacha La',state:'Himachal Pradesh',lat:32.7400,lng:77.4000,uploaded:false},
  {name:'Suraj Taal',state:'Himachal Pradesh',lat:32.8000,lng:77.3500,uploaded:false},
  {name:'Jispa',state:'Himachal Pradesh',lat:32.6500,lng:77.1700,uploaded:false},
  {name:'Chandra Taal',state:'Himachal Pradesh',lat:32.4800,lng:77.6200,uploaded:false},
  {name:'Kullu',state:'Himachal Pradesh',lat:31.9592,lng:77.1089,uploaded:false},
  {name:'Baijnath',state:'Himachal Pradesh',lat:32.0548,lng:76.6510,uploaded:false},
  {name:'Minkiani Pass',state:'Himachal Pradesh',lat:31.8800,lng:77.2000,uploaded:false},
  {name:'Kalatop',state:'Himachal Pradesh',lat:32.5500,lng:75.9800,uploaded:false},
  {name:'Khajjiar',state:'Himachal Pradesh',lat:32.5500,lng:75.9998,uploaded:false},
  {name:'Chamba',state:'Himachal Pradesh',lat:32.5531,lng:76.1252,uploaded:false},
  {name:'Srinagar',state:'Jammu & Kashmir',lat:34.0837,lng:74.7973,uploaded:false},
  {name:'Gulmarg',state:'Jammu & Kashmir',lat:34.0484,lng:74.3805,uploaded:false},
  {name:'Pahalgam',state:'Jammu & Kashmir',lat:34.0161,lng:75.3153,uploaded:false},
  {name:'Amritsar',state:'Punjab',lat:31.6340,lng:74.8723,uploaded:false},
  {name:'Taran Taran',state:'Punjab',lat:31.4515,lng:74.9270,uploaded:false},
  {name:'Dhanbad',state:'Jharkhand',lat:23.7957,lng:86.4304,uploaded:false},
  {name:'Giridih',state:'Jharkhand',lat:24.1900,lng:86.3000,uploaded:false},
  {name:'Mysuru',state:'Karnataka',lat:12.2958,lng:76.6394,uploaded:false},
  {name:'Coorg',state:'Karnataka',lat:12.3375,lng:75.8069,uploaded:false},
  {name:'Chikmagalur',state:'Karnataka',lat:13.3153,lng:75.7754,uploaded:false},
  {name:'Gokarna',state:'Karnataka',lat:14.5479,lng:74.3188,uploaded:false},
  {name:'Murudeshwar',state:'Karnataka',lat:14.0944,lng:74.4924,uploaded:false},
  {name:'Udupi',state:'Karnataka',lat:13.3409,lng:74.7421,uploaded:false},
  {name:'Badami',state:'Karnataka',lat:15.9210,lng:75.6794,uploaded:true,galleries:['gallery-Architecture-india-Badami']},
  {name:'Pattadakal',state:'Karnataka',lat:15.9480,lng:75.8177,uploaded:true,galleries:['gallery-Architecture-india-Pattadhakal']},
  {name:'Aihole',state:'Karnataka',lat:16.0025,lng:75.8794,uploaded:true,galleries:['gallery-Architecture-india-Aihole']},
  {name:'Belur',state:'Karnataka',lat:13.1648,lng:75.8661,uploaded:false},
  {name:'Halebidu',state:'Karnataka',lat:13.2146,lng:75.9946,uploaded:false},
  {name:'Jog Falls',state:'Karnataka',lat:14.2261,lng:74.8029,uploaded:false},
  {name:'Bandipur National Park',state:'Karnataka',lat:11.6854,lng:76.6340,uploaded:false},
  {name:'Kabini',state:'Karnataka',lat:11.9300,lng:76.3500,uploaded:false},
  {name:'Kudremukh',state:'Karnataka',lat:13.1667,lng:75.2333,uploaded:false},
  {name:'Agumbe',state:'Karnataka',lat:13.5025,lng:75.0942,uploaded:false},
  {name:'Karwar',state:'Karnataka',lat:14.8135,lng:74.1288,uploaded:false},
  {name:'Maravanthe',state:'Karnataka',lat:13.7986,lng:74.6009,uploaded:false},
  {name:'Shravanabelagola',state:'Karnataka',lat:12.8553,lng:76.4893,uploaded:false},
  {name:'Sakleshpur',state:'Karnataka',lat:12.9447,lng:75.7867,uploaded:false},
  {name:'Madikeri',state:'Karnataka',lat:12.4244,lng:75.7382,uploaded:false},
  {name:'Nandi Hills',state:'Karnataka',lat:13.3702,lng:77.6835,uploaded:false},
  {name:'Munnar',state:'Kerala',lat:10.0889,lng:77.0595,uploaded:true,galleries:['gallery-Flora_n_Fauna-india-Munnar','gallery-People_n_Culture-india-Munnar']},
  {name:'Thekkady',state:'Kerala',lat:9.5988,lng:77.1633,uploaded:true,galleries:['gallery-Flora_n_Fauna-india-Thekkady']},
  {name:'Kamarakom',state:'Kerala',lat:9.5920,lng:76.5272,uploaded:false},
  {name:'Athirappilly Waterfalls',state:'Kerala',lat:10.2836,lng:76.5693,uploaded:false},
  {name:'Guruvayur',state:'Kerala',lat:10.5942,lng:76.0409,uploaded:false},
  {name:'Sabarimala',state:'Kerala',lat:9.4336,lng:77.0843,uploaded:false},
  {name:'Leh',state:'Ladakh',lat:34.1526,lng:77.5771,uploaded:false},
  {name:'Pangong',state:'Ladakh',lat:33.7500,lng:78.6700,uploaded:false},
  {name:'Tso Moriri',state:'Ladakh',lat:32.9000,lng:78.2833,uploaded:false},
  {name:'Nubra Valley',state:'Ladakh',lat:34.7700,lng:77.6800,uploaded:false},
  {name:'Stok Pass',state:'Ladakh',lat:33.9700,lng:77.6200,uploaded:false},
  {name:'Gwalior',state:'Madhya Pradesh',lat:26.2183,lng:78.1828,uploaded:false},
  {name:'Shivpuri',state:'Madhya Pradesh',lat:25.4241,lng:77.6480,uploaded:false},
  {name:'Orchha',state:'Madhya Pradesh',lat:25.3516,lng:78.6411,uploaded:false},
  {name:'Sanchi',state:'Madhya Pradesh',lat:23.4793,lng:77.7399,uploaded:false},
  {name:'Ujjain',state:'Madhya Pradesh',lat:23.1765,lng:75.7885,uploaded:false},
  {name:'Mandu',state:'Madhya Pradesh',lat:22.3576,lng:75.3968,uploaded:false},
  {name:'Omkareshwar',state:'Madhya Pradesh',lat:22.2400,lng:76.1500,uploaded:false},
  {name:'Jabalpur',state:'Madhya Pradesh',lat:23.1815,lng:79.9864,uploaded:false},
  {name:'Indore',state:'Madhya Pradesh',lat:22.7196,lng:75.8577,uploaded:false},
  {name:'Bhopal',state:'Madhya Pradesh',lat:23.2599,lng:77.4126,uploaded:false},
  {name:'Mumbai',state:'Maharashtra',lat:19.0760,lng:72.8777,uploaded:false},
  {name:'Tadoba National Park',state:'Maharashtra',lat:20.3500,lng:79.3833,uploaded:true,galleries:['gallery-Flora_n_Fauna-india-Tadoba','gallery-People_n_Culture-india-Tadoba','gallery-Landscape-india-Tadoba']},
  {name:'Panchgani',state:'Maharashtra',lat:17.9239,lng:73.8006,uploaded:false},
  {name:'Malshej Ghat',state:'Maharashtra',lat:19.4300,lng:73.7800,uploaded:false},
  {name:'Aurangabad',state:'Maharashtra',lat:19.8762,lng:75.3433,uploaded:true,galleries:['gallery-Architecture-india-Aurangabad']},
  {name:'Shillong',state:'Meghalaya',lat:25.5788,lng:91.8933,uploaded:false},
  {name:'Konark',state:'Odisha',lat:19.8876,lng:86.0945,uploaded:false},
  {name:'Gopalpur on Sea',state:'Odisha',lat:19.2581,lng:84.9040,uploaded:false},
  {name:'Bikaner',state:'Rajasthan',lat:28.0229,lng:73.3119,uploaded:false},
  {name:'Ranthambore National Park',state:'Rajasthan',lat:26.0173,lng:76.5026,uploaded:false},
  {name:'Udaipur',state:'Rajasthan',lat:24.5854,lng:73.7125,uploaded:false},
  {name:'Jaipur',state:'Rajasthan',lat:26.9124,lng:75.7873,uploaded:false},
  {name:'Pushkar',state:'Rajasthan',lat:26.4900,lng:74.5500,uploaded:false},
  {name:'Keoladeo National Park',state:'Rajasthan',lat:27.1583,lng:77.5167,uploaded:false},
  {name:'Gangtok',state:'Sikkim',lat:27.3389,lng:88.6065,uploaded:false},
  {name:'Yuksom',state:'Sikkim',lat:27.3167,lng:88.2167,uploaded:false},
  {name:'Pelling',state:'Sikkim',lat:27.3000,lng:88.2333,uploaded:false},
  {name:'Namchi',state:'Sikkim',lat:27.1667,lng:88.3667,uploaded:false},
  {name:'Zuluk',state:'Sikkim',lat:27.2000,lng:88.8167,uploaded:false},
  {name:'Nathula',state:'Sikkim',lat:27.3878,lng:88.8367,uploaded:false},
  {name:'Ravangla',state:'Sikkim',lat:27.3000,lng:88.3667,uploaded:false},
  {name:'Mahabalipuram',state:'Tamil Nadu',lat:12.6269,lng:80.1927,uploaded:false},
  {name:'Ooty',state:'Tamil Nadu',lat:11.4102,lng:76.6950,uploaded:false},
  {name:'Kodaikanal',state:'Tamil Nadu',lat:10.2381,lng:77.4892,uploaded:false},
  {name:'Madurai',state:'Tamil Nadu',lat:9.9252,lng:78.1198,uploaded:true,galleries:['gallery-Architecture-india-Madurai']},
  {name:'Tanjore',state:'Tamil Nadu',lat:10.7870,lng:79.1378,uploaded:false},
  {name:'Trichy',state:'Tamil Nadu',lat:10.8050,lng:78.6856,uploaded:false},
  {name:'Rameshwaram',state:'Tamil Nadu',lat:9.2882,lng:79.3129,uploaded:false},
  {name:'Kanyakumari',state:'Tamil Nadu',lat:8.0883,lng:77.5385,uploaded:false},
  {name:'Coimbatore',state:'Tamil Nadu',lat:11.0168,lng:76.9558,uploaded:false},
  {name:'Valparai',state:'Tamil Nadu',lat:10.3270,lng:76.9550,uploaded:false},
  {name:'Megamalai',state:'Tamil Nadu',lat:9.9500,lng:77.4167,uploaded:true,galleries:['gallery-Landscape-india-Megamalai','gallery-People_n_Culture-india-Megamalai']},
  {name:'Kumbakonam',state:'Tamil Nadu',lat:10.9602,lng:79.3845,uploaded:false},
  {name:'Chidambaram',state:'Tamil Nadu',lat:11.3992,lng:79.6931,uploaded:false},
  {name:'Kalakkad Mundanthurai Tiger Reserve',state:'Tamil Nadu',lat:8.7500,lng:77.3500,uploaded:false},
  {name:'Pichavaram Mangrove Forest',state:'Tamil Nadu',lat:11.4300,lng:79.7700,uploaded:false},
  {name:'Dhanushkodi',state:'Tamil Nadu',lat:9.1761,lng:79.4164,uploaded:false},
  {name:'Velankanni',state:'Tamil Nadu',lat:10.6836,lng:79.8519,uploaded:false},
  {name:'Agra',state:'Uttar Pradesh',lat:27.1767,lng:78.0081,uploaded:false},
  {name:'Varanasi',state:'Uttar Pradesh',lat:25.3176,lng:82.9739,uploaded:false},
  {name:'Allahabad',state:'Uttar Pradesh',lat:25.4358,lng:81.8463,uploaded:false},
  {name:'Mathura',state:'Uttar Pradesh',lat:27.4924,lng:77.6737,uploaded:false},
  {name:'Fatehpur Sikri',state:'Uttar Pradesh',lat:27.0945,lng:77.6614,uploaded:false},
  {name:'Haridwar',state:'Uttarakhand',lat:29.9457,lng:78.1642,uploaded:false},
  {name:'Rishikesh',state:'Uttarakhand',lat:30.0869,lng:78.2676,uploaded:false},
  {name:'Mussoorie',state:'Uttarakhand',lat:30.4598,lng:78.0664,uploaded:false},
  {name:'Devprayag',state:'Uttarakhand',lat:30.1461,lng:78.5965,uploaded:false},
  {name:'Joshimath',state:'Uttarakhand',lat:30.5579,lng:79.5636,uploaded:false},
  {name:'Badrinath',state:'Uttarakhand',lat:30.7433,lng:79.4938,uploaded:true,galleries:['gallery-Landscape-india-Badrinath','gallery-Flora_n_Fauna-india-Badrinath']},
  {name:'Mana Village',state:'Uttarakhand',lat:30.7700,lng:79.5300,uploaded:false},
  {name:'Valley of Flowers',state:'Uttarakhand',lat:30.7300,lng:79.6100,uploaded:true,galleries:['gallery-Landscape-india-Valley_of_Flowers','gallery-Flora_n_Fauna-india-Valley_of_Flowers']},
  {name:'Hemkund Sahib',state:'Uttarakhand',lat:30.7167,lng:79.6000,uploaded:false},
  {name:'Gangotri',state:'Uttarakhand',lat:30.9942,lng:78.9398,uploaded:false},
  {name:'Gaumukh',state:'Uttarakhand',lat:30.9197,lng:79.0736,uploaded:false},
  {name:'Kedarnath',state:'Uttarakhand',lat:30.7352,lng:79.0669,uploaded:false},
  {name:'Chaukori',state:'Uttarakhand',lat:29.8600,lng:80.4700,uploaded:false},
  {name:'Berinag',state:'Uttarakhand',lat:29.9200,lng:80.2500,uploaded:false},
  {name:'Patal Bhuvaneshwar',state:'Uttarakhand',lat:29.8700,lng:80.4200,uploaded:false},
  {name:'Munsyari',state:'Uttarakhand',lat:30.0667,lng:80.2333,uploaded:false},
  {name:'Almora',state:'Uttarakhand',lat:29.5971,lng:79.6591,uploaded:false},
  {name:'Ranikhet',state:'Uttarakhand',lat:29.6399,lng:79.4322,uploaded:false},
  {name:'Mukteshwar',state:'Uttarakhand',lat:29.4700,lng:79.6500,uploaded:false},
  {name:'Corbett National Park',state:'Uttarakhand',lat:29.5300,lng:78.7800,uploaded:false},
  {name:'Auli',state:'Uttarakhand',lat:30.5219,lng:79.5664,uploaded:false},
  {name:'Lansdowne',state:'Uttarakhand',lat:29.8378,lng:78.6872,uploaded:false},
  {name:'Rajaji Tiger Reserve',state:'Uttarakhand',lat:29.9700,lng:78.1500,uploaded:false},
];

var JOURNEYS_WORLD = [
  {name:'Adelaide',country:'Australia',lat:-34.9285,lng:138.6007,uploaded:false},
  {name:'Melbourne',country:'Australia',lat:-37.8136,lng:144.9631,uploaded:false},
  {name:'Tasmania',country:'Australia',lat:-42.0000,lng:146.5000,uploaded:false},
  {name:'Niagara Falls',country:'Canada',lat:43.0896,lng:-79.0849,uploaded:false},
  {name:'Montreal',country:'Canada',lat:45.5017,lng:-73.5673,uploaded:false},
  {name:'Quebec City',country:'Canada',lat:46.8139,lng:-71.2082,uploaded:false},
  {name:'Calgary',country:'Canada',lat:51.0447,lng:-114.0719,uploaded:true,galleries:['gallery-Landscape-overseas-Canada','gallery-Flora_n_Fauna-overseas-Canada','gallery-People_n_Culture-overseas-Canada']},
  {name:'Jasper',country:'Canada',lat:52.8737,lng:-118.0814,uploaded:true,galleries:['gallery-Landscape-overseas-Canada']},
  {name:'Waterton',country:'Canada',lat:49.0514,lng:-113.9019,uploaded:true,galleries:['gallery-Landscape-overseas-Canada']},
  {name:'Athabasca Falls',country:'Canada',lat:52.6637,lng:-117.8845,uploaded:true,galleries:['gallery-Landscape-overseas-Canada']},
  {name:'Santorini',country:'Greece',lat:36.3932,lng:25.4615,uploaded:false},
  {name:'Delphi',country:'Greece',lat:38.4824,lng:22.5010,uploaded:false},
  {name:'Hydra',country:'Greece',lat:37.3489,lng:23.4627,uploaded:false},
  {name:'Kuala Lumpur',country:'Malaysia',lat:3.1390,lng:101.6869,uploaded:false},
  {name:'Kota Kinabalu',country:'Malaysia',lat:5.9804,lng:116.0735,uploaded:false},
  {name:'Doha',country:'Qatar',lat:25.2854,lng:51.5310,uploaded:false},
  {name:'Singapore',country:'Singapore',lat:1.3521,lng:103.8198,uploaded:false},
  {name:'Bangkok',country:'Thailand',lat:13.7563,lng:100.5018,uploaded:false},
  {name:'Abu Dhabi',country:'UAE',lat:24.4539,lng:54.3773,uploaded:false},
  {name:'San Francisco',country:'USA',lat:37.7749,lng:-122.4194,uploaded:false},
  {name:'Oregon',country:'USA',lat:43.8041,lng:-120.5542,uploaded:false},
  {name:'New York',country:'USA',lat:40.7128,lng:-74.0060,uploaded:false},
  {name:'Washington DC',country:'USA',lat:38.9072,lng:-77.0369,uploaded:false},
  {name:'Maryland',country:'USA',lat:39.0458,lng:-76.6413,uploaded:false},
  {name:'Texas',country:'USA',lat:31.9686,lng:-99.9018,uploaded:false},
  {name:'New Jersey',country:'USA',lat:40.0583,lng:-74.4057,uploaded:false},
];

function showJourneys(){
  hideAll();
  var pg = document.getElementById('page-journeys');
  if(pg){ pg.classList.add('visible'); pg.scrollTop=0; window.scrollTo(0,0); }
  setActiveTab('journeys');
  history.replaceState(null,'','#journeys');
  setTimeout(function(){ initJourneysMap(); }, 200);
}

var _journeysMapIndia = null;
var _journeysMapWorld = null;
var _journeysTab = 'india';

function initJourneysMap(){
  if(_journeysTab === 'india'){
    if(!_journeysMapIndia) _buildJourneysMap('journeys-map-india', JOURNEYS_INDIA, 'india');
  } else {
    if(!_journeysMapWorld) _buildJourneysMap('journeys-map-world', JOURNEYS_WORLD, 'world');
  }
}

function switchJourneysTab(tab){
  _journeysTab = tab;
  document.querySelectorAll('.journeys-tab').forEach(function(t){ t.classList.remove('active'); });
  var bt = document.getElementById('jtab-' + tab);
  if(bt) bt.classList.add('active');
  document.getElementById('journeys-map-india').style.display = tab === 'india' ? 'block' : 'none';
  document.getElementById('journeys-map-world').style.display = tab === 'world' ? 'block' : 'none';
  initJourneysMap();
  /* Invalidate map size after display change */
  setTimeout(function(){
    if(tab === 'india' && _journeysMapIndia) _journeysMapIndia.invalidateSize();
    if(tab === 'world' && _journeysMapWorld) _journeysMapWorld.invalidateSize();
  }, 100);
}

function _buildJourneysMap(containerId, places, type){
  var centre = type === 'india' ? [22.0, 80.0] : [20.0, 15.0];
  var zoom   = type === 'india' ? 5 : 2;
  var map = L.map(containerId, {
    center: centre, zoom: zoom,
    minZoom: type === 'india' ? 4 : 2,
    maxZoom: 12,
    zoomControl: true,
    scrollWheelZoom: true,
  });
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    maxZoom: 18,
  }).addTo(map);

  function makeIcon(uploaded){
    return L.divIcon({
      className: '',
      html: '<div style="width:12px;height:12px;border-radius:50%;background:' +
            (uploaded ? '#c9a96e' : 'transparent') +
            ';border:2.5px solid #c9a96e;box-shadow:0 0 6px rgba(201,169,110,0.5);"></div>',
      iconSize: [12,12], iconAnchor: [6,6], popupAnchor: [0,-10],
    });
  }

  places.forEach(function(place){
    var marker = L.marker([place.lat, place.lng], {icon: makeIcon(place.uploaded)}).addTo(map);
    var loc = place.state || place.country || '';
    var html = '<div style="font-family:Montserrat,sans-serif;min-width:160px;">' +
      '<div style="font-size:13px;font-weight:700;color:#c9a96e;margin-bottom:3px;">' + place.name + '</div>' +
      '<div style="font-size:9px;color:#888;letter-spacing:1px;text-transform:uppercase;margin-bottom:8px;">' + loc + '</div>';
    if(place.uploaded && place.galleries && place.galleries.length){
      html += '<div style="font-size:10px;color:#4caf50;margin-bottom:6px;">&#10003; Gallery uploaded</div>';
      place.galleries.forEach(function(gid){
        var label = gid.replace('gallery-','').replace(/-india-|-overseas-/,' · ').replace(/_n_/,' & ').replace(/_/,' ');
        html += '<button onclick="showGallery(\'' + gid + '\');document.querySelectorAll(\'.leaflet-popup-close-button\').forEach(function(b){b.click();});" ' +
          'style="display:block;width:100%;margin-bottom:4px;background:none;border:1px solid #c9a96e;' +
          'color:#c9a96e;padding:5px 8px;font-family:Montserrat,sans-serif;font-size:9px;' +
          'letter-spacing:2px;text-transform:uppercase;cursor:pointer;">&#9654; ' + label + '</button>';
      });
    } else {
      html += '<div style="font-size:10px;color:#888;font-style:italic;">Photos being curated —<br>check back soon</div>';
    }
    html += '</div>';
    marker.bindPopup(html, {maxWidth:220, className:'journeys-popup'});
  });

  if(type === 'india') _journeysMapIndia = map;
  else _journeysMapWorld = map;
}

/* ── PAGE INIT — always call goHome() on first load ── */
document.addEventListener('DOMContentLoaded', function(){
  var hash = window.location.hash;
  if(hash){
    var val = hash.replace('#','');
    if(val === 'travel-stories'){ showStoriesIndex(); return; }
    if(val.indexOf('story-') === 0){
      var postId = val.replace('story-','');
      var el = document.getElementById(postId);
      if(el && el.classList.contains('story-post')){ showStoryPost(postId); return; }
    }
    if(val.indexOf('category-') === 0){
      var cat = val.replace('category-','').replace(/_/g,' ').replace(/n(?=\s|$)/g,'&');
      openCategory(cat); return;
    }
    if(val.indexOf('gallery-') === 0){
      var galId = val.replace('gallery-','');
      var galEl = document.getElementById(galId);
      if(galEl && galEl.classList.contains('section-block')){
        var parts = galId.split('-');
        if(parts.length >= 2) currentCat = parts[0].replace(/_/g,' ').replace(/n/g,'&');
        showGallery(galId); return;
      }
    }
  }
  var _origOpenCategory = openCategory;
  openCategory = function(cat){
    _origOpenCategory(cat);
    history.replaceState(null,'','#category-'+cat.replace(/ /g,'_').replace(/&/g,'n'));
  };
  var _origShowGallery = showGallery;
  showGallery = function(id, bc){
    _origShowGallery(id, bc);
    history.replaceState(null,'','#gallery-'+id);
  };
  var _origShowStoryPost = showStoryPost;
  showStoryPost = function(id){
    _origShowStoryPost(id);
    history.replaceState(null,'','#story-'+id);
    setTimeout(function(){ loadComments(id); }, 300);
  };
  var _origShowStoriesIndex = showStoriesIndex;
  showStoriesIndex = function(){
    _origShowStoriesIndex();
    history.replaceState(null,'','#travel-stories');
  };
  goHome();
});
