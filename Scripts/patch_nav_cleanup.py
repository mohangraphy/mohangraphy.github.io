#!/usr/bin/env python3
"""
patch_nav_cleanup.py
-----------------------
Part C: navigation cleanup, based on user feedback. Applies to both
desktop and mobile — this is a real behavior/JS change, not a style fix.

1. updateBreadcrumb() currently renders EVERY ancestor level as its own
   clickable pill (e.g. "HOME / LANDSCAPE / BADRINATH"), plus the
   current page repeated again as plain text — redundant with the big
   page title shown separately. Replaced with a single "\u2190 Back"
   button that goes up exactly one level (to the immediate parent),
   matching conventional one-level-at-a-time back navigation. Since
   the existing Copy Link button already sits right next to the
   breadcrumb bar in the HTML, this alone produces the target layout:
   Back arrow (left) + Copy Link (right), nothing else.

2. Removes the 5 "\u2190 Back to Home" buttons on info pages (About Me,
   Contact, etc.) — redundant since the Mohangraphy logo already goes
   home, and inconsistent with how gallery pages will now work.

No CSS changes needed — reuses the existing .bc-back button style.

Run once, locally:
    python3 patch_nav_cleanup.py
"""

import os
import shutil
import datetime

SCRIPT_PATH = "/Users/ncm/Pictures/Mohangraphy/Scripts/Claude_mohangraphy.py"

OLD_BREADCRUMB_FN = """function updateBreadcrumb(crumbs){
  /* crumbs: [{label:'Home', fn:'goHome()'}, {label:'Places'}, ...] */
  ['bc-bar','gal-bc-bar'].forEach(function(barId){
    var bar = document.getElementById(barId);
    if(!bar) return;
    bar.innerHTML = '';
    crumbs.forEach(function(c, i){
      if(i > 0){
        var sep = document.createElement('span');
        sep.className = 'bc-sep'; sep.textContent = '/';
        bar.appendChild(sep);
      }
      if(c.fn && i < crumbs.length-1){
        var btn = document.createElement('button');
        btn.className = 'bc-back'; btn.textContent = c.label;
        btn.setAttribute('onclick', c.fn);
        bar.appendChild(btn);
      } else {
        var sp = document.createElement('span');
        sp.className = 'bc-current'; sp.textContent = c.label;
        bar.appendChild(sp);
      }
    });
  });
}"""

NEW_BREADCRUMB_FN = """function updateBreadcrumb(crumbs){
  /* crumbs: [{label:'Home', fn:'goHome()'}, {label:'Places'}, ...] —
     only the second-to-last crumb's fn is used, so this always jumps
     back exactly one level, e.g. Badrinath -> Landscape -> Collections -> Home. */
  ['bc-bar','gal-bc-bar'].forEach(function(barId){
    var bar = document.getElementById(barId);
    if(!bar) return;
    bar.innerHTML = '';
    if(crumbs.length < 2) return;
    var parent = crumbs[crumbs.length - 2];
    var btn = document.createElement('button');
    btn.className = 'bc-back';
    btn.innerHTML = '&larr; Back';
    btn.setAttribute('onclick', parent.fn || 'goHome()');
    bar.appendChild(btn);
  });
}"""

BACK_TO_HOME_BTN = '\'    <button class="info-page-back" onclick="goHome()">&larr; Back to Home</button>\\n\'\n'


def main():
    if not os.path.exists(SCRIPT_PATH):
        print(f"ERROR: could not find {SCRIPT_PATH}")
        return

    with open(SCRIPT_PATH, "r", encoding="utf-8") as f:
        source = f.read()

    if "only the second-to-last crumb's fn is used" in source:
        print("This file already looks patched. Stopping — nothing changed.")
        return

    if OLD_BREADCRUMB_FN not in source:
        print("ERROR: could not find the expected updateBreadcrumb() function.")
        print("Stopping without changing anything — the file may differ from what this script expects.")
        return

    back_home_count = source.count(BACK_TO_HOME_BTN)
    if back_home_count == 0:
        print("ERROR: could not find the expected 'Back to Home' button lines.")
        print("Stopping without changing anything.")
        return

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = SCRIPT_PATH + f".bak_{ts}"
    shutil.copyfile(SCRIPT_PATH, backup_path)
    print(f"Backup written: {backup_path}")

    new_source = source.replace(OLD_BREADCRUMB_FN, NEW_BREADCRUMB_FN, 1)
    new_source = new_source.replace(BACK_TO_HOME_BTN, "", back_home_count)

    with open(SCRIPT_PATH, "w", encoding="utf-8") as f:
        f.write(new_source)

    print(f"\nDone. {SCRIPT_PATH} updated.")
    print("Replaced the multi-level breadcrumb trail with a single one-level-up")
    print("Back button (both desktop and mobile).")
    print(f"Removed {back_home_count} 'Back to Home' button(s) from info pages.")
    print(f"\nIf anything looks wrong, restore with:\n  cp {backup_path} {SCRIPT_PATH}")
    print("\nNext: run 'python3 Claude_mohangraphy.py' to deploy, then check:")
    print("  - Collections > Landscape > Badrinath: should show just 'BADRINATH'")
    print("    title with a Back arrow + Copy Link, tapping Back goes to Landscape")
    print("  - About Me / Contact pages: no more 'Back to Home' button")


if __name__ == "__main__":
    main()
