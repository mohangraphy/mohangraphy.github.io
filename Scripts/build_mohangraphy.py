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
    
    # Organize data: gallery[MainCategory][SubCategory][PlaceName] = [paths]
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

    # Slideshow: 10 random images
    all_pics = [i.get('path') for i in index_data.values()]
    slides = random.sample(all_pics, min(len(all_pics), 10)) if all_pics else []

    html_start = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8"><title>M O H A N G R A P H Y</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@100;300;700&display=swap');
            body, html {{ background: #000; color: #fff; font-family: 'Inter', sans-serif; margin: 0; scroll-behavior: smooth; }}
            
            /* HEADER & LOGO */
            header {{ position: fixed; top: 0; width: 100%; background: #000; z-index: 1000; display: flex; flex-direction: column; align-items: center; padding: 60px 0 20px 0; border-bottom: 1px solid #111; }}
            .logo {{ font-size: 60px; letter-spacing: 25px; font-weight: 100; text-transform: uppercase; margin-bottom: 30px; cursor: pointer; }}
            
            /* MAIN NAV */
            nav {{ display: flex; gap: 40px; }}
            nav a {{ color: #444; text-decoration: none; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 4px; transition: 0.3s; }}
            nav a:hover, nav a.active {{ color: #fff; }}

            /* SLIDESHOW */
            #hero {{ height: 100vh; width: 100%; position: relative; overflow: hidden; display: flex; align-items: center; justify-content: center; }}
            .slide {{ position: absolute; width: 100%; height: 100%; object-fit: cover; opacity: 0; transition: 3s ease-in-out; filter: brightness(0.5); }}
            .slide.active {{ opacity: 1; }}

            /* GALLERY LAYOUT */
            main {{ padding-top: 220px; min-height: 100vh; display: none; }}
            .section-block {{ max-width: 1800px; margin: 100px auto; padding: 0 40px; }}
            
            /* HEADINGS */
            .main-title {{ font-size: 50px; font-weight: 100; letter-spacing: 20px; text-transform: uppercase; border-left: 4px solid #fff; padding-left: 30px; margin-bottom: 60px; }}
            .sub-title {{ font-size: 18px; font-weight: 300; letter-spacing: 10px; text-transform: uppercase; color: #888; margin-top: 80px; }}
            .place-title {{ font-size: 10px; font-weight: 700; letter-spacing: 4px; color: #444; text-transform: uppercase; margin: 10px 0 30px 0; }}

            .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(600px, 1fr)); gap: 40px; }}
            .grid img {{ width: 100%; height: 750px; object-fit: cover; filter: grayscale(1); transition: 0.8s; cursor: pointer; }}
            .grid img:hover {{ filter: grayscale(0); transform: scale(1.02); }}

            /* FOOTER MENU */
            footer {{ position: fixed; bottom: 0; width: 100%; height: 60px; background: rgba(0,0,0,0.95); border-top: 1px solid #222; z-index: 1000; display: flex; align-items: center; justify-content: center; gap: 40px; }}
            footer a {{ color: #666; text-decoration: none; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 2px; }}
            footer a:hover {{ color: #fff; }}
        </style>
    </head>
    <body>
    <header>
        <div class="logo" onclick="window.location.reload()">M O H A N G R A P H Y</div>
        <nav id="top-nav">
            {"".join([f'<a href="#{c}" onclick="activate(\'{c}\', this)">{c}</a>' for c in main_cats])}
        </nav>
    </header>

    <div id="hero">
        {"".join([f'<img src="{p}" class="slide">' for p in slides])}
    </div>

    <main id="gallery-container">
    """

    content = ""
    for m_cat, s_dict in gallery.items():
        if s_dict:
            content += f'<div class="section-block" id="{m_cat}">'
            content += f'<div class="main-title">{m_cat}</div>'
            for s_cat, p_dict in s_dict.items():
                content += f'<div class="sub-title">{s_cat}</div>'
                for place, photos in p_dict.items():
                    content += f'<div class="place-title">— {place}</div>'
                    content += '<div class="grid">'
                    for p in photos:
                        content += f'<img src="{p}">'
                    content += '</div>'
            content += '</div>'

    html_end = """
    </main>
    <footer>
        <a href="#" onclick="window.location.reload()">Home</a>
        <a href="#top-nav">Back to Top</a>
        <a href="https://instagram.com/mohangraphy" target="_blank">Instagram</a>
    </footer>
    <script>
        // Hero Slideshow
        let cur = 0; let s = document.querySelectorAll('.slide');
        if(s.length) { s[0].classList.add('active'); setInterval(() => { s[cur].classList.remove('active'); cur=(cur+1)%s.length; s[cur].classList.add('active'); }, 5000); }

        function activate(id, el) {
            document.getElementById('hero').style.display = 'none';
            document.getElementById('gallery-container').style.display = 'block';
            document.querySelectorAll('nav a').forEach(a => a.classList.remove('active'));
            el.classList.add('active');
        }
    </script>
    </body></html>
    """
    with open("index.html", "w") as f: f.write(html_start + content + html_end)
    print("✅ Website Re-Built Successfully.")

if __name__ == "__main__": generate_html()