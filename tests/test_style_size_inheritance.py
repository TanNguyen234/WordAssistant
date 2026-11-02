import pytest
from pathlib import Path
from docx import Document
from docx.shared import Pt

from wordassistant.document.validate import validate_document
from wordassistant.profiles.loader import load_profile


@pytest.mark.parametrize('inherited_size,expected_error', [(13, False), (12, True)])
def test_profile_style_size_resolves_base_style_but_keeps_persistent_requirement(tmp_path, inherited_size, expected_error):
    doc = Document()
    doc.styles['Normal'].font.size = Pt(inherited_size)
    doc.styles['Heading 3'].font.size = None
    doc.styles['Heading 3'].base_style = doc.styles['Normal']
    paragraph = doc.add_heading('Inherited subsection', 3)
    # Directly correct text cannot hide a wrong persistent style definition.
    paragraph.runs[0].font.size = Pt(13)
    path = tmp_path / 'inherited.docx'
    doc.save(path)
    profile = load_profile(Path(__file__).parents[1] / 'profiles/hcmunre_dacn_2026_2027.json')
    result = validate_document(path, profile, 'course_essay_style', verify_mode=True)
    errors = [issue for issue in result.issues if issue.code == 'style_size_mismatch' and 'Heading 3' in issue.message]
    assert bool(errors) == expected_error
