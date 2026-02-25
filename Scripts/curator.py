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
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

def choose_from_mac_list(title, prompt, items):
    applescript = f'choose from list {json.dumps(items)} with title "{title}" with prompt "{prompt}"'
    proc = subprocess.Popen(['osascript', '-e', applescript], stdout=subprocess.PIPE)
    out, _ = proc.communicate()
    result = out.decode('utf-8').strip()
    return [x.strip() for x in result.split(',')] if result != "false" else None

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

def process_photo(path, filename, prev_cats, prev_place, data, is_new=True):
    subprocess.run(["open", path])
    cat_summary = ", ".join(prev_cats) if prev_cats else "None"
    place_summary = prev_place if prev_place else "None"
    
    if is_new:
        msg = f"PHOTO: {filename}\n\nRepeat: {cat_summary}\nLocation: {place_summary}?"
        action = ask_mac_question("Curator", msg, ["New Selection", "Repeat Last", "Stop"])
    else:
        msg = f"EDITING: {filename}\nCategories: {cat_summary}\nPlace: {place_summary}\n\nIs this the one?"
        action = ask_mac_question("Verify Photo", msg, ["Edit This", "Wrong One (Next)", "Exit Search"])

    if action in ["Stop", "Exit Search"]: return "EXIT", prev_cats, prev_place
    if action == "Wrong One (Next)": return "NEXT", prev_cats, prev_place
    
    if action == "Repeat Last":
        current_cats, current_place = prev_cats, prev_place
    else:
        current_cats = choose_from_mac_list("Select Categories", f"Categorizing: {filename}", FLAT_CATEGORIES)
        if not current_cats: current_cats = ["Uncategorized"]
        current_place = ask_mac_input("Location", "Enter Place Name:", prev_place)

    data[get_file_hash(path)] = {
        "path": os.path.relpath(path, ROOT_DIR),
        "categories": current_cats,
        "place": current_place,
        "filename": filename
    }
    with open(DATA_FILE, 'w') as f: json.dump(data, f, indent=4)
    return "CONTINUE", current_cats, current_place

def run_curator():
    if not os.path.exists(os.path.dirname(DATA_FILE)): os.makedirs(os.path.dirname(DATA_FILE))
    data = (json.load(open(DATA_FILE)) if os.path.exists(DATA_FILE) else {})
    
    mode = ask_mac_question("Mohangraphy", "Main Menu", ["Index New", "Edit Existing", "Exit"])
    if mode == "Exit": return

    if mode == "Edit Existing":
        search_query = ask_mac_input("Search", "Enter keyword (e.g., Munnar):").lower()
        results = []
        # Gather all matching full paths and info
        for h, v in data.items():
            if any(search_query in str(v.get(key, '')).lower() for key in ['filename', 'place', 'categories']):
                results.append(v)
        
        if not results:
            ask_mac_question("Search", "No results found.", ["Back"])
            return run_curator()

        for info in sorted(results, key=lambda x: x['filename']):
            full_path = os.path.join(ROOT_DIR, info['path'])
            status, _, _ = process_photo(full_path, info['filename'], info['categories'], info['place'], data, is_new=False)
            
            if status == "EXIT": break
            if status == "CONTINUE": # After editing one, ask if user wants to continue or exit
                if ask_mac_question("Done", "Photo Updated. Continue with next search result?", ["Yes", "Exit"]) == "Exit": break
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

    prev_cats, prev_place = [], ""
    for i, path in enumerate(new_files):
        status, prev_cats, prev_place = process_photo(path, os.path.basename(path), prev_cats, prev_place, data)
        if status == "EXIT": break

if __name__ == "__main__":
    run_curator()