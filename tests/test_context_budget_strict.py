from __future__ import annotations
import pytest
from wordassistant.context.retrieve import build_context, estimate_tokens
from wordassistant.document.model import DocumentSection

def test_context_budget_rejects_invalid_types_and_values():
    sections = [DocumentSection("s1", "Title 1", "Some content", 1)]
    
    with pytest.raises((ValueError, TypeError)):
        build_context(sections, "query", max_tokens=0)
        
    with pytest.raises((ValueError, TypeError)):
        build_context(sections, "query", max_tokens=-1)
        
    with pytest.raises((ValueError, TypeError)):
        build_context(sections, "query", max_tokens=99)
        
    with pytest.raises((ValueError, TypeError)):
        build_context(sections, "query", max_tokens="8000")  # type: ignore

    with pytest.raises((ValueError, TypeError)):
        build_context(sections, "query", max_tokens=True)  # type: ignore

    with pytest.raises(ValueError, match="hard maximum of 12000"):
        build_context(sections, "query", max_tokens=12001)

def test_context_hard_invariant_preserved():
    sections = [
        DocumentSection(f"s{i}", f"Title {i}", "Long repetitive text " * 50, 1)
        for i in range(20)
    ]
    for budget in [100, 250, 500, 1000]:
        bundle = build_context(sections, "text", max_tokens=budget)
        assert estimate_tokens(bundle.text) <= budget
