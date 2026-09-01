from wordassistant.backends.word_native.worker import _field_results_match


def _field(*, story, field_type, instruction, result, locked=False):
    return {
        "story": story,
        "type": field_type,
        "instruction": instruction,
        "result": result,
        "locked": locked,
    }


def test_field_freshness_ignores_com_enumeration_order_and_story_labels():
    before = [
        _field(story="story:9:0", field_type=33, instruction="PAGE", result="1"),
        _field(story="story:9:0", field_type=26, instruction="NUMPAGES", result="3"),
    ]
    after = [
        _field(story="story:9:1", field_type=26, instruction="NUMPAGES", result="3"),
        _field(story="story:9:1", field_type=33, instruction="PAGE", result="1"),
    ]

    assert _field_results_match(before, after)


def test_field_freshness_treats_shared_page_results_as_contextual():
    before = [
        _field(story="story:9:0", field_type=33, instruction="PAGE", result="i")
    ]
    after = [
        _field(story="story:9:1", field_type=33, instruction="PAGE", result="xi")
    ]

    assert _field_results_match(before, after)


def test_field_freshness_detects_changed_results_or_lock_state():
    before = [
        _field(story="document", field_type=26, instruction="NUMPAGES", result="3")
    ]

    assert not _field_results_match(
        before,
        [_field(story="document", field_type=26, instruction="NUMPAGES", result="4")],
    )
    assert not _field_results_match(
        before,
        [
            _field(
                story="document",
                field_type=26,
                instruction="NUMPAGES",
                result="3",
                locked=True,
            )
        ],
    )
    assert not _field_results_match([], [])


def test_field_freshness_ignores_only_volatile_word_toc_bookmark_suffixes():
    before = [
        _field(
            story="document",
            field_type=88,
            instruction='HYPERLINK \\l "_Toc239020693"',
            result="Heading\t1",
        ),
        _field(
            story="document",
            field_type=37,
            instruction="PAGEREF _Toc239020693 \\h",
            result="1",
        ),
    ]
    after = [
        _field(
            story="document",
            field_type=37,
            instruction="PAGEREF _Toc239020701 \\h",
            result="1",
        ),
        _field(
            story="document",
            field_type=88,
            instruction='HYPERLINK \\l "_Toc239020701"',
            result="Heading\t1",
        ),
    ]

    assert _field_results_match(before, after)
    after[0]["instruction"] = "PAGEREF customer_bookmark \\h"
    assert not _field_results_match(before, after)

    customer_before = [
        _field(
            story="document",
            field_type=88,
            instruction='HYPERLINK \\l "_Toc123Customer"',
            result="Customer A",
        )
    ]
    customer_after = [
        _field(
            story="document",
            field_type=88,
            instruction='HYPERLINK \\l "_Toc456Customer"',
            result="Customer A",
        )
    ]
    assert not _field_results_match(customer_before, customer_after)
