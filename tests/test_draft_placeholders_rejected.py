from __future__ import annotations
import json
from pathlib import Path
from docx import Document
from wordassistant.cli import run
from wordassistant.document.validate import validate_document
from wordassistant.profiles.loader import resolve_profile
from wordassistant.document.scaffold import scaffold_document

def test_scaffold_with_placeholders_fails_final_verify(tmp_path: Path):
    doc_path = tmp_path / "scaffold_report.docx"
    prof = resolve_profile("hcmunre_dacn_2026_2027")
    
    # Scaffold report with metadata
    scaffold_document(
        doc_path,
        prof,
        "report",
        title="HE THONG THONG TIN QUAN LY",
        student="NGUYEN VAN A - 2351010001",
        supervisor="TS. NGUYEN VAN B"
    )
    
    # Add 11 references to bibliography section
    d = Document(doc_path)
    # Find bibliography heading
    for p in d.paragraphs:
        if "tài liệu tham khảo" in p.text.lower() or "tai lieu tham khao" in p.text.lower():
            for i in range(1, 12):
                d.add_paragraph(f"[{i}] Tac gia {i}, Ten sach {i}, NXB {i}, 2024.")
            break
    d.save(doc_path)
    
    # Draft validate should pass or warn
    val_draft = validate_document(doc_path, prof, "report", verify_mode=False)
    assert val_draft.valid is True
    
    # Final verify MUST FAIL because scaffold placeholders remain:
    # [Front matter content], [Section content...], [List of figures], etc.
    val_final = validate_document(doc_path, prof, "report", verify_mode=True)
    assert val_final.valid is False
    codes = [i.code for i in val_final.issues if i.severity == "error"]
    assert "draft_placeholder_detected" in codes

def test_completed_synthetic_report_passes_final_verify(tmp_path: Path):
    doc_path = tmp_path / "completed_report.docx"
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
    
    # Replace all placeholders with realistic synthetic content
    for p in d.paragraphs:
        if "[Front matter content]" in p.text:
            p.text = "Tôi xin chân thành cảm ơn các thầy cô khoa Công nghệ Thông tin đã tận tình giảng dạy và hướng dẫn."
        elif "[Section content...]" in p.text:
            p.text = "Nội dung chi tiết của chương được trình bày đầy đủ nhằm giải quyết bài toán đặt ra trong đề tài."
        elif "[List of figures]" in p.text:
            p.text = "Hình 1.1: Sơ đồ kiến trúc hệ thống tổng thể\nHình 1.2: Quy trình xử lý dữ liệu"
        elif "[List of tables]" in p.text:
            p.text = "Bảng 1.1: Danh sách các thành phần chức năng\nBảng 1.2: Kết quả đánh giá hiệu năng"
        elif "[Document content]" in p.text:
            p.text = "Toàn bộ tài liệu được hoàn thiện và kiểm tra kỹ lưỡng trước khi nộp."
            
    # Add references under bibliography
    in_bib = False
    for p in d.paragraphs:
        if ("tài liệu tham khảo" in p.text.lower() or "tai lieu tham khao" in p.text.lower()) and p.style.name.startswith("Heading"):
            in_bib = True
            continue
        if in_bib:
            break
            
    for i in range(1, 12):
        d.add_paragraph(f"[{i}] Tác giả {i}, Tên tài liệu nghiên cứu {i}, Tạp chí Khoa học {i}, 2024.")
        
    d.save(doc_path)
    
    # CLI verify
    code = run(["verify", str(doc_path), "--profile", "hcmunre_dacn_2026_2027", "--variant", "report", "--json"])
    assert code == 0
    
    val_final = validate_document(doc_path, prof, "report", verify_mode=True)
    assert val_final.valid is True
    errors = [i for i in val_final.issues if i.severity == "error"]
    assert len(errors) == 0
