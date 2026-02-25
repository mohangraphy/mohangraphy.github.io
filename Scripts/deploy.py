import os
import subprocess

# --- CONFIGURATION ---
# Use your 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 token here
TOKEN = "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" 
USER = "mohangraphy"
REPO = "mohangraphy.github.io"
# ---------------------

def final_push():
    root = os.path.dirname(os.path.abspath(__file__))
    # Ensure we are in the main Mohangraphy folder
    os.chdir(os.path.dirname(root))
    
    print("🧹 Cleaning old connection settings...")
    # This removes the old 'origin' that is asking for a password
    subprocess.run(["git", "remote", "remove", "origin"], capture_output=True)

    # Re-build the index.html
    print("🔨 Building your gallery...")
    subprocess.run(["python3", "Scripts/build_mohangraphy.py"])

    # Set the NEW remote URL using the token
    # We use the token twice to satisfy Git's 'username:password' requirement
    remote_url = f"https://{TOKEN}@github.com/{USER}/{REPO}.git"
    subprocess.run(["git", "remote", "add", "origin", remote_url])

    try:
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", "Categorized Update"], capture_output=True)
        
        print(f"📤 Pushing to {REPO} (No password should be required)...")
        # We tell Git to ignore the Mac keychain for this one push
        result = subprocess.run([
            "git", "-c", "credential.helper=", "push", "-u", "origin", "main", "--force"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"\n✅ SUCCESS! Site is live at https://{REPO}")
        else:
            print(f"\n❌ ERROR: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Script Error: {e}")

if __name__ == "__main__":
    final_push()