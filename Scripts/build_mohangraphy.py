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
    
    # Store images by category and the final leaf-node (Place) only
    gallery = {c: {} for c in main_cats}

    for info in index_data.values():
        path = info.get('path')
        tags = info.get('categories', [])
        place = info.get('place', 'General')

        for tag in tags:
            parts = tag.split('/')
            m_cat = parts[0]
            if m_cat in gallery:
                # We ignore the middle-tier (like 'Landscape') to keep the menu sleek
                if place not in gallery[m_cat]: gallery[m_cat][place] = []
                gallery[m_cat][place].append(path)

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
            body, html {{ background: #000; color: #fff; font-family: 'Inter', sans-serif; margin: 0; padding: 0; scroll-behavior: smooth; overflow-x: hidden; }}
            
            header {{ 
                position: fixed; top: 0; width: 100%; background: #000; z-index: 5000; 
                display: flex; flex-direction: column; align-items: center; 
                padding: 40px 0 25px 0; border-bottom: 1px solid #111;
            }}
            .logo {{ font-size: 55px; letter-spacing: 10px; font-weight: 900; text-transform: uppercase; margin-bottom: 25px; cursor: pointer; color: #fff; }}
            
            nav {{ display: flex; gap: 40px; position: relative; }}
            .nav-item {{ position: relative; padding-bottom: 15px; display: flex; justify-content: center; }}
            .nav-item > a {{ color: #555; text-decoration: none; font-size: 12px; font-weight: 900; text-transform: uppercase; letter-spacing: 2px; transition: 0.3s; }}
            .nav-item:hover > a, .nav-item.active > a {{ color: #fff; }}
            
            /* TOP-DOWN CENTERED SUBMENU */
            .submenu {{ 
                position: absolute; top: 35px; left: 50%; transform: translateX(-50%); 
                background: #000; border: 1px solid #222; min-width: 160px; 
                display: none; flex-direction: column; padding: 8px 0; z-index: 5100;
            }}
            .nav-item:hover .submenu {{ display: flex; }}
            .submenu a {{ 
                color: #666; padding: 12px 15px; text-decoration: none; 
                font-size: 10px; letter-spacing: 2px; text-transform: uppercase; 
                transition: 0.2s; text-align: center;
            }}
            .submenu a:hover {{ color: #fff; background: #111; }}

            #hero {{ height: 100vh; width: 100%; position: relative; display: flex; align-items: center; justify-content: center; background: #000; z-index: 1; }}
            .slide {{ position: absolute; width: 100%; height: 100%; object-fit: cover; opacity: 0; transition: 3s; filter: brightness(0.4); }}
            .slide.active {{ opacity: 1; }}

            main {{ padding-top: 180px; display: none; width: 100%; }}
            .section-block {{ max-width: 1600px; margin: 0 auto 100px; padding: 0 40px; display: none; }}
            
            /* PURE GRID ONLY - NO TEXT TITLES */
            .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(600px, 1fr)); gap: 30px; }}
            .grid img {{ width: 100%; height: auto; aspect-ratio: 3/2; object-fit: cover; filter: grayscale(1); transition: 0.8s; cursor: pointer; }}
            .grid img:hover {{ filter: grayscale(0); }}

            footer {{ position: fixed; bottom: 0; width: 100%; height: 50px; background: rgba(0,0,0,0.9); border-top: 1px solid #111; z-index: 5000; display: flex; align-items: center; justify-content: center; gap: 40px; }}
            footer a {{ color: #444; text-decoration: none; font-size: 9px; font-weight: 900; text-transform: uppercase; letter-spacing: 2px; }}
        </style>
    </head>
    <body>
    <header>
        <div class="logo" onclick="goHome()">M O H A N G R A P H Y</div>
        <nav id="main-nav">
    """

    nav_html = ""
    content = ""
    for m_cat in main_cats:
        has_images = bool(gallery[m_cat])
        nav_html += f'<div class="nav-item" id="nav-{m_cat}"><a href="#" onclick="showSection(\'{m_cat}\')">{m_cat}</a>'
        
        if has_images:
            nav_html += '<div class="submenu">'
            content += f'<div class="section-block" id="sec-{m_cat}"><div class="grid">'
            
            # Sort places to keep them neat
            for place in sorted(gallery[m_cat].keys()):
                # Add to flattened menu
                nav_html += f'<a href="#" onclick="showSection(\'{m_cat}\')">{place}</a>'
                # Add images to the pure grid
                for img_path in gallery[m_cat][place]:
                    content += f'<img src="{img_path}">'
            
            nav_html += '</div>' # End Submenu
            content += '</div></div>' # End Grid and Section
        nav_html += '</div>'

    html_end = """
    </main>
    <footer><a href="#" onclick="goHome()">Home</a><a href="#main-nav">Top</a></footer>
    <script>
        let slides = document.querySelectorAll('.slide'); let cur = 0;
        if(slides.length) { 
            slides[0].classList.add('active'); 
            setInterval(() => { slides[cur].classList.remove('active'); cur=(cur+1)%slides.length; slides[cur].classList.add('active'); }, 5000); 
        }
        
        function goHome() { 
            document.getElementById('gallery-container').style.display = 'none'; 
            document.getElementById('hero').style.display = 'flex'; 
            document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
            window.scrollTo(0,0); 
        }

        function showSection(id) { 
            document.getElementById('hero').style.display = 'none'; 
            document.getElementById('gallery-container').style.display = 'block'; 
            document.querySelectorAll('.section-block').forEach(sec => sec.style.display = 'none');
            let target = document.getElementById('sec-'+id);
            if(target) target.style.display = 'block';
            document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
            document.getElementById('nav-'+id).classList.add('active');
            window.scrollTo(0,0);
        }
    </script>
    </body></html>
    """
    with open("index.html", "w") as f:
        f.write(html_start + nav_html + "</nav></header>" + 
                '<div id="hero">' + "".join([f'<img src="{p}" class="slide">' for p in slides]) + '</div>' + 
                '<main id="gallery-container">' + content + html_end)
    print("✅ Build Final: No nested submenus, no on-page labels.")

if __name__ == "__main__":
    generate_html()