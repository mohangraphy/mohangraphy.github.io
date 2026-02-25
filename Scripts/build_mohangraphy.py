import os
import random

# --- CONFIGURATION ---
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
    path = "Photos/Nature/Landscape"
    if os.path.exists(path):
        photos = [os.path.join(path, f) for f in os.listdir(path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        if not photos: return []
        return random.sample(photos, min(len(photos), 12))
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
            :root {{ --bg: #000; --menu-grey: #222; --text-white: #fff; --accent: #fff; }}
            body, html {{ height: 100%; margin: 0; background: var(--bg); color: var(--text-white); font-family: 'Inter', sans-serif; overflow: hidden; }}
            
            header {{
                position: fixed; top: 0; width: 100%; height: 220px;
                background: linear-gradient(to bottom, rgba(0,0,0,1) 80%, rgba(0,0,0,0)); 
                display: flex; flex-direction: column; align-items: center; justify-content: center; 
                z-index: 1000; transition: all 0.5s ease;
            }}
            header.shrink {{ height: 100px; background: rgba(0,0,0,0.95); border-bottom: 1px solid #222; }}
            header.shrink .logo {{ font-size: 24px; margin-bottom: 10px; letter-spacing: 10px; }}
            
            .logo {{ font-size: 48px; font-weight: 200; letter-spacing: 20px; text-transform: uppercase; margin-bottom: 30px; transition: 0.5s; }}
            
            nav {{ display: flex; gap: 15px; }}
            .nav-item > a {{ 
                background: var(--menu-grey); color: #888; padding: 12px 24px; 
                text-decoration: none; font-size: 10px; font-weight: 800; text-transform: uppercase; 
                letter-spacing: 2px; display: block; border: 1px solid #333; transition: 0.3s;
            }}
            .nav-item > a.active, .nav-item:hover > a {{ color: var(--text-white); background: #333; border-color: #666; }}

            #hero-slideshow {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 1; overflow: hidden; background: #000; }}
            .slide {{ position: absolute; width: 100%; height: 100%; object-fit: cover; opacity: 0; transition: opacity 2.5s ease-in-out; }}
            .slide.active {{ opacity: 0.45; animation: kenburns-random 15s infinite alternate ease-in-out; }}

            @keyframes kenburns-random {{
                0% {{ transform: scale(1); }}
                100% {{ transform: scale(1.15) translate(-1%, -1%); }}
            }}

            main {{ position: absolute; top: 220px; bottom: 75px; width: 100%; overflow-y: auto; display: none; background: var(--bg); z-index: 500; }}
            .container {{ max-width: 1600px; margin: 0 auto; padding: 40px 20px; }}
            .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(450px, 1fr)); gap: 20px; margin-bottom: 150px; }}
            .grid img {{ width: 100%; height: 550px; object-fit: cover; cursor: pointer; filter: brightness(0.85); transition: 0.6s ease; }}
            .grid img:hover {{ filter: brightness(1.1); transform: scale(1.02); }}
            
            h1 {{ font-size: 28px; font-weight: 200; letter-spacing: 12px; border-left: 4px solid var(--accent); padding-left: 20px; margin-top: 100px; text-transform: uppercase; }}

            footer {{ position: fixed; bottom: 0; width: 100%; height: 75px; background: #000; border-top: 1px solid #111; display: flex; align-items: center; justify-content: center; gap: 60px; z-index: 1000; }}
            footer a {{ color: #555; text-decoration: none; font-size: 10px; font-weight: 800; text-transform: uppercase; letter-spacing: 2px; transition: 0.3s; }}
            footer a:hover {{ color: #fff; }}
        </style>
    </head>
    <body>
    <header id="main-header">
        <div class="logo">Mohangraphy</div>
        <nav>"""

    for main in STRUCTURE.keys():
        m_id = main.replace(" ", "").replace("&", "")
        html_start += f'<div class="nav-item"><a href="#{m_id}" class="nav-link" onclick="activateSection(this)">{main}</a></div>'
    
    html_start += f"""
        </nav>
    </header>

    <div id="hero-slideshow">
        {''.join([f'<img src="{p}" class="slide">' for p in slideshow_list])}
    </div>

    <main id="main-gallery" onscroll="handleScroll()"><div class="container">"""

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
                        content_html += f'<img src="{os.path.join(path, img)}" onclick="openLightbox(this.src)">'
        content_html += "</div>"

    footer = """
    </div></main>
    <footer>
        <a href="/" onclick="location.reload()">Home</a>
        <a href="#top" onclick="document.getElementById('main-gallery').scrollTo(0,0)">Back to Top</a>
        <a href="https://instagram.com/mohangraphy" target="_blank">@mohangraphy</a>
    </footer>

    <div id="lightbox" style="position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.98); display:none; align-items:center; justify-content:center; z-index:2000;" onclick="this.style.display='none'">
        <img id="lb-img" style="max-width:95%; max-height:95%; object-fit:contain;">
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
            if (gallery.scrollTop > 100) { header.classList.add('shrink'); } 
            else { header.classList.remove('shrink'); }
        }

        function openLightbox(src) {
            document.getElementById('lb-img').src = src;
            document.getElementById('lightbox').style.display = 'flex';
        }
    </script>
    </body></html>"""

    with open("index.html", "w") as f:
        f.write(html_start + content_html + footer)
    print("🚀 MASTER BUILD COMPLETE: Cinematic experience is now built.")

if __name__ == "__main__":
    generate_html()