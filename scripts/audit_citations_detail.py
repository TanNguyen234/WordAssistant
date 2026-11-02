import sys
import re
from pathlib import Path
from docx import Document

sys.stdout.reconfigure(encoding='utf-8')

files = {
    'StrongWine': Path('artifacts/course-essay/strongwine-revision-20261027/output/StrongWine_20261102_standardized.docx'),
    'LMS': Path('artifacts/course-essay/lms-qlpm-trello-drawio/output/LMS_20261102_standardized.docx'),
    'VietLex': Path('D:/Download/ProfessionalLegalRAG/artifacts/course-essay-vietlex-20261020/output/VietLex_20261102_standardized_logo.docx'),
}

citation_re = re.compile(r'\[(\d+(?:[–,\s-]+\d+)*)\]')

for name, path in files.items():
    print(f'==================================================')
    print(f'=== {name}: {path.name} ===')
    print(f'==================================================')
    if not path.is_file():
        print(f'FILE NOT FOUND: {path}')
        continue
    doc = Document(path)
    paras = doc.paragraphs
    print(f'Total paragraphs: {len(paras)}')
    
    # List all Headings to see structure
    headings = []
    for i, p in enumerate(paras):
        if p.style.name.startswith('Heading 1'):
            headings.append((i, p.text.strip()))
            
    print(f'Major Headings (Heading 1):')
    for p_idx, h_text in headings:
        print(f'  P{p_idx:4d}: {h_text}')
        
    # Find bibliography range
    bib_start = -1
    bib_end = len(paras)
    for idx, (p_idx, h_text) in enumerate(headings):
        if 'TÀI LIỆU THAM KHẢO' in h_text.upper():
            bib_start = p_idx
            if idx + 1 < len(headings):
                bib_end = headings[idx + 1][0]
            else:
                bib_end = len(paras)
            break
            
    print(f'\nBibliography paragraph range: P{bib_start} to P{bib_end}')
    bib_items = []
    if bib_start != -1:
        for i in range(bib_start + 1, bib_end):
            t = paras[i].text.strip()
            if t:
                bib_items.append((i, t))
    print(f'Bibliography entries found: {len(bib_items)}')
    for idx, (p_idx, b_text) in enumerate(bib_items[:15]):
        print(f'  Bib [{idx+1}] (P{p_idx}): {b_text}')
        
    # Find in-text citations before bibliography
    in_text = []
    current_h1 = 'Front Matter'
    for i in range(bib_start if bib_start != -1 else len(paras)):
        p = paras[i]
        t = p.text.strip()
        if p.style.name.startswith('Heading 1'):
            current_h1 = t
        matches = citation_re.findall(t)
        if matches:
            for m in matches:
                in_text.append((i, current_h1, m, t))
                
    print(f'\nTotal in-text citation markers found: {len(in_text)}')
    unique_cites = set()
    for p_idx, h1, cite, full_text in in_text:
        nums = re.findall(r'\d+', cite)
        unique_cites.update(nums)
        print(f'  -> P{p_idx:4d} [{cite}] under "{h1}":\n     "{full_text[:140]}..."')
        
    print(f'\nUnique citation numbers cited in-text: {sorted(list(unique_cites), key=int) if unique_cites else "NONE"}')
    print(f'Total unique citation numbers cited in-text: {len(unique_cites)}')
    print()
