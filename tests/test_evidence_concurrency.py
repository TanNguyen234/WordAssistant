from __future__ import annotations
import concurrent.futures
from pathlib import Path
from wordassistant.evidence.registry import EvidenceRegistry

def test_evidence_concurrent_writers(tmp_path: Path):
    reg_path = tmp_path / "evidence.json"
    reg = EvidenceRegistry(reg_path)
    
    def add_batch(start_idx: int, count: int):
        for i in range(start_idx, start_idx + count):
            rec = {
                "id": f"rec_{i}",
                "title": f"Title {i}",
                "authors": [f"Author {i}"],
                "year": 2024,
                "url": f"https://example.com/item/{i}",
                "verified_by": "CI",
                "synthetic": False,
            }
            reg.add(rec)
            
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        f1 = executor.submit(add_batch, 0, 15)
        f2 = executor.submit(add_batch, 15, 15)
        f1.result()
        f2.result()
        
    records = reg.list()
    assert len(records) == 30
    ids = {r["id"] for r in records}
    assert ids == {f"rec_{i}" for i in range(30)}
