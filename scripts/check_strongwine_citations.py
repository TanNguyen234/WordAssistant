import sys
import docx
import re

sys.stdout.reconfigure(encoding='utf-8')
doc = docx.Document('artifacts/course-essay/strongwine-revision-20261027/output/StrongWine_20261102_academic_standardized.docx')

citations = {}
for idx in range(0, 1272):
    p = doc.paragraphs[idx]
    matches = re.findall(r'\[(\d+)\]', p.text)
    if matches:
        for m in matches:
            citations.setdefault(m, []).append((idx, p.text[:80]))

print(f"Total in-text citations found: {sum(len(v) for v in citations.values())}")
print(f"Distinct bibliography keys cited: {len(citations)}")
for k in sorted(citations.keys(), key=lambda x: int(x)):
    print(f"  [{k:2s}]: cited {len(citations[k]):2d} times (across paras: {', '.join(str(p[0]) for p in citations[k])})")
