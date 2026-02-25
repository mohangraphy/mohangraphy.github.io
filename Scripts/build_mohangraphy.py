import os

# Configuration
# This points to the main 'Mohangraphy' folder
BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_FILE = os.path.join(BASE_PATH, "index.html")

def generate_mohangraphy():
    # --- Professional Minimalist CSS ---
    css = """
    :root { --bg: #050505; --text: #ffffff; --accent: #a0a0a0; --dim: #444; }
    body { margin: 0; background: var(--bg); color: var(--text); font-family: 'Inter', sans-serif; line-height: 1.6; }
    header { padding: 120px 20px; text-align: center; }
    h1 { font-size: 3rem; letter-spacing: 12px; text-transform: uppercase; font-weight: 200; margin: 0; }
    .container { max-width: 1200px; margin: 0 auto; padding: 0 30px; }
    h2 { font-size: 1.1rem; letter-spacing: 5px; text-transform: uppercase; margin: 80px 0 30px; border-bottom: 1px solid #222; padding-bottom: 10px; color: var(--accent); }
    .gallery { display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 25px; }
    .photo-card img { width: 100%; height: 450px; object-fit: cover; transition: 0.6s ease; filter: grayscale(80%) brightness(0.7); }
    .photo-card:hover img { transform: scale(1.02); filter: grayscale(0%) brightness(1); }
    .profile-section { margin-top: 100px; padding: 80px 0; border-top: 1px solid #222; display: grid; grid-template-columns: 1fr 1fr; gap: 50px; }
    footer { padding: 50px; text-align: center; font-size: 0.7rem; color: var(--dim); letter-spacing: 2px; }
    """

    content_html = ""
    valid_exts = ('.jpg', '.jpeg', '.png', '.webp')
    
    # SAFETY UPDATE: Filter out 'scripts', '.git', and any file/folder containing 'Token'
    categories = sorted([d for d in os.listdir(BASE_PATH) 
                        if os.path.isdir(os.path.join(BASE_PATH, d)) 
                        and d not in ["scripts", ".git", "CNAME"] 
                        and "Token" not in d
                        and not d.startswith('.')])
    
    for cat in categories:
        cat_path = os.path.join(BASE_PATH, cat)
        content_html += f"<h2>{cat}</h2><div class='gallery'>"
        
        # Get all images in this category (including subfolders)
        for root, dirs, files in os.walk(cat_path):
            for img in sorted(files):
                if img.lower().endswith(valid_exts):
                    rel_path = os.path.relpath(os.path.join(root, img), BASE_PATH)
                    content_html += f'<div class="photo-card"><img src="{rel_path}" loading="lazy"></div>'
        content_html += '</div>'

    full_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Mohangraphy | Portfolio</title>
        <style>{css}</style>
    </head>
    <body>
        <header><h1>Mohangraphy</h1></header>
        <div class="container">
            {content_html}
            <section class="profile-section">
                <div><h4>About</h4><p>Nature & Wildlife Photographer based in Bangalore.</p></div>
                <div><h4>Contact</h4><p>Email: hello@mohangraphy.com<br>Instagram: @mohangraphy</p></div>
            </section>
        </div>
        <footer>&copy; 2026 MOHANGRAPHY</footer>
    </body>
    </html>
    """

    with open(OUTPUT_FILE, "w") as f:
        f.write(full_html)
    print(f"✨ Website updated successfully at {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_mohangraphy()