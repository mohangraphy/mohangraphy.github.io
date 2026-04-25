import os
import json
import random
import subprocess
from urllib.parse import quote as _url_quote

# ── CONFIGURATION ─────────────────────────────────────────────────────────────
ROOT_DIR         = "/Users/ncm/Pictures/Mohangraphy"
DATA_FILE        = os.path.join(ROOT_DIR, "Scripts/photo_metadata.json")
CONTENT_FILE     = os.path.join(ROOT_DIR, "Scripts/content.json")  # ← editable content
BLOG_FILE        = os.path.join(ROOT_DIR, "Scripts/blog_posts.json")  # travel stories
THUMBS_DIR       = os.path.join(ROOT_DIR, "Thumbs")
WEB_DIR          = os.path.join(ROOT_DIR, "Web")    # 2048px web-optimised copies
MEGAMALAI_FOLDER = os.path.join(ROOT_DIR, "Photos/Nature/Landscape/Megamalai")
BLOG_PHOTOS_DIR  = os.path.join(ROOT_DIR, "Photos/Blog")   # blog-only photos — not in Collections
THUMB_WIDTH      = 800
WEB_WIDTH        = 2048   # max long-edge for lightbox display

MANUAL_STRUCTURE = {
    "Landscape":       [],
    "Flora & Fauna":   [],
    "Architecture":    [],
    "People & Culture":[],
}
# Display ORDER in Collections menu
CAT_ORDER = ["Landscape", "Flora & Fauna", "Architecture", "People & Culture"]

# ── NEW ARCHITECTURE ──────────────────────────────────────────────────────────
# Each category has India / Overseas filter pills.
# India   → city cards (city + state from metadata)
# Overseas → country cards → city cards (city + country from metadata)
#
# Which old tags map to which new category:
CAT_TAG_MAP = {
    "Landscape": {
        "Nature/Landscapes", "Nature/Landscape", "Nature/Landscape/Mountains",
        "Nature/Mountains", "Nature/Sunsets and Sunrises", "Nature/Sunsets",
        # Common Curator.py variants:
        "Landscape", "Landscapes", "Nature/Landscape/Glacier",
        "Nature/Landscape/Lakes", "Nature/Landscape/Waterfalls",
        "Nature/Landscape/Forests", "Nature/Landscape/Canada",
        "Nature/Landscape/Panorama", "Nature/Panorama",
    },
    "Flora & Fauna": {
        "Nature/Wildlife", "Nature/Birds", "Nature/Flora",
        "Nature/Flowers", "Flowers", "Birds", "Nature/Flowers",
        "Flora & Fauna",    # top-level tag used when all three apply
        # Common variants:
        "Wildlife", "Nature/Animals", "Nature/Wildlife/Canada",
        "Nature/Birds/Canada",
    },
    "Architecture": {
        "Architecture",
    },
    "People & Culture": {
        "People & Culture", "People/Portraits", "People & Culture/Portraits",
        "People & Culture/Street", "People & Culture/Culture",
        "People & Culture/Abstract",   # new sub-tag for future Search
    },
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
            # Diagnostic
            email       = data.get('site',  {}).get('contact_email', '(missing)')
            ga          = data.get('site',  {}).get('ga_measurement_id', '(not set)')
            supa        = data.get('site',  {}).get('supabase_url', '(not set)')
            plaus       = data.get('site',  {}).get('plausible_domain', '(not set)')
            print(f"  ✅ content.json loaded OK")
            print(f"     Contact email    : {email}")
            print(f"     GA measurement ID: {ga}")
            print(f"     Supabase URL     : {supa[:40] if supa != '(not set)' else supa}")
            print(f"     Plausible domain : {plaus}")
            return data
        except Exception as e:
            print("  ❌ ERROR reading content.json: " + str(e))
            print("     Validate at: https://jsonlint.com")
            return {}



def load_blog_posts():
    """Load blog_posts.json — travel stories written by the photographer."""
    if not os.path.exists(BLOG_FILE):
        print("  info: blog_posts.json not found — Travel Stories will be empty.")
        print("        Run blog_editor.py to create your first post.")
        return []
    with open(BLOG_FILE, "r", encoding="utf-8") as f:
        try:
            posts = json.load(f)
            print(f"  OK blog_posts.json loaded — {len(posts)} post(s)")
            return posts
        except Exception as e:
            print("  ERROR reading blog_posts.json: " + str(e))
            return []
def deduplicate_by_path(raw_data):
    """One entry per unique relative path — kills the hash+filename duplicates."""
    seen = {}
    for info in raw_data.values():
        path = info.get('path', '').strip()
        if path and path not in seen:
            seen[path] = info
    return list(seen.values())

def scan_folder_for_photos(folder_path, exclude_blog=True):
    """Scan folder recursively for photos. Skips Photos/Blog/ by default."""
    paths = []
    if not os.path.isdir(folder_path):
        return paths
    blog_abs = os.path.abspath(BLOG_PHOTOS_DIR)
    for root, dirs, files in os.walk(folder_path):
        # Skip the Blog folder entirely
        if exclude_blog and os.path.abspath(root).startswith(blog_abs):
            dirs[:] = []
            continue
        # Also prevent walking INTO Blog if it appears as a subdir
        if exclude_blog:
            dirs[:] = [d for d in dirs if os.path.abspath(os.path.join(root, d)) != blog_abs]
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
        '<img src="' + _url_quote(rel_path,safe="/") + '" '
        'data-full="' + _url_quote(web_rel_path,safe="/") + '" '
        'loading="lazy" decoding="async" '
        'alt="' + alt + '" '
        'style="width:100%;height:100%;object-fit:cover;display:block;">'
    )

# ── BUILD TAG MAP ─────────────────────────────────────────────────────────────
def build_maps(unique_entries):
    """
    Returns:
      cat_city_map : {category: {
                        'India':    {city: {state: [paths]}},
                        'Overseas': {country: {city: [paths]}}
                      }}
      all_paths    : [all unique paths]
      path_info    : {path: {remarks, state, city, country, date_added}}

    Every photo is classified by:
      1. Content category  (Landscape / Flora & Fauna / Architecture / People & Culture)
      2. Location          (India: state+city  OR  Overseas: country+city)

    A photo tagged Places/National AND Nature/Landscapes appears in:
      → Landscape → India → [its city]
    A photo tagged Places/International AND Nature/Birds appears in:
      → Flora & Fauna → Overseas → [its country] → [its city]
    """
    # Build reverse lookup: tag string → category name
    tag_to_cat = {}
    for cat, tags in CAT_TAG_MAP.items():
        for t in tags:
            tag_to_cat[t] = cat

    # cat_city_map[cat]['India'][city][state] = [paths]
    # cat_city_map[cat]['Overseas'][country][city] = [paths]
    cat_city_map = {cat: {'India': {}, 'Overseas': {}} for cat in CAT_ORDER}

    all_paths     = []
    path_info_map = {}

    # Known single-word place→(state, city) mapping for backward compatibility
    # Map province names → country (for overseas photos where country field is blank)
    KNOWN_COUNTRIES = {
        'alberta': 'Canada', 'british columbia': 'Canada', 'ontario': 'Canada',
        'quebec': 'Canada', 'manitoba': 'Canada', 'saskatchewan': 'Canada',
        'nova scotia': 'Canada', 'new brunswick': 'Canada',
        'banff': 'Canada', 'jasper': 'Canada', 'lake louise': 'Canada',
        'yoho': 'Canada', 'vancouver': 'Canada', 'victoria': 'Canada',
        'toronto': 'Canada', 'ottawa': 'Canada', 'montreal': 'Canada',
    }

    KNOWN_STATES = {
        'megamalai':   ('Tamil Nadu', 'Megamalai'),
        'munnar':      ('Kerala',     'Munnar'),
        'badami':      ('Karnataka',  'Badami'),
        'pattadhakal': ('Karnataka',  'Pattadhakal'),
        'hampi':       ('Karnataka',  'Hampi'),
        'coorg':       ('Karnataka',  'Coorg'),
        'ooty':        ('Tamil Nadu', 'Ooty'),
        'kodaikanal':  ('Tamil Nadu', 'Kodaikanal'),
        'thekkady':    ('Kerala',     'Thekkady'),
        'madurai':     ('Tamil Nadu', 'Madurai'),
        'aihole':      ('Karnataka',  'Aihole'),
        'banff':         ('Alberta',          'Banff'),
        'jasper':        ('Alberta',          'Jasper'),
        'jasper np':     ('Alberta',          'Jasper'),
        'jaspernp':      ('Alberta',          'Jasper'),
        'athabasca':     ('Alberta',          'Jasper'),
        'lake louise':   ('Alberta',          'Lake Louise'),
        'yoho':          ('British Columbia', 'Yoho'),
        'vancouver':     ('British Columbia', 'Vancouver'),
        'victoria':      ('British Columbia', 'Victoria'),
        'kelowna':       ('British Columbia', 'Kelowna'),
        'toronto':       ('Ontario',          'Toronto'),
        'ottawa':        ('Ontario',          'Ottawa'),
        'niagara':       ('Ontario',          'Niagara'),
        'montreal':      ('Quebec',           'Montreal'),
        'quebec':        ('Quebec',           'Quebec City'),
        'tadoba':        ('Maharashtra',      'Tadoba'),
    }

    for info in unique_entries:
        path    = info.get('path', '')
        # Skip blog-only photos — they are not part of Collections
        if path.startswith('Photos/Blog/') or path.startswith('Photos\\Blog\\'):
            continue
        tags    = info.get('categories', [])
        place   = info.get('place', '').strip()
        remarks = info.get('remarks', '').strip()
        state   = info.get('state',   '').strip()
        city    = info.get('city',    '').strip()
        country = info.get('country', '').strip()

        # Backward-compat: parse old-style place fields
        if not state and ' - ' in place:
            parts = place.split(' - ', 1)
            state, city = parts[0].strip(), parts[1].strip()
        elif not state and place:
            lookup = KNOWN_STATES.get(place.lower().strip())
            if lookup:
                state, city = lookup
            else:
                city  = place
                state = ''

        if state and not city:
            city = state
        if country and not city and state:
            city = state

        if not path:
            continue
        all_paths.append(path)
        date_added = info.get('date_added', '')
        path_info_map[path] = {
            'remarks':    remarks,
            'state':      state,
            'city':       city,
            'country':    country,
            'date_added': date_added,
        }

        # Determine content category from tags
        content_cats = set()
        is_national     = False
        is_international = False

        for raw_tag in tags:
            cat = tag_to_cat.get(raw_tag)
            if cat:
                content_cats.add(cat)
            if 'Places/National' in raw_tag:
                is_national = True
            if 'Places/International' in raw_tag:
                is_international = True

        # Warn about photos whose tags don't map to any content category
        if tags and not content_cats:
            print(f"  ⚠️  No content category for: {os.path.basename(path)}")
            print(f"     Tags: {tags}")
            print(f"     → Will try path-based fallback")

        # If no content category tag found, try inferring from file path
        if not content_cats:
            path_lower = path.lower().replace('\\', '/')
            if any(k in path_lower for k in ['/landscape', '/landscapes', '/mountain', '/sunset', '/glacier', '/panorama']):
                content_cats.add('Landscape')
            elif any(k in path_lower for k in ['/wildlife', '/birds', '/flora', '/flowers', '/fauna']):
                content_cats.add('Flora & Fauna')
            elif '/architecture' in path_lower:
                content_cats.add('Architecture')
            elif any(k in path_lower for k in ['/people', '/portrait', '/street', '/culture']):
                content_cats.add('People & Culture')
            if not content_cats:
                continue  # still nothing — skip

        # Determine location bucket
        # Auto-detect international: if city/state resolves to a known country,
        # treat as international even if Places/International tag was not set.
        if not is_international and not is_national:
            auto_country = KNOWN_COUNTRIES.get((city or state).lower().strip(), '')
            if auto_country:
                is_international = True
                country = auto_country

        if is_international:
            # Resolve country: use explicit field, or look up from KNOWN_COUNTRIES
            resolved_country = country
            if not resolved_country and city:
                resolved_country = KNOWN_COUNTRIES.get(city.lower().strip(), '')
            if not resolved_country and state:
                resolved_country = KNOWN_COUNTRIES.get(state.lower().strip(), '')
            if not resolved_country:
                resolved_country = state  # last resort fallback
            intl_country = resolved_country
            intl_city    = city if city else state
            if intl_country and intl_city:
                for cat in content_cats:
                    m = cat_city_map[cat]['Overseas']
                    m.setdefault(intl_country, {})
                    m[intl_country].setdefault(intl_city, [])
                    if path not in m[intl_country][intl_city]:
                        m[intl_country][intl_city].append(path)

        elif is_national:
            if city:
                for cat in content_cats:
                    m = cat_city_map[cat]['India']
                    m.setdefault(city, {})
                    m[city].setdefault(state, [])
                    if path not in m[city][state]:
                        m[city][state].append(path)

        else:
            # No Places tag — put under India using whatever location we have
            if city or state:
                effective_city = city or state
                for cat in content_cats:
                    m = cat_city_map[cat]['India']
                    m.setdefault(effective_city, {})
                    m[effective_city].setdefault(state, [])
                    if path not in m[effective_city][state]:
                        m[effective_city][state].append(path)

    # ── DIAGNOSTIC: print Canada/overseas photo summary ──────────────────────
    overseas_total = 0
    for cat in cat_city_map:
        for country, cities in cat_city_map[cat]['Overseas'].items():
            for city2, paths2 in cities.items():
                overseas_total += len(paths2)
                if country == 'Canada':
                    print(f"  📷 {cat}/Canada/{city2}: {len(paths2)} photo(s)")
    if overseas_total == 0:
        print("  ⚠️  WARNING: No overseas photos found. Check that your Canada photos have:")
        print("     1. A content tag: Nature/Landscapes, Nature/Landscape, Nature/Wildlife, etc.")
        print("     2. Either Places/International tag OR place/city matching a known Canadian city")
    # ── END DIAGNOSTIC ────────────────────────────────────────────────────────

    return cat_city_map, all_paths, path_info_map


# ── THUMBNAIL BATCH ───────────────────────────────────────────────────────────
def ensure_thumbs(all_paths, blog_paths=None):
    """Pre-generate thumbnails AND 2048px web copies for all photos.
    blog_paths are processed for thumbs but NOT added to Collections.
    """
    combined = list(all_paths) + (blog_paths or [])
    total = len(combined)
    print(f"  Generating thumbnails + 2048px web copies ({total} photos)...")
    print(f"  First run takes a few minutes. Subsequent runs are instant (skips existing).")
    thumb_map = {}
    web_map   = {}
    for i, p in enumerate(combined):
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
    info       = path_info.get(orig_path, {})
    remarks    = info.get('remarks',    '').strip()
    place      = info.get('place',      '').strip()
    state      = info.get('state',      '').strip()
    city       = info.get('city',       '').strip()
    date_added = info.get('date_added', '').strip()

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
        ' data-photo="'      + qa(orig_path)  + '"'
        ' data-state="'      + qa(state)      + '"'
        ' data-city="'       + qa(city)       + '"'
        ' data-remarks="'    + qa(remarks)    + '"'
        ' data-cats="'       + qa(','.join(cats)) + '"'
        ' data-date-added="' + qa(date_added) + '"'
        ' onclick="openImgModal(this)">'
        '<div class="grid-item-photo">'
        + thumb_img(thumb_path, web_path, alt)
        + '<div class="grid-item-overlay"></div>'
        + overlay
        + '</div>'
        '</div>'
    )

