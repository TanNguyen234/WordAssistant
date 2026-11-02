import sys
import docx
import re

sys.stdout.reconfigure(encoding='utf-8')
doc = docx.Document('artifacts/course-essay/strongwine-revision-20261027/output/StrongWine_20261102_standardized.docx')

citations = {}
for idx in range(0, 1272):
    p = doc.paragraphs[idx]
    matches = re.findall(r'\[(\d+)\]', p.text)
    if matches:
        for m in matches:
            citations.setdefault(m, []).append((idx, p.text[:100]))

print(f"Total citations found: {sum(len(v) for v in citations.values())}")
for k in sorted(citations.keys(), key=lambda x: int(x)):
    print(f"[{k}]: cited {len(citations[k])} times")
    for p_idx, preview in citations[k]:
        print(f"    p.{p_idx}: {preview}")
