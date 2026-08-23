import json
from pathlib import Path
from docx import Document
from wordassistant.profiles.loader import load_profile
from wordassistant.document.scaffold import scaffold_document

def test_custom_profile_cover_contains_no_hcmunre_strings(tmp_path):
    custom_profile_data = {
        "id": "oxford_thesis",
        "name": "Oxford University Thesis",
        "version": 1,
        "variants": {
            "default": {
                "page": {
                    "size": "A4",
                    "width_cm": 21.0,
                    "height_cm": 29.7,
                    "margins_cm": {"top": 2.5, "bottom": 2.5, "left": 3.0, "right": 2.5},
                    "one_sided": True
                },
                "typography": {
                    "body_font": "Calibri",
                    "body_size_pt": 11.0,
                    "line_spacing": 1.15
                },
                "front_matter": ["cover", "inner_cover", "abstract", "table_of_contents"],
                "section_blueprint": [
                    {"title": "1. Introduction", "level": 1},
                    {"title": "2. Methods", "level": 1}
                ],
                "cover": {
                    "institution_lines": ["UNIVERSITY OF OXFORD", "Department of Computer Science"],
                    "document_type": "DOCTORAL DISSERTATION",
                    "title_prefix": "TITLE:",
                    "metadata_fields": [
                        {"label": "Candidate", "value_key": "student", "default": "[Candidate Name]"},
                        {"label": "Supervisor", "value_key": "supervisor", "default": "[Supervisor Name]"}
                    ],
                    "location_year": "OXFORD, 2026"
                }
            }
        }
    }
    
    prof_file = tmp_path / "oxford.json"
    prof_file.write_text(json.dumps(custom_profile_data), encoding="utf-8")
    profile = load_profile(prof_file)
    
    out_docx = tmp_path / "oxford_scaffold.docx"
    scaffold_document(
        out_docx,
        profile,
        "default",
        title="NEURAL NETWORK OPTIMIZATION",
        student="Jane Doe",
        supervisor="Prof. Alan Turing"
    )
    
    d = Document(out_docx)
    full_text = "\n".join(p.text for p in d.paragraphs)
    
    # Custom strings must be present
    assert "UNIVERSITY OF OXFORD" in full_text
    assert "DOCTORAL DISSERTATION" in full_text
    assert "Jane Doe" in full_text
    assert "Prof. Alan Turing" in full_text
    assert "OXFORD, 2026" in full_text
    
    # HCMUNRE strings MUST NOT be present
    forbidden = [
        "TÀI NGUYÊN VÀ MÔI TRƯỜNG",
        "HCMUNRE",
        "KHOA CÔNG NGHỆ THÔNG TIN",
        "BÁO CÁO ĐỒ ÁN CHUYÊN NGÀNH",
        "TP. HỒ CHÍ MINH",
        "2023 - 2027",
        "Khóa học:",
        "Ngành:"
    ]
    for bad_str in forbidden:
        assert bad_str not in full_text, f"Found hardcoded HCMUNRE string in generic profile scaffold: {bad_str}"
