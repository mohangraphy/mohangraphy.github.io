import os
import json
import random

# ── CONFIGURATION ─────────────────────────────────────────────────────────────
ROOT_DIR  = "/Users/ncm/Pictures/Mohangraphy"
DATA_FILE = os.path.join(ROOT_DIR, "Scripts/photo_metadata.json")

MANUAL_STRUCTURE = {
    "Places":       ["National", "International"],
    "Nature":       ["Landscape", "Sunsets and Sunrises", "Wildlife", "Mountains"],
    "People":       ["Portraits"],
    "Architecture": [],
    "Birds":        [],
    "Flowers":      []
}

# ── HELPERS ───────────────────────────────────────────────────────────────────

def load_index():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, 'r') as f:
        try:
            return json.load(f)
        except Exception:
            return {}

def deduplicate_by_path(raw_data):
    """
    The JSON can have the same photo stored twice — once keyed by MD5 hash
    and once keyed by filename.  We collapse everything to ONE entry per
    unique *relative path*, so photo counts and gallery grids are correct.
    """
    seen = {}          # path → info dict
    for info in raw_data.values():
        path = info.get('path', '').strip()
        if path and path not in seen:
            seen[path] = info
    return list(seen.values())   # list of unique info dicts

def scan_folder_for_photos(folder_path):
    """Return a sorted list of relative paths for all images in a folder tree."""
    paths = []
    if not os.path.isdir(folder_path):
        return paths
    for root, _, files in os.walk(folder_path):
        for f in sorted(files):
            if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                rel = os.path.relpath(os.path.join(root, f), ROOT_DIR)
                paths.append(rel)
    return paths

def count_folder(folder_path):
    return len(scan_folder_for_photos(folder_path))

def pick_cover(paths):
    return random.choice(paths) if paths else ""


# ── BUILD PHOTO MAPS FROM DEDUPLICATED DATA ───────────────────────────────────

def build_maps(unique_entries):
    """
    Returns:
      tag_map   : category-tag  → [unique paths]
      place_map : {National:{place:[paths]}, International:{place:[paths]}}
      all_paths : [all unique paths]
    """
    tag_map   = {}
    place_map = {"National": {}, "International": {}}
    all_paths = []

    for info in unique_entries:
        path  = info.get('path', '')
        tags  = info.get('categories', [])
        place = info.get('place', 'General')

        all_paths.append(path)

        for tag in tags:
            tag_map.setdefault(tag, [])
            if path not in tag_map[tag]:
                tag_map[tag].append(path)

            if "Places/National" in tag:
                place_map["National"].setdefault(place, [])
                if path not in place_map["National"][place]:
                    place_map["National"][place].append(path)
            elif "Places/International" in tag:
                place_map["International"].setdefault(place, [])
                if path not in place_map["International"][place]:
                    place_map["International"][place].append(path)

    return tag_map, place_map, list(dict.fromkeys(all_paths))  # final dedup


# ── PHOTO COUNT: always from actual filesystem, not metadata ──────────────────

def folder_count_for_category(m_cat, subs, place_map):
    """Count images on disk for a main category."""
    if m_cat == "Places":
        n = 0
        for grp in ["National", "International"]:
            for place, paths in place_map[grp].items():
                folder = os.path.join(ROOT_DIR, "Photos", m_cat, grp, place)
                disk   = scan_folder_for_photos(folder)
                n += len(disk) if disk else len(paths)  # fallback to metadata count
        return n
    else:
        folder = os.path.join(ROOT_DIR, "Photos", m_cat)
        disk   = scan_folder_for_photos(folder)
        return len(disk) if os.path.isdir(folder) else 0


# ── MAIN BUILD ────────────────────────────────────────────────────────────────

