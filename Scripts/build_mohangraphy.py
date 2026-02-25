import os

# Configuration
BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_FILE = os.path.join(BASE_PATH, "index.html")

def generate_mohangraphy():
    # --- Professional CSS ---
    css = """
    :root { --bg: #050505; --text: #e0e0e0; --accent: #888; --dim: #555; }
    body { margin: 0; background: var(--bg); color: var(--text); font-family: 'Inter', -apple-system, sans-serif; line-height: 1.6; }
    
    header { padding: 120px 20px; text-align: center; }
    h1 { font-size: 3rem; letter-spacing: 12px; text-transform: uppercase; font-weight: 100; margin: 0; }
    
    .container { max-width: 1200px; margin: 0 auto; padding: 0 20px; }
    
    /* Gallery Styles */
    h2 { font-size: 1.2rem; letter-spacing: 4px; text-transform: uppercase; margin: 80px 0 30px; border-bottom: 1px solid #222; padding-bottom: 10px; color: var(--accent); }
    h3 { font-size: 0.9rem; color: var(--dim); text-transform: uppercase; margin-bottom: 20px; }
    .gallery { display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 20px; }
    .photo-card { overflow: hidden; background: #111; cursor: pointer; text-decoration: none; display: block; }
    .photo-card img { width: 100%; height: 400px; object-fit: cover; transition: transform 0.8s ease, filter 0.5s ease; filter: grayscale(50%) brightness(0.7); }
    .photo-card:hover img { transform: scale(1.03); filter: grayscale(0%) brightness(1); }
    
    /* About & Contact Sections */
    .profile-section { margin-top: 150px; padding: 100px 0; border-top: 1px solid #222; display: grid; grid-template-columns: 1fr 1fr; gap: 50px; align-items: center; }
    .bio h4 { font-size: 1.5rem; text-transform: uppercase; letter-spacing: 3px; margin-bottom: 20px; }
    .bio p { color: var(--accent); font-size: 1rem; line-height: 1.8; }
    
    .contact-info h4 { font-size: 1.5rem; text-transform: uppercase; letter-spacing: 3px; margin-bottom: 20px; }
    .contact-links a { display: block; color: var(--text); text-decoration: none; margin-bottom: 10px; font-size: 0.9rem; transition: color 0.3s; }
    .contact-links a:hover { color: #fff; text-decoration: underline; }
    
    /* Lightbox */
    .lightbox { display: none; position: fixed; z-index: 999; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.98); align-items: center; justify-content: center; }
    .lightbox img { max-width: 90%; max-height: 90%; }
    .lightbox:target { display: flex; }
    
    footer { padding: 60px 20px; text-align: center; font-size: 0.7rem; color: var(--dim); letter-spacing: 2px; text-transform: uppercase; }
    
    @media (max-width: 768px) { .profile-section { grid-template-columns: 1fr; text-align: center; } }
    """

    # --- Section Logic ---
    content_html = ""
    valid_exts = ('.jpg', '.jpeg', '.png', '.webp')
    categories = sorted([d for d in os.listdir(BASE_PATH) if os.path.isdir(os.path.join(BASE_PATH, d)) and d not in ["scripts", "CNAME"] and not d.startswith('.')])
    
    for cat in categories:
        cat_path = os.path.join(BASE_PATH, cat)
        content_html += f"<h2>{cat}</h2>"
        locations = sorted([d for d in os.listdir(cat_path) if os.path.isdir(os.path.join(cat_path, d)) and not d.startswith('.')])
        
        for loc in locations:
            loc_path = os.path.join(cat_path, loc)
            images = sorted([f for f in os.listdir(loc_path) if f.lower().endswith(valid_exts)])
            if images:
                content_html += f"<h3>{loc}</h3><div class='gallery'>"
                for img in images:
                    rel_path = f"{cat}/{loc}/{img}"
                    img_id = "".join(filter(str.isalnum, img))
                    content_html += f'<a href="#{img_id}" class="photo-card"><img src="{rel_path}"></a>'
                    content_html += f'<div id="{img_id}" class="lightbox" onclick="window.location.href=\'#\'"><img src="{rel_path}"></div>'
                content_html += '</div>'

    # --- The Final HTML Assembly ---
    full_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Mohangraphy | Nature & Wildlife</title>
        <style>{css}</style>
    </head>
    <body>
        <header><h1>Mohangraphy</h1></header>

        <div class="container">
            {content_html}

            <section class="profile-section">
                <div class="bio">
                    <h4>About Me</h4>
                    <p>
                        I am a photographer focused on the raw beauty of nature and wildlife. 
                        From the misty hills of Megamalai to the streets of Bangalore, 
                        my work is an attempt to capture moments of stillness and character 
                        in a fast-moving world.
                    </p>
                </div>
                <div class="contact-info">
                    <h4>Get In Touch</h4>
                    <div class="contact-links">
                        <a href="mailto:your-email@example.com">Email: hello@mohangraphy.com</a>
                        <a href="https://instagram.com/yourprofile" target="_blank">Instagram: @Mohangraphy</a>
                        <a href="#">Based in Bangalore, India</a>
                    </div>
                </div>
            </section>
        </div>

        <footer>&copy; 2026 MOHANGRAPHY | All Rights Reserved</footer>
    </body>
    </html>
    """

    with open(OUTPUT_FILE, "w") as f:
        f.write(full_html)
    print(f"Success! Portfolio with About/Contact generated at: {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_mohangraphy()