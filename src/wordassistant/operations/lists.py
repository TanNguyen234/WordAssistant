from __future__ import annotations

from pathlib import Path
import re
from typing import Sequence

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

from .common import atomic_save
from .models import Fidelity, OperationResult


_FORMAT_TEXT = {
    "decimal": "%1.",
    "lowerLetter": "%1)",
    "upperLetter": "%1)",
    "lowerRoman": "%1.",
    "upperRoman": "%1.",
    "bullet": "•",
}

_LITERAL_HEADING_PREFIX = re.compile(r"^\s*\d+(?:\.\d+)*[.)]?\s+")


def _next_id(elements, attribute: str) -> int:
    values = []
    key = qn(attribute)
    for element in elements:
        value = element.get(key)
        if value is not None and value.isdigit():
            values.append(int(value))
    return max(values, default=0) + 1


def _append_level(abstract, level: int, number_format: str, start: int = 1):
    lvl = OxmlElement("w:lvl")
    lvl.set(qn("w:ilvl"), str(level))
    start_element = OxmlElement("w:start")
    start_element.set(qn("w:val"), str(start))
    lvl.append(start_element)
    num_fmt = OxmlElement("w:numFmt")
    num_fmt.set(qn("w:val"), number_format)
    lvl.append(num_fmt)
    text = OxmlElement("w:lvlText")
    text.set(
        qn("w:val"),
        _FORMAT_TEXT.get(number_format, f"%{level + 1}.").replace("%1", f"%{level + 1}"),
    )
    lvl.append(text)
    justification = OxmlElement("w:lvlJc")
    justification.set(qn("w:val"), "left")
    lvl.append(justification)
    ppr = OxmlElement("w:pPr")
    tabs = OxmlElement("w:tabs")
    tab = OxmlElement("w:tab")
    tab.set(qn("w:val"), "num")
    tab.set(qn("w:pos"), str(720 * (level + 1)))
    tabs.append(tab)
    indent = OxmlElement("w:ind")
    indent.set(qn("w:left"), str(720 * (level + 1)))
    indent.set(qn("w:hanging"), "360")
    ppr.extend([tabs, indent])
    lvl.append(ppr)
    abstract.append(lvl)


def _create_numbering_definition(document, formats: Sequence[str]) -> int:
    numbering = document.part.numbering_part.element
    abstract_id = _next_id(numbering.findall(qn("w:abstractNum")), "w:abstractNumId")
    abstract = OxmlElement("w:abstractNum")
    abstract.set(qn("w:abstractNumId"), str(abstract_id))
    multi = OxmlElement("w:multiLevelType")
    multi.set(qn("w:val"), "multilevel")
    abstract.append(multi)
    normalized = list(formats) or ["decimal"]
    for level in range(9):
        _append_level(abstract, level, normalized[min(level, len(normalized) - 1)])
    numbering.append(abstract)

    num_id = _next_id(numbering.findall(qn("w:num")), "w:numId")
    num = OxmlElement("w:num")
    num.set(qn("w:numId"), str(num_id))
    abstract_ref = OxmlElement("w:abstractNumId")
    abstract_ref.set(qn("w:val"), str(abstract_id))
    num.append(abstract_ref)
    numbering.append(num)
    return num_id


def _remove_heading_numbering(document) -> list[int]:
    numbering = document.part.numbering_part.element
    abstract_ids = []
    for abstract in list(numbering.findall(qn("w:abstractNum"))):
        linked = [
            level.find(qn("w:pStyle"))
            for level in abstract.findall(qn("w:lvl"))
        ]
        if any(
            item is not None
            and (item.get(qn("w:val")) or "").startswith("Heading")
            for item in linked
        ):
            abstract_ids.append(int(abstract.get(qn("w:abstractNumId"))))
            numbering.remove(abstract)

    num_ids = []
    for num in list(numbering.findall(qn("w:num"))):
        reference = num.find(qn("w:abstractNumId"))
        if reference is not None and int(reference.get(qn("w:val"))) in abstract_ids:
            num_ids.append(int(num.get(qn("w:numId"))))
            numbering.remove(num)

    for level in range(1, 10):
        style = document.styles[f"Heading {level}"]
        p_pr = style.element.pPr
        num_pr = p_pr.find(qn("w:numPr")) if p_pr is not None else None
        if num_pr is not None:
            num_id = num_pr.find(qn("w:numId"))
            if num_id is not None and int(num_id.get(qn("w:val"))) in num_ids:
                p_pr.remove(num_pr)
    for paragraph in document.paragraphs:
        p_pr = paragraph._p.pPr
        num_pr = p_pr.find(qn("w:numPr")) if p_pr is not None else None
        if num_pr is not None:
            num_id = num_pr.find(qn("w:numId"))
            if num_id is not None and int(num_id.get(qn("w:val"))) in num_ids:
                p_pr.remove(num_pr)
    return num_ids


