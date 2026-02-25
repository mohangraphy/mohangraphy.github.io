import os
import subprocess
import time
import sys

def master_deploy():
    # Ensure we are in the right directory
    root_dir = "/Users/ncm/Pictures/Mohangraphy"
    os.chdir(root_dir)
    
    print("\n--- STARTING MOHANGRAPHY WORKFLOW ---")

    # 1. RUN THE CURATOR
    print("🔍 Step 1: Scanning for un-indexed photos...")
    try:
        subprocess.run([sys.executable, "Scripts/curator.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Curator failed or was closed early: {e}")

    # 2. RUN THE MEGAMALAI FIXER
    print("📍 Step 2: Applying Megamalai & Mountains tags...")
    try:
        subprocess.run([sys.executable, "Scripts/fix_megamalai.py"], check=True)
    except Exception as e:
        print(f"⚠️ Megamalai fixer skipped or failed: {e}")

    # 3. RUN THE BUILDER (Claude version)
    print("🔨 Step 3: Building the gallery from your index...")
    subprocess.run([sys.executable, "Scripts/Claude_mohangraphy.py"], check=True)

    # 4. SYNC TO GITHUB
    print("📤 Step 4: Syncing to GitHub...")
    subprocess.run(["git", "add", "."], check=True)
    
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    commit_msg = f"Gallery Index Update: {timestamp}"
    
    subprocess.run(["git", "commit", "-m", commit_msg], capture_output=True)
    subprocess.run(["git", "push", "origin", "main", "--force"], capture_output=True)
    
    print(f"✅ DEPLOYMENT COMPLETE at {timestamp}")
    print("--- Use 'Cmd + Shift + R' in your browser in 60 seconds ---\n")

if __name__ == "__main__":
    master_deploy()
