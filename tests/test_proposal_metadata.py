import hashlib
from pathlib import Path
from docx import Document
from wordassistant.profiles.loader import load_profile
from wordassistant.document.scaffold import scaffold_document

ROOT = Path(__file__).resolve().parents[1]
PROPOSAL_SRC = ROOT / 'use_cases/hcmunre_dacn_2026_2027/assets/mau_de_cuong_do_an_chuyen_nganh.docx'
EXPECTED_SHA256 = 'bb291a6de459e33267170c3dd9087903a0d9f1911086bbfc935cb9f7781904e6'

def test_proposal_scaffold_fills_metadata_without_altering_source_bytes(tmp_path):
    # Verify source asset hash BEFORE
    src_bytes = PROPOSAL_SRC.read_bytes()
    assert hashlib.sha256(src_bytes).hexdigest().lower() == EXPECTED_SHA256
    
    profile = load_profile(ROOT / 'profiles/hcmunre_dacn_2026_2027.json')
    out = tmp_path / 'my_proposal.docx'
    
    scaffold_document(
        out,
        profile,
        'proposal',
        title='XÂY DỰNG TRỢ LÝ THÔNG MINH CHO TÀI LIỆU WORD',
        student='Nguyễn Văn An - 2100005678',
        supervisor='PGS. TS. Lê Văn C'
    )
    
    # 1. Output must exist and have filled metadata
    assert out.exists()
    d = Document(out)
    full_text = "\n".join(p.text for p in d.paragraphs)
    # Check that metadata was placed into the cloned doc
    assert 'XÂY DỰNG TRỢ LÝ THÔNG MINH CHO TÀI LIỆU WORD' in full_text or 'Nguyễn Văn An' in full_text
    
    # 2. Source asset MUST remain byte-identical
    src_bytes_after = PROPOSAL_SRC.read_bytes()
    assert hashlib.sha256(src_bytes_after).hexdigest().lower() == EXPECTED_SHA256
