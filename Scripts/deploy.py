import os
import subprocess
import time

def master_deploy():
    # 1. Path Setup
    root_dir = "/Users/ncm/Pictures/Mohangraphy"
    os.chdir(root_dir)
    
    # 2. Run the Master Build Script
    print("🔨 Building the Master Cinematic Gallery...")
    subprocess.run(["python3", "Scripts/build_mohangraphy.py"])

    # 3. Add, Commit, and Force Push
    print("📤 Forcing push to GitHub...")
    try:
        subprocess.run(["git", "add", "."], check=True)
        
        # We use a unique timestamp in the message to force GitHub to refresh
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        commit_msg = f"Master Build Refresh: {timestamp}"
        
        subprocess.run(["git", "commit", "-m", commit_msg], capture_output=True)
        
        # Use --force to ensure the remote repository matches your Mac exactly
        result = subprocess.run(["git", "push", "origin", "main", "--force"], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"\n✅ SUCCESS! Site pushed at {timestamp}")
            print("💡 IMPORTANT: Wait 60 seconds, then use 'Cmd + Shift + R' to refresh.")
        else:
            print(f"❌ Error: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Script Error: {e}")

if __name__ == "__main__":
    master_deploy()