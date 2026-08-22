from pathlib import Path
from wordassistant.document.structure import index_docx

ROOT = Path(__file__).resolve().parents[1]
GUIDE = ROOT/'use_cases/hcmunre_dacn_2026_2027/assets/huong_dan_trinh_bay_dacn_2026_2027.docx'
PROPOSAL = ROOT/'use_cases/hcmunre_dacn_2026_2027/assets/mau_de_cuong_do_an_chuyen_nganh.docx'


def test_guidance_is_not_one_preamble_and_not_oversegmented():
    sections=index_docx(GUIDE)
    assert 10 <= len(sections) <= 45
    titles=[s.title.casefold() for s in sections]
    assert any('tài liệu tham khảo' in t for t in titles)
    assert any('trích dẫn' in t for t in titles)


def test_proposal_detects_major_and_minor_structure():
    sections=index_docx(PROPOSAL)
    assert 8 <= len(sections) <= 30
    titles='\n'.join(s.title for s in sections).casefold()
    assert 'mở đầu' in titles
    assert 'phương pháp nghiên cứu' in titles
    assert 'tài liệu tham khảo' in titles

def test_citation_section_does_not_swallow_later_sample_pages():
    sections=index_docx(GUIDE)
    sec=next(s for s in sections if s.title.startswith('17.3.'))
    assert 'TRƯỜNG ĐẠI HỌC TÀI NGUYÊN' not in sec.text
