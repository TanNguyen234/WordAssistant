import sys
import json
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

p = Path("artifacts/course-essay/lms-qlpm-trello-drawio/evidence.json")
d = json.loads(p.read_text(encoding='utf-8'))
print(f"Total keys in LMS evidence.json: {len(d)}")
for k, v in list(d.items())[:20]:
    t = v.get("title", v.get("source_file", ""))
    st = v.get("review_status", "")
    print(f"  {k:15s}: {t[:50]:50s} [{st}]")
