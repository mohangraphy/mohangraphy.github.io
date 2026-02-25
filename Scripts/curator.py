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

def clean_and_load_data():
    """Forces the JSON to only have ONE entry per unique file path."""
    if not os.path.exists(DATA_FILE):
        return {}
    
    with open(DATA_FILE, 'r') as f:
        raw_data = json.load(f)
    
    clean_data = {}
    # We map by PATH to ensure 1 photo = 1 entry
    for _, info in raw_data.items():
        path = info.get('path')
        # This overwrites any previous duplicate entry for this same path
        clean_data[path] = info 
        
    # Re-index by hash for the script's internal logic, but keep it unique
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

    # Get all actual files on disk
    disk_files = []
    for root, _, files in os.walk(PHOTOS_DIR):
        for f in files:
            if f.lower().endswith(('.jpg', '.jpeg', '.png')):
                disk_files.append(os.path.join(root, f))

    for path in disk_files:
        f_hash = get_file_hash(path)
        filename = os.path.basename(path)
        rel_path = os.path.relpath(path, ROOT_DIR)
        
        # If photo already exists, show it and ask if user wants to EDIT
        exists = f_hash in data
        status_msg = "ALREADY TAGGED" if exists else "NEW PHOTO"
        current_tags = data[f_hash]['categories'] if exists else []
        
        subprocess.run(["open", path])
        action = ask_mac_question("Curator", f"{status_msg}: {filename}\nTags: {current_tags}", ["Edit/Tag", "Skip", "Stop"])
        
        if action == "Stop": break
        if action == "Skip": continue
        
        # Fresh selection: remove everything and start over
        selected = choose_from_mac_list("Select Categories", f"Tagging: {filename}", FLAT_CATEGORIES)
        if selected:
            data[f_hash] = {
                "path": rel_path,
                "categories": selected,
                "filename": filename
            }
            with open(DATA_FILE, 'w') as f:
                json.dump(data, f, indent=4)

    print(f"✅ Finished! Total photos in database: {len(data)}")

if __name__ == "__main__":
    run_curator()