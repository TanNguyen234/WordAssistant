import pytest
from wordassistant.evidence.registry import EvidenceRegistry, EvidenceError

def test_evidence_strict_schema(tmp_path):
    reg = EvidenceRegistry(tmp_path / 'evidence.json')
    
    # Missing required field
    with pytest.raises(EvidenceError, match="Missing evidence field|authors"):
        reg.add({'id': 'e1', 'title': 'Title', 'year': 2024, 'url': 'https://example.com', 'verified_by': 'tester'})
        
    # Invalid year
    with pytest.raises(EvidenceError, match="year"):
        reg.add({'id': 'e1', 'title': 'Title', 'authors': ['A'], 'year': 1750, 'url': 'https://example.com', 'verified_by': 'tester'})
        
    # Invalid URL
    with pytest.raises(EvidenceError, match="url"):
        reg.add({'id': 'e1', 'title': 'Title', 'authors': ['A'], 'year': 2024, 'url': 'ftp://bad', 'verified_by': 'tester'})

def test_evidence_duplicate_id_policy(tmp_path):
    reg = EvidenceRegistry(tmp_path / 'evidence.json')
    rec = {'id': 'e1', 'title': 'Paper 1', 'authors': ['Author A'], 'year': 2023, 'url': 'https://example.com/p1', 'verified_by': 'human'}
    reg.add(rec)
    
    # Second add without replace=True must fail
    with pytest.raises(EvidenceError, match="already exists"):
        reg.add(rec, replace=False)
        
    # With replace=True it should succeed
    rec['title'] = 'Paper 1 (Updated)'
    reg.add(rec, replace=True)
    assert reg.get('e1')['title'] == 'Paper 1 (Updated)'

def test_evidence_get_and_remove(tmp_path):
    reg = EvidenceRegistry(tmp_path / 'evidence.json')
    rec = {'id': 'e2', 'title': 'Paper 2', 'authors': ['Author B'], 'year': 2024, 'url': 'https://example.com/p2', 'verified_by': 'human'}
    reg.add(rec)
    
    assert reg.get('e2')['id'] == 'e2'
    with pytest.raises(EvidenceError, match="not found"):
        reg.get('non_existent')
        
    assert reg.remove('e2') is True
    assert len(reg.list()) == 0
    assert reg.remove('e2') is False
