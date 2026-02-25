import os
import subprocess

# --- CONFIGURATION ---
TOKEN = "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" 
USER = "mohangraphy"
REPO = "mohangraphy.github.io"
# ---------------------

def master_deploy():
    # Set the path correctly
    script_path = os.path.abspath(__file__)
    root_dir = os.path.dirname(os.path.dirname(script_path))
    os.chdir(root_dir)
    
    # 1. Run the gallery builder
    print("🔨 Building your categorized gallery...")
    subprocess.run(["python3", "Scripts/build_mohangraphy.py"])

    # 2. Prepare the files
    print("📦 Preparing files for upload...")
    subprocess.run(["git", "add", "."], capture_output=True)
    subprocess.run(["git", "commit", "-m", "Final Sync"], capture_output=True)

    # 3. THE "BRUTE FORCE" PUSH
    # We bypass the 'origin' nickname and push directly to the URL with the token
    print(f"📤 Uploading to {REPO}...")
    direct_url = f"https://{TOKEN}@github.com/{USER}/{REPO}.git"
    
    # We use -c credential.helper= to ensure Mac doesn't try to use an old password
    result = subprocess.run([
        "git", "-c", "credential.helper=", "push", direct_url, "main", "--force"
    ], capture_output=True, text=True)

    if result.returncode == 0:
        print(f"\n✅ SUCCESS! Your portfolio is live.")
        print(f"🌍 View it here: https://{REPO}")
    else:
        print(f"\n❌ STILL BLOCKED")
        print(f"Details: {result.stderr}")
        print("\n💡 PEER TIP: If it still fails, your token might have expired.")
        print("Please check GitHub Settings -> Developer Settings -> Personal Access Tokens.")

if __name__ == "__main__":
    master_deploy()