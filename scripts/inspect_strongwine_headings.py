import sys
import docx

sys.stdout.reconfigure(encoding='utf-8')
doc = docx.Document('artifacts/course-essay/strongwine-revision-20261027/output/StrongWine_20261102_standardized.docx')

for idx, p in enumerate(doc.paragraphs):
    t = p.text.strip()
    if p.style and 'Heading' in p.style.name:
        print(f"p.{idx} [{p.style.name}]: {t}")
    elif any(t.startswith(prefix) for prefix in ['CHƯƠNG', 'MỞ ĐẦU', 'KẾT LUẬN', 'TÀI LIỆU', 'PHỤ LỤC']):
        print(f"p.{idx} [Prefix]: {t}")
