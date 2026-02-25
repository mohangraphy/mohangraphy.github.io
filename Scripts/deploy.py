import os
import subprocess

def deploy_site():
    # 1. Run the build script first
    print("Building the latest version of Mohangraphy...")
    subprocess.run(["python3", "build_mohangraphy.py"])

    # 2. Navigate to parent directory for Git commands
    os.chdir("..")

    # 3. Run Git commands
    print("Pushing updates to the web...")
    try:
        subprocess.run(["git", "add", "."])
        subprocess.run(["git", "commit", "-m", "Automatic update of portfolio"])
        subprocess.run(["git", "push", "origin", "main"])
        print("\n✨ Success! Your website is being updated at YOUR_USERNAME.github.io/mohangraphy/")
    except Exception as e:
        print(f"Error during deployment: {e}")

if __name__ == "__main__":
    deploy_site()