import os

# --- STRUCTURE CONFIGURATION (Matches image_329b9c.png) ---
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
            :root { --accent: #fff; --bg: #000; --text-dim: #555; }
            body, html { height: 100%; margin: 0; background: var(--bg); color: #fff; font-family: 'Inter', -apple-system, sans-serif; overflow: hidden; }
            
            /* STATIC TOP SECTION */
            header {
                position: fixed; top: 0; width: 100%; height: 150px;
                background: var(--bg); border-bottom: 1px solid #111;
                display: flex; flex-direction: column; align-items: center; justify-content: center;
                z-index: 1000;
            }
            .logo { font-size: 30px; font-weight: 200; letter-spacing: 12px; text-transform: uppercase; margin-bottom: 20px; color: var(--accent); }
            
            nav { display: flex; list-style: none; padding: 0; margin: 0; gap: 20px; }
            .nav-item { position: relative; }
            .nav-item a { color: var(--text-dim); text-decoration: none; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 2px; transition: 0.3s; }
            .nav-item:hover > a { color: var(--accent); }
            
            .dropdown { display: none; position: absolute; top: 100%; left: 0; background: #080808; border: 1px solid #111; min-width: 160px; padding: 10px 0; box-shadow: 0 10px 20px rgba(0,0,0,0.5); }
            .nav-item:hover .dropdown { display: block; }
            .dropdown a { padding: 8px 20px; display: block; text-transform: capitalize; color: #777; letter-spacing: 1px; }
            .dropdown a:hover { color: var(--accent); background: #111; }

            /* SCROLLABLE MIDDLE GALLERY */
            main { position: absolute; top: 150px; bottom: 60px; width: 100%; overflow-y: auto; scroll-behavior: smooth; }
            .container { max-width: 1600px; margin: 0 auto; padding: 40px 20px; }
            
            .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(400px, 1fr)); gap: 15px; margin-bottom: 100px; }
            
            /* IMAGE STYLING & HOVER */
            .img-wrapper { position: relative; overflow: hidden; background: #050505; height: 500px; cursor: zoom-in; }
            .grid img { width: 100%; height: 100%; object-fit: cover; opacity: 0; transition: opacity 0.8s, transform 0.8s ease; filter: brightness(0.8); }
            .grid img.loaded { opacity: 1; }
            .img-wrapper:hover img { transform: scale(1.03); filter: brightness(1); }
            
            /* HOVER CAPTION */
            .caption { position: absolute; bottom: 0; left: 0; width: 100%; padding: 20px; background: linear-gradient(transparent, rgba(0,0,0,0.8)); font-size: 10px; letter-spacing: 1px; color: #fff; opacity: 0; transition: 0.3s; pointer-events: none; }
            .img-wrapper:hover .caption { opacity: 1; }

            h1 { font-size: 22px; font-weight: 300; letter-spacing: 5px; border-left: 3px solid var(--accent); padding-left: 15px; margin-top: 60px; text-transform: uppercase; display: flex; align-items: baseline; }
            .count { font-size: 10px; color: #333; margin-left: 15px; font-weight: 700; }

            /* STATIC BOTTOM SECTION */
            footer {
                position: fixed; bottom: 0; width: 100%; height: 60px;
                background: var(--bg); border-top: 1px solid #111;
                display: flex; align-items: center; justify-content: center; gap: 40px;
                z-index: 1000;
            }
            footer a { color: var(--text-dim); text-decoration: none; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 2px; transition: 0.3s; }
            footer a:hover { color: var(--accent); }

            /* LIGHTBOX (MODAL) */
            #lightbox { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.95); display: none; align-items: center; justify-content: center; z-index: 2000; }
            #lightbox img { max-width: 90%; max-height: 90%; object-fit: contain; box-shadow: 0 0 50px rgba(0,0,0,1); }
            #lightbox:target { display: flex; }

            /* MOBILE FIXES */
            @media (max-width: 768px) {
                header { height: 120px; }
                main { top: 120px; }
                .grid { grid-template-columns: 1fr; }
                .logo { font-size: 22px; letter-spacing: 6px; }
                nav { gap: 10px; }
                .nav-item a { font-size: 8px; }
            }
        </style>
    </head>
    <body>

    <header>
        <div class="logo">Mohangraphy</div>
        <ul class="nav">
    """

    # 1. Navigation Builder
    for main, content in STRUCTURE.items():
        m_id = main.replace(" ", "").replace("&", "")
        html_start += f'<li class="nav-item"><a href="#{m_id}">{main}</a>'
        if isinstance(content, dict):
            html_start += '<div class="dropdown">'
            for sub in content.keys():
                s_id = sub.replace(" ", "").replace("&", "")
                html_start += f'<a href="#{m_id}-{s_id}">{sub}</a>'
            html_start += '</div>'
        html_start += '</li>'
    
    html_start += "</ul></header><main><div class='container' id='top'>"

    # 2. Section Builder with Counts
    content_html = ""
    for main, content in STRUCTURE.items():
        m_id = main.replace(" ", "").replace("&", "")
        
        # Calculate Image Count for the category
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
                            name = img.split('.')[0].replace('_', ' ')
                            grid_html += f'''
                            <div class="img-wrapper" onclick="openLightbox('{img_path}')">
                                <img data-src="{img_path}" class="lazy" alt="{name}">
                                <div class="caption">{name}</div>
                            </div>'''
            return grid_html + "</div>"

        if isinstance(content, dict):
            for sub, paths in content.items():
                s_id = sub.replace(" ", "").replace("&", "")
                content_html += f'<div id="{m_id}-{s_id}"><h3>{sub}</h3>' + render_grid(paths) + "</div>"
        else:
            content_html += render_grid(content)

    # 3. Footer, Lightbox, and Javascript (Lazy Loading & Modal)
    footer = """
    </div></main>
    <footer>
        <a href="#top">Home</a>
        <a href="#top">Back to Top</a>
        <a href="https://instagram.com/mohangraphy" target="_blank">@mohangraphy</a>
    </footer>

    <div id="lightbox" onclick="this.style.display='none'"><img id="lightbox-img"></div>

    <script>
        // Lightbox Logic
        function openLightbox(src) {
            document.getElementById('lightbox-img').src = src;
            document.getElementById('lightbox').style.display = 'flex';
        }

        // Lazy Loading Logic
        document.addEventListener("DOMContentLoaded", function() {
            var lazyImages = [].slice.call(document.querySelectorAll("img.lazy"));
            if ("IntersectionObserver" in window) {
                let imgObserver = new IntersectionObserver(function(entries, observer) {
                    entries.forEach(function(entry) {
                        if (entry.isIntersecting) {
                            let img = entry.target;
                            img.src = img.dataset.src;
                            img.classList.add("loaded");
                            imgObserver.unobserve(img);
                        }
                    });
                });
                lazyImages.forEach(function(img) { imgObserver.observe(img); });
            }
        });
    </script>
    </body></html>"""

    with open(OUTPUT_FILE, "w") as f:
        f.write(html_start + content_html + footer)
    print("✨ SUCCESS: Portfolio built with Lightbox, Lazy Loading, and Metadata.")

if __name__ == "__main__":
    generate_html()