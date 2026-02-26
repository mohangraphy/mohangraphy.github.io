import os
import json
import hashlib
import subprocess

# ── SETTINGS ──────────────────────────────────────────────────────────────────
ROOT_DIR   = "/Users/ncm/Pictures/Mohangraphy"
PHOTOS_DIR = os.path.join(ROOT_DIR, "Photos")
DATA_FILE  = os.path.join(ROOT_DIR, "Scripts/photo_metadata.json")

# ── TAG CATEGORIES ────────────────────────────────────────────────────────────
# HOW PLACES WORK:
#   Step 1 — Select the CATEGORY: Places/National or Places/International
#   Step 2 — Enter the PLACE NAME (e.g. "Megamalai", "Paris")
#   The category puts the photo in the right section of the site.
#   The place name creates its own named sub-gallery within that section.
#   There is NO separate standalone "Place" category — it works as a pair.
FLAT_CATEGORIES = [
    "Architecture",
    "Birds",
    "Flowers",
    "Nature/Landscape",
    "Nature/Landscape/Mountains",
    "Nature/Sunsets",
    "Nature/Wildlife",
    "People/Portraits",
    "Places/International",
    "Places/National",
]

# ── HELPERS ───────────────────────────────────────────────────────────────────
def get_file_hash(filepath):
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def osascript(script):
    proc = subprocess.Popen(
        ['osascript', '-e', script],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    out, _ = proc.communicate()
    return out.decode('utf-8').strip()

def ask_input(title, prompt, default=""):
    script = (
        f'display dialog "{prompt}" with title "{title}" '
        f'default answer "{default}" buttons {{"OK"}} default button "OK"'
    )
    result = osascript(script)
    if "text returned:" in result:
        return result.split("text returned:")[-1].strip()
    return default

def choose_list(title, prompt, items, multiple=True):
    script = (
        f'choose from list {json.dumps(items)} '
        f'with title "{title}" with prompt "{prompt}" '
        + ('with multiple selections allowed ' if multiple else '')
        + 'and empty selection allowed'
    )
    result = osascript(script)
    if result == "false" or not result:
        return []
    return [x.strip() for x in result.split(',')]

def ask_button(title, prompt, buttons):
    btn_str = '", "'.join(buttons)
    script = (
        f'display dialog "{prompt}" with title "{title}" '
        f'buttons {{"{btn_str}"}} default button "{buttons[0]}"'
    )
    result = osascript(script)
    return result.split("button returned:")[-1].strip()

def notify(msg):
    subprocess.run(['osascript', '-e',
        f'display notification "{msg}" with title "Mohangraphy Curator"'])

# ── DATA ──────────────────────────────────────────────────────────────────────
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, 'r') as f:
        raw = json.load(f)
    # Deduplicate: one entry per unique file path, re-keyed by hash
    by_path = {}
    for _, info in raw.items():
        p = info.get('path', '')
        if p:
            by_path[p] = info
    final = {}
    for path, info in by_path.items():
        full = os.path.join(ROOT_DIR, path)
        if os.path.exists(full):
            h = get_file_hash(full)
            final[h] = info
    print(f"  Loaded {len(final)} tagged photos.")
    return final

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def scan_photos():
    results = []
    for root, _, files in os.walk(PHOTOS_DIR):
        for f in sorted(files):
            if f.lower().endswith(('.jpg', '.jpeg', '.png')) and not f.startswith('.'):
                results.append(os.path.join(root, f))
    return results

