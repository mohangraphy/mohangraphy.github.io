import os
import json
import hashlib
import subprocess
import sys

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
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

def cleanup_duplicates(data):
    """Scan JSON for multiple entries pointing to the same file path and remove them."""
    seen_paths = {}
    clean_data = {}
    count = 0
    
    for h_id, info in data.items():
        path = info.get('path')
        if path in seen_paths:
            count += 1
        # Always use the latest entry for a path
        seen_paths[path] = h_id
        clean_data[h_id] = info
        
    if count > 0:
        print(f"🧹 Auto-Cleanup: Removed {count} ghost/duplicate entries from metadata.")
        # Save the cleaned data immediately
        with open(DATA_FILE, 'w') as f:
            json.dump(clean_data, f, indent=4)
            
    return clean_data

def choose_from_mac_list(title, prompt, items):
    applescript = (
        f'choose from list {json.dumps(items)} '
        f'with title "{title}" '
        f'with prompt "{prompt}" '
        f'with multiple selections allowed '
        f'and empty selection allowed'
    )
    proc = subprocess.Popen(['osascript', '-e', applescript], stdout=subprocess.PIPE)
    out, _ = proc.communicate()
    result = out.decode('utf-8').strip()
    
    if result == "false": return None
    if result == "": return ["Uncategorized"]
    return [x.strip() for x in result.split(',')]

def ask_mac_question(title, prompt, buttons=["Next", "Repeat Last", "Stop"]):
    btn_str = '", "'.join(buttons)
    applescript = f'display dialog "{prompt}" with title "{title}" buttons {{"{btn_str}"}} default button "{buttons[0]}"'
    proc = subprocess.Popen(['osascript', '-e', applescript], stdout=subprocess.PIPE)
    out, _ = proc.communicate()
    return out.decode('utf-8').strip().split(':')[-1]

def ask_mac_input(title, prompt, default=""):
    applescript = f'display dialog "{prompt}" with title "{title}" default answer "{default}" buttons {{"OK"}} default button "OK"'
    proc = subprocess.Popen(['osascript', '-e', applescript], stdout=subprocess.PIPE)
    out, _ = proc.communicate()
    if "text returned:" in out.decode('utf-8'):
        return out.decode('utf-8').split("text returned:")[-1].strip()
    return default

def process_photo(path, filename, current_tags, current_place, data, is_new=True):
    if os.path.exists(path):
        subprocess.run(["open", path])
    
    tag_str = ", ".join(current_tags) if current_tags else "None"
    
    if is_new:
        msg = f"NEW PHOTO: {filename}\n\nLast Tags: {tag_str}\nLast Place: {current_place}"
        action = ask_mac_question("Curator", msg, ["New Selection", "Repeat Last", "Stop"])
    else:
        msg = f"EDITING: {filename}\n\nCurrent Tags: {tag_str}\nCurrent Place: {current_place}\n\nMake changes?"
        action = ask_mac_question("Editor", msg, ["Edit This", "Next Result", "Exit"])

    if action in ["Stop", "Exit"]: return "EXIT", current_tags, current_place
    if action == "Next Result": return "NEXT", current_tags, current_place
    
    if action == "Repeat Last" and is_new:
        final_cats, final_place = current_tags, current_place
    else:
        selected = choose_from_mac_list("Categories", f"Select for: {filename}", FLAT_CATEGORIES)
        if selected is None: return "NEXT", current_tags, current_place
        
        final_cats = selected
        final_place = ask_mac_input("Location", "Enter Place Name:", current_place)

    # Key logic: Use the file's hash as the ID to ensure we overwrite rather than duplicate
    photo_id = get_file_hash(path)
    data[photo_id] = {
        "path": os.path.relpath(path, ROOT_DIR),
        "categories": final_cats,
        "place": final_place,
        "filename": filename
    }
    
    with open(DATA_FILE, 'w') as f: 
        json.dump(data, f, indent=4)
        
    return "CONTINUE", final_cats, final_place

def run_curator():
    if not os.path.exists(os.path.dirname(DATA_FILE)): os.makedirs(os.path.dirname(DATA_FILE))
    
    # Load and clean duplicates before starting any tasks
    raw_data = (json.load(open(DATA_FILE)) if os.path.exists(DATA_FILE) else {})
    data = cleanup_duplicates(raw_data)

    mode = ask_mac_question("Mohangraphy", "Main Menu", ["Index New", "Edit Existing", "Exit"])
    if mode == "Exit": return

    if mode == "Edit Existing":
        query = ask_mac_input("Search", "Keyword:").lower()
        results = []
        for h, v in data.items():
            search_blob = f"{v.get('filename','')} {v.get('place','')} {' '.join(v.get('categories',[]))}".lower()
            if query in search_blob: results.append(v)
        
        if not results:
            ask_mac_question("Search", "No results found.", ["Back"])
            return run_curator()

        for info in sorted(results, key=lambda x: x.get('filename', os.path.basename(x.get('path', '')))):
            full_path = os.path.join(ROOT_DIR, info['path'])
            fname = info.get('filename', os.path.basename(info['path']))
            status, _, _ = process_photo(full_path, fname, info.get('categories', []), info.get('place', ''), data, is_new=False)
            if status == "EXIT": break
        return

    # Indexing Logic
    all_files = []
    for root, _, files in os.walk(PHOTOS_DIR):
        for f in files:
            if f.lower().endswith(('.jpg', '.jpeg', '.png')):
                all_files.append(os.path.join(root, f))
                
    new_files = [f for f in all_files if get_file_hash(f) not in data]
    if not new_files:
        ask_mac_question("Curator", "All photos indexed!", ["OK"])
        return

    p_cats, p_place = [], ""
    for path in new_files:
        status, p_cats, p_place = process_photo(path, os.path.basename(path), p_cats, p_place, data, is_new=True)
        if status == "EXIT": break

if __name__ == "__main__":
    run_curator()