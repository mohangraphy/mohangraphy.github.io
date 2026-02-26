import os
import json
import random
import subprocess

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
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, 'r') as f:
        try:
            return json.load(f)
        except Exception:
            return {}

def load_content():
    if not os.path.exists(CONTENT_FILE):
        return {}
    with open(CONTENT_FILE, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except Exception as e:
            print("  ERROR reading content.json: " + str(e))
            return {}

def deduplicate_by_path(raw_data):
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

def pick_cover(paths):
    return random.choice(paths) if paths else ""

def make_thumb(rel_path):
    src_full   = os.path.join(ROOT_DIR, rel_path)
    thumb_rel  = os.path.join("Thumbs", rel_path)
    thumb_full = os.path.join(ROOT_DIR, thumb_rel)
    if not os.path.exists(thumb_full):
        os.makedirs(os.path.dirname(thumb_full), exist_ok=True)
        try:
            subprocess.run(["sips", "-Z", str(THUMB_WIDTH), src_full, "--out", thumb_full], capture_output=True, check=True)
        except Exception:
            return rel_path
    return thumb_rel

def build_maps(unique_entries):
    tag_map   = {}
    place_map = {"National": {}, "International": {}}
    all_paths = []
    for info in unique_entries:
        path  = info.get('path', '')
        tags  = info.get('categories', [])
        place = info.get('place', 'General')
        if not path: continue
        all_paths.append(path)
        for raw_tag in tags:
            if raw_tag in MOUNTAINS_TAGS or raw_tag == "Nature/Landscape/Mountains":
                for t in ["Nature/Mountains", "Nature/Landscape"]:
                    tag_map.setdefault(t, [])
                    if path not in tag_map[t]: tag_map[t].append(path)
            elif raw_tag in SUNSETS_TAGS:
                tag_map.setdefault("Nature/Sunsets and Sunrises", []).append(path)
            else:
                tag_map.setdefault(raw_tag, [])
                if path not in tag_map[raw_tag]: tag_map[raw_tag].append(path)
            if "Places/National" in raw_tag:
                place_map["National"].setdefault(place, []).append(path)
            elif "Places/International" in raw_tag:
                place_map["International"].setdefault(place, []).append(path)
    return tag_map, place_map, list(dict.fromkeys(all_paths))

def get_display_paths(m_cat, s_cat, tag_map):
    if s_cat:
        disk_folder = os.path.join(ROOT_DIR, "Photos", m_cat, s_cat)
        disk_paths  = scan_folder_for_photos(disk_folder)
        if disk_paths: return disk_paths
    tag_key = m_cat + "/" + s_cat if s_cat else m_cat
    if s_cat == "Mountains":
        paths = []
        for t in ["Nature/Mountains", "Nature/Landscape/Mountains"]:
            for p in tag_map.get(t, []):
                if p not in paths: paths.append(p)
        return paths
    return list(dict.fromkeys(tag_map.get(tag_key, [])))

def ensure_thumbs(all_paths):
    print("  Generating thumbnails...")
    mapping = {p: make_thumb(p) for p in all_paths}
    return mapping

def render_paragraphs(paragraphs):
    return ''.join('<p>' + p + '</p>\n' for p in paragraphs)

def render_items(items):
    return ''.join('<p><strong>' + i['heading'] + '</strong><br>' + i['detail'] + '</p>\n' for i in items)

def generate_html():
    raw_data = load_index()
    unique   = deduplicate_by_path(raw_data)
    tag_map, place_map, all_paths = build_maps(unique)
    
    C = load_content()
    site       = C.get('site',       {})
    c_about    = C.get('about',      {})
    c_phil     = C.get('philosophy', {})
    c_gear     = C.get('gear',       {})
    c_contact  = C.get('contact',    {})
    c_prints   = C.get('prints',     {})
    c_licens   = C.get('licensing',  {})
    c_legal    = C.get('legal',      {})

    thumb_map = ensure_thumbs(all_paths)
    
    # Hero/Cover logic using your Megamalai data
    megamalai_paths = scan_folder_for_photos(MEGAMALAI_FOLDER)
    if not megamalai_paths: megamalai_paths = tag_map.get("Nature/Landscape", all_paths[:20])
    hero_slides = random.sample(megamalai_paths, min(len(megamalai_paths), 15))
    
    # Logic continues with your specific site titles and layout...
    print("BUILD COMPLETE")

if __name__ == "__main__":
    generate_html()