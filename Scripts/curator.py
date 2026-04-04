import os
import json
import hashlib
import subprocess
import datetime

# --- SETTINGS ---
ROOT_DIR = "/Users/ncm/Pictures/Mohangraphy"
PHOTOS_DIR = os.path.join(ROOT_DIR, "Photos")
DATA_FILE = os.path.join(ROOT_DIR, "Scripts/photo_metadata.json")

FLAT_CATEGORIES = [
    "Nature/Landscapes",
    "Nature/Wildlife",
    "Nature/Birds",
    "Nature/Flora",
    "Places/National",
    "Places/International",
    "Architecture",
    "People & Culture",
]

# ── Helpers ───────────────────────────────────────────────────────────────────

def get_file_hash(filepath):
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def ask_input(title, prompt, default=""):
    safe_prompt  = str(prompt).replace('\\', '\\\\').replace('"', '\\"')
    safe_default = str(default).replace('\\', '\\\\').replace('"', '\\"')
    safe_title   = str(title).replace('\\', '\\\\').replace('"', '\\"')
    script = (
        f'display dialog "{safe_prompt}" with title "{safe_title}" '
        f'default answer "{safe_default}" '
        f'buttons {{"Cancel","OK"}} default button "OK"'
    )
    proc = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
    if proc.returncode != 0:
        return None
    out = proc.stdout.strip()
    if "text returned:" in out:
        return out.split("text returned:")[-1].strip()
    return ""

def ask_list(title, prompt, items):
    safe_prompt = str(prompt).replace('\\', '\\\\').replace('"', '\\"')
    safe_title  = str(title).replace('\\', '\\\\').replace('"', '\\"')
    script = (
        f'choose from list {json.dumps(items)} '
        f'with title "{safe_title}" with prompt "{safe_prompt}" '
        f'with multiple selections allowed and empty selection allowed'
    )
    proc = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
    result = proc.stdout.strip()
    if result == "false" or proc.returncode != 0:
        return None
    return [x.strip() for x in result.split(',') if x.strip()]

def ask_button(title, prompt, buttons, default=None):
    safe_prompt = str(prompt).replace('\\', '\\\\').replace('"', '\\"')
    safe_title  = str(title).replace('\\', '\\\\').replace('"', '\\"')
    default_btn = default or buttons[0]
    btn_str = ', '.join(f'"{b}"' for b in buttons)
    script = (
        f'display dialog "{safe_prompt}" with title "{safe_title}" '
        f'buttons {{{btn_str}}} default button "{default_btn}"'
    )
    proc = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
    if proc.returncode != 0:
        return None
    out = proc.stdout.strip()
    if "button returned:" in out:
        return out.split("button returned:")[-1].strip()
    return None

# ── Data ──────────────────────────────────────────────────────────────────────

def clean_and_load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, 'r') as f:
        raw_data = json.load(f)
    by_path = {}
    for _, info in raw_data.items():
        path = info.get('path')
        if path:
            by_path[path] = info
    final_data = {}
    for path, info in by_path.items():
        full_path = os.path.join(ROOT_DIR, path)
        if os.path.exists(full_path):
            h = get_file_hash(full_path)
            final_data[h] = info
    print(f"📊 Metadata loaded: {len(final_data)} unique photos.")
    return final_data

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# ── Main ──────────────────────────────────────────────────────────────────────

