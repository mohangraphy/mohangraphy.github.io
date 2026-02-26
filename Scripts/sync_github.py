import subprocess
import os
from datetime import datetime

REPO_DIR = "/Users/ncm/Pictures/Mohangraphy"

def sync_to_github():
    os.chdir(REPO_DIR)
    try:
        print("🔄 Syncing your clean local files to GitHub...")
        # Stage everything (all photos and scripts)
        subprocess.run(["git", "add", "-A"], check=True)
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        subprocess.run(["git", "commit", "-m", f"Clean Sync: {timestamp}"], capture_output=True)
        
        # Push via SSH
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print(f"✅ SUCCESS: GitHub is now updated and clean.")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Git Error: {e}")

if __name__ == "__main__":
    sync_to_github()
