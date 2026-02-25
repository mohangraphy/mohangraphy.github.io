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

    # 1.5 NEW: RUN THE MEGAMALAI FIXER
    # This ensures those 20 photos are always tagged correctly before building
    print("📍 Step 1.5: Applying Megamalai & Mountains tags...")
    try:
        subprocess.run([sys.executable, "Scripts/fix_megamalai.py"], check=True)
    except Exception as e:
        print(f"⚠️ Megamalai fixer skipped or failed: {e}")

    # 2. RUN THE BUILDER
    print("🔨 Step 2: Building the gallery from your index...")
    subprocess.run([sys.executable, "Scripts/build_mohangraphy.py"], check=True)

    # 3. SYNC TO GITHUB
    print("📤 Step 3: Syncing to GitHub...")
    subprocess.run(["git", "add", "."], check=True)
    
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    commit_msg = f"Gallery Index Update: {timestamp}"
    
    # We hide the output of commit/push to keep your terminal clean
    subprocess.run(["git", "commit", "-m", commit_msg], capture_output=True)
    subprocess.run(["git", "push", "origin", "main", "--force"], capture_output=True)
    
    print(f"✅ DEPLOYMENT COMPLETE at {timestamp}")
    print("--- Use 'Cmd + Shift + R' in your browser in 60 seconds ---\n")

if __name__ == "__main__":
    master_deploy()