from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

from ..evidence.registry import EvidenceRegistry
from ..operations.citations import (
    _TAG_PREFIX,
    _format_bibliography,
    _format_in_text,
    _replace_bibliography_content,
)
from ..operations.common import atomic_save


_ROOT_KEYS = {"version", "sections", "bibliography_heading", "citation_style"}
_SECTION_KEYS = {"heading", "paragraphs", "subsections"}
_SUBSECTION_KEYS = {"title", "level", "paragraphs"}
_PARAGRAPH_KEYS = {"text", "citations"}
_PLACEHOLDERS = {"[section content...]", "[front matter content]", "[document content]"}


def _unknown_keys(value: Mapping[str, Any], allowed: set[str], context: str) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise ValueError(f"Unsupported {context} keys: {', '.join(unknown)}")


def _paragraph_spec(value: Any, context: str) -> tuple[str, list[str]]:
    if isinstance(value, str):
        text = value
        citations: list[str] = []
    elif isinstance(value, Mapping):
        _unknown_keys(value, _PARAGRAPH_KEYS, context)
        text = value.get("text")
        citations = value.get("citations", [])
        if not isinstance(citations, list) or any(
            not isinstance(item, str) or not item.strip() for item in citations
        ):
            raise TypeError(f"{context}.citations must be an array of non-empty strings")
        citations = [item.strip() for item in citations]
    else:
        raise TypeError(f"{context} must be a string or object")
    if not isinstance(text, str) or not text.strip():
        raise ValueError(f"{context}.text must be a non-empty string")
    if len(text) > 20_000:
        raise ValueError(f"{context}.text exceeds 20000 characters")
    return text.strip(), citations


def _append_citation(paragraph, evidence_id: str, text: str) -> None:
    if len(paragraph._p):
        paragraph.add_run(" ")
    sdt = OxmlElement("w:sdt")
    properties = OxmlElement("w:sdtPr")
    tag = OxmlElement("w:tag")
    tag.set(qn("w:val"), f"{_TAG_PREFIX}{evidence_id}")
    alias = OxmlElement("w:alias")
    alias.set(qn("w:val"), f"Citation {evidence_id}")
    properties.extend([alias, tag])
    content = OxmlElement("w:sdtContent")
    run = OxmlElement("w:r")
    value = OxmlElement("w:t")
    value.text = text
    run.append(value)
    content.append(run)
    sdt.extend([properties, content])
    paragraph._p.append(sdt)


def _insert_after(document, cursor, text: str, style: str | None = None):
    paragraph = document.add_paragraph(style=style)
    paragraph.add_run(text)
    cursor.addnext(paragraph._p)
    return paragraph


def _remove_placeholder_after(paragraph) -> bool:
    node = paragraph._p.getnext()
    if node is None or node.tag != qn("w:p"):
        return False
    text = "".join(item.text or "" for item in node.iter(qn("w:t"))).strip().casefold()
    if text not in _PLACEHOLDERS:
        return False
    node.getparent().remove(node)
    return True


