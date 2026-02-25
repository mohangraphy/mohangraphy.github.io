import os
import subprocess

# --- PASTE YOUR NEW TOKEN HERE ---
TOKEN = "ghp_PASTE_YOUR_NEW_TOKEN_HERE" 
USER = "mohangraphy"
OLD_NAME = "mohangraphy"
NEW_NAME = "mohangraphy.github.io"
# ---------------------------------

def fix_everything():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(root_dir)
    
    print("🛠️ Starting Portfolio Rescue...")

    # 1. Update the Remote URL with the New Token
    # Even if the name hasn't changed on the web yet, we point to the desired name
    remote_url = f"https://{USER}:{TOKEN}@github.com/{USER}/{NEW_NAME}.git"
    
    subprocess.run(["git", "remote", "remove", "origin"], capture_output=True)
    subprocess.run(["git", "remote", "add", "origin", remote_url])
    
    print(f"🔗 Linked Mac to: {NEW_NAME}")

    # 2. Build the website file
    build_script = os.path.join(root_dir, "Scripts", "build_mohangraphy.py")
    if os.path.exists(build_script):
        subprocess.run(["python3", build_script])

    # 3. Attempt to push
    print("📤 Attempting to push to the new Primary URL...")
    try:
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", "Initial primary domain setup"], capture_output=True)
        result = subprocess.run(["git", "push", "-u", "origin", "main", "--force"], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"\n✅ SUCCESS! Site should be live at: https://{NEW_NAME}")
        else:
            print(f"\n❌ Error: {result.stderr}")
            print("\n💡 TIP: If it says 'Not Found', please ensure you clicked 'Rename' on the GitHub website first!")
            
    except Exception as e:
        print(f"❌ Python Error: {e}")

if __name__ == "__main__":
    fix_everything()