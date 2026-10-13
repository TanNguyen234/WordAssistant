from __future__ import annotations


# Evidence is explicit and reviewable. Absence means UNVERIFIED; backend names
# never imply verification on their own.
NATIVE_WORD_LIVE_RUN = "docs/reviews/native-word-live-evidence-2026-08-30.json"

OPERATION_EVIDENCE: dict[str, dict[str, dict[str, object]]] = {
    "text.edit": {
        "structural": {"status": "VERIFIED", "tests": ["tests/core/test_text_operations.py"]},
    },
    "heading.numbering_apply": {
        "structural": {"status": "VERIFIED", "tests": ["tests/ooxml/test_numbering_operations.py"]},
        "native_roundtrip": {"status": "VERIFIED", "tests": ["tests/native_word/test_native_live_operations.py::test_live_heading_numbering_is_recognized_by_word_list_engine"]},
        "dynamic_result": {"status": "VERIFIED", "tests": ["tests/native_word/test_native_live_operations.py::test_live_heading_numbering_is_recognized_by_word_list_engine"]},
    },
    "heading.numbering_remove": {
        "structural": {"status": "VERIFIED", "tests": ["tests/ooxml/test_numbering_operations.py"]},
    },
    "table.create": {
        "structural": {"status": "VERIFIED", "tests": ["tests/core/test_table_operations.py"]},
    },
    "table.layout": {
        "structural": {"status": "VERIFIED", "tests": ["tests/integration/test_review_remediations.py"]},
    },
    "field.insert": {
        "structural": {"status": "VERIFIED", "tests": ["tests/ooxml/test_field_engine.py"]},
    },
    "field.remove": {
        "structural": {"status": "VERIFIED", "tests": ["tests/integration/test_review_remediations.py"]},
    },
    "bookmark.rename": {
        "structural": {"status": "VERIFIED", "tests": ["tests/integration/test_review_remediations.py"]},
    },
    "reference.cross_reference": {
        "structural": {"status": "VERIFIED", "tests": ["tests/integration/test_review_remediations.py"]},
    },
    "content-control.create": {
        "structural": {"status": "VERIFIED", "tests": ["tests/ooxml/test_properties_protection_equations_controls.py"], "scope": "plain_text only"},
    },
    "field.update_all": {
        "native_roundtrip": {"status": "VERIFIED", "tests": ["tests/native_word/test_native_live_operations.py::test_live_field_update_survives_reopen"], "scope": "Word-native evaluation, save, reopen, and persisted result verification"},
        "dynamic_result": {"status": "VERIFIED", "tests": ["tests/native_word/test_native_live_operations.py::test_live_page_and_numpages_are_evaluated_and_persisted"], "scope": "PAGE and NUMPAGES evaluated and persisted by an isolated Microsoft Word session"},
    },
    "comment.create": {
        "native_roundtrip": {"status": "VERIFIED", "tests": ["tests/native_word/test_native_live_operations.py::test_live_comment_create_list_delete"]},
    },
    "comment.list": {
        "native_roundtrip": {"status": "VERIFIED", "tests": ["tests/native_word/test_native_live_operations.py::test_live_comment_create_list_delete"]},
    },
    "comment.delete": {
        "native_roundtrip": {"status": "VERIFIED", "tests": ["tests/native_word/test_native_live_operations.py::test_live_comment_create_list_delete"]},
    },
    "revision.enable": {
        "native_roundtrip": {"status": "VERIFIED", "tests": ["tests/native_word/test_native_live_operations.py::test_live_revision_toggle_compare_accept_and_native_render"]},
    },
    "revision.disable": {
        "native_roundtrip": {"status": "VERIFIED", "tests": ["tests/native_word/test_native_live_operations.py::test_live_revision_toggle_compare_accept_and_native_render"]},
    },
    "revision.list": {
        "native_roundtrip": {"status": "VERIFIED", "tests": ["tests/native_word/test_native_live_operations.py::test_live_revision_toggle_compare_accept_and_native_render"]},
    },
    "revision.accept_all": {
        "native_roundtrip": {"status": "VERIFIED", "tests": ["tests/native_word/test_native_live_operations.py::test_live_revision_toggle_compare_accept_and_native_render"]},
    },
    "compare.documents": {
        "native_roundtrip": {"status": "VERIFIED", "tests": ["tests/native_word/test_native_live_operations.py::test_live_revision_toggle_compare_accept_and_native_render"]},
    },
    "render.pdf": {
        "structural": {"status": "VERIFIED", "tests": ["tests/test_render_isolated.py"]},
        "native_roundtrip": {"status": "VERIFIED", "tests": ["tests/native_word/test_native_live_operations.py::test_live_revision_toggle_compare_accept_and_native_render"]},
        "visual": {"status": "AVAILABLE_NOT_REVIEWED", "tests": []},
    },
}


