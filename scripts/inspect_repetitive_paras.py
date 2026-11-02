import sys
import docx

sys.stdout.reconfigure(encoding='utf-8')
doc = docx.Document('artifacts/course-essay/strongwine-revision-20261027/output/StrongWine_20261102_standardized.docx')

check_indices = [
    559, 654, 869, 896, # 'báo cáo không'
    450, 1208, 1220, 1271, # 'các sơ đồ'
    1019, 1100, 1124, 1152, 1260, # 'các thao tác'
    719, 764, 1241 # 'cần kiểm thử'
]

for idx in check_indices:
    p = doc.paragraphs[idx]
    print(f"=== p.{idx} ===")
    print(p.text)
