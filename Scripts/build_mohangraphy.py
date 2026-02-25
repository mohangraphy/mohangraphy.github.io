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
    
    # Re-establishing the deep hierarchy
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
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>M O H A N G R A P H Y</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;900&display=swap');
            body, html {{ background: #000; color: #fff; font-family: 'Inter', sans-serif; margin: 0; padding: 0; scroll-behavior: smooth; }}
            
            header {{ 
                position: fixed; top: 0; width: 100%; background: #000; z-index: 5000; 
                display: flex; flex-direction: column; align-items: center; 
                padding: 40px 0 25px 0; border-bottom: 1px solid #111;
            }}
            .logo {{ font-size: 55px; letter-spacing: 12px; font-weight: 900; text-transform: uppercase; margin-bottom: 25px; cursor: pointer; color: #fff; }}
            
            nav {{ display: flex; gap: 40px; position: relative; }}
            .nav-item {{ position: relative; padding-bottom: 15px; }}
            .nav-item > a {{ color: #555; text-decoration: none; font-size: 13px; font-weight: 900; text-transform: uppercase; letter-spacing: 2px; transition: 0.3s; }}
            .nav-item:hover > a, .nav-item.active > a {{ color: #fff; }}
            
            /* SUBMENU */
            .submenu {{ 
                position: absolute; top: 35px; left: 0; background: #000; border: 1px solid #222; 
                min-width: 180px; display: none; flex-direction: column; padding: 10px 0; z-index: 5100;
            }}
            .nav-item:hover .submenu {{ display: flex; }}
            .submenu a {{ color: #666; padding: 10px 20px; text-decoration: none; font-size: 11px; letter-spacing: 2px; text-transform: uppercase; transition: 0.2s; }}
            .submenu a:hover {{ color: #fff; background: #111; }}
            
            /* THIRD LEVEL (National -> City) */
            .has-nested {{ position: relative; }}
            .nested-menu {{ 
                position: absolute; top: 0; left: 100%; background: #000; border: 1px solid #222; 
                display: none; flex-direction: column; min-width: 180px; 
            }}
            .has-nested:hover .nested-menu {{ display: flex; }}
            
            /* Prevent right-side clipping */
            .nav-item:nth-last-child(-n+2) .submenu {{ left: auto; right: 0; }}
            .nav-item:nth-last-child(-n+2) .nested-menu {{ left: auto; right: 100%; }}

            #hero {{ height: 100vh; width: 100%; position: relative; display: flex; align-items: center; justify-content: center; background: #000; z-index: 1; }}
            .slide {{ position: absolute; width: 100%; height: 100%; object-fit: cover; opacity: 0; transition: 3s; filter: brightness(0.4); }}
            .slide.active {{ opacity: 1; }}

            main {{ padding-top: 200px; display: none; width: 100%; }}
            .section-block {{ max-width: 1600px; margin: 0 auto 100px; padding: 0 40px; display: none; }}
            
            /* THE SILENT GRID - NO TEXT */
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
        has_content = any(gallery[m_cat].values())
        nav_html += f'<div class="nav-item" id="nav-{m_cat}"><a href="#" onclick="showSection(\'{m_cat}\')">{m_cat}</a>'
        
        if has_content:
            nav_html += '<div class="submenu">'
            content += f'<div class="section-block" id="sec-{m_cat}"><div class="grid">'
            
            for s_cat, p_dict in gallery[m_cat].items():
                if s_cat == "General":
                    for place, photos in p_dict.items():
                        nav_html += f'<a href="#" onclick="showSection(\'{m_cat}\')">{place}</a>'
                        for p in photos: content += f'<img src="{p}">'
                else:
                    # Creating the "National/International" level
                    nav_html += f'<div class="has-nested"><a href="#">{s_cat} &raquo;</a>'
                    nav_html += '<div class="nested-menu">'
                    for place, photos in p_dict.items():
                        nav_html += f'<a href="#" onclick="showSection(\'{m_cat}\')">{place}</a>'
                        for p in photos: content += f'<img src="{p}">'
                    nav_html += '</div></div>'
            
            nav_html += '</div>'
            content += '</div></div>'
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
            window.scrollTo(0,0); 
        }

        function showSection(id) { 
            document.getElementById('hero').style.display = 'none'; 
            document.getElementById('gallery-container').style.display = 'block'; 
            document.querySelectorAll('.section-block').forEach(sec => sec.style.display = 'none');
            let target = document.getElementById('sec-'+id);
            if(target) target.style.display = 'block';
            window.scrollTo(0,0);
        }
    </script>
    </body></html>
    """
    with open("index.html", "w") as f:
        f.write(html_start + nav_html + "</nav></header>" + 
                '<div id="hero">' + "".join([f'<img src="{p}" class="slide">' for p in slides]) + '</div>' + 
                '<main id="gallery-container">' + content + html_end)
    print("✅ Build Restored: Full hierarchy enabled. All text headers removed from gallery.")

if __name__ == "__main__":
    generate_html()