import sys
from pathlib import Path
from docx import Document

sys.stdout.reconfigure(encoding='utf-8')

in_path = Path('D:/Download/ProfessionalLegalRAG/artifacts/course-essay-vietlex-20261020/output/VietLex_20261102_academic_standardized.docx')
doc = Document(in_path)
paras = doc.paragraphs

# Let's inspect paragraphs between 267 and 460 in Chapter 2
print("Searching for candidate paragraphs in Chapter 2 (P267 - P460)...")
for i in range(267, 461):
    t = paras[i].text
    if any(k in t.lower() for k in ["vector", "qdrant", "embedding", "nhúng", "truy xuất", "chunk", "tách đoạn", "mismatch"]):
        print(f"P{i:3d}: {t[:110]}...")
