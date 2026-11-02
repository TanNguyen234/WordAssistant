import sys
from pathlib import Path
from docx import Document

sys.stdout.reconfigure(encoding='utf-8')

doc = Document('D:/Download/ProfessionalLegalRAG/artifacts/course-essay-vietlex-20261020/output/VietLex_20261102_standardized_logo.docx')
paras = doc.paragraphs

print("=== CHAPTER 2 HEADINGS AND KEY PARAGRAPHS ===")
for i in range(267, 330):
    p = paras[i]
    if p.style.name.startswith("Heading"):
        print(f"P{i:3d} [{p.style.name:15s}]: {p.text}")
    elif i in [270, 275, 280, 290, 300, 310, 320]:
        print(f"P{i:3d} [Sample Text   ]: {p.text[:120]}...")

print("\n=== CHAPTER 3 HEADINGS AND KEY PARAGRAPHS ===")
for i in range(461, 520):
    p = paras[i]
    if p.style.name.startswith("Heading"):
        print(f"P{i:3d} [{p.style.name:15s}]: {p.text}")
    elif i in [465, 475, 485, 495, 505]:
        print(f"P{i:3d} [Sample Text   ]: {p.text[:120]}...")
