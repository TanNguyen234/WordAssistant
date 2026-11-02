import sys
from pathlib import Path
from docx import Document

sys.stdout.reconfigure(encoding='utf-8')

doc = Document('D:/Download/ProfessionalLegalRAG/artifacts/course-essay-vietlex-20261020/output/VietLex_20261102_standardized_logo.docx')
paras = doc.paragraphs

# Find Chapter 1 start and end
ch1_start = -1
ch2_start = -1
for i, p in enumerate(paras):
    t = p.text.strip()
    if 'CHƯƠNG 1: TỔNG QUAN TÀI LIỆU' in t:
        ch1_start = i
    elif 'CHƯƠNG 2: PHƯƠNG PHÁP THỰC HIỆN' in t:
        ch2_start = i

print(f"Chapter 1 range: P{ch1_start} to P{ch2_start} (total {ch2_start - ch1_start} paragraphs)")
for i in range(ch1_start, ch2_start):
    p = paras[i]
    print(f"P{i:3d} [{p.style.name:15s}]: {p.text}")
