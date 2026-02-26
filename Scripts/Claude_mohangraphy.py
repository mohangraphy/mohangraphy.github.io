import os
import json
import random
import subprocess
import sys

# ── CONFIGURATION ─────────────────────────────────────────────────────────────
ROOT_DIR         = "/Users/ncm/Pictures/Mohangraphy"
DATA_FILE        = os.path.join(ROOT_DIR, "Scripts/photo_metadata.json")
CONTENT_FILE     = os.path.join(ROOT_DIR, "Scripts/content.json")
THUMBS_DIR       = os.path.join(ROOT_DIR, "Thumbs")
MEGAMALAI_FOLDER = os.path.join(ROOT_DIR, "Photos/Nature/Landscape/Megamalai")
THUMB_WIDTH      = 800

MANUAL_STRUCTURE = {
    "Places":       ["National", "International"],
    "Nature":       ["Landscape", "Sunsets and Sunrises", "Wildlife", "Mountains"],
    "People":       ["Portraits"],
    "Architecture": [],
    "Birds":        [],
    "Flowers":      []
}

TAG_OVERRIDES = {
    "Nature/Mountains":              "Nature/Landscape/Mountains",
    "Nature/Sunsets and Sunrises":   "Nature/Sunsets",
}

MOUNTAINS_TAGS = {"Nature/Landscape/Mountains", "Nature/Mountains"}
SUNSETS_TAGS   = {"Nature/Sunsets and Sunrises", "Nature/Sunsets"}

# ── HELPERS ───────────────────────────────────────────────────────────────────

def load_index():
    if not os.path.exists(DATA_FILE): return {}
    with open(DATA_FILE, 'r') as f:
        try: return json.load(f)
        except: return {}

def load_content():
    if not os.path.exists(CONTENT_FILE): return {}
    with open(CONTENT_FILE, 'r', encoding='utf-8') as f:
        try: return json.load(f)
        except Exception as e:
            print(f"  ERROR reading content.json: {e}")
            return {}

def deduplicate_by_path(raw_data):
    seen = {}
    for entry_id, info in raw_data.items():
        path = info.get('path', '').strip()
        if path and path not in seen: seen[path] = info
    return list(seen.values())

def scan_folder_for_photos(folder_path):
    paths = []
    if not os.path.isdir(folder_path): return paths
    for root, dirs, files in os.walk(folder_path):
        for f in sorted(files):
            if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                rel = os.path.relpath(os.path.join(root, f), ROOT_DIR)
                paths.append(rel)
    return paths

def make_thumb(rel_path):
    src_full = os.path.join(ROOT_DIR, rel_path)
    thumb_rel = os.path.join("Thumbs", rel_path)
    thumb_full = os.path.join(ROOT_DIR, thumb_rel)
    if not os.path.exists(thumb_full):
        os.makedirs(os.path.dirname(thumb_full), exist_ok=True)
        try:
            subprocess.run(["sips", "-Z", str(THUMB_WIDTH), src_full, "--out", thumb_full], 
                           capture_output=True, check=True)
        except: return rel_path
    return thumb_rel

def build_maps(unique_entries):
    tag_map = {}
    place_map = {"National": {}, "International": {}}
    all_paths = []
    for info in unique_entries:
        path = info.get('path', '')
        tags = info.get('categories', [])
        if not path: continue
        all_paths.append(path)
        for raw_tag in tags:
            tag = TAG_OVERRIDES.get(raw_tag, raw_tag)
            if tag in MOUNTAINS_TAGS:
                tag_map.setdefault("Nature/Mountains", []).append(path)
                tag_map.setdefault("Nature/Landscape", []).append(path)
            else:
                tag_map.setdefault(tag, []).append(path)
    return tag_map, place_map, list(dict.fromkeys(all_paths))

def render_paragraphs(paragraphs):
    if not paragraphs: return ""
    return ''.join(f'<p>{p}</p>\n' for p in paragraphs)

def render_items(items):
    if not items: return ""
    return ''.join(f'<p><strong>{i["heading"]}</strong><br>{i["detail"]}</p>\n' for i in items)

def generate_html():
    raw_data = load_index()
    unique = deduplicate_by_path(raw_data)
    tag_map, place_map, all_paths = build_maps(unique)
    
    C = load_content()
    site = C.get('site', {})
    c_about = C.get('about', {})
    c_phil = C.get('philosophy', {})
    c_gear = C.get('gear', {})
    c_contact = C.get('contact', {})
    c_prints = C.get('prints', {})
    c_licens = C.get('licensing', {})
    c_legal = C.get('legal', {})

    # Use Megamalai photos for cover
    megamalai_paths = scan_folder_for_photos(MEGAMALAI_FOLDER)
    if not megamalai_paths: megamalai_paths = all_paths[:10]
    hero_slides = random.sample(megamalai_paths, min(len(megamalai_paths), 15))

    # HTML Construction
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{site.get('title', 'MOHANGRAPHY')}</title>
    <style>
        body {{ font-family: sans-serif; background: #111; color: #eee; padding: 40px; line-height: 1.6; }}
        .container {{ max-width: 900px; margin: auto; }}
        h1 {{ color: #fff; border-bottom: 1px solid #333; padding-bottom: 10px; }}
        .section {{ margin-bottom: 40px; padding: 20px; background: #1a1a1a; border-radius: 8px; }}
        strong {{ color: #eec170; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{site.get('title')}</h1>
        <p><em>{site.get('tagline')}</em></p>

        <div class="section">
            <h2>{c_about.get('title')}</h2>
            {render_paragraphs(c_about.get('paragraphs', []))}
        </div>

        <div class="section">
            <h2>{c_gear.get('title')}</h2>
            {render_items(c_gear.get('items', []))}
        </div>

        <div class="section">
            <h2>{c_contact.get('title')}</h2>
            {render_paragraphs(c_contact.get('paragraphs', []))}
        </div>
    </div>
</body>
</html>"""

    out_path = os.path.join(ROOT_DIR, "index.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    print("=" * 55)
    print("✅ BUILD COMPLETE")
    print(f"  Output: {out_path}")

if __name__ == "__main__":
    generate_html()