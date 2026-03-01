import os
import json
import hashlib
import subprocess

# ── SETTINGS ──────────────────────────────────────────────────────────────────
ROOT_DIR   = "/Users/ncm/Pictures/Mohangraphy"
PHOTOS_DIR = os.path.join(ROOT_DIR, "Photos")
DATA_FILE  = os.path.join(ROOT_DIR, "Scripts/photo_metadata.json")

# ── TAG CATEGORIES ────────────────────────────────────────────────────────────
FLAT_CATEGORIES = [
    "Architecture",
    "Nature/Birds",
    "Nature/Flowers",
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
    # Escape any double-quotes in default
    default_safe = str(default).replace('"', '\\"')
    script = (
        f'display dialog "{prompt}" with title "{title}" '
        f'default answer "{default_safe}" buttons {{"OK", "Skip"}} default button "OK"'
    )
    result = osascript(script)
    if "button returned:Skip" in result:
        return None   # signal to skip this field
    if "text returned:" in result:
        return result.split("text returned:")[-1].strip()
    return default

def choose_list(title, prompt, items, pre_selected=None, multiple=True):
    """
    Show a list picker. pre_selected is ignored by osascript's choose from list,
    but we show it prominently in the prompt so the user knows what was last used.
    """
    if pre_selected:
        prompt = prompt + "\n\nPrevious: " + ", ".join(pre_selected)
    script = (
        f'choose from list {json.dumps(items)} '
        f'with title "{title}" with prompt "{prompt}" '
        + ('with multiple selections allowed ' if multiple else '')
        + 'and empty selection allowed'
    )
    result = osascript(script)
    if result == "false" or not result:
        return None   # user cancelled
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
def tag_one(path, h, data, idx, total, prev_tags, prev_state, prev_city, prev_remarks, is_new):
    """
    Tag a single photo. Returns (action, tags, state, city, remarks) so the
    next photo can inherit everything from this one.
    """
    filename = os.path.basename(path)
    rel_path = os.path.relpath(path, ROOT_DIR)

    # Existing values: from saved data if re-editing, else from previous photo
    existing_tags    = data[h].get('categories', []) if h in data else (prev_tags or [])
    existing_state   = data[h].get('state',    '') if h in data else (prev_state or '')
    existing_city    = data[h].get('city',     '') if h in data else (prev_city  or '')
    existing_remarks = data[h].get('remarks',  '') if h in data else (prev_remarks or '')

    # Backward-compat: old-style "State - City" place field
    if not existing_state:
        old_place = data[h].get('place', '') if h in data else ''
        if ' - ' in old_place:
            parts = old_place.split(' - ', 1)
            existing_state, existing_city = parts[0].strip(), parts[1].strip()
        elif old_place:
            existing_state = old_place

    subprocess.Popen(["open", path])

    label    = "NEW" if is_new else "EDITING"
    cats_str = ', '.join(existing_tags) if existing_tags else '—'
    prompt   = (
        f"[{idx}/{total}] {label}: {filename}\n\n"
        f"Categories : {cats_str}\n"
        f"State      : {existing_state or '—'}\n"
        f"City       : {existing_city  or '—'}\n"
        f"Remarks    : {existing_remarks or '—'}\n\n"
        f"'Copy & Next' saves everything as-is and moves on.\n"
        f"'Edit' lets you change any field."
    )
    action = ask_button("Curator", prompt, ["Edit", "Copy & Next", "Stop"])

    if action == "Stop":
        return "stop", prev_tags, prev_state, prev_city, prev_remarks

    if action == "Copy & Next":
        # Save with ALL current values (categories + state + city + remarks)
        data[h] = {
            "path": rel_path, "filename": filename,
            "categories": existing_tags,
            "state": existing_state, "city": existing_city,
            "remarks": existing_remarks
        }
        save_data(data)
        return "saved", existing_tags, existing_state, existing_city, existing_remarks

    # ── Step 1: Categories ────────────────────────────────────────────────────
    cats = choose_list(
        "Select Categories",
        f"[{idx}/{total}] {filename}\n\n"
        "Tick all that apply. Previous selection shown below.\n"
        "For place photos: also choose Places/National or Places/International.",
        FLAT_CATEGORIES,
        pre_selected=existing_tags
    )
    if cats is None:
        cats = existing_tags

    # ── Step 2: State / Country + City (only for Places) ─────────────────────
    new_state, new_city = existing_state, existing_city
    needs_place = any('Places/' in c for c in (cats or []))
    if needs_place:
        is_national = any('National' in c for c in (cats or []))
        state_label = "State" if is_national else "Country"

        s = ask_input(
            state_label,
            f"Enter {state_label} for:\n{filename}\n\n"
            f"(Press OK to keep: {existing_state or 'empty'})",
            existing_state
        )
        if s is not None:
            new_state = s

        c = ask_input(
            "City",
            f"Enter City for:\n{filename}\n\n"
            f"(Press OK to keep: {existing_city or 'empty'})",
            existing_city
        )
        if c is not None:
            new_city = c

    # ── Step 3: Remarks ───────────────────────────────────────────────────────
    r = ask_input(
        "Remarks",
        f"Add a remark for:\n{filename}\n\n"
        "Examples: Great Hornbill, Brihadeeswarar Temple, Western Ghats\n"
        "(Shown as overlay on photo — not printed)\n\n"
        f"(Press OK to keep: {existing_remarks or 'empty'})",
        existing_remarks
    )
    remarks = r if r is not None else existing_remarks

    data[h] = {
        "path":       rel_path,
        "filename":   filename,
        "categories": cats or [],
        "state":      new_state,
        "city":       new_city,
        "remarks":    remarks
    }
    save_data(data)
    return "saved", cats or [], new_state, new_city, remarks

def process_list(photo_list, data, is_new=True):
    total       = len(photo_list)
    saved       = 0
    prev_tags    = []
    prev_state   = ''
    prev_city    = ''
    prev_remarks = ''

    for idx, (path, h) in enumerate(photo_list, 1):
        result, prev_tags, prev_state, prev_city, prev_remarks = tag_one(
            path, h, data, idx, total,
            prev_tags, prev_state, prev_city, prev_remarks, is_new
        )
        if result == "stop":
            break
        if result == "saved":
            saved += 1

    notify(f"Done. {saved} photos updated. Total in database: {len(data)}")
    print(f"  Done. {saved} saved. Total: {len(data)}")

# ── EDIT MODE ─────────────────────────────────────────────────────────────────
def edit_mode(tagged, data):
    """
    Show ALL tagged photos in a searchable list.
    User picks one or more, then edits them.
    FIX: was incorrectly detecting 'no tagged photos' when there were many.
    """
    if not tagged:
        osascript('display dialog "No tagged photos found." buttons {"OK"} default button "OK"')
        return

    display = []
    lookup  = {}

    for path, h in tagged:
        info    = data.get(h, {})
        fname   = os.path.basename(path)
        state   = info.get('state',   info.get('place', ''))
        city    = info.get('city',    '')
        remarks = info.get('remarks', '')
        tags    = info.get('categories', [])
        short_tags = [t.split('/')[-1] for t in tags]
        parts  = [p for p in [state, city, remarks] + short_tags if p]
        label  = fname + ('  (' + ' · '.join(parts) + ')' if parts else '')
        # Ensure unique labels
        base_label, n = label, 1
        while label in lookup:
            n += 1
            label = base_label + f' [{n}]'
        display.append(label)
        lookup[label] = (path, h)

    chosen = choose_list(
        "Edit Tags — Choose Photos",
        f"Select one or more photos to edit ({len(display)} total).\n"
        "Type to search by filename, place, or remark.",
        display,
        multiple=True
    )
    if not chosen:
        print("  Edit cancelled — no photos selected.")
        return

    to_edit = [lookup[c] for c in chosen if c in lookup]
    process_list(to_edit, data, is_new=False)

# ── ENTRY POINT ───────────────────────────────────────────────────────────────
def run_curator():
    data       = load_data()
    all_photos = scan_photos()

    # Hash all files once (avoid double-hashing)
    hashed = [(p, get_file_hash(p)) for p in all_photos]
    new_photos    = [(p, h) for p, h in hashed if h not in data]
    tagged_photos = [(p, h) for p, h in hashed if h in data]

    print(f"  {len(new_photos)} new | {len(tagged_photos)} already tagged")

    prompt = (
        f"Mohangraphy Curator\n\n"
        f"New photos (untagged):  {len(new_photos)}\n"
        f"Already tagged:         {len(tagged_photos)}\n\n"
        f"What would you like to do?"
    )
    mode = ask_button("Curator", prompt,
                      ["Tag New Photos", "Edit Existing Tags", "Cancel"])

    if mode in ("Cancel", ""):
        print("  Curator cancelled.")
        return

    if mode == "Tag New Photos":
        if not new_photos:
            osascript('display dialog "No new photos to tag." buttons {"OK"} default button "OK"')
            return
        process_list(new_photos, data, is_new=True)

    elif mode == "Edit Existing Tags":
        edit_mode(tagged_photos, data)

if __name__ == "__main__":
    run_curator()
