from __future__ import annotations

from pathlib import Path
import re

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

from ..evidence.registry import EvidenceRegistry
from ..selectors import resolve_single_paragraph
from .common import atomic_save
from .models import Fidelity, OperationResult


_TAG_PREFIX = "wordassistant:citation:"


def _citation_elements(document):
    result = []
    for sdt in document.element.body.xpath(".//w:sdt"):
        properties = sdt.find(qn("w:sdtPr"))
        tag = properties.find(qn("w:tag")) if properties is not None else None
        if tag is not None and tag.get(qn("w:val"), "").startswith(_TAG_PREFIX):
            result.append(sdt)
    return result


def _citation_tag(element):
    properties = element.find(qn("w:sdtPr"))
    tag = properties.find(qn("w:tag")) if properties is not None else None
    return tag.get(qn("w:val"), "") if tag is not None else ""


def _citation_numbers(document):
    numbers = {}
    for element in _citation_elements(document):
        evidence_id = _citation_tag(element)[len(_TAG_PREFIX) :]
        if evidence_id not in numbers:
            numbers[evidence_id] = len(numbers) + 1
    return numbers


def _format_in_text(record, style, number):
    if record.get("synthetic") is True:
        return f"[SYNTHETIC-{number}]"
    normalized = style.lower()
    if normalized in {"numeric", "ieee", "numeric_brackets", "hcmunre_numeric"}:
        return f"[{number}]"
    author = record["authors"][0].split()[-1]
    if normalized in {"apa", "chicago"}:
        return f"({author}, {record['year']})"
    if normalized == "mla":
        return f"({author})"
    raise ValueError(f"Unsupported citation style: {style}")


def _format_bibliography(record, style, number):
    authors = ", ".join(record["authors"])
    marker = "[SYNTHETIC TEST DATA] " if record.get("synthetic") is True else ""
    normalized = style.lower()
    if normalized in {"numeric", "ieee", "numeric_brackets", "hcmunre_numeric"}:
        return f'[{number}] {marker}{authors}, "{record["title"]}," {record["year"]}. {record["url"]}'
    if normalized == "apa":
        return f"{marker}{authors}. ({record['year']}). {record['title']}. {record['url']}"
    if normalized == "mla":
        return f'{marker}{authors}. "{record["title"]}." {record["year"]}, {record["url"]}.'
    if normalized == "chicago":
        return f"{marker}{authors}. {record['title']}. {record['year']}. {record['url']}."
    raise ValueError(f"Unsupported bibliography style: {style}")


def insert_citation(
    input_path,
    *,
    output_path,
    evidence_registry,
    evidence_id,
    style="numeric",
    selector=None,
    dry_run=False,
):
    registry = EvidenceRegistry(evidence_registry)
    record = registry.get(evidence_id)
    document = Document(input_path)
    numbers = _citation_numbers(document)
    number = numbers.get(evidence_id, len(numbers) + 1)
    text = _format_in_text(record, style, number)
    paragraph = (
        document.add_paragraph()
        if selector is None
        else resolve_single_paragraph(document, selector)
    )
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
    if paragraph.text:
        paragraph.add_run(" ")
    paragraph._p.append(sdt)
    output = Path(output_path).resolve()
    if not dry_run:
        atomic_save(document, output)
    return OperationResult.success(
        "reference.cite",
        "ooxml",
        Fidelity.HIGH,
        {
            "evidence_id": evidence_id,
            "number": number,
            "style": style,
            "synthetic": record.get("synthetic") is True,
            "anchored": selector is not None,
        },
        output_path=None if dry_run else output,
    )


def list_citations(input_path):
    document = Document(input_path)
    result = []
    for index, element in enumerate(_citation_elements(document)):
        tag = _citation_tag(element)
        result.append(
            {
                "index": index,
                "evidence_id": tag[len(_TAG_PREFIX) :],
                "text": "".join(value.text or "" for value in element.iter(qn("w:t"))),
            }
        )
    return result


def remove_citation(input_path, *, output_path, citation_index: int, dry_run=False):
    document = Document(input_path)
    try:
        element = _citation_elements(document)[citation_index]
    except IndexError as exc:
        raise ValueError(f"Citation index out of range: {citation_index}") from exc
    element.getparent().remove(element)
    numbers = _citation_numbers(document)
    for remaining in _citation_elements(document):
        evidence_id = _citation_tag(remaining)[len(_TAG_PREFIX) :]
        number = numbers[evidence_id]
        text_nodes = list(remaining.iter(qn("w:t")))
        current = "".join(node.text or "" for node in text_nodes)
        if re.fullmatch(r"\[(?:SYNTHETIC-)?\d+\]", current.strip()) and text_nodes:
            prefix = "SYNTHETIC-" if "SYNTHETIC-" in current else ""
            text_nodes[0].text = f"[{prefix}{number}]"
            for node in text_nodes[1:]:
                node.text = ""
    output = Path(output_path).resolve()
    if not dry_run:
        atomic_save(document, output)
    return OperationResult.success("reference.remove", "ooxml", Fidelity.HIGH, {"citation_index": citation_index}, output_path=None if dry_run else output)


def _heading_level(paragraph) -> int | None:
    name = paragraph.style.name if paragraph.style is not None else ""
    if not name.startswith("Heading "):
        return 1 if name == "Title" else None
    try:
        return int(name.removeprefix("Heading ").strip())
    except ValueError:
        return None


def _replace_bibliography_content(document, heading: str, lines: list[str]):
    matches = [
        paragraph
        for paragraph in document.paragraphs
        if paragraph.text.strip().casefold() == heading.strip().casefold()
        and _heading_level(paragraph) is not None
    ]
    if len(matches) > 1:
        raise ValueError(
            f"Bibliography heading must be unique; found {len(matches)} exact matches for {heading!r}"
        )
    if matches:
        target = matches[0]
    else:
        target = document.add_heading(heading, level=1)

    target_level = _heading_level(target) or 1
    node = target._p.getnext()
    while node is not None:
        next_node = node.getnext()
        paragraph = next(
            (item for item in document.paragraphs if item._p is node), None
        )
        if paragraph is not None:
            level = _heading_level(paragraph)
            if level is not None and level <= target_level:
                break
            node.getparent().remove(node)
        node = next_node

    cursor = target._p
    for line in lines:
        paragraph = document.add_paragraph(line)
        cursor.addnext(paragraph._p)
        cursor = paragraph._p
    return target


def generate_bibliography(input_path, *, output_path, evidence_registry, style="IEEE", heading="REFERENCES", dry_run=False):
    document = Document(input_path)
    citations = list_citations(input_path)
    registry = EvidenceRegistry(evidence_registry)
    seen = set()
    lines = []
    for citation in citations:
        evidence_id = citation["evidence_id"]
        if evidence_id in seen:
            continue
        seen.add(evidence_id)
        lines.append(_format_bibliography(registry.get(evidence_id), style, len(lines) + 1))
    _replace_bibliography_content(document, heading, lines)
    output = Path(output_path).resolve()
    if not dry_run:
        atomic_save(document, output)
    return OperationResult.success("reference.bibliography", "python-docx", Fidelity.HIGH, {"entries": len(lines), "style": style, "heading": heading}, output_path=None if dry_run else output)
