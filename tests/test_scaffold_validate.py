from pathlib import Path
from docx import Document
from wordassistant.profiles.loader import load_profile
from wordassistant.document.scaffold import scaffold_document
from wordassistant.document.validate import validate_document

ROOT=Path(__file__).resolve().parents[1]


def test_hcmunre_report_scaffold_has_normative_geometry(tmp_path):
    profile=load_profile(ROOT/'profiles/hcmunre_dacn_2026_2027.json')
    out=tmp_path/'report.docx'
    scaffold_document(out, profile, 'report', title='TEST PROJECT')
    d=Document(out); s=d.sections[0]
    assert round(s.left_margin.cm,1)==3.0
    assert round(s.right_margin.cm,1)==2.0
    assert round(s.top_margin.cm,1)==2.0
    result=validate_document(out, profile, 'report')
    assert result.valid


def test_generic_profile_does_not_enforce_hcmunre_reference_rule(tmp_path):
    p=load_profile(ROOT/'profiles/generic.json')
    out=tmp_path/'generic.docx'
    scaffold_document(out,p,'default',title='General report')
    r=validate_document(out,p,'default')
    assert not any('10' in x.message and 'reference' in x.message.casefold() for x in r.issues)

def test_hcmunre_proposal_scaffold_matches_official_template_geometry(tmp_path):
    profile=load_profile(ROOT/'profiles/hcmunre_dacn_2026_2027.json')
    out=tmp_path/'proposal.docx'
    scaffold_document(out, profile, 'proposal', title='ignored for exact template copy')
    result=validate_document(out, profile, 'proposal')
    assert result.valid
