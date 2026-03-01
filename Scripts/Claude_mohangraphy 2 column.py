import os
import json
import random
import subprocess

# ── CONFIGURATION ─────────────────────────────────────────────────────────────
ROOT_DIR         = "/Users/ncm/Pictures/Mohangraphy"
DATA_FILE        = os.path.join(ROOT_DIR, "Scripts/photo_metadata.json")
CONTENT_FILE     = os.path.join(ROOT_DIR, "Scripts/content.json")  # ← editable content
THUMBS_DIR       = os.path.join(ROOT_DIR, "Thumbs")
WEB_DIR          = os.path.join(ROOT_DIR, "Web")    # 2048px web-optimised copies
MEGAMALAI_FOLDER = os.path.join(ROOT_DIR, "Photos/Nature/Landscape/Megamalai")
THUMB_WIDTH      = 800
WEB_WIDTH        = 2048   # max long-edge for lightbox display

MANUAL_STRUCTURE = {
    "Places":       ["National", "International"],
    "Nature":       ["Birds", "Flowers", "Landscape", "Mountains", "Sunsets and Sunrises", "Wildlife"],
    "People":       ["Portraits"],
    "Architecture": [],
}

# ── TAG MAP: what metadata tag resolves to each MANUAL_STRUCTURE sub-key ──────
# The curator stores "Nature/Landscape/Mountains" — map that to the "Mountains"
# sub-category under Nature.
TAG_OVERRIDES = {
    "Nature/Mountains":              "Nature/Landscape/Mountains",   # alias
    "Nature/Sunsets and Sunrises":   "Nature/Sunsets",               # alias
}

# All tag strings that count as "Mountains" content
MOUNTAINS_TAGS = {"Nature/Landscape/Mountains", "Nature/Mountains"}
SUNSETS_TAGS   = {"Nature/Sunsets and Sunrises", "Nature/Sunsets"}

# ── HELPERS ───────────────────────────────────────────────────────────────────

def load_index():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, 'r') as f:
        try:
            return json.load(f)
        except Exception:
            return {}

