import pytest
from wordassistant.evidence.registry import EvidenceRegistry, EvidenceError


def test_evidence_requires_provenance(tmp_path):
    reg=EvidenceRegistry(tmp_path/'evidence.json')
    with pytest.raises(EvidenceError):
        reg.add({'id':'x','title':'Paper','authors':['A'],'year':2024})
    reg.add({'id':'x','title':'Paper','authors':['A'],'year':2024,'url':'https://example.org/p','verified_by':'manual'})
    assert reg.get('x')['verified_by']=='manual'
