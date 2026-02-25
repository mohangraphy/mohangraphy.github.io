import os
import json
import hashlib
import subprocess

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

def run_curator():
    data = clean_and_load_data()

    disk_files = []
    for root, _, files in os.walk(PHOTOS_DIR):
        for f in files:
            if f.lower().endswith(('.jpg', '.jpeg', '.png')):
                disk_files.append(os.path.join(root, f))

    for path in disk_files:
        f_hash = get_file_hash(path)
        filename = os.path.basename(path)
        rel_path = os.path.relpath(path, ROOT_DIR)
        
        exists = f_hash in data
        status_msg = "ALREADY TAGGED" if exists else "NEW PHOTO"
        current_tags = data[f_hash].get('categories', []) if exists else []
        current_place = data[f_hash].get('place', "") if exists else ""
        
        subprocess.run(["open", path])
        action = ask_mac_question("Curator", f"{status_msg}: {filename}\nTags: {current_tags}\nPlace: {current_place}", ["Edit/Tag", "Skip", "Stop"])
        
        if action == "Stop": break
        if action == "Skip": continue
        
        # 1. Select Categories
        selected_cats = choose_from_mac_list("Select Categories", f"Tagging: {filename}", FLAT_CATEGORIES)
        if selected_cats is None: continue
        
        # 2. ASK FOR PLACE NAME (The fixed part)
        selected_place = ask_mac_input("Location", "Enter Place Name (e.g., Megamalai):", current_place)
        
        # 3. Overwrite with Fresh Data
        data[f_hash] = {
            "path": rel_path,
            "categories": selected_cats,
            "place": selected_place,
            "filename": filename
        }
        
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=4)

    print(f"✅ Finished! Total photos in database: {len(data)}")

if __name__ == "__main__":
    run_curator()