import os

# --- STRUCTURE CONFIGURATION (Verified folders) ---
STRUCTURE = {
    "Architecture": ["Photos/Architecture"],
    "Birds": ["Photos/Birds"],
    "Flowers": ["Photos/Flowers"],
    "Nature": {
        "Landscape": ["Photos/Nature/Landscape", "Photos/Nature/Landscape/Megamalai"],
        "Sunsets & Sunrises": ["Photos/Nature/Sunsets and Sunrises"],
        "Wildlife": ["Photos/Nature/Wildlife"]
    },
    "People": {
        "Portraits": ["Photos/People/Portraits"]
    },
    "Places": {
        "International": ["Photos/Places/International"],
        "National": ["Photos/Places/National", "Photos/Nature/Landscape/Megamalai"]
    }
}

OUTPUT_FILE = "index.html"

def generate_html():
    html_start = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Mohangraphy</title>
        <style>
            :root { --bg: #000; --menu-grey: #222; --text-white: #fff; --footer-bright: #fff; }
            body, html { height: 100%; margin: 0; background: var(--bg); color: var(--text-white); font-family: 'Inter', sans-serif; overflow: hidden; }
            
            /* 1. COMPLETELY FROZEN TOP SECTION */
            header {
                position: fixed; top: 0; width: 100%; 
                height: 200px; /* Increased height to fit everything */
                background: var(--bg); 
                display: flex; flex-direction: column; align-items: center; justify-content: center;
                z-index: 1000;
                border-bottom: 1px solid #1a1a1a;
            }
            .logo { 
                font-size: 42px; font-weight: 200; letter-spacing: 18px; 
                text-transform: uppercase; margin-bottom: 25px; color: var(--text-white); 
                line-height: 1;
            }
            
            nav { display: flex; list-style: none; padding: 0; margin: 0; gap: 12px; }
            .nav-item { position: relative; }
            .nav-item > a { 
                background: var(--menu-grey); color: var(--text-white); 
                padding: 14px 28px; text-decoration: none; font-size: 12px; 
                font-weight: 800; text-transform: uppercase; letter-spacing: 2px; 
                display: block; transition: 0.2s; border: 1px solid #333;
            }
            .nav-item:hover > a { background: #444; border-color: #555; }
            
            /* Dropdowns */
            .dropdown { display: none; position: absolute; top: 100%; left: 0; background: #111; border: 1px solid #333; min-width: 200px; z-index: 1001; }
            .nav-item:hover .dropdown { display: block; }
            .dropdown a { padding: 12px 20px; display: block; color: #aaa; text-decoration: none; font-size: 11px; border-bottom: 1px solid #222; }
            .dropdown a:hover { color: #fff; background: #222; }

            /* 2. SCROLLABLE GALLERY - Starts after the 200px header */
            main { 
                position: absolute; top: 200px; bottom: 70px; 
                width: 100%; overflow-y: auto; scroll-behavior: smooth; 
            }
            .container { max-width: 1600px; margin: 0 auto; padding: 60px 20px; }
            
            /* Photo Grid */
            .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(450px, 1fr)); gap: 20px; margin-bottom: 150px; }
            .img-wrapper { position: relative; overflow: hidden; background: #0a0a0a; height: 550px; cursor: pointer; }
            .grid img { width: 100%; height: 100%; object-fit: cover; filter: brightness(0.8); transition: 0.5s ease; }
            .img-wrapper:hover img { filter: brightness(1); transform: scale(1.02); }
            
            h1 { font-size: 32px; font-weight: 200; letter-spacing: 8px; border-left: 6px solid #fff; padding-left: 25px; margin-top: 100px; text-transform: uppercase; }
            .count { font-size: 13px; color: #444; margin-left: 20px; font-weight: 800; }

            /* 3. BRIGHTER FIXED FOOTER */
            footer {
                position: fixed; bottom: 0; width: 100%; height: 70px;
                background: #0a0a0a; border-top: 1px solid #222;
                display: flex; align-items: center; justify-content: center; gap: 60px;
                z-index: 1000;
            }
            footer a { color: var(--footer-bright); text-decoration: none; font-size: 12px; font-weight: 900; text-transform: uppercase; letter-spacing: 3px; transition: 0.3s; }
            footer a:hover { text-shadow: 0 0 15px #fff; }

            /* Lightbox */
            #lightbox { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.98); display: none; align-items: center; justify-content: center; z-index: 2000; }
            #lightbox img { max-width: 95%; max-height: 95%; object-fit: contain; }
        </style>
    </head>
    <body>

    <header>
        <div class="logo">Mohangraphy</div>
        <nav>
    """

    # 1. Navigation Builder (Grey Buttons)
    for main, content in STRUCTURE.items():
        m_id = main.replace(" ", "").replace("&", "")
        html_start += f'<div class="nav-item"><a href="#{m_id}">{main}</a>'
        if isinstance(content, dict):
            html_start += '<div class="dropdown">'
            for sub in content.keys():
                s_id = sub.replace(" ", "").replace("&", "")
                html_start += f'<a href="#{m_id}-{s_id}">{sub}</a>'
            html_start += '</div>'
        html_start += '</div>'
    
    html_start += "</nav></header><main><div class='container' id='top'>"

    # 2. Section Builder
    content_html = ""
    for main, content in STRUCTURE.items():
        m_id = main.replace(" ", "").replace("&", "")
        
        # Calculate image count
        img_list = []
        if isinstance(content, dict):
            for paths in content.values():
                for p in paths:
                    if os.path.exists(p):
                        img_list.extend([i for i in os.listdir(p) if i.lower().endswith(('.jpg','.jpeg','.png'))])
        else:
            for p in content:
                if os.path.exists(p):
                    img_list.extend([i for i in os.listdir(p) if i.lower().endswith(('.jpg','.jpeg','.png'))])
        
        content_html += f'<h1 id="{m_id}">{main} <span class="count">{len(set(img_list))} WORKS</span></h1>'
        
        def render_grid(paths):
            grid_html = '<div class="grid">'
            for path in paths:
                if os.path.exists(path):
                    for img in sorted(os.listdir(path)):
                        if img.lower().endswith(('.jpg', '.jpeg', '.png')):
                            img_path = os.path.join(path, img)
                            grid_html += f'''
                            <div class="img-wrapper" onclick="openLightbox('{img_path}')">
                                <img src="{img_path}" loading="lazy">
                            </div>'''
            return grid_html + "</div>"

        if isinstance(content, dict):
            for sub, paths in content.items():
                s_id = sub.replace(" ", "").replace("&", "")
                content_html += f'<div id="{m_id}-{s_id}"><h3>{sub}</h3>' + render_grid(paths) + "</div>"
        else:
            content_html += render_grid(content)

    footer = """
    </div></main>
    <footer>
        <a href="#top">Home</a>
        <a href="#top">Back to Top</a>
        <a href="https://instagram.com/mohangraphy" target="_blank">Instagram: @mohangraphy</a>
    </footer>

    <div id="lightbox" onclick="this.style.display='none'"><img id="lightbox-img"></div>

    <script>
        function openLightbox(src) {
            document.getElementById('lightbox-img').src = src;
            document.getElementById('lightbox').style.display = 'flex';
        }
    </script>
    </body></html>"""

    with open(OUTPUT_FILE, "w") as f:
        f.write(html_start + content_html + footer)
    print("✅ Build Complete: Mohangraphy logo and menu are now perfectly frozen at the top.")

if __name__ == "__main__":
    generate_html()