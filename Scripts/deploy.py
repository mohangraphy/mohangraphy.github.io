import os
import subprocess

# --- CONFIGURATION ---
# IMPORTANT: Paste the FULL token here. It MUST start with ghp_
TOKEN = "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" 
USER = "mohangraphy"
REPO = "mohangraphy.github.io"
# ---------------------

def final_rescue_deploy():
    # Set the directory to your Mohangraphy folder
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(script_dir)
    os.chdir(root_dir)
    
    print(f"🚀 Starting Final Rescue for: {REPO}")

    # 1. THE FIX: We use the 'token@github' format which is the most reliable
    # We remove the old 'origin' and add a fresh one with the new credentials
    remote_url = f"https://{TOKEN}@github.com/{USER}/{REPO}.git"
    
    subprocess.run(["git", "remote", "remove", "origin"], capture_output=True)
    subprocess.run(["git", "remote", "add", "origin", remote_url])
    
    print("🔗 Connection refreshed with new token.")

    # 2. Run the Build Script
    build_script = os.path.join(script_dir, "build_mohangraphy.py")
    if os.path.exists(build_script):
        print("🔨 Regenerating your photo gallery...")
        subprocess.run(["python3", build_script])

    # 3. Push to GitHub
    try:
        subprocess.run(["git", "add", "."], check=True)
        # We use a placeholder commit message
        subprocess.run(["git", "commit", "-m", "Manual fix for authentication"], capture_output=True)
        
        print("📤 Uploading to GitHub (this may take a moment)...")
        # We use --force to ensure it overwrites the old 'mohangraphy' repo history
        result = subprocess.run(["git", "push", "-u", "origin", "main", "--force"], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"\n✅ SUCCESS! Your site is finally live.")
            print(f"🌍 View it here: https://{REPO}")
        else:
            print(f"\n❌ STILL FAILING")
            print(f"GitHub says: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Script Error: {e}")

if __name__ == "__main__":
    final_rescue_deploy()