from __future__ import annotations
import json
from pathlib import Path
from docx import Document
from wordassistant.document.scaffold import scaffold_document, _DEFAULT_FRONT_TITLES
from wordassistant.profiles.loader import load_profile

def test_default_front_titles_are_english_neutral():
    assert _DEFAULT_FRONT_TITLES["acknowledgements"] == "ACKNOWLEDGEMENTS"
    assert _DEFAULT_FRONT_TITLES["declaration"] == "DECLARATION"
    assert _DEFAULT_FRONT_TITLES["abstract"] == "ABSTRACT"
    assert _DEFAULT_FRONT_TITLES["table_of_contents"] == "TABLE OF CONTENTS"
    assert _DEFAULT_FRONT_TITLES["list_of_figures"] == "LIST OF FIGURES"
    assert _DEFAULT_FRONT_TITLES["list_of_tables"] == "LIST OF TABLES"
    assert _DEFAULT_FRONT_TITLES["abbreviations"] == "ABBREVIATIONS"

def test_generic_profile_contains_no_vietnamese_text(tmp_path: Path):
    custom_prof = {
        "id": "english_report",
        "name": "English University Report",
        "version": 1,
        "variants": {
            "default": {
                "page": {
                    "size": "A4",
                    "width_cm": 21.0,
                    "height_cm": 29.7,
                    "margins_cm": {"top": 2.0, "bottom": 2.0, "left": 2.0, "right": 2.0},
                    "one_sided": True
                },
                "typography": {
                    "body_font": "Arial",
                    "body_size_pt": 11.0
                },
                "front_matter": [
                    "acknowledgements",
                    "declaration",
                    "abstract",
                    "table_of_contents"
                ]
            }
        }
    }
    prof_file = tmp_path / "custom.json"
    prof_file.write_text(json.dumps(custom_prof), encoding="utf-8")
    
    prof = load_profile(prof_file)
    out_docx = tmp_path / "english.docx"
    scaffold_document(out_docx, prof, "default", title="AI Research Paper")
    
    d = Document(out_docx)
    all_text = " ".join(p.text for p in d.paragraphs)
    
    # Assert English titles are present
    assert "ACKNOWLEDGEMENTS" in all_text
    assert "DECLARATION" in all_text
    assert "ABSTRACT" in all_text
    
    # Assert NO Vietnamese defaults leaked
    assert "LỜI CẢM ƠN" not in all_text
    assert "LỜI CAM ĐOAN" not in all_text
    assert "MỤC LỤC" not in all_text
