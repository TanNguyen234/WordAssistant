import concurrent.futures
import json
import pytest
from wordassistant.evidence.registry import EvidenceRegistry, EvidenceError

def test_evidence_strict_schema(tmp_path):
    reg = EvidenceRegistry(tmp_path / 'evidence.json')
    
    # Missing required field
    with pytest.raises(EvidenceError, match="Missing evidence field|authors"):
        reg.add({'id': 'e1', 'title': 'Title', 'year': 2024, 'url': 'https://example.com', 'verified_by': 'tester'})
        
    # Invalid year
    with pytest.raises(EvidenceError, match="year"):
        reg.add({'id': 'e1', 'title': 'Title', 'authors': ['A'], 'year': 1750, 'url': 'https://example.com', 'verified_by': 'tester', 'synthetic': False})
        
    # Invalid URL scheme
    with pytest.raises(EvidenceError, match="url"):
        reg.add({'id': 'e1', 'title': 'Title', 'authors': ['A'], 'year': 2024, 'url': 'ftp://bad', 'verified_by': 'tester', 'synthetic': False})
        
    # Empty scheme / no host
    with pytest.raises(EvidenceError, match="url"):
        reg.add({'id': 'e1', 'title': 'Title', 'authors': ['A'], 'year': 2024, 'url': 'https://', 'verified_by': 'tester', 'synthetic': False})
        
    with pytest.raises(EvidenceError, match="url"):
        reg.add({'id': 'e1', 'title': 'Title', 'authors': ['A'], 'year': 2024, 'url': 'https:///foo', 'verified_by': 'tester', 'synthetic': False})

    with pytest.raises(EvidenceError, match="synthetic"):
        reg.add({'id': 'e1', 'title': 'Title', 'authors': ['A'], 'year': 2024, 'url': 'https://example.com', 'verified_by': 'tester', 'synthetic': 'yes'})

    with pytest.raises(EvidenceError, match="synthetic"):
        reg.add({'id': 'e2', 'title': 'Title', 'authors': ['A'], 'year': 2024, 'url': 'https://example.com', 'verified_by': 'tester'})

def test_evidence_duplicate_id_policy(tmp_path):
    reg = EvidenceRegistry(tmp_path / 'evidence.json')
    rec = {'id': 'e1', 'title': 'Paper 1', 'authors': ['Author A'], 'year': 2023, 'url': 'https://example.com/p1', 'verified_by': 'human', 'synthetic': False}
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
    rec = {'id': 'e2', 'title': 'Paper 2', 'authors': ['Author B'], 'year': 2024, 'url': 'https://example.com/p2', 'verified_by': 'human', 'synthetic': False}
    reg.add(rec)
    
    assert reg.get('e2')['id'] == 'e2'
    with pytest.raises(EvidenceError, match="not found"):
        reg.get('non_existent')
        
    assert reg.remove('e2') is True
    assert len(reg.list()) == 0
    assert reg.remove('e2') is False

def test_evidence_concurrent_writes(tmp_path):
    reg_path = tmp_path / 'concurrent_evidence.json'
    reg = EvidenceRegistry(reg_path)
    
    def add_worker(idx: int):
        r = EvidenceRegistry(reg_path)
        r.add({
            'id': f'item_{idx}',
            'title': f'Title {idx}',
            'authors': [f'Author {idx}'],
            'year': 2024,
            'url': f'https://example.com/{idx}',
            'verified_by': 'concurrent_test',
            'synthetic': False,
        })
        
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(add_worker, i) for i in range(20)]
        for f in futures:
            f.result()
            
    items = reg.list()
    assert len(items) == 20


def test_registry_read_rejects_tampered_record_missing_synthetic(tmp_path):
    path = tmp_path / "tampered.json"
    path.write_text(
        json.dumps(
            {
                "fake": {
                    "id": "fake",
                    "title": "Self asserted source",
                    "authors": ["Agent"],
                    "year": 2026,
                    "url": "https://example.com/fake",
                    "verified_by": "the same agent",
                }
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(EvidenceError, match="synthetic"):
        EvidenceRegistry(path).get("fake")
