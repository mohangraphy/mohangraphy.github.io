import os
import subprocess

# --- CONFIGURATION ---
TOKEN = "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" 
USER = "mohangraphy"
REPO = "mohangraphy.github.io"
# ---------------------

def run_deployment():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(root)
    
    # 1. Build the index.html first
    subprocess.run(["python3", "Scripts/build_mohangraphy.py"])

    # 2. Push to GitHub
    try:
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", "Portfolio Structure Finalized"], capture_output=True)
        
        # Link to the public repo
        remote_url = f"https://{TOKEN}@github.com/{USER}/{REPO}.git"
        subprocess.run(["git", "remote", "set-url", "origin", remote_url])
        
        print(f"📤 Syncing to https://{REPO}...")
        subprocess.run(["git", "push", "-u", "origin", "main", "--force"], check=True)
        print(f"\n✨ SUCCESS! Your gallery is live with the new structure.")
    except Exception as e:
        print(f"❌ Deployment Failed: {e}")

if __name__ == "__main__":
    run_deployment()