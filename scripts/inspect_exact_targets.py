import sys
import docx

sys.stdout.reconfigure(encoding='utf-8')
doc = docx.Document('artifacts/course-essay/strongwine-revision-20261027/output/StrongWine_20261102_standardized.docx')

check_idxs = [428, 514, 554, 886, 1018, 1128, 1192, 1207]
for idx in check_idxs:
    print(f"p.{idx}: {repr(doc.paragraphs[idx].text)}")
