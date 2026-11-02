from dataclasses import replace
from pathlib import Path
import json
import pytest
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH as A
from wordassistant.document.validate import validate_document
from wordassistant.profiles.loader import load_profile, ProfileError
from wordassistant.operations.styles import update_style

ROOT = Path(__file__).parents[1]

@pytest.mark.parametrize('style_alignment,direct,expected_bad', [
    (A.LEFT, None, False), (A.LEFT, A.CENTER, True),
    (A.CENTER, A.LEFT, True), (None, None, False)])
def test_profile_alignment_checks_style_inheritance_and_direct_override(tmp_path, style_alignment, direct, expected_bad):
    doc = Document()
    doc.styles['Normal'].paragraph_format.alignment = A.LEFT
    doc.styles['Heading 1'].paragraph_format.alignment = style_alignment
    p = doc.add_heading('Section', 1); p.alignment = direct
    source = tmp_path / 'report.docx'; doc.save(source)
    profile = load_profile(ROOT / 'profiles/generic.json')
    variant = profile.variant('default')
    variant = replace(variant, typography=replace(variant.typography, styles={'heading1': {'alignment': 'left'}}))
    profile = replace(profile, variants={'default': variant})
    result = validate_document(source, profile, 'default', verify_mode=True)
    assert bool([x for x in result.issues if x.code == 'style_alignment_mismatch']) == expected_bad

@pytest.mark.parametrize('alignment,expected_bad', [(A.CENTER,False),(A.LEFT,True)])
def test_figure_alignment_is_scoped_and_does_not_reject_left_table_captions(tmp_path, alignment, expected_bad):
    raw = json.loads((ROOT / 'profiles/generic.json').read_text())
    raw['variants']['default']['captions'] = {'figure_labels':[{'display':'Figure','sequence':'Figure'}], 'figure_alignment':'center'}
    spec=tmp_path/'profile.json';spec.write_text(json.dumps(raw))
    profile=load_profile(spec)
    doc=Document(); p=doc.add_paragraph('Figure 1. Data model',style='Caption');p.alignment=alignment
    doc.add_paragraph('Table 1. Results',style='Caption').alignment=A.LEFT
    source=tmp_path/'report.docx';doc.save(source)
    result=validate_document(source,profile,'default',verify_mode=True)
    assert bool([x for x in result.issues if x.code=='figure_caption_alignment_mismatch']) == expected_bad

@pytest.mark.parametrize('value', ['diagonal', None, []])
def test_invalid_caption_alignment_fails_profile_load(tmp_path, value):
    raw=json.loads((ROOT/'profiles/generic.json').read_text());raw['variants']['default']['captions']={'figure_alignment':value}
    spec=tmp_path/'bad.json';spec.write_text(json.dumps(raw))
    with pytest.raises(ProfileError,match='figure_alignment'):load_profile(spec)

def test_style_update_persists_alignment_and_rejects_invalid_value(tmp_path):
    source=tmp_path/'source.docx';Document().save(source)
    output=tmp_path/'out.docx'
    update_style(source,output_path=output,name='Heading 1',alignment='left')
    assert Document(output).styles['Heading 1'].paragraph_format.alignment==A.LEFT
    bad=tmp_path/'bad.docx'
    with pytest.raises(ValueError,match='alignment'):update_style(source,output_path=bad,name='Heading 1',alignment='diagonal')
    assert not bad.exists()


def test_scaffold_front_matter_respects_explicit_heading_alignment(tmp_path):
    from wordassistant.document.scaffold import scaffold_document
    profile=load_profile(ROOT/'profiles/hcmunre_dacn_2026_2027.json')
    source=tmp_path/'scaffold.docx'
    scaffold_document(source,profile,'report',title='Test report',student='Student',supervisor='Supervisor')
    result=validate_document(source,profile,'report',verify_mode=True)
    assert not [x for x in result.issues if x.code=='style_alignment_mismatch']


def test_hcmunre_report_caption_uses_guide_body_size():
    profile=load_profile(ROOT/'profiles/hcmunre_dacn_2026_2027.json')
    assert profile.variant('report').typography.styles['Caption']['size_pt']==13
