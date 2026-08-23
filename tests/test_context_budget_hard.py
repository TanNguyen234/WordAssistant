import random
import pytest
from wordassistant.context.retrieve import build_context, estimate_tokens
from wordassistant.document.model import DocumentSection

def make_sections(n=200):
    return [
        DocumentSection(
            section_id=f's{i}',
            title=f'Section {i}: Topic {i}',
            text=(f'content term{i} analysis data result ' * 50),
            level=1
        )
        for i in range(n)
    ]

def test_hard_budget_invariant_never_exceeded():
    # Test across multiple budgets and oversized texts
    ss = [
        DocumentSection('s1', 'Giant Section', 'word ' * 5000, 1),
        DocumentSection('s2', 'Short Section', 'quick brown fox', 1)
    ]
    for budget in [100, 120, 150, 200, 300, 500, 1000, 2500]:
        bundle = build_context(ss, query='Giant word', max_tokens=budget)
        actual_tokens = estimate_tokens(bundle.text)
        assert actual_tokens <= budget, f"Exceeded budget {budget}: actual={actual_tokens}"
        assert bundle.estimated_tokens == actual_tokens
        assert bundle.estimated_tokens <= bundle.max_tokens

def test_hard_budget_with_adversarial_short_words():
    # Many single-letter words where word_count * 1.6 dominates chars / 3.0
    short_words_text = " ".join(["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"] * 300)
    ss = [DocumentSection('adv', 'Adversarial Short Words', short_words_text, 1)]
    for budget in [100, 105, 110, 150, 250, 500]:
        bundle = build_context(ss, query='a b c', max_tokens=budget)
        actual_tokens = estimate_tokens(bundle.text)
        assert actual_tokens <= budget, f"Failed for budget {budget}: actual={actual_tokens}"
        assert bundle.estimated_tokens == actual_tokens
        assert len(bundle.text) > 0, f"Expected non-empty text for budget {budget}"

def test_max_tokens_100_produces_useful_output_for_oversized_section():
    ss = [DocumentSection('s1', 'Huge Section Title', 'important information ' * 300, 1)]
    bundle = build_context(ss, query='important information', max_tokens=100)
    assert estimate_tokens(bundle.text) <= 100
    assert bundle.estimated_tokens <= 100
    assert len(bundle.sections) > 0
    assert "important information" in bundle.text
    assert "[… truncated to budget …]" in bundle.text or "[…truncated…]" in bundle.text

def test_randomized_budget_properties():
    random.seed(42)
    vocab = ["alpha", "beta", "gamma", "delta", "epsilon", "nhiệm", "vụ", "đồ", "án", "phương", "pháp"]
    sections = []
    for i in range(50):
        words = [random.choice(vocab) for _ in range(random.randint(10, 500))]
        sections.append(DocumentSection(f's{i}', f'Heading {i} {" ".join(words[:4])}', " ".join(words), 1))
    
    for _ in range(25):
        budget = random.randint(100, 2000)
        query = " ".join([random.choice(vocab) for _ in range(3)])
        bundle = build_context(sections, query=query, max_tokens=budget)
        actual_tokens = estimate_tokens(bundle.text)
        assert actual_tokens <= budget, f"Randomized test failed: budget={budget}, actual={actual_tokens}"
        assert bundle.estimated_tokens == actual_tokens