def compose_document(
    input_path: str | Path,
    *,
    output_path: str | Path,
    content: Mapping[str, Any],
    evidence_registry: str | Path | None = None,
    min_visible_characters: int | None = None,
    max_visible_characters: int | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Populate an existing scaffold from a bounded, fail-closed JSON contract."""
    if not isinstance(content, Mapping):
        raise TypeError("Composition content must be a JSON object")
    _unknown_keys(content, _ROOT_KEYS, "composition")
    if content.get("version") != 1 or isinstance(content.get("version"), bool):
        raise ValueError("Composition content version must be 1")
    sections = content.get("sections")
    if not isinstance(sections, list) or not sections:
        raise ValueError("Composition sections must be a non-empty array")
    if len(sections) > 100:
        raise ValueError("Composition cannot contain more than 100 sections")
    for name, value in (
        ("min_visible_characters", min_visible_characters),
        ("max_visible_characters", max_visible_characters),
    ):
        if value is not None and (type(value) is not int or value < 0):
            raise ValueError(f"{name} must be a non-negative integer")
    if (
        min_visible_characters is not None
        and max_visible_characters is not None
        and min_visible_characters > max_visible_characters
    ):
        raise ValueError("min_visible_characters cannot exceed max_visible_characters")

    citation_style = content.get("citation_style", "numeric")
    if not isinstance(citation_style, str) or not citation_style.strip():
        raise ValueError("citation_style must be a non-empty string")
    registry = EvidenceRegistry(evidence_registry) if evidence_registry else None
    document = Document(input_path)
    citation_numbers: dict[str, int] = {}
    paragraph_count = 0
    subsection_count = 0
    removed_placeholders = 0
    used_targets: set[str] = set()

    for section_index, section in enumerate(sections):
        context = f"sections[{section_index}]"
        if not isinstance(section, Mapping):
            raise TypeError(f"{context} must be an object")
        _unknown_keys(section, _SECTION_KEYS, context)
        heading = section.get("heading")
        if not isinstance(heading, str) or not heading.strip():
            raise ValueError(f"{context}.heading must be a non-empty string")
        key = heading.strip().casefold()
        if key in used_targets:
            raise ValueError(f"Duplicate composition target heading: {heading!r}")
        used_targets.add(key)
        matches = [
            paragraph
            for paragraph in document.paragraphs
            if paragraph.text.strip().casefold() == key
        ]
        if len(matches) != 1:
            raise ValueError(
                f"{context}.heading must match exactly one paragraph; found {len(matches)}"
            )
        target = matches[0]
        removed_placeholders += int(_remove_placeholder_after(target))
        cursor = target._p

        raw_paragraphs = section.get("paragraphs", [])
        if not isinstance(raw_paragraphs, list):
            raise TypeError(f"{context}.paragraphs must be an array")
        for paragraph_index, raw in enumerate(raw_paragraphs):
            text, citations = _paragraph_spec(
                raw, f"{context}.paragraphs[{paragraph_index}]"
            )
            paragraph = _insert_after(document, cursor, text)
            for evidence_id in citations:
                if registry is None:
                    raise ValueError("evidence_registry is required when citations are used")
                record = registry.get(evidence_id)
                number = citation_numbers.setdefault(evidence_id, len(citation_numbers) + 1)
                _append_citation(
                    paragraph,
                    evidence_id,
                    _format_in_text(record, citation_style, number),
                )
            cursor = paragraph._p
            paragraph_count += 1

        raw_subsections = section.get("subsections", [])
        if not isinstance(raw_subsections, list):
            raise TypeError(f"{context}.subsections must be an array")
        for subsection_index, subsection in enumerate(raw_subsections):
            sub_context = f"{context}.subsections[{subsection_index}]"
            if not isinstance(subsection, Mapping):
                raise TypeError(f"{sub_context} must be an object")
            _unknown_keys(subsection, _SUBSECTION_KEYS, sub_context)
            title = subsection.get("title")
            level = subsection.get("level", 2)
            if not isinstance(title, str) or not title.strip():
                raise ValueError(f"{sub_context}.title must be a non-empty string")
            if type(level) is not int or not 2 <= level <= 9:
                raise ValueError(f"{sub_context}.level must be an integer from 2 to 9")
            heading_paragraph = _insert_after(
                document, cursor, title.strip(), f"Heading {level}"
            )
            cursor = heading_paragraph._p
            subsection_count += 1
            raw_sub_paragraphs = subsection.get("paragraphs", [])
            if not isinstance(raw_sub_paragraphs, list):
                raise TypeError(f"{sub_context}.paragraphs must be an array")
            for paragraph_index, raw in enumerate(raw_sub_paragraphs):
                text, citations = _paragraph_spec(
                    raw, f"{sub_context}.paragraphs[{paragraph_index}]"
                )
                paragraph = _insert_after(document, cursor, text)
                for evidence_id in citations:
                    if registry is None:
                        raise ValueError("evidence_registry is required when citations are used")
                    record = registry.get(evidence_id)
                    number = citation_numbers.setdefault(
                        evidence_id, len(citation_numbers) + 1
                    )
                    _append_citation(
                        paragraph,
                        evidence_id,
                        _format_in_text(record, citation_style, number),
                    )
                cursor = paragraph._p
                paragraph_count += 1

    bibliography_heading = content.get("bibliography_heading")
    if bibliography_heading is not None:
        if not isinstance(bibliography_heading, str) or not bibliography_heading.strip():
            raise ValueError("bibliography_heading must be a non-empty string")
        if registry is None:
            raise ValueError("evidence_registry is required for bibliography generation")
        lines = [
            _format_bibliography(registry.get(evidence_id), citation_style, number)
            for evidence_id, number in citation_numbers.items()
        ]
        _replace_bibliography_content(document, bibliography_heading, lines)

    if paragraph_count > 5000:
        raise ValueError("Composition cannot contain more than 5000 content paragraphs")
    visible_characters = sum(
        len("".join(node.text or "" for node in paragraph._p.iter(qn("w:t"))).strip())
        for paragraph in document.paragraphs
    )
    if (
        min_visible_characters is not None
        and visible_characters < min_visible_characters
    ):
        raise ValueError(
            "Composition visible character count is below the required minimum: "
            f"{visible_characters} < {min_visible_characters}"
        )
    if (
        max_visible_characters is not None
        and visible_characters > max_visible_characters
    ):
        raise ValueError(
            "Composition visible character count exceeds the allowed maximum: "
            f"{visible_characters} > {max_visible_characters}"
        )
    output = Path(output_path).resolve()
    if not dry_run:
        atomic_save(document, output)
    return {
        "status": "DRY_RUN" if dry_run else "SUCCESS",
        "output": None if dry_run else str(output),
        "sections": len(sections),
        "subsections": subsection_count,
        "paragraphs": paragraph_count,
        "visible_characters": visible_characters,
        "citations": len(citation_numbers),
        "bibliography_entries": len(citation_numbers) if bibliography_heading else 0,
        "removed_placeholders": removed_placeholders,
    }
