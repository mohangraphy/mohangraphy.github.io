import os
import subprocess

# --- CONFIGURATION ---
# Ensure this includes the 'ghp_' prefix!
TOKEN = "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" 
USER = "mohangraphy"
REPO = "mohangraphy.github.io"
# ---------------------

def deploy_portfolio():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(script_dir)
    os.chdir(root_dir)
    
    print(f"🚀 Final Sync Attempt for: {REPO}")

    # Resetting the remote to use the token-embedded URL
    # Format: https://token@github.com/user/repo.git
    remote_url = f"https://{TOKEN}@github.com/{USER}/{REPO}.git"
    
    subprocess.run(["git", "remote", "remove", "origin"], capture_output=True)
    subprocess.run(["git", "remote", "add", "origin", remote_url])

    # 1. Run the Build
    build_script = os.path.join(script_dir, "build_mohangraphy.py")
    if os.path.exists(build_script):
        subprocess.run(["python3", build_script])
        print("🔨 Gallery rebuilt.")

    # 2. Push to GitHub
    try:
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", "Switch to primary domain"], capture_output=True)
        
        print(f"📤 Pushing to https://github.com/{USER}/{REPO}...")
        result = subprocess.run(["git", "push", "-u", "origin", "main", "--force"], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"\n✅ SUCCESS! Site is live: https://{REPO}")
        else:
            print(f"\n❌ STILL NOT FOUND")
            print(f"Details: {result.stderr}")
            print("\n🚨 STOP! Please check your browser. If the repo name isn't exactly")
            print(f"'{REPO}', this script cannot find the target.")
            
    except Exception as e:
        print(f"❌ Python Error: {e}")

if __name__ == "__main__":
    deploy_portfolio()