def run_curator():
    data = clean_and_load_data()

    disk_files = []
    for root, _, files in os.walk(PHOTOS_DIR):
        for f in sorted(files):
            if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                disk_files.append(os.path.join(root, f))

    total = len(disk_files)
    print(f"📷 Found {total} photos in {PHOTOS_DIR}")

    # carry-forward — remarks always blank, location/cats carry over
    prev = {
        "categories": [],
        "state":      "",
        "city":       "",
        "country":    "",
    }

    today = datetime.date.today().strftime('%Y-%m-%d')

    for idx, path in enumerate(disk_files, 1):
        f_hash   = get_file_hash(path)
        filename = os.path.basename(path)
        rel_path = os.path.relpath(path, ROOT_DIR)

        exists  = f_hash in data
        current = data[f_hash] if exists else {}

        cur_cats    = current.get('categories', [])
        cur_state   = current.get('state',   current.get('place', ''))
        cur_city    = current.get('city',    '')
        cur_country = current.get('country', '')
        cur_remarks = current.get('remarks', '')
        cur_date    = current.get('date_added', today)

        tag_summary = ', '.join(cur_cats) if cur_cats else '(none)'
        loc_summary = ' / '.join(x for x in [cur_state, cur_city, cur_country] if x) or '(none)'

        status_detail = (
            f"Photo {idx} of {total}  |  {'ALREADY TAGGED' if exists else 'NEW'}\n\n"
            f"Tags    : {tag_summary}\n"
            f"Location: {loc_summary}\n"
            f"Remarks : {cur_remarks or '(none)'}"
        )

        subprocess.Popen(["open", path])

        action = ask_button(
            f"Curator — {filename}",
            status_detail,
            ["Edit / Tag", "Skip", "Stop"],
            default="Skip" if exists else "Edit / Tag"
        )

        if action is None or action == "Stop":
            break
        if action == "Skip":
            if exists:
                prev["categories"] = cur_cats
                prev["state"]      = cur_state
                prev["city"]       = cur_city
                prev["country"]    = cur_country
            continue

        # ── STEP 1: Categories ─────────────────────────────────────────────
        default_cats = cur_cats if exists else prev["categories"]
        cats_hint    = ', '.join(default_cats) if default_cats else 'none'

        selected_cats = ask_list(
            "Categories",
            f"Select categories for: {filename}\nPrevious: {cats_hint}",
            FLAT_CATEGORIES
        )
        if selected_cats is None:
            selected_cats = default_cats

        # ── STEP 2: Location ───────────────────────────────────────────────
        def_state   = cur_state   if exists else prev["state"]
        def_city    = cur_city    if exists else prev["city"]
        def_country = cur_country if exists else prev["country"]

        is_intl = any("International" in c for c in selected_cats)

        if is_intl:
            country = ask_input("Country", "Country (e.g. Canada):", def_country)
            if country is None: country = def_country
            city = ask_input("City", "City (e.g. Banff):", def_city)
            if city is None: city = def_city
            state = ""
        else:
            state = ask_input("State", "State (e.g. Tamil Nadu):", def_state)
            if state is None: state = def_state
            city = ask_input("City / Place", "City or Place (e.g. Megamalai):", def_city)
            if city is None: city = def_city
            country = ""

        # ── STEP 3: Remarks — always blank default, never carried forward ──
        remarks = ask_input(
            "Remarks",
            "Remarks for this specific photo:\n(e.g. Great Hornbill in flight)\nLeave blank if none.",
            ""
        )
        if remarks is None: remarks = ""

        # ── STEP 4: Date added ─────────────────────────────────────────────
        selected_date = ask_input(
            "Date Added",
            "Date added to site (YYYY-MM-DD):",
            cur_date
        )
        if selected_date is None:
            selected_date = cur_date
        try:
            datetime.datetime.strptime(selected_date, '%Y-%m-%d')
        except ValueError:
            selected_date = today

        # ── Save ──────────────────────────────────────────────────────────
        data[f_hash] = {
            "path":       rel_path,
            "filename":   filename,
            "categories": selected_cats,
            "state":      state,
            "city":       city,
            "country":    country,
            "remarks":    remarks,
            "date_added": selected_date,
        }
        save_data(data)

        # ── Update carry-forward ───────────────────────────────────────────
        prev["categories"] = selected_cats
        prev["state"]      = state
        prev["city"]       = city
        prev["country"]    = country

        print(f"  ✅ {filename} | {', '.join(selected_cats)} | {state or country} / {city}")

    print(f"\n✅ Done. {len(data)} photos in database.")

if __name__ == "__main__":
    run_curator()
