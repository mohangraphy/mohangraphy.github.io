import os
import subprocess
import time
import sys

def master_deploy():
    root_dir = "/Users/ncm/Pictures/Mohangraphy"
    os.chdir(root_dir)

    print("\n─── MOHANGRAPHY DEPLOY ───────────────────────────────")

    # Step 1 — Run curator (tag new photos / edit existing)
    print("Step 1: Opening curator for new photos...")
    try:
        subprocess.run([sys.executable, "Scripts/curator.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"  Curator closed early or failed: {e}")

    # Step 1.5 — Apply any Megamalai/Mountains tag fixes if fixer exists
    fixer = "Scripts/fix_megamalai.py"
    if os.path.exists(fixer):
        print("Step 1.5: Applying tag fixes...")
        try:
            subprocess.run([sys.executable, fixer], check=True)
        except Exception as e:
            print(f"  Tag fixer skipped: {e}")

    # Step 2 — Rebuild index.html from metadata + content.json
    # KEY FIX: was calling 'build_mohangraphy.py' (old name).
    # Now correctly calls 'Claude_mohangraphy.py'.
    print("Step 2: Building gallery website...")
    try:
        subprocess.run(
            [sys.executable, "Scripts/Claude_mohangraphy.py"],
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"  Build failed: {e}")
        print("  Deploy aborted — fix the error above and try again.")
        return

    # Step 3 — Push everything to GitHub
    print("Step 3: Pushing to GitHub...")
    subprocess.run(["git", "add",
                    "index.html",
                    "Scripts/photo_metadata.json",
                    "Scripts/content.json",
                    "Thumbs/"],
                   check=True)

    timestamp  = time.strftime('%Y-%m-%d %H:%M:%S')
    commit_msg = f"Gallery update: {timestamp}"

    result = subprocess.run(
        ["git", "commit", "-m", commit_msg],
        capture_output=True, text=True
    )
    if "nothing to commit" in (result.stdout + result.stderr):
        print("  Nothing changed since last deploy — skipping push.")
    else:
        subprocess.run(["git", "push", "origin", "main", "--force"],
                       capture_output=True)
        print(f"  Live in ~60 seconds. Hard-refresh with Cmd+Shift+R.")

    print(f"─── DONE at {timestamp} ─────────────────────────────\n")

if __name__ == "__main__":
    master_deploy()
