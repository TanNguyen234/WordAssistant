import sys
from pathlib import Path
from docx import Document

sys.stdout.reconfigure(encoding='utf-8')

in_path = Path('D:/Download/ProfessionalLegalRAG/artifacts/course-essay-vietlex-20261020/output/VietLex_20261102_academic_standardized.docx')
doc = Document(in_path)
paras = doc.paragraphs

print("Searching for candidate paragraphs in Chapter 3 (P461 - P564)...")
for i in range(461, 564):
    t = paras[i].text
    if any(k in t.lower() for k in ["chỉ số", "đánh giá", "faithfulness", "recall", "độ đúng", "trích dẫn", "kết quả", "thử nghiệm", "chẩn đoán", "groundedness"]):
        print(f"P{i:3d}: {t[:110]}...")
