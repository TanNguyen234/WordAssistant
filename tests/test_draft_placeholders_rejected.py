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

def test_completed_synthetic_report_requires_materialized_dynamic_fields(tmp_path: Path, capsys):
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
    
    # Content placeholders are resolved, but TOC/LOF/LOT caches emitted by the
    # scaffold remain placeholders until a field-update backend materializes
    # them. Final delivery must fail closed at this stage.
    code = run(["verify", str(doc_path), "--profile", "hcmunre_dacn_2026_2027", "--variant", "report", "--json"])
    assert code == 2
    report = json.loads(capsys.readouterr().out)
    assert report["format_status"] == "PASS"
    assert report["field_structure_status"] == "PASS"
    assert report["field_freshness_status"] == "FAIL"
    assert report["manual_review_required"] is True
    
    val_final = validate_document(doc_path, prof, "report", verify_mode=True)
    assert val_final.valid is True
    errors = [i for i in val_final.issues if i.severity == "error"]
    assert len(errors) == 0


def test_global_placeholder_review_detects_vietnamese_placeholders_in_body_and_tables(tmp_path: Path):
    doc_path = tmp_path / "generic_placeholders.docx"
    document = Document()
    document.add_paragraph("LỜI CẢM ƠN")
    document.add_paragraph("[sinh viên tự điền sau khi xác nhận]")
    document.add_paragraph("Nguồn tham khảo được trích dẫn [1].")
    table = document.add_table(rows=1, cols=1)
    table.cell(0, 0).text = "[mô tả đóng góp thực tế]"
    document.save(doc_path)

    profile = resolve_profile("generic")
    draft = validate_document(doc_path, profile, "default", verify_mode=False)
    final = validate_document(doc_path, profile, "default", verify_mode=True)

    assert any(issue.code == "draft_placeholder_detected" and issue.severity == "warning" for issue in draft.issues)
    assert any(issue.code == "draft_placeholder_detected" and issue.severity == "error" for issue in final.issues)
    assert not any("[1]" in issue.message for issue in draft.issues if issue.code == "draft_placeholder_detected")


def test_global_numbering_review_is_scoped_to_chapter_style_outlines(tmp_path: Path):
    from wordassistant.operations.lists import apply_heading_numbering

    source = tmp_path / "numbering_source.docx"
    document = Document()
    document.add_heading("CHƯƠNG 1: TỔNG QUAN", level=1)
    document.add_heading("Cơ sở", level=2)
    document.add_heading("Khái niệm", level=3)
    document.add_heading("Overview", level=1)
    document.add_heading("Purpose", level=2)
    document.save(source)

    profile = resolve_profile("generic")
    unnumbered = validate_document(source, profile, "default", verify_mode=False)
    assert any(issue.code == "chapter_heading_numbering_missing" for issue in unnumbered.issues)

    numbered_path = tmp_path / "numbered.docx"
    apply_heading_numbering(
        source,
        output_path=numbered_path,
        allow_literal_prefixes=True,
        suppress_first_level_label=True,
    )
    numbered = validate_document(numbered_path, profile, "default", verify_mode=False)
    assert not any(issue.code == "chapter_heading_numbering_missing" for issue in numbered.issues)

    unnumbered_chapter_name = tmp_path / "unnumbered_chapter_name.docx"
    simple = Document()
    simple.add_heading("Overview", level=1)
    simple.add_heading("Purpose", level=2)
    simple.save(unnumbered_chapter_name)
    not_applicable = validate_document(
        unnumbered_chapter_name, profile, "default", verify_mode=False
    )
    assert not any(issue.code == "chapter_heading_numbering_missing" for issue in not_applicable.issues)


def test_hcmunre_report_profile_requires_chapter_numbering_at_final_verify(tmp_path: Path):
    doc_path = tmp_path / "hcmunre_unnumbered_chapter.docx"
    document = Document()
    document.add_heading("CHƯƠNG 1: TỔNG QUAN TÀI LIỆU", level=1)
    document.add_heading("Cơ sở lý thuyết", level=2)
    document.save(doc_path)

    profile = resolve_profile("hcmunre_dacn_2026_2027")
    report = validate_document(doc_path, profile, "report", verify_mode=True)

    findings = [issue for issue in report.issues if issue.code == "chapter_heading_numbering_missing"]
    assert len(findings) == 1
    assert findings[0].severity == "error"
