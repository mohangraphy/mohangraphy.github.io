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
    "Architecture", "Birds", "Flowers", 
    "Nature/Landscape", "Nature/Landscape/Mountains",
    "Nature/Sunsets", "Nature/Wildlife",
    "People/Portraits", "Places/International", "Places/National"
]

def get_file_hash(filepath):
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def ask_mac_input(title, prompt, default=""):
    applescript = f'display dialog "{prompt}" with title "{title}" default answer "{default}" buttons {{"OK"}} default button "OK"'
    proc = subprocess.Popen(['osascript', '-e', applescript], stdout=subprocess.PIPE)
    out, _ = proc.communicate()
    if "text returned:" in out.decode('utf-8'):
        return out.decode('utf-8').split("text returned:")[-1].strip()
    return default

def clean_and_load_data():
    """Forces the JSON to only have ONE entry per unique file path."""
    if not os.path.exists(DATA_FILE):
        return {}
    
    with open(DATA_FILE, 'r') as f:
        raw_data = json.load(f)
    
    clean_data = {}
    for _, info in raw_data.items():
        path = info.get('path')
        clean_data[path] = info 
        
    final_data = {}
    for path, info in clean_data.items():
        full_path = os.path.join(ROOT_DIR, path)
        if os.path.exists(full_path):
            h = get_file_hash(full_path)
            final_data[h] = info
            
    print(f"📊 Metadata Cleaned: {len(final_data)} unique photos found.")
    return final_data

def choose_from_mac_list(title, prompt, items):
    applescript = (
        f'choose from list {json.dumps(items)} '
        f'with title "{title}" with prompt "{prompt}" '
        f'with multiple selections allowed and empty selection allowed'
    )
    proc = subprocess.Popen(['osascript', '-e', applescript], stdout=subprocess.PIPE)
    out, _ = proc.communicate()
    result = out.decode('utf-8').strip()
    return None if result == "false" else [x.strip() for x in result.split(',')]

def ask_mac_question(title, prompt, buttons=["Next", "Stop"]):
    btn_str = '", "'.join(buttons)
    applescript = f'display dialog "{prompt}" with title "{title}" buttons {{"{btn_str}"}} default button "{buttons[0]}"'
    proc = subprocess.Popen(['osascript', '-e', applescript], stdout=subprocess.PIPE)
    out, _ = proc.communicate()
    return out.decode('utf-8').strip().split(':')[-1]

def ask_location(selected_cats, existing={}):
    """
    Ask for location details based on whether photo is National or International.
    National  → State + City
    International → Country + City
    Returns dict with keys: state, city
    """
    is_national      = "Places/National"      in selected_cats
    is_international = "Places/International" in selected_cats

    # If neither Places category selected, still ask for a location (used as overlay)
    if not is_national and not is_international:
        # Simple single location field for non-Places photos
        current = existing.get('city', '') or existing.get('state', '') or existing.get('place', '')
        location = ask_mac_input("Location", "Enter Location Name (e.g., Megamalai):", current)
        return {"state": location, "city": location}

    # Determine National or International
    if is_national and is_international:
        # Both selected — ask which applies to this photo
        choice = ask_mac_question(
            "National or International?",
            "Is this photo National (India) or International?",
            ["National", "International"]
        )
        is_national      = (choice == "National")
        is_international = (choice == "International")

    if is_national:
        current_state = existing.get('state', '')
        current_city  = existing.get('city',  '')
        state = ask_mac_input(
            "Location — National",
            "Enter State (e.g., Karnataka, Tamil Nadu, Kerala):",
            current_state
        )
        city = ask_mac_input(
            "Location — National",
            f"Enter City / Place (e.g., Badami, Munnar, Megamalai):",
            current_city
        )
        return {"state": state.strip(), "city": city.strip()}

    if is_international:
        current_state = existing.get('state', '')
        current_city  = existing.get('city',  '')
        country = ask_mac_input(
            "Location — International",
            "Enter Country (e.g., Canada, Japan, France):",
            current_state
        )
        city = ask_mac_input(
            "Location — International",
            f"Enter City / Place (e.g., Banff, Tokyo, Paris):",
            current_city
        )
        return {"state": country.strip(), "city": city.strip()}

    return {"state": "", "city": ""}

def run_curator():
    data = clean_and_load_data()

    disk_files = []
    for root, _, files in os.walk(PHOTOS_DIR):
        for f in files:
            if f.lower().endswith(('.jpg', '.jpeg', '.png')):
                disk_files.append(os.path.join(root, f))

    for path in disk_files:
        f_hash   = get_file_hash(path)
        filename = os.path.basename(path)
        rel_path = os.path.relpath(path, ROOT_DIR)
        
        exists        = f_hash in data
        status_msg    = "ALREADY TAGGED" if exists else "NEW PHOTO"
        current_tags  = data[f_hash].get('categories', []) if exists else []
        current_state = data[f_hash].get('state', '') if exists else ''
        current_city  = data[f_hash].get('city',  '') if exists else ''
        # Backward compat — old entries may have 'place' instead of state/city
        if not current_state and not current_city and exists:
            current_state = data[f_hash].get('place', '')

        subprocess.run(["open", path])
        action = ask_mac_question(
            "Curator",
            f"{status_msg}: {filename}\n"
            f"Tags: {current_tags}\n"
            f"State/Country: {current_state}   City: {current_city}",
            ["Edit/Tag", "Skip", "Stop"]
        )
        
        if action == "Stop": break
        if action == "Skip": continue
        
        # 1. Select Categories
        selected_cats = choose_from_mac_list("Select Categories", f"Tagging: {filename}", FLAT_CATEGORIES)
        if selected_cats is None: continue

        # 2. Location — smart National vs International
        existing_location = {"state": current_state, "city": current_city}
        location = ask_location(selected_cats, existing_location)

        # 3. Remarks (optional caption shown as overlay on photo)
        current_remarks = data[f_hash].get('remarks', '') if exists else ''
        remarks = ask_mac_input(
            "Remarks (optional)",
            "Enter photo caption/remarks (shown as overlay, e.g., 'Great Hornbill in flight'):\n"
            "Leave blank if not needed.",
            current_remarks
        )

        # 4. Date added (defaults to today)
        today        = datetime.date.today().strftime('%Y-%m-%d')
        current_date = data[f_hash].get('date_added', today) if exists else today
        selected_date = ask_mac_input(
            "Date Added",
            "Date photo was added to site (YYYY-MM-DD):\n(Press OK to keep today's date)",
            current_date
        )
        # Validate date format — fallback to today if invalid
        try:
            datetime.datetime.strptime(selected_date, '%Y-%m-%d')
        except ValueError:
            selected_date = today

        # 5. Save
        data[f_hash] = {
            "path":       rel_path,
            "filename":   filename,
            "categories": selected_cats,
            "state":      location["state"],
            "city":       location["city"],
            "remarks":    remarks.strip(),
            "date_added": selected_date
        }
        
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"  ✅ Saved: {filename}  |  {location['state']} / {location['city']}")

    print(f"\n✅ Finished! Total photos in database: {len(data)}")

if __name__ == "__main__":
    run_curator()