def generate_html():
    raw_data      = load_index()
    unique        = deduplicate_by_path(raw_data)
    tag_map, place_map, all_paths = build_maps(unique)

    # Hero slideshow — pick up to 12 random unique photos
    slides = random.sample(all_paths, min(len(all_paths), 12)) if all_paths else []

    # Cover photo per main category
    cat_covers = {}
    for m_cat, subs in MANUAL_STRUCTURE.items():
        pool = []
        if m_cat == "Places":
            for grp in place_map.values():
                for p in grp.values():
                    pool.extend(p)
        else:
            for s in subs:
                pool.extend(tag_map.get(f"{m_cat}/{s}", []))
            pool.extend(tag_map.get(m_cat, []))
        cat_covers[m_cat] = pick_cover(pool)

    # ── CSS ───────────────────────────────────────────────────────────────────
    css = """
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;600;700&family=Montserrat:wght@300;400;700;900&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --gold:  #c9a96e;
  --dark:  #080808;
  --mid:   #161616;
  --dim:   #222;
  --light: #f0ece4;
  --hdr:   80px;   /* header height — used everywhere */
}

html { scroll-behavior: smooth; }
body {
  background: var(--dark);
  color: #fff;
  font-family: 'Montserrat', sans-serif;
  overflow-x: hidden;
  -webkit-tap-highlight-color: transparent;
}

/* ── HEADER ─────────────────────────────────────────────────────────────── */
header {
  position: fixed; top: 0; left: 0; right: 0;
  height: var(--hdr);
  background: rgba(8,8,8,0.96);
  backdrop-filter: blur(6px);
  border-bottom: 1px solid rgba(201,169,110,0.12);
  z-index: 9999;
  display: flex; align-items: center; justify-content: center;
  padding: 0 16px;
}
.logo-svg { height: 42px; cursor: pointer; display: block; }
.logo-svg text { transition: fill 0.3s; }
.logo-svg:hover text { fill: var(--gold); }

/* ── HERO ───────────────────────────────────────────────────────────────── */
#hero {
  position: relative;
  height: 100svh;          /* svh = safe viewport on mobile */
  width: 100%;
  overflow: hidden;
  background: #000;
  display: flex; align-items: center; justify-content: center;
}
.slide {
  position: absolute; inset: 0;
  width: 100%; height: 100%;
  object-fit: cover;
  opacity: 0;
  transition: opacity 2.8s ease-in-out;
  filter: brightness(0.32) saturate(0.75);
  will-change: opacity;
}
.slide.active { opacity: 1; }
.hero-caption {
  position: relative; z-index: 2;
  text-align: center; pointer-events: none;
  padding: 0 20px;
}
.hero-caption h2 {
  font-family: 'Cormorant Garamond', serif;
  font-size: clamp(15px, 4vw, 32px);
  font-weight: 400; letter-spacing: clamp(4px, 1.5vw, 10px);
  color: rgba(255,255,255,0.45); text-transform: uppercase;
}
.hero-caption p {
  margin-top: 12px;
  font-size: clamp(9px, 1.2vw, 11px);
  letter-spacing: 5px; color: var(--gold); opacity: 0.6;
  text-transform: uppercase;
}
.scroll-cue {
  position: absolute; bottom: 24px; left: 50%;
  transform: translateX(-50%);
  display: flex; flex-direction: column; align-items: center; gap: 6px;
  animation: cue 2.2s ease-in-out infinite;
  z-index: 2;
}
.scroll-cue span {
  font-size: 8px; letter-spacing: 4px;
  color: rgba(255,255,255,0.25); text-transform: uppercase;
}
@keyframes cue {
  0%,100% { transform: translateX(-50%) translateY(0); opacity:.4; }
  50%      { transform: translateX(-50%) translateY(7px); opacity:.9; }
}

/* ── VERTICAL TILE NAV ──────────────────────────────────────────────────── */
/*
  The main menu is a VERTICAL column of full-width tiles that scroll
  top-to-bottom (and back). Each tile is the full viewport width and
  roughly 40 % of the viewport height, giving 2.5 tiles visible at once
  so users know to scroll.  On phones each tile is ~55 vw tall.
*/
#tile-nav {
  display: none;
  padding-top: var(--hdr);
  background: var(--dark);
  min-height: 100svh;
}
#tile-nav.visible { display: block; }

.tile-nav-label {
  font-family: 'Cormorant Garamond', serif;
  font-size: 10px; letter-spacing: 7px;
  color: var(--gold); text-transform: uppercase; opacity: .65;
  text-align: center;
  padding: 28px 0 18px;
}

/* Each main-category tile */
.cat-tile {
  position: relative;
  width: 100%;
  height: clamp(200px, 40svh, 420px);
  overflow: hidden;
  cursor: pointer;
  border-bottom: 1px solid rgba(201,169,110,0.08);
  /* no flex/grid needed — they stack naturally */
}
.cat-tile-bg {
  position: absolute; inset: 0;
  background-size: cover; background-position: center;
  filter: brightness(0.28) saturate(0.6);
  transition: filter .7s ease, transform .8s ease;
  will-change: transform, filter;
}
.cat-tile:hover .cat-tile-bg,
.cat-tile:focus .cat-tile-bg {
  filter: brightness(0.5) saturate(0.9);
  transform: scale(1.04);
}
.cat-tile-vignette {
  position: absolute; inset: 0;
  background:
    linear-gradient(to right,  rgba(0,0,0,0.55) 0%, transparent 40%),
    linear-gradient(to top,    rgba(0,0,0,0.7)  0%, transparent 55%);
}
.cat-tile-content {
  position: absolute; bottom: 0; left: 0; right: 0;
  padding: clamp(16px, 3vw, 36px) clamp(20px, 5vw, 60px);
  display: flex; align-items: flex-end; justify-content: space-between;
}
.cat-tile-name {
  font-family: 'Cormorant Garamond', serif;
  font-size: clamp(28px, 6vw, 64px);
  font-weight: 600; letter-spacing: clamp(2px, 1vw, 6px);
  text-transform: uppercase; color: #fff; line-height: 1;
  transition: color .3s;
}
.cat-tile:hover .cat-tile-name { color: var(--gold); }
.cat-tile-meta {
  text-align: right; flex-shrink: 0; padding-left: 16px;
}
.cat-tile-count {
  display: block;
  font-size: clamp(9px, 1.1vw, 11px); letter-spacing: 3px;
  color: rgba(255,255,255,0.35); text-transform: uppercase; margin-bottom: 6px;
}
.cat-tile-arrow {
  font-size: clamp(18px, 3vw, 28px);
  color: var(--gold); opacity: 0;
  transform: translateX(-6px);
  transition: opacity .3s, transform .3s;
  display: block;
}
.cat-tile:hover .cat-tile-arrow { opacity: 1; transform: translateX(0); }

/* ── SUB-CATEGORY PAGE ──────────────────────────────────────────────────── */
#sub-nav {
  display: none;
  padding-top: var(--hdr);
  background: var(--dark);
  min-height: 100svh;
}
#sub-nav.visible { display: block; }

.breadcrumb-bar {
  display: flex; align-items: center; gap: 10px;
  padding: 18px clamp(16px,4vw,48px);
  border-bottom: 1px solid rgba(201,169,110,0.1);
}
.bc-back {
  font-size: 9px; letter-spacing: 4px; color: rgba(255,255,255,0.3);
  text-transform: uppercase; cursor: pointer;
  transition: color .3s;
  background: none; border: none; color: rgba(255,255,255,0.3);
  font-family: 'Montserrat', sans-serif;
  display: flex; align-items: center; gap: 6px;
}
.bc-back:hover { color: var(--gold); }
.bc-sep { color: rgba(255,255,255,0.1); }
.bc-current {
  font-family: 'Cormorant Garamond', serif;
  font-size: 13px; letter-spacing: 5px;
  color: var(--gold); text-transform: uppercase;
}

.sub-panel { display: none; }
.sub-panel.active { display: block; }

/* Sub-tiles: same vertical stacking as main, but shorter */
.sub-tile {
  position: relative;
  width: 100%;
  height: clamp(140px, 28svh, 280px);
  overflow: hidden; cursor: pointer;
  border-bottom: 1px solid rgba(201,169,110,0.07);
}
.sub-tile-bg {
  position: absolute; inset: 0;
  background-size: cover; background-position: center;
  filter: brightness(0.25) saturate(0.5);
  transition: filter .6s ease, transform .7s ease;
}
.sub-tile:hover .sub-tile-bg {
  filter: brightness(0.5) saturate(0.85);
  transform: scale(1.05);
}
.sub-tile-vignette {
  position: absolute; inset: 0;
  background: linear-gradient(to top, rgba(0,0,0,0.85) 0%, transparent 60%);
}
.sub-tile-content {
  position: absolute; bottom: 0; left: 0; right: 0;
  padding: clamp(12px,2.5vw,28px) clamp(16px,4vw,48px);
  display: flex; align-items: flex-end; justify-content: space-between;
}
.sub-tile-name {
  font-family: 'Cormorant Garamond', serif;
  font-size: clamp(20px, 4.5vw, 46px);
  letter-spacing: clamp(1px,.8vw,4px); text-transform: uppercase;
  color: #fff; transition: color .3s;
}
.sub-tile:hover .sub-tile-name { color: var(--gold); }
.sub-tile-count {
  font-size: 9px; letter-spacing: 3px;
  color: rgba(255,255,255,0.3); text-transform: uppercase;
  flex-shrink: 0; padding-left: 12px; text-align: right;
}
.sub-tile-wip { font-size: 9px; letter-spacing: 3px; color: rgba(255,255,255,0.2); text-transform: uppercase; }

/* ── GALLERY ─────────────────────────────────────────────────────────────── */
#gallery-container {
  display: none;
  padding-top: var(--hdr);
  min-height: 100svh;
  background: var(--dark);
}
#gallery-container.visible { display: block; }

.gal-header {
  padding: clamp(24px,4vw,48px) clamp(16px,4vw,48px) clamp(12px,2vw,24px);
  border-bottom: 1px solid rgba(201,169,110,0.12);
}
.gal-breadcrumb {
  font-size: 9px; letter-spacing: 4px; color: rgba(255,255,255,0.25);
  text-transform: uppercase; margin-bottom: 10px; cursor: pointer;
  display: inline-flex; align-items: center; gap: 6px;
  transition: color .3s;
}
.gal-breadcrumb:hover { color: var(--gold); }
.gal-title {
  font-family: 'Cormorant Garamond', serif;
  font-size: clamp(24px, 6vw, 64px);
  font-weight: 600; letter-spacing: clamp(3px,1vw,8px);
  text-transform: uppercase;
}
.gal-sub {
  font-size: 10px; letter-spacing: 5px;
  color: var(--gold); text-transform: uppercase; margin-top: 6px; opacity: .7;
}

.section-block { display: none; padding-bottom: 80px; }

/* Masonry-style responsive grid */
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(100%, 360px), 1fr));
  gap: 3px;
  padding: 3px;
}
@media (max-width: 480px) {
  .grid { grid-template-columns: 1fr; gap: 2px; padding: 2px; }
}

.grid-item {
  position: relative; overflow: hidden;
  aspect-ratio: 3/2; background: var(--mid);
  cursor: pointer;
}
.grid-item img {
  width: 100%; height: 100%; object-fit: cover; display: block;
  filter: grayscale(0.6) brightness(0.88);
  transition: filter .7s ease, transform .7s ease;
}
.grid-item:hover img { filter: grayscale(0) brightness(1); transform: scale(1.04); }
.grid-item-overlay {
  position: absolute; inset: 0;
  background: transparent; transition: background .3s;
  pointer-events: none;
}
.grid-item:hover .grid-item-overlay {
  background: linear-gradient(to top, rgba(0,0,0,0.25) 0%, transparent 50%);
}

.wip-message {
  text-align: center; padding: 100px 20px;
  font-family: 'Cormorant Garamond', serif;
  font-size: clamp(16px,3vw,24px);
  color: rgba(255,255,255,0.12); text-transform: uppercase; letter-spacing: 8px;
}

/* ── LIGHTBOX ────────────────────────────────────────────────────────────── */
#lightbox {
  display: none; position: fixed; inset: 0; z-index: 99999;
  background: rgba(0,0,0,0.97);
  align-items: center; justify-content: center;
  touch-action: none;
}
#lightbox.open { display: flex; }
#lb-image {
  max-width: 94vw; max-height: 88svh;
  object-fit: contain; display: block;
  border: 1px solid rgba(201,169,110,0.08);
  user-select: none;
}
.lb-btn {
  position: absolute;
  background: none; border: none; cursor: pointer;
  color: rgba(255,255,255,0.35); transition: color .2s;
  font-family: inherit; z-index: 100;
}
.lb-btn:hover { color: var(--gold); }
#lb-close { top: 16px; right: 20px; font-size: 26px; }
#lb-prev   { left:  10px; top: 50%; transform: translateY(-50%); font-size: 36px; padding: 16px; }
#lb-next   { right: 10px; top: 50%; transform: translateY(-50%); font-size: 36px; padding: 16px; }
.lb-counter {
  position: absolute; bottom: 16px; left: 50%; transform: translateX(-50%);
  font-size: 9px; letter-spacing: 3px; color: rgba(255,255,255,0.25);
  text-transform: uppercase; white-space: nowrap;
}

/* ── FOOTER ──────────────────────────────────────────────────────────────── */
footer {
  position: fixed; bottom: 0; left: 0; right: 0;
  height: 44px; background: rgba(8,8,8,0.94);
  border-top: 1px solid rgba(201,169,110,0.07);
  z-index: 9998;
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 clamp(12px,4vw,40px);
}
.footer-copy { font-size: 8px; letter-spacing: 3px; color: rgba(255,255,255,0.12); }
.footer-links { display: flex; gap: 24px; }
.footer-link {
  font-size: 8px; font-weight: 700; letter-spacing: 3px;
  color: rgba(255,255,255,0.22); text-transform: uppercase;
  text-decoration: none; cursor: pointer; transition: color .3s;
  background: none; border: none; font-family: 'Montserrat', sans-serif;
}
.footer-link:hover { color: var(--gold); }

/* ── PAGE TRANSITIONS ────────────────────────────────────────────────────── */
.page-enter { animation: pEnter .4s ease forwards; }
@keyframes pEnter { from { opacity:0; transform:translateY(14px); } to { opacity:1; transform:none; } }
    """

    # ── GALLERY BLOCKS + SUB-PANELS ──────────────────────────────────────────
    gallery_blocks = ""
    sub_panels     = ""

    for m_cat, subs in MANUAL_STRUCTURE.items():
        sub_items = []   # [{id, name, cover, count}]

        if m_cat == "Places":
            for group in ["National", "International"]:
                places = place_map[group]
                if places:
                    for p_name, p_paths in places.items():
                        # Count from disk; fall back to unique metadata paths
                        disk_folder = os.path.join(ROOT_DIR, "Photos", m_cat, group, p_name)
                        disk_paths  = scan_folder_for_photos(disk_folder)
                        display_paths = disk_paths if disk_paths else list(dict.fromkeys(p_paths))
                        s_id    = f"place-{group}-{p_name.replace(' ', '-')}"
                        s_cover = pick_cover(display_paths)
                        sub_items.append({"id": s_id, "name": p_name,
                                          "cover": s_cover, "count": len(display_paths),
                                          "subtitle": group})
                        imgs = "".join([
                            f'<div class="grid-item" onclick="openLightbox(this)">'
                            f'<img src="{p}" loading="lazy" alt="">'
                            f'<div class="grid-item-overlay"></div></div>'
                            for p in display_paths
                        ])
                        gallery_blocks += f"""
<div class="section-block" id="{s_id}">
  <div class="gal-header">
    <div class="gal-breadcrumb" onclick="openSubNav(currentCat)">← Back to {m_cat}</div>
    <div class="gal-title">{p_name}</div>
    <div class="gal-sub">{group} · {len(display_paths)} Photos</div>
  </div>
  <div class="grid">{imgs if display_paths else '<div class="wip-message">Work in progress</div>'}</div>
</div>"""
                else:
                    sub_items.append({"id": f"wip-{m_cat}-{group}", "name": group,
                                      "cover": "", "count": 0, "subtitle": "Coming soon"})

        elif subs:
            for s_cat in subs:
                tag          = f"{m_cat}/{s_cat}"
                meta_paths   = list(dict.fromkeys(tag_map.get(tag, [])))
                # Also absorb nested tag paths (e.g. Nature/Landscape/Mountains)
                nested_tag   = f"{tag}/Mountains" if s_cat == "Mountains" else None
                if nested_tag:
                    for p in tag_map.get(nested_tag, []):
                        if p not in meta_paths:
                            meta_paths.append(p)
                # Disk count
                disk_folder  = os.path.join(ROOT_DIR, "Photos", m_cat, s_cat)
                disk_paths   = scan_folder_for_photos(disk_folder)
                display_paths = disk_paths if disk_paths else meta_paths
                s_id    = f"sub-{m_cat}-{s_cat.replace(' ', '-')}"
                s_cover = pick_cover(display_paths)
                sub_items.append({"id": s_id, "name": s_cat,
                                  "cover": s_cover, "count": len(display_paths),
                                  "subtitle": m_cat})
                imgs = "".join([
                    f'<div class="grid-item" onclick="openLightbox(this)">'
                    f'<img src="{p}" loading="lazy" alt="">'
                    f'<div class="grid-item-overlay"></div></div>'
                    for p in display_paths
                ])
                gallery_blocks += f"""
<div class="section-block" id="{s_id}">
  <div class="gal-header">
    <div class="gal-breadcrumb" onclick="openSubNav(currentCat)">← Back to {m_cat}</div>
    <div class="gal-title">{s_cat}</div>
    <div class="gal-sub">{m_cat} · {len(display_paths)} Photos</div>
  </div>
  <div class="grid">{imgs if display_paths else '<div class="wip-message">Work in progress</div>'}</div>
</div>"""

        else:
            # No subcategories — direct gallery
            disk_folder   = os.path.join(ROOT_DIR, "Photos", m_cat)
            disk_paths    = scan_folder_for_photos(disk_folder)
            meta_paths    = list(dict.fromkeys(tag_map.get(m_cat, [])))
            display_paths = disk_paths if disk_paths else meta_paths
            s_id    = f"direct-{m_cat}"
            s_cover = pick_cover(display_paths)
            sub_items.append({"id": s_id, "name": m_cat,
                              "cover": s_cover, "count": len(display_paths),
                              "subtitle": ""})
            imgs = "".join([
                f'<div class="grid-item" onclick="openLightbox(this)">'
                f'<img src="{p}" loading="lazy" alt="">'
                f'<div class="grid-item-overlay"></div></div>'
                for p in display_paths
            ])
            gallery_blocks += f"""
<div class="section-block" id="{s_id}">
  <div class="gal-header">
    <div class="gal-breadcrumb" onclick="goHome()">← Home</div>
    <div class="gal-title">{m_cat}</div>
    <div class="gal-sub">{len(display_paths)} Photos</div>
  </div>
  <div class="grid">{imgs if display_paths else '<div class="wip-message">Work in progress</div>'}</div>
</div>"""

        # Build sub-panel HTML for this category
        sub_tiles_html = ""
        for item in sub_items:
            bg  = f'background-image:url("{item["cover"]}");' if item.get("cover") else "background:#161616;"
            cnt = f'{item["count"]} Photos' if item["count"] else "Coming Soon"
            sub_tiles_html += f"""
<div class="sub-tile" onclick="showGallery('{item['id']}')">
  <div class="sub-tile-bg" style="{bg}"></div>
  <div class="sub-tile-vignette"></div>
  <div class="sub-tile-content">
    <div class="sub-tile-name">{item['name']}</div>
    <div class="sub-tile-count">{cnt}</div>
  </div>
</div>"""

        sub_panels += f"""
<div class="sub-panel" id="subpanel-{m_cat}">
  {sub_tiles_html}
</div>"""

    # ── MAIN CATEGORY TILES ───────────────────────────────────────────────────
    cat_tiles_html = ""
    for m_cat, subs in MANUAL_STRUCTURE.items():
        cover = cat_covers.get(m_cat, "")
        bg    = f'background-image:url("{cover}");' if cover else "background:#161616;"

        # Disk-based count
        disk_folder = os.path.join(ROOT_DIR, "Photos", m_cat)
        disk_cnt    = count_folder(disk_folder)
        count_lbl   = f"{disk_cnt} Photos" if disk_cnt else "Coming Soon"

        # If no subs, clicking a tile goes straight to gallery
        click = f"openCategory('{m_cat}')" if subs else f"showGallery('direct-{m_cat}')"

        cat_tiles_html += f"""
<div class="cat-tile" onclick="{click}" role="button" tabindex="0"
     onkeypress="if(event.key==='Enter') this.click()">
  <div class="cat-tile-bg" style="{bg}"></div>
  <div class="cat-tile-vignette"></div>
  <div class="cat-tile-content">
    <div class="cat-tile-name">{m_cat}</div>
    <div class="cat-tile-meta">
      <span class="cat-tile-count">{count_lbl}</span>
      <span class="cat-tile-arrow">→</span>
    </div>
  </div>
</div>"""

    # ── JAVASCRIPT ────────────────────────────────────────────────────────────
    js = """
/* ── State ── */
let currentCat = null;

/* ── Slideshow ── */
(function(){
  const sl = document.querySelectorAll('.slide');
  if (!sl.length) return;
  let i = 0;
  sl[0].classList.add('active');
  setInterval(() => {
    sl[i].classList.remove('active');
    i = (i + 1) % sl.length;
    sl[i].classList.add('active');
  }, 5500);
})();

/* ── Show/hide helpers ── */
function hideAll() {
  document.getElementById('hero').style.display             = 'none';
  document.getElementById('tile-nav').classList.remove('visible');
  document.getElementById('sub-nav').classList.remove('visible');
  document.getElementById('gallery-container').classList.remove('visible');
  document.querySelectorAll('.sub-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.section-block').forEach(b => b.style.display = 'none');
}

function goHome() {
  hideAll();
  document.getElementById('hero').style.display = 'flex';
  document.getElementById('tile-nav').classList.add('visible');
  document.getElementById('tile-nav').classList.add('page-enter');
  window.scrollTo(0, 0);
}

function openCategory(cat) {
  currentCat = cat;
  hideAll();
  const subNav = document.getElementById('sub-nav');
  subNav.classList.add('visible', 'page-enter');
  document.getElementById('bc-label').textContent = cat;
  const panel = document.getElementById('subpanel-' + cat);
  if (panel) panel.classList.add('active');
  window.scrollTo(0, 0);
}

function openSubNav(cat) { openCategory(cat); }

function showGallery(sectionId) {
  hideAll();
  const gc = document.getElementById('gallery-container');
  gc.classList.add('visible', 'page-enter');
  const block = document.getElementById(sectionId);
  if (block) block.style.display = 'block';
  window.scrollTo(0, 0);
}

/* Remove animation class after it plays so re-navigation works */
['tile-nav','sub-nav','gallery-container'].forEach(id => {
  document.getElementById(id).addEventListener('animationend', function(){
    this.classList.remove('page-enter');
  });
});

/* ── Lightbox ── */
let lbImages = [], lbIdx = 0;
const lb    = document.getElementById('lightbox');
const lbImg = document.getElementById('lb-image');
const lbCtr = document.getElementById('lb-counter');

function openLightbox(el) {
  const grid = el.closest('.grid');
  lbImages   = Array.from(grid.querySelectorAll('.grid-item img')).map(i => i.src);
  lbIdx      = Array.from(grid.querySelectorAll('.grid-item')).indexOf(el);
  lbImg.src  = lbImages[lbIdx];
  lbCtr.textContent = (lbIdx + 1) + ' / ' + lbImages.length;
  lb.classList.add('open');
  document.body.style.overflow = 'hidden';
}
function closeLightbox() { lb.classList.remove('open'); document.body.style.overflow = ''; }
function lbStep(dir) {
  lbIdx = (lbIdx + dir + lbImages.length) % lbImages.length;
  lbImg.src = lbImages[lbIdx];
  lbCtr.textContent = (lbIdx + 1) + ' / ' + lbImages.length;
}
lb.addEventListener('click', e => { if (e.target === lb) closeLightbox(); });
document.addEventListener('keydown', e => {
  if (!lb.classList.contains('open')) return;
  if (e.key === 'Escape')      closeLightbox();
  if (e.key === 'ArrowRight')  lbStep(1);
  if (e.key === 'ArrowLeft')   lbStep(-1);
});

/* Touch swipe for lightbox */
let tsX = null;
lb.addEventListener('touchstart', e => { tsX = e.touches[0].clientX; }, {passive:true});
lb.addEventListener('touchend', e => {
  if (tsX === null) return;
  const dx = e.changedTouches[0].clientX - tsX;
  if (Math.abs(dx) > 50) lbStep(dx < 0 ? 1 : -1);
  tsX = null;
});

/* ── Init ── */
goHome();
"""

    # ── ASSEMBLE HTML ─────────────────────────────────────────────────────────
    logo_svg = (
        '<svg viewBox="0 0 1200 80" xmlns="http://www.w3.org/2000/svg" '
        'class="logo-svg" onclick="goHome()">'
        '<text x="50%" y="58%" text-anchor="middle" dominant-baseline="middle" '
        'font-family="\'Cormorant Garamond\', serif" font-weight="700" font-size="52" '
        'letter-spacing="20" fill="white">MOHANGRAPHY</text></svg>'
    )

    slide_tags = "".join(
        f'<img src="{p}" class="slide" loading="lazy" alt="">' for p in slides
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
  <meta name="theme-color" content="#080808">
  <title>M O H A N G R A P H Y</title>
  <style>{css}</style>
</head>
<body>

<!-- HEADER -->
<header>{logo_svg}</header>

<!-- HERO -->
<div id="hero">
  {slide_tags}
  <div class="hero-caption">
    <h2>Light &nbsp;·&nbsp; Moment &nbsp;·&nbsp; Story</h2>
    <p>Photography by Mohan</p>
  </div>
  <div class="scroll-cue">
    <svg width="14" height="20" viewBox="0 0 14 20" fill="none">
      <path d="M7 2v12M2 11l5 5 5-5" stroke="rgba(255,255,255,0.4)" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
    <span>Explore</span>
  </div>
</div>

<!-- MAIN VERTICAL TILE MENU -->
<div id="tile-nav">
  <div class="tile-nav-label">Collections</div>
  {cat_tiles_html}
</div>

<!-- SUB-CATEGORY PAGE -->
<div id="sub-nav">
  <div class="breadcrumb-bar">
    <button class="bc-back" onclick="goHome()">← Home</button>
    <span class="bc-sep">|</span>
    <span class="bc-current" id="bc-label"></span>
  </div>
  {sub_panels}
</div>

<!-- GALLERY -->
<main id="gallery-container">
  {gallery_blocks}
</main>

<!-- LIGHTBOX -->
<div id="lightbox" role="dialog" aria-modal="true">
  <button class="lb-btn" id="lb-close" onclick="closeLightbox()" aria-label="Close">✕</button>
  <button class="lb-btn" id="lb-prev"  onclick="lbStep(-1)"       aria-label="Previous">‹</button>
  <img id="lb-image" src="" alt="Gallery photo">
  <button class="lb-btn" id="lb-next"  onclick="lbStep(1)"        aria-label="Next">›</button>
  <div class="lb-counter" id="lb-counter"></div>
</div>

<!-- FOOTER -->
<footer>
  <span class="footer-copy">© Mohangraphy</span>
  <div class="footer-links">
    <button class="footer-link" onclick="goHome()">Home</button>
    <button class="footer-link" onclick="goHome()">Collections</button>
  </div>
</footer>

<script>{js}</script>
</body>
</html>"""

    out_path = os.path.join(ROOT_DIR, "index.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ Build complete → {out_path}")
    print(f"   Unique photos indexed : {len(unique)}")
    print(f"   Slideshow frames      : {len(slides)}")

if __name__ == "__main__":
    generate_html()
