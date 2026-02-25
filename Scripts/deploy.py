import os
import subprocess

# --- CONFIGURATION ---
TOKEN = "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" 
USER = "mohangraphy"
REPO = "mohangraphy.github.io"
# ---------------------

def final_push():
    # Set the path correctly
    script_path = os.path.abspath(__file__)
    root_dir = os.path.dirname(os.path.dirname(script_path))
    os.chdir(root_dir)
    
    print("🧹 Resetting Git configuration...")
    subprocess.run(["git", "remote", "remove", "origin"], capture_output=True)

    # Re-build the gallery
    print("🔨 Building gallery...")
    subprocess.run(["python3", "Scripts/build_mohangraphy.py"])

    # THE FIX: We use 'x-access-token' as the username. 
    # This is the official way to tell Git NOT to ask for a password.
    remote_url = f"https://x-access-token:{TOKEN}@github.com/{USER}/{REPO}.git"
    subprocess.run(["git", "remote", "add", "origin", remote_url])

    try:
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", "Structure Update"], capture_output=True)
        
        print(f"📤 Uploading to {REPO}...")
        # We temporarily disable the Mac Credential Manager to prevent the popup
        result = subprocess.run([
            "git", "-c", "credential.helper=", "push", "-u", "origin", "main", "--force"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"\n✅ SUCCESS! Site is live: https://{REPO}")
        else:
            print(f"\n❌ PUSH FAILED")
            print(f"Details: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Script Error: {e}")

if __name__ == "__main__":
    final_push()