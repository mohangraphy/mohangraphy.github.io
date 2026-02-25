import os
import json
import random

# CONFIGURATION
ROOT_DIR = "/Users/ncm/Pictures/Mohangraphy"
DATA_FILE = os.path.join(ROOT_DIR, "Scripts/photo_metadata.json")

# THE GUARANTEED STRUCTURE
MANUAL_STRUCTURE = {
    "Places": ["National", "International"],
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
    photo_map = {}
    place_map = {"National": {}, "International": {}}

    # Sort photos into categories and places
    for info in index_data.values():
        path = info.get('path')
        tags = info.get('categories', [])
        place_name = info.get('place', 'General')
        for tag in tags:
            if tag not in photo_map: photo_map[tag] = []
            photo_map[tag].append(path)
            if "Places/National" in tag:
                if place_name not in place_map["National"]: place_map["National"][place_name] = []
                place_map["National"][place_name].append(path)
            elif "Places/International" in tag:
                if place_name not in place_map["International"]: place_map["International"][place_name] = []
                place_map["International"][place_name].append(path)

    all_pics = [i.get('path') for i in index_data.values()]
    slides = random.sample(all_pics, min(len(all_pics), 10)) if all_pics else []

    # THE VECTOR LOGO (SVG)
    logo_svg = """
    <svg viewBox="0 0 1000 80" xmlns="http://www.w3.org/2000/svg" class="logo-vector" onclick="goHome()">
        <text x="50%" y="50%" text-anchor="middle" dominant-baseline="middle" 
              font-family="'Inter', sans-serif" font-weight="900" font-size="42" 
              letter-spacing="22" fill="white">MOHANGRAPHY</text>
    </svg>
    """

    html_start = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>M O H A N G R A P H Y</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;900&display=swap');
            * {{ box-sizing: border-box; }}
            body, html {{ background: #000; color: #fff; font-family: 'Inter', sans-serif; margin: 0; padding: 0; scroll-behavior: smooth; overflow-x: hidden; }}
            
            header {{ 
                position: fixed; top: 0; width: 100%; background: #000; z-index: 9999; 
                display: flex; flex-direction: column; align-items: center; 
                padding: 20px 0; border-bottom: 1px solid #111;
            }}
            .logo-vector {{ width: 90%; max-width: 600px; height: auto; cursor: pointer; margin-bottom: 15px; }}

            nav {{ display: flex; gap: 15px; justify-content: center; flex-wrap: wrap; width: 100%; padding: 0 10px; }}
            @media (min-width: 768px) {{ nav {{ gap: 35px; }} }}

            .nav-item {{ position: relative; padding-bottom: 10px; }}
            .nav-link {{ color: #666; text-decoration: none; font-size: clamp(10px, 2vw, 13px); font-weight: 900; text-transform: uppercase; letter-spacing: 2px; transition: 0.3s; }}
            .nav-item:hover > .nav-link {{ color: #fff; }}
            
            .submenu {{ 
                position: absolute; top: 100%; left: 50%; transform: translateX(-50%); 
                background: #000; border: 1px solid #222; min-width: 200px; 
                display: none; flex-direction: column; padding: 10px 0; z-index: 10000;
            }}
            .nav-item:hover .submenu {{ display: flex; }}
            .submenu a, .nested-header {{ color: #777; padding: 10px 20px; text-decoration: none; font-size: 11px; letter-spacing: 1px; text-transform: uppercase; text-align: center; display: block; }}
            .submenu a:hover {{ color: #fff; background: #111; }}
            
            .nested-group {{ border-top: 1px solid #111; background: #050505; }}
            .nested-header {{ color: #999; font-weight: 900; pointer-events: none; padding-top: 10px; }}
            
            #hero {{ height: 100vh; width: 100%; position: relative; display: flex; align-items: center; justify-content: center; background: #000; z-index: 1; }}
            .slide {{ position: absolute; width: 100%; height: 100%; object-fit: cover; opacity: 0; transition: 3s; filter: brightness(0.4); }}
            .slide.active {{ opacity: 1; }}
            
            main {{ padding-top: 180px; display: none; width: 100%; min-height: 100vh; }}
            @media (min-width: 768px) {{ main {{ padding-top: 220px; }} }}
            
            .section-block {{ max-width: 1600px; margin: 0 auto 100px; padding: 0 20px; display: none; }}
            .grid {{ display: grid; grid-template-columns: 1fr; gap: 20px; }}
            @media (min-width: 768px) {{ .grid {{ grid-template-columns: 1fr 1fr; gap: 30px; }} }}
            @media (min-width: 1200px) {{ .grid {{ grid-template-columns: repeat(auto-fill, minmax(600px, 1fr)); }} }}

            .grid img {{ width: 100%; height: auto; aspect-ratio: 3/2; object-fit: cover; filter: grayscale(1); transition: 0.8s; }}
            @media (max-width: 1024px) {{ .grid img {{ filter: grayscale(0); }} }}
            .grid img:hover {{ filter: grayscale(0); }}
            
            .wip-message {{ text-align: center; font-size: 14px; color: #444; text-transform: uppercase; margin-top: 150px; letter-spacing: 2px; }}
            
            footer {{ position: fixed; bottom: 0; width: 100%; height: 50px; background: rgba(0,0,0,0.9); z-index: 9999; display: flex; align-items: center; justify-content: center; gap: 40px; }}
            .footer-link {{ color: #555; text-decoration: none; font-size: 11px; font-weight: 900; text-transform: uppercase; }}
        </style>
    </head>
    <body>
    <header>{logo_svg}<nav id="main-nav">
    """

    nav_html = ""
    content_html = ""

    for m_cat, subs in MANUAL_STRUCTURE.items():
        nav_html += f'<div class="nav-item"><a href="#" class="nav-link" onclick="showSection(\'sec-{m_cat}\')">{m_cat}</a>'
        m_photos = []

        if m_cat == "Places":
            nav_html += '<div class="submenu">'
            for group in ["National", "International"]:
                nav_html += f'<div class="nested-group"><div class="nested-header">{group}</div>'
                if place_map[group]:
                    for p_name, p_list in place_map[group].items():
                        safe_id = f"place-{p_name.replace(' ', '-')}"
                        nav_html += f'<a href="#" onclick="showSection(\'{safe_id}\')">{p_name}</a>'
                        m_photos.extend(p_list)
                        content_html += f'<div class="section-block" id="{safe_id}"><div class="grid">' + "".join([f'<img src="{img}">' for img in p_list]) + '</div></div>'
                else:
                    nav_html += '<a href="#">Work in progress</a>'
                nav_html += '</div>'
            nav_html += '</div>'
        
        elif subs:
            nav_html += '<div class="submenu">'
            for s_cat in subs:
                safe_id = f"sub-{m_cat}-{s_cat.replace(' ', '-')}"
                nav_html += f'<a href="#" onclick="showSection(\'{safe_id}\')">{s_cat}</a>'
                tag = f"{m_cat}/{s_cat}"
                photos = photo_map.get(tag, [])
                m_photos.extend(photos)
                content_html += f'<div class="section-block" id="{safe_id}">' + (f'<div class="grid">{"".join([f"<img src='{p}'>" for p in photos])}</div>' if photos else '<div class="wip-message">Work in progress</div>') + '</div>'
            nav_html += '</div>'

        content_html += f'<div class="section-block" id="sec-{m_cat}">'
        photos_to_show = list(set(m_photos)) if m_photos else photo_map.get(m_cat, [])
        if photos_to_show:
            content_html += '<div class="grid">' + "".join([f'<img src="{p}">' for p in photos_to_show]) + '</div>'
        else:
            content_html += '<div class="wip-message">Work in progress</div>'
        content_html += '</div>'
        nav_html += '</div>'

    html_end = """
    </nav></header>
    <div id="hero">""" + "".join([f'<img src="{p}" class="slide">' for p in slides]) + """</div>
    <main id="gallery-container">""" + content_html + """</main>
    <footer><a href="#" class="footer-link" onclick="goHome()">Home</a><a href="#main-nav" class="footer-link">Top</a></footer>
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
        f.write(html_start + nav_html + html_end)
    print("✅ Build Fixed: Vector Logo, Responsive Menus, and Submenus restored.")

if __name__ == "__main__":
    generate_html()