_STRUCTURAL_TEST_GROUPS = {
    "tests/core/test_format_operations.py": {
        "format.run", "format.paragraph", "style.create", "style.apply", "style.delete",
    },
    "tests/core/test_table_operations.py": {
        "table.create", "table.insert_row", "table.insert_column",
        "table.delete_column", "table.set_cell", "table.merge", "table.layout",
    },
    "tests/core/test_image_operations.py": {
        "image.insert", "image.resize", "image.remove",
    },
    "tests/ooxml/test_numbering_operations.py": {
        "list.create", "list.restart", "list.set_level",
        "heading.numbering_apply", "heading.numbering_remove",
        "heading.numbering_inspect",
    },
    "tests/ooxml/test_section_layout.py": {"section.add", "section.layout"},
    "tests/ooxml/test_styles.py": {"style.update"},
    "tests/ooxml/test_page_numbering_semantics.py": {
        "page-number.apply", "page-number.inspect",
    },
    "tests/ooxml/test_field_engine.py": {
        "field.insert", "field.inspect", "field.lock", "field.unlock", "field.remove",
    },
    "tests/ooxml/test_caption_toc_fields.py": {"toc.insert", "caption.insert"},
    "tests/ooxml/test_bookmark_cross_reference.py": {
        "bookmark.create", "bookmark.rename", "bookmark.delete", "bookmark.inspect",
        "reference.cross_reference", "reference.hyperlink",
    },
    "tests/core/test_citation_workflow.py": {
        "citation.insert", "citation.remove", "citation.list", "bibliography.generate",
    },
    "tests/ooxml/test_properties_protection_equations_controls.py": {
        "properties.set", "properties.get", "protection.protect",
        "protection.unprotect", "protection.inspect", "equation.insert",
        "content-control.create", "content-control.set", "content-control.list",
    },
}

for _test_path, _operations in _STRUCTURAL_TEST_GROUPS.items():
    for _operation in _operations:
        OPERATION_EVIDENCE.setdefault(_operation, {})["structural"] = {
            "status": "VERIFIED",
            "tests": [_test_path],
        }

for _operation in ("content-control.create", "content-control.set", "content-control.list"):
    OPERATION_EVIDENCE[_operation]["structural"]["scope"] = "plain_text only"

for _dimensions in OPERATION_EVIDENCE.values():
    for _dimension_name in ("native_roundtrip", "dynamic_result"):
        _record = _dimensions.get(_dimension_name)
        if _record is not None and _record.get("status") == "VERIFIED":
            _record["runs"] = [NATIVE_WORD_LIVE_RUN]


def evidence_for(operation: str) -> dict[str, dict[str, object]]:
    return OPERATION_EVIDENCE.get(operation, {})


def operation_is_verified(operation: str, *, native: bool) -> bool:
    dimension = "native_roundtrip" if native else "structural"
    return evidence_for(operation).get(dimension, {}).get("status") == "VERIFIED"
