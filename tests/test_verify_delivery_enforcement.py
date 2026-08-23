from __future__ import annotations
from pathlib import Path
from docx import Document
from wordassistant.document.scaffold import scaffold_document
from wordassistant.document.validate import validate_document
from wordassistant.profiles.loader import resolve_profile

def test_verify_fails_when_required_front_matter_missing(tmp_path: Path):
    doc_path = tmp_path / "report.docx"
    prof = resolve_profile("hcmunre_dacn_2026_2027")
    scaffold_document(doc_path, prof, "report", title="TEST TITLE", student="STUDENT A", supervisor="SUPERVISOR B")
    
    # Add enough references so reference check passes
    d = Document(doc_path)
    for i in range(1, 12):
        d.add_paragraph(f"[{i}] Author {i}, Title {i}, 2024.")
        
    # Delete the heading "LỜI CẢM ƠN"
    for p in d.paragraphs:
        if "cảm ơn" in p.text.lower() or "cam on" in p.text.lower():
            p.text = "THAY THE"
            p.style = d.styles["Normal"]
    d.save(doc_path)
    
    res = validate_document(doc_path, prof, "report", verify_mode=True)
    assert res.valid is False
    codes = [i.code for i in res.issues]
    assert "missing_front_matter" in codes

def test_verify_fails_when_header_topic_missing(tmp_path: Path):
    doc_path = tmp_path / "report.docx"
    prof = resolve_profile("hcmunre_dacn_2026_2027")
    scaffold_document(doc_path, prof, "report", title="TEST TITLE", student="STUDENT A", supervisor="SUPERVISOR B")
    
    d = Document(doc_path)
    for i in range(1, 12):
        d.add_paragraph(f"[{i}] Author {i}, Title {i}, 2024.")
    # Clear header text in all sections
    for s in d.sections:
        for p in s.header.paragraphs:
            p.text = ""
    d.save(doc_path)
    
    res = validate_document(doc_path, prof, "report", verify_mode=True)
    assert res.valid is False
    codes = [i.code for i in res.issues]
    assert any("header" in c for c in codes)
