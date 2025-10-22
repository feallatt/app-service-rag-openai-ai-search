#!/usr/bin/env python3
"""
Format data/suggestions.json to minimal schema: id, recommendations, searchText
Creates a backup suggestions.bak.json before overwriting.
"""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
data_file = root / 'data' / 'suggestions.json'
backup_file = root / 'data' / 'suggestions.bak.json'

if not data_file.exists():
    print(f"File not found: {data_file}")
    raise SystemExit(1)

with data_file.open('r', encoding='utf-8') as f:
    items = json.load(f)

# Backup
with backup_file.open('w', encoding='utf-8') as f:
    json.dump(items, f, ensure_ascii=False, indent=2)
print(f"Backup written to: {backup_file}")

new_items = []
for it in items:
    new_it = {
        'id': it.get('id'),
        'recommendations': it.get('recommendations', []),
        'searchText': it.get('searchText') or ''
    }
    new_items.append(new_it)

with data_file.open('w', encoding='utf-8') as f:
    json.dump(new_items, f, ensure_ascii=False, indent=2)

print(f"Rewrote {data_file} with {len(new_items)} entries (minimal schema).")
