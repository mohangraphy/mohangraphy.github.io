import os
import json
import random

ROOT_DIR = "/Users/ncm/Pictures/Mohangraphy"
DATA_FILE = os.path.join(ROOT_DIR, "Scripts/photo_metadata.json")

def load_index():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            try: return json.load(f)
            except: return {}
    return {}

def generate_html():
    index_data = load_index()
    main_cats = ["Architecture", "Birds", "Flowers", "Nature", "People", "Places"]
    
    # Structure: gallery[Main][Sub][Place] = [paths]
    gallery = {c: {} for c in main_cats}

    for info in index_data.values():
        path = info.get('path')
        tags = info.get('categories', [])
        place = info.get('place', 'General')

        for tag in tags:
            parts = tag.split('/')
            m_cat = parts[0]
            if m_cat in gallery:
                s_cat = parts[1] if len(parts) > 1 else "General"
                if s_cat not in gallery[m_cat]: gallery[m_cat][s_cat] = {}
                if place not in gallery[m_cat][s_cat]: gallery[m_cat][s_cat][place] = []
                gallery[m_cat][s_cat][place].append(path)

    all_pics = [i.get('path') for i in index_data.values()]
    slides = random.sample(all_pics, min(len(all_pics), 10)) if all_pics else []

    html_start = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8"><title>M O H A N G R A P H Y</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@100;300;700&display=swap');
            body, html {{ background: #000; color: #fff; font-family: 'Inter', sans-serif; margin: 0; scroll-behavior: smooth; overflow-x: hidden; }}
            
            header {{ position: fixed; top: 0; width: 100%; background: #000; z-index: 1000; display: flex; flex-direction: column; align-items: center; padding: 40px 0 20px 0; border-bottom: 1px solid #111; }}
            .logo {{ font-size: 50px; letter-spacing: 20px; font-weight: 100; text-transform: uppercase; margin-bottom: 25px; cursor: pointer; }}
            
            /* DYNAMIC DROPDOWN SYSTEM */
            nav {{ display: flex; gap: 35px; position: relative; }}
            .nav-item {{ position: relative; padding-bottom: 10px; }}
            .nav-item > a {{ color: #444; text-decoration: none; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 3px; transition: 0.3s; }}
            .nav-item:hover > a {{ color: #fff; }}
            
            .submenu {{ position: absolute; top: 25px; left: 0; background: #000; border: 1px solid #222; min-width: 180px; display: none; flex-direction: column; padding: 10px 0; z-index: 1100; }}
            .nav-item:hover .submenu {{ display: flex; }}
            .submenu a {{ color: #666; padding: 8px 20px; text-decoration: none; font-size: 9px; letter-spacing: 2px; text-transform: uppercase; transition: 0.2s; }}
            .submenu a:hover {{ color: #fff; background: #111; }}

            /* NESTED PLACES (National/International) */
            .has-nested {{ position: relative; }}
            .nested-menu {{ position: absolute; top: 0; left: 100%; background: #000; border: 1px solid #222; display: none; flex-direction: column; min-width: 180px; }}
            .has-nested:hover .nested-menu {{ display: flex; }}

            #hero {{ height: 100vh; width: 100%; position: relative; display: flex; align-items: center; justify-content: center; background: #000; }}
            .slide {{ position: absolute; width: 100%; height: 100%; object-fit: cover; opacity: 0; transition: 3s; filter: brightness(0.4); }}
            .slide.active {{ opacity: 1; }}

            main {{ padding-top: 200px; display: none; }}
            .section-block {{ max-width: 1800px; margin: 0 auto 100px; padding: 0 40px; }}
            .main-title {{ font-size: 40px; font-weight: 100; letter-spacing: 15px; text-transform: uppercase; border-left: 3px solid #fff; padding-left: 25px; margin-bottom: 50px; }}
            .place-heading {{ font-size: 14px; letter-spacing: 5px; color: #888; text-transform: uppercase; margin: 60px 0 20px; font-weight: 300; }}

            .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(500px, 1fr)); gap: 30px; }}
            .grid img {{ width: 100%; height: 650px; object-fit: cover; filter: grayscale(1); transition: 0.6s; cursor: pointer; }}
            .grid img:hover {{ filter: grayscale(0); }}

            footer {{ position: fixed; bottom: 0; width: 100%; height: 50px; background: rgba(0,0,0,0.9); border-top: 1px solid #111; z-index: 1000; display: flex; align-items: center; justify-content: center; gap: 30px; }}
            footer a {{ color: #444; text-decoration: none; font-size: 9px; font-weight: 700; text-transform: uppercase; letter-spacing: 2px; }}
        </style>
    </head>
    <body>
    <header>
        <div class="logo" onclick="goHome()">M O H A N G R A P H Y</div>
        <nav id="main-nav">
    """

    # --- DYNAMIC MENU LOGIC ---
    nav_html = ""
    for m_cat in main_cats:
        # Check if category has any photos
        has_images = any(len(p_list) > 0 for s in gallery[m_cat].values() for p_list in s.values())
        link_action = f"onclick=\"showCat('{m_cat}')\"" if has_images else "onclick=\"goHome()\""
        
        nav_html += f'<div class="nav-item"><a href="#" {link_action}>{m_cat}</a>'
        
        if has_images and gallery[m_cat]:
            nav_html += '<div class="submenu">'
            for s_cat, p_dict in gallery[m_cat].items():
                if s_cat == "General":
                    for place in p_dict.keys():
                        nav_html += f'<a href="#{m_cat}-{place}">{place}</a>'
                else:
                    # Creating the National/International Dropdown
                    nav_html += f'<div class="has-nested"><a href="#">{s_cat} &raquo;</a>'
                    nav_html += '<div class="nested-menu">'
                    for place in p_dict.keys():
                        nav_html += f'<a href="#{m_cat}-{s_cat}-{place}">{place}</a>'
                    nav_html += '</div></div>'
            nav_html += '</div>'
        nav_html += '</div>'

    content = ""
    for m_cat, s_dict in gallery.items():
        if any(s_dict.values()):
            content += f'<div class="section-block" id="sec-{m_cat}">'
            content += f'<div class="main-title">{m_cat}</div>'
            for s_cat, p_dict in s_dict.items():
                for place, photos in p_dict.items():
                    div_id = f"{m_cat}-{s_cat}-{place}" if s_cat != "General" else f"{m_cat}-{place}"
                    content += f'<div class="place-heading" id="{div_id}">| {s_cat if s_cat != "General" else ""} {place}</div>'
                    content += '<div class="grid">'
                    for p in photos: content += f'<img src="{p}">'
                    content += '</div>'
            content += '</div>'

    html_end = """
    </main>
    <footer><a href="#" onclick="goHome()">Home</a><a href="#main-nav">Back to Top</a></footer>
    <script>
        let s = document.querySelectorAll('.slide'); let cur = 0;
        if(s.length) { s[0].classList.add('active'); setInterval(() => { s[cur].classList.remove('active'); cur=(cur+1)%s.length; s[cur].classList.add('active'); }, 5000); }

        function goHome() { 
            document.getElementById('hero').style.display = 'flex'; 
            document.getElementById('gallery-container').style.display = 'none'; 
            window.scrollTo(0,0);
        }
        
        function showCat(id) {
            document.getElementById('hero').style.display = 'none';
            document.getElementById('gallery-container').style.display = 'block';
            let target = document.getElementById('sec-'+id);
            if(target) target.scrollIntoView();
        }
    </script>
    </body></html>
    """
    
    with open("index.html", "w") as f:
        f.write(html_start + nav_html + "</nav></header>" + 
                '<div id="hero">' + "".join([f'<img src="{p}" class="slide">' for p in slides]) + '</div>' + 
                '<main id="gallery-container">' + content + html_end)
    
    print("✅ Build Process Complete.")

if __name__ == "__main__":
    generate_html()