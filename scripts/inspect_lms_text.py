import sys
import docx
import re
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

docx_path = Path("artifacts/course-essay/lms-qlpm-trello-drawio/output/LMS_20261102_standardized.docx")
doc = docx.Document(docx_path)

print("=== CHECKING LMS SOURCE MENTIONS ===")
matches = []
for i, p in enumerate(doc.paragraphs[:472]):
    t = p.text
    for kw in ['EV-', 'Trello', 'PMI', 'Drawio', 'Draw.io', 'Atlassian', 'Practice Standard', 'Charter', 'RACI', 'Sổ rủi ro', 'lược đồ', 'schema', 'kho mã nguồn', '01_PROJECT_CHARTER']:
        if kw.lower() in t.lower():
            matches.append((i, kw, t[:90]))
            break

print(f"Total paragraphs mentioning sources: {len(matches)}")
for i, kw, prev in matches[:15]:
    print(f"  p.{i} [{kw}]: {prev}...")
