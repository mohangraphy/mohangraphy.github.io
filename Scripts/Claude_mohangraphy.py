import os
import json
import random

# CONFIGURATION
ROOT_DIR = "/Users/ncm/Pictures/Mohangraphy"
DATA_FILE = os.path.join(ROOT_DIR, "Scripts/photo_metadata.json")

MANUAL_STRUCTURE = {
    "Places":       ["National", "International"],
    "Nature":       ["Landscape", "Sunsets and Sunrises", "Wildlife", "Mountains"],
    "People":       ["Portraits"],
    "Architecture": [],
    "Birds":        [],
    "Flowers":      []
}

# ── Helper: pick a cover photo for a given category tag ──────────────────────
def pick_cover(photo_map, *tag_keys):
    for key in tag_keys:
        pool = photo_map.get(key, [])
        if pool:
            return random.choice(pool)
    return ""

def load_index():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}

def generate_html():
    index_data = load_index()

    photo_map  = {}   # tag → [paths]
    place_map  = {"National": {}, "International": {}}

    for info in index_data.values():
        path       = info.get('path', '')
        tags       = info.get('categories', [])
        place_name = info.get('place', 'General')
        for tag in tags:
            photo_map.setdefault(tag, []).append(path)
            if "Places/National" in tag:
                place_map["National"].setdefault(place_name, []).append(path)
            elif "Places/International" in tag:
                place_map["International"].setdefault(place_name, []).append(path)

    all_pics = [i.get('path', '') for i in index_data.values() if i.get('path')]
    slides   = random.sample(all_pics, min(len(all_pics), 10)) if all_pics else []

    # ── Cover photo per main category ────────────────────────────────────────
    cat_covers = {}
    for m_cat, subs in MANUAL_STRUCTURE.items():
        if m_cat == "Places":
            cover = pick_cover(photo_map, "Places/National", "Places/International")
        elif subs:
            cover = pick_cover(photo_map, *[f"{m_cat}/{s}" for s in subs], m_cat)
        else:
            cover = pick_cover(photo_map, m_cat)
        cat_covers[m_cat] = cover

    # ── Cover photo per sub-category ─────────────────────────────────────────
    sub_covers = {}
    for m_cat, subs in MANUAL_STRUCTURE.items():
        if m_cat == "Places":
            for group in ["National", "International"]:
                for p_name, p_list in place_map[group].items():
                    sub_covers[f"place-{p_name.replace(' ', '-')}"] = random.choice(p_list) if p_list else ""
        else:
            for s_cat in subs:
                tag   = f"{m_cat}/{s_cat}"
                cover = pick_cover(photo_map, tag)
                sub_covers[f"sub-{m_cat}-{s_cat.replace(' ', '-')}"] = cover

    logo_svg = """<svg viewBox="0 0 1200 80" xmlns="http://www.w3.org/2000/svg" class="logo-vector" onclick="goHome()">
      <text x="50%" y="55%" text-anchor="middle" dominant-baseline="middle"
            font-family="'Cormorant Garamond', serif" font-weight="700" font-size="54"
            letter-spacing="22" fill="white">MOHANGRAPHY</text>
    </svg>"""

    # ────────────────────────────────────────────────────────────────────────
    # CSS
    # ────────────────────────────────────────────────────────────────────────
    css = """
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;600;700&family=Montserrat:wght@300;400;700&display=swap');

    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --gold:   #c9a96e;
      --dark:   #0a0a0a;
      --mid:    #1a1a1a;
      --light:  #f0ece4;
      --accent: #8b6b3d;
    }

    html, body {
      background: var(--dark);
      color: #fff;
      font-family: 'Montserrat', sans-serif;
      scroll-behavior: smooth;
      overflow-x: hidden;
    }

    /* ── HEADER ── */
    header {
      position: fixed; top: 0; width: 100%; z-index: 9999;
      background: linear-gradient(to bottom, rgba(0,0,0,0.95) 70%, transparent);
      padding: 18px 0 12px;
      display: flex; flex-direction: column; align-items: center;
      transition: padding 0.4s;
    }
    header.scrolled { padding: 10px 0 8px; }

    .logo-vector { width: 90%; max-width: 700px; height: auto; cursor: pointer; display: block; }
    .logo-vector text { transition: fill 0.3s; }
    .logo-vector:hover text { fill: var(--gold); }

    .header-tagline {
      font-family: 'Cormorant Garamond', serif;
      font-size: 11px; letter-spacing: 6px; color: var(--gold);
      text-transform: uppercase; margin-top: 4px; opacity: 0.7;
    }

    /* ── HERO ── */
    #hero {
      height: 100vh; width: 100%; position: relative;
      display: flex; align-items: center; justify-content: center; background: #000;
    }
    .slide {
      position: absolute; width: 100%; height: 100%;
      object-fit: cover; opacity: 0;
      transition: opacity 3s ease-in-out;
      filter: brightness(0.35) saturate(0.8);
    }
    .slide.active { opacity: 1; }
    .hero-text {
      position: relative; z-index: 2; text-align: center; pointer-events: none;
    }
    .hero-text h2 {
      font-family: 'Cormorant Garamond', serif;
      font-size: clamp(18px, 4vw, 36px);
      font-weight: 400; letter-spacing: 8px; color: rgba(255,255,255,0.5);
      text-transform: uppercase;
    }
    .scroll-hint {
      position: absolute; bottom: 30px; left: 50%; transform: translateX(-50%);
      z-index: 2; display: flex; flex-direction: column; align-items: center; gap: 6px;
      animation: bounce 2s infinite;
    }
    .scroll-hint span { font-size: 9px; letter-spacing: 4px; color: rgba(255,255,255,0.3); }
    .scroll-hint svg { opacity: 0.3; }
    @keyframes bounce { 0%,100%{ transform:translateX(-50%) translateY(0);} 50%{ transform:translateX(-50%) translateY(6px);} }

    /* ── MAIN TILE NAVIGATION ── */
    #tile-nav {
      display: none;
      padding: 130px 0 60px;
      min-height: 100vh;
      background: var(--dark);
      flex-direction: column;
      align-items: center;
    }
    #tile-nav.visible { display: flex; }

    .tile-nav-title {
      font-family: 'Cormorant Garamond', serif;
      font-size: clamp(11px, 1.5vw, 14px);
      letter-spacing: 8px; color: var(--gold);
      text-transform: uppercase; margin-bottom: 50px;
      opacity: 0.7;
    }

    .tiles-scroll-wrapper {
      width: 100%;
      overflow-x: auto;
      padding: 20px 5vw 40px;
      cursor: grab;
      -webkit-overflow-scrolling: touch;
      scrollbar-width: thin;
      scrollbar-color: var(--gold) var(--mid);
    }
    .tiles-scroll-wrapper:active { cursor: grabbing; }
    .tiles-scroll-wrapper::-webkit-scrollbar { height: 3px; }
    .tiles-scroll-wrapper::-webkit-scrollbar-track { background: var(--mid); }
    .tiles-scroll-wrapper::-webkit-scrollbar-thumb { background: var(--gold); border-radius: 2px; }

    .tiles-row {
      display: flex; gap: 24px;
      width: max-content;
      padding-bottom: 10px;
    }

    /* Main category tile */
    .cat-tile {
      position: relative;
      width: clamp(220px, 28vw, 380px);
      height: clamp(300px, 38vw, 520px);
      overflow: hidden;
      cursor: pointer;
      flex-shrink: 0;
      border: 1px solid rgba(201,169,110,0.15);
      transition: border-color 0.4s, transform 0.5s cubic-bezier(0.25,0.46,0.45,0.94);
    }
    .cat-tile:hover { border-color: var(--gold); transform: translateY(-8px) scale(1.01); }

    .cat-tile-bg {
      position: absolute; inset: 0;
      background-size: cover; background-position: center;
      filter: brightness(0.35) saturate(0.6);
      transition: filter 0.6s, transform 0.8s cubic-bezier(0.25,0.46,0.45,0.94);
    }
    .cat-tile:hover .cat-tile-bg { filter: brightness(0.5) saturate(0.9); transform: scale(1.06); }

    .cat-tile-overlay {
      position: absolute; inset: 0;
      background: linear-gradient(to top, rgba(0,0,0,0.85) 0%, rgba(0,0,0,0.1) 60%, transparent 100%);
    }

    .cat-tile-content {
      position: absolute; bottom: 0; left: 0; right: 0;
      padding: 28px 24px 32px;
    }
    .cat-tile-name {
      font-family: 'Cormorant Garamond', serif;
      font-size: clamp(26px, 3.5vw, 42px);
      font-weight: 600; letter-spacing: 3px;
      text-transform: uppercase; color: #fff;
      line-height: 1.1;
      transition: color 0.3s;
    }
    .cat-tile:hover .cat-tile-name { color: var(--gold); }

    .cat-tile-count {
      font-size: 10px; letter-spacing: 3px; color: rgba(255,255,255,0.4);
      text-transform: uppercase; margin-top: 8px;
    }
    .cat-tile-arrow {
      position: absolute; top: 24px; right: 24px;
      opacity: 0; transform: translateX(-8px);
      transition: opacity 0.3s, transform 0.3s;
      color: var(--gold); font-size: 20px;
    }
    .cat-tile:hover .cat-tile-arrow { opacity: 1; transform: translateX(0); }

    /* ── SUB-TILE PAGE ── */
    #sub-nav {
      display: none;
      padding: 130px 5vw 80px;
      min-height: 100vh;
      background: var(--dark);
    }
    #sub-nav.visible { display: block; }

    .sub-nav-breadcrumb {
      display: flex; align-items: center; gap: 12px;
      margin-bottom: 50px;
    }
    .breadcrumb-back {
      cursor: pointer;
      font-size: 10px; letter-spacing: 4px;
      color: rgba(255,255,255,0.3);
      text-transform: uppercase; text-decoration: none;
      transition: color 0.3s;
      display: flex; align-items: center; gap: 8px;
    }
    .breadcrumb-back:hover { color: var(--gold); }
    .breadcrumb-sep { color: rgba(255,255,255,0.15); font-size: 12px; }
    .breadcrumb-current {
      font-family: 'Cormorant Garamond', serif;
      font-size: 13px; letter-spacing: 5px;
      color: var(--gold); text-transform: uppercase;
    }

    .sub-tiles-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(min(100%, 260px), 1fr));
      gap: 20px;
    }

    .sub-tile {
      position: relative;
      aspect-ratio: 4/3;
      overflow: hidden;
      cursor: pointer;
      border: 1px solid rgba(201,169,110,0.12);
      transition: border-color 0.4s, transform 0.4s ease;
    }
    .sub-tile:hover { border-color: var(--gold); transform: translateY(-5px); }

    .sub-tile-bg {
      position: absolute; inset: 0;
      background-size: cover; background-position: center;
      filter: brightness(0.3) saturate(0.5);
      transition: filter 0.5s, transform 0.7s ease;
    }
    .sub-tile:hover .sub-tile-bg { filter: brightness(0.55) saturate(0.85); transform: scale(1.07); }

    .sub-tile-overlay {
      position: absolute; inset: 0;
      background: linear-gradient(to top, rgba(0,0,0,0.9) 0%, transparent 60%);
    }
    .sub-tile-content {
      position: absolute; bottom: 0; left: 0; right: 0;
      padding: 20px 18px 22px;
    }
    .sub-tile-name {
      font-family: 'Cormorant Garamond', serif;
      font-size: clamp(18px, 2.5vw, 26px);
      letter-spacing: 2px; text-transform: uppercase;
      color: #fff; transition: color 0.3s;
    }
    .sub-tile:hover .sub-tile-name { color: var(--gold); }
    .sub-tile-wip {
      font-size: 9px; letter-spacing: 3px;
      color: rgba(255,255,255,0.3); text-transform: uppercase;
      margin-top: 5px;
    }

    /* Placeholder tile for categories with no subcategories */
    .sub-tile-placeholder .sub-tile-bg {
      background-color: var(--mid);
    }

    /* ── GALLERY ── */
    main {
      display: none; padding-top: 110px;
      width: 100%; min-height: 100vh;
      background: var(--dark);
    }
    main.visible { display: block; }

    .gallery-header {
      max-width: 1600px; margin: 0 auto;
      padding: 40px 30px 30px;
      border-bottom: 1px solid rgba(201,169,110,0.15);
      display: flex; align-items: baseline; gap: 20px;
    }
    .gallery-title {
      font-family: 'Cormorant Garamond', serif;
      font-size: clamp(28px, 5vw, 56px);
      font-weight: 600; letter-spacing: 6px;
      text-transform: uppercase; color: #fff;
    }
    .gallery-subtitle {
      font-size: 10px; letter-spacing: 4px;
      color: var(--gold); text-transform: uppercase;
    }
    .gallery-back {
      max-width: 1600px; margin: 20px auto 0;
      padding: 0 30px;
    }
    .gallery-back a {
      font-size: 10px; letter-spacing: 4px; color: rgba(255,255,255,0.3);
      text-transform: uppercase; text-decoration: none; cursor: pointer;
      transition: color 0.3s; display: inline-flex; align-items: center; gap: 8px;
    }
    .gallery-back a:hover { color: var(--gold); }

    .section-block { max-width: 1600px; margin: 0 auto 100px; padding: 30px 20px; display: none; }

    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(min(100%, 500px), 1fr));
      gap: 4px;
    }
    .grid-item {
      position: relative; overflow: hidden;
      aspect-ratio: 3/2; background: var(--mid);
      cursor: pointer;
    }
    .grid-item img {
      width: 100%; height: 100%; object-fit: cover;
      filter: grayscale(0.8) brightness(0.85);
      transition: filter 0.8s ease, transform 0.8s ease;
      display: block;
    }
    .grid-item:hover img { filter: grayscale(0) brightness(1); transform: scale(1.03); }
    .grid-item-overlay {
      position: absolute; inset: 0; background: transparent;
      transition: background 0.3s;
    }
    .grid-item:hover .grid-item-overlay {
      background: linear-gradient(to top, rgba(0,0,0,0.3) 0%, transparent 50%);
    }

    .wip-message {
      text-align: center; font-family: 'Cormorant Garamond', serif;
      font-size: clamp(16px, 3vw, 22px); color: rgba(255,255,255,0.15);
      text-transform: uppercase; letter-spacing: 8px;
      margin-top: 120px; padding-bottom: 80px;
    }

    /* ── LIGHTBOX ── */
    #lightbox {
      display: none; position: fixed; inset: 0; z-index: 99999;
      background: rgba(0,0,0,0.97);
      align-items: center; justify-content: center;
    }
    #lightbox.open { display: flex; }
    #lightbox img {
      max-width: 92vw; max-height: 88vh;
      object-fit: contain; border: 1px solid rgba(201,169,110,0.1);
    }
    .lb-close {
      position: absolute; top: 20px; right: 28px;
      font-size: 28px; color: rgba(255,255,255,0.5);
      cursor: pointer; transition: color 0.2s; z-index: 100000;
      background: none; border: none; font-family: inherit;
    }
    .lb-close:hover { color: var(--gold); }
    .lb-prev, .lb-next {
      position: absolute; top: 50%; transform: translateY(-50%);
      font-size: 32px; color: rgba(255,255,255,0.3);
      cursor: pointer; transition: color 0.2s, transform 0.2s;
      background: none; border: none; font-family: inherit; z-index: 100000;
      padding: 20px;
    }
    .lb-prev { left: 10px; }
    .lb-next { right: 10px; }
    .lb-prev:hover { color: var(--gold); transform: translateY(-50%) translateX(-3px); }
    .lb-next:hover { color: var(--gold); transform: translateY(-50%) translateX(3px); }

    /* ── FOOTER ── */
    footer {
      position: fixed; bottom: 0; width: 100%;
      background: rgba(0,0,0,0.92);
      border-top: 1px solid rgba(201,169,110,0.08);
      z-index: 9999;
      display: flex; align-items: center; justify-content: space-between;
      padding: 0 5vw; height: 44px;
    }
    .footer-left { font-size: 9px; letter-spacing: 3px; color: rgba(255,255,255,0.15); }
    .footer-links { display: flex; gap: 30px; }
    .footer-link {
      color: rgba(255,255,255,0.25); text-decoration: none;
      font-size: 9px; font-weight: 700; text-transform: uppercase; letter-spacing: 3px;
      transition: color 0.3s; cursor: pointer;
    }
    .footer-link:hover { color: var(--gold); }

    /* ── PAGE TRANSITIONS ── */
    .page-fade { animation: pageFadeIn 0.5s ease forwards; }
    @keyframes pageFadeIn { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }

    /* ── RESPONSIVE ── */
    @media (max-width: 600px) {
      .cat-tile { width: 75vw; height: 55vw; min-height: 260px; }
      .sub-tiles-grid { grid-template-columns: 1fr 1fr; gap: 10px; }
      footer { padding: 0 4vw; }
      .footer-left { display: none; }
    }
    """

    # ────────────────────────────────────────────────────────────────────────
    # BUILD HTML SECTIONS
    # ────────────────────────────────────────────────────────────────────────

    # Main category tiles
    cat_tiles_html = ""
    for m_cat in MANUAL_STRUCTURE:
        cover = cat_covers.get(m_cat, "")
        bg_style = f'background-image:url("{cover}");' if cover else "background-color:#1a1a1a;"
        
        # Count photos in this category
        count = 0
        if m_cat == "Places":
            for g in ["National", "International"]:
                for plist in place_map[g].values():
                    count += len(plist)
        else:
            for s in MANUAL_STRUCTURE[m_cat]:
                count += len(photo_map.get(f"{m_cat}/{s}", []))
            count += len(photo_map.get(m_cat, []))
        
        count_label = f"{count} Photos" if count else "Coming Soon"
        cat_tiles_html += f"""
        <div class="cat-tile" onclick="openCategory('{m_cat}')">
          <div class="cat-tile-bg" style="{bg_style}"></div>
          <div class="cat-tile-overlay"></div>
          <span class="cat-tile-arrow">→</span>
          <div class="cat-tile-content">
            <div class="cat-tile-name">{m_cat}</div>
            <div class="cat-tile-count">{count_label}</div>
          </div>
        </div>"""

    # Sub-category tile pages (one per main category)
    sub_pages_html = ""
    gallery_blocks_html = ""
    all_sub_nav_data = {}  # m_cat → list of {id, name, cover}

    for m_cat, subs in MANUAL_STRUCTURE.items():
        sub_items = []

        if m_cat == "Places":
            # Two sub-groups: National, International
            for group in ["National", "International"]:
                grp_cover = pick_cover(photo_map, f"Places/{group}")
                s_id = f"sub-places-{group.lower()}"
                # Build the inner place listing
                if place_map[group]:
                    for p_name, p_list in place_map[group].items():
                        p_id    = f"place-{p_name.replace(' ', '-')}"
                        p_cover = sub_covers.get(p_id, "")
                        sub_items.append({"id": p_id, "name": p_name, "cover": p_cover, "count": len(p_list)})
                        # Gallery block
                        gallery_blocks_html += f"""
                        <div class="section-block" id="{p_id}">
                          <div class="gallery-back"><a onclick="openSubNav(currentCat)">← Back to {m_cat}</a></div>
                          <div class="gallery-header"><span class="gallery-title">{p_name}</span><span class="gallery-subtitle">{group}</span></div>
                          <div class="grid">{''.join([f'<div class="grid-item" onclick="openLightbox(this)"><img src="{p}" loading="lazy"><div class="grid-item-overlay"></div></div>' for p in p_list])}</div>
                        </div>"""
                else:
                    sub_items.append({"id": f"wip-places-{group.lower()}", "name": group, "cover": "", "count": 0})

        else:
            if subs:
                for s_cat in subs:
                    s_id    = f"sub-{m_cat}-{s_cat.replace(' ', '-')}"
                    s_cover = sub_covers.get(s_id, "")
                    tag     = f"{m_cat}/{s_cat}"
                    photos  = photo_map.get(tag, [])
                    if s_cat == "Mountains":
                        photos = list(set(photos + photo_map.get("Nature/Landscape/Mountains", [])))
                    sub_items.append({"id": s_id, "name": s_cat, "cover": s_cover, "count": len(photos)})
                    # Gallery block
                    gallery_blocks_html += f"""
                    <div class="section-block" id="{s_id}">
                      <div class="gallery-back"><a onclick="openSubNav(currentCat)">← Back to {m_cat}</a></div>
                      <div class="gallery-header"><span class="gallery-title">{s_cat}</span><span class="gallery-subtitle">{m_cat}</span></div>
                      {'<div class="grid">' + "".join([f'<div class="grid-item" onclick="openLightbox(this)"><img src="{p}" loading="lazy"><div class="grid-item-overlay"></div></div>' for p in photos]) + '</div>' if photos else '<div class="wip-message">Work in progress</div>'}
                    </div>"""
            else:
                # No subcategories - direct gallery
                photos = photo_map.get(m_cat, [])
                sub_items.append({"id": f"direct-{m_cat}", "name": m_cat, "cover": cat_covers.get(m_cat,""), "count": len(photos)})
                gallery_blocks_html += f"""
                <div class="section-block" id="direct-{m_cat}">
                  <div class="gallery-back"><a onclick="goHome()">← Home</a></div>
                  <div class="gallery-header"><span class="gallery-title">{m_cat}</span></div>
                  {'<div class="grid">' + "".join([f'<div class="grid-item" onclick="openLightbox(this)"><img src="{p}" loading="lazy"><div class="grid-item-overlay"></div></div>' for p in photos]) + '</div>' if photos else '<div class="wip-message">Work in progress</div>'}
                </div>"""

        all_sub_nav_data[m_cat] = sub_items

    # Render sub-nav panels
    sub_nav_panels = ""
    for m_cat, items in all_sub_nav_data.items():
        tiles_inner = ""
        for item in items:
            bg = f'background-image:url("{item["cover"]}");' if item.get("cover") else "background-color:var(--mid);"
            count_lbl = f'{item["count"]} Photos' if item["count"] else "Coming Soon"
            tiles_inner += f"""
            <div class="sub-tile" onclick="showGallery('{item['id']}')">
              <div class="sub-tile-bg" style="{bg}"></div>
              <div class="sub-tile-overlay"></div>
              <div class="sub-tile-content">
                <div class="sub-tile-name">{item['name']}</div>
                <div class="sub-tile-wip">{count_lbl}</div>
              </div>
            </div>"""

        sub_nav_panels += f"""
        <div class="sub-panel page-fade" id="subpanel-{m_cat}" style="display:none;">
          <div class="sub-nav-breadcrumb">
            <a class="breadcrumb-back" onclick="goHome()">← Home</a>
            <span class="breadcrumb-sep">|</span>
            <span class="breadcrumb-current">{m_cat}</span>
          </div>
          <div class="sub-tiles-grid">{tiles_inner}</div>
        </div>"""

    # ────────────────────────────────────────────────────────────────────────
    # JAVASCRIPT
    # ────────────────────────────────────────────────────────────────────────
    js = """
    let currentCat = null;

    // ── Slideshow ──────────────────────────────────────────────────────────
    const slides = document.querySelectorAll('.slide');
    let cur = 0;
    if (slides.length) {
      slides[0].classList.add('active');
      setInterval(() => {
        slides[cur].classList.remove('active');
        cur = (cur + 1) % slides.length;
        slides[cur].classList.add('active');
      }, 5500);
    }

    // ── Drag-to-scroll on tiles row ────────────────────────────────────────
    const wrapper = document.querySelector('.tiles-scroll-wrapper');
    if (wrapper) {
      let isDown = false, startX, scrollLeft;
      wrapper.addEventListener('mousedown', e => { isDown=true; wrapper.classList.add('active'); startX=e.pageX-wrapper.offsetLeft; scrollLeft=wrapper.scrollLeft; });
      wrapper.addEventListener('mouseleave', () => { isDown=false; });
      wrapper.addEventListener('mouseup', () => { isDown=false; });
      wrapper.addEventListener('mousemove', e => { if(!isDown) return; e.preventDefault(); const x=e.pageX-wrapper.offsetLeft; wrapper.scrollLeft=scrollLeft-(x-startX)*1.5; });
    }

    // ── Header shrink on scroll ────────────────────────────────────────────
    window.addEventListener('scroll', () => {
      document.querySelector('header').classList.toggle('scrolled', window.scrollY > 60);
    });

    // ── Navigation helpers ─────────────────────────────────────────────────
    function hideAll() {
      document.getElementById('hero').style.display       = 'none';
      document.getElementById('tile-nav').classList.remove('visible');
      document.getElementById('sub-nav').classList.remove('visible');
      document.getElementById('gallery-container').classList.remove('visible');
      document.querySelectorAll('.sub-panel').forEach(p => p.style.display = 'none');
      document.querySelectorAll('.section-block').forEach(b => b.style.display = 'none');
    }

    function goHome() {
      hideAll();
      document.getElementById('hero').style.display       = 'flex';
      document.getElementById('tile-nav').classList.add('visible');
      window.scrollTo(0, 0);
    }

    function openCategory(cat) {
      currentCat = cat;
      hideAll();
      document.getElementById('sub-nav').classList.add('visible');
      const panel = document.getElementById('subpanel-' + cat);
      if (panel) { panel.style.display = 'block'; }
      window.scrollTo(0, 0);
    }

    function openSubNav(cat) {
      openCategory(cat);
    }

    function showGallery(sectionId) {
      hideAll();
      document.getElementById('gallery-container').classList.add('visible');
      const block = document.getElementById(sectionId);
      if (block) { block.style.display = 'block'; }
      window.scrollTo(0, 0);
    }

    // ── Lightbox ──────────────────────────────────────────────────────────
    let lbImages = [], lbIndex = 0;
    const lightbox = document.getElementById('lightbox');
    const lbImg    = document.getElementById('lb-image');

    function openLightbox(el) {
      const grid = el.closest('.grid');
      lbImages   = Array.from(grid.querySelectorAll('img')).map(i => i.src);
      lbIndex    = Array.from(grid.querySelectorAll('.grid-item')).indexOf(el);
      lbImg.src  = lbImages[lbIndex];
      lightbox.classList.add('open');
      document.body.style.overflow = 'hidden';
    }
    function closeLightbox() { lightbox.classList.remove('open'); document.body.style.overflow = ''; }
    function lbStep(dir) { lbIndex = (lbIndex + dir + lbImages.length) % lbImages.length; lbImg.src = lbImages[lbIndex]; }
    lightbox.addEventListener('click', e => { if (e.target === lightbox) closeLightbox(); });
    document.addEventListener('keydown', e => {
      if (!lightbox.classList.contains('open')) return;
      if (e.key === 'Escape') closeLightbox();
      if (e.key === 'ArrowRight') lbStep(1);
      if (e.key === 'ArrowLeft') lbStep(-1);
    });

    // ── Init: show hero + tile nav ─────────────────────────────────────────
    document.getElementById('tile-nav').classList.add('visible');
    document.getElementById('hero').style.display = 'flex';
    """

    # ────────────────────────────────────────────────────────────────────────
    # ASSEMBLE FINAL HTML
    # ────────────────────────────────────────────────────────────────────────
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>M O H A N G R A P H Y</title>
  <style>{css}</style>
