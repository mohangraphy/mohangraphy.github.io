import os
import subprocess

# --- CONFIGURATION ---
TOKEN = "YOUR_TOKEN_HERE"  # Your ghp_... token
USER = "mohangraphy"
REPO = "mohangraphy.github.io"
# ---------------------

def deploy():
    # Set working directory to Mohangraphy root
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(root_dir)
    
    print(f"🚀 Repairing and Syncing with https://{REPO}...")

    # 1. Update the Git Remote
    # This forces the Mac to use the correct Primary URL and Token
    remote_url = f"https://{USER}:{TOKEN}@github.com/{USER}/{REPO}.git"
    subprocess.run(["git", "remote", "remove", "origin"], capture_output=True)
    subprocess.run(["git", "remote", "add", "origin", remote_url])

    # 2. Run the Build Script to update HTML
    build_script = os.path.join(root_dir, "Scripts", "build_mohangraphy.py")
    if os.path.exists(build_script):
        print("🔨 Regenerating index.html...")
        subprocess.run(["python3", build_script])

    # 3. Push to GitHub
    try:
        subprocess.run(["git", "add", "."], check=True)
        # Commit might fail if no new changes, so we ignore the error
        subprocess.run(["git", "commit", "-m", "Portfolio update to primary domain"], capture_output=True)
        
        print("📤 Uploading files...")
        result = subprocess.run(["git", "push", "-u", "origin", "main"], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"\n✅ SUCCESS! Your site is live at: https://{REPO}/")
        else:
            print(f"\n❌ Error: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Python Error: {e}")

if __name__ == "__main__":
    deploy()