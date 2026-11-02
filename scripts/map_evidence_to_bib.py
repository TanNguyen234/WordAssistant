import sys
import json
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

base = Path('D:/Download/ProfessionalLegalRAG/artifacts/course-essay-vietlex-20261020')
ev_path = base / 'evidence.json'
ev_data = json.loads(ev_path.read_text(encoding='utf-8'))
records = ev_data if isinstance(ev_data, list) else list(ev_data.values())

print(f"Total records in evidence.json: {len(records)}")
for r in records:
    st = str(r.get('review_status') or 'None')
    print(f"ID: {r.get('id'):40s} | Status: {st:10s} | DOI/URL: {r.get('doi') or r.get('url')}")
