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
    
    # Define the Main Buckets
    categories = ["Architecture", "Birds", "Flowers", "Nature", "People", "Places"]
    # gallery_tree[Main][Sub][Place] = [list of photos]
    gallery_tree = {cat: {} for cat in categories}

    for info in index_data.values():
        rel_path = info.get('path')
        tags = info.get('categories', [])
        place_name = info.get('place', 'General')

        for tag in tags:
            parts = tag.split('/')
            main_cat = parts[0]
            
            if main_cat in gallery_tree:
                # Get the sub-category (e.g., "National" or "Landscape")
                sub_cat = parts[1] if len(parts) > 1 else "General"
                
                if sub_cat not in gallery_tree[main_cat]:
                    gallery_tree[main_cat][sub_cat] = {}
                
                if place_name not in gallery_tree[main_cat][sub_cat]:
                    gallery_tree[main_cat][sub_cat][place_name] = []
                
                gallery_tree[main_cat][sub_cat][place_name].append(rel_path)

    # Slideshow: 12 Random High-Res photos
    all_photos = [info.get('path') for info in index_data.values()]
    slideshow = random.sample(all_photos, min(len(all_photos), 12)) if all_photos else []

    # --- HTML & CSS (Large Cinematic Style) ---
    html_start = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8"><title>Mohangraphy</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@100;400;800&display=swap');
            body {{ background: #000; color: #fff; font-family: 'Inter', sans-serif; margin: 0; overflow: hidden; }}
            header {{ position: fixed; top: 0; width: 100%; height: 250px; background: linear-gradient(to bottom, black 60%, transparent); z-index: 1000; display: flex; flex-direction: column; align-items: center; justify-content: center; transition: 0.5s; }}
            header.shrink {{ height: 100px; background: rgba(0,0,0,0.9); }}
            .logo {{ font-size: 60px; letter-spacing: 25px; text-transform: uppercase; font-weight: 100; transition: 0.5s; margin-bottom: 20px; }}
            header.shrink .logo {{ font-size: 24px; letter-spacing: 10px; margin-bottom: 5px; }}
            nav {{ display: flex; gap: 25px; }}
            nav a {{ color: #555; text-decoration: none; font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 3px; transition: 0.3s; padding: 10px; }}
            nav a:hover, nav a.active {{ color: #fff; border-bottom: 1px solid #fff; }}
            #hero {{ position: absolute; width: 100%; height: 100%; z-index: 1; background: #000; }}
            .slide {{ position: absolute; width: 100%; height: 100%; object-fit: cover; opacity: 0; transition: opacity 3s ease-in-out; }}
            .slide.active {{ opacity: 0.5; }}
            main {{ position: absolute; top: 0; bottom: 0; width: 100%; overflow-y: auto; display: none; z-index: 500; background: #000; padding-top: 250px; }}
            .container {{ max-width: 1600px; margin: 0 auto; padding: 20px; }}
            .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(500px, 1fr)); gap: 30px; margin-bottom: 80px; }}
            .grid img {{ width: 100%; height: 600px; object-fit: cover; cursor: pointer; transition: 0.6s; filter: brightness(0.7); }}
            .grid img:hover {{ filter: brightness(1); transform: scale(1.02); }}
            h1 {{ font-size: 40px; font-weight: 100; letter-spacing: 15px; text-transform: uppercase; margin: 100px 0 10px 0; border-left: 5px solid #fff; padding-left: 20px; }}
            h2 {{ font-size: 18px; letter-spacing: 8px; color: #aaa; text-transform: uppercase; margin: 40px 0 10px 0; font-weight: 400; }}
            h3 {{ font-size: 11px; letter-spacing: 4px; color: #666; text-transform: uppercase; margin-bottom: 20px; font-weight: 800; }}
            #lightbox {{ position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.95); display:none; align-items:center; justify-content:center; z-index:2000; }}
        </style>
    </head>
    <body>
    <header id="main-header">
        <div class="logo">Mohangraphy</div>
        <nav>
            {"".join([f'<a href="#{c}" onclick="showSection(\'{c}\', this)">{c}</a>' for c in categories])}
        </nav>
    </header>
    <div id="hero">
        {"".join([f'<img src="{p}" class="slide">' for p in slideshow])}
    </div>
    <main id="main-gallery" onscroll="checkScroll()">
        <div class="container">
    """

    content = ""
    for main_cat, sub_dict in gallery_tree.items():
        if sub_dict:
            content += f'<h1 id="{main_cat}">{main_cat}</h1>'
            for sub_cat, places in sub_dict.items():
                content += f'<h2>{sub_cat}</h2>' # Shows "National" or "International"
                for place_name, photos in places.items():
                    content += f'<h3>— {place_name}</h3>'
                    content += '<div class="grid">'
                    for p in photos:
                        content += f'<img src="{p}" onclick="openLB(this.src)">'
                    content += '</div>'

    html_end = """
        </div>
        <div style="height:200px;"></div>
    </main>
    <div id="lightbox" onclick="this.style.display='none'">
        <img id="lb-img" style="max-width:90%; max-height:90%;">
    </div>
    <script>
        let slides = document.querySelectorAll('.slide');
        let cur = 0;
        if(slides.length) {
            slides[0].classList.add('active');
            setInterval(() => {
                slides[cur].classList.remove('active');
                cur = (cur + 1) % slides.length;
                slides[cur].classList.add('active');
            }, 6000);
        }
        function showSection(id, el) {
            document.getElementById('hero').style.display = 'none';
            document.getElementById('main-gallery').style.display = 'block';
            document.querySelectorAll('nav a').forEach(a => a.classList.remove('active'));
            el.classList.add('active');
            document.getElementById(id).scrollIntoView({behavior: 'smooth'});
        }
        function checkScroll() {
            let m = document.getElementById('main-gallery');
            let h = document.getElementById('main-header');
            if (m.scrollTop > 100) h.classList.add('shrink');
            else h.classList.remove('shrink');
        }
        function openLB(src) {
            document.getElementById('lb-img').src = src;
            document.getElementById('lightbox').style.display = 'flex';
        }
    </script>
    </body></html>
    """
    
    with open("index.html", "w") as f:
        f.write(html_start + content + html_end)
    print("🚀 BUILD SUCCESSFUL: Places are now sorted by Region.")

if __name__ == "__main__":
    generate_html()