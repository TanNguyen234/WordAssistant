import sys
import zipfile
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding='utf-8')

f = r'artifacts/course-essay/strongwine-revision-20261027/output/StrongWine_20261102_academic_standardized.docx'
with zipfile.ZipFile(f) as z:
    raw_xml = z.read('word/document.xml')

root = ET.fromstring(raw_xml)
NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'

invalid_count = 0
for idx, p in enumerate(root.iter(f'{{{NS}}}p')):
    # In valid XML, p.text should be None or empty whitespace
    has_text = bool(p.text and p.text.strip())
    # pPr if present must be the first child
    bad_ppr_order = False
    children = list(p)
    for c_idx, c in enumerate(children):
        if c.tag == f'{{{NS}}}pPr' and c_idx != 0:
            bad_ppr_order = True
            break
        # Also check child .tail or non-standard children
        if c.tail and c.tail.strip():
            has_text = True
            
    if has_text or bad_ppr_order:
        invalid_count += 1
        print(f"Paragraph #{idx} is INVALID! text={repr(p.text)}, bad_ppr_order={bad_ppr_order}")
        sample = ET.tostring(p, encoding='utf-8').decode('utf-8')[:200]
        print(f"  Sample: {sample}")

print(f"\nTotal invalid paragraphs found: {invalid_count}")
