import os
import random

# --- CONFIGURATION (Folders from image_329b9c.png) ---
STRUCTURE = {
    "Architecture": ["Photos/Architecture"],
    "Birds": ["Photos/Birds"],
    "Flowers": ["Photos/Flowers"],
    "Nature": {
        "Landscape": ["Photos/Nature/Landscape", "Photos/Nature/Landscape/Megamalai"],
        "Sunsets & Sunrises": ["Photos/Nature/Sunsets and Sunrises"],
        "Wildlife": ["Photos/Nature/Wildlife"]
    },
    "People": {"Portraits": ["Photos/People/Portraits"]},
    "Places": {
        "International": ["Photos/Places/International"],
        "National": ["Photos/Places/National", "Photos/Nature/Landscape/Megamalai"]
    }
}

def get_slideshow_photos():
    # Target Landscape folder for the intro slideshow
    path = "Photos/Nature/Landscape"
    if os.path.exists(path):
        photos = [os.path.join(path, f) for f in os.listdir(path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        return random.sample(photos, min(len(photos), 10))
    return []

def generate_html():
    slideshow_list = get_slideshow_photos()
    
    html_start = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Mohangraphy</title>
        <style>
            :root {{ --bg: #000; --menu-grey: #222; --text-white: #fff; }}
            body, html {{ height: 100%; margin: 0; background: var(--bg); color: var(--text-white); font-family: 'Inter', sans-serif; overflow: hidden; }}
            
            /* TOP FROZEN SECTION */
            header {{
                position: fixed; top: 0; width: 100%; height: 220px;
                background: linear-gradient(to bottom, rgba(0,0,0,1) 70%, rgba(0,0,0,0)); 
                display: flex; flex-direction: column; align-items: center; justify-content: center; z-index: 1000;
            }}
            .logo {{ font-size: 48px; font-weight: 200; letter-spacing: 20px; text-transform: uppercase; margin-bottom: 30px; }}
            
            nav {{ display: flex; gap: 15px; }}
            .nav-item {{ position: relative; }}
            .nav-item > a {{ 
                background: var(--menu-grey); color: var(--text-white); padding: 14px 28px; 
                text-decoration: none; font-size: 11px; font-weight: 800; text-transform: uppercase; 
                letter-spacing: 2px; display: block; border: 1px solid #333; transition: 0.3s;
            }}
            .nav-item:hover > a {{ background: #444; }}

            /* KEN BURNS SLIDESHOW */
            #hero-slideshow {{
                position: absolute; top: 0; left: 0; width: 100%; height: 100%;
                background: #000; z-index: 1; overflow: hidden;
            }}
            .slide {{
                position: absolute; width: 100%; height: 100%; object-fit: cover;
                opacity: 0; transition: opacity 2s ease-in-out;
            }}
            .slide.active {{ 
                opacity: 0.5; 
                animation: kenburns 12s infinite alternate ease-in-out;
            }}

            @keyframes kenburns {{
                from {{ transform: scale(1); }}
                to {{ transform: scale(1.15); }}
            }}

            /* GALLERY AREA (Hidden until clicked) */
            main {{ 
                position: absolute; top: 220px; bottom: 75px; width: 100%; 
                overflow-y: auto; display: none; background: var(--bg); z-index: 500; scroll-behavior: smooth;
            }}
            .container {{ max-width: 1600px; margin: 0 auto; padding: 40px 20px; }}
            .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(450px, 1fr)); gap: 15px; margin-bottom: 120px; }}
            .grid img {{ width: 100%; height: 500px; object-fit: cover; cursor: pointer; transition: 0.5s; }}
            .grid img:hover {{ filter: brightness(1.2); }}
            
            h1 {{ font-size: 32px; font-weight: 200; letter-spacing: 10px; border-left: 6px solid #fff; padding-left: 25px; margin-top: 80px; text-transform: uppercase; }}

            /* BRIGHT FOOTER */
            footer {{
                position: fixed; bottom: 0; width: 100%; height: 75px;
                background: #000; border-top: 1px solid #222;
                display: flex; align-items: center; justify-content: center; gap: 60px; z-index: 1000;
            }}
            footer a {{ color: #fff; text-decoration: none; font-size: 11px; font-weight: 900; text-transform: uppercase; letter-spacing: 3px; }}
        </style>
    </head>
    <body>
    <header>
        <div class="logo">Mohangraphy</div>
        <nav>"""

    for main in STRUCTURE.keys():
        m_id = main.replace(" ", "").replace("&", "")
        html_start += f'<div class="nav-item"><a href="#{m_id}" onclick="showGallery()">{main}</a></div>'
    
    html_start += f"""
        </nav>
    </header>

    <div id="hero-slideshow">
        {''.join([f'<img src="{p}" class="slide">' for p in slideshow_list])}
    </div>

    <main id="main-gallery"><div class="container">"""

    content_html = ""
    for main, content in STRUCTURE.items():
        m_id = main.replace(" ", "").replace("&", "")
        content_html += f'<h1 id="{m_id}">{main}</h1><div class="grid">'
        
        paths = []
        if isinstance(content, dict):
            for p_list in content.values(): paths.extend(p_list)
        else: paths.extend(content)
            
        for path in paths:
            if os.path.exists(path):
                for img in sorted(os.listdir(path)):
                    if img.lower().endswith(('.jpg', '.jpeg', '.png')):
                        img_path = os.path.join(path, img)
                        content_html += f'<img src="{img_path}" onclick="openLightbox(this.src)">'
        content_html += "</div>"

    footer = """
    </div></main>
    <footer>
        <a href="/" onclick="location.reload()">Home</a>
        <a href="#top" onclick="document.getElementById('main-gallery').scrollTo(0,0)">Back to Top</a>
        <a href="https://instagram.com/mohangraphy" target="_blank">Instagram: @mohangraphy</a>
    </footer>

    <div id="lightbox" style="position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.95); display:none; align-items:center; justify-content:center; z-index:2000;" onclick="this.style.display='none'">
        <img id="lb-img" style="max-width:90%; max-height:90%;">
    </div>

    <script>
        // Slideshow Transitions
        let slides = document.querySelectorAll('.slide');
        let current = 0;
        if(slides.length > 0) {{
            slides[0].classList.add('active');
            setInterval(() => {{
                slides[current].classList.remove('active');