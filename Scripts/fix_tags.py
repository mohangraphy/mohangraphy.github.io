"""
fix_tags.py — fixes all metadata issues found by check_tags.py
Run once, then run deploy.py to publish.
"""
import json, os

DATA_FILE = '/Users/ncm/Pictures/Mohangraphy/Scripts/photo_metadata.json'

with open(DATA_FILE) as f:
    data = json.load(f)

fixed = 0

for key, info in data.items():
    path  = info.get('path', '')
    cats  = info.get('categories', [])
    state = info.get('state', '').strip()
    city  = info.get('city',  '').strip()

    changed = False

    # ── GROUP 1: Megamalai photos — have Places/National but no state/city ──
    if 'Megamalai' in path and any('Places' in c for c in cats):
        if not state:
            info['state'] = 'Tamil Nadu'
            changed = True
        if not city:
            info['city'] = 'Megamalai'
            changed = True

    # ── GROUP 2: Badami/Pattadhakal — have state/city but missing Places/National ──
    if 'Badami' in path and state in ('Karnataka',) and city:
        if 'Places/National' not in cats:
            info['categories'] = list(set(cats + ['Places/National']))
            changed = True
        # Fix the one photo missing city
        if not city:
            info['city'] = 'Badami'
            changed = True

    # ── GROUP 3: Munnar Birds — have state/city but missing Places/National ──
    if 'MunnarBirds' in path and state == 'Kerala' and city == 'Munnar':
        if 'Places/National' not in cats:
            info['categories'] = list(set(cats + ['Places/National']))
            changed = True

    if changed:
        fixed += 1
        print(f'  Fixed: {path.split("/")[-1]}  →  state={info.get("state")!r} city={info.get("city")!r} cats={info.get("categories")}')

# Save
with open(DATA_FILE, 'w') as f:
    json.dump(data, f, indent=2)

print(f'\n✅ Fixed {fixed} photos. Now run: python3 Scripts/deploy.py')
