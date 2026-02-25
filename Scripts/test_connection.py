import json
import urllib.request
import ssl

# --- ENTER YOUR TOKEN HERE ---
TOKEN = "ghp_PASTE_YOUR_ACTUAL_TOKEN_HERE" 
# -----------------------------

def check_github():
    print("🔍 Connecting to GitHub (No-Library Version)...")
    
    # Bypass SSL issues if any
    context = ssl._create_unverified_context()
    
    headers = {
        'Authorization': f'token {TOKEN}',
        'User-Agent': 'Python-Urllib'
    }
    
    try:
        # 1. Check User
        user_req = urllib.request.Request('https://api.github.com/user', headers=headers)
        with urllib.request.urlopen(user_req, context=context) as response:
            user_data = json.loads(response.read().decode())
            username = user_data['login']
            print(f"✅ Authenticated as: {username}")

        # 2. Check Repositories
        repo_req = urllib.request.Request(f'https://api.github.com/users/{username}/repos', headers=headers)
        with urllib.request.urlopen(repo_req, context=context) as response:
            repos_data = json.loads(response.read().decode())
            repos = [r['name'] for r in repos_data]
            
            print("-" * 40)
            print(f"📂 Repositories on your account: {repos}")
            print("-" * 40)
            
            if "mohangraphy.github.io" in repos:
                print("🚀 RESULT: 'mohangraphy.github.io' exists and is ready!")
            elif "mohangraphy" in repos:
                print("⚠️ RESULT: The repo is still named 'mohangraphy'.")
            else:
                print("❌ RESULT: No matching repository found.")

    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    check_github()