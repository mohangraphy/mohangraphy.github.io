import os

# This looks for the parent folder of the 'scripts' folder
BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_FILE = os.path.join(BASE_PATH, "index.html")

def generate_mohangraphy():
    # --- High-End Photography CSS ---
    css = """
    :root { --bg: #050505; --text: #ffffff; --accent: #a0a0a0; --dim: #444; }
    body { margin: 0; background: var(--bg); color: var(--text); font-family: 'Inter', -apple-system, sans-serif; line-height: 1.6; }
    
    header { padding: 150px 20px 100px; text-align: center; }
    h1 { font-size: 3.5rem; letter-spacing: 15px; text-transform: uppercase; font-weight: 200; margin: 0; }
    .subtitle { font-size: 0.8rem; letter-spacing: 5px; color: var(--accent); text-transform: uppercase; margin-top: 15px; }
    
    .container { max-width: 1300px; margin: 0 auto; padding: 0 30px; }
    
    /* Section Headings */
    h2 { font-size: 1.1rem; letter-spacing: 6px; text-transform: uppercase; margin: 100px 0 40px; border-bottom: 1px solid #1a1a1a; padding-bottom: 15px; color: var(--accent); }
    h3 { font-size: 0.8rem; color: var(--dim); text-transform: uppercase; margin-bottom: 25px; letter-spacing: 2px; }
    
    /* Gallery Grid */
    .gallery { display: grid; grid-template-columns: repeat(auto-fill, minmax(400px, 1fr)); gap: 30px; }
    .photo-card { overflow: hidden; background: #000; cursor: pointer; text-decoration: none; display: block; position: relative; }
    .photo-card img { width: 100%; height: 500px; object-fit: cover; transition: all 1s ease; filter: grayscale(100%) brightness(0.7); }
    .photo-card:hover img { transform: scale(1.05); filter: grayscale(0%) brightness(1); }
    
    /* Profile & Contact */
    .profile-section { margin-top: 150px; padding: 120px 0; border-top: 1px solid #1a1a1a; display: grid; grid-template-columns: 1fr 1fr; gap: 80px; }
    .bio h4, .contact-info h4 { font-size: 1.2rem; text-transform: uppercase; letter-spacing: 4px; margin-bottom: 30px; font-weight: 400; }
    .bio p { color: var(--accent); font-size: 1rem; line-height: 2; font-weight: 300; }
    .contact-links a { display: block; color: var(--text); text-decoration: none; margin-bottom: 15px; font-size: 0.9rem; letter-spacing: 1px; }
    .contact-links a:hover { color: var(--accent); }
    
    /* Full-Screen Lightbox */
    .lightbox { display: none; position: fixed; z-index: 1000; top: 0; left: 0; width: 100%; height: 100%; background: #000; align-items: center; justify-content: center; }
    .lightbox img { max-width: 95%; max-height: 95%; object-fit: contain; }
    .lightbox:target { display: flex; }
    .close-btn { position: absolute; top: 40px; right: 40px; color: #fff; font-size: 2rem; text-decoration: none; font-weight: 100; }
    
    footer { padding: 100px 20px; text-align: center; font-size: 0.6rem; color: var(--dim); letter-spacing: 3px; text-transform: uppercase; }
    @media (max-width: 768px) { 
        .profile-section { grid-template-columns: 1fr; text-align: center; } 
        h1 { font-size: 2rem; }
        .gallery { grid-template-columns: 1fr; }
    }
    """

    content_html = ""
    valid_exts = ('.jpg', '.jpeg', '.png', '.webp')
    
    # Exclude scripts and Git files
    categories = sorted([d for d in os.listdir(BASE_PATH) 
                        if os.path.isdir(os.path.join(BASE_PATH, d)) 
                        and d not in ["scripts", ".git", "CNAME"] 
                        and not d.startswith('.')])
    
    for cat in categories:
        cat_path = os.path.join(BASE_PATH, cat)
        content_html += f"<h2>{cat}</h2>"
        
        locations = sorted([d for d in os.listdir(cat_path) 
                           if os.path.isdir(os.path.join(cat_path, d)) 
                           and not d.startswith('.')])
        
        for loc in locations:
            loc_path = os.path.join(cat_path, loc)
            images = sorted([f for f in os.listdir(loc_path) if f.lower().endswith(valid_exts)])
            
            if images:
                content_html += f"<h3>{loc}</h3><div class='gallery'>"
                for img in images:
                    rel_path = f"{cat}/{loc}/{img}"
                    # Create a safe ID for the lightbox
                    img_id = "".join(filter(str.isalnum, img))
                    content_html += f"""
                    <a href="#{img_id}" class="photo-card"><img src="{rel_path}" loading="lazy"></a>
                    <div id="{img_id}" class="lightbox">
                        <a href="#" class="close-btn">&times;</a>
                        <img src="{rel_path}">
                    </div>"""
                content_html += '</div>'

    # --- HTML Shell ---
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
        <header>
            <h1>Mohangraphy</h1>
            <div class="subtitle">Nature & Wildlife Photography</div>
        </header>

        <div class="container">
            {content_html}

            <section class="profile-section">
                <div class="bio">
                    <h4>The Artist</h4>
                    <p>
                        Based in Bangalore, I specialize in capturing the quiet, 
                        unseen moments of the natural world. My work in Megamalai 
                        focuses on the interplay of light and landscape in one 
                        of India's most pristine environments.
                    </p>
                </div>
                <div class="contact-info">
                    <h4>Inquiries</h4>
                    <div class="contact-links">
                        <a href="mailto:hello@mohangraphy.com">Email: hello@mohangraphy.com</a>
                        <a href="https://instagram.com/mohangraphy" target="_blank">Instagram: @mohangraphy</a>
                        <a href="#">Gallery: Bangalore, India</a>
                    </div>
                </div>
            </section>
        </div>

        <footer>&copy; 2026 MOHANGRAPHY. All Rights Reserved.</footer>
    </body>
    </html>
    """

    with open(OUTPUT_FILE, "w") as f:
        f.write(full_html)
    print(f"✨ Portfolio generated successfully at: {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_mohangraphy()