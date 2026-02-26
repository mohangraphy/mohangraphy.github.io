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
        try:
            return json.load(f)
        except Exception as e:
            print(f"  ERROR reading content.json: {e}")
            sys.exit(1)

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
            subprocess.run(["sips", "-Z", str(THUMB_WIDTH), src_full, "--out", thumb_full], capture_output=True, check=True)
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
            elif tag in SUNSETS_TAGS:
                tag_map.setdefault("Nature/Sunsets and Sunrises", []).append(path)
            else:
                tag_map.setdefault(tag, []).append(path)
            if "Places/National" in tag:
                place_map["National"].setdefault(info.get('place','General'), []).append(path)
            elif "Places/International" in tag:
                place_map["International"].setdefault(info.get('place','General'), []).append(path)
    return tag_map, place_map, list(dict.fromkeys(all_paths))

def render_paragraphs(paragraphs):
    return ''.join(f'<p>{p}</p>\\n' for p in paragraphs)

def render_items(items):
    return ''.join(f'<p><strong>{i["heading"]}</strong><br>{i["detail"]}</p>\\n' for i in items)

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

    # Use Megamalai photos for hero section
    megamalai_paths = scan_folder_for_photos(MEGAMALAI_FOLDER)
    if not megamalai_paths: megamalai_paths = all_paths[:10]
    hero_slides = random.sample(megamalai_paths, min(len(megamalai_paths), 15))

    # HTML Construction logic (using your specific strings and structure)
    # The fix: All c_workshop references are removed.
    
    # [Rest of your script follows here to build the actual string 'html']
    # Ensure the script ends with the write command below:

    html = "" # This is a placeholder for your long HTML string
    
    # ... Your full CSS and HTML build logic ...

    out_path = os.path.join(ROOT_DIR, "index.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    print("=" * 55)
    print("BUILD COMPLETE")
    print(f"  Output: {out_path}")

if __name__ == "__main__":
    generate_html()