import os
import random

# --- STRUCTURE CONFIGURATION (Reflecting your folder hierarchy) ---
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
    # Targets Landscape for the home screen slideshow
    path = "Photos/Nature/Landscape"
    if os.path.exists(path):
        photos = [os.path.join(path, f) for f in os.listdir(path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        # Randomly select 10 unique photos
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
                background: linear-gradient(to bottom, rgba(0,0,0,1) 75%, rgba(0,0,0,0)); 
                display: flex; flex-direction: column; align-items: center; justify-content: center; z-index: 1000;
            }}
            .logo {{ font-size: 48px; font-weight: 200; letter-spacing: 20px; text-transform: uppercase; margin-bottom: 30px; }}
            
            nav {{ display: flex; gap: 15px; }}
            .nav-item > a {{ 
                background: var(--menu-grey); color: var(--text-white); padding: 14px 28px; 
                text-decoration: none; font-size: 11px; font-weight: 800; text-transform: uppercase; 
                letter-spacing: 2px; display: block; border: 1px solid #333; transition: 0.3s;
            }}
            .nav-item:hover > a {{ background: #444; border-color: #555; }}

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
                opacity: 0.45; 
                animation: kenburns 12s infinite alternate ease-in-out;
            }}

            @keyframes kenburns {{
                from {{ transform: scale(1); }}
                to {{ transform: scale(1.12); }}
            }}

            /* GALLERY AREA */
            main {{ 
                position: absolute; top: 220px; bottom: 75px; width: 100%; 
                overflow-y: auto; display: none; background: var(--bg); z-index: 500; scroll-behavior: smooth;
            }}
            .container {{ max-width: 1600px; margin: 0 auto; padding: 40px 20px; }}
            .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(450px, 1fr)); gap: 15px; margin-bottom: 120px; }}
            .grid img {{ width: 100%; height: 500px; object-fit: