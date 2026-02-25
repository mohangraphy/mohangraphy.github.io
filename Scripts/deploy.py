import os
import subprocess

# --- CONFIGURATION ---
USER = "mohangraphy"
REPO = "mohangraphy.github.io"
# ---------------------

def ssh_deploy():
    # Identify the folder path
    script_path = os.path.abspath(__file__)
    root_dir = os.path.dirname(os.path.dirname(script_path))
    os.chdir(root_dir)
    
    # 1. Build the gallery (Handling Megamalai/Categories)
    print("🔨 Building your categorized gallery...")
    subprocess.run(["python3", "Scripts/build_mohangraphy.py"])

    # 2. Ensure we are using the SSH URL
    ssh_url = f"git@github.com:{USER}/{REPO}.git"
    subprocess.run(["git", "remote", "remove", "origin"], capture_output=True)
    subprocess.run(["git", "remote", "add", "origin", ssh_url])

    # 3. Push the files
    print(f"📤 Uploading via SSH key...")
    try:
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", "Final SSH Setup"], capture_output=True)
        
        # Force push to main branch
        result = subprocess.run(["git", "push", "-u", "origin", "main", "--force"], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"\n✅ SUCCESS! Site is live: https://{REPO}")
        else:
            print(f"\n❌ ERROR: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Script Error: {e}")

if __name__ == "__main__":
    ssh_deploy()