def _create_heading_numbering_definition(
    document,
    levels: int,
    *,
    link_heading_styles: bool = True,
    suppress_first_level_label: bool = False,
) -> int:
    numbering = document.part.numbering_part.element
    abstract_id = _next_id(
        numbering.findall(qn("w:abstractNum")), "w:abstractNumId"
    )
    abstract = OxmlElement("w:abstractNum")
    abstract.set(qn("w:abstractNumId"), str(abstract_id))
    multi = OxmlElement("w:multiLevelType")
    multi.set(qn("w:val"), "multilevel")
    abstract.append(multi)
    for level in range(levels):
        lvl = OxmlElement("w:lvl")
        lvl.set(qn("w:ilvl"), str(level))
        start = OxmlElement("w:start")
        start.set(qn("w:val"), "1")
        num_fmt = OxmlElement("w:numFmt")
        num_fmt.set(qn("w:val"), "decimal")
        p_style = None
        if link_heading_styles:
            p_style = OxmlElement("w:pStyle")
            p_style.set(qn("w:val"), document.styles[f"Heading {level + 1}"].style_id)
        lvl_text = OxmlElement("w:lvlText")
        level_text = ".".join(f"%{index}" for index in range(1, level + 2))
        if level == 0 and suppress_first_level_label:
            level_text = ""
        lvl_text.set(qn("w:val"), level_text)
        suffix = OxmlElement("w:suff")
        suffix.set(qn("w:val"), "tab")
        justification = OxmlElement("w:lvlJc")
        justification.set(qn("w:val"), "left")
        p_pr = OxmlElement("w:pPr")
        tabs = OxmlElement("w:tabs")
        tab = OxmlElement("w:tab")
        tab.set(qn("w:val"), "num")
        tab.set(qn("w:pos"), str(720 * (level + 1)))
        tabs.append(tab)
        indent = OxmlElement("w:ind")
        indent.set(qn("w:left"), str(720 * (level + 1)))
        indent.set(qn("w:hanging"), "360")
        p_pr.extend([tabs, indent])
        lvl.extend([start, num_fmt])
        # CT_Lvl is sequence-sensitive. Word repairs out-of-order children by
        # replacing affected levels with numFmt=none, which looks valid in XML
        # but produces an empty ListString after a native round-trip.
        # Omitted lvlRestart intentionally uses Word's standard behavior: each
        # level restarts when its immediately preceding level is used.
        if p_style is not None:
            lvl.append(p_style)
        lvl.extend([suffix, lvl_text, justification, p_pr])
        abstract.append(lvl)
    numbering.append(abstract)

    num_id = _next_id(numbering.findall(qn("w:num")), "w:numId")
    num = OxmlElement("w:num")
    num.set(qn("w:numId"), str(num_id))
    abstract_ref = OxmlElement("w:abstractNumId")
    abstract_ref.set(qn("w:val"), str(abstract_id))
    num.append(abstract_ref)
    numbering.append(num)
    return num_id


