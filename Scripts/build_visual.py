import os
import json

# --- SETTINGS ---
ROOT_DIR = "/Users/ncm/Pictures/Mohangraphy"
DATA_FILE = os.path.join(ROOT_DIR, "Scripts/photo_metadata.json")
# We move the site to the ROOT so it can see the Photos folder easily
OUTPUT_DIR = ROOT_DIR 

SITE_STRUCTURE = {
    "Architecture": [],
    "Birds": [],
    "Flowers": [],
    "Nature": ["Landscape", "Mountains", "Sunsets", "Wildlife"],
    "People": ["Portraits"],
    "Places": ["National", "International"]
}

def generate_html(title, nav_buttons, grid_content, is_home=False):
    title_display = "Mohangraphy" if is_home else title
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>{title} | Mohangraphy</title>
        <link rel="stylesheet" href="visual_style.css">
    </head>
    <body>
        <h1 class="main-title">{title_display}</h1>
        <div class="sub-nav">{nav_buttons}</div>
        <div class="tile-container">{grid_content}</div>
        <div style="margin: 40px; text-align:center;">
            <a href="index.html" class="bevel-button">← Home</a>
        </div>
    </body>
    </html>
    """

def run_build():
    if not os.path.exists(DATA_FILE):
        print("❌ Error: photo_metadata.json not found!"); return
        
    with open(DATA_FILE, 'r') as f:
        data = json.load(f)

    # Clean the data to ensure 33 unique photos
    clean_photo_map = {info['path']: info for info in data.values() if os.path.exists(os.path.join(ROOT_DIR, info['path']))}
    
    category_buckets = {}
    for rel_path, info in clean_photo_map.items():
        for cat in info.get('categories', []):
            if cat not in category_buckets: category_buckets[cat] = []
            category_buckets[cat].append(info)

    # --- 1. HOME PAGE ---
    home_tiles = ""
    for main in SITE_STRUCTURE.keys():
        bg_photo = next((p['path'] for p in clean_photo_map.values() if any(main in c for c in p['categories'])), None)
        bg_style = f"style='background-image:url(\"{bg_photo}\")'" if bg_photo else ""
        home_tiles += f'<div class="category-tile" {bg_style}><div class="overlay"></div><a href="{main}.html" class="bevel-button">{main}</a></div>'
    
    with open(os.path.join(OUTPUT_DIR, "index.html"), "w") as f:
        f.write(generate_html("Home", "", home_tiles, is_home=True))

    # --- 2. CATEGORY PAGES ---
    for main, subs in SITE_STRUCTURE.items():
        nav_btns = "".join([f'<a href="{main}_{s}.html" class="bevel-button">{s}</a> ' for s in subs])
        
        grid_tiles = ""
        if not subs:
            photos = category_buckets.get(main, [])
            if not photos:
                grid_tiles = '<div class="category-tile wip-tile"><div class="overlay"></div><span class="bevel-button">Work in Progress</span></div>'
            else:
                for p in photos:
                    grid_tiles += f'<div class="category-tile" style="background-image:url(\"{p["path"]}\")"><div class="overlay"></div></div>'
        else:
            for s in subs:
                full_cat = f"{main}/{s}"
                photos = category_buckets.get(full_cat, [])
                bg_img = photos[0]['path'] if photos else None
                bg_style = f"style='background-image:url(\"{bg_img}\")'" if bg_img else ""
                label = s if photos else f"{s} (WIP)"
                grid_tiles += f'<div class="category-tile" {bg_style}><div class="overlay"></div><a href="{main}_{s}.html" class="bevel-button">{label}</a></div>'

        with open(os.path.join(OUTPUT_DIR, f"{main}.html"), "w") as f:
            f.write(generate_html(main, nav_btns, grid_tiles))

        # --- 3. SUB-CAT PAGES ---
        for s in subs:
            full_cat = f"{main}/{s}"
            photos = category_buckets.get(full_cat, [])
            photo_grid = ""
            if not photos:
                photo_grid = '<div class="category-tile wip-tile"><div class="overlay"></div><span class="bevel-button">Work in Progress</span></div>'
            else:
                if s == "National":
                    places = {}
                    for p in photos:
                        pl = p.get('place', 'Megamalai')
                        if pl not in places: places[pl] = p['path']
                    for pl, img in places.items():
                        photo_grid += f'<div class="category-tile" style="background-image:url(\"{img}\")"><div class="overlay"></div><a href="#" class="bevel-button">{pl}</a></div>'
                else:
                    for p in photos:
                        photo_grid += f'<div class="category-tile" style="background-image:url(\"{p["path"]}\")"><div class="overlay"></div></div>'
            
            with open(os.path.join(OUTPUT_DIR, f"{main}_{s}.html"), "w") as f:
                f.write(generate_html(f"{main} > {s}", "", photo_grid))

    print(f"✅ Website built in {OUTPUT_DIR}. Unique photos: {len(clean_photo_map)}")

if __name__ == "__main__":
    run_build()