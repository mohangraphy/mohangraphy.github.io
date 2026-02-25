import os
import json
import random

ROOT_DIR = "/Users/ncm/Pictures/Mohangraphy"
DATA_FILE = os.path.join(ROOT_DIR, "Scripts/photo_metadata.json")

# Master structure for non-Places menus
MANUAL_STRUCTURE = {
    "Nature": ["Landscape", "Sunsets and Sunrises", "Wildlife"],
    "People": ["Portraits"],
    "Architecture": [],
    "Birds": [],
    "Flowers": []
}

def load_index():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            try: return json.load(f)
            except: return {}
    return {}

def generate_html():
    index_data = load_index()
    
    # Organize data for quick lookup
    # category_map tracks: "Nature/Landscape" -> [paths]
    # place_map tracks: "National" -> {"Megamalai": [paths]}
    category_map = {}
    place_map = {"National": {}, "International": {}}

    for info in index_data.values():
        path = info.get('path')
        tags = info.get('categories', [])
        place_name = info.get('place', 'General')

        for tag in tags:
            if tag not in category_map: category_map[tag] = []
            category_map[tag].append(path)
            
            # If it's a Places tag, sort the place name into the right bucket
            if tag.startswith("Places/"):
                bucket = tag.split('/')[-1] # National or International
                if bucket in place_map:
                    if place_name not in place_map[bucket]:
                        place_map[bucket][place_name] = []
                    place_map[bucket][place_name].append(path)

    all_pics = [i.get('path') for i in index_data.values()]
    slides = random.sample(all_pics, min(len(all_pics), 10)) if all_pics else []

    html_start = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>M O H A N G R A P H Y</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;900&display=swap');
            body, html {{ background: #000; color: #fff; font-family: 'Inter', sans-serif; margin: 0; padding: 0; scroll-behavior: smooth; }}
            header {{ position: fixed; top: 0; width: 100%; background: #000; z-index: 5000; display: flex; flex-direction: column; align-items: center; padding: 40px 0 25px 0; border-bottom: 1px solid #111; }}
            .logo {{ font-size: 55px; letter-spacing: 12px; font-weight: 900; text-transform: uppercase; margin-bottom: 25px; cursor: pointer; color: #fff; }}
            nav {{ display: flex; gap: 40px; position: relative; }}
            .nav-item {{ position: relative; padding-bottom: 15px; }}
            .nav-link, .footer-link {{ color: #555; text-decoration: none; font-size: 13px; font-weight: 900; text-transform: uppercase; letter-spacing: 2px; transition: 0.3s; }}
            .nav-item:hover > .nav-link, .footer-link:hover {{ color: #fff; }}
            
            .submenu {{ position: absolute; top: 35px; left: 50%; transform: translateX(-50%); background: #000; border: 1px solid #222; min-width: 240px; display: none; flex-direction: column; padding: 10px 0; z-index: 5100; }}
            .nav-item:hover .submenu {{ display: flex; }}
            .submenu a, .nested-header {{ color: #666; padding: 10px 20px; text-decoration: none; font-size: 11px; letter-spacing: 2px; text-transform: uppercase; text-align: center; display: block; }}
            .submenu a:hover {{ color: #fff; background: #111; }}
            
            .nested-group {{ border-top: 1px solid #111; background: #050505; padding: 5px 0; }}
            .nested-header {{ color: #888; font-weight: 900; pointer-events: none; }}
            .nested-item {{ font-size: 10px !important; color: #444 !important; }}
            
            #hero {{ height: 100vh; width: 100%; position: relative; display: flex; align-items: center; justify-content: center; background: #000; z-index: 1; }}
            .slide {{ position: absolute; width: 100%; height: 100%; object-fit: cover; opacity: 0; transition: 3s; filter: brightness(0.4); }}
            .slide.active {{ opacity: 1; }}
            
            main {{ padding-top: 220px; display: none; width: 100%; min-height: 100vh; }}
            .section-block {{ max-width: 1600px; margin: 0 auto 100px; padding: 0 40px; display: none; }}
            .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(600px, 1fr)); gap: 30px; }}
            .grid img {{ width: 100%; height: auto; aspect-ratio: 3/2; object-fit: cover; filter: grayscale(1); transition: 0.8s; cursor: pointer; }}
            .grid img:hover {{ filter: grayscale(0); }}
            
            .wip-message {{ text-align: center; font-size: 14px; letter-spacing: 3px; color: #444; text-transform: uppercase; margin-top: 150px; }}
            footer {{ position: fixed; bottom: 0; width: 100%; height: 60px; background: rgba(0,0,0,0.95); border-top: 1px solid #111; z-index: 5000; display: flex; align-items: center; justify-content: center; gap: 60px; }}
        </style>
    </head>
    <body>
    <header><div class="logo" onclick="goHome()">M O H A N G R A P H Y</div><nav id="main-nav">
    """

    nav_html = ""
    content_html = ""

    # --- BUILD PLACES MENU (DYNAMIC) ---
    nav_html += '<div class="nav-item"><a href="#" class="nav-link" onclick="showSection(\'sec-Places\')">Places</a><div class="submenu">'
    all_place_photos = []
    for group in ["National", "International"]:
        nav_html += f'<div class="nested-group"><div class="nested-header">{group}</div>'
        if place_map[group]:
            for p_name, p_list in place_map[group].items():
                safe_id = f"place-{p_name.replace(' ', '-')}"
                nav_html += f'<a href="#" class="nested-item" onclick="showSection(\'{safe_id}\')">{p_name}</a>'
                all_place_photos.extend(p_list)
                # Create section for specific place
                content_html += f'<div class="section-block" id="{safe_id}"><div class="grid">' + "".join([f'<img src="{img}">' for img in p_list]) + '</div></div>'
        else:
            nav_html += '<a href="#" class="nested-item">Work in progress</a>'
        nav_html += '</div>'
    nav_html += '</div></div>'
    
    # General Places section (View All)
    content_html += '<div class="section-block" id="sec-Places"><div class="grid">' + "".join([f'<img src="{img}">' for img in list(set(all_place_photos))]) + '</div></div>'

    # --- BUILD MANUAL MENUS (NATURE, PEOPLE, etc) ---
    for m_cat, subs in MANUAL_STRUCTURE.items():
        nav_html += f'<div class="nav-item"><a href="#" class="nav-link" onclick="showSection(\'sec-{m_cat}\')">{m_cat}</a>'
        m_photos = []
        
        if subs:
            nav_html += '<div class="submenu">'
            for s_cat in subs:
                safe_id = f"sub-{m_cat}-{s_cat.replace(' ', '-')}"
                nav_html += f'<a href="#" onclick="showSection(\'{safe_id}\')">{s_cat}</a>'
                
                tag = f"{m_cat}/{s_cat}"
                photos = category_map.get(tag, [])
                m_photos.extend(photos)
                
                content_html += f'<div class="section-block" id="{safe_id}">'
                if photos:
                    content_html += '<div class="grid">' + "".join([f'<img src="{p}">' for p in photos]) + '</div>'
                else:
                    content_html += '<div class="wip-message">Work in progress</div>'
                content_html += '</div>'
            nav_html += '</div>'
        
        # Main Category View All
        content_html += f'<div class="section-block" id="sec-{m_cat}">'
        if m_photos:
            content_html += '<div class="grid">' + "".join([f'<img src="{p}">' for p in list(set(m_photos))]) + '</div>'
        else:
            content_html += '<div class="wip-message">Work in progress</div>'
        content_html += '</div>'
        nav_html += '</div>'

    html_end = """
    </main>
    <footer><a href="#" class="footer-link" onclick="goHome()">Home</a><a href="#main-nav" class="footer-link">Back to Top</a></footer>
    <script>
        let slides = document.querySelectorAll('.slide'); let cur = 0;
        if(slides.length) { slides[0].classList.add('active'); setInterval(() => { slides[cur].classList.remove('active'); cur=(cur+1)%slides.length; slides[cur].classList.add('active'); }, 5000); }
        function goHome() { document.getElementById('gallery-container').style.display = 'none'; document.getElementById('hero').style.display = 'flex'; window.scrollTo(0,0); }
        function showSection(id) { 
            document.getElementById('hero').style.display = 'none'; document.getElementById('gallery-container').style.display = 'block';
            document.querySelectorAll('.section-block').forEach(sec => sec.style.display = 'none');
            let target = document.getElementById(id);
            if(target) target.style.display = 'block'; else goHome();
            window.scrollTo(0,0);
        }
    </script>
    </body></html>
    """
    with open("index.html", "w") as f:
        f.write(html_start + nav_html + "</nav></header>" + 
                '<div id="hero">' + "".join([f'<img src="{p}" class="slide">' for p in slides]) + '</div>' + 
                '<main id="gallery-container">' + content_html + html_end)
    print("✅ Build Complete: Places list names dynamically. Nature/People are hardcoded.")

if __name__ == "__main__":
    generate_html()