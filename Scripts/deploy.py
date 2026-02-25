import os
import subprocess

# --- CONFIGURATION ---
USER = "mohangraphy"
REPO = "mohangraphy.github.io"
# ---------------------

def ssh_deploy():
    # Set the path to your Mohangraphy folder
    script_path = os.path.abspath(__file__)
    root_dir = os.path.dirname(os.path.dirname(script_path))
    os.chdir(root_dir)
    
    # 1. Build the gallery (Handling Megamalai cross-links)
    print("🔨 Building your categorized gallery...")
    subprocess.run(["python3", "Scripts/build_mohangraphy.py"])

    # 2. Reset the connection to use SSH instead of HTTPS
    # This is what stops the password prompt!
    ssh_url = f"git@github.com:{USER}/{REPO}.git"
    subprocess.run(["git", "remote", "remove", "origin"], capture_output=True)
    subprocess.run(["git", "remote", "add", "origin", ssh_url])

    # 3. Push the files
    print(f"📤 Uploading via SSH key...")
    try:
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", "Switching to SSH"], capture_output=True)
        
        # The first time you do this, it might ask if you trust GitHub. Type 'yes'.
        result = subprocess.run(["git", "push", "-u", "origin", "main", "--force"], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"\n✅ SUCCESS! Site is live: https://{REPO}")
        else:
            print(f"\n❌ ERROR: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Script Error: {e}")

if __name__ == "__main__":
    ssh_deploy()