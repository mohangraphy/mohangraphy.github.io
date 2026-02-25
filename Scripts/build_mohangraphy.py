import os

# --- MAPPING THE NEW STRUCTURE ---
# This matches your image_329b9c.png exactly
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
        "National": ["Photos/Places/National", "Photos/Nature/Landscape/Megamalai"] # Cross-links Megamalai here
    }
}

OUTPUT_FILE = "index.html"

def generate_html():
    html_start = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Mohangraphy | Portfolio</title>
        <style>
            body { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background: #050505; color: #fff; margin: 0; }
            
            /* Horizontal Top Nav */
            nav { 
                background: #000; 
                display: flex; 
                justify-content: center; 
                position: sticky; 
                top: 0; 
                z-index: 999; 
                border-bottom: 1px solid #222; 
            }
            .nav-menu { display: flex; list-style: none; margin: 0; padding: 0; }
            .nav-item { position: relative; padding: 25px 20px; }
            .nav-item a { color: #888; text-decoration: none; font-weight: bold; text-transform: uppercase; letter-spacing: 2px; font-size: 13px; }
            .nav-item:hover > a { color: #fff; }

            /* Pull-down Dropdowns */
            .dropdown { 
                display: none; 
                position: absolute; 
                top: 100%; 
                left: 0; 
                background: #111; 
                min-width: 200px; 
                border: 1px solid #222; 
                box-shadow: 0 10px 20px rgba(0,0,0,0.5);
            }
            .nav-item:hover .dropdown { display: block; }
            .dropdown a { 
                padding: 15px 20px; 
                display: block; 
                font-size: 12px; 
                border-bottom: 1px solid #1a1a1a; 
                text-transform: capitalize; 
            }
            .dropdown a:hover { background: #222; color: #fff; }

            /* Gallery Layout */
            .container { padding: 50px 5%; max-width: 1400px; margin: auto; }
            .grid { 
                display: grid; 
                grid-template-columns: repeat(auto-fill, minmax(400px, 1fr)); 
                gap: 25px; 
                margin-bottom: 70px; 
            }
            .grid img { 
                width: 100%; 
                height: 450px; 
                object-fit: cover; 
                border-radius: 3px; 
                transition: 0.4s; 
                filter: grayscale(30%); 
            }
            .grid img:hover { filter: grayscale(0%); transform: scale(1.01); }
            
            h1 { font-weight: 200; font-size: 35px; letter-spacing: 5px; text-transform: uppercase; margin-bottom: 30px; border-left: 5px solid #fff; padding-left: 20px; }
            h3 { color: #555; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 20px; }
        </style>
    </head>
    <body><nav><ul class="nav-menu">"""

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
    
    html_start += "</ul></nav><div class='container'>"

    # 2. Section Content Builder
    content_html = ""
    for main, content in STRUCTURE.items():
        m_id = main.replace(" ", "").replace("&", "")
        content_html += f'<h1 id="{m_id}">{main}</h1>'
        
        if isinstance(content, dict):
            for sub, paths in content.items():
                s_id = sub.replace(" ", "").replace("&", "")
                content_html += f'<div id="{m_id}-{s_id}"><h3>{sub}</h3><div class="grid">'
                for path in paths:
                    if os.path.exists(path):
                        for img in sorted(os.listdir(path)):
                            if img.lower().endswith(('.jpg', '.jpeg', '.png')):
                                content_html += f'<img src="{os.path.join(path, img)}" loading="lazy">'
                content_html += "</div></div>"
        else:
            content_html += '<div class="grid">'
            for path in content:
                if os.path.exists(path):
                    for img in sorted(os.listdir(path)):
                        if img.lower().endswith(('.jpg', '.jpeg', '.png')):
                            content_html += f'<img src="{os.path.join(path, img)}" loading="lazy">'
            content_html += "</div>"

    with open(OUTPUT_FILE, "w") as f:
        f.write(html_start + content_html + "</div></body></html>")
    print("✅ Build Complete: Categories and 'Megamalai' cross-linking are ready.")

if __name__ == "__main__":
    generate_html()