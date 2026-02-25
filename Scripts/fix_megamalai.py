import json
import os

# CONFIGURATION
DATA_FILE = "/Users/ncm/Pictures/Mohangraphy/Scripts/photo_metadata.json"
MEGAMALAI_FOLDER = "/Users/ncm/Pictures/Mohangraphy/Photos/Nature/Landscape/Megamalai"

def update_tags_completely():
    if not os.path.exists(DATA_FILE):
        print("❌ Error: JSON file not found!")
        return

    with open(DATA_FILE, 'r') as f:
        data = json.load(f)

    files = [f for f in os.listdir(MEGAMALAI_FOLDER) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    count = 0
    for filename in files:
        # We need the path relative to the root of your project
        relative_path = f"Photos/Nature/Landscape/Megamalai/{filename}"
        
        # APPLYING MULTIPLE TAGS HERE
        data[filename] = {
            "path": relative_path,
            "categories": [
                "Places/National", 
                "Nature/Landscape", 
                "Nature/Landscape/Mountains"
            ],
            "place": "Megamalai"
        }
        count += 1

    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

    print(f"✅ Updated {count} photos with 3 tags each (Places, Landscape, and Mountains).")

if __name__ == "__main__":
    update_tags_completely()