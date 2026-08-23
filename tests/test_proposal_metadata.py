import hashlib
from pathlib import Path
from docx import Document
from wordassistant.profiles.loader import load_profile
from wordassistant.document.scaffold import scaffold_document

ROOT = Path(__file__).resolve().parents[1]
PROPOSAL_SRC = ROOT / 'use_cases/hcmunre_dacn_2026_2027/assets/mau_de_cuong_do_an_chuyen_nganh.docx'
EXPECTED_SHA256 = 'bb291a6de459e33267170c3dd9087903a0d9f1911086bbfc935cb9f7781904e6'

def test_proposal_scaffold_without_metadata_produces_exact_byte_clone(tmp_path):
    src_bytes = PROPOSAL_SRC.read_bytes()
    assert hashlib.sha256(src_bytes).hexdigest().lower() == EXPECTED_SHA256
    
    profile = load_profile(ROOT / 'profiles/hcmunre_dacn_2026_2027.json')
    out = tmp_path / 'unmodified_proposal.docx'
    
    # Call with no explicit metadata
    scaffold_document(out, profile, 'proposal')
    
    # Must produce 100% byte-identical copy of template
    out_bytes = out.read_bytes()
    assert hashlib.sha256(out_bytes).hexdigest().lower() == EXPECTED_SHA256

def test_proposal_scaffold_fills_all_individual_metadata_fields(tmp_path):
    src_bytes = PROPOSAL_SRC.read_bytes()
    assert hashlib.sha256(src_bytes).hexdigest().lower() == EXPECTED_SHA256
    
    profile = load_profile(ROOT / 'profiles/hcmunre_dacn_2026_2027.json')
    out = tmp_path / 'filled_proposal.docx'
    
    scaffold_document(
        out,
        profile,
        'proposal',
        title='XÂY DỰNG TRỢ LÝ THÔNG MINH CHO TÀI LIỆU WORD',
        student='Nguyễn Văn An - 2100005678',
        supervisor='PGS. TS. Lê Văn C'
    )
    
    assert out.exists()
    d = Document(out)
    full_text = "\n".join(p.text for p in d.paragraphs)
    
    # Check EACH metadata field individually - NO OR assertions
    assert 'XÂY DỰNG TRỢ LÝ THÔNG MINH CHO TÀI LIỆU WORD' in full_text
    assert 'Nguyễn Văn An - 2100005678' in full_text
    assert 'PGS. TS. Lê Văn C' in full_text
    
    # Verify source asset bytes remain untouched
    src_bytes_after = PROPOSAL_SRC.read_bytes()
    assert hashlib.sha256(src_bytes_after).hexdigest().lower() == EXPECTED_SHA256
