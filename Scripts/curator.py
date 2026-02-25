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
    try:
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except: return None

def ask_mac_input(title, prompt, default=""):
    applescript = f'display dialog "{prompt}" with title "{title}" default answer "{default}" buttons {{"OK"}} default button "OK"'
    proc = subprocess.Popen(['osascript', '-e', applescript], stdout=subprocess.PIPE)
    out, _ = proc.communicate()
    out_str = out.decode('utf-8')
    if "text returned:" in out_str:
        return out_str.split("text returned:")[-1].strip()
    return default

def clean_and_load_data():
    if not os.path.exists(DATA_FILE): return {}
    with open(DATA_FILE, 'r') as f:
        raw_data = json.load(f)
    
    clean_by_path = {}
    for _, info in raw_data.items():
        path = info.get('path')
        if os.path.exists(os.path.join(ROOT_DIR, path)):
            clean_by_path[path] = info 
            
    final_data = {}
    for path, info in clean_by_path.items():
        h = get_file_hash(os.path.join(ROOT_DIR, path))
        if h: final_data[h] = info
            
    print(f"📊 Metadata Cleaned: {len(final_data)} unique photos remain.")
    return final_data

def choose_from_mac_list(title, prompt, items):
    applescript = (f'choose from list {json.dumps(items)} with title "{title}" '
                   f'with prompt "{prompt}" with multiple selections allowed')
    proc = subprocess.Popen(['osascript', '-e', applescript], stdout=subprocess.PIPE)
    out, _ = proc.communicate()
    result = out.decode('utf-8').strip()
    return None if result == "false" else [x.strip() for x in result.split(',')]

def ask_mac_question(title, prompt, buttons=["Edit/Tag", "Skip", "Stop"]):
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

    last_place = "Megamalai"

    for path in disk_files:
        f_hash = get_file_hash(path)
        filename = os.path.basename(path)
        rel_path = os.path.relpath(path, ROOT_DIR)
        
        exists = f_hash in data
        current_tags = data[f_hash].get('categories', []) if exists else []
        current_place = data[f_hash].get('place', last_place) if exists else last_place
        
        subprocess.run(["open", path])
        action = ask_mac_question("Curator", f"File: {filename}\nTags: {current_tags}\nPlace: {current_place}")
        
        if action == "Stop": break
        if action == "Skip": continue
        
        selected_cats = choose_from_mac_list("Categories", f"Tagging {filename}", FLAT_CATEGORIES)
        if selected_cats:
            p_name = current_place
            if any("Places" in c for c in selected_cats):
                p_name = ask_mac_input("Location", "Enter Name (e.g., Megamalai):", current_place)
                last_place = p_name

            data[f_hash] = {
                "path": rel_path,
                "categories": selected_cats,
                "place": p_name,
                "filename": filename
            }
            with open(DATA_FILE, 'w') as f:
                json.dump(data, f, indent=4)

    print(f"✅ Finished. Metadata count: {len(data)}")

if __name__ == "__main__":
    run_curator()
