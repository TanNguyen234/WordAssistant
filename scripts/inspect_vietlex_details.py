import sys
import json
from pathlib import Path
from docx import Document

sys.stdout.reconfigure(encoding='utf-8')

base = Path('D:/Download/ProfessionalLegalRAG/artifacts/course-essay-vietlex-20261020')
docx_path = base / 'output/VietLex_20261102_standardized_logo.docx'
ev_path = base / 'evidence.json'

print("=== VIETLEX EVIDENCE REGISTRY ===")
if ev_path.is_file():
    ev_data = json.loads(ev_path.read_text(encoding='utf-8'))
    records = ev_data if isinstance(ev_data, list) else list(ev_data.values())
    print(f"Total evidence records: {len(records)}")
    for r in records:
        r_id = r.get("id")
        title = r.get("title", "")
        status = r.get("review_status", "")
        tags = r.get("tags", [])
        print(f"  ID: {r_id} | Status: {status} | Title: {title[:50]}... | Tags: {tags}")
else:
    print("evidence.json NOT found!")

print("\n=== VIETLEX DOCX PARAGRAPHS & CITATIONS ===")
doc = Document(docx_path)
print(f"Total paragraphs: {len(doc.paragraphs)}")

# Inspect where citations are currently located and where they SHOULD be located
# Group paragraphs by Chapter
chapters = []
current_chap = "Front Matter"
for i, p in enumerate(doc.paragraphs):
    t = p.text.strip()
    if p.style.name.startswith("Heading 1"):
        current_chap = t
        chapters.append((i, t, []))
    elif chapters:
        chapters[-1][2].append((i, p))

for p_start, chap_name, p_list in chapters:
    print(f"\n--- {chap_name} (start P{p_start}, total {len(p_list)} paragraphs) ---")
    # count citations in this chapter
    cites = []
    import re
    for idx, p in p_list:
        m = re.findall(r'\[(\d+(?:[–,\s-]+\d+)*)\]', p.text)
        if m:
            cites.append((idx, m, p.text[:80]))
    print(f"  Citations in chapter: {len(cites)} instances")
    for idx, m, excerpt in cites:
        print(f"    P{idx:3d} [{', '.join(m)}]: {excerpt}...")


print("\n=== SPECIFIC CITATION RECORDS ===")
from wordassistant.document.integrity import _collect_paragraphs
records = _collect_paragraphs(doc)
for idx in [268, 269, 273, 274, 279, 283, 287, 292, 599, 645]:
    if idx < len(records):
        r = records[idx]
        print(f"Rec {idx} (story={r.get('story')}, style={r.get('style')}):")
        print(f"  {r.get('text')[:140]}...")
