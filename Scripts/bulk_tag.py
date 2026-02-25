import os
import json
import hashlib

# --- SETTINGS ---
ROOT_DIR = "/Users/ncm/Pictures/Mohangraphy"
# Point this exactly to your Megamalai folder
MEGAMALAI_FOLDER = os.path.join(ROOT_DIR, "Photos/Places/National/Megamalai") 
DATA_FILE = os.path.join(ROOT_DIR, "Scripts/photo_metadata.json")

# THE TAGS YOU WANT FOR ALL 33
TARGET_CATEGORIES = ["Places/National", "Nature/Landscape/Mountains"]
TARGET_PLACE = "Megamalai"

def get_file_hash(filepath):
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def bulk_apply():
    if not os.path.exists(DATA_FILE):
        data = {}
    else:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)

    print(f"🚀 Scanning: {MEGAMALAI_FOLDER}")
    
    count = 0
    for root, _, files in os.walk(MEGAMALAI_FOLDER):
        for f in files:
            if f.lower().endswith(('.jpg', '.jpeg', '.png')):
                full_path = os.path.join(root, f)
                f_hash = get_file_hash(full_path)
                rel_path = os.path.relpath(full_path, ROOT_DIR)
                
                # OVERWRITE/CREATE entry
                data[f_hash] = {
                    "path": rel_path,
                    "categories": TARGET_CATEGORIES,
                    "place": TARGET_PLACE,
                    "filename": f
                }
                count += 1

    # Final cleanup: Remove any "ghost" entries that might have different hashes for the same path
    clean_data = {}
    seen_paths = {}
    for h_id, info in data.items():
        p = info.get('path')
        seen_paths[p] = h_id
        clean_data[h_id] = info
        
    with open(DATA_FILE, 'w') as f:
        json.dump(clean_data, f, indent=4)

    print(f"✅ Success! Processed {count} photos.")
    print(f"📂 All 33 photos are now tagged as '{TARGET_PLACE}' with categories: {TARGET_CATEGORIES}")

if __name__ == "__main__":
    bulk_apply()