def generate_html():

    # Load photo data
    raw_data = load_index()
    unique   = deduplicate_by_path(raw_data)
    cat_city_map, all_paths, path_info = build_maps(unique)

    # Build path→full metadata dict for embedding into grid items
    meta_by_path = {e.get('path','').strip(): e for e in unique if e.get('path','').strip()}
    # Load travel-story blog posts
    blog_posts = load_blog_posts()

    # About Me photo — copy Scripts/about_photo.jpg to root if it exists
    about_photo_src = os.path.join(ROOT_DIR, "Scripts", "about_photo.jpg")
    about_photo_dst = os.path.join(ROOT_DIR, "about_photo.jpg")
    has_about_photo = False
    if os.path.exists(about_photo_src):
        import shutil as _shutil
        _shutil.copy2(about_photo_src, about_photo_dst)
        has_about_photo = True
        print(f"  📷 About Me photo found and copied")
    elif os.path.exists(about_photo_dst):
        has_about_photo = True

    print(f"Unique photos: {len(unique)}")

    # Load editable content
    C = load_content()
    site       = C.get('site',       {})
    c_about    = C.get('about',      {})
    c_phil     = C.get('philosophy', {})
    c_gear     = C.get('gear',       {})
    c_contact  = C.get('contact',    {})
    c_prints   = C.get('prints',     {})
    c_licens   = C.get('licensing',  {})
    c_legal    = C.get('legal',      {})

    # Site-wide values with safe fallbacks
    contact_email    = site.get('contact_email',    'info@mohangraphy.com')
    photographer     = site.get('photographer_name','N C Mohan')
    site_description = site.get('description',      'Fine art photography by N C Mohan. Landscapes, architecture, wildlife, and more.')
    supabase_url     = site.get('supabase_url',     'https://xjcpryfgodgqqtbblklg.supabase.co')
    supabase_key     = site.get('supabase_anon_key','eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhqY3ByeWZnb2RncXF0YmJsa2xnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzIxODEzMjcsImV4cCI6MjA4Nzc1NzMyN30.M9KoprG4uaH3wcZ7nI0Hip4IAdqiy8m5UoiB9DzjreI')
    admin_password   = site.get('admin_password',   'mohan2024')
    plausible_domain = site.get('plausible_domain', 'www.mohangraphy.com')
    ga_id            = site.get('ga_measurement_id','')

    # Generate / verify thumbnails + 2048px web copies
    # Blog photos are processed for thumbs but never appear in Collections
    blog_only_paths = scan_folder_for_photos(BLOG_PHOTOS_DIR, exclude_blog=False)
    print(f"  📁 Blog folder: {BLOG_PHOTOS_DIR}")
    if blog_only_paths:
        print(f"  📝 Blog-only photos found: {len(blog_only_paths)}")
        for bp in blog_only_paths:
            print(f"     {os.path.basename(bp)}")
    else:
        print(f"  ⚠️  No blog photos found — folder may be empty or missing")
    thumb_map, web_map = ensure_thumbs(all_paths, blog_only_paths)

    # Hero slides — Megamalai landscape only, 3-second rotation
    megamalai_paths = scan_folder_for_photos(MEGAMALAI_FOLDER)
    if not megamalai_paths:
        megamalai_paths = all_paths[:20]
    hero_slides = random.sample(megamalai_paths, min(len(megamalai_paths), 15))
    hero_thumb_paths = [thumb_map.get(p, p) for p in hero_slides]

    # Cover photo per main category — pick first available photo from India or Overseas
    cat_covers = {}
    for m_cat in CAT_ORDER:
        pool = []
        for region in ['India', 'Overseas']:
            region_data = cat_city_map.get(m_cat, {}).get(region, {})
            for top in region_data.values():
                if isinstance(top, dict):
                    for paths in top.values():
                        pool.extend(paths)
                elif isinstance(top, list):
                    pool.extend(top)
        raw = pick_cover(pool)
        cat_covers[m_cat] = thumb_map.get(raw, raw)

    # ── CSS ───────────────────────────────────────────────────────────────────
    css = """
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;0,700;1,400&family=Montserrat:wght@300;400;600;700;900&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

/* ── Global image protection ──
   -webkit-touch-callout: none  suppresses iOS Safari's native "Save Image" callout on long-press.
   This is the ONLY way to block it on iOS — JS touchstart handlers cannot prevent it.
   user-select / user-drag block selection and drag-to-desktop on all platforms. */
img {
  -webkit-touch-callout: none;
  -webkit-user-select: none;
  user-select: none;
  -webkit-user-drag: none;
}

:root {
  --gold:  #c9a96e;
  --gold2: #e8d4a0;
  --dark:  #080808;
  --mid:   #161616;
  --hdr:   80px;
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
   HEADER — Logo left | Tabs center | CTA right
   Mobile: Logo center | Hamburger right
   ══════════════════════════════════════════════════════════════ */
header {
  position: fixed; top: 0; left: 0; right: 0;
  height: var(--hdr);
  background: rgba(8,8,8,0.97);
  backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(201,169,110,0.15);
  z-index: 2000;
  display: grid;
  grid-template-columns: auto 1fr auto auto;
  align-items: center;
  padding: 0 clamp(16px,3vw,40px);
  gap: 0;
}

/* Logo */
.site-logo {
  font-family: 'Cormorant Garamond', serif;
  font-weight: 300;
  font-size: 30px;
  letter-spacing: 6px;
  color: rgba(255,255,255,0.9);
  text-transform: uppercase;
  cursor: pointer; user-select: none;
  white-space: nowrap;
  transition: color .25s;
  line-height: 1;
}
.site-logo:hover { color: var(--gold); }

/* Center nav tabs */
.hdr-tabs {
  display: flex; align-items: center; justify-content: center;
  gap: 0;
}
.hdr-tab {
  position: relative;
  font-family: 'Montserrat', sans-serif;
  font-size: 10px; font-weight: 600; letter-spacing: 3px;
  text-transform: uppercase;
  color: rgba(255,255,255,0.55);
  cursor: pointer; background: none; border: none;
  padding: 0 14px; height: var(--hdr);
  display: flex; align-items: center; gap: 5px;
  transition: color .2s;
  white-space: nowrap;
}
.hdr-tab:hover { color: rgba(255,255,255,0.9); }
.hdr-tab.active { color: #fff; }
.hdr-tab.active::after {
  content: '';
  position: absolute; bottom: 0; left: 14px; right: 14px;
  height: 2px; background: var(--gold);
}
/* Collections dropdown chevron */
.hdr-tab-chevron {
  font-size: 8px; color: rgba(201,169,110,0.6);
  transition: transform .2s;
}
.hdr-tab:hover .hdr-tab-chevron,
.hdr-tab.dd-open .hdr-tab-chevron { transform: rotate(180deg); }

/* Collections dropdown — triggered by JS, not CSS hover, to avoid invalid nesting */
.hdr-dropdown {
  position: absolute; top: var(--hdr); left: 50%;
  transform: translateX(-50%);
  background: rgba(10,10,10,0.98);
  border: 1px solid rgba(201,169,110,0.18);
  border-top: 2px solid var(--gold);
  min-width: 180px;
  opacity: 0; visibility: hidden; pointer-events: none;
  transition: opacity .2s, visibility .2s;
  z-index: 2001;
}
.hdr-tab.dd-open .hdr-dropdown {
  opacity: 1; visibility: visible; pointer-events: all;
}
.hdr-dd-item {
  display: block; padding: 13px 20px;
  font-family: 'Montserrat', sans-serif;
  font-size: 9px; font-weight: 600; letter-spacing: 3px; text-transform: uppercase;
  color: rgba(255,255,255,0.6);
  cursor: pointer; border: none; background: none;
  width: 100%; text-align: left;
  transition: color .15s, background .15s;
  border-bottom: 1px solid rgba(255,255,255,0.04);
}
.hdr-dd-item:hover { color: var(--gold); background: rgba(201,169,110,0.06); }

/* CTA button */
.hdr-cta {
  font-family: 'Montserrat', sans-serif;
  font-size: 9px; font-weight: 600; letter-spacing: 3px;
  text-transform: uppercase;
  color: var(--gold); border: 1px solid rgba(201,169,110,0.5);
  background: none; cursor: pointer;
  padding: 0 18px; height: 36px;
  display: flex; align-items: center;
  transition: background .2s, color .2s, border-color .2s;
  white-space: nowrap;
}
.hdr-cta:hover { background: var(--gold); color: #000; border-color: var(--gold); }

/* Hamburger — mobile only */
.hdr-hamburger {
  display: none;
  width: 40px; height: 40px;
  background: none; border: none; cursor: pointer;
  color: rgba(255,255,255,0.6);
  align-items: center; justify-content: center;
  flex-direction: column; gap: 5px;
  transition: color .2s;
}
.hdr-hamburger:hover { color: var(--gold); }
.hdr-hamburger span {
  display: block; width: 22px; height: 1px;
  background: currentColor; transition: transform .25s, opacity .25s;
}

/* Tablet + mobile — hamburger at ≤1024px (portrait iPad and below) */
@media (max-width: 1024px) {
  header {
    grid-template-columns: 1fr auto;
    padding: 0 16px;
  }
  .hdr-tabs { display: none !important; }
  .hdr-cta  { display: none !important; }
  .hdr-hamburger { display: flex; grid-column: 2; }
}
@media (max-width: 767px) {
  .site-logo {
    font-size: 22px;
    letter-spacing: 4px;
    text-align: left;
    grid-column: 1;
  }
}

/* ══════════════════════════════════════════════════════════════
   MOBILE MENU DRAWER
   ══════════════════════════════════════════════════════════════ */
#mobile-menu {
  display: none; position: fixed; inset: 0; z-index: 9500;
  background: rgba(0,0,0,0.95);
  flex-direction: column;
  padding: var(--hdr) 0 0;
}
#mobile-menu.open { display: flex; }
.mob-menu-close {
  position: absolute; top: 12px; right: 14px;
  background: none; border: none; cursor: pointer;
  color: rgba(255,255,255,0.4); font-size: 22px;
  width: 40px; height: 40px;
  display: flex; align-items: center; justify-content: center;
  transition: color .2s;
}
.mob-menu-close:hover { color: var(--gold); }
.mob-menu-item {
  padding: 18px 32px;
  font-family: 'Montserrat', sans-serif;
  font-size: 11px; letter-spacing: 4px; text-transform: uppercase;
  color: rgba(255,255,255,0.7); cursor: pointer;
  border-bottom: 1px solid rgba(255,255,255,0.05);
  transition: color .15s;
  background: none; border-left: none; border-right: none; border-top: none;
  text-align: left; width: 100%;
}
.mob-menu-item:hover { color: var(--gold); }
.mob-menu-item.mob-menu-active { color: #fff; }
.mob-menu-sub {
  display: none; background: rgba(0,0,0,0.4);
}
.mob-menu-sub.open { display: block; }
.mob-menu-subitem {
  padding: 14px 32px 14px 48px;
  font-family: 'Montserrat', sans-serif;
  font-size: 10px; letter-spacing: 3px; text-transform: uppercase;
  color: rgba(255,255,255,0.45); cursor: pointer;
  border-bottom: 1px solid rgba(255,255,255,0.03);
  transition: color .15s;
  background: none; border-left: none; border-right: none; border-top: none;
  text-align: left; width: 100%;
}
.mob-menu-subitem:hover { color: var(--gold); }
.mob-menu-cta {
  margin: 24px 32px 0;
  padding: 14px 24px; text-align: center;
  font-family: 'Montserrat', sans-serif;
  font-size: 9px; letter-spacing: 4px; text-transform: uppercase;
  color: var(--gold); border: 1px solid rgba(201,169,110,0.5);
  background: none; cursor: pointer;
  transition: background .2s, color .2s;
}
.mob-menu-cta:hover { background: var(--gold); color: #000; }

/* ══════════════════════════════════════════════════════════════
   PAGE LAYOUT — everything scrolls, no fixed footer
   ══════════════════════════════════════════════════════════════ */
/* Overlay — only needed for old drawer, now just for modal backdrops */
.drawer-overlay { display: none !important; }

/* Hide old drawer elements if any remain */
#nav-drawer, #about-drawer { display: none !important; }

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
  user-select: none; -webkit-user-select: none;
}
.info-page-body p { margin-bottom: 20px; }
.info-page-body strong { color: var(--gold); font-weight: 600; }

/* About Me — photo + text side by side */
.about-layout {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: clamp(32px, 5vw, 64px);
  align-items: start;
  margin-bottom: 32px;
}
.about-photo-wrap {
  position: sticky; top: calc(var(--hdr) + 32px);
}
.about-photo-wrap img {
  width: 100%; display: block;
  border: 1px solid rgba(201,169,110,0.15);
  filter: grayscale(15%);
  transition: filter .4s;
}
.about-photo-wrap img:hover { filter: grayscale(0%); }
.about-photo-caption {
  font-family: 'Montserrat', sans-serif;
  font-size: 8px; letter-spacing: 3px; text-transform: uppercase;
  color: rgba(255,255,255,0.25); margin-top: 10px; text-align: center;
}
@media (max-width: 640px) {
  .about-layout {
    grid-template-columns: 1fr;
  }
  .about-photo-wrap {
    position: static;
    max-width: 260px; margin: 0 auto 8px;
  }
}

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
  color: var(--gold); padding: 0 32px; height: 44px;
  font-family: 'Montserrat', sans-serif;
  font-size: 9px; letter-spacing: 4px; text-transform: uppercase;
  cursor: pointer; transition: background .25s, color .25s;
  display: inline-flex; align-items: center; justify-content: center;
  margin-top: 0;
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
  background: linear-gradient(160deg, #0a0a0a 0%, #111820 50%, #0a0a0a 100%);
  display: none;
  align-items: center;
  justify-content: center;
  padding-top: var(--hdr);
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
  position: absolute; bottom: 15vh; left: 50%;
  transform: translateX(-50%);
  display: flex; flex-direction: column; align-items: center; gap: 6px;
  animation: cue 2.2s ease-in-out infinite; z-index: 2;
  background: none; border: none; cursor: pointer;
  padding: 8px 12px;
}
.scroll-cue span {
  font-family: 'Montserrat', sans-serif;
  font-size: 9px; letter-spacing: 5px; font-weight: 600;
  color: rgba(255,255,255,0.65); text-transform: uppercase;
}
.scroll-cue svg path { stroke: rgba(255,255,255,0.65) !important; }
@keyframes cue {
  0%,100% { transform: translateX(-50%) translateY(0); opacity:.6; }
  50%      { transform: translateX(-50%) translateY(9px); opacity:1; }
}

/* ── MAIN VERTICAL TILE NAV ── */
#tile-nav {
  display: none;
  padding-top: var(--hdr);
  background: var(--dark);
  min-height: 100svh;
}
#tile-nav.visible { display: block; }

.tile-nav-label {
  font-size: 9px; letter-spacing: 6px;
  color: var(--gold); text-transform: uppercase;
  opacity: .7; text-align: center;
  padding: 24px 0 4px;
}

/* ── 4-column card grid for sub-categories (Level 2+) ── */
.cat-grid-4 {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: clamp(8px, 1.5vw, 16px);
  padding: clamp(14px, 2.5vw, 28px) clamp(14px, 4vw, 44px);
}
@media (max-width: 900px) {
  .cat-grid-4 { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 480px) {
  .cat-grid-4 { grid-template-columns: 1fr; }
}

/* ── Places filter pills ── */
.places-filters {
  display: flex; gap: 8px;
  padding: clamp(16px,3vw,32px) clamp(14px,4vw,44px) 0;
  flex-wrap: wrap;
}
.places-pill {
  padding: 7px 20px;
  font-family: 'Montserrat', sans-serif;
  font-size: 10px; font-weight: 600; letter-spacing: 3px;
  text-transform: uppercase;
  color: rgba(255,255,255,0.5);
  border: 1px solid rgba(255,255,255,0.15);
  background: none; cursor: pointer; border-radius: 20px;
  transition: all .2s;
}
.places-pill.active, .places-pill:hover {
  color: var(--gold); border-color: rgba(201,169,110,0.6);
  background: rgba(201,169,110,0.07);
}

/* Places: state cards expand inline to show cities */
.places-state-wrap { position: relative; }
.places-state-cities {
  display: none;
  grid-column: 1 / -1;   /* span full row */
  padding: 16px 0 8px;
  animation: pEnter .25s ease;
}
.places-state-cities.open { display: block; }
.cat-card.state-expanded::after { border-color: var(--gold) !important; }
.cat-card.state-expanded .cat-card-bar {
  background: linear-gradient(to top, rgba(20,14,0,0.92) 0%, transparent 100%);
}

/* ── Minimum font-size 14px on desktop ── */
@media (min-width: 1025px) {
  .cat-card-count, .gal-sub, .bc-sep, #visit-count {
  opacity: 0.6;
  font-size: inherit;
  letter-spacing: inherit;
}

.footer-copy { font-size: 14px !important; }
  .hdr-tab { font-size: 11px; }
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
@media (max-width: 480px) {
  .cat-grid { grid-template-columns: 1fr; }
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
  border-bottom: 1px solid rgba(201,169,110,0.08);
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
  background: #1a1a1a;
}
.grid {
  display: grid;
  gap: 3px; padding: 3px;
  background: #2a2a2a;
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
  background: #111;
  cursor: pointer;
  max-width: 100vw;
  overflow: hidden;
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
  padding: 24px 8px 6px;
  background: linear-gradient(to top, rgba(0,0,0,0.82) 0%, transparent 100%);
  opacity: 0;
  transition: opacity .35s;
  pointer-events: none;
}
.grid-item:hover .grid-item-info { opacity: 1; }
.grid-item-info-text {
  font-size: 9px; letter-spacing: 1.2px;
  color: rgba(255,255,255,0.92);
  font-family: 'Montserrat', sans-serif;
  white-space: normal;
  word-wrap: break-word;
  line-height: 1.6;
  display: block;
}

/* ── ACTION BAR — removed, now in image modal ── */
.grid-item-bar { display: none !important; }

/* Like badge (legacy — hidden) */
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
/* Edit Tags — always visible; prompts for password if not unlocked */
#ctx-admin-item { display: flex; }
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

/* ── NOTIFICATION PANEL ── */
#notify-panel {
  display: none; position: fixed; inset: 0; z-index: 9400;
  background: rgba(0,0,0,0.88);
  align-items: center; justify-content: center;
  padding: 20px;
}
#notify-panel.open { display: flex; }
#notify-box {
  background: #0e0e0e; border: 1px solid rgba(201,169,110,0.2);
  width: min(520px,96vw); padding: 32px 28px;
  font-family: Montserrat,sans-serif; position: relative;
}
.notify-title {
  font-family: "Cormorant Garamond",serif;
  font-size: 20px; letter-spacing: 5px; text-transform: uppercase;
  color: var(--gold); margin-bottom: 6px;
}
.notify-sub {
  font-size: 8px; letter-spacing: 3px; text-transform: uppercase;
  color: rgba(255,255,255,0.25); margin-bottom: 24px;
}
.notify-select {
  width: 100%; background: #111;
  border: 1px solid rgba(201,169,110,0.2);
  color: #fff; padding: 10px 12px;
  font-family: Montserrat,sans-serif; font-size: 11px;
  outline: none; margin-bottom: 16px; -webkit-appearance: none;
}
.notify-select:focus { border-color: var(--gold); }
.notify-btn-row { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 16px; }
.notify-btn {
  background: none; border: 1px solid rgba(201,169,110,0.5);
  color: var(--gold); padding: 0 18px; height: 38px;
  font-family: Montserrat,sans-serif; font-size: 9px;
  letter-spacing: 3px; text-transform: uppercase;
  cursor: pointer; transition: background .2s, color .2s;
  white-space: nowrap;
}
.notify-btn:hover:not(:disabled) { background: var(--gold); color: #000; }
.notify-btn:disabled { opacity: 0.35; cursor: not-allowed; }
.notify-btn-ghost {
  background: none; border: 1px solid rgba(255,255,255,0.15);
  color: rgba(255,255,255,0.5); padding: 0 18px; height: 38px;
  font-family: Montserrat,sans-serif; font-size: 9px;
  letter-spacing: 3px; text-transform: uppercase; cursor: pointer;
}
.notify-status {
  display: none; padding: 10px 12px; font-size: 10px;
  letter-spacing: 1px; line-height: 1.7; white-space: pre-line;
  border-left: 2px solid rgba(201,169,110,0.3);
  color: rgba(255,255,255,0.6); background: rgba(0,0,0,0.4);
  margin-top: 4px;
}
.notify-status.visible { display: block; }
.notify-status.ok  { border-left-color: #4caf50; }
.notify-status.err { border-left-color: #e04060; }
.notify-close {
  position: absolute; top: 12px; right: 14px;
  background: none; border: none; cursor: pointer;
  color: rgba(255,255,255,0.3); font-size: 20px;
}
.notify-close:hover { color: var(--gold); }

/* ── SLIDESHOW BUTTON ── */
.slideshow-btn {
  display: inline-flex; align-items: center; gap: 8px;
  background: none; border: 1px solid rgba(201,169,110,0.5);
  color: var(--gold); cursor: pointer;
  padding: 0 18px; height: 34px;
  font-family: 'Montserrat', sans-serif;
  font-size: 9px; font-weight: 600; letter-spacing: 3px; text-transform: uppercase;
  transition: background .2s, border-color .2s;
  white-space: nowrap; flex-shrink: 0;
}
.slideshow-btn:hover { background: rgba(201,169,110,0.1); border-color: var(--gold); }

/* ── FULLSCREEN SLIDESHOW OVERLAY ── */
#ss-overlay {
  display: none; position: fixed; inset: 0; z-index: 9800;
  background: #000; flex-direction: column;
}
#ss-overlay.open { display: flex; }
#ss-img-wrap {
  flex: 1 1 0; position: relative; overflow: hidden;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer;
}
#ss-img {
  max-width: 100%; max-height: 100%;
  object-fit: contain; display: block;
  user-select: none; -webkit-user-drag: none;
  opacity: 1; transition: opacity 0.5s ease;
}
#ss-img.ss-fade { opacity: 0; }
#ss-bar {
  flex-shrink: 0; height: 52px;
  background: rgba(0,0,0,0.85);
  border-top: 1px solid rgba(201,169,110,0.12);
  display: flex; align-items: center;
  padding: 0 16px; gap: 14px;
}
#ss-counter {
  font-family: 'Montserrat', sans-serif;
  font-size: 9px; letter-spacing: 3px; color: rgba(255,255,255,0.35);
  text-transform: uppercase; white-space: nowrap;
}
#ss-caption {
  flex: 1; text-align: center;
  font-family: 'Montserrat', sans-serif;
  font-size: 11px; letter-spacing: 1px; color: rgba(255,255,255,0.65);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
#ss-hint {
  font-family: 'Montserrat', sans-serif;
  font-size: 8px; letter-spacing: 2px; color: rgba(255,255,255,0.25);
  text-transform: uppercase; white-space: nowrap;
}
#ss-progress {
  position: absolute; bottom: 0; left: 0; height: 2px;
  background: var(--gold); width: 0%;
  transition: width linear;
}
.ss-nav-btn {
  position: absolute; top: 50%; transform: translateY(-50%);
  background: rgba(0,0,0,0.35); border: none; cursor: pointer;
  color: rgba(255,255,255,0.5); font-size: 28px;
  width: 52px; height: 52px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  transition: color .2s, background .2s; z-index: 1;
}
.ss-nav-btn:hover { color: var(--gold); background: rgba(0,0,0,0.6); }
#ss-prev { left: 10px; }
#ss-next { right: 10px; }
#ss-close {
  position: absolute; top: 12px; right: 14px; z-index: 9801;
  background: rgba(0,0,0,0.5); border: 1px solid rgba(255,255,255,0.15);
  cursor: pointer; color: rgba(255,255,255,0.6); font-size: 18px;
  width: 38px; height: 38px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  transition: color .2s, border-color .2s;
}
#ss-close:hover { color: var(--gold); border-color: var(--gold); }
#ss-pause-lbl {
  position: absolute; top: 14px; left: 50%; transform: translateX(-50%);
  font-family: 'Montserrat', sans-serif; font-size: 8px; letter-spacing: 3px;
  text-transform: uppercase; color: rgba(255,255,255,0.4);
  background: rgba(0,0,0,0.55); padding: 4px 14px;
  pointer-events: none; opacity: 0; transition: opacity .3s;
}
#ss-overlay.ss-paused #ss-pause-lbl { opacity: 1; }

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

/* ── COPYRIGHT BANNER — now inline, not fixed ── */
#copyright-banner {
  display: none;
  background: rgba(8,8,8,0.95);
  border-top: 1px solid rgba(201,169,110,0.1);
  padding: 10px 12px; text-align: center;
  font-size: 8px; letter-spacing: 2px;
  color: rgba(201,169,110,0.6); text-transform: uppercase; line-height: 1.8;
}
#copyright-banner.visible { display: block; }

/* ── FOOTER — scrollable, not fixed ── */

/* ── PLACES FILTER PILLS ── */
.places-filters {
  display: flex; gap: 8px; flex-wrap: wrap;
  padding: clamp(14px,2.5vw,28px) clamp(14px,4vw,44px) 0;
}
.places-pill {
  padding: 7px 20px;
  font-family: 'Montserrat', sans-serif;
  font-size: 9px; font-weight: 600; letter-spacing: 3px;
  text-transform: uppercase;
  color: rgba(255,255,255,0.5);
  border: 1px solid rgba(255,255,255,0.15);
  background: none; cursor: pointer; border-radius: 20px;
  transition: all .2s;
}
.places-pill.active,
.places-pill:hover {
  color: var(--gold); border-color: rgba(201,169,110,0.6);
  background: rgba(201,169,110,0.07);
}

/* ── 4-column grid for level 2+ (sub-categories, states, cities) ── */
.cat-grid-4 {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: clamp(8px, 1.5vw, 16px);
  padding: clamp(14px, 2.5vw, 28px) clamp(14px, 4vw, 44px);
}
@media (max-width: 900px) {
  .cat-grid-4 { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 480px) {
  .cat-grid-4 { grid-template-columns: 1fr; }
}

/* Expand-in-place state section inside Places */
.places-state-group {
  margin-bottom: 2px;
}
.places-state-header {
  /* Each state shows as a card, clicking expands cities below */
}
.places-state-cities {
  display: none;
  padding: 12px clamp(14px,4vw,44px) 20px;
  background: rgba(0,0,0,0.3);
  border-bottom: 1px solid rgba(201,169,110,0.07);
}
.places-state-cities.open { display: block; }
.places-state-cities .cat-grid-4 { padding: 0; }

/* State card with "expanded" indicator */
.cat-card.state-card.expanded {
  border-bottom: 2px solid var(--gold);
}
.cat-card.state-card.expanded .cat-card-bar {
  background: linear-gradient(to top, rgba(20,14,0,0.92) 0%, transparent 100%);
}

/* ══════════════════════════════════════════════════════
   IMAGE DETAIL MODAL — replaces lightbox for photo click
   ══════════════════════════════════════════════════════ */
#img-modal {
  display: none; position: fixed; inset: 0; z-index: 9000;
  background: rgba(0,0,0,0.96);
  align-items: stretch; justify-content: center;
}
#img-modal.open { display: flex; }

/* Left: image */
.img-modal-photo {
  flex: 1 1 0; min-width: 0;
  display: flex; align-items: center; justify-content: center;
  padding: clamp(40px,5vh,80px) clamp(12px,3vw,40px);
  position: relative;
}
#img-modal-img {
  max-width: 100%; max-height: 100%;
  object-fit: contain; display: block;
  user-select: none; -webkit-user-drag: none;
}

/* Prev/next arrows */
.img-modal-nav {
  position: absolute; top: 50%; transform: translateY(-50%);
  background: rgba(0,0,0,0.4); border: none; cursor: pointer;
  color: rgba(255,255,255,0.5); font-size: 24px;
  width: 44px; height: 44px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  transition: color .2s, background .2s; z-index: 1;
}
.img-modal-nav:hover { color: var(--gold); background: rgba(0,0,0,0.7); }
#img-modal-prev { left: 8px; }
#img-modal-next { right: 8px; }

/* Right panel: actions */
.img-modal-panel {
  width: clamp(220px, 28vw, 320px); flex-shrink: 0;
  background: #0e0e0e;
  border-left: 1px solid rgba(201,169,110,0.12);
  display: flex; flex-direction: column;
  padding: 0; position: relative;
  overflow-y: auto;
}
.img-modal-close {
  position: absolute; top: 12px; right: 14px;
  background: rgba(0,0,0,0.5); border: 1px solid rgba(255,255,255,0.12);
  cursor: pointer; color: rgba(255,255,255,0.6); font-size: 18px;
  width: 34px; height: 34px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  transition: color .2s, border-color .2s; z-index: 10;
}
.img-modal-close:hover { color: var(--gold); border-color: var(--gold); }
.img-modal-info {
  padding: 16px 24px 24px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}
.img-modal-counter {
  font-size: 9px; letter-spacing: 3px; color: rgba(255,255,255,0.7);
  text-transform: uppercase; margin-bottom: 8px; font-weight: 600;
}
.img-modal-title {
  font-family: 'Montserrat', sans-serif;
  font-size: 13px; letter-spacing: 1.5px; color: #fff;
  text-transform: uppercase; line-height: 1.5; font-weight: 500;
}
.img-modal-subtitle {
  font-size: 9px; letter-spacing: 2px; color: var(--gold);
  text-transform: uppercase; margin-top: 4px; opacity: .7;
}
.img-modal-actions {
  padding: 24px;
  display: flex; flex-direction: column; gap: 12px;
}
.img-modal-like {
  display: flex; align-items: center; gap: 10px;
  background: none; border: 1px solid rgba(255,255,255,0.12);
  color: rgba(255,255,255,0.55); cursor: pointer;
  padding: 11px 16px; font-family: 'Montserrat', sans-serif;
  font-size: 9px; letter-spacing: 3px; text-transform: uppercase;
  transition: all .2s;
}
.img-modal-like:hover { border-color: var(--gold); color: var(--gold); }
.img-modal-like.liked { border-color: var(--gold); color: var(--gold); background: rgba(201,169,110,0.1); }
.img-modal-like .like-heart { font-size: 14px; }
.like-count {
  font-size: 11px; font-weight: 600; letter-spacing: 0;
  margin-left: 4px; opacity: 0.85;
}
.img-modal-rq {
  background: none; border: 1px solid rgba(201,169,110,0.5);
  color: var(--gold); cursor: pointer;
  padding: 12px 16px; font-family: 'Montserrat', sans-serif;
  font-size: 9px; letter-spacing: 3px; text-transform: uppercase;
  transition: background .2s, color .2s;
}
.img-modal-rq:hover { background: var(--gold); color: #000; }

.img-modal-copyright {
  margin-top: auto; padding: 20px 24px;
  font-size: 7px; letter-spacing: 2px;
  color: rgba(255,255,255,0.2); text-transform: uppercase; line-height: 1.8;
}

/* Loading spinner inside modal */
#img-modal-spinner {
  display: none; position: absolute;
  width: 32px; height: 32px;
  border: 2px solid rgba(201,169,110,0.15);
  border-top-color: rgba(201,169,110,0.7);
  border-radius: 50%;
  animation: lb-spin 0.7s linear infinite;
  pointer-events: none;
}
#img-modal.loading #img-modal-spinner { display: block; }

/* Mobile: stack vertically */
@media (max-width: 640px) {
  #img-modal { flex-direction: column; }
  .img-modal-photo { flex: 1 1 0; padding: 56px 8px 8px; }
  .img-modal-panel {
    width: 100%; flex-shrink: 0; max-height: 45vh;
    border-left: none; border-top: 1px solid rgba(201,169,110,0.12);
  }
  .img-modal-actions { flex-direction: row; padding: 16px; }
  .img-modal-like, .img-modal-rq { flex: 1; justify-content: center; }
  .img-modal-copyright { display: none; }
  /* Force gold on mobile — override any OS default button colour */
  .img-modal-like { color: rgba(255,255,255,0.55) !important; border-color: rgba(255,255,255,0.2) !important; }
  .img-modal-like:hover, .img-modal-like.liked { color: var(--gold) !important; border-color: var(--gold) !important; }
  .like-heart { color: inherit !important; }
}

/* ══════════════════════════════════════════════════════
   REQUEST QUOTE — full page (not modal overlay)
   ══════════════════════════════════════════════════════ */
#rq-modal {
  display: none; position: fixed; inset: 0; z-index: 9100;
  background: #080808;
  overflow-y: auto;
  padding-top: 0;
}
#rq-modal.open { display: block; }
#rq-box {
  max-width: 600px; margin: 0 auto;
  padding: clamp(60px,10vh,100px) clamp(24px,5vw,48px) 80px;
  min-height: 100vh;
}
.rq-back {
  display: inline-flex; align-items: center; gap: 8px;
  background: none; border: none; cursor: pointer;
  font-family: 'Montserrat', sans-serif;
  font-size: 9px; letter-spacing: 3px; text-transform: uppercase;
  color: rgba(255,255,255,0.4); margin-bottom: 40px;
  padding: 0; transition: color .2s;
}
.rq-back:hover { color: var(--gold); }
.rq-title {
  font-family: 'Cormorant Garamond', serif;
  font-size: clamp(28px,5vw,44px); letter-spacing: 6px; text-transform: uppercase;
  color: #fff; margin-bottom: 6px; font-weight: 300; line-height: 1.1;
}
.rq-subtitle {
  font-size: 9px; letter-spacing: 2px; text-transform: uppercase;
  color: rgba(255,255,255,0.35); margin-bottom: 36px;
}
/* Step indicator */
.rq-steps {
  display: flex; align-items: center; gap: 12px;
  margin-bottom: 32px;
  padding-bottom: 24px;
  border-bottom: 1px solid rgba(255,255,255,0.07);
}
.rq-step {
  display: flex; align-items: center; gap: 10px;
  font-family: 'Montserrat', sans-serif;
  font-size: 9px; letter-spacing: 2px; text-transform: uppercase;
  color: rgba(255,255,255,0.3); white-space: nowrap;
}
.rq-step.active { color: var(--gold); }
.rq-step.done { color: rgba(201,169,110,0.5); }
.rq-step-num {
  width: 22px; height: 22px; border-radius: 50%;
  border: 1px solid currentColor;
  display: flex; align-items: center; justify-content: center;
  font-size: 9px; flex-shrink: 0;
}
.rq-step-sep {
  flex: 1; height: 1px; background: rgba(255,255,255,0.12);
}
.rq-step-line { flex: 1; height: 1px; background: rgba(255,255,255,0.1); margin: 0 12px; }

/* Step 1: Size selection */
.rq-size-grid {
  display: grid; grid-template-columns: 1fr 1fr;
  gap: 10px; margin-bottom: 24px;
}
.rq-size-card {
  border: 1px solid rgba(255,255,255,0.12);
  padding: 14px 16px; cursor: pointer;
  transition: border-color .2s, background .2s;
}
.rq-size-card:hover { border-color: rgba(201,169,110,0.4); }
.rq-size-card.selected {
  border-color: var(--gold); background: rgba(201,169,110,0.08);
}
.rq-size-name {
  font-family: 'Cormorant Garamond', serif;
  font-size: 18px; letter-spacing: 1px; color: #fff;
}
.rq-size-dims {
  font-size: 9px; letter-spacing: 1px;
  color: rgba(255,255,255,0.75); margin-top: 4px; line-height: 1.7;
}
.rq-size-edition {
  font-size: 7px; letter-spacing: 2px;
  color: var(--gold); text-transform: uppercase; margin-top: 4px; opacity: .7;
}

/* Step 2: Contact details */
.rq-field { margin-bottom: 16px; }
.rq-field label {
  display: block; font-size: 8px; letter-spacing: 3px;
  text-transform: uppercase; color: rgba(255,255,255,0.35); margin-bottom: 6px;
}
.rq-field input, .rq-field textarea {
  width: 100%; background: rgba(255,255,255,0.04);
  border: 1px solid rgba(201,169,110,0.15);
  color: #fff; padding: 11px 14px;
  font-family: 'Montserrat', sans-serif; font-size: 13px;
  outline: none; transition: border-color .2s;
  -webkit-appearance: none;
}
.rq-field input:focus, .rq-field textarea:focus { border-color: var(--gold); }
.rq-field textarea { min-height: 80px; resize: vertical; }

.rq-nav {
  display: flex; justify-content: space-between; gap: 12px;
  margin-top: 24px; align-items: stretch;
}
.btn-ghost {
  background: none; border: 1px solid rgba(255,255,255,0.15);
  color: rgba(255,255,255,0.5); padding: 0 24px; height: 44px;
  font-family: 'Montserrat', sans-serif;
  font-size: 9px; letter-spacing: 3px; text-transform: uppercase;
  cursor: pointer; transition: all .2s;
  display: inline-flex; align-items: center; justify-content: center;
}
.btn-ghost:hover { border-color: rgba(255,255,255,0.3); color: rgba(255,255,255,0.8); }

/* ── COPYRIGHT BANNER — inline in gallery flow ── */
#copyright-banner {
  display: none;
  background: rgba(8,8,8,0.95);
  border-top: 1px solid rgba(201,169,110,0.08);
  padding: 10px 12px; text-align: center;
  font-size: 9px; letter-spacing: 2px;
  color: rgba(201,169,110,0.5); text-transform: uppercase; line-height: 1.8;
}
#copyright-banner.visible { display: block; }

/* ── SUBPANEL HEADER — category description at top of Level 2 panels ── */
.subpanel-header {
  padding: clamp(24px,4vw,48px) clamp(14px,4vw,44px) 0;
}
.subpanel-title {
  font-family: 'Cormorant Garamond', serif;
  font-size: clamp(28px, 5vw, 52px);
  font-weight: 600; letter-spacing: clamp(4px,1vw,8px);
  text-transform: uppercase; color: #fff; line-height: 1.1;
  margin-bottom: 8px;
}
.subpanel-desc {
  font-size: clamp(11px,1.4vw,13px); letter-spacing: 2px;
  color: rgba(255,255,255,0.4); text-transform: uppercase;
  margin-bottom: 0; font-family: 'Montserrat', sans-serif;
}

/* ── FOOTER — non-persistent, scrollable at page bottom ── */
footer {
  position: relative;   /* NOT fixed */
  background: #0a0a0a;
  border-top: 1px solid rgba(201,169,110,0.12);
  padding: 48px clamp(20px,6vw,80px) 40px;
}
.footer-inner {
  max-width: 860px; margin: 0 auto;
  display: grid; grid-template-columns: 1fr 1fr;
  gap: 40px 60px;
}
@media (max-width: 600px) {
  .footer-inner { grid-template-columns: 1fr; gap: 28px; }
}
.footer-section-title {
  font-family: 'Cormorant Garamond', serif;
  font-size: 16px; letter-spacing: 4px;
  color: var(--gold); text-transform: uppercase;
  margin-bottom: 14px;
}
.footer-section-body {
  font-size: 12px; letter-spacing: 0.5px; line-height: 1.9;
  color: rgba(255,255,255,0.38);
  font-family: 'Montserrat', sans-serif;
}
.footer-section-body p { margin-bottom: 10px; }
.footer-section-body strong { color: rgba(255,255,255,0.55); font-weight: 600; }
.footer-copy {
  grid-column: 1 / -1;
  border-top: 1px solid rgba(255,255,255,0.05);
  padding-top: 20px;
  font-size: 10px; letter-spacing: 2px;
  color: rgba(255,255,255,0.55); text-align: center;
}

/* ── NEW badge on recently added photos ── */
.new-badge {
  position: absolute; top: 10px; right: 10px;
  background: rgba(201,169,110,0.15);
  border: 1px solid rgba(201,169,110,0.6);
  color: var(--gold);
  font-family: 'Montserrat', sans-serif;
  font-size: 7px; letter-spacing: 3px; font-weight: 600;
  text-transform: uppercase;
  padding: 3px 7px;
  pointer-events: none;
  z-index: 3;
}

/* ── Recently Added notification button ── */
#new-photos-banner {
  position: absolute;
  bottom: clamp(20px, 5vh, 56px);
  left: 50%;
  transform: translateX(-50%);
  z-index: 3;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  white-space: normal;
  text-align: center;
  width: max-content;
  max-width: calc(100vw - 32px);
  padding: 10px clamp(14px, 4vw, 28px);
  font-family: 'Montserrat', sans-serif;
  font-size: clamp(8px, 2vw, 9px);
  letter-spacing: clamp(1px, 0.5vw, 3px);
  text-transform: uppercase;
  background: rgba(0,0,0,0.6);
  border: 1px solid rgba(201,169,110,0.5);
  color: var(--gold);
  cursor: pointer;
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  animation: bannerPulse 3s ease-in-out infinite;
  transition: background .25s, border-color .25s, color .25s;
}
#new-photos-banner svg { flex-shrink: 0; }
#new-photos-banner:hover {
  background: rgba(201,169,110,0.12);
  border-color: var(--gold);
  color: #fff;
}
@keyframes bannerPulse {
  0%, 100% { opacity: 0.7; }
  50%       { opacity: 1; }
}
@media (max-width: 480px) {
  #new-photos-banner {
    font-size: 8px;
    letter-spacing: 1.5px;
    padding: 9px 14px;
    gap: 6px;
  }
}

/* ── PAGE TRANSITIONS ── */
.page-enter { animation: pEnter .35s ease forwards; }
@keyframes pEnter {
  from { opacity: 0; transform: translateY(10px); }
  to   { opacity: 1; transform: none; }
}

#subscribe-section {
  padding: clamp(48px,8vw,96px) clamp(20px,5vw,80px);
  text-align: center;
  border-top: 1px solid rgba(201,169,110,0.12);
  background: var(--dark);
}
.subscribe-inner { max-width: 520px; margin: 0 auto; }
.subscribe-title {
  font-family: 'Cormorant Garamond', serif;
  font-size: clamp(26px,4vw,42px); font-weight: 300;
  letter-spacing: clamp(4px,1.5vw,10px); text-transform: uppercase;
  color: rgba(255,255,255,0.9); margin-bottom: 10px;
}
.subscribe-subtitle {
  font-family: 'Montserrat', sans-serif;
  font-size: 9px; letter-spacing: 4px; text-transform: uppercase;
  color: rgba(255,255,255,0.65); margin-bottom: 36px;
}
.subscribe-form { display: flex; flex-wrap: wrap; gap: 10px; justify-content: center; margin-bottom: 16px; }
.subscribe-form input {
  flex: 1 1 180px; background: transparent; border: none;
  border-bottom: 1px solid rgba(201,169,110,0.3);
  color: rgba(255,255,255,0.85); padding: 10px 4px;
  font-family: 'Montserrat', sans-serif; font-size: 12px; letter-spacing: 1px;
  outline: none; transition: border-color .25s;
}
.subscribe-form input::placeholder { color: rgba(255,255,255,0.5); }
.subscribe-form input:focus { border-color: var(--gold); }
.subscribe-form button {
  background: none; border: 1px solid rgba(201,169,110,0.5); color: var(--gold);
  padding: 10px 28px; font-family: 'Montserrat', sans-serif;
  font-size: 9px; letter-spacing: 4px; text-transform: uppercase;
  cursor: pointer; transition: background .25s, color .25s, border-color .25s; white-space: nowrap;
}
.subscribe-form button:hover { background: var(--gold); color: #000; border-color: var(--gold); }
#subscribe-msg { font-family: 'Montserrat', sans-serif; font-size: 10px; letter-spacing: 2px; color: var(--gold); min-height: 20px; margin-top: 4px; }

.new-photo-wrap { display: flex; flex-direction: column; }
.new-photo-tags { display: flex; flex-wrap: wrap; gap: 6px; padding: 8px 4px 4px; }


/* ═══════════════════════════════════════════════════════════════
   TRAVEL STORIES  (blog index + individual post pages)
   Mobile-first, matches existing dark/gold design language
   ═══════════════════════════════════════════════════════════════ */

/* ── Index page wrapper ── */
#page-stories { padding-top: var(--hdr); }
#page-stories.visible { display: block; }

.stories-header {
  padding: clamp(32px,5vw,64px) clamp(16px,4vw,64px) 0;
  border-bottom: 1px solid rgba(201,169,110,0.1);
  padding-bottom: clamp(20px,3vw,40px);
}
.stories-header-title {
  font-family: 'Cormorant Garamond', serif;
  font-size: clamp(28px,6vw,60px); font-weight: 300;
  letter-spacing: clamp(4px,1.5vw,14px); text-transform: uppercase;
  color: rgba(255,255,255,0.92); line-height: 1;
}
.stories-header-sub {
  font-family: 'Montserrat', sans-serif;
  font-size: 9px; letter-spacing: 5px; text-transform: uppercase;
  color: var(--gold); opacity: .7; margin-top: 10px;
}

/* ── Index card grid ── */
.stories-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(100%, 320px), 1fr));
  gap: clamp(14px, 2vw, 24px);
  padding: clamp(20px,3vw,48px) clamp(16px,4vw,64px);
}
.story-card {
  background: #0f0f0f;
  border: 1px solid rgba(201,169,110,0.1);
  cursor: pointer;
  transition: border-color .25s, transform .25s;
  overflow: hidden;
  -webkit-tap-highlight-color: transparent;
}
@media (hover: hover) {
  .story-card:hover {
    border-color: rgba(201,169,110,0.45);
    transform: translateY(-3px);
  }
}
.story-card:active { opacity: .85; }

.story-card-hero {
  width: 100%; aspect-ratio: 16/9;
  object-fit: cover; display: block;
  filter: brightness(0.82);
  transition: filter .35s;
}
@media (hover: hover) {
  .story-card:hover .story-card-hero { filter: brightness(1); }
}
.story-card-hero-placeholder {
  width: 100%; aspect-ratio: 16/9;
  background: #1a1a1a;
  display: flex; align-items: center; justify-content: center;
}
.story-card-hero-placeholder span {
  font-size: 9px; letter-spacing: 3px;
  color: rgba(255,255,255,0.15); text-transform: uppercase;
}
.story-card-body { padding: 18px 20px 20px; }
.story-card-meta {
  font-family: 'Montserrat', sans-serif;
  font-size: 8px; letter-spacing: 3px; text-transform: uppercase;
  color: var(--gold); opacity: .75; margin-bottom: 8px;
}
.story-card-title {
  font-family: 'Cormorant Garamond', serif;
  font-size: clamp(18px, 2.8vw, 26px); font-weight: 600;
  letter-spacing: 1px; color: #fff; line-height: 1.25;
  margin-bottom: 8px;
}
.story-card-summary {
  font-family: 'Montserrat', sans-serif;
  font-size: 11px; letter-spacing: 0.4px; line-height: 1.8;
  color: rgba(255,255,255,0.42);
}
.story-card-footer {
  display: flex; align-items: center; gap: 10px;
  padding: 12px 20px; border-top: 1px solid rgba(255,255,255,0.05);
}
.story-card-cats { display: flex; flex-wrap: wrap; gap: 6px; flex: 1; }
.story-card-cat {
  font-family: 'Montserrat', sans-serif;
  font-size: 7px; letter-spacing: 2px; text-transform: uppercase;
  color: rgba(201,169,110,0.7); border: 1px solid rgba(201,169,110,0.2);
  padding: 2px 7px;
}
.story-card-arrow {
  font-size: 18px; color: rgba(201,169,110,0.5);
  transition: transform .2s, color .2s; flex-shrink: 0;
}
@media (hover: hover) {
  .story-card:hover .story-card-arrow {
    transform: translateX(4px); color: var(--gold);
  }
}

/* ── Individual post page ── */
.story-post {
  display: none; position: fixed; inset: 0;
  background: var(--dark); z-index: 1500;
  overflow-y: auto; overflow-x: hidden;
  padding-top: var(--hdr);
  -webkit-overflow-scrolling: touch;
}
.story-post.visible { display: block; }

.story-post-hero {
  width: 100%;
  height: clamp(180px, 35vw, 380px);
  object-fit: cover; display: block;
  filter: brightness(0.52);
}
.story-post-hero-placeholder {
  width: 100%; height: clamp(120px, 25vw, 280px);
  background: linear-gradient(160deg,#111820,#0a0a0a);
}

.story-post-inner {
  max-width: 780px; margin: 0 auto;
  padding: 0 clamp(16px,5vw,60px) clamp(60px,8vw,100px);
}

.story-post-back {
  display: inline-flex; align-items: center; gap: 8px;
  font-size: 8px; letter-spacing: 4px; text-transform: uppercase;
  color: rgba(255,255,255,0.28); cursor: pointer;
  background: none; border: none;
  font-family: 'Montserrat', sans-serif;
  padding: clamp(20px,4vw,36px) 0 clamp(20px,4vw,32px);
  transition: color .25s; -webkit-tap-highlight-color: transparent;
}
.story-post-back:hover { color: var(--gold); }

.story-post-eyebrow {
  font-family: 'Montserrat', sans-serif;
  font-size: 8px; letter-spacing: 5px; text-transform: uppercase;
  color: var(--gold); opacity: .75; margin-bottom: 10px;
}
.story-post-title {
  font-family: 'Cormorant Garamond', serif;
  font-size: clamp(26px, 6vw, 56px); font-weight: 600;
  letter-spacing: clamp(2px,0.8vw,6px); text-transform: uppercase;
  color: #fff; line-height: 1.1; margin-bottom: 8px;
  user-select: none; -webkit-user-select: none;
}
.story-post-dates {
  font-family: 'Montserrat', sans-serif;
  font-size: 9px; letter-spacing: 3px; text-transform: uppercase;
  color: rgba(255,255,255,0.32); margin-bottom: clamp(24px,4vw,40px);
  user-select: none; -webkit-user-select: none;
}
.story-post-divider {
  height: 1px; background: rgba(201,169,110,0.12);
  margin: clamp(20px,3vw,32px) 0;
}
.story-section-label {
  font-family: 'Montserrat', sans-serif;
  font-size: 7px; letter-spacing: 5px; text-transform: uppercase;
  color: var(--gold); opacity: .65; margin-bottom: 12px;
}
.story-body {
  font-family: 'Montserrat', sans-serif;
  font-size: clamp(14px, 1.8vw, 16px); font-weight: 400;
  color: rgba(255,255,255,0.82); line-height: 1.75;
  user-select: none; -webkit-user-select: none;
}
.story-body p { margin-bottom: 14px; }
.story-body h2 {
  font-family: 'Montserrat', sans-serif !important;
  font-size: clamp(14px, 1.8vw, 16px) !important;
  font-weight: 700 !important;
  color: #fff !important;
  letter-spacing: 0.5px;
  margin: 28px 0 10px;
  text-transform: none;
  line-height: 1.4;
}
.story-inline-photo {
  width: 100%; margin: 24px 0;
  display: block;
}
.story-inline-photo img {
  width: 100%; display: block;
  border: 1px solid rgba(201,169,110,0.1);
  cursor: pointer;
}
.story-inline-caption {
  font-family: 'Montserrat', sans-serif;
  font-size: 11px; letter-spacing: 1.5px;
  color: rgba(255,255,255,0.75); text-transform: uppercase;
  margin-top: 8px; text-align: center;
  line-height: 1.5;
}

/* ── Logistics cards ── */
.story-logistics {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(100%, 180px), 1fr));
  gap: 12px; margin: 16px 0 24px;
}
.story-logistic-card {
  background: #111; border: 1px solid rgba(201,169,110,0.12);
  padding: 14px 16px;
}
.story-logistic-icon { font-size: 18px; margin-bottom: 6px; }
.story-logistic-label {
  font-family: 'Montserrat', sans-serif;
  font-size: 7px; letter-spacing: 3px; text-transform: uppercase;
  color: var(--gold); opacity: .7; margin-bottom: 5px;
}
.story-logistic-value {
  font-family: 'Montserrat', sans-serif;
  font-size: 11px; letter-spacing: 0.4px;
  color: rgba(255,255,255,0.62); line-height: 1.7;
}

/* ── Highlights ── */
.story-highlights { list-style: none; padding: 0; margin: 12px 0 24px; }
.story-highlights li {
  font-family: 'Cormorant Garamond', serif;
  font-size: clamp(15px,1.8vw,19px); font-weight: 300;
  color: rgba(255,255,255,0.58); line-height: 1.8;
  padding: 9px 0 9px 22px; position: relative;
  border-bottom: 1px solid rgba(255,255,255,0.04);
}
.story-highlights li::before {
  content: ''; position: absolute; left: 0; top: 50%;
  width: 8px; height: 1px; background: var(--gold); opacity: .7;
}

/* ── Tips box ── */
.story-tips-box {
  background: rgba(201,169,110,0.04);
  border: 1px solid rgba(201,169,110,0.18);
  border-left: 3px solid var(--gold);
  padding: 18px 20px; margin: 16px 0 24px;
}
.story-tips-box ul { list-style: none; padding: 0; margin: 0; }
.story-tips-box li {
  font-family: 'Montserrat', sans-serif;
  font-size: 12px; letter-spacing: 0.4px;
  color: rgba(255,255,255,0.58); line-height: 1.85;
  padding-left: 16px; position: relative; margin-bottom: 5px;
}
.story-tips-box li::before {
  content: '›'; position: absolute; left: 0;
  color: var(--gold); font-size: 14px; line-height: 1.5;
}

/* ── Inline photo strip ── */
.story-photo-strip {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(100%, 160px), 1fr));
  gap: clamp(5px, 1vw, 10px);
  margin: 18px 0 24px;
}
.story-photo-strip .grid-item { aspect-ratio: 4/3; cursor: pointer; }
.story-photo-strip .grid-item-photo { height: 100%; }

/* ── CTA row ── */
.story-cta-row {
  display: flex; flex-wrap: wrap; gap: 12px;
  margin-top: clamp(28px,4vw,44px);
  padding-top: clamp(20px,3vw,32px);
  border-top: 1px solid rgba(201,169,110,0.12);
}
.story-cta-btn {
  display: inline-flex; align-items: center; gap: 8px;
  background: none; border: 1px solid rgba(201,169,110,0.5);
  color: var(--gold); padding: 0 20px; height: 42px;
  font-family: 'Montserrat', sans-serif;
  font-size: 9px; letter-spacing: 3px; text-transform: uppercase;
  cursor: pointer; transition: background .2s, color .2s;
  -webkit-tap-highlight-color: transparent;
  flex: 1 1 auto; justify-content: center; text-align: center;
}
.story-cta-btn:hover { background: var(--gold); color: #000; }
.story-cta-btn-ghost {
  display: inline-flex; align-items: center; gap: 8px;
  background: none; border: 1px solid rgba(255,255,255,0.14);
  color: rgba(255,255,255,0.55); padding: 0 20px; height: 42px;
  font-family: 'Montserrat', sans-serif;
  font-size: 9px; letter-spacing: 3px; text-transform: uppercase;
  cursor: pointer; transition: all .2s;
  -webkit-tap-highlight-color: transparent;
  flex: 1 1 auto; justify-content: center; text-align: center;
}
.story-cta-btn-ghost:hover { border-color: rgba(201,169,110,0.4); color: var(--gold); }

/* ── Empty state ── */
.stories-empty {
  text-align: center;
  padding: clamp(48px,10vw,100px) clamp(16px,5vw,80px);
}
.stories-empty-title {
  font-family: 'Cormorant Garamond', serif;
  font-size: clamp(20px,4vw,38px); font-weight: 300;
  letter-spacing: 6px; text-transform: uppercase;
  color: rgba(255,255,255,0.28); margin-bottom: 14px;
}
.stories-empty-sub {
  font-family: 'Montserrat', sans-serif;
  font-size: 9px; letter-spacing: 4px; text-transform: uppercase;
  color: rgba(255,255,255,0.18);
}

/* ── Blog list (Travel Stories index) ── */
.blog-list {
  max-width: 780px; margin: 0 auto;
  padding: clamp(20px,3vw,40px) clamp(16px,4vw,64px);
}
.blog-row {
  display: flex; align-items: center; justify-content: space-between;
  gap: 16px; padding: clamp(18px,2.5vw,28px) 0;
  border-bottom: 1px solid rgba(255,255,255,0.06);
  cursor: pointer;
  transition: border-color .2s;
  -webkit-tap-highlight-color: transparent;
}
.blog-row:first-child { border-top: 1px solid rgba(255,255,255,0.06); }
.blog-row:hover { border-bottom-color: rgba(201,169,110,0.3); }
.blog-row-main { flex: 1; min-width: 0; }
.blog-row-title {
  font-family: 'Cormorant Garamond', serif;
  font-size: clamp(18px,2.8vw,26px); font-weight: 600;
  letter-spacing: 1px; color: #fff; line-height: 1.3;
  transition: color .2s;
}
.blog-row:hover .blog-row-title { color: var(--gold); }
.blog-row-summary {
  font-family: 'Montserrat', sans-serif;
  font-size: 11px; letter-spacing: 0.3px; line-height: 1.7;
  color: rgba(255,255,255,0.38); margin-top: 5px;
}
.blog-row-meta {
  display: flex; flex-direction: column; align-items: flex-end;
  gap: 4px; flex-shrink: 0;
}
.blog-row-loc {
  font-family: 'Montserrat', sans-serif;
  font-size: 9px; letter-spacing: 2px; text-transform: uppercase;
  color: var(--gold); opacity: .75;
}
.blog-row-date {
  font-family: 'Montserrat', sans-serif;
  font-size: 9px; letter-spacing: 1px;
  color: rgba(255,255,255,0.28);
}
.blog-row-arrow {
  font-size: 22px; color: rgba(201,169,110,0.4);
  transition: transform .2s, color .2s; margin-top: 4px;
}
.blog-row:hover .blog-row-arrow { transform: translateX(4px); color: var(--gold); }
.blog-post-loc {
  font-family: 'Montserrat', sans-serif;
  font-size: 8px; letter-spacing: 5px; text-transform: uppercase;
  color: var(--gold); opacity: .75; margin-bottom: 10px;
}
@media (max-width: 480px) {
  .blog-row { flex-direction: column; align-items: flex-start; gap: 8px; }
  .blog-row-meta { flex-direction: row; align-items: center; gap: 10px; }
  .blog-row-arrow { display: none; }
}

/* Mobile tweaks */
@media (max-width: 480px) {
  .story-cta-btn, .story-cta-btn-ghost { flex: 1 1 100%; }
}
.new-photo-tag { font-family: 'Montserrat', sans-serif; font-size: 7px; letter-spacing: 2px; color: var(--gold); opacity: 0.8; border: 1px solid rgba(201,169,110,0.3); padding: 3px 7px; }

"""

    # ── BUILD GALLERY BLOCKS + SUB-PANELS ────────────────────────────────────
    gallery_blocks = ""
    sub_panels     = ""

    # ── NEW ARCHITECTURE: each category → India/Overseas pills → city/country cards ──
    for m_cat in CAT_ORDER:
        india_data    = cat_city_map.get(m_cat, {}).get('India', {})
        overseas_data = cat_city_map.get(m_cat, {}).get('Overseas', {})

        # ── India: city cards ─────────────────────────────────────────────────
        india_city_cards = ""
        for city in sorted(india_data.keys(), key=str.lower):
            state_dict = india_data[city]   # {state: [paths]}
            city_paths = [p for ps in state_dict.values() for p in ps]
            state_name = next(iter(state_dict.keys()), '')
            city_id    = 'gallery-' + m_cat.replace(' ','_').replace('&','n') + '-india-' + city.replace(' ','_')
            city_cover = thumb_map.get(pick_cover(city_paths), '')

            india_city_cards += (
                '\n<div class="cat-card" onclick="showGallery(\'' + city_id + '\')">'
                + ('<img class="cat-card-img" src="' + _url_quote(city_cover,safe="/") + '" loading="lazy" decoding="async" alt="">'
                   if city_cover else '<div class="cat-card-placeholder"><span>Coming<br>Soon</span></div>')
                + '<div class="cat-card-bar">'
                '<div class="cat-card-name">' + city + '</div>'
                '<div class="cat-card-count">' + (state_name + ' · ' if state_name else '') + str(len(city_paths)) + ' Photos</div>'
                '</div>\n</div>'
            )

            # Photo grid for this India city
            imgs = ""
            for p in city_paths:
                pi     = path_info.get(p, {})
                rem    = pi.get('remarks', '').strip()
                sv     = pi.get('state',   '').strip()
                cv     = pi.get('city',    '').strip()
                da     = pi.get('date_added', '').strip()
                cats_p = meta_by_path.get(p, {}).get('categories', [])
                th     = thumb_map.get(p, p)
                web    = web_map.get(p, p)
                # Overlay: Remarks · City · State
                overlay_parts = [x for x in [rem, cv, sv] if x]
                overlay_text  = ' · '.join(overlay_parts)
                overlay_html  = ('<div class="grid-item-info"><span class="grid-item-info-text">'
                                 + overlay_text + '</span></div>') if overlay_text else ''
                imgs += (
                    '<div class="grid-item"'
                    ' data-photo="'      + p              + '"'
                    ' data-state="'      + sv             + '"'
                    ' data-city="'       + cv             + '"'
                    ' data-remarks="'    + rem            + '"'
                    ' data-cats="'       + ','.join(cats_p) + '"'
                    ' data-date-added="' + da             + '"'
                    ' onclick="openImgModal(this)">'
                    '<div class="grid-item-photo">'
                    '<img src="' + _url_quote(th,safe="/") + '" data-full="' + _url_quote(web,safe="/") + '" loading="lazy" decoding="async" alt=""'
                    ' style="width:100%;height:100%;object-fit:cover;display:block;">'
                    '<div class="grid-item-overlay"></div>'
                    + overlay_html +
                    '</div></div>'
                )
            _ss_btn = ('<button class="slideshow-btn" onclick="startSlideshow(\'' + city_id + '\')">' +
                       '<svg width="11" height="11" viewBox="0 0 11 11" fill="none">' +
                       '<polygon points="1,0.5 10.5,5.5 1,10.5" fill="currentColor"/></svg>' +
                       'View Slideshow</button>') if city_paths else ''
            gallery_blocks += (
                '\n<div class="section-block" id="' + city_id + '">'
                '\n  <div class="gal-header">'
                '<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;">'
                '<div><div class="gal-title">' + city + '</div>'
                '<div class="gal-sub">' + m_cat + ' · ' + (state_name + ' · ' if state_name else '') + str(len(city_paths)) + ' Photos</div>'
                '</div>' + _ss_btn + '</div>'
                '</div>'
                + ('\n  <div class="grid">' + imgs + '</div>' if city_paths else '\n  <div class="wip-message">Work in progress</div>')
                + '\n</div>'
            )

        # ── Overseas: country cards → city cards ──────────────────────────────
        overseas_country_cards = ""
        for country in sorted(overseas_data.keys(), key=str.lower):
            city_dict   = overseas_data[country]   # {city: [paths]}
            ctry_paths  = [p for ps in city_dict.values() for p in ps]
            ctry_id     = 'gallery-' + m_cat.replace(' ','_').replace('&','n') + '-overseas-' + country.replace(' ','_')
            ctry_cover  = thumb_map.get(pick_cover(ctry_paths), '')

            overseas_country_cards += (
                '\n<div class="cat-card" onclick="showGallery(\'' + ctry_id + '\')">'
                + ('<img class="cat-card-img" src="' + _url_quote(ctry_cover,safe="/") + '" loading="lazy" decoding="async" alt="">'
                   if ctry_cover else '<div class="cat-card-placeholder"><span>Coming<br>Soon</span></div>')
                + '<div class="cat-card-bar">'
                '<div class="cat-card-name">' + country + '</div>'
                '<div class="cat-card-count">' + str(len(ctry_paths)) + ' Photos</div>'
                '</div>\n</div>'
            )

            # City cards within this country
            city_cards_html = ""
            for city in sorted(city_dict.keys(), key=str.lower):
                city_paths = city_dict[city]
                city_id    = ctry_id + '-' + city.replace(' ','_')
                city_cover = thumb_map.get(pick_cover(city_paths), '')

                city_cards_html += (
                    '\n<div class="cat-card" onclick="showGallery(\'' + city_id + '\')">'
                    + ('<img class="cat-card-img" src="' + city_cover + '" loading="lazy" decoding="async" alt="">'
                       if city_cover else '<div class="cat-card-placeholder"><span>Coming<br>Soon</span></div>')
                    + '<div class="cat-card-bar">'
                    '<div class="cat-card-name">' + city + '</div>'
                    '<div class="cat-card-count">' + str(len(city_paths)) + ' Photos</div>'
                    '</div>\n</div>'
                )

                # Photo grid for this overseas city
                imgs = ""
                for p in city_paths:
                    pi     = path_info.get(p, {})
                    rem    = pi.get('remarks', '').strip()
                    sv     = pi.get('state',   '').strip()
                    cv     = pi.get('city',    '').strip()
                    co     = pi.get('country', '').strip()
                    da     = pi.get('date_added', '').strip()
                    cats_p = meta_by_path.get(p, {}).get('categories', [])
                    th     = thumb_map.get(p, p)
                    web    = web_map.get(p, p)
                    # Overlay: Remarks · City · Country
                    overlay_parts = [x for x in [rem, cv, co or country] if x]
                    overlay_text  = ' · '.join(overlay_parts)
                    overlay_html  = ('<div class="grid-item-info"><span class="grid-item-info-text">'
                                     + overlay_text + '</span></div>') if overlay_text else ''
                    imgs += (
                        '<div class="grid-item"'
                        ' data-photo="'      + p              + '"'
                        ' data-state="'      + sv             + '"'
                        ' data-city="'       + cv             + '"'
                        ' data-remarks="'    + rem            + '"'
                        ' data-cats="'       + ','.join(cats_p) + '"'
                        ' data-date-added="' + da             + '"'
                        ' onclick="openImgModal(this)">'
                        '<div class="grid-item-photo">'
                        '<img src="' + _url_quote(th,safe="/") + '" data-full="' + _url_quote(web,safe="/") + '" loading="lazy" decoding="async" alt=""'
                        ' style="width:100%;height:100%;object-fit:cover;display:block;">'
                        '<div class="grid-item-overlay"></div>'
                        + overlay_html +
                        '</div></div>'
                    )
                _ss_btn2 = ('<button class="slideshow-btn" onclick="startSlideshow(\'' + city_id + '\')">' +
                            '<svg width="11" height="11" viewBox="0 0 11 11" fill="none">' +
                            '<polygon points="1,0.5 10.5,5.5 1,10.5" fill="currentColor"/></svg>' +
                            'View Slideshow</button>') if city_paths else ''
                gallery_blocks += (
                    '\n<div class="section-block" id="' + city_id + '">'
                    '\n  <div class="gal-header">'
                    '<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;">'
                    '<div><div class="gal-title">' + city + '</div>'
                    '<div class="gal-sub">' + m_cat + ' · ' + country + ' · ' + str(len(city_paths)) + ' Photos</div>'
                    '</div>' + _ss_btn2 + '</div>'
                    '</div>'
                    + ('\n  <div class="grid">' + imgs + '</div>' if city_paths else '\n  <div class="wip-message">Work in progress</div>')
                    + '\n</div>'
                )

            # Country panel shows city cards
            gallery_blocks += (
                '\n<div class="section-block" id="' + ctry_id + '">'
                '\n  <div class="gal-header">'
                '<div class="gal-title">' + country + '</div>'
                '<div class="gal-sub">' + m_cat + ' · Overseas · ' + str(len(ctry_paths)) + ' Photos</div>'
                '</div>'
                '\n  <div class="cat-grid-4">' + city_cards_html + '\n  </div>'
                '\n</div>'
            )

        # ── Sub-panel for this category: India/Overseas pills ─────────────────
        india_empty    = not india_data
        overseas_empty = not overseas_data

        if india_empty:
            india_city_cards = '<div class="wip-message">No India photos tagged yet</div>'
        if overseas_empty:
            overseas_country_cards = '<div class="wip-message">No Overseas photos tagged yet</div>'

        sub_panels += (
            '\n<div class="sub-panel" id="subpanel-' + m_cat.replace(' ','_').replace('&','n') + '">'
            '\n<div class="subpanel-header">'
            '<div class="subpanel-title">' + m_cat + '</div>'
            '</div>'
            # Filter pills
            '\n<div class="places-filters" style="padding-top:clamp(16px,3vw,28px)">'
            '<button class="places-pill active" data-region="india-' + m_cat.replace(' ','_').replace('&','n') + '"'
            ' onclick="setCatFilter(this,\'india-' + m_cat.replace(' ','_').replace('&','n') + '\')">India</button>'
            '<button class="places-pill" data-region="overseas-' + m_cat.replace(' ','_').replace('&','n') + '"'
            ' onclick="setCatFilter(this,\'overseas-' + m_cat.replace(' ','_').replace('&','n') + '\')">Overseas</button>'
            '</div>'
            # India section (default visible)
            '\n<div class="cat-region-section cat-grid-4" id="india-' + m_cat.replace(' ','_').replace('&','n') + '">'
            + india_city_cards +
            '\n</div>'
            # Overseas section (default hidden)
            '\n<div class="cat-region-section cat-grid-4" id="overseas-' + m_cat.replace(' ','_').replace('&','n') + '" style="display:none">'
            + overseas_country_cards +
            '\n</div>'
            '\n</div>'
        )

    # ── MAIN CATEGORY TILES ───────────────────────────────────────────────────
    cat_tiles_html = ""
    for m_cat in CAT_ORDER:
        raw_cover   = cat_covers.get(m_cat, "")
        thumb_cover = thumb_map.get(raw_cover, raw_cover) if raw_cover else ""
        # Count all photos in this category
        total = sum(
            len(paths)
            for region in ['India', 'Overseas']
            for top in cat_city_map.get(m_cat, {}).get(region, {}).values()
            for paths in (top.values() if isinstance(top, dict) else [top])
        )
        count_lbl = str(total) + " Photos" if total else "Coming Soon"
        panel_id  = 'subpanel-' + m_cat.replace(' ','_').replace('&','n')

        cat_tiles_html += (
            '\n<div class="cat-card" onclick="openCategory(\'' + m_cat + '\')" role="button" tabindex="0"'
            ' onkeypress="if(event.key===\'Enter\') this.click()">'
            + ('<img class="cat-card-img" src="' + thumb_cover + '" loading="lazy" decoding="async" alt="">'
               if thumb_cover else '<div class="cat-card-placeholder"><span>Coming<br>Soon</span></div>')
            + '<div class="cat-card-bar">'
            '<div class="cat-card-name">' + m_cat + '</div>'
            '</div>'
            '\n</div>'
        )

    # ── RECENTLY ADDED — compute 14-day window for the hero banner ───────────────
    import datetime as _dt
    _now = _dt.datetime.now()
    _RECENT_DAYS = 14
    _recent_paths = sorted(
        [p for p, pi in path_info.items()
         if pi.get('date_added','') and
         (_now - _dt.datetime.fromisoformat(pi['date_added'])).days <= _RECENT_DAYS],
        key=lambda p: path_info[p].get('date_added',''),
        reverse=True
    )
    _ra_count = len(_recent_paths)  # only photos within 14 days

    nav_drawer_rows = ''  # legacy — not used with new header dropdown

    # ── BUILD TRAVEL STORIES HTML ─────────────────────────────────────────────
    import html as _htmlmod, json as _jsonmod

    def _ea(s):
        return _htmlmod.escape(str(s), quote=True)

    def _eh(s):
        return _htmlmod.escape(str(s))

    def build_blog_html(posts, path_info, thumb_map, web_map, meta_by_path):
        """
        Simple blog:
          - Index page  : list of titles as clickable links + date + one-line summary
          - Post page   : title, date, full body text (pasted in), then photo CTA buttons
          blog_posts.json fields used:
            id, title, dates_visited, place, country, summary, body, place_tag,
            collections_links
        """
        if not posts:
            empty = (
                '<div class="stories-empty">'
                '<div class="stories-empty-title">No Stories Yet</div>'
                '<div class="stories-empty-sub">Add posts to blog_posts.json and redeploy</div>'
                '</div>'
            )
            return empty, ""

        index_rows = ""
        post_pages = ""

        for post in posts:
            pid       = "story-" + _ea(post.get("id", ""))
            title     = _eh(post.get("title",  post.get("place", "Untitled")))
            dates     = _eh(post.get("dates_visited", ""))
            place     = post.get("place", "")
            country   = post.get("country", "")
            summary   = _eh(post.get("summary", ""))
            body      = post.get("body", "")          # free-text write-up, newlines = paragraphs
            place_tag = post.get("place_tag", place)
            cats_link = post.get("collections_links", [])

            loc_parts = [x for x in [place, country] if x]
            loc_str   = " \u00b7 ".join(loc_parts)

            # ── Index row ──────────────────────────────────────────────────
            index_rows += (
                '<div class="blog-row" onclick="showStoryPost(\'' + _ea(pid) + '\')">'
                '<div class="blog-row-main">'
                '<div class="blog-row-title">' + title + '</div>'
                + ('<div class="blog-row-summary">' + summary + '</div>' if post.get("summary") else '')
                + '</div>'
                '<div class="blog-row-meta">'
                + ('<span class="blog-row-loc">' + _eh(loc_str) + '</span>' if loc_str else '')
                + ('<span class="blog-row-date">' + dates + '</span>' if post.get("dates_visited") else '')
                + '<span class="blog-row-arrow">\u203a</span>'
                '</div>'
                '</div>\n'
            )

            # ── CTA buttons at end of post ─────────────────────────────────
            place_lower = place_tag.lower().strip()
            place_photos = [
                p for p, pi in path_info.items()
                if place_lower and place_lower in (
                    pi.get("city","").lower().strip(),
                    pi.get("state","").lower().strip(),
                    pi.get("place","").lower().strip()
                )
            ]

            cta_html = ""
            if place_photos:
                cta_html += (
                    '<button class="story-cta-btn"'
                    ' onclick="showStoryGallery(\'' + _ea(pid) + "','" + _ea(place_tag) + "')"
                    + '">\u25b6\u00a0 View Photos from ' + _eh(place) + '</button>'
                )
            # Collections link buttons removed — only show View Photos button

            # ── Body paragraphs ────────────────────────────────────────────
            # \n\n = paragraph break, \n = line break within paragraph
            # ## Heading text        → bold sub-heading
            # [photo: filename.jpg]  → inline photo, can be anywhere in text
            # [photo: filename.jpg | My caption]  → inline photo with caption
            if body:
                import re as _re

                def render_photo_tag(fname, caption):
                    """Turn a [photo:...] reference into HTML. Returns HTML string."""
                    fname = fname.strip()
                    caption = caption.strip() if caption else ''
                    photo_path = next(
                        (p for p in thumb_map if os.path.basename(p).lower() == fname.lower()),
                        None
                    )
                    if not photo_path:
                        print(f"  ⚠️  Blog photo not found: {fname!r}")
                        return '<p style="color:rgba(201,169,110,0.4);font-size:11px;font-style:italic;">[Photo not found: ' + _eh(fname) + ']</p>'
                    th     = thumb_map.get(photo_path, photo_path)
                    web    = web_map.get(photo_path, photo_path)
                    pi     = path_info.get(photo_path, {})
                    rem    = pi.get('remarks', '').strip()
                    sv     = pi.get('state',   '').strip()
                    cv     = pi.get('city',    '').strip()
                    da     = pi.get('date_added', '').strip()
                    cats_p = meta_by_path.get(photo_path, {}).get('categories', [])
                    cap_html = (
                        '<div class="story-inline-caption">' + _eh(caption) + '</div>'
                        if caption else ''
                    )
                    return (
                        '<div class="story-inline-photo">'
                        '<div class="grid" style="display:block;background:none;padding:0;">'
                        '<div class="grid-item"'
                        ' data-photo="'      + _ea(photo_path)       + '"'
                        ' data-state="'      + _ea(sv)               + '"'
                        ' data-city="'       + _ea(cv)               + '"'
                        ' data-remarks="'    + _ea(rem)              + '"'
                        ' data-cats="'       + _ea(','.join(cats_p)) + '"'
                        ' data-date-added="' + _ea(da)               + '"'
                        ' onclick="openImgModal(this)">'
                        '<div class="grid-item-photo" style="padding-bottom:0;height:auto;">'
                        '<img src="' + _ea(th) + '" data-full="' + _ea(web) + '"'
                        ' loading="lazy" decoding="async"'
                        ' alt="' + _ea(caption or rem or cv) + '"'
                        ' style="width:100%;height:auto;object-fit:contain;display:block;position:static;">'
                        '<div class="grid-item-overlay"></div>'
                        '</div></div></div>'
                        + cap_html +
                        '</div>'
                    )

                def render_text_chunk(text):
                    """Render a text chunk that may contain [photo:...] tags anywhere."""
                    # Split on [photo:...] tags — they can be inline in the text
                    PHOTO_RE = _re.compile(r'\[photo:\s*([^\]|]+?)(?:\s*\|\s*([^\]]*))?\]', _re.IGNORECASE)
                    parts = []
                    last = 0
                    for m in PHOTO_RE.finditer(text):
                        before = text[last:m.start()].strip()
                        if before:
                            parts.append('<p>' + _eh(before).replace('\n', '<br>') + '</p>')
                        parts.append(render_photo_tag(m.group(1), m.group(2)))
                        last = m.end()
                    after = text[last:].strip()
                    if after:
                        parts.append('<p>' + _eh(after).replace('\n', '<br>') + '</p>')
                    return ''.join(parts)

                paras = [p.strip() for p in body.split('\n\n') if p.strip()]
                body_parts = []
                for para in paras:
                    if para.startswith('##'):
                        body_parts.append('<h2>' + _eh(para.lstrip('#').strip()) + '</h2>')
                    else:
                        body_parts.append(render_text_chunk(para))
                body_html = ''.join(body_parts)

            else:
                body_html = '<p style="color:rgba(255,255,255,0.25);font-style:italic;">No write-up yet. Add a \\"body\\" field to this post in blog_posts.json.</p>'

            # ── Assemble post page ─────────────────────────────────────────
            post_pages += (
                '<div id="' + _ea(pid) + '" class="story-post">\n'
                '<div class="story-post-inner">\n'
                '<button class="story-post-back" onclick="closeStoryPost()">'
                '\u2039 Travel Stories</button>\n'
                + ('<div class="blog-post-loc">' + _eh(loc_str) + '</div>\n' if loc_str else '')
                + '<div class="story-post-title">' + title + '</div>\n'
                + ('<div class="story-post-dates">' + dates + '</div>\n' if post.get("dates_visited") else '')
                + '<div class="story-post-divider"></div>\n'
                + '<div class="story-body">' + body_html + '</div>\n'
                + ('<div class="story-post-divider"></div>\n'
                   '<div class="story-cta-row">' + cta_html + '</div>\n'
                   if cta_html else '')
                + '</div>\n</div>\n\n'
            )

        index_html = (
            '<div class="blog-list">' + index_rows + '</div>'
        )
        return index_html, post_pages


    stories_index_html, story_post_pages = build_blog_html(
        blog_posts, path_info, thumb_map, web_map, meta_by_path
    )

    # ── BLOG PHOTO MAP (needed for config) ────────────────────────────────────
    # Serialize photo paths per post for the JS gallery function
    _blog_photo_map = {}
    for _bp in blog_posts:
        _bpid  = _bp.get("id", "")
        _bptag = _bp.get("place_tag", _bp.get("place", "")).lower().strip()
        _bpaths = []
        for _pp, _pi in path_info.items():
            _c = _pi.get("city",  "").lower().strip()
            _s = _pi.get("state", "").lower().strip()
            _n = _pi.get("place", "").lower().strip()
            if _bptag and _bptag in (_c, _s, _n):
                _bpaths.append(_pp)
        if _bpid:
            _blog_photo_map["story-" + _bpid] = _bpaths
    # _blog_photo_map goes directly into _mohan_config below — no separate JSON needed

    # ── JAVASCRIPT FILE ──────────────────────────────────────────────────────────
    # Pure JS in r-string — no Python interpolation, no escape issues.
    # Python data injected via window.MOHAN_CONFIG in the HTML config block.
    _MOHAN_JS = r"""
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
    const hash = window.location.hash;
    
    // 1. Handle Travel Stories (Blog)
    if (hash === '#travel-stories') {
        if (typeof showStoriesIndex === 'function') {
            showStoriesIndex();
            // Small delay to allow the DOM to render before scrolling
            setTimeout(() => {
                const el = document.getElementById('travel-stories');
                if (el) el.scrollIntoView({ behavior: 'smooth' });
            }, 300);
        }
    } 
    
    // 2. Handle Recently Added (Gallery)
    else if (hash === '#recently-added') {
        const el = document.getElementById('recently-added');
        if (el) el.scrollIntoView({ behavior: 'smooth' });
    }
});# This is the end of your _MOHAN_JS string

"""

    # ── ASSEMBLE HTML ─────────────────────────────────────────────────────────
    # Build MOHAN_CONFIG — all Python data passed to JS via JSON, zero interpolation
    categories_list = sorted([
        "Nature/Landscapes","Nature/Wildlife","Nature/Birds","Nature/Flora",
        "Places/National","Places/International",
        "Architecture","People & Culture"
    ])
    _blog_posts_for_js = [
        {"id": p.get("id",""), "title": p.get("title",""),
         "place": p.get("place",""), "dates": p.get("dates_visited",""),
         "summary": p.get("summary","")}
        for p in blog_posts
    ]
    _mohan_config = {
        "heroThumbs":   hero_thumb_paths,
        "supaUrl":      supabase_url,
        "supaKey":      supabase_key,
        "adminPass":    admin_password,
        "contactEmail": contact_email,
        "categories":   categories_list,
        "blogPhotoMap": _blog_photo_map,
        "blogPosts":    _blog_posts_for_js,
    }
    _config_json = json.dumps(_mohan_config)

    # Pre-build about body HTML (avoids inline ternary in string concat)
    about_paras = render_paragraphs(c_about.get('paragraphs', ['[ Add your story in content.json ]']))
    if has_about_photo:
        about_body_html = (
            '    <div class="about-layout">\n'
            '      <div class="about-photo-wrap">\n'
            '        <img src="about_photo.jpg" alt="' + photographer + '">\n'
            '        <div class="about-photo-caption">' + photographer + '</div>\n'
            '      </div>\n'
            '      <div class="info-page-body">\n'
            + about_paras +
            '      </div>\n'
            '    </div>\n'
        )
    else:
        about_body_html = (
            '    <div class="info-page-body">\n'
            + about_paras +
            '    </div>\n'
        )


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
        + ''
        + (
            '  <!-- Google Analytics -->\n'
            '  <script>\n'
            '  /* GA opt-out: run once in browser console on your own devices:\n'
            '     localStorage.setItem("ga_optout","1")  */\n'
            '  window.dataLayer=window.dataLayer||[];\n'
            '  function gtag(){dataLayer.push(arguments);}\n'
            '  (function(){\n'
            '    if(localStorage.getItem("ga_optout")==="1") return;\n'
            '    var s=document.createElement("script");\n'
            '    s.async=true;\n'
            '    s.onload=function(){ gtag("js",new Date()); gtag("config","' + ga_id + '",{anonymize_ip:true}); };\n'
            '    s.src="https://www.googletagmanager.com/gtag/js?id=' + ga_id + '";\n'
            '    document.head.appendChild(s);\n'
            '  })();\n'
            '  </script>\n'
            if ga_id else ''
        )
        + '  <style>' + css + '</style>\n'
        '</head>\n'
        '<body>\n'
        '<div id="toast"></div>\n\n'

        # ── HEADER ──────────────────────────────────────────────────────────
        '<!-- HEADER -->\n'
        '<header>\n'

        # Left — logo
        '  <div class="site-logo" onclick="goHome()" ondblclick="toggleAdminMode()" role="button" tabindex="0"'
        '       onkeypress="if(event.key===\'Enter\') goHome()">MOHANGRAPHY</div>\n'

        # Center — tabs (Collections uses div to allow nested dropdown div)
        '  <nav class="hdr-tabs" role="navigation">\n'
        '    <button class="hdr-tab" id="tab-home" onclick="goHome()">Home</button>\n'
        '    <div class="hdr-tab" id="tab-collections" role="button" tabindex="0"'
        '         onclick="toggleCollectionsDD(event)">\n'
        '      Collections <span class="hdr-tab-chevron">&#9662;</span>\n'
        '      <div class="hdr-dropdown" id="hdr-collections-dd">\n'
        + ''.join(
            '        <button class="hdr-dd-item" onclick="openCategory(\'' + m_cat + '\'); closeCollectionsDD()">' + m_cat + '</button>\n'
            for m_cat in CAT_ORDER
        ) +
        '      </div>\n'
        '    </div>\n'
        '    <button class="hdr-tab" id="tab-about" onclick="showInfoPage(\'page-about\')">About Me</button>\n'
        '    <button class="hdr-tab" id="tab-stories" onclick="showStoriesIndex()">Travel Stories</button>\n'
        '  </nav>\n'

        # Right — CTA + hamburger
        '  <button class="hdr-cta" onclick="showInfoPage(\'page-contact\')">Get In Touch</button>\n'
        '  <button class="hdr-hamburger" onclick="openMobileMenu()" aria-label="Menu">\n'
        '    <span></span><span></span><span></span>\n'
        '  </button>\n'

        '</header>\n\n'

        # ── MOBILE MENU ────────────────────────────────────────────────────
        '<div id="mobile-menu">\n'
        '  <button class="mob-menu-close" onclick="closeMobileMenu()">&#x2715;</button>\n'
        '  <button class="mob-menu-item" onclick="goHome();closeMobileMenu()">Home</button>\n'
        '  <button class="mob-menu-item" onclick="mobToggleCollections()">Collections &#9662;</button>\n'
        '  <div class="mob-menu-sub" id="mob-collections-sub">\n'
        + ''.join(
            '    <button class="mob-menu-subitem" onclick="openCategory(\'' + m_cat + '\');closeMobileMenu()">' + m_cat + '</button>\n'
            for m_cat in CAT_ORDER
        ) +
        '  </div>\n'
        '  <button class="mob-menu-item" onclick="showInfoPage(\'page-about\');closeMobileMenu()">About Me</button>\n'
        '  <button class="mob-menu-item" onclick="showStoriesIndex();closeMobileMenu()">Travel Stories</button>\n'
        '  <button class="mob-menu-cta" onclick="showInfoPage(\'page-contact\');closeMobileMenu()">Get In Touch</button>\n'
        '</div>\n\n'

        # ── HERO ────────────────────────────────────────────────────────────
        '<!-- HERO -->\n'
        '<div id="hero">\n'
        '  <div class="hero-caption">\n'
        '    <div class="hero-tagline">Light <span class="dot">&middot;</span> Moment <span class="dot">&middot;</span> Story</div>\n'
        '    <div class="hero-byline"><span class="byline-label">Photos by</span><span class="name">N C Mohan</span></div>\n'
        '  </div>\n'
        '  <button class="scroll-cue" onclick="scrollToCollections()" aria-label="Explore collections">\n'
        '    <svg width="14" height="20" viewBox="0 0 12 18" fill="none">\n'
        '      <path d="M6 2v10M2 9l4 5 4-5" stroke="rgba(255,255,255,0.65)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>\n'
        '    </svg>\n'
        '    <span>Explore</span>\n'
        '  </button>\n'
        + '  <button id="new-photos-banner" onclick="showNewPhotos()" aria-label="View recently added photos">\n'
        '    <svg width="10" height="10" viewBox="0 0 10 10" fill="none" style="flex-shrink:0">'
        '<circle cx="5" cy="5" r="4" stroke="currentColor" stroke-width="1.2"/>'
        '<circle cx="5" cy="5" r="1.5" fill="currentColor"/></svg>\n'
        '    <span id="new-photos-label">Checking for new photos\u2026</span>\n'
        '  </button>\n'
        + '</div>\n\n'

        # ── MAIN MENU ────────────────────────────────────────────────────────
        '<div id="tile-nav">\n'
        '  <div class="tile-nav-label">Collections</div>\n'
        '  <div class="cat-grid">\n'
        + cat_tiles_html +
        '\n  </div>\n'
        '\n</div>\n\n'

        # ── SUB-NAV ──────────────────────────────────────────────────────────
        '<div id="sub-nav">\n'
        '  <div class="breadcrumb-bar" id="bc-bar"></div>\n'
        + sub_panels +
        '\n</div>\n\n'

        # ── GALLERY ──────────────────────────────────────────────────────────
        '<main id="gallery-container">\n'
        '  <div class="breadcrumb-bar" id="gal-bc-bar"></div>\n'
        + gallery_blocks +
        '\n</main>\n\n'

        # ── INFO PAGES ───────────────────────────────────────────────────────
        # ABOUT ME — combined About + Philosophy + Gear & Kit
        '<div id="page-about" class="info-page">\n'
        '  <div class="info-page-inner">\n'
        '    <button class="info-page-back" onclick="goHome()">&larr; Back to Home</button>\n'
        '    <div class="info-page-title">' + c_about.get('title','About Me') + '</div>\n'
        '    <div class="info-page-subtitle">' + c_about.get('subtitle','Photographer · ' + photographer) + '</div>\n'
        '    <div class="info-page-divider"></div>\n'
        + about_body_html
        + '    <div class="info-page-divider"></div>\n'
        '    <div class="info-page-title" style="font-size:clamp(20px,3vw,32px);margin-bottom:6px">' + c_phil.get('title','Philosophy') + '</div>\n'
        '    <div class="info-page-subtitle">' + c_phil.get('subtitle','How I see the world') + '</div>\n'
        '    <div class="info-page-body">\n'
        + render_paragraphs(c_phil.get('paragraphs', ['[ Add your philosophy in content.json ]'])) +
        '    </div>\n'
        '    <div class="info-page-divider"></div>\n'
        '    <div class="info-page-title" style="font-size:clamp(20px,3vw,32px);margin-bottom:6px">' + c_gear.get('title','Gear &amp; Kit') + '</div>\n'
        '    <div class="info-page-subtitle">' + c_gear.get('subtitle','The tools of the trade') + '</div>\n'
        '    <div class="info-page-body">\n'
        + render_items(c_gear.get('items', [])) +
        '    </div>\n'
        '  </div>\n</div>\n\n'

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


        # ── TRAVEL STORIES PAGES ──────────────────────────────────────────────────
        # ── TRAVEL STORIES — index page ─────────────────────────────────────
        '<div id="page-stories" class="info-page">\n'
        '  <div class="stories-header">\n'
        '    <div class="stories-header-title">Travel Stories</div>\n'
        '    <div class="stories-header-sub">Places · Moments · Reflections</div>\n'
        '  </div>\n'
        + stories_index_html
        + '</div>\n\n'
        + story_post_pages
        + '\n'

        # ── IMAGE DETAIL MODAL ───────────────────────────────────────────────────
        '<div id="img-modal" role="dialog" aria-modal="true">\n'
        '  <div class="img-modal-photo">\n'
        '    <button class="img-modal-close" onclick="closeImgModal()" aria-label="Close">&#x2715;</button>\n'
        '    <button class="img-modal-nav" id="img-modal-prev" onclick="imgStep(-1)" aria-label="Previous">&#8249;</button>\n'
        '    <button class="img-modal-nav" id="img-modal-next" onclick="imgStep(1)" aria-label="Next">&#8250;</button>\n'
        '    <div id="img-modal-spinner"></div>\n'
        '    <img id="img-modal-img" src="" alt="Photograph by N C Mohan">\n'
        '    <canvas id="lb-canvas" style="display:none"></canvas>\n'
        '  </div>\n'
        '  <div class="img-modal-panel">\n'
        '    <div class="img-modal-info">\n'
        '      <div class="img-modal-counter" id="img-modal-counter"></div>\n'
        '      <div class="img-modal-title" id="img-modal-title"></div>\n'
        '      <div class="img-modal-subtitle" id="img-modal-subtitle"></div>\n'
        '    </div>\n'
        '    <div class="img-modal-actions">\n'
        '      <button class="img-modal-like" id="img-modal-like-btn" onclick="imgModalToggleLike()">\n'
        '        <span class="like-heart">&#10084;</span> Like\n'
        '        <span class="like-count" id="img-modal-like-count"></span>\n'
        '      </button>\n'
        '      <button class="img-modal-rq" onclick="openRqModal()">Request Quote</button>\n'
        '    </div>\n'
        '    <div class="img-modal-copyright">&copy; N C Mohan &middot; All rights reserved</div>\n'
        '  </div>\n'
        '</div>\n\n'

        # ── REQUEST QUOTE MODAL ───────────────────────────────────────────────────
        '<div id="rq-modal" role="dialog" aria-modal="true">\n'
        '  <div id="rq-box">\n'
        '    <button class="rq-back" onclick="closeRqModal()">&#8249; Back to photo</button>\n'
        '    <div class="rq-title">Request a Quote</div>\n'
        '    <div class="rq-steps">\n'
        '      <div class="rq-step active" id="rq-st1"><span class="rq-step-num">1</span> Select Size</div>\n'
        '      <div class="rq-step-sep"></div>\n'
        '      <div class="rq-step" id="rq-st2"><span class="rq-step-num">2</span> Contact Details</div>\n'
        '    </div>\n'
        '    <div id="rq-step1">\n'
        '      <p style="font-size:10px;letter-spacing:2px;color:rgba(255,255,255,0.4);text-transform:uppercase;margin-bottom:16px">Choose a print size:</p>\n'
        '      <div class="rq-size-grid">\n'
        + ''.join(
            '<div class="rq-size-card" onclick="rqSelectSize(' + chr(39) + s.get('size','') + chr(39) + ', this)">'
            '<div class="rq-size-name">' + s.get('size','') + '</div>'
            '<div class="rq-size-dims">' + s.get('dimensions','') + '</div>'
            '</div>\n'
            for s in c_prints.get('sizes', [
                {'size':'A4','dimensions':'210 × 297 mm | 8.3 × 11.7 in'},
                {'size':'A3','dimensions':'297 × 420 mm | 11.7 × 16.5 in'},
                {'size':'A2','dimensions':'420 × 594 mm | 16.5 × 23.4 in'},
                {'size':'A1','dimensions':'594 × 841 mm | 23.4 × 33.1 in'},
            ])
        ) +
        '      </div>\n'
        '      <div style="display:flex;justify-content:flex-end;margin-top:20px">\n'
        '        <button class="btn-gold" onclick="rqNext()">Next &#8250;</button>\n'
        '      </div>\n'
        '    </div>\n'
        '    <div id="rq-step2" style="display:none">\n'
        '      <div class="rq-field"><label>Your Name *</label><input id="rq-name" type="text" placeholder="Full name"></div>\n'
        '      <div class="rq-field"><label>Email Address *</label><input id="rq-email" type="email" placeholder="you@example.com"></div>\n'
        '      <div class="rq-field"><label>Additional Notes</label><textarea id="rq-notes" placeholder="Any special requirements..."></textarea></div>\n'
        '      <div style="display:flex;gap:10px;justify-content:flex-end;margin-top:20px">\n'
        '        <button class="btn-ghost" onclick="rqBack()">&#8249; Back</button>\n'
        '        <button class="btn-gold" onclick="rqSubmit()">Send Request</button>\n'
        '      </div>\n'
        '    </div>\n'
        '  </div>\n'
        '</div>\n\n'

        # ── CONTEXT MENU ─────────────────────────────────────────────────────
        '<div id="ctx-menu">\n'
        '  <div class="ctx-item" onclick="ctxLike()">&#10084;&nbsp; Like</div>\n'
        '  <div class="ctx-divider"></div>\n'
        '  <div class="ctx-item" onclick="ctxBuy()">&#9998;&nbsp; Request Quote</div>\n'
        '  <div class="ctx-divider"></div>\n'
        '  <div class="ctx-item ctx-admin" id="ctx-admin-item" onclick="ctxAdminEdit()">&#9881;&nbsp; Edit tags</div>\n'
        '</div>\n\n'

        # ── ADMIN MODAL ──────────────────────────────────────────────────────
        # ── NOTIFICATION PANEL ────────────────────────────────────────────────
        '<div id="notify-panel">\n'
        '  <div id="notify-box">\n'
        '    <button class="notify-close" onclick="closeNotifyPanel()" aria-label="Close">&#x2715;</button>\n'
        '    <div class="notify-title" id="notify-panel-title">Blog Notification</div>\n'
        '    <div class="notify-sub">Send email to all subscribers</div>\n'
        '    <div id="notify-blog-row">\n'
        '      <select class="notify-select" id="notify-post-select">\n'
        '        <option value="">-- Select a blog post --</option>\n'
        '      </select>\n'
        '    </div>\n'
        '    <div class="notify-btn-row">\n'
        '      <button class="notify-btn" id="notify-test-btn" onclick="notifyBlogTest()">&#9993; Send Test Email</button>\n'
        '      <button class="notify-btn" id="notify-send-btn" onclick="notifyBlogConfirm()">&#9654; Notify All Subscribers</button>\n'
        '    </div>\n'
        '    <div class="notify-status" id="notify-status"></div>\n'
        '    <div style="text-align:right;margin-top:16px">\n'
        '      <button class="notify-btn-ghost" onclick="closeNotifyPanel()">Close</button>\n'
        '    </div>\n'
        '  </div>\n'
        '</div>\n\n'

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
        '    <!-- Choice screen: shown after password unlock -->\n'
        '    <div id="admin-choice-screen" style="display:none">\n'
        '      <p style="font-size:9px;letter-spacing:3px;text-transform:uppercase;color:rgba(255,255,255,0.4);margin-bottom:20px">Select an action:</p>\n'
        '      <div style="display:flex;flex-direction:column;gap:12px">\n'
        '        <button class="btn-gold" style="width:100%;height:44px" onclick="adminOpenTagEditor()">&#9998;&nbsp; Edit Tags</button>\n'
        '        <button class="btn-gold" style="width:100%;height:44px" onclick="closeAdminModal();openNotifyPanel(\'blog\')">&#9993;&nbsp; Blog Notification</button>\n'
        '        <button class="btn-gold" style="width:100%;height:44px" onclick="closeAdminModal();openNotifyPanel(\'photos\')">&#128247;&nbsp; Photo Notification</button>\n'
        '      </div>\n'
        '      <div style="text-align:right;margin-top:20px">\n'
        '        <button class="btn-ghost" onclick="closeAdminModal()">Close</button>\n'
        '      </div>\n'
        '    </div>\n'
        '    <!-- Edit Tags screen -->\n'
        '    <div id="admin-edit-screen" style="display:none">\n'
        '      <div style="font-size:8px;color:rgba(255,255,255,0.3);letter-spacing:1px;margin-bottom:6px" id="admin-photo-ref"></div>\n'
        '      <div style="font-size:8px;color:var(--gold);letter-spacing:1px;margin-bottom:14px" id="admin-count"></div>\n'
        '      <div class="admin-field"><label>Categories (tap to toggle)</label><div class="admin-cats" id="admin-cats"></div></div>\n'
        '      <div class="admin-field"><label>State / Country</label><input id="admin-state" type="text" placeholder="e.g. Karnataka"></div>\n'
        '      <div class="admin-field"><label>City</label><input id="admin-city" type="text" placeholder="e.g. Badami"></div>\n'
        '      <div class="admin-field"><label>Remarks</label><textarea id="admin-remarks" placeholder="e.g. Great Hornbill in flight"></textarea></div>\n'
        '      <p class="admin-note">Run patch_tags.py on your Mac first, then Save will update photo_metadata.json automatically.</p>\n'
        '      <div class="admin-row">\n'
        '        <button class="btn-ghost" onclick="adminBackToChoice()">&#8249; Back</button>\n'
        '        <button class="btn-gold" onclick="saveAdminTags()">Save</button>\n'
        '      </div>\n'
        '    </div>\n'
        '  </div>\n'
        '</div>\n\n'

        # Lightbox removed — replaced by img-modal