def apply_heading_numbering(
    input_path: str | Path,
    *,
    output_path: str | Path,
    levels: int = 9,
    allow_literal_prefixes: bool = False,
    suppress_first_level_label: bool = False,
    start_text: str | None = None,
    end_text: str | None = None,
    dry_run: bool = False,
) -> OperationResult:
    if levels < 1 or levels > 9:
        raise ValueError("levels must be between 1 and 9")
    if end_text and not start_text:
        raise ValueError("end_text requires start_text")
    document = Document(input_path)
    heading_paragraphs = [
        (index, paragraph)
        for index, paragraph in enumerate(document.paragraphs)
        if paragraph.style is not None
        and paragraph.style.style_id.startswith("Heading")
    ]
    scoped_headings = heading_paragraphs
    scope = None
    if start_text:
        start_matches = [
            (index, paragraph)
            for index, paragraph in heading_paragraphs
            if paragraph.text.strip().casefold().startswith(start_text.strip().casefold())
        ]
        if len(start_matches) != 1:
            raise ValueError(
                f"start_text must match exactly one heading prefix; found {len(start_matches)}"
            )
        start_index = start_matches[0][0]
        end_index = len(document.paragraphs)
        if end_text:
            end_matches = [
                (index, paragraph)
                for index, paragraph in heading_paragraphs
                if index > start_index
                and paragraph.text.strip().casefold().startswith(end_text.strip().casefold())
            ]
            if len(end_matches) != 1:
                raise ValueError(
                    f"end_text must match exactly one later heading prefix; found {len(end_matches)}"
                )
            end_index = end_matches[0][0]
        scoped_headings = [
            (index, paragraph)
            for index, paragraph in heading_paragraphs
            if start_index <= index < end_index
        ]
        if not scoped_headings:
            raise ValueError("Heading numbering scope contains no headings")
        scope = {
            "start_text": start_text,
            "end_text": end_text,
            "start_paragraph_index": start_index,
            "end_paragraph_index": None
            if end_index == len(document.paragraphs)
            else end_index,
        }
    literal = [
        {"paragraph_index": index, "text": paragraph.text}
        for index, paragraph in scoped_headings
        if _LITERAL_HEADING_PREFIX.match(paragraph.text)
    ]
    if literal and not allow_literal_prefixes:
        raise ValueError(
            "Heading text contains a literal numbering prefix; remove it before "
            "applying automatic heading numbering"
        )
    _remove_heading_numbering(document)
    scoped = start_text is not None
    num_id = _create_heading_numbering_definition(
        document,
        levels,
        link_heading_styles=not scoped,
        suppress_first_level_label=suppress_first_level_label,
    )
    if scoped:
        for _, paragraph in scoped_headings:
            style_id = paragraph.style.style_id
            try:
                level = int(style_id.removeprefix("Heading")) - 1
            except ValueError:
                continue
            if 0 <= level < levels:
                _assign_numbering(paragraph, num_id, level)
    else:
        for level in range(levels):
            style = document.styles[f"Heading {level + 1}"]
            p_pr = style.element.get_or_add_pPr()
            existing = p_pr.find(qn("w:numPr"))
            if existing is not None:
                p_pr.remove(existing)
            num_pr = OxmlElement("w:numPr")
            ilvl = OxmlElement("w:ilvl")
            ilvl.set(qn("w:val"), str(level))
            num = OxmlElement("w:numId")
            num.set(qn("w:val"), str(num_id))
            num_pr.extend([ilvl, num])
            p_pr.append(num_pr)
    output = Path(output_path).resolve()
    if not dry_run:
        atomic_save(document, output)
    return OperationResult.success(
        "heading.numbering_apply",
        "ooxml",
        Fidelity.HIGH,
        {
            "levels": levels,
            "num_id": num_id,
            "literal_prefixes": literal,
            "suppress_first_level_label": suppress_first_level_label,
            "scope": scope,
            "numbered_heading_count": len(scoped_headings),
        },
        output_path=None if dry_run else output,
    )


def inspect_heading_numbering(input_path: str | Path) -> dict:
    document = Document(input_path)
    numbering = document.part.numbering_part.element
    linked_levels = []
    for abstract in numbering.findall(qn("w:abstractNum")):
        for level in abstract.findall(qn("w:lvl")):
            p_style = level.find(qn("w:pStyle"))
            if p_style is not None:
                value = p_style.get(qn("w:val"))
                if value and value.startswith("Heading"):
                    linked_levels.append(value)
    headings = [
        (index, paragraph)
        for index, paragraph in enumerate(document.paragraphs)
        if paragraph.style is not None
        and paragraph.style.style_id.startswith("Heading")
    ]
    return {
        "linked_levels": linked_levels,
        "heading_paragraphs": len(headings),
        "literal_prefixes": [
            {"paragraph_index": index, "text": paragraph.text}
            for index, paragraph in headings
            if _LITERAL_HEADING_PREFIX.match(paragraph.text)
        ],
    }


def remove_heading_numbering(
    input_path: str | Path,
    *,
    output_path: str | Path,
    dry_run: bool = False,
) -> OperationResult:
    document = Document(input_path)
    removed = _remove_heading_numbering(document)
    output = Path(output_path).resolve()
    if not dry_run:
        atomic_save(document, output)
    return OperationResult.success(
        "heading.numbering_remove",
        "ooxml",
        Fidelity.HIGH,
        {"removed_num_ids": removed},
        output_path=None if dry_run else output,
    )


def _assign_numbering(paragraph, num_id: int, level: int):
    ppr = paragraph._p.get_or_add_pPr()
    existing = ppr.find(qn("w:numPr"))
    if existing is not None:
        ppr.remove(existing)
    num_pr = OxmlElement("w:numPr")
    ilvl = OxmlElement("w:ilvl")
    ilvl.set(qn("w:val"), str(level))
    num = OxmlElement("w:numId")
    num.set(qn("w:val"), str(num_id))
    num_pr.extend([ilvl, num])
    ppr.append(num_pr)


