"""
check_content.py — run this any time to verify content.json is valid
and being read correctly before deploying.

Usage:
  cd /Users/ncm/Pictures/Mohangraphy
  python3 Scripts/check_content.py
"""
import os
import json

ROOT_DIR     = "/Users/ncm/Pictures/Mohangraphy"
CONTENT_FILE = os.path.join(ROOT_DIR, "Scripts/content.json")

print("\n─── content.json diagnostic ──────────────────────────")
print(f"Looking for: {CONTENT_FILE}")

# 1. Does the file exist?
if not os.path.exists(CONTENT_FILE):
    print("\n❌ FILE NOT FOUND")
    print("   Make sure content.json is in your Scripts/ folder.")
    print("   Download it again from Claude and copy it there.")
    exit(1)

print("✅ File found")

# 2. Is it valid JSON?
with open(CONTENT_FILE, 'r', encoding='utf-8') as f:
    raw = f.read()

try:
    data = json.loads(raw)
    print("✅ JSON is valid — no syntax errors")
except json.JSONDecodeError as e:
    print(f"\n❌ JSON SYNTAX ERROR on line {e.lineno}: {e.msg}")
    print(f"   Near: ...{raw[max(0,e.pos-40):e.pos+40]}...")
    print("\n   Fix the error then run this script again.")
    print("   You can also paste content.json into https://jsonlint.com to find errors.")
    exit(1)

# 3. Print all key values so you can verify your edits are present
print("\n─── Content currently in content.json ────────────────")

site = data.get('site', {})
print(f"\n[site]")
print(f"  title          : {site.get('title', '(missing)')}")
print(f"  contact_email  : {site.get('contact_email', '(missing)')}")
print(f"  photographer   : {site.get('photographer_name', '(missing)')}")

about = data.get('about', {})
print(f"\n[about]")
print(f"  title          : {about.get('title', '(missing)')}")
print(f"  subtitle       : {about.get('subtitle', '(missing)')}")
paras = about.get('paragraphs', [])
print(f"  paragraphs     : {len(paras)} paragraph(s)")
for i, p in enumerate(paras, 1):
    preview = p[:80] + '...' if len(p) > 80 else p
    print(f"    [{i}] {preview}")

phil = data.get('philosophy', {})
print(f"\n[philosophy]")
print(f"  paragraphs     : {len(phil.get('paragraphs', []))} paragraph(s)")

gear = data.get('gear', {})
print(f"\n[gear]")
for item in gear.get('items', []):
    print(f"  {item.get('heading','?')}: {item.get('detail','?')[:60]}")

contact = data.get('contact', {})
print(f"\n[contact]")
print(f"  subjects       : {contact.get('subjects', [])}")

prints = data.get('prints', {})
print(f"\n[prints]")
for s in prints.get('sizes', []):
    print(f"  {s.get('size','?')} — {s.get('price','?')}")

print("\n─── All checks passed ─────────────────────────────────")
print("✅ content.json is valid and readable.")
print("   Run Claude_Deploy.py to publish your changes.\n")
