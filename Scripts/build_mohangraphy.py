import os
import json
import random

ROOT_DIR = "/Users/ncm/Pictures/Mohangraphy"
DATA_FILE = os.path.join(ROOT_DIR, "Scripts/photo_metadata.json")

def load_index():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def generate_html():
    index_data = load_index()
    
    # 1. Organize Photos by Category based on your Tags
    categorized_photos = {
        "Architecture": [], "Birds": [], "Flowers": [], 
        "Nature": [], "People": [], "Places": []
    }
    
    # Also track specific "Places" (like Munnar) for sub-headings
    place_specific = {}

    for photo_hash, info in index_data.items():
        rel_path = info['path']
        # Map to main categories
        for cat in info['categories']:
            if cat in categorized_photos:
                categorized_photos[cat].append(rel_path)
        
        # Map to specific places (National/International logic)
        if info.get('place'):
            p_name = info['place']
            if p_name not in place_specific: place_specific[p_name] = []
            place_specific[p_name].append(rel_path)

    # 2. Get 12 Random Landscape photos for the Intro Slideshow
    landscape_pool = categorized_photos.get("Nature", [])
    slideshow_list = random.sample(landscape_pool, min(len(landscape_pool), 12)) if landscape_pool else []

    # --- HTML GENERATION (The same Cinematic UI as before) ---
    html_start = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Mohangraphy</title>
        <style>
            :root {{ --bg: #000; --menu-grey: #222; --text-white: #fff; }}
            body, html {{ height: 100%; margin: 0; background: var(--bg); color: var(--text-white); font-family: 'Inter', sans-serif; overflow: hidden; }}
            header {{ position: fixed; top: 0; width: 100%; height: 220px; background: linear-gradient(to bottom, rgba(0,0,0,1) 80%, rgba(0,0,0,0)); display: flex; flex-direction: column; align-items: center; justify-content: center; z-index: 1000; transition: 0.5s; }}
            header.shrink {{ height: 100px; background: rgba(0,0,0,0.95); }}
            .logo {{ font-size: 48px; font-weight: 200; letter-spacing: 20px; text-transform: uppercase; margin-bottom: 30px; transition: 0.5s; }}
            header.shrink .logo {{ font-size: 24px; margin-bottom: 10px; letter-spacing: 10px; }}
            nav {{ display: flex; gap: 15px; }}
            .nav-link {{ background: var(--menu-grey); color: #888; padding: 12px 24px; text-decoration: none; font-size: 10px; font-weight: 800; text-transform: uppercase; letter-spacing: 2px; border: 1px solid #333; transition: 0.3s; }}
            .nav-link:hover, .nav-link.active {{ color: #fff; background: #333; border-color: #666; }}
            #hero-slideshow {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 1; overflow: hidden; }}
            .slide {{ position: absolute; width: 100%; height: 100%; object-fit: cover; opacity: 0; transition: opacity 2.5s ease; }}
            .slide.active {{ opacity: 0.45; animation: kenburns 15s infinite alternate ease-in-out; }}
            @keyframes kenburns {{ from {{ transform: scale(1); }} to {{ transform: scale(1.15); }} }}
            main {{ position: absolute; top: 220px; bottom: 75px; width: 100%; overflow-y: auto; display: none; background: #000; z-index: 500; }}
            .container {{ max-width: 1600px; margin: 0 auto; padding: 40px 20px; }}
            .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(450px, 1fr)); gap: 20px; margin-bottom: 100px; }}
            .grid img {{ width: 100%; height: 550px; object-fit: cover; cursor: pointer; filter: brightness(0.8); transition: 0.5s; }}
            .grid img:hover {{ filter: brightness(1.1); transform: scale(1.02); }}
            h1 {{ font-size: 28px; font-weight: 200; letter-spacing: 12px; border-left: 4px solid #fff; padding-left: 20px; margin-top: 100px; text-transform: uppercase; }}
            footer {{ position: fixed; bottom: 0; width: 100%; height: 75px; background: #000; border-top: 1px solid #111; display: flex; align-items: center; justify-content: center; gap: 60px; z-index: 1000; }}
            footer a {{ color: #555; text-decoration: none; font-size: 10px; font-weight: 800; text-transform: uppercase; letter-spacing: 2px; }}
        </style>
    </head>
    <body>
    <header id="main-header">
        <div class="logo">Mohangraphy</div>
        <nav>
            {"".join([f'<a href="#{cat}" class="nav-link" onclick="activateSection(this)">{cat}</a>' for cat in categorized_photos.keys()])}
        </nav>
    </header>
    <div id="hero-slideshow">
        {"".join([f'<img src="{p}" class="slide">' for p in slideshow_list])}
    </div>
    <main id="main-gallery" onscroll="handleScroll()"><div class="container">
    """

    content_html = ""
    for cat, photos in categorized_photos.items():
        if photos:
            content_html += f'<h1 id="{cat}">{cat}</h1><div class="grid">'
            for p in photos:
                content_html += f'<img src="{p}" onclick="openLightbox(this.src)">'
            content_html += "</div>"
            
            # If this is "Places", also show specific place names
            if cat == "Places":
                for place, p_list in place_specific.items():
                    content_html += f'<h3>| {place}</h3><div class="grid">'
                    for p in p_list:
                        content_html += f'<img src="{p}" onclick="openLightbox(this.src)">'
                    content_html += "</div>"

    footer = """
    </div></main>
    <footer>
        <a href="/" onclick="location.reload()">Home</a>
        <a href="https://instagram.com/mohangraphy" target="_blank">@mohangraphy</a>
    </footer>
    <div id="lightbox" style="position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.98); display:none; align-items:center; justify-content:center; z-index:2000;" onclick="this.style.display='none'">
        <img id="lb-img" style="max-width:95%; max-height:95%;">
    </div>
    <script>
        let slides = document.querySelectorAll('.slide');
        let current = 0;
        if(slides.length > 0) {
            slides[0].classList.add('active');
            setInterval(() => {
                slides[current].classList.remove('active');
                current = (current + 1) % slides.length;
                slides[current].classList.add('active');
            }, 5000);
        }
        function activateSection(el) {
            document.querySelectorAll('.nav-link').forEach(link => link.classList.remove('active'));
            el.classList.add('active');
            document.getElementById('hero-slideshow').style.display = 'none';
            document.getElementById('main-gallery').style.display = 'block';
        }
        function handleScroll() {
            const header = document.getElementById('main-header');
            const gallery = document.getElementById('main-gallery');
            if (gallery.scrollTop > 50) header.classList.add('shrink');
            else header.classList.remove('shrink');
        }
        function openLightbox(src) {
            document.getElementById('lb-img').src = src;
            document.getElementById('lightbox').style.display = 'flex';
        }
    </script>
    </body></html>
    """
    
    with open("index.html", "w") as f:
        f.write(html_start + content_html + footer)
    print("🚀 INDEX-BASED BUILD COMPLETE.")

if __name__ == "__main__":
    generate_html()