import sys
import docx
import re
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

docx_path = Path("artifacts/course-essay/lms-qlpm-trello-drawio/output/LMS_20261102_standardized.docx")
doc = docx.Document(docx_path)
print(f"LMS paragraphs: {len(doc.paragraphs)}")

# Find Bib heading
bib_idx = None
for idx, p in enumerate(doc.paragraphs):
    if 'TÀI LIỆU THAM KHẢO' in p.text.upper() and p.style.name.startswith('Heading'):
        bib_idx = idx
        print(f"Found Bib Heading at p.{idx}: {repr(p.text)}")
        break

if bib_idx:
    print("\nBibliography entries:")
    for i in range(bib_idx + 1, min(bib_idx + 25, len(doc.paragraphs))):
        t = doc.paragraphs[i].text.strip()
        if t.startswith('PHỤ LỤC') or (doc.paragraphs[i].style.name.startswith('Heading') and t):
            break
        if t:
            print(f"  {repr(t)}")

# In-text citations
citations = {}
end_search = bib_idx if bib_idx else len(doc.paragraphs)
for idx in range(0, end_search):
    p = doc.paragraphs[idx]
    matches = re.findall(r'\[(\d+)\]', p.text)
    if matches:
        for m in matches:
            citations.setdefault(m, []).append((idx, p.text[:60]))

print(f"\nIn-text citations found: {sum(len(v) for v in citations.values())}")
print(f"Distinct keys: {sorted(citations.keys(), key=lambda x: int(x))}")
for k in sorted(citations.keys(), key=lambda x: int(x)):
    print(f"  [{k}]: cited {len(citations[k])} times")
