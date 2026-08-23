from __future__ import annotations
from pathlib import Path
from docx import Document
from wordassistant.document.validate import validate_document
from wordassistant.profiles.loader import resolve_profile
from wordassistant.document.scaffold import scaffold_document

def test_body_numbered_items_outside_bibliography_do_not_count(tmp_path: Path):
    doc_path = tmp_path / "body_numbered.docx"
    prof = resolve_profile("hcmunre_dacn_2026_2027")
    scaffold_document(
        doc_path,
        prof,
        "report",
        title="XAY DUNG HE THONG RAG CHO VAN BAN PHAP LUAT",
        student="NGUYEN VAN A - 2351010001",
        supervisor="TS. NGUYEN VAN B"
    )
    d = Document(doc_path)
    # Add 12 numbered items inside Chapter 1 (body content) but leave bibliography empty
    for idx, p in enumerate(d.paragraphs):
        if "CHƯƠNG 1" in p.text.upper():
            p_next = d.paragraphs[idx + 1]
            for i in range(1, 13):
                p_next.insert_paragraph_before(f"[{i}] Đây là một yêu cầu chức năng thứ {i} trong phần nội dung chương 1.")
            break
            
    d.save(doc_path)
    
    # Draft validate should still report missing_references or insufficient_references
    res = validate_document(doc_path, prof, "report", verify_mode=False)
    issues = [i for i in res.issues if i.code in ("missing_references", "insufficient_references")]
    assert len(issues) >= 1
    assert any("0 reference" in i.message or "insufficient" in i.message.lower() for i in issues)

def test_references_in_bibliography_section_count_properly(tmp_path: Path):
    doc_path = tmp_path / "bib_numbered.docx"
    prof = resolve_profile("hcmunre_dacn_2026_2027")
    scaffold_document(
        doc_path,
        prof,
        "report",
        title="XAY DUNG HE THONG RAG CHO VAN BAN PHAP LUAT",
        student="NGUYEN VAN A - 2351010001",
        supervisor="TS. NGUYEN VAN B"
    )
    d = Document(doc_path)
    # Add 10 references under bibliography heading
    in_bib = False
    for p in d.paragraphs:
        if ("tài liệu tham khảo" in p.text.lower() or "tai lieu tham khao" in p.text.lower()) and p.style.name.startswith("Heading"):
            in_bib = True
            for i in range(1, 11):
                d.add_paragraph(f"[{i}] Tác giả {i}, Tên tài liệu {i}, 2024.")
            break
            
    d.save(doc_path)
    
    res = validate_document(doc_path, prof, "report", verify_mode=False)
    issues = [i for i in res.issues if i.code in ("missing_references", "insufficient_references")]
    assert len(issues) == 0