# ── SUBSCRIBE SECTION ────────────────────────────────────────────────
        '<section id="subscribe-section">\n'
        '  <div class="subscribe-inner">\n'
        '    <div class="subscribe-title">Stay in the Loop</div>\n'
        '    <div class="subscribe-subtitle">Be the first to know when new photographs are added</div>\n'
        '    <div class="subscribe-form">\n'
        '      <input type="text" id="sub-name" placeholder="Your Name (optional)">\n'
        '      <input type="email" id="sub-email" placeholder="Your Email Address *">\n'
        '      <button onclick="subscribeVisitor()">Notify Me</button>\n'
        '    </div>\n'
        '    <div id="subscribe-msg"></div>\n'
        '  </div>\n'
        '</section>\n\n'
        # ── COPYRIGHT BANNER ─────────────────────────────────────────────────
        '<div id="copyright-banner">\n'
        '  &copy; All photographs are the exclusive property of N C Mohan and are protected under copyright law.'
        ' &middot; Reproduction or use without prior written permission is strictly prohibited.\n'
        '</div>\n\n'

        # ── FOOTER — scrollable, rich, contains Licensing + Legal ────────────
        '<footer>\n'
        '  <div class="footer-inner">\n'

        # Licensing section
        '    <div class="footer-section">\n'
        '      <div class="footer-section-title">Licensing</div>\n'
        '      <div class="footer-section-body">\n'
        + render_paragraphs(c_licens.get('paragraphs', [
            'All photographs are available for commercial and editorial licensing.',
            'Please <a href="#" onclick="showInfoPage(\'page-contact\'); return false;" style="color:var(--gold)">get in touch</a> to discuss usage rights and pricing.'
        ])) +
        '      </div>\n'
        '    </div>\n'

        # Copyright & Legal section
        '    <div class="footer-section">\n'
        '      <div class="footer-section-title">Copyright &amp; Legal</div>\n'
        '      <div class="footer-section-body">\n'
        + render_items(c_legal.get('items', [
            {'heading': 'Copyright', 'detail': 'All photographs &copy; N C Mohan. All rights reserved. Reproduction or use without prior written permission is strictly prohibited.'},
            {'heading': 'Usage', 'detail': 'Personal, non-commercial viewing is permitted. Any other use requires a written licence agreement.'}
        ])) +
        '      </div>\n'
        '    </div>\n'

        '    <div class="footer-copy">&copy; ' + photographer + ' &middot; All rights reserved &middot; Mohangraphy<span id="visit-count"></span></div>\n'
        '  </div>\n'
        '</footer>\n\n'

        '<!-- SLIDESHOW OVERLAY -->\n'
        '<div id="ss-overlay" role="dialog" aria-modal="true">\n'
        '  <div id="ss-img-wrap">\n'
        '    <img id="ss-img" src="" alt="">\n'
        '    <button class="ss-nav-btn" id="ss-prev" onclick="ssPrev()" aria-label="Previous">&#8249;</button>\n'
        '    <button class="ss-nav-btn" id="ss-next" onclick="ssNext()" aria-label="Next">&#8250;</button>\n'
        '    <button id="ss-close" onclick="ssClose()" aria-label="Close">&#x2715;</button>\n'
        '    <div id="ss-pause-lbl">PAUSED</div>\n'
        '  </div>\n'
        '  <div id="ss-bar">\n'
        '    <span id="ss-counter"></span>\n'
        '    <span id="ss-caption"></span>\n'
        '    <span id="ss-hint">Tap photo to pause</span>\n'
        '    <div id="ss-progress"></div>\n'
        '  </div>\n'
        '</div>\n\n'

        '<script>\nwindow.MOHAN_CONFIG=' + _config_json + ';\n</script>\n'
        '<script src="mohangraphy.js"></script>\n'
        '</body>\n'
        '</html>'
    )


    # Write CNAME file — tells GitHub Pages to serve on custom domain
    cname_path = os.path.join(ROOT_DIR, "CNAME")
    with open(cname_path, "w") as f:
        f.write("www.mohangraphy.com")

    out_path = os.path.join(ROOT_DIR, "index.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    js_out_path = os.path.join(ROOT_DIR, "mohangraphy.js")
    with open(js_out_path, "w", encoding="utf-8") as f:
        f.write(_MOHAN_JS)
    print(f"  ✅ mohangraphy.js written → {js_out_path}")

    print("=" * 55)
    print("BUILD COMPLETE")
    print("  Output       : " + out_path)
    print("  Unique photos: " + str(len(unique)))
    total_cats = {cat: sum(len(ps) for region in ['India','Overseas']
                  for top in cat_city_map.get(cat,{}).get(region,{}).values()
                  for ps in (top.values() if isinstance(top,dict) else [top]))
                  for cat in CAT_ORDER}
    for cat, cnt in total_cats.items():
        print(f"  {cat:<20}: {cnt} photos")
    print("  Hero slides  : " + str(len(hero_slides)) + " (Megamalai, 3s rotation)")
    print("=" * 55)

def clean_metadata():
    """
    Remove entries from photo_metadata.json whose source file no longer
    exists on disk. Runs automatically before every build.
    Returns the number of entries removed.
    """
    if not os.path.exists(DATA_FILE):
        return 0
    with open(DATA_FILE, 'r') as f:
        try:
            data = json.load(f)
        except Exception:
            return 0

    removed = []
    cleaned = {}
    for key, info in data.items():
        rel_path = info.get('path', '').strip()
        if not rel_path:
            cleaned[key] = info   # keep entries with no path (safety)
            continue
        full_path = os.path.join(ROOT_DIR, rel_path)
        if os.path.exists(full_path):
            cleaned[key] = info
        else:
            removed.append(rel_path)

    if removed:
        with open(DATA_FILE, 'w') as f:
            json.dump(cleaned, f, indent=2)
        print(f"  🗑  Cleaned {len(removed)} deleted photo(s) from photo_metadata.json:")
        for r in removed:
            print(f"       - {r}")
    else:
        print(f"  ✅ photo_metadata.json is clean — no deleted photos found")

    return len(removed)


def git_deploy():
    """
    Stage all changes, commit with a timestamp, and push to GitHub.
    Runs automatically after every build.
    """
    import datetime
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    def run(cmd, cwd=ROOT_DIR):
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
        return result.returncode, result.stdout.strip(), result.stderr.strip()

    print()
    print("─" * 55)
    print("DEPLOYING TO GITHUB...")
    print("─" * 55)

    # git add everything
    code, out, err = run(["git", "add", "-A"])
    if code != 0:
        print(f"  ❌ git add failed: {err}")
        return

    # Check if there's actually anything to commit
    code, out, err = run(["git", "status", "--porcelain"])
    if not out.strip():
        print("  ✅ Nothing new to deploy — GitHub is already up to date.")
        return

    # Count changed files for the commit message
    changed = [l for l in out.splitlines() if l.strip()]
    msg = f"Deploy {stamp} — {len(changed)} file(s) updated"

    code, out, err = run(["git", "commit", "-m", msg])
    if code != 0:
        print(f"  ❌ git commit failed: {err}")
        return
    print(f"  ✅ Committed: {msg}")

    # Pull remote changes first so push is never rejected
    code, out, err = run(["git", "pull", "--rebase"])
    if code != 0:
        print(f"  ❌ git pull failed: {err}")
        print(f"     Run: git pull --rebase  then try again.")
        return

    code, out, err = run(["git", "push"])
    if code != 0:
        print(f"  ❌ git push failed: {err}")
        print(f"     {err}")
        return
    print(f"  ✅ Pushed to GitHub successfully!")
    print(f"  🌐 Live in ~30 seconds at: https://www.mohangraphy.com")
    print("─" * 55)



if __name__ == "__main__":
    print("=" * 55)
    print("MOHANGRAPHY DEPLOY")
    print("=" * 55)
    print()
    print("Step 1 — Checking for deleted photos...")
    clean_metadata()
    print()
    print("Step 2 — Building site...")
    generate_html()
    print()
    print("Step 3 — Deploying to GitHub...")
    git_deploy()