# ── TAGGING ───────────────────────────────────────────────────────────────────
def tag_one(path, h, data, idx, total, is_new):
    filename = os.path.basename(path)
    rel_path = os.path.relpath(path, ROOT_DIR)

    existing_tags  = data[h].get('categories', []) if h in data else []
    existing_place = data[h].get('place',      '')  if h in data else ''
    existing_rem   = data[h].get('remarks',    '')  if h in data else ''

    subprocess.Popen(["open", path])   # open photo preview

    label  = "NEW" if is_new else "EDITING"
    prompt = (
        f"[{idx}/{total}] {label}: {filename}\n\n"
        f"Current tags:    {', '.join(existing_tags) or 'None'}\n"
        f"Current place:   {existing_place or '—'}\n"
        f"Current remarks: {existing_rem or '—'}"
    )
    action = ask_button("Curator", prompt, ["Tag / Edit", "Skip", "Stop"])

    if action == "Stop":  return "stop"
    if action == "Skip":  return "skip"

    # Step 1 — Categories
    cats = choose_list(
        "Select Categories",
        f"[{idx}/{total}] {filename}\n\n"
        "Tick all categories that apply.\n"
        "For place photos: choose Places/National or Places/International,\n"
        "then you will be asked for the place name on the next screen.",
        FLAT_CATEGORIES
    )

    # Step 2 — Place name (only if a Places/* category was chosen)
    place = existing_place
    if any('Places/' in c for c in cats):
        place = ask_input(
            "Place Name",
            f"Enter the PLACE NAME for:\n{filename}\n\n"
            "Examples: Megamalai, Hampi, Munnar, Paris, New York\n\n"
            "This name will appear as its own gallery on the website.",
            existing_place
        )

    # Step 3 — Remarks
    remarks = ask_input(
        "Remarks",
        f"Add a REMARK for:\n{filename}\n\n"
        "Use this for the subject name — bird species, temple name,\n"
        "mountain range, festival name, etc.\n\n"
        "Examples: Great Hornbill, Brihadeeswarar Temple, Western Ghats\n\n"
        "This will be shown as a subtle label on the photo in the gallery.\n"
        "It does NOT appear on downloads or prints.",
        existing_rem
    )

    data[h] = {
        "path":       rel_path,
        "filename":   filename,
        "categories": cats,
        "place":      place,
        "remarks":    remarks
    }
    save_data(data)
    return "saved"

def process_list(photo_list, data, is_new=True):
    total, saved = len(photo_list), 0
    for idx, (path, h) in enumerate(photo_list, 1):
        result = tag_one(path, h, data, idx, total, is_new)
        if result == "stop": break
        if result == "saved": saved += 1
    notify(f"Done. {saved} photos updated. Total in database: {len(data)}")
    print(f"  Done. {saved} saved. Total: {len(data)}")

# ── EDIT MODE — searchable list ───────────────────────────────────────────────
def edit_mode(tagged, data):
    """
    Instead of scrolling photo by photo, the user picks from a searchable list.
    Each item shows:  filename  (Place · Remarks · tags)
    Type any part of the name, place, or remark to filter the list.
    """
    display = []
    lookup  = {}
    for path, h in tagged:
        info    = data.get(h, {})
        fname   = os.path.basename(path)
        place   = info.get('place',   '')
        remarks = info.get('remarks', '')
        tags    = info.get('categories', [])
        # Shorten tag names for display
        short_tags = [t.split('/')[-1] for t in tags]
        parts = [p for p in [place, remarks] + short_tags if p]
        label = fname + ('  (' + ' · '.join(parts) + ')' if parts else '')
        display.append(label)
        lookup[label] = (path, h)

    chosen = choose_list(
        "Edit Tags — Choose Photos",
        "Select one or more photos to edit.\n"
        "Scroll or start typing to search by filename, place, or remark.",
        display,
        multiple=True
    )
    if not chosen:
        return
    to_edit = [lookup[c] for c in chosen if c in lookup]
    process_list(to_edit, data, is_new=False)

# ── ENTRY POINT ───────────────────────────────────────────────────────────────
def run_curator():
    data       = load_data()
    all_photos = scan_photos()

    new_photos    = [(p, get_file_hash(p)) for p in all_photos
                     if get_file_hash(p) not in data]
    tagged_photos = [(p, get_file_hash(p)) for p in all_photos
                     if get_file_hash(p) in data]

    print(f"  {len(new_photos)} new | {len(tagged_photos)} tagged")

    prompt = (
        f"Mohangraphy Curator\n\n"
        f"New photos (untagged):  {len(new_photos)}\n"
        f"Already tagged:         {len(tagged_photos)}\n\n"
        f"What would you like to do?"
    )
    mode = ask_button("Curator", prompt,
                      ["Tag New Photos", "Edit Existing Tags", "Cancel"])

    if mode in ("Cancel", ""):
        return
    if mode == "Tag New Photos":
        if not new_photos:
            osascript('display dialog "No new photos found." buttons {"OK"} default button "OK"')
            return
        process_list(new_photos, data, is_new=True)
    elif mode == "Edit Existing Tags":
        if not tagged_photos:
            osascript('display dialog "No tagged photos yet." buttons {"OK"} default button "OK"')
            return
        edit_mode(tagged_photos, data)

if __name__ == "__main__":
    run_curator()