def create_list(
    input_path: str | Path,
    *,
    output_path: str | Path,
    items: Sequence[str],
    kind: str = "bullet",
    levels: Sequence[int] | None = None,
    formats: Sequence[str] | None = None,
    start: int = 1,
    dry_run: bool = False,
) -> OperationResult:
    if kind not in {"bullet", "numbered"}:
        raise ValueError("kind must be bullet or numbered")
    if not items:
        raise ValueError("items must not be empty")
    item_levels = list(levels or [0] * len(items))
    if len(item_levels) != len(items) or any(level < 0 or level > 8 for level in item_levels):
        raise ValueError("levels must contain one value from 0 through 8 per item")
    number_formats = list(formats or (["bullet"] if kind == "bullet" else ["decimal"]))
    document = Document(input_path)
    num_id = _create_numbering_definition(document, number_formats)
    paragraphs = []
    for item, level in zip(items, item_levels):
        paragraph = document.add_paragraph(str(item))
        _assign_numbering(paragraph, num_id, level)
        paragraphs.append(paragraph)
    if start != 1:
        _restart(document, paragraphs[0], start)
    output = Path(output_path).resolve()
    if not dry_run:
        atomic_save(document, output)
    return OperationResult(
        "DRY_RUN" if dry_run else "SUCCESS",
        "list.create",
        "ooxml",
        Fidelity.HIGH,
        None if dry_run else output,
        data={"items": len(items), "num_id": num_id},
    )


def set_list_level(input_path, *, output_path, paragraph_index: int, level: int, dry_run=False):
    if level < 0 or level > 8:
        raise ValueError("level must be between 0 and 8")
    document = Document(input_path)
    paragraph = document.paragraphs[paragraph_index]
    num_pr = paragraph._p.pPr.numPr if paragraph._p.pPr is not None else None
    if num_pr is None or num_pr.numId is None:
        raise ValueError("Selected paragraph is not a numbered list item")
    _assign_numbering(paragraph, int(num_pr.numId.val), level)
    if not dry_run:
        atomic_save(document, output_path)
    return OperationResult.success("list.set_level", "ooxml", Fidelity.HIGH, {"level": level}, output_path=None if dry_run else output_path)


def _restart(document, paragraph, start: int) -> int:
    num_pr = paragraph._p.pPr.numPr if paragraph._p.pPr is not None else None
    if num_pr is None or num_pr.numId is None:
        raise ValueError("Selected paragraph is not a numbered list item")
    old_id = int(num_pr.numId.val)
    level = int(num_pr.ilvl.val) if num_pr.ilvl is not None else 0
    numbering = document.part.numbering_part.element
    old_num = next(
        (element for element in numbering.findall(qn("w:num")) if int(element.get(qn("w:numId"))) == old_id),
        None,
    )
    if old_num is None:
        raise ValueError(f"Numbering instance not found: {old_id}")
    abstract_ref = old_num.find(qn("w:abstractNumId"))
    abstract_id = abstract_ref.get(qn("w:val"))
    new_id = _next_id(numbering.findall(qn("w:num")), "w:numId")
    new_num = OxmlElement("w:num")
    new_num.set(qn("w:numId"), str(new_id))
    new_abstract_ref = OxmlElement("w:abstractNumId")
    new_abstract_ref.set(qn("w:val"), str(abstract_id))
    override = OxmlElement("w:lvlOverride")
    override.set(qn("w:ilvl"), str(level))
    start_override = OxmlElement("w:startOverride")
    start_override.set(qn("w:val"), str(start))
    override.append(start_override)
    new_num.extend([new_abstract_ref, override])
    numbering.append(new_num)
    _assign_numbering(paragraph, new_id, level)
    return new_id


def restart_numbering(input_path, *, output_path, paragraph_index: int, start: int = 1, dry_run=False):
    if start < 0:
        raise ValueError("start must be non-negative")
    document = Document(input_path)
    new_id = _restart(document, document.paragraphs[paragraph_index], start)
    if not dry_run:
        atomic_save(document, output_path)
    return OperationResult.success("list.restart", "ooxml", Fidelity.HIGH, {"start": start, "num_id": new_id}, output_path=None if dry_run else output_path)


def continue_numbering(input_path, *, output_path, paragraph_index: int, source_paragraph_index: int, dry_run=False):
    document = Document(input_path)
    source = document.paragraphs[source_paragraph_index]
    source_num = source._p.pPr.numPr if source._p.pPr is not None else None
    if source_num is None or source_num.numId is None:
        raise ValueError("Source paragraph is not numbered")
    target = document.paragraphs[paragraph_index]
    level = int(target._p.pPr.numPr.ilvl.val) if target._p.pPr is not None and target._p.pPr.numPr is not None and target._p.pPr.numPr.ilvl is not None else 0
    _assign_numbering(target, int(source_num.numId.val), level)
    if not dry_run:
        atomic_save(document, output_path)
    return OperationResult.success("list.continue", "ooxml", Fidelity.HIGH, {"num_id": int(source_num.numId.val)}, output_path=None if dry_run else output_path)