</head>
<body>

<header>
  {logo_svg}
  <div class="header-tagline">Through the lens</div>
</header>

<!-- HERO SLIDESHOW -->
<div id="hero" style="display:flex;">
  {''.join([f'<img src="{p}" class="slide" loading="lazy">' for p in slides])}
  <div class="hero-text"><h2>Light &nbsp;·&nbsp; Moment &nbsp;·&nbsp; Story</h2></div>
  <div class="scroll-hint">
    <svg width="16" height="24" viewBox="0 0 16 24" fill="none">
      <path d="M8 3v14M3 13l5 5 5-5" stroke="white" stroke-width="1.5" stroke-linecap="round"/>
    </svg>
    <span>Explore</span>
  </div>
</div>

<!-- MAIN TILE NAV (appears below hero or replaces it on scroll) -->
<div id="tile-nav">
  <div class="tile-nav-title">Collections</div>
  <div class="tiles-scroll-wrapper">
    <div class="tiles-row">{cat_tiles_html}</div>
  </div>
</div>

<!-- SUB-CATEGORY NAV -->
<div id="sub-nav">
  {sub_nav_panels}
</div>

<!-- GALLERY -->
<main id="gallery-container">
  {gallery_blocks_html}
</main>

<!-- LIGHTBOX -->
<div id="lightbox">
  <button class="lb-close" onclick="closeLightbox()">✕</button>
  <button class="lb-prev" onclick="lbStep(-1)">‹</button>
  <img id="lb-image" src="" alt="">
  <button class="lb-next" onclick="lbStep(1)">›</button>
</div>

<footer>
  <span class="footer-left">© Mohangraphy</span>
  <div class="footer-links">
    <a class="footer-link" onclick="goHome()">Home</a>
    <a class="footer-link" href="#tile-nav">Collections</a>
  </div>
</footer>

<script>{js}</script>
</body>
</html>"""

    with open("index.html", "w") as f:
        f.write(html)
    print("✅ Build Complete: Tile-based navigation with sub-category pages generated.")

if __name__ == "__main__":
    generate_html()