def load_content():
    """Load content.json — the plain-text editable content file."""
    if not os.path.exists(CONTENT_FILE):
        print("  ⚠️  WARNING: content.json NOT FOUND at:")
        print("       " + CONTENT_FILE)
        print("  Copy content.json into your Scripts/ folder and try again.")
        return {}
    with open(CONTENT_FILE, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
            # Diagnostic — confirm what was loaded
            about_title = data.get('about', {}).get('title', '(missing)')
            email       = data.get('site',  {}).get('contact_email', '(missing)')
            n_paras     = len(data.get('about', {}).get('paragraphs', []))
            print(f"  ✅ content.json loaded OK")
            print(f"     About title : {about_title}")
            print(f"     Contact email: {email}")
            print(f"     About paragraphs: {n_paras}")
            return data
        except Exception as e:
            print("  ❌ ERROR reading content.json: " + str(e))
            print("     Common causes: missing comma, unclosed quote, or extra bracket.")
            print("     Validate your file at: https://jsonlint.com")
            return {}

def deduplicate_by_path(raw_data):
    """One entry per unique relative path — kills the hash+filename duplicates."""
    seen = {}
    for info in raw_data.values():
        path = info.get('path', '').strip()
        if path and path not in seen:
            seen[path] = info
    return list(seen.values())

def scan_folder_for_photos(folder_path):
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

# ── THUMBNAIL GENERATION ──────────────────────────────────────────────────────
def make_thumb(rel_path):
    """
    Generate a web-optimised JPEG thumbnail using sips (built into macOS).
    Returns the relative path to the thumbnail (relative to ROOT_DIR).
    Falls back to the original if sips is unavailable.
    """
    src_full   = os.path.join(ROOT_DIR, rel_path)
    thumb_rel  = os.path.join("Thumbs", rel_path)
    thumb_full = os.path.join(ROOT_DIR, thumb_rel)

    if not os.path.exists(thumb_full):
        os.makedirs(os.path.dirname(thumb_full), exist_ok=True)
        try:
            subprocess.run(
                ["sips", "-Z", str(THUMB_WIDTH), src_full,
                 "--out", thumb_full],
                capture_output=True, check=True
            )
        except Exception:
            # sips not available (e.g. running on non-macOS) — use original
            return rel_path
    return thumb_rel

def make_web(rel_path):
    """
    Generate a 2048px web-optimised JPEG using sips.
    These are served by the lightbox instead of the full-res originals.
    - Stored in Web/ mirroring the Photos/ folder structure
    - Only created if larger than 2048px (smaller images kept as-is)
    - Skipped if already exists (fast on re-runs)
    Returns the relative path to the web copy (relative to ROOT_DIR).
    """
    src_full = os.path.join(ROOT_DIR, rel_path)
    web_rel  = os.path.join("Web", rel_path)
    web_full = os.path.join(ROOT_DIR, web_rel)

    if not os.path.exists(web_full):
        os.makedirs(os.path.dirname(web_full), exist_ok=True)
        try:
            subprocess.run(
                ["sips", "-Z", str(WEB_WIDTH), src_full, "--out", web_full],
                capture_output=True, check=True
            )
        except Exception:
            return rel_path  # fallback to original
    return web_rel

def thumb_img(rel_path, web_rel_path, alt=""):
    """
    <img> that:
      • shows the small thumbnail (fast on mobile)
      • data-full stores 2048px web copy for the lightbox
      • lazy-loads + async-decodes
    """
    return (
        '<img src="' + rel_path + '" '
        'data-full="' + web_rel_path + '" '
        'loading="lazy" decoding="async" '
        'alt="' + alt + '" '
        'style="width:100%;height:100%;object-fit:cover;display:block;">'
    )

# ── BUILD TAG MAP ─────────────────────────────────────────────────────────────
def build_maps(unique_entries):
    """
    Returns:
      tag_map      : normalised-tag → [unique paths]
      place_map    : {
                       National:      {state: {city: [paths]}},
                       International: {country: {city: [paths]}}
                     }
      all_paths    : [all unique paths]
      path_info    : {path: {place, remarks, state, city}} for overlay display

    Place field format:  "State - City"  (National)
                     or  "Country - City" (International)
    If no separator found, the whole value is treated as the top-level key.
    """
    tag_map       = {}
    place_map     = {"National": {}, "International": {}}
    all_paths     = []
    path_info_map = {}

    # Known single-word place→(state, city) mapping for backward compatibility
    KNOWN_STATES = {
        'megamalai':   ('Tamil Nadu', 'Megamalai'),
        'munnar':      ('Kerala',     'Munnar'),
        'badami':      ('Karnataka',  'Badami'),
        'pattadhakal': ('Karnataka',  'Pattadhakal'),
        'hampi':       ('Karnataka',  'Hampi'),
        'coorg':       ('Karnataka',  'Coorg'),
        'ooty':        ('Tamil Nadu', 'Ooty'),
        'kodaikanal':  ('Tamil Nadu', 'Kodaikanal'),
    }

    for info in unique_entries:
        path    = info.get('path', '')
        tags    = info.get('categories', [])
        place   = info.get('place', '').strip()
        remarks = info.get('remarks', '').strip()
        state   = info.get('state', '').strip()
        city    = info.get('city',  '').strip()

        # Backward-compat: parse old-style place fields into state + city
        if not state and ' - ' in place:
            parts  = place.split(' - ', 1)
            state, city = parts[0].strip(), parts[1].strip()
        elif not state and place:
            lookup = KNOWN_STATES.get(place.lower().strip())
            if lookup:
                state, city = lookup
            else:
                # Unknown single-word place: treat as CITY under an unknown state.
                # The state will remain blank — user should re-tag via curator.
                city  = place
                state = ''

        # If we have state but no city, city = state (shows under the state tile)
        if state and not city:
            city = state

        if not path:
            continue
        all_paths.append(path)
        overlay_place = city if city else state
        path_info_map[path] = {'place': overlay_place, 'remarks': remarks,
                               'state': state, 'city': city}

        for raw_tag in tags:
            if raw_tag in MOUNTAINS_TAGS or raw_tag == "Nature/Landscape/Mountains":
                for t in ["Nature/Mountains", "Nature/Landscape"]:
                    tag_map.setdefault(t, [])
                    if path not in tag_map[t]:
                        tag_map[t].append(path)
            elif raw_tag in SUNSETS_TAGS:
                norm = "Nature/Sunsets and Sunrises"
                tag_map.setdefault(norm, [])
                if path not in tag_map[norm]:
                    tag_map[norm].append(path)
            elif raw_tag == "Birds":
                tag_map.setdefault("Nature/Birds", [])
                if path not in tag_map["Nature/Birds"]:
                    tag_map["Nature/Birds"].append(path)
            elif raw_tag == "Flowers":
                tag_map.setdefault("Nature/Flowers", [])
                if path not in tag_map["Nature/Flowers"]:
                    tag_map["Nature/Flowers"].append(path)
            else:
                tag_map.setdefault(raw_tag, [])
                if path not in tag_map[raw_tag]:
                    tag_map[raw_tag].append(path)

            # Build place_map: National/International → State → City → [paths]
            if "Places/National" in raw_tag and state and city:
                pm = place_map["National"]
                pm.setdefault(state, {})
                pm[state].setdefault(city, [])
                if path not in pm[state][city]:
                    pm[state][city].append(path)
            elif "Places/International" in raw_tag and state and city:
                pm = place_map["International"]
                pm.setdefault(state, {})
                pm[state].setdefault(city, [])
                if path not in pm[state][city]:
                    pm[state][city].append(path)

    return tag_map, place_map, list(dict.fromkeys(all_paths)), path_info_map

def get_display_paths(m_cat, s_cat, tag_map):
    """
    Resolve which photos belong to a category or sub-category.
    Priority: disk folder scan → tag_map lookup.
    For flat categories (no s_cat), scans the disk folder too.
    """
    if s_cat:
        disk_folder = os.path.join(ROOT_DIR, "Photos", m_cat, s_cat)
        disk_paths  = scan_folder_for_photos(disk_folder)
        if disk_paths:
            return disk_paths

    # Special case: Mountains
    if s_cat == "Mountains":
        paths = []
        for t in ["Nature/Mountains", "Nature/Landscape/Mountains"]:
            for p in tag_map.get(t, []):
                if p not in paths:
                    paths.append(p)
        return paths

    tag_key = m_cat + "/" + s_cat if s_cat else m_cat

    # For flat categories (no subs), also try disk folder
    if not s_cat:
        disk_folder = os.path.join(ROOT_DIR, "Photos", m_cat)
        disk_paths  = scan_folder_for_photos(disk_folder)
        tag_paths   = list(dict.fromkeys(tag_map.get(tag_key, [])))
        # Merge: disk paths take priority, add any tag-only paths
        merged = list(disk_paths)
        for p in tag_paths:
            if p not in merged:
                merged.append(p)
        return merged

    return list(dict.fromkeys(tag_map.get(tag_key, [])))


# ── THUMBNAIL BATCH ───────────────────────────────────────────────────────────
def ensure_thumbs(all_paths):
    """Pre-generate thumbnails AND 2048px web copies for all photos."""
    total = len(all_paths)
    print(f"  Generating thumbnails + 2048px web copies ({total} photos)...")
    print(f"  First run takes a few minutes. Subsequent runs are instant (skips existing).")
    thumb_map = {}
    web_map   = {}
    for i, p in enumerate(all_paths):
        thumb_map[p] = make_thumb(p)
        web_map[p]   = make_web(p)
        if (i + 1) % 20 == 0:
            print(f"    {i+1}/{total} done")
    print(f"  Thumbnails ready: {len(thumb_map)}  |  Web copies ready: {len(web_map)}")
    return thumb_map, web_map


# ── MAIN BUILD ────────────────────────────────────────────────────────────────
def render_paragraphs(paragraphs):
    """Convert a list of paragraph strings from content.json to HTML <p> tags."""
    return ''.join('<p>' + p + '</p>\n' for p in paragraphs)

def render_items(items):
    """Convert a list of {heading, detail} dicts to HTML <p> blocks."""
    return ''.join(
        '<p><strong>' + item['heading'] + '</strong><br>' + item['detail'] + '</p>\n'
        for item in items
    )

def grid_item_html(thumb_path, orig_path, alt, path_info, meta_by_path=None, web_map=None):
    """
    Build a single grid cell. Embeds existing metadata as data-* attributes.
    Lightbox uses 2048px web copy (Web/) not the original.
    """
    info    = path_info.get(orig_path, {})
    remarks = info.get('remarks', '').strip()
    place   = info.get('place',   '').strip()
    state   = info.get('state',   '').strip()
    city    = info.get('city',    '').strip()

    cats = []
    if meta_by_path and orig_path in meta_by_path:
        cats = meta_by_path[orig_path].get('categories', [])

    # Use pre-generated web copy path (fast lookup), fallback to make_web
    web_path = (web_map.get(orig_path) if web_map else None) or make_web(orig_path)

    import html as _html
    def qa(s): return _html.escape(s, quote=True)

    parts = [p for p in [remarks, place] if p]
    label = ' · '.join(parts)
    overlay = (
        '<div class="grid-item-info">'
        '<span class="grid-item-info-text">' + label + '</span>'
        '</div>'
    ) if label else ''

    return (
        '<div class="grid-item"'
        ' data-photo="'   + qa(orig_path) + '"'
        ' data-state="'   + qa(state)     + '"'
        ' data-city="'    + qa(city)      + '"'
        ' data-remarks="' + qa(remarks)   + '"'
        ' data-cats="'    + qa(','.join(cats)) + '"'
        ' onclick="openLightbox(this)">'
        '<div class="grid-item-photo">'
        + thumb_img(thumb_path, web_path, alt)
        + '<div class="grid-item-overlay"></div>'
        + overlay
        + '</div>'
        '<div class="grid-item-bar" onclick="event.stopPropagation()">'
        '<button class="bar-btn like-btn" title="Like" onclick="event.stopPropagation();barLike(this)">'
        '&#10084;<span class="bar-btn-count like-count"></span>'
        '</button>'
        '<div class="bar-sep"></div>'
        '<button class="bar-btn buy-btn" title="Order a print" onclick="event.stopPropagation();barBuy(this)">'
        '&#128722;'
        '</button>'
        '</div>'
        '</div>'
    )

def generate_html():

    # Load photo data
    raw_data = load_index()
    unique   = deduplicate_by_path(raw_data)
    tag_map, place_map, all_paths, path_info = build_maps(unique)

    # Build path→full metadata dict for embedding into grid items
    meta_by_path = {e.get('path','').strip(): e for e in unique if e.get('path','').strip()}

    print(f"Unique photos: {len(unique)}")
    print(f"Mountains photos found: {len(tag_map.get('Nature/Mountains', []))}")

    # Load editable content
    C = load_content()
    site       = C.get('site',       {})
    c_about    = C.get('about',      {})
    c_phil     = C.get('philosophy', {})
    c_gear     = C.get('gear',       {})
    c_contact  = C.get('contact',    {})
    c_prints   = C.get('prints',     {})
    c_licens   = C.get('licensing',  {})
    c_workshop = C.get('workshops',  {})
    c_legal    = C.get('legal',      {})

    # Site-wide values with safe fallbacks
    contact_email    = site.get('contact_email',    'your@email.com')
    photographer     = site.get('photographer_name','N C Mohan')
    site_description = site.get('description',      'Photography by N C Mohan')
    supabase_url     = site.get('supabase_url',     'NONE')
    supabase_key     = site.get('supabase_anon_key','NONE')
    admin_password   = site.get('admin_password',   'mohan2024')
    plausible_domain = site.get('plausible_domain', '')

    # Generate / verify thumbnails + 2048px web copies
    thumb_map, web_map = ensure_thumbs(all_paths)

    # Hero slides — Megamalai landscape only, 3-second rotation
    megamalai_paths = scan_folder_for_photos(MEGAMALAI_FOLDER)
    if not megamalai_paths:
        megamalai_paths = tag_map.get("Nature/Landscape", all_paths[:20])
    hero_slides = random.sample(megamalai_paths, min(len(megamalai_paths), 15))
    # Use thumbs for hero too (faster initial load)
    hero_thumb_paths = [thumb_map.get(p, p) for p in hero_slides]

    # Cover photo per main category (use thumb)
    cat_covers = {}
    for m_cat, subs in sorted(MANUAL_STRUCTURE.items(), key=lambda x: x[0].lower()):
        pool = []
        if m_cat == "Places":
            for grp in place_map.values():          # grp = {state: {city: [paths]}}
                for cities in grp.values():
                    for paths in cities.values():
                        pool.extend(paths)
        else:
            for s in subs:
                pool.extend(get_display_paths(m_cat, s, tag_map))
            pool.extend(tag_map.get(m_cat, []))
        raw = pick_cover(pool)
        cat_covers[m_cat] = thumb_map.get(raw, raw)

    # ── CSS ───────────────────────────────────────────────────────────────────
    css = """
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;0,700;1,400&family=Montserrat:wght@300;400;600;700;900&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --gold:  #c9a96e;
  --gold2: #e8d4a0;
  --dark:  #080808;
  --mid:   #161616;
  --hdr:   64px;
}

/* ── BASE ── */
html { scroll-behavior: smooth; font-size: 16px; }
body {
  background: var(--dark); color: #fff;
  font-family: 'Montserrat', sans-serif;
  overflow-x: hidden;
  -webkit-tap-highlight-color: transparent;
  -webkit-text-size-adjust: 100%;
}

/* ══════════════════════════════════════════════════════════════
   HEADER  — three zones: [☰ left icon] [title] [≡ right icon]
   ══════════════════════════════════════════════════════════════ */
header {
  position: fixed; top: 0; left: 0; right: 0;
  height: var(--hdr);
  background: rgba(8,8,8,0.97);
  backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(201,169,110,0.15);
  z-index: 2000;
  display: grid;
  grid-template-columns: 48px 1fr 48px;
  align-items: center;
  padding: 0;
  overflow: hidden;
}
@media (min-width: 480px) {
  header { grid-template-columns: var(--hdr) 1fr var(--hdr); }
}

/* Left icon button — About / Contact / more */
.hdr-icon-left,
.hdr-icon-right {
  width: var(--hdr); height: var(--hdr);
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; background: none; border: none;
  color: rgba(255,255,255,0.45);
  transition: color .25s, background .25s;
  flex-shrink: 0;
}
.hdr-icon-left:hover,  .hdr-icon-right:hover,
.hdr-icon-left:active, .hdr-icon-right:active {
  color: var(--gold); background: rgba(201,169,110,0.06);
}
.hdr-icon-left  svg, .hdr-icon-right svg { pointer-events: none; }

/* MOHANGRAPHY — largest text on the page, always fits one line */
.site-title {
  font-family: 'Cormorant Garamond', serif;
  font-weight: 700;
  font-size: clamp(14px, 3.5vw, 46px);
  letter-spacing: clamp(3px, 1.6vw, 18px);
  color: #fff; text-transform: uppercase;
  cursor: pointer; user-select: none;
  transition: color 0.3s;
  white-space: nowrap; overflow: hidden;
  text-align: center;
  padding-right: clamp(3px, 1.6vw, 18px); /* compensate last-char spacing */
}
.site-title:hover { color: var(--gold); }

/* ══════════════════════════════════════════════════════════════
   OVERLAY BACKDROP — shared by both drawers
   ══════════════════════════════════════════════════════════════ */
.drawer-overlay {
  display: none; position: fixed; inset: 0;
  background: rgba(0,0,0,0.6);
  z-index: 2998;
  backdrop-filter: blur(2px); -webkit-backdrop-filter: blur(2px);
}
.drawer-overlay.open { display: block; }

/* ══════════════════════════════════════════════════════════════
   RIGHT DRAWER — Collections nav (hamburger ≡)
   Full tree: main cats → expand to sub-cats inline
   ══════════════════════════════════════════════════════════════ */
#nav-drawer {
  position: fixed; top: 0; right: 0;
  width: min(320px, 88vw); height: 100svh;
  background: #0e0e0e;
  border-left: 1px solid rgba(201,169,110,0.12);
  z-index: 2999;
  display: flex; flex-direction: column;
  transform: translateX(100%);
  transition: transform .35s cubic-bezier(.4,0,.2,1);
  overflow: hidden;
}
#nav-drawer.open { transform: translateX(0); }

.drawer-header {
  height: var(--hdr);
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 20px;
  border-bottom: 1px solid rgba(201,169,110,0.1);
  flex-shrink: 0;
}
.drawer-header-title {
  font-family: 'Cormorant Garamond', serif;
  font-size: 11px; letter-spacing: 6px;
  color: var(--gold); text-transform: uppercase; opacity: .7;
}
.drawer-close {
  background: none; border: none; cursor: pointer;
  color: rgba(255,255,255,0.3); font-size: 20px;
  width: 36px; height: 36px;
  display: flex; align-items: center; justify-content: center;
  transition: color .2s; border-radius: 50%;
}
.drawer-close:hover { color: var(--gold); }

.drawer-scroll { overflow-y: auto; flex: 1; padding: 8px 0 80px; }
.drawer-scroll::-webkit-scrollbar { width: 2px; }
.drawer-scroll::-webkit-scrollbar-thumb { background: rgba(201,169,110,0.2); }

/* Main category row in drawer */
.dnav-cat {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 20px; height: 52px; cursor: pointer;
  border-bottom: 1px solid rgba(255,255,255,0.04);
  transition: background .2s;
  -webkit-tap-highlight-color: transparent;
}
.dnav-cat:hover, .dnav-cat:active { background: rgba(201,169,110,0.05); }
.dnav-cat-name {
  font-family: 'Cormorant Garamond', serif;
  font-size: clamp(15px, 3.5vw, 18px);
  letter-spacing: 3px; text-transform: uppercase;
  color: #fff; transition: color .2s;
}
.dnav-cat:hover .dnav-cat-name { color: var(--gold); }
.dnav-chevron {
  color: rgba(255,255,255,0.25); font-size: 11px;
  transition: transform .25s, color .2s; flex-shrink: 0;
}
.dnav-cat.expanded .dnav-chevron { transform: rotate(90deg); color: var(--gold); }

/* Sub-items inside the drawer */
.dnav-subs {
  display: none; background: rgba(0,0,0,0.3);
  border-bottom: 1px solid rgba(255,255,255,0.04);
}
.dnav-subs.open { display: block; }
.dnav-sub {
  display: flex; align-items: center; gap: 10px;
  padding: 0 20px 0 36px; height: 44px; cursor: pointer;
  border-bottom: 1px solid rgba(255,255,255,0.03);
  transition: background .2s;
  -webkit-tap-highlight-color: transparent;
}
.dnav-sub:hover, .dnav-sub:active { background: rgba(201,169,110,0.06); }
.dnav-sub-dot {
  width: 4px; height: 4px; border-radius: 50%;
  background: rgba(201,169,110,0.35); flex-shrink: 0;
}
.dnav-sub-name {
  font-size: 11px; letter-spacing: 3px; text-transform: uppercase;
  color: rgba(255,255,255,0.5); transition: color .2s;
}
.dnav-sub:hover .dnav-sub-name { color: var(--gold); }

/* Divider in drawer */
.dnav-divider {
  height: 1px; background: rgba(201,169,110,0.1);
  margin: 8px 20px;
}

/* ══════════════════════════════════════════════════════════════
   LEFT DRAWER — About / Contact / etc  (person icon)
   ══════════════════════════════════════════════════════════════ */
#about-drawer {
  position: fixed; top: 0; left: 0;
  width: min(320px, 88vw); height: 100svh;
  background: #0e0e0e;
  border-right: 1px solid rgba(201,169,110,0.12);
  z-index: 2999;
  display: flex; flex-direction: column;
  transform: translateX(-100%);
  transition: transform .35s cubic-bezier(.4,0,.2,1);
  overflow: hidden;
}
#about-drawer.open { transform: translateX(0); }

.about-scroll { overflow-y: auto; flex: 1; padding: 0 0 80px; }
.about-scroll::-webkit-scrollbar { width: 2px; }
.about-scroll::-webkit-scrollbar-thumb { background: rgba(201,169,110,0.2); }

/* Section header inside about drawer */
.adrawer-section-hdr {
  padding: 20px 20px 8px;
  font-size: 8px; letter-spacing: 5px;
  color: var(--gold); text-transform: uppercase; opacity: .55;
}

/* Each item row */
.adrawer-item {
  display: flex; align-items: center; gap: 14px;
  padding: 0 20px; height: 52px; cursor: pointer;
  border-bottom: 1px solid rgba(255,255,255,0.04);
  transition: background .2s;
  -webkit-tap-highlight-color: transparent;
}
.adrawer-item:hover, .adrawer-item:active { background: rgba(201,169,110,0.05); }
.adrawer-icon {
  width: 32px; height: 32px; border-radius: 50%;
  background: rgba(201,169,110,0.08);
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.adrawer-icon svg { color: var(--gold); }
.adrawer-label {
  font-size: 11px; letter-spacing: 3px; text-transform: uppercase;
  color: rgba(255,255,255,0.55); transition: color .2s;
}
.adrawer-item:hover .adrawer-label { color: var(--gold); }
.adrawer-badge {
  margin-left: auto; font-size: 7px; letter-spacing: 2px;
  color: rgba(201,169,110,0.4); text-transform: uppercase;
  background: rgba(201,169,110,0.08);
  padding: 2px 6px; border-radius: 2px;
}

/* ── Sub-page panels (About, Contact, etc.) ── */
.info-page {
  display: none; position: fixed; inset: 0;
  background: var(--dark);
  z-index: 1500; overflow-y: auto;
  padding: var(--hdr) 0 80px;
}
.info-page.visible { display: block; }
.info-page-inner {
  max-width: 680px; margin: 0 auto;
  padding: 40px clamp(20px,5vw,60px);
}
.info-page-back {
  display: inline-flex; align-items: center; gap: 8px;
  font-size: 8px; letter-spacing: 4px; text-transform: uppercase;
  color: rgba(255,255,255,0.25); cursor: pointer; background: none; border: none;
  font-family: 'Montserrat', sans-serif; margin-bottom: 40px;
  transition: color .25s;
}
.info-page-back:hover { color: var(--gold); }
.info-page-title {
  font-family: 'Cormorant Garamond', serif;
  font-size: clamp(28px, 6vw, 54px); font-weight: 600;
  letter-spacing: clamp(4px,1.5vw,10px); text-transform: uppercase;
  margin-bottom: 8px;
}
.info-page-subtitle {
  font-size: 9px; letter-spacing: 5px; color: var(--gold);
  text-transform: uppercase; opacity: .7; margin-bottom: 36px;
}
.info-page-divider {
  height: 1px; background: rgba(201,169,110,0.15); margin: 32px 0;
}
.info-page-body {
  font-family: 'Cormorant Garamond', serif;
  font-size: clamp(16px, 2.2vw, 20px); font-weight: 300;
  color: rgba(255,255,255,0.65); line-height: 1.9;
}
.info-page-body p { margin-bottom: 20px; }
.info-page-body strong { color: var(--gold); font-weight: 600; }

/* Contact form fields */
.contact-field {
  width: 100%; margin-bottom: 18px;
}
.contact-field label {
  display: block; font-size: 8px; letter-spacing: 4px;
  text-transform: uppercase; color: rgba(255,255,255,0.3);
  margin-bottom: 8px;
}
.contact-field input,
.contact-field textarea,
.contact-field select {
  width: 100%; background: #111;
  border: 1px solid rgba(201,169,110,0.15);
  color: #fff; padding: 12px 14px;
  font-family: 'Montserrat', sans-serif; font-size: 13px;
  outline: none; border-radius: 0;
  transition: border-color .25s;
  -webkit-appearance: none;
}
.contact-field input:focus,
.contact-field textarea:focus,
.contact-field select:focus { border-color: var(--gold); }
.contact-field textarea { min-height: 120px; resize: vertical; }
.contact-field select option { background: #111; }

.btn-gold {
  background: none; border: 1px solid var(--gold);
  color: var(--gold); padding: 12px 32px;
  font-family: 'Montserrat', sans-serif;
  font-size: 9px; letter-spacing: 4px; text-transform: uppercase;
  cursor: pointer; transition: background .25s, color .25s;
  margin-top: 8px;
}
.btn-gold:hover { background: var(--gold); color: #000; }

/* Print sale info grid */
.prints-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(100%,200px),1fr));
  gap: 16px; margin-top: 20px;
}
.print-card {
  background: #111; border: 1px solid rgba(201,169,110,0.18);
  padding: 20px 16px;
}
.print-card-size {
  font-family: 'Cormorant Garamond', serif;
  font-size: 22px; letter-spacing: 2px; color: #fff; margin-bottom: 8px;
}
.print-card-desc {
  font-size: 9px; letter-spacing: 1.5px; color: rgba(255,255,255,0.75);
  text-transform: uppercase; line-height: 2;
  white-space: pre-line;   /* honours \n line breaks */
}
.print-card-price {
  margin-top: 12px; font-size: 10px; letter-spacing: 3px;
  color: var(--gold); text-transform: uppercase;
}

/* ── HERO ── */
#hero {
  position: relative;
  width: 100%;
  height: 100svh;
  overflow: hidden;
  background: #000;
  display: none;
  align-items: center;
  justify-content: center;
}
#hero.visible { display: flex; }
.slide {
  position: absolute; inset: 0;
  width: 100%; height: 100%;
  object-fit: cover; object-position: center 40%;
  opacity: 0;
  transition: opacity 1.2s ease-in-out;
  filter: brightness(0.32) saturate(0.65);
  will-change: opacity;
}
.slide.active { opacity: 1; }

/* Tagline sits over the photo */
.hero-caption {
  position: relative; z-index: 2;
  text-align: center;
  padding: 0 clamp(16px, 6vw, 80px);
  pointer-events: none;
  width: 100%;
}
.hero-tagline {
  font-family: 'Cormorant Garamond', serif;
  font-weight: 300;
  /*
    "LIGHT · MOMENT · STORY" must always be ONE line.
    4.2vw gives ~26px on 320px (fits), ~60px on 1440px.
    white-space: nowrap + overflow hidden guarantees no wrapping.
  */
  font-size: clamp(14px, 4.2vw, 52px);
  letter-spacing: clamp(3px, 1.5vw, 14px);
  color: rgba(255,255,255,0.9);
  text-transform: uppercase;
  line-height: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: clip;
  max-width: 100%;
}
.hero-tagline .dot { color: var(--gold); margin: 0 0.4em; }

.hero-byline {
  margin-top: clamp(18px, 3.5vw, 40px);
  font-family: 'Montserrat', sans-serif;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: clamp(8px, 1.5vw, 16px);
}
.hero-byline .byline-label {
  font-weight: 300;
  font-size: clamp(7px, 1.1vw, 10px);
  letter-spacing: clamp(4px, 1.5vw, 10px);
  color: var(--gold2);
  text-transform: uppercase;
}
.hero-byline .name {
  font-weight: 600;
  font-size: clamp(13px, 2.2vw, 22px);
  letter-spacing: clamp(3px, 1vw, 8px);
  color: var(--gold);
  text-transform: uppercase;
}

.scroll-cue {
  position: absolute; bottom: 20px; left: 50%;
  transform: translateX(-50%);
  display: flex; flex-direction: column; align-items: center; gap: 4px;
  animation: cue 2.4s ease-in-out infinite; z-index: 2;
}
.scroll-cue span {
  font-size: 7px; letter-spacing: 4px;
  color: rgba(255,255,255,0.2); text-transform: uppercase;
}
@keyframes cue {
  0%,100% { transform: translateX(-50%) translateY(0); opacity:.3; }
  50%      { transform: translateX(-50%) translateY(7px); opacity:.8; }
}

/* ── MAIN VERTICAL TILE NAV ── */
/*
  Each menu row is a COMPACT HORIZONTAL ROW:
    [ category name + photo count ]  [ thumbnail OR "Coming Soon" box ]
  Height is fixed and compact so all 6 items fit on one screen scroll.
*/
#tile-nav {
  display: none;
  padding-top: var(--hdr);
  background: var(--dark);
  min-height: 100svh;
  padding-bottom: 56px;
}
#tile-nav.visible { display: block; }

.tile-nav-label {
  font-size: 8px; letter-spacing: 6px;
  color: var(--gold); text-transform: uppercase;
  opacity: .8; text-align: center;
  padding: 18px 0 10px;
}

/* Each row */
/* ── Minimum 14px text on desktop ── */
@media (min-width: 768px) {
  body, p, li, span, div, label, input, textarea, select, button {
    font-size: max(var(--font-size, 1em), 14px);
  }
  .footer-copy, .lb-counter, .lb-copyright, .lb-hint,
  .admin-note, .grid-item-info-text, .bar-btn-count {
    font-size: max(11px, 14px) !important;
  }
}

/* ══════════════════════════════════════════════════════
   CATEGORY CARD GRID — 2-up cards replacing list rows
   ══════════════════════════════════════════════════════ */
.cat-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: clamp(10px, 2vw, 20px);
  padding: clamp(14px, 3vw, 32px);
}
.cat-card {
  position: relative;
  overflow: hidden;
  cursor: pointer;
  border-radius: 3px;
  background: #111;
  aspect-ratio: 4 / 3;
  -webkit-tap-highlight-color: transparent;
}
/* Image fills the card */
.cat-card-img {
  width: 100%; height: 100%;
  object-fit: cover; object-position: center;
  display: block;
  filter: brightness(0.75) saturate(0.85);
  transition: filter .45s ease, transform .45s ease;
}
.cat-card:hover .cat-card-img,
.cat-card:active .cat-card-img {
  filter: brightness(0.95) saturate(1.05);
  transform: scale(1.05);
}
/* Placeholder when no image */
.cat-card-placeholder {
  width: 100%; height: 100%;
  background: linear-gradient(135deg, #1a1a1a 0%, #242424 100%);
  display: flex; align-items: center; justify-content: center;
}
.cat-card-placeholder span {
  font-size: clamp(9px, 1.5vw, 11px); letter-spacing: 3px;
  color: rgba(201,169,110,0.6); text-transform: uppercase; text-align: center;
}
/* Title bar at bottom of card */
.cat-card-bar {
  position: absolute; bottom: 0; left: 0; right: 0;
  padding: clamp(8px,1.5vw,14px) clamp(10px,2vw,18px);
  background: linear-gradient(to top, rgba(0,0,0,0.82) 0%, transparent 100%);
  display: flex; flex-direction: column; gap: 2px;
  transition: background .3s;
}
.cat-card:hover .cat-card-bar {
  background: linear-gradient(to top, rgba(20,14,0,0.9) 0%, transparent 100%);
}
.cat-card-name {
  font-family: 'Cormorant Garamond', serif;
  font-size: clamp(16px, 2.8vw, 28px);
  font-weight: 700; letter-spacing: clamp(2px,.5vw,5px);
  text-transform: uppercase; color: #fff; line-height: 1;
  transition: color .25s;
}
.cat-card:hover .cat-card-name { color: var(--gold); }
.cat-card-count {
  font-size: clamp(9px, 1.2vw, 11px); letter-spacing: 2px;
  color: rgba(255,255,255,0.6); text-transform: uppercase;
  font-family: 'Montserrat', sans-serif; font-weight: 600;
}
/* Gold border reveal on hover */
.cat-card::after {
  content: ''; position: absolute; inset: 0;
  border: 1px solid rgba(201,169,110,0);
  border-radius: 3px;
  transition: border-color .3s;
  pointer-events: none;
}
.cat-card:hover::after { border-color: rgba(201,169,110,0.35); }

/* Keep old cat-tile / sub-tile styles but hide them — 
   new card grid replaces these in tile-nav */
.cat-tile  { display: none !important; }
.sub-tile  { display: none !important; }
.sub-nav .cat-grid { padding-top: clamp(8px,2vw,20px); }

/* ── SUB-CATEGORY PAGE ── */
#sub-nav {
  display: none; padding-top: var(--hdr);
  background: var(--dark); min-height: 100svh;
  padding-bottom: 56px;
}
#sub-nav.visible { display: block; }

.breadcrumb-bar {
  display: flex; align-items: center; gap: 8px;
  padding: 14px clamp(14px,4vw,44px);
  border-bottom: 1px solid rgba(201,169,110,0.1);
}
.bc-back {
  font-size: 9px; letter-spacing: 2px;
  color: rgba(255,255,255,0.75);   /* clearly visible */
  text-transform: uppercase;
  cursor: pointer; background: rgba(255,255,255,0.06);
  border: none; border-radius: 3px;
  font-family: 'Montserrat', sans-serif; font-weight: 600;
  padding: 0 12px;
  height: 32px; display: flex; align-items: center; gap: 6px;
  transition: color .2s, background .2s;
}
.bc-back:hover, .bc-back:active {
  color: var(--gold);
  background: rgba(201,169,110,0.12);
}
.bc-sep { color: rgba(255,255,255,0.4); font-size: 11px; }
.bc-current {
  font-family: 'Cormorant Garamond', serif;
  font-size: 12px; letter-spacing: 4px;
  color: var(--gold); text-transform: uppercase;
}
.sub-panel { display: none; }
.sub-panel.active { display: block; }

/* ── SUB-TILES — compact rows, same pattern as main menu ── */
.sub-tile {
  width: 100%;
  height: clamp(72px, 14vw, 115px);
  overflow: hidden; cursor: pointer;
  border-bottom: 1px solid rgba(201,169,110,0.07);
  display: flex; align-items: stretch;
  background: #111;
  -webkit-tap-highlight-color: transparent;
  transition: background .3s;
}
.sub-tile:hover,
.sub-tile:active { background: #1c1c1c; }
/* City-level tiles are shorter and slightly indented */
.sub-tile--city {
  height: clamp(54px, 10vw, 72px);
  background: #0e0e0e;
  border-left: 2px solid rgba(201,169,110,0.15);
}
.sub-tile--city:hover,
.sub-tile--city:active { background: #181818; }

/* LEFT: sub-category name + count */
.sub-tile-left, .sub-tile-info {
  flex: 1 1 0;
  display: flex; flex-direction: column; justify-content: center;
  padding: clamp(8px,1.8vw,16px) clamp(14px,3.5vw,36px);
  min-width: 0;
  border-right: 1px solid rgba(201,169,110,0.07);
}
/* ── State list items (Karnataka, Kerala…) — medium serif ── */
.sub-tile-name {
  font-family: 'Cormorant Garamond', serif;
  font-size: clamp(18px, 3vw, 30px);
  font-weight: 400;
  letter-spacing: clamp(2px, .5vw, 5px);
  text-transform: uppercase; color: rgba(255,255,255,0.9); line-height: 1;
  transition: color .25s;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
/* ── City list items (Badami, Pattadhakal…) — small montserrat ── */
.sub-tile-name--city {
  font-family: 'Montserrat', sans-serif;
  font-size: clamp(11px, 1.6vw, 13px);
  font-weight: 600;
  letter-spacing: clamp(2px, .4vw, 4px);
  color: rgba(255,255,255,0.7);
}
.sub-tile:hover .sub-tile-name,
.sub-tile:active .sub-tile-name { color: var(--gold); }
.sub-tile-count {
  margin-top: 4px;
  font-size: 8px; letter-spacing: 2px;
  color: rgba(255,255,255,0.6); text-transform: uppercase;
}
.sub-tile-arrow {
  display: inline-block; margin-left: 7px;
  color: var(--gold); opacity: 0;
  transform: translateX(-4px);
  transition: opacity .25s, transform .25s;
  font-size: 11px;
}
.sub-tile:hover .sub-tile-arrow { opacity: 1; transform: translateX(0); }

/* RIGHT: thumbnail or Coming Soon */
.sub-tile-thumb {
  flex: 0 0 clamp(95px, 19vw, 160px);
  position: relative; overflow: hidden;
  background: #1a1a1a;
}
.sub-tile-thumb img {
  width: 100%; height: 100%;
  object-fit: cover; object-position: center; display: block;
  filter: brightness(0.80) saturate(0.82);
  transition: filter .45s, transform .45s;
}
.sub-tile:hover .sub-tile-thumb img,
.sub-tile:active .sub-tile-thumb img {
  filter: brightness(1) saturate(1);
  transform: scale(1.07);
}
.sub-tile-thumb-placeholder {
  width: 100%; height: 100%;
  display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, #181818 0%, #222 100%);
  border-left: 1px solid rgba(201,169,110,0.07);
}
.sub-tile-thumb-placeholder span {
  font-size: 9px; letter-spacing: 3px;
  color: rgba(201,169,110,0.7); text-transform: uppercase;
  text-align: center; padding: 0 6px; line-height: 1.6;
}

/* ── GALLERY ── */
#gallery-container {
  display: none; padding-top: var(--hdr);
  min-height: 100svh; background: var(--dark);
  padding-bottom: 80px;
}
#gallery-container.visible { display: block; }

.gal-header {
  padding: clamp(18px,3vw,42px) clamp(14px,4vw,44px) clamp(8px,1.5vw,18px);
  border-bottom: 1px solid rgba(201,169,110,0.1);
}
.gal-breadcrumb {
  font-size: 9px; letter-spacing: 2px;
  color: rgba(255,255,255,0.75);   /* clearly visible */
  text-transform: uppercase;
  margin-bottom: 8px; cursor: pointer;
  display: inline-flex; align-items: center; gap: 6px;
  background: rgba(255,255,255,0.06); border: none;
  border-radius: 3px; padding: 0 12px; height: 32px;
  font-family: 'Montserrat', sans-serif; font-weight: 600;
  transition: color .2s, background .2s;
}
.gal-breadcrumb:hover, .gal-breadcrumb:active {
  color: var(--gold);
  background: rgba(201,169,110,0.12);
}
/* ── LEVEL 3: Gallery title — PAGE HEADER shown at top of each panel ── */
.gal-title {
  font-family: 'Cormorant Garamond', serif;
  font-size: clamp(28px, 5vw, 52px);
  font-weight: 600; letter-spacing: clamp(3px, .8vw, 8px);
  text-transform: uppercase; line-height: 1.1;
  color: #fff; margin-top: 6px;
}
.gal-sub {
  font-size: 8px; letter-spacing: 3px;
  color: var(--gold); text-transform: uppercase;
  margin-top: 4px; opacity: .85;
}
.section-block { display: none; }
.section-block.visible { display: block; }

/* ── PHOTO GRID ── */
/*
  PHOTO GRID — responsive columns with max-width constraint
  Mobile   (<480px)   : 1 column, full width
  Tablet   (480–900px): 2 columns, full width
  Laptop   (>900px)   : 3 columns, max 1200px centred
  Desktop  (>1400px)  : 4 columns, max 1440px centred
  All cells: 3:2 aspect ratio — photos never exceed screen width
*/
.gallery-wrap {
  width: 100%;
  display: flex; justify-content: center;
  background: rgba(255,255,255,0.06);  /* white gap color between cells */
}
.grid {
  display: grid;
  gap: 3px; padding: 3px;
  background: rgba(255,255,255,0.06);
  width: 100%;
  grid-template-columns: 1fr;
}
@media (min-width: 480px) {
  .grid { grid-template-columns: 1fr 1fr; }
}
@media (min-width: 900px) {
  .grid {
    grid-template-columns: 1fr 1fr 1fr;
    max-width: 1200px;
    margin: 0 auto;
  }
}
@media (min-width: 1400px) {
  .grid {
    grid-template-columns: 1fr 1fr 1fr 1fr;
    max-width: 1440px;
  }
}

/* ── PHOTO GRID ITEMS ───────────────────────────────────────────────────────
   Each cell has:
   - White/light gap between items (grid gap on .grid)
   - Bottom action bar with ♥ Like  🛒 Buy — always visible
   - Info overlay (remarks/place) on hover
   The action bar height is fixed so the photo stays 3:2 ratio above it.
*/
/* ── PHOTO GRID ITEMS ── */
.grid-item {
  background: var(--mid);
  cursor: pointer;
  max-width: 100vw;
  /* No overflow:hidden here — bar needs to sit outside */
}
.grid-item-photo {
  position: relative;
  width: 100%;
  padding-bottom: 66.66%;   /* 3:2 ratio */
  overflow: hidden;
  background: #111;
}
.grid-item-photo img {
  position: absolute;
  inset: 0;
  width: 100%; height: 100%; object-fit: cover; display: block;
  filter: brightness(0.94);
  transition: filter .5s, transform .5s;
}
.grid-item:hover .grid-item-photo img,
.grid-item:active .grid-item-photo img {
  filter: brightness(1.05);
  transform: scale(1.04);
}
.grid-item-overlay {
  position: absolute; inset: 0;
  background: transparent; pointer-events: none;
  transition: background .3s;
}
.grid-item:hover .grid-item-overlay {
  background: linear-gradient(to top, rgba(0,0,0,0.22) 0%, transparent 50%);
}

/* Remarks/place info — slides up on hover */
.grid-item-info {
  position: absolute; bottom: 0; left: 0; right: 0;
  padding: 18px 8px 5px;
  background: linear-gradient(to top, rgba(0,0,0,0.75) 0%, transparent 100%);
  opacity: 0;
  transition: opacity .35s;
  pointer-events: none;
}
.grid-item:hover .grid-item-info { opacity: 1; }
.grid-item-info-text {
  font-size: 9px; letter-spacing: 1.5px;
  color: rgba(255,255,255,0.9);
  font-family: 'Montserrat', sans-serif;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  display: block;
}

/* ── ACTION BAR — sits below the photo ── */
.grid-item-bar {
  width: 100%;
  background: rgba(255,255,255,0.04);
  border-top: 1px solid rgba(255,255,255,0.07);
  display: flex;
  align-items: center;
  gap: 2px;
  padding: 4px 8px;
  height: 28px;
  box-sizing: border-box;
}
@media (min-width: 900px) {
  .grid-item-bar { height: 30px; padding: 4px 10px; }
}
.bar-btn {
  background: none; border: none;
  color: rgba(255,255,255,0.45);
  font-size: 13px; line-height: 1;
  cursor: pointer; padding: 3px 6px; border-radius: 3px;
  transition: color .2s, background .2s;
  display: flex; align-items: center; gap: 4px;
  font-family: 'Montserrat', sans-serif;
}
.bar-btn:hover { color: rgba(255,255,255,0.9); background: rgba(255,255,255,0.06); }
.bar-btn.liked { color: #e04060; }
.bar-btn-count {
  font-size: 8px; letter-spacing: 0;
  opacity: 0.8; min-width: 8px;
}
.bar-sep {
  width: 1px; height: 14px;
  background: rgba(255,255,255,0.1);
  margin: 0 2px;
}

/* Like badge (legacy — hidden now, counts shown in bar) */
.like-badge { display: none !important; }

/* Right-click context menu */
#ctx-menu {
  display: none; position: fixed; z-index: 99999;
  background: #111; border: 1px solid rgba(201,169,110,0.25);
  border-radius: 4px; min-width: 160px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.7);
  overflow: hidden;
}
.ctx-item {
  padding: 13px 18px; font-size: 10px; letter-spacing: 2px;
  text-transform: uppercase; color: rgba(255,255,255,0.8);
  cursor: pointer; font-family: 'Montserrat', sans-serif;
  transition: background .15s, color .15s;
  display: flex; align-items: center; gap: 10px;
}
.ctx-item:hover { background: rgba(201,169,110,0.1); color: var(--gold); }
.ctx-item.ctx-admin { color: rgba(201,169,110,0.6); }
/* Edit Tags hidden until admin unlocked */
#ctx-admin-item { display: none; }
.admin-unlocked #ctx-admin-item { display: flex; }
.ctx-divider { height: 1px; background: rgba(201,169,110,0.12); }

/* Admin tag editor modal */
#admin-modal {
  display: none; position: fixed; inset: 0; z-index: 99998;
  background: rgba(0,0,0,0.85);
  align-items: center; justify-content: center;
}
#admin-modal.open { display: flex; }
#admin-box {
  background: #111; border: 1px solid rgba(201,169,110,0.2);
  border-radius: 6px; padding: 28px 24px;
  width: min(480px, 92vw); max-height: 85vh; overflow-y: auto;
  font-family: 'Montserrat', sans-serif;
}
#admin-box h3 {
  font-family: 'Cormorant Garamond', serif;
  font-size: 18px; letter-spacing: 3px; color: var(--gold);
  text-transform: uppercase; margin-bottom: 16px;
}
.admin-field { margin-bottom: 14px; }
.admin-field label {
  display: block; font-size: 8px; letter-spacing: 2px;
  color: rgba(255,255,255,0.45); text-transform: uppercase; margin-bottom: 5px;
}
.admin-field input, .admin-field textarea {
  width: 100%; background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.1); border-radius: 3px;
  color: #fff; font-family: 'Montserrat', sans-serif;
  font-size: 11px; padding: 8px 10px;
}
.admin-field textarea { height: 60px; resize: vertical; }
.admin-cats { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 4px; }
.admin-cat {
  padding: 5px 10px; border-radius: 20px; font-size: 8px; letter-spacing: 1px;
  cursor: pointer; border: 1px solid rgba(255,255,255,0.15);
  background: rgba(255,255,255,0.04);
  color: rgba(255,255,255,0.5); text-transform: uppercase;
  transition: all .2s;
}
.admin-cat:hover { border-color: rgba(255,255,255,0.3); color: rgba(255,255,255,0.8); }
.admin-cat.selected {
  background: rgba(201,169,110,0.15); border-color: var(--gold);
  color: var(--gold);
}
.admin-row { display: flex; gap: 10px; justify-content: flex-end; margin-top: 18px; }
.admin-note { font-size: 8px; color: rgba(255,255,255,0.3); letter-spacing: 1px; margin-top: 8px; }

@media print {
  .grid-item-info, .like-badge, #ctx-menu, .grid-item-bar { display: none !important; }
}
/* NO watermark pseudo-element — removed as it showed as garbled text on some devices */

.wip-message {
  text-align: center; padding: 80px 20px;
  font-family: 'Cormorant Garamond', serif;
  font-size: clamp(14px, 2.5vw, 20px);
  color: rgba(255,255,255,0.1); text-transform: uppercase; letter-spacing: 6px;
}

/* Toast notification */
#toast {
  position: fixed; bottom: 80px; left: 50%; transform: translateX(-50%);
  background: rgba(201,169,110,0.95); color: #000;
  font-family: 'Montserrat', sans-serif; font-size: 10px; letter-spacing: 2px;
  padding: 10px 20px; border-radius: 4px;
  opacity: 0; transition: opacity .3s; pointer-events: none; z-index: 99990;
  white-space: nowrap;
}
#toast.show { opacity: 1; }

/* ── LIGHTBOX ── */
#lightbox {
  display: none; position: fixed; inset: 0; z-index: 9000;
  background: rgba(0,0,0,0.97);
  align-items: center; justify-content: center;
  touch-action: none;
}
#lightbox.open { display: flex; }
#lb-image {
  max-width: 96vw; max-height: 82svh;
  object-fit: contain; display: block;
  border: 1px solid rgba(201,169,110,0.06);
  user-select: none; -webkit-user-drag: none;
}
/* Offscreen canvas for watermark download only — never shown */
#lb-canvas-display { display: none; }
/* Loading spinner */
#lb-spinner {
  display: none; position: absolute;
  width: 36px; height: 36px;
  border: 2px solid rgba(201,169,110,0.15);
  border-top-color: rgba(201,169,110,0.7);
  border-radius: 50%;
  animation: lb-spin 0.7s linear infinite;
  pointer-events: none; z-index: 9002;
}
#lightbox.loading #lb-spinner { display: block; }
@keyframes lb-spin { to { transform: rotate(360deg); } }
.lb-btn {
  position: absolute; background: rgba(0,0,0,0.4);
  border: none; cursor: pointer;
  color: rgba(255,255,255,0.45); transition: color .2s, background .2s;
  z-index: 9001; border-radius: 50%;
  /* Large touch targets */
  width: 48px; height: 48px;
  display: flex; align-items: center; justify-content: center;
  font-size: 22px;
}
.lb-btn:hover, .lb-btn:active { color: var(--gold); background: rgba(0,0,0,0.7); }
#lb-close { top: 12px; right: 12px; font-size: 18px; }
#lb-prev  { left: 8px;  top: 50%; transform: translateY(-50%); }
#lb-next  { right: 8px; top: 50%; transform: translateY(-50%); }

.lb-meta {
  position: absolute; bottom: 0; left: 0; right: 0;
  background: linear-gradient(to top, rgba(0,0,0,0.85) 0%, transparent 100%);
  padding: 20px 16px 14px;
  display: flex; align-items: flex-end; justify-content: space-between;
  flex-wrap: wrap; gap: 4px;
}
.lb-counter {
  font-size: 8px; letter-spacing: 3px;
  color: rgba(255,255,255,0.25); text-transform: uppercase;
}
.lb-copyright {
  font-size: 8px; letter-spacing: 2px;
  color: rgba(201,169,110,0.5); text-transform: uppercase;
}
.lb-hint {
  width: 100%; font-size: 7px; letter-spacing: 2px;
  color: rgba(255,255,255,0.35); text-transform: uppercase; text-align: center;
}

/* ── SCREENSHOT DETERRENT ──
   -webkit-user-select + mix-blend-mode trick makes screenshots black on
   supported browsers. Not foolproof but raises the barrier.           */
@media screen {
  #lb-image {
    -webkit-user-select: none; user-select: none;
    -webkit-user-drag: none;
  }
}
/* On screenshot (print media used as proxy by some screenshot tools) */
@media print {
  #lightbox, #lb-image { visibility: hidden !important; background: #000 !important; }
}

/* ── COPYRIGHT BANNER ── */
#copyright-banner {
  display: none; position: fixed;
  bottom: 44px; left: 0; right: 0;
  background: rgba(8,8,8,0.95);
  border-top: 1px solid rgba(201,169,110,0.15);
  padding: 6px 12px; text-align: center; z-index: 8990;
  font-size: 8px; letter-spacing: 2px;
  color: rgba(201,169,110,0.75); text-transform: uppercase; line-height: 1.8;
}
#copyright-banner.visible { display: block; }

/* ── FOOTER ── */
footer {
  position: fixed; bottom: 0; left: 0; right: 0;
  height: 48px; background: rgba(8,8,8,0.98);
  border-top: 1px solid rgba(201,169,110,0.18);
  z-index: 9000;
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 clamp(10px,4vw,36px);
}
.footer-copy {
  font-size: 8px; letter-spacing: 2px;
  color: rgba(255,255,255,0.55);   /* visible on dark background */
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.footer-links { display: flex; gap: 6px; flex-shrink: 0; }
.footer-link {
  font-size: 9px; font-weight: 600; letter-spacing: 2px;
  color: rgba(255,255,255,0.75);
  text-transform: uppercase;
  cursor: pointer; border: none;
  background: rgba(255,255,255,0.06);
  border-radius: 3px;
  padding: 0 12px;
  font-family: 'Montserrat', sans-serif;
  height: 32px; display: flex; align-items: center;
  transition: color .2s, background .2s;
  white-space: nowrap;
}
.footer-link:hover, .footer-link:active {
  color: var(--gold);
  background: rgba(201,169,110,0.12);
}

/* ── PAGE TRANSITIONS ── */
.page-enter { animation: pEnter .35s ease forwards; }
@keyframes pEnter {
  from { opacity: 0; transform: translateY(10px); }
  to   { opacity: 1; transform: none; }
}
"""

    # ── BUILD GALLERY BLOCKS + SUB-PANELS ────────────────────────────────────
    gallery_blocks = ""
    sub_panels     = ""

    # Sort main categories A→Z; sub-lists are also sorted A→Z below
    sorted_structure = sorted(MANUAL_STRUCTURE.items(), key=lambda x: x[0].lower())

    for m_cat, subs in sorted_structure:
        subs = sorted(subs, key=lambda s: s.lower())   # sort sub-categories A→Z
        sub_items = []

        if m_cat == "Places":
            for group in ["National", "International"]:   # National first
                grp_data = place_map[group]   # {state: {city: [paths]}}

                if not grp_data:
                    # No photos yet — show Coming Soon tile
                    sub_items.append({"id": "wip-Places-" + group, "name": group,
                                      "cover": "", "count": 0, "subtitle": "Coming soon"})
                    continue

                # Collect all paths in this group for cover + count
                grp_all = []
                for cities in grp_data.values():
                    for paths in cities.values():
                        grp_all.extend(paths)
                grp_cover = thumb_map.get(pick_cover(grp_all), "")
                grp_id    = "places-group-" + group

                sub_items.append({"id": grp_id, "name": group,
                                  "cover": grp_cover, "count": len(grp_all),
                                  "subtitle": m_cat})

                # ── State tiles shown when user clicks National/International ──
                state_tiles_html = ""
                for state in sorted(grp_data.keys(), key=str.lower):
                    cities    = grp_data[state]
                    state_all = [p for ps in cities.values() for p in ps]
                    state_cover = thumb_map.get(pick_cover(state_all), "")
                    state_id    = "places-state-" + group + "-" + state.replace(' ', '-')

                    st_thumb = (
                        '<div class="sub-tile-thumb"><img src="' + state_cover + '" loading="lazy" decoding="async" alt=""></div>'
                        if state_cover else
                        '<div class="sub-tile-thumb"><div class="sub-tile-thumb-placeholder"><span>Coming<br>Soon</span></div></div>'
                    )
                    state_tiles_html += (
                        '<div class="cat-card" onclick="showSection(\'' + state_id + '\',\'' + grp_id + '\')">'
                        + (
                            '<img class="cat-card-img" src="' + state_cover + '" loading="lazy" decoding="async" alt="">'
                            if state_cover else
                            '<div class="cat-card-placeholder"><span>Coming<br>Soon</span></div>'
                        ) +
                        '<div class="cat-card-bar">'
                        '<div class="cat-card-name">' + state + '</div>'
                        '<div class="cat-card-count">' + str(len(state_all)) + ' Photos</div>'
                        '</div>'
                        '</div>'
                    )

                    # ── City tiles shown when user clicks a State ──────────────
                    city_tiles_html = ""
                    for city in sorted(cities.keys(), key=str.lower):
                        city_paths = cities[city]
                        city_id    = "places-city-" + group + "-" + state.replace(' ','_') + "-" + city.replace(' ','_')
                        city_cover = thumb_map.get(pick_cover(city_paths), "")

                        ct_thumb = (
                            '<div class="sub-tile-thumb"><img src="' + city_cover + '" loading="lazy" decoding="async" alt=""></div>'
                            if city_cover else
                            '<div class="sub-tile-thumb"><div class="sub-tile-thumb-placeholder"><span>Coming<br>Soon</span></div></div>'
                        )
                        city_tiles_html += (
                            '<div class="cat-card" onclick="showSection(\'' + city_id + '\',\'' + state_id + '\')">'
                            + (
                                '<img class="cat-card-img" src="' + city_cover + '" loading="lazy" decoding="async" alt="">'
                                if city_cover else
                                '<div class="cat-card-placeholder"><span>Coming<br>Soon</span></div>'
                            ) +
                            '<div class="cat-card-bar">'
                            '<div class="cat-card-name">' + city + '</div>'
                            '<div class="cat-card-count">' + str(len(city_paths)) + ' Photos</div>'
                            '</div>'
                            '</div>'
                        )

                        # ── Photo grid for this city ───────────────────────────
                        imgs = "".join([
                            grid_item_html(thumb_map.get(p, p), p, city, path_info, meta_by_path, web_map)
                            for p in city_paths
                        ])
                        gallery_blocks += (
                            '\n<div class="section-block" id="' + city_id + '">'
                            '\n  <div class="gal-header">'
                            '<button class="gal-breadcrumb" onclick="showSection(\'' + state_id + '\',\'' + grp_id + '\')">&larr; Back to ' + state + '</button>'
                            '<div class="gal-title">' + city + '</div>'
                            '<div class="gal-sub">' + state + ' &middot; ' + group + ' &middot; ' + str(len(city_paths)) + ' Photos</div>'
                            '</div>'
                            + ('\n  <div class="grid">' + imgs + '</div>' if city_paths else '\n  <div class="wip-message">Work in progress</div>')
                            + '\n</div>'
                        )

                    # State panel shows city tiles
                    gallery_blocks += (
                        '\n<div class="section-block" id="' + state_id + '">'
                        '\n  <div class="gal-header">'
                        '<button class="gal-breadcrumb" onclick="showSection(\'' + grp_id + '\',\'sub-Places\')">&larr; Back to ' + group + '</button>'
                        '<div class="gal-title">' + state + '</div>'
                        '<div class="gal-sub">' + group + ' &middot; ' + str(len(state_all)) + ' Photos</div>'
                        '</div>'
                        '\n  <div class="cat-grid">' + city_tiles_html + '\n  </div>'
                        '\n</div>'
                    )

                # Group panel (National/International) shows state tiles
                gallery_blocks += (
                    '\n<div class="section-block" id="' + grp_id + '">'
                    '\n  <div class="gal-header">'
                    '<button class="gal-breadcrumb" onclick="openSubNav(\'Places\')">&larr; Back to Places</button>'
                    '<div class="gal-title">' + group + '</div>'
                    '<div class="gal-sub">' + str(len(grp_all)) + ' Photos</div>'
                    '</div>'
                    '\n  <div class="cat-grid">' + state_tiles_html + '\n  </div>'
                    '\n</div>'
                )

        elif subs:
            for s_cat in subs:
                orig_paths = get_display_paths(m_cat, s_cat, tag_map)
                s_id    = "sub-" + m_cat + "-" + s_cat.replace(' ', '-')
                s_cover = thumb_map.get(pick_cover(orig_paths), "")
                sub_items.append({"id": s_id, "name": s_cat, "cover": s_cover,
                                  "count": len(orig_paths), "subtitle": m_cat})
                imgs = "".join([
                    grid_item_html(thumb_map.get(p, p), p, s_cat, path_info, meta_by_path, web_map)
                    for p in orig_paths
                ])
                gallery_blocks += (
                    '\n<div class="section-block" id="' + s_id + '">'
                    '\n  <div class="gal-header">'
                    '<button class="gal-breadcrumb" onclick="openSubNav(currentCat)">&larr; Back to ' + m_cat + '</button>'
                    '<div class="gal-title">' + s_cat + '</div>'
                    '<div class="gal-sub">' + m_cat + ' &middot; ' + str(len(orig_paths)) + ' Photos</div>'
                    '</div>'
                    + ('\n  <div class="grid">' + imgs + '</div>' if orig_paths else '\n  <div class="wip-message">Work in progress</div>')
                    + '\n</div>'
                )

        else:
            orig_paths = get_display_paths(m_cat, "", tag_map)
            s_id    = "direct-" + m_cat
            s_cover = thumb_map.get(pick_cover(orig_paths), "")
            sub_items.append({"id": s_id, "name": m_cat, "cover": s_cover,
                              "count": len(orig_paths), "subtitle": ""})
            imgs = "".join([
                grid_item_html(thumb_map.get(p, p), p, m_cat, path_info, meta_by_path, web_map)
                for p in orig_paths
            ])
            gallery_blocks += (
                '\n<div class="section-block" id="' + s_id + '">'
                '\n  <div class="gal-header">'
                '<button class="gal-breadcrumb" onclick="goHome()">&larr; Home</button>'
                '<div class="gal-title">' + m_cat + '</div>'
                '<div class="gal-sub">' + str(len(orig_paths)) + ' Photos</div>'
                '</div>'
                + ('\n  <div class="grid">' + imgs + '</div>' if orig_paths else '\n  <div class="wip-message">Work in progress</div>')
                + '\n</div>'
            )

        # Sub-panel tiles — card grid
        sub_tiles_html = ""
        for item in sub_items:
            cnt = str(item["count"]) + " Photos" if item["count"] else "Coming Soon"
            cover = item.get("cover", "")
            sub_tiles_html += (
                '\n<div class="cat-card" onclick="showGallery(\'' + item['id'] + '\')">'
                + (
                    '<img class="cat-card-img" src="' + cover + '" loading="lazy" decoding="async" alt="">'
                    if cover else
                    '<div class="cat-card-placeholder"><span>Coming<br>Soon</span></div>'
                ) +
                '<div class="cat-card-bar">'
                '<div class="cat-card-name">' + item['name'] + '</div>'
                '<div class="cat-card-count">' + cnt + '</div>'
                '</div>'
                '\n</div>'
            )
        sub_panels += (
            '\n<div class="sub-panel" id="subpanel-' + m_cat + '">'
            '\n<div class="cat-grid">'
            + sub_tiles_html
            + '\n</div>\n</div>'
        )

    # ── MAIN CATEGORY TILES ───────────────────────────────────────────────────
    cat_tiles_html = ""
    for m_cat, subs in sorted(MANUAL_STRUCTURE.items(), key=lambda x: x[0].lower()):
        raw_cover   = cat_covers.get(m_cat, "")
        thumb_cover = thumb_map.get(raw_cover, raw_cover) if raw_cover else ""

        # Count photos correctly per category type
        if m_cat == "Places":
            # Sum all photos across both National and International
            total = sum(
                len(paths)
                for grp in place_map.values()
                for cities in grp.values()
                for paths in cities.values()
            )
        elif subs:
            total = count_folder(os.path.join(ROOT_DIR, "Photos", m_cat))
        else:
            # Flat category: merge disk + tagged
            total = len(get_display_paths(m_cat, "", tag_map))

        count_lbl = str(total) + " Photos" if total else "Coming Soon"
        click     = ("openCategory('" + m_cat + "')" if subs
                     else "showGallery('direct-" + m_cat + "')")

        # Right-side thumbnail or "Coming Soon" placeholder
        if thumb_cover:
            thumb_html = (
                '<div class="cat-tile-thumb">'
                '<img src="' + thumb_cover + '" loading="lazy" decoding="async" alt="">'
                '</div>'
            )
        else:
            thumb_html = (
                '<div class="cat-tile-thumb">'
                '<div class="cat-tile-thumb-placeholder">'
                '<span>Coming<br>Soon</span>'
                '</div>'
                '</div>'
            )

        cat_tiles_html += (
            '\n<div class="cat-card" onclick="' + click + '" role="button" tabindex="0"'
            ' onkeypress="if(event.key===\'Enter\') this.click()">'
            + (
                '<img class="cat-card-img" src="' + thumb_cover + '" loading="lazy" decoding="async" alt="">'
                if thumb_cover else
                '<div class="cat-card-placeholder"><span>Coming<br>Soon</span></div>'
            ) +
            '<div class="cat-card-bar">'
            '<div class="cat-card-name">' + m_cat + '</div>'
            '<div class="cat-card-count">' + count_lbl + '</div>'
            '</div>'
            '\n</div>'
        )

    # ── BUILD RIGHT DRAWER (Collections nav) ─────────────────────────────────
    # Generated dynamically so new categories auto-appear, already sorted A→Z
    nav_drawer_rows = ''
    for m_cat, subs in sorted_structure:
        subs_sorted = sorted(subs, key=lambda s: s.lower())
        cat_id = 'dnav-' + m_cat.replace(' ', '-')
        if subs_sorted:
            # Expandable row
            sub_rows = ''
            for s in subs_sorted:
                sid = ('sub-' + m_cat + '-' + s.replace(' ', '-')
                       if m_cat != 'Places'
                       else '')
                action = ("showGallery('" + sid + "'); closeNavDrawer()"
                          if sid else "openCategory('" + m_cat + "'); closeNavDrawer()")
                sub_rows += (
                    '<div class="dnav-sub" onclick="' + action + '">'
                    '<span class="dnav-sub-dot"></span>'
                    '<span class="dnav-sub-name">' + s + '</span>'
                    '</div>'
                )
            nav_drawer_rows += (
                '<div class="dnav-cat" id="' + cat_id + '" '
                'onclick="toggleDnavCat(\'' + cat_id + '\')">'
                '<span class="dnav-cat-name">' + m_cat + '</span>'
                '<span class="dnav-chevron">&#9656;</span>'
                '</div>'
                '<div class="dnav-subs" id="subs-' + cat_id + '">'
                + sub_rows +
                '</div>'
            )
        else:
            # Direct link — no sub-menu
            action = "showGallery('direct-" + m_cat + "'); closeNavDrawer()"
            nav_drawer_rows += (
                '<div class="dnav-cat" onclick="' + action + '">'
                '<span class="dnav-cat-name">' + m_cat + '</span>'
                '<span class="dnav-chevron" style="opacity:0">&#9656;</span>'
                '</div>'
            )

    # ── JAVASCRIPT ────────────────────────────────────────────────────────────
    slides_json = json.dumps(hero_thumb_paths)

    js = """
/* ══════════════════════════════════════════════════════
   NAVIGATION — single source of truth
   All visibility is controlled ONLY via classList.
   Never mix style.display with classList on same element.
   ══════════════════════════════════════════════════════ */
var currentCat     = null;
var currentSection = null;
var currentParent  = null;

/* IDs that use classList 'visible' for show/hide */
var NAV_PANELS = ['tile-nav', 'sub-nav', 'gallery-container'];

function hideAll(){
  document.getElementById('hero').classList.remove('visible');
  NAV_PANELS.forEach(function(id){
    var el = document.getElementById(id);
    if(el) el.classList.remove('visible', 'page-enter');
  });
  document.getElementById('copyright-banner').classList.remove('visible');
  document.querySelectorAll('.info-page').forEach(function(p){ p.classList.remove('visible'); });
  document.querySelectorAll('.sub-panel').forEach(function(p){ p.classList.remove('active'); });
  document.querySelectorAll('.section-block').forEach(function(b){ b.classList.remove('visible'); });
}

function goHome(){
  hideAll();
  document.getElementById('hero').classList.add('visible');
  document.getElementById('tile-nav').classList.add('visible','page-enter');
  window.scrollTo(0,0);
}

function goCollections(){
  goHome();
  setTimeout(function(){
    var tn = document.getElementById('tile-nav');
    if(tn) tn.scrollIntoView({behavior:'smooth', block:'start'});
  }, 60);
}

function openCategory(cat){
  currentCat = cat; hideAll();
  var sn = document.getElementById('sub-nav');
  if(sn) sn.classList.add('visible','page-enter');
  var lbl = document.getElementById('bc-label');
  if(lbl) lbl.textContent = cat;
  var p = document.getElementById('subpanel-'+cat);
  if(p) p.classList.add('active');
  window.scrollTo(0,0);
}

function openSubNav(cat){ openCategory(cat); }

function showGallery(id){
  hideAll();
  var gc = document.getElementById('gallery-container');
  if(gc) gc.classList.add('visible','page-enter');
  var b = document.getElementById(id);
  if(b) b.classList.add('visible');
  document.getElementById('copyright-banner').classList.add('visible');
  window.scrollTo(0,0);
}

function showSection(targetId, parentId){
  /* Used for Places hierarchy: National→State→City */
  hideAll();
  var gc = document.getElementById('gallery-container');
  if(gc) gc.classList.add('visible');
  var el = document.getElementById(targetId);
  if(el){ el.classList.add('visible'); currentSection=targetId; currentParent=parentId; }
  window.scrollTo(0,0);
}

function showInfoPage(id){
  hideAll();
  var pg = document.getElementById(id);
  if(pg){ pg.classList.add('visible'); window.scrollTo(0,0); }
}

NAV_PANELS.forEach(function(id){
  var el = document.getElementById(id);
  if(el) el.addEventListener('animationend', function(){ this.classList.remove('page-enter'); });
});
(function(){
  var thumbs = """ + slides_json + """;
  var hero   = document.getElementById('hero');
  if (!thumbs.length) return;
  var imgs = thumbs.map(function(src){
    var img = document.createElement('img');
    img.src=src; img.className='slide';
    img.loading='lazy'; img.decoding='async'; img.alt='';
    hero.prepend(img); return img;
  });
  var cur=0; imgs[0].classList.add('active');
  setInterval(function(){
    imgs[cur].classList.remove('active');
    cur=(cur+1)%imgs.length;
    imgs[cur].classList.add('active');
  },3000);
})();

/* ── RIGHT DRAWER — Collections ── */
var navDrawer = document.getElementById('nav-drawer');
var overlay   = document.getElementById('drawer-overlay');

function openNavDrawer(){ navDrawer.classList.add('open'); overlay.classList.add('open'); document.body.style.overflow='hidden'; }
function closeNavDrawer(){ navDrawer.classList.remove('open'); overlay.classList.remove('open'); document.body.style.overflow=''; }
function toggleDnavCat(id){
  var row=document.getElementById(id), subs=document.getElementById('subs-'+id);
  if(!subs) return;
  var open=subs.classList.contains('open');
  document.querySelectorAll('.dnav-subs.open').forEach(function(el){ el.classList.remove('open'); });
  document.querySelectorAll('.dnav-cat.expanded').forEach(function(el){ el.classList.remove('expanded'); });
  if(!open){ subs.classList.add('open'); row.classList.add('expanded'); }
}

/* ── LEFT DRAWER — About ── */
var aboutDrawer = document.getElementById('about-drawer');
function openAboutDrawer(){ aboutDrawer.classList.add('open'); overlay.classList.add('open'); document.body.style.overflow='hidden'; }
function closeAboutDrawer(){ aboutDrawer.classList.remove('open'); overlay.classList.remove('open'); document.body.style.overflow=''; }

overlay.addEventListener('click', function(){ closeNavDrawer(); closeAboutDrawer(); });

/* ── Lightbox ── */
var lbImages=[], lbFullImages=[], lbIdx=0;
var lb        = document.getElementById('lightbox');
var lbImg     = document.getElementById('lb-image');
var lbCtr     = document.getElementById('lb-counter');
var lbDisplay = document.getElementById('lb-canvas-display');
var lbPreloadCache = {};
var lbCurrentLoad  = null;  /* tracks the active Image() load so we can cancel on fast navigation */

function lbShow(src, thumbSrc){
  /* Cancel any in-progress load */
  if(lbCurrentLoad){ lbCurrentLoad.onload = null; lbCurrentLoad.onerror = null; lbCurrentLoad = null; }

  /* Always show thumbnail instantly — guaranteed non-blank */
  if(thumbSrc){
    lbImg.src = thumbSrc;
    lbImg.style.opacity = '1';
  }

  /* If full image already in cache, swap immediately */
  var cached = lbPreloadCache[src];
  if(cached && cached.complete && cached.naturalWidth > 0){
    lbImg.src = src;
    lbImg.style.opacity = '1';
    lb.classList.remove('loading');
    lbPreloadAdjacent();
    return;
  }

  /* Load full image in background */
  lb.classList.add('loading');
  var full = new Image();
  lbCurrentLoad = full;
  full.onload = function(){
    if(lbCurrentLoad !== full) return;  /* superseded */
    lbPreloadCache[src] = full;
    lbCurrentLoad = null;
    lbImg.src = src;
    lbImg.style.opacity = '1';
    lb.classList.remove('loading');
    lbPreloadAdjacent();
  };
  full.onerror = function(){
    if(lbCurrentLoad !== full) return;
    lbCurrentLoad = null;
    lb.classList.remove('loading');
  };
  lbPreloadCache[src] = full;
  full.src = src;
}

function lbPreloadAdjacent(){
  [-1, 1].forEach(function(dir){
    var idx = (lbIdx + dir + lbFullImages.length) % lbFullImages.length;
    var src = lbFullImages[idx];
    if(src && !lbPreloadCache[src]){
      var img = new Image();
      img.src = src;
      lbPreloadCache[src] = img;
    }
  });
}

function lbAddWatermark(ctx, w, h){
  var fontSize = Math.max(32, Math.floor(w * 0.09));
  ctx.save();
  ctx.translate(w/2, h/2);
  ctx.rotate(-Math.PI / 5);
  ctx.font = 'bold ' + fontSize + 'px "Cormorant Garamond", Georgia, serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.shadowColor   = 'rgba(0,0,0,0.2)';
  ctx.shadowBlur    = fontSize * 0.15;
  ctx.shadowOffsetX = fontSize * 0.03;
  ctx.shadowOffsetY = fontSize * 0.03;
  ctx.fillStyle = 'rgba(255,255,255,0.18)';
  ctx.fillText('MOHANGRAPHY', 0, 0);
  ctx.restore();
}

function openLightbox(el){
  var grid = el.closest('.grid');
  if(!grid) return;
  var items  = Array.from(grid.querySelectorAll('.grid-item'));
  var imgEls = Array.from(grid.querySelectorAll('.grid-item-photo img'));
  lbFullImages = imgEls.map(function(i){ return i.getAttribute('data-full')||i.src; });
  lbImages     = imgEls.map(function(i){ return i.src; });
  lbIdx = items.indexOf(el);
  if(lbIdx<0) lbIdx=0;
  lb.classList.add('open');
  document.body.style.overflow='hidden';
  lbShow(lbFullImages[lbIdx]||'', lbImages[lbIdx]||'');
  lbCtr.textContent = (lbIdx+1)+' / '+lbImages.length;
}
function closeLightbox(){
  if(lbCurrentLoad){ lbCurrentLoad.onload = null; lbCurrentLoad.onerror = null; lbCurrentLoad = null; }
  lb.classList.remove('open','loading');
  document.body.style.overflow='';
  /* Reset image so no stale image on next open */
  lbImg.src = '';
  lbImg.style.opacity = '1';
}
function lbStep(dir){
  lbIdx=(lbIdx+dir+lbFullImages.length)%lbFullImages.length;
  lbShow(lbFullImages[lbIdx], lbImages[lbIdx]);
  lbCtr.textContent=(lbIdx+1)+' / '+lbFullImages.length;
}
lb.addEventListener('click', function(e){ if(e.target===lb) closeLightbox(); });
var tsX=null, tsY=null;
lb.addEventListener('touchstart', function(e){ tsX=e.touches[0].clientX; tsY=e.touches[0].clientY; },{passive:true});
lb.addEventListener('touchend', function(e){
  if(tsX===null) return;
  var dx=e.changedTouches[0].clientX-tsX, dy=e.changedTouches[0].clientY-tsY;
  if(Math.abs(dx)>Math.abs(dy)&&Math.abs(dx)>44) lbStep(dx<0?1:-1);
  tsX=null; tsY=null;
});

/* Right-click on lightbox → download watermarked copy via canvas */
lbImg.addEventListener('contextmenu', function(e){
  e.preventDefault();
  var canvas = document.getElementById('lb-canvas');
  canvas.width  = lbImg.naturalWidth;
  canvas.height = lbImg.naturalHeight;
  var ctx = canvas.getContext('2d');
  try {
    ctx.drawImage(lbImg, 0, 0);
    lbAddWatermark(ctx, canvas.width, canvas.height);
    var a = document.createElement('a');
    a.href = canvas.toDataURL('image/jpeg', 0.92);
    a.download = 'mohangraphy-' + (lbIdx+1) + '.jpg';
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
  } catch(e2) {
    /* CORS blocked canvas — just show toast */
    showToast('Right-click save blocked. Contact for licensed copy.');
  }
});
var lbLpTimer = null;
lbImg.addEventListener('touchstart', function(){ lbLpTimer = setTimeout(function(){ showToast('Contact ncmohan.photos@gmail.com for a licensed copy.'); }, 800); },{passive:true});
lbImg.addEventListener('touchend',  function(){ clearTimeout(lbLpTimer); },{passive:true});
lbImg.addEventListener('touchmove', function(){ clearTimeout(lbLpTimer); },{passive:true});

document.addEventListener('keydown', function(e){
  if(e.key==='Escape'){
    if(lb.classList.contains('open')) closeLightbox();
    else { closeNavDrawer(); closeAboutDrawer(); }
  }
  if(!lb.classList.contains('open')) return;
  if(e.key==='ArrowRight') lbStep(1);
  if(e.key==='ArrowLeft')  lbStep(-1);
});

/* ══════════════════════════════════════════════════════
   LIKES — shared across all visitors via Supabase
   Free tier: https://supabase.com
   Set your project URL and anon key in content.json:
     "supabase_url": "https://xxxx.supabase.co",
     "supabase_anon_key": "eyJ..."
   Table setup (run once in Supabase SQL editor):
     CREATE TABLE likes (
       photo TEXT PRIMARY KEY,
       count INTEGER DEFAULT 0
     );
     ALTER TABLE likes ENABLE ROW LEVEL SECURITY;
     CREATE POLICY "read" ON likes FOR SELECT USING (true);
     CREATE POLICY "upsert" ON likes FOR INSERT WITH CHECK (true);
     CREATE POLICY "update" ON likes FOR UPDATE USING (true);
   ══════════════════════════════════════════════════════ */
var SUPA_URL  = '""" + supabase_url + """';
var SUPA_KEY  = '""" + supabase_key + """';
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

function getLikeCount(photo, cb){
  supaRequest('GET', 'likes?photo=eq.'+encodeURIComponent(photo)+'&select=count')
    .then(function(rows){ cb(rows&&rows[0] ? rows[0].count : 0); })
    .catch(function(){ cb(localLikes[photo]||0); });
}

function barLike(btn){
  var item = btn.closest('.grid-item');
  var key  = getPhotoKey(item);
  if(!key) return;
  var liked = !!localLikes[key];
  if(liked){
    localLikes[key] = false;
    localStorage.setItem('mohan_likes2', JSON.stringify(localLikes));
    btn.classList.remove('liked');
    /* Decrement in Supabase */
    supaRequest('GET', 'likes?photo=eq.'+encodeURIComponent(key)+'&select=count')
      .then(function(rows){
        var cur = rows&&rows[0] ? rows[0].count : 1;
        return supaRequest('POST', 'likes', {photo:key, count:Math.max(0,cur-1)});
      })
      .then(function(rows){
        var n = rows&&rows[0] ? rows[0].count : 0;
        refreshLikeCount(btn, n);
      })
      .catch(function(){
        refreshLikeCount(btn, 0);
      });
  } else {
    localLikes[key] = true;
    localStorage.setItem('mohan_likes2', JSON.stringify(localLikes));
    btn.classList.add('liked');
    /* Increment in Supabase */
    supaRequest('GET', 'likes?photo=eq.'+encodeURIComponent(key)+'&select=count')
      .then(function(rows){
        var cur = rows&&rows[0] ? rows[0].count : 0;
        return supaRequest('POST', 'likes', {photo:key, count:cur+1});
      })
      .then(function(rows){
        var n = rows&&rows[0] ? rows[0].count : 1;
        refreshLikeCount(btn, n);
      })
      .catch(function(){
        refreshLikeCount(btn, 1);
      });
  }
}

function refreshLikeCount(btn, n){
  var span = btn.querySelector('.like-count');
  if(span) span.textContent = n>0 ? n : '';
}

function initLikes(){
  document.querySelectorAll('.grid-item').forEach(function(item){
    var key = getPhotoKey(item);
    var btn = item.querySelector('.like-btn');
    if(!key||!btn) return;
    if(localLikes[key]) btn.classList.add('liked');
    getLikeCount(key, function(n){ refreshLikeCount(btn, n); });
  });
}
document.addEventListener('DOMContentLoaded', initLikes);

/* ── Buy ── */
var pendingBuyPhoto='', pendingBuySize='';
function barBuy(btn){
  var item=btn.closest('.grid-item'), img=item.querySelector('img');
  pendingBuyPhoto=img?(img.getAttribute('data-full')||img.src).split('/').pop().replace(/[.][^.]+$/,''):'';
  showInfoPage('page-prints');
}
function orderSize(size){
  pendingBuySize=size; showInfoPage('page-contact');
  var subj=document.getElementById('cf-subject');
  if(subj) for(var i=0;i<subj.options.length;i++){ if(subj.options[i].text.indexOf('Print')>-1){subj.selectedIndex=i;break;} }
  var msg=document.getElementById('cf-msg');
  if(msg&&pendingBuyPhoto) msg.value='I would like to order a print:\\nPhoto: '+pendingBuyPhoto+'\\nSize: '+pendingBuySize+'\\n\\nPlease let me know pricing and shipping details.';
  pendingBuyPhoto=''; pendingBuySize='';
}
function clearContactForm(){
  ['cf-name','cf-email','cf-msg'].forEach(function(id){ var el=document.getElementById(id); if(el) el.value=''; });
  var subj=document.getElementById('cf-subject'); if(subj) subj.selectedIndex=0;
}

/* ══════════════════════════════════════════════════════
   CONTEXT MENU — right-click / long-press
   ══════════════════════════════════════════════════════ */
var ctxMenu   = document.getElementById('ctx-menu');
var ctxTarget = null;

function showCtxMenu(el, x, y){
  ctxTarget = el;
  ctxMenu.style.left = Math.min(x, window.innerWidth-190)+'px';
  ctxMenu.style.top  = Math.min(y, window.innerHeight-170)+'px';
  ctxMenu.style.display = 'block';
}
function hideCtxMenu(){ ctxMenu.style.display='none'; ctxTarget=null; }

document.addEventListener('click',       function(e){ if(!e.target.closest('#ctx-menu')) hideCtxMenu(); });
document.addEventListener('contextmenu', function(e){
  var item=e.target.closest('.grid-item');
  if(item){ e.preventDefault(); showCtxMenu(item, e.clientX, e.clientY); }
  else hideCtxMenu();
});

/* Long-press mobile */
var lpTimer=null, lpEl=null;
document.addEventListener('touchstart', function(e){
  var item=e.target.closest('.grid-item'); if(!item) return;
  lpEl=item; lpTimer=setTimeout(function(){ showCtxMenu(lpEl, e.touches[0].clientX, e.touches[0].clientY); },600);
},{passive:true});
document.addEventListener('touchend',  function(){ clearTimeout(lpTimer); },{passive:true});
document.addEventListener('touchmove', function(){ clearTimeout(lpTimer); },{passive:true});

function ctxLike(){ var t=ctxTarget; hideCtxMenu(); if(t){ var b=t.querySelector('.like-btn'); if(b) barLike(b); } }
function ctxBuy(){  var t=ctxTarget; hideCtxMenu(); if(t) barBuy(t.querySelector('.buy-btn')); }

/* ══════════════════════════════════════════════════════
   ADMIN TAG EDITOR
   Password protected. Right-click any photo → Edit tags.
   Sends patch to patch_tags.py server (localhost:9393).
   ══════════════════════════════════════════════════════ */
var ADMIN_UNLOCKED = false;
var ADMIN_PASS     = '""" + admin_password + """';
var adminItems     = [];
var adminLastSaved = {state:'', city:'', cats:[]};
var CATEGORIES     = """ + json.dumps(sorted([
    "Architecture","Nature/Birds","Nature/Flowers","Nature/Landscape",
    "Nature/Landscape/Mountains","Nature/Sunsets","Nature/Wildlife",
    "People/Portraits","Places/International","Places/National"
])) + """;

function ctxAdminEdit(){
  var target = ctxTarget;
  hideCtxMenu();
  if(!target) return;
  adminItems = [target];
  openAdminModal();
}

function openAdminModal(){
  var first  = adminItems[0];
  var photo  = first ? first.getAttribute('data-photo')  : '';
  var state  = first ? first.getAttribute('data-state')  : '';
  var city   = first ? first.getAttribute('data-city')   : '';
  var rem    = first ? first.getAttribute('data-remarks'): '';
  var cats   = first ? (first.getAttribute('data-cats')||'').split(',').filter(Boolean) : [];

  /* If photo has no state/city/remarks yet, carry forward from last save */
  if(!state && !city && !rem && adminLastSaved.state)  state   = adminLastSaved.state;
  if(!state && !city && !rem && adminLastSaved.city)   city    = adminLastSaved.city;
  if(!cats.length  && adminLastSaved.cats.length)      cats    = adminLastSaved.cats.slice();

  /* Build category buttons */
  var catDiv = document.getElementById('admin-cats');
  catDiv.innerHTML = '';
  CATEGORIES.forEach(function(c){
    var btn = document.createElement('button');
    btn.className = 'admin-cat';
    btn.textContent = c.split('/').pop();
    btn.title = c;
    btn.setAttribute('data-cat', c);
    if(cats.indexOf(c) > -1) btn.classList.add('selected');
    btn.onclick = function(){ btn.classList.toggle('selected'); };
    catDiv.appendChild(btn);
  });

  /* Pre-fill fields */
  document.getElementById('admin-photo-ref').textContent = photo.split('/').pop();
  document.getElementById('admin-count').textContent     = adminItems.length + ' photo(s)';
  document.getElementById('admin-state').value   = state;
  document.getElementById('admin-city').value    = city;
  document.getElementById('admin-remarks').value = rem;

  /* Show correct screen */
  if(!ADMIN_UNLOCKED){
    document.getElementById('admin-pw-screen').style.display  = 'block';
    document.getElementById('admin-edit-screen').style.display = 'none';
    document.getElementById('admin-pw-input').value = '';
    document.getElementById('admin-pw-error').style.display   = 'none';
  } else {
    document.getElementById('admin-pw-screen').style.display  = 'none';
    document.getElementById('admin-edit-screen').style.display = 'block';
  }
  document.getElementById('admin-modal').classList.add('open');
}

function adminCheckPassword(){
  var pw = document.getElementById('admin-pw-input').value;
  if(pw !== ADMIN_PASS){
    document.getElementById('admin-pw-error').style.display = 'block';
    return;
  }
  ADMIN_UNLOCKED = true;
  document.body.classList.add('admin-unlocked');
  document.getElementById('admin-pw-screen').style.display  = 'none';
  document.getElementById('admin-edit-screen').style.display = 'block';
}

function closeAdminModal(){
  document.getElementById('admin-modal').classList.remove('open');
  adminItems=[];
}

function saveAdminTags(){
  var cats    = Array.from(document.querySelectorAll('.admin-cat.selected')).map(function(b){ return b.getAttribute('data-cat'); });
  var state   = document.getElementById('admin-state').value.trim();
  var city    = document.getElementById('admin-city').value.trim();
  var remarks = document.getElementById('admin-remarks').value.trim();
  var photos  = adminItems.map(function(item){ return item.getAttribute('data-photo'); });
  var payload = {categories:cats, state:state, city:city, remarks:remarks, photos:photos};

  /* Store for carry-forward to next photo */
  adminLastSaved = {state:state, city:city, cats:cats.slice()};

  /* Update DOM data attributes so re-editing same photo shows latest values */
  adminItems.forEach(function(item){
    item.setAttribute('data-state',   state);
    item.setAttribute('data-city',    city);
    item.setAttribute('data-remarks', remarks);
    item.setAttribute('data-cats',    cats.join(','));
  });

  fetch('http://localhost:9393/patch',{
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify(payload)
  }).then(function(r){ return r.json(); })
    .then(function(d){ showToast('✓ Saved. Run deploy to publish.'); })
    .catch(function(){
      navigator.clipboard.writeText(JSON.stringify(payload,null,2))
        .then(function(){ showToast('Server offline. JSON copied to clipboard.'); })
        .catch(function(){ showToast('Start patch_tags.py, then try again.'); });
    });
  closeAdminModal();
}

/* ── Toast ── */
function showToast(msg){
  var t=document.getElementById('toast');
  t.textContent=msg; t.classList.add('show');
  setTimeout(function(){ t.classList.remove('show'); },3000);
}

/* ── Contact form ── */
function submitContact(){
  var name=document.getElementById('cf-name').value.trim();
  var email=document.getElementById('cf-email').value.trim();
  var subject=document.getElementById('cf-subject').value;
  var msg=document.getElementById('cf-msg').value.trim();
  if(!name||!email||!msg){ alert('Please fill all fields.'); return; }
  var body=encodeURIComponent('Name: '+name+'\\nEmail: '+email+'\\n\\n'+msg);
  window.location.href='mailto:""" + contact_email + """?subject='+encodeURIComponent(subject)+'&body='+body;
  setTimeout(clearContactForm,500);
}

goHome();
"""

    # ── ASSEMBLE HTML ─────────────────────────────────────────────────────────
    html = (
        '<!DOCTYPE html>\n'
        '<html lang="en">\n'
        '<head>\n'
        '  <meta charset="UTF-8">\n'
        '  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">\n'
        '  <meta name="theme-color" content="#080808">\n'
        '  <meta name="description" content="Mohangraphy — Fine art photography by N C Mohan. '
        'Landscapes, wildlife, architecture and more. All photographs copyright N C Mohan.">\n'
        '  <meta property="og:title" content="Mohangraphy — Photography by N C Mohan">\n'
        '  <meta property="og:description" content="Fine art photography — Light · Moment · Story">\n'
        '  <meta property="og:type" content="website">\n'
        '  <title>MOHANGRAPHY — Photography by N C Mohan</title>\n'
        + ('  <script defer data-domain="' + plausible_domain + '" src="https://plausible.io/js/script.js"></script>\n' if plausible_domain else '')
        + '  <script>/* GA opt-out — set once on your own devices via browser console: localStorage.setItem("ga_optout","1") */\n'
        + '  if(localStorage.getItem("ga_optout")==="1"){\n'
        + '    window["ga-disable-G-XXXXXXXXXX"]=true; /* replace G-XXXXXXXXXX with your GA measurement ID */\n'
        + '    window["ga-disable-UA-XXXXXXXXX-X"]=true;\n'
        + '  }\n'
        + '  </script>\n'
        + '  <style>' + css + '</style>\n'
        '</head>\n'
        '<body>\n'
        '<div id="toast"></div>\n\n'

        # ── HEADER ──────────────────────────────────────────────────────────
        '<!-- HEADER -->\n'
        '<header>\n'

        # Left icon — person / about
        '  <button class="hdr-icon-left" onclick="openAboutDrawer()" aria-label="About &amp; Contact">\n'
        '    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">\n'
        '      <circle cx="12" cy="8" r="4"/>\n'
        '      <path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/>\n'
        '    </svg>\n'
        '  </button>\n'

        # Centre title — double-click toggles admin mode
        '  <div class="site-title" onclick="goHome()" ondblclick="toggleAdminMode()" role="button" tabindex="0"\n'
        '       onkeypress="if(event.key===\'Enter\') goHome()">M O H A N G R A P H Y</div>\n'

        # Right icon — hamburger / collections
        '  <button class="hdr-icon-right" onclick="openNavDrawer()" aria-label="Collections menu">\n'
        '    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round">\n'
        '      <line x1="3" y1="6"  x2="21" y2="6"/>\n'
        '      <line x1="3" y1="12" x2="21" y2="12"/>\n'
        '      <line x1="3" y1="18" x2="21" y2="18"/>\n'
        '    </svg>\n'
        '  </button>\n'
        '</header>\n\n'

        # ── OVERLAY ─────────────────────────────────────────────────────────
        '<div id="drawer-overlay" class="drawer-overlay"></div>\n\n'

        # ── RIGHT DRAWER (hamburger) — Home, Contact, Order Prints only ────────
        '<div id="nav-drawer" role="navigation" aria-label="Menu">\n'
        '  <div class="drawer-header">\n'
        '    <span class="drawer-header-title">Menu</span>\n'
        '    <button class="drawer-close" onclick="closeNavDrawer()" aria-label="Close">&#x2715;</button>\n'
        '  </div>\n'
        '  <div class="drawer-scroll">\n'
        '    <div class="dnav-cat" onclick="goHome(); closeNavDrawer()">'
        '<span class="dnav-cat-name" style="color:var(--gold)">Home</span>'
        '<span class="dnav-chevron" style="opacity:0">&#9656;</span>'
        '</div>\n'
        '    <div class="dnav-divider"></div>\n'
        '    <div class="dnav-cat" onclick="showInfoPage(\'page-contact\'); closeNavDrawer()">'
        '<span class="dnav-cat-name">Contact</span>'
        '<span class="dnav-chevron" style="opacity:0">&#9656;</span>'
        '</div>\n'
        '    <div class="dnav-cat" onclick="showInfoPage(\'page-prints\'); closeNavDrawer()">'
        '<span class="dnav-cat-name">Order Print(s)</span>'
        '<span class="dnav-chevron" style="opacity:0">&#9656;</span>'
        '</div>\n'
        '  </div>\n'
        '</div>\n\n'

        # ── LEFT DRAWER (About / Contact / Commercial) ───────────────────────
        '<div id="about-drawer" role="navigation" aria-label="About and contact">\n'
        '  <div class="drawer-header">\n'
        '    <span class="drawer-header-title">Menu</span>\n'
        '    <button class="drawer-close" onclick="closeAboutDrawer()" aria-label="Close">&#x2715;</button>\n'
        '  </div>\n'
        '  <div class="about-scroll">\n'

        '    <div class="adrawer-section-hdr">Photographer</div>\n'

        '    <div class="adrawer-item" onclick="showInfoPage(\'page-about\'); closeAboutDrawer()">\n'
        '      <div class="adrawer-icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/></svg></div>\n'
        '      <span class="adrawer-label">About Me</span>\n'
        '    </div>\n'

        '    <div class="adrawer-item" onclick="showInfoPage(\'page-philosophy\'); closeAboutDrawer()">\n'
        '      <div class="adrawer-icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><path d="M12 2l2 7h7l-5.5 4 2 7L12 16l-5.5 4 2-7L3 9h7z"/></svg></div>\n'
        '      <span class="adrawer-label">Philosophy</span>\n'
        '    </div>\n'

        '    <div class="adrawer-item" onclick="showInfoPage(\'page-gear\'); closeAboutDrawer()">\n'
        '      <div class="adrawer-icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><circle cx="12" cy="12" r="3"/><path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83"/></svg></div>\n'
        '      <span class="adrawer-label">Gear &amp; Kit</span>\n'
        '    </div>\n'

        '    <div class="adrawer-item" onclick="showInfoPage(\'page-licensing\'); closeAboutDrawer()">\n'
        '      <div class="adrawer-icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14,2 14,8 20,8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10,9 9,9 8,9"/></svg></div>\n'
        '      <span class="adrawer-label">Licensing</span>\n'
        '    </div>\n'

        '    <div class="adrawer-section-hdr">Legal</div>\n'

        '    <div class="adrawer-item" onclick="showInfoPage(\'page-legal\'); closeAboutDrawer()">\n'
        '      <div class="adrawer-icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg></div>\n'
        '      <span class="adrawer-label">Copyright &amp; Legal</span>\n'
        '    </div>\n'

        '  </div>\n'
        '</div>\n\n'

        # ── HERO ────────────────────────────────────────────────────────────
        '<!-- HERO -->\n'
        '<div id="hero">\n'
        '  <div class="hero-caption">\n'
        '    <div class="hero-tagline">Light <span class="dot">&middot;</span> Moment <span class="dot">&middot;</span> Story</div>\n'
        '    <div class="hero-byline"><span class="byline-label">Photos by</span><span class="name">N C Mohan</span></div>\n'
        '  </div>\n'
        '  <div class="scroll-cue">\n'
        '    <svg width="12" height="18" viewBox="0 0 12 18" fill="none">\n'
        '      <path d="M6 2v10M2 9l4 5 4-5" stroke="rgba(255,255,255,0.3)" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>\n'
        '    </svg>\n'
        '    <span>Explore</span>\n'
        '  </div>\n'
        '</div>\n\n'

        # ── MAIN MENU ────────────────────────────────────────────────────────
        '<div id="tile-nav">\n'
        '  <div class="tile-nav-label">Collections</div>\n'
        '  <div class="cat-grid">\n'
        + cat_tiles_html +
        '\n  </div>\n'
        '\n</div>\n\n'

        # ── SUB-NAV ──────────────────────────────────────────────────────────
        '<div id="sub-nav">\n'
        '  <div class="breadcrumb-bar">\n'
        '    <button class="bc-back" onclick="goHome()">&larr; Home</button>\n'
        '    <span class="bc-sep">|</span>\n'
        '    <span class="bc-current" id="bc-label"></span>\n'
        '  </div>\n'
        + sub_panels +
        '\n</div>\n\n'

        # ── GALLERY ──────────────────────────────────────────────────────────
        '<main id="gallery-container">\n'
        + gallery_blocks +
        '\n</main>\n\n'

        # ── INFO PAGES ───────────────────────────────────────────────────────
        # ABOUT ME
        '<div id="page-about" class="info-page">\n'
        '  <div class="info-page-inner">\n'
        '    <button class="info-page-back" onclick="goHome()">&larr; Back to Home</button>\n'
        '    <div class="info-page-title">' + c_about.get('title','About Me') + '</div>\n'
        '    <div class="info-page-subtitle">' + c_about.get('subtitle','Photographer · ' + photographer) + '</div>\n'
        '    <div class="info-page-divider"></div>\n'
        '    <div class="info-page-body">\n'
        + render_paragraphs(c_about.get('paragraphs', ['[ Add your story in content.json ]'])) +
        '    </div>\n  </div>\n</div>\n\n'

        # PHILOSOPHY
        '<div id="page-philosophy" class="info-page">\n'
        '  <div class="info-page-inner">\n'
        '    <button class="info-page-back" onclick="goHome()">&larr; Back to Home</button>\n'
        '    <div class="info-page-title">' + c_phil.get('title','Philosophy') + '</div>\n'
        '    <div class="info-page-subtitle">' + c_phil.get('subtitle','How I see the world') + '</div>\n'
        '    <div class="info-page-divider"></div>\n'
        '    <div class="info-page-body">\n'
        + render_paragraphs(c_phil.get('paragraphs', ['[ Add your philosophy in content.json ]'])) +
        '    </div>\n  </div>\n</div>\n\n'

        # GEAR
        '<div id="page-gear" class="info-page">\n'
        '  <div class="info-page-inner">\n'
        '    <button class="info-page-back" onclick="goHome()">&larr; Back to Home</button>\n'
        '    <div class="info-page-title">' + c_gear.get('title','Gear &amp; Kit') + '</div>\n'
        '    <div class="info-page-subtitle">' + c_gear.get('subtitle','The tools of the trade') + '</div>\n'
        '    <div class="info-page-divider"></div>\n'
        '    <div class="info-page-body">\n'
        + render_items(c_gear.get('items', [])) +
        '    </div>\n  </div>\n</div>\n\n'

        # CONTACT
        '<div id="page-contact" class="info-page">\n'
        '  <div class="info-page-inner">\n'
        '    <button class="info-page-back" onclick="goHome()">&larr; Back to Home</button>\n'
        '    <div class="info-page-title">' + c_contact.get('title','Contact') + '</div>\n'
        '    <div class="info-page-subtitle">' + c_contact.get('subtitle','Get in touch') + '</div>\n'
        '    <div class="info-page-divider"></div>\n'
        '    <div class="info-page-body"><p>' + c_contact.get('intro','') + '</p></div>\n'
        '    <div class="contact-field"><label>Your Name *</label>'
        '<input type="text" id="cf-name" placeholder="Full name"></div>\n'
        '    <div class="contact-field"><label>Email Address *</label>'
        '<input type="email" id="cf-email" placeholder="you@example.com"></div>\n'
        '    <div class="contact-field"><label>Subject</label>'
        '<select id="cf-subject">'
        + ''.join('<option>' + s + '</option>' for s in c_contact.get('subjects', ['General Enquiry']))
        + '</select></div>\n'
        '    <div class="contact-field"><label>Message *</label>'
        '<textarea id="cf-msg" placeholder="Your message..."></textarea></div>\n'
        '    <button class="btn-gold" onclick="submitContact()">Send Message</button>\n'
        '  </div>\n</div>\n\n'

        # PRINT SALES
        '<div id="page-prints" class="info-page">\n'
        '  <div class="info-page-inner">\n'
        '    <button class="info-page-back" onclick="goHome()">&larr; Back to Home</button>\n'
        '    <div class="info-page-title">' + c_prints.get('title','Order Print(s)') + '</div>\n'
        '    <div class="info-page-subtitle">' + c_prints.get('subtitle','Own a piece of the light') + '</div>\n'
        '    <div class="info-page-divider"></div>\n'
        '    <div class="info-page-body">'
        '<p>' + c_prints.get('intro','') + '</p>'
        '<p>' + c_prints.get('note','') + '</p>'
        '</div>\n'
        '    <div class="prints-grid">\n'
        + ''.join(
            '      <div class="print-card">'
            '<div class="print-card-size">' + s.get('size','') + '</div>'
            '<div class="print-card-desc">'
            + '\n'.join(s.get('dimensions','').replace(' | ', '\n').split('\n'))
            + '</div>'
            '<div class="print-card-price">' + s.get('price','On request') + '</div>'
            '<button class="btn-gold" style="margin-top:10px;font-size:8px;padding:8px 14px;" '
            'onclick="orderSize(\'' + s.get('size','') + '\')">Order this size</button>'
            '</div>\n'
            for s in c_prints.get('sizes', [])
        ) +
        '    </div>\n'
        '    <div class="info-page-divider"></div>\n'
        '    <p style="font-size:13px;color:rgba(255,255,255,0.4);letter-spacing:1px;">'
        'To order or enquire about a specific image, please use the '
        '<button style="background:none;border:none;color:var(--gold);cursor:pointer;'
        'font-size:13px;letter-spacing:1px;padding:0;" '
        'onclick="showInfoPage(\'page-contact\')">Contact</button> page.</p>\n'
        '  </div>\n</div>\n\n'

        # LICENSING
        '<div id="page-licensing" class="info-page">\n'
        '  <div class="info-page-inner">\n'
        '    <button class="info-page-back" onclick="goHome()">&larr; Back to Home</button>\n'
        '    <div class="info-page-title">' + c_licens.get('title','Licensing') + '</div>\n'
        '    <div class="info-page-subtitle">' + c_licens.get('subtitle','Usage rights &amp; commercial use') + '</div>\n'
        '    <div class="info-page-divider"></div>\n'
        '    <div class="info-page-body">\n'
        + render_paragraphs(c_licens.get('paragraphs', [])) +
        '    </div>\n  </div>\n</div>\n\n'

        # WORKSHOPS
        '<div id="page-workshops" class="info-page">\n'
        '  <div class="info-page-inner">\n'
        '    <button class="info-page-back" onclick="goHome()">&larr; Back to Home</button>\n'
        '    <div class="info-page-title">' + c_workshop.get('title','Workshops &amp; Tours') + '</div>\n'
        '    <div class="info-page-subtitle">' + c_workshop.get('subtitle','Learn to see, learn to shoot') + '</div>\n'
        '    <div class="info-page-divider"></div>\n'
        '    <div class="info-page-body">\n'
        + render_paragraphs(c_workshop.get('paragraphs', [])) +
        '    </div>\n  </div>\n</div>\n\n'

        # LEGAL
        '<div id="page-legal" class="info-page">\n'
        '  <div class="info-page-inner">\n'
        '    <button class="info-page-back" onclick="goHome()">&larr; Back to Home</button>\n'
        '    <div class="info-page-title">' + c_legal.get('title','Copyright &amp; Legal') + '</div>\n'
        '    <div class="info-page-subtitle">' + c_legal.get('subtitle','Your rights and ours') + '</div>\n'
        '    <div class="info-page-divider"></div>\n'
        '    <div class="info-page-body">\n'
        + render_items(c_legal.get('items', [])) +
        '    </div>\n  </div>\n</div>\n\n'

        # ── CONTEXT MENU ─────────────────────────────────────────────────────
        '<div id="ctx-menu">\n'
        '  <div class="ctx-item" onclick="ctxLike()">&#10084;&nbsp; Like</div>\n'
        '  <div class="ctx-divider"></div>\n'
        '  <div class="ctx-item" onclick="ctxBuy()">&#128722;&nbsp; Buy a print</div>\n'
        '  <div class="ctx-divider"></div>\n'
        '  <div class="ctx-item ctx-admin" id="ctx-admin-item" onclick="ctxAdminEdit()">&#9881;&nbsp; Edit tags</div>\n'
        '</div>\n\n'

        # ── ADMIN MODAL ──────────────────────────────────────────────────────
        '<div id="admin-modal">\n'
        '  <div id="admin-box">\n'
        '    <h3>Edit Tags</h3>\n'
        '    <!-- Password screen (shown first) -->\n'
        '    <div id="admin-pw-screen">\n'
        '      <div class="admin-field">\n'
        '        <label>Admin Password</label>\n'
        '        <input id="admin-pw-input" type="password" placeholder="Enter password"\n'
        '               onkeydown="if(event.key===\'Enter\') adminCheckPassword()">\n'
        '      </div>\n'
        '      <div id="admin-pw-error" style="display:none;color:#e04060;font-size:9px;letter-spacing:1px;margin-bottom:10px">Incorrect password</div>\n'
        '      <div class="admin-row">\n'
        '        <button class="btn-ghost" onclick="closeAdminModal()">Cancel</button>\n'
        '        <button class="btn-gold" onclick="adminCheckPassword()">Unlock</button>\n'
        '      </div>\n'
        '    </div>\n'
        '    <!-- Edit screen (shown after password) -->\n'
        '    <div id="admin-edit-screen" style="display:none">\n'
        '      <div style="font-size:8px;color:rgba(255,255,255,0.3);letter-spacing:1px;margin-bottom:6px" id="admin-photo-ref"></div>\n'
        '      <div style="font-size:8px;color:var(--gold);letter-spacing:1px;margin-bottom:14px" id="admin-count"></div>\n'
        '      <div class="admin-field"><label>Categories (tap to toggle)</label><div class="admin-cats" id="admin-cats"></div></div>\n'
        '      <div class="admin-field"><label>State / Country</label><input id="admin-state" type="text" placeholder="e.g. Karnataka"></div>\n'
        '      <div class="admin-field"><label>City</label><input id="admin-city" type="text" placeholder="e.g. Badami"></div>\n'
        '      <div class="admin-field"><label>Remarks</label><textarea id="admin-remarks" placeholder="e.g. Great Hornbill in flight"></textarea></div>\n'
        '      <p class="admin-note">Run patch_tags.py on your Mac first, then Save will update photo_metadata.json automatically.</p>\n'
        '      <div class="admin-row">\n'
        '        <button class="btn-ghost" onclick="closeAdminModal()">Cancel</button>\n'
        '        <button class="btn-gold" onclick="saveAdminTags()">Save</button>\n'
        '      </div>\n'
        '    </div>\n'
        '  </div>\n'
        '</div>\n\n'

        # ── LIGHTBOX ─────────────────────────────────────────────────────────
        '<div id="lightbox" role="dialog" aria-modal="true">\n'
        '  <button class="lb-btn" id="lb-close" onclick="closeLightbox()" aria-label="Close">&#x2715;</button>\n'
        '  <button class="lb-btn" id="lb-prev"  onclick="lbStep(-1)" aria-label="Previous">&#8249;</button>\n'
        '  <div id="lb-spinner"></div>\n'
        '  <canvas id="lb-canvas" style="display:none"></canvas>\n'
        '  <canvas id="lb-canvas-display"></canvas>\n'
        '  <img id="lb-image" src="" alt="Photograph by N C Mohan">\n'
        '  <button class="lb-btn" id="lb-next"  onclick="lbStep(1)"  aria-label="Next">&#8250;</button>\n'
        '  <div class="lb-meta">\n'
        '    <div class="lb-counter" id="lb-counter"></div>\n'
        '    <div class="lb-copyright">&copy; N C Mohan &mdash; All rights reserved</div>\n'
        '    <div class="lb-hint">For a clean copy for promotional use, contact ncmohan.photos@gmail.com</div>\n'
        '  </div>\n'
        '</div>\n\n'

        # ── COPYRIGHT BANNER ─────────────────────────────────────────────────
        '<div id="copyright-banner">\n'
        '  &copy; All photographs are the exclusive property of N C Mohan and are protected under copyright law.'
        ' &middot; Reproduction or use without prior written permission is strictly prohibited.\n'
        '</div>\n\n'

        # ── FOOTER ───────────────────────────────────────────────────────────
        '<footer>\n'
        '  <span class="footer-copy">&copy; N C Mohan &middot; All rights reserved</span>\n'
        '</footer>\n\n'

        '<script>' + js + '</script>\n'
        '</body>\n'
        '</html>'
    )

    out_path = os.path.join(ROOT_DIR, "index.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    print("=" * 55)
    print("BUILD COMPLETE")
    print("  Output       : " + out_path)
    print("  Unique photos: " + str(len(unique)))
    print("  Mountains    : " + str(len(tag_map.get('Nature/Mountains', []))) + " photos")
    print("  Hero slides  : " + str(len(hero_slides)) + " (Megamalai, 3s rotation)")
    print("=" * 55)

if __name__ == "__main__":
    generate_html()
