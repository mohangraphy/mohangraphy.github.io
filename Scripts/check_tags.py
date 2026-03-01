import json

with open('/Users/ncm/Pictures/Mohangraphy/Scripts/photo_metadata.json') as f:
    data = json.load(f)

issues = []
ok = []
for key, info in data.items():
    path    = info.get('path', '')
    cats    = info.get('categories', [])
    state   = info.get('state', '').strip()
    city    = info.get('city',  '').strip()
    is_places = any('Places' in c for c in cats)

    if is_places and not state:
        issues.append(f'  NO STATE   : {path}')
    elif is_places and not city:
        issues.append(f'  NO CITY    : {path}  (state={state!r})')
    elif state and not is_places:
        issues.append(f'  NO PLACES/ : {path}  (state={state!r} city={city!r})')
    elif is_places and state and city:
        ok.append(path)

print(f'Total photos : {len(data)}')
print(f'Correctly tagged for Places: {len(ok)}')
print(f'Issues found : {len(issues)}')
print()
for i in issues:
    print(i)
