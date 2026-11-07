"""Accept tracked changes at the XML level, without Word or LibreOffice.

Accepting keeps inserted content, removes deleted content, joins paragraphs whose
paragraph mark was deleted, and drops recorded property changes. The steps follow
the Word semantics for ``w:ins``, ``w:del``, ``w:moveFrom``, ``w:moveTo`` and
the ``*PrChange`` family. Unsupported cell-level revisions are counted and
reported instead of being guessed at.
"""

from __future__ import annotations

import re
import tempfile
from pathlib import Path
from typing import Any

from lxml import etree

from .package import OOXMLError, pack_directory, unpack_docx

WML_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_W = f"{{{WML_NS}}}"
PROPERTY_CHANGE_TAGS = (
    "rPrChange",
    "pPrChange",
    "sectPrChange",
    "tblPrChange",
    "trPrChange",
    "tcPrChange",
    "tblGridChange",
    "numberingChange",
)
UNSUPPORTED_TAGS = ("cellIns", "cellDel", "customXmlInsRangeStart", "customXmlDelRangeStart")
_PART_RE = re.compile(r"^word/(document|header\d*|footer\d*|footnotes|endnotes)\.xml$")


def _unwrap(element: etree._Element) -> None:
    """Replace a wrapper element by its children, keeping order and tail text."""
    parent = element.getparent()
    if parent is None:
        return
    children = list(element)
    previous = element.getprevious()
    index = parent.index(element)
    tail = element.tail
    for offset, child in enumerate(children):
        parent.insert(index + offset, child)
    if tail:
        if children:
            children[-1].tail = (children[-1].tail or "") + tail
        elif previous is not None:
            previous.tail = (previous.tail or "") + tail
        else:
            parent.text = (parent.text or "") + tail
    parent.remove(element)


def _remove_keeping_tail(element: etree._Element) -> None:
    parent = element.getparent()
    if parent is None:
        return
    tail = element.tail
    if tail:
        previous = element.getprevious()
        if previous is not None:
            previous.tail = (previous.tail or "") + tail
        else:
            parent.text = (parent.text or "") + tail
    parent.remove(element)


def _is_paragraph_mark(element: etree._Element) -> bool:
    parent = element.getparent()
    return parent is not None and parent.tag == _W + "rPr"


def _join_into_next_paragraph(paragraph: etree._Element) -> bool:
    nxt = paragraph.getnext()
    while nxt is not None and nxt.tag != _W + "p":
        nxt = nxt.getnext()
    if nxt is None:
        return False
    properties = paragraph.find(_W + "pPr")
    if properties is not None:
        mark = properties.find(_W + "rPr")
        if mark is not None:
            for node in mark.findall(_W + "del"):
                mark.remove(node)
    content = [child for child in paragraph if child.tag != _W + "pPr"]
    target_props = nxt.find(_W + "pPr")
    insert_at = 1 if target_props is not None else 0
    for offset, child in enumerate(content):
        nxt.insert(insert_at + offset, child)
    _remove_keeping_tail(paragraph)
    return True


def accept_changes_xml(root: etree._Element) -> dict[str, int]:
    counts = {
        "insertions_accepted": 0,
        "deletions_removed": 0,
        "paragraph_marks_joined": 0,
        "property_changes_removed": 0,
        "unsupported_revisions": 0,
    }
    for tag in UNSUPPORTED_TAGS:
        counts["unsupported_revisions"] += len(root.findall(f".//{_W}{tag}"))

    marked = [p for p in root.iter(_W + "p") if p.find(f"{_W}pPr/{_W}rPr/{_W}del") is not None]
    for paragraph in marked:
        if paragraph.getparent() is None:
            continue
        if _join_into_next_paragraph(paragraph):
            counts["paragraph_marks_joined"] += 1
        else:
            for node in paragraph.findall(f"{_W}pPr/{_W}rPr/{_W}del"):
                _remove_keeping_tail(node)

    for node in list(root.iter(_W + "del")):
        if node.getparent() is None or _is_paragraph_mark(node):
            continue
        _remove_keeping_tail(node)
        counts["deletions_removed"] += 1

    for node in list(root.iter(_W + "moveFrom")):
        if node.getparent() is None:
            continue
        _remove_keeping_tail(node)
        counts["deletions_removed"] += 1

    for node in list(root.iter(_W + "ins")):
        if node.getparent() is None:
            continue
        if _is_paragraph_mark(node):
            _remove_keeping_tail(node)
        else:
            _unwrap(node)
        counts["insertions_accepted"] += 1

    for node in list(root.iter(_W + "moveTo")):
        if node.getparent() is None:
            continue
        _unwrap(node)
        counts["insertions_accepted"] += 1

    for tag in PROPERTY_CHANGE_TAGS:
        for node in list(root.iter(_W + tag)):
            if node.getparent() is None:
                continue
            _remove_keeping_tail(node)
            counts["property_changes_removed"] += 1
    return counts


def accept_changes_docx(source: str | Path, output: str | Path) -> dict[str, Any]:
    """Write a copy of ``source`` with tracked changes accepted."""
    src = Path(source)
    out = Path(output)
    if out.resolve() == src.resolve():
        raise OOXMLError("output must differ from the source; keep inputs unchanged")
    totals = {
        "insertions_accepted": 0,
        "deletions_removed": 0,
        "paragraph_marks_joined": 0,
        "property_changes_removed": 0,
        "unsupported_revisions": 0,
    }
    parts_touched: list[str] = []
    with tempfile.TemporaryDirectory(prefix="wa-accept-changes-") as work:
        unpacked = Path(work) / "pkg"
        unpack_docx(src, unpacked)
        for part in sorted(unpacked.rglob("*.xml")):
            relative = part.relative_to(unpacked).as_posix()
            if not _PART_RE.match(relative):
                continue
            tree = etree.parse(str(part))
            counts = accept_changes_xml(tree.getroot())
            if any(counts.values()):
                parts_touched.append(relative)
                tree.write(str(part), xml_declaration=True, encoding="UTF-8", standalone=True)
            for key, value in counts.items():
                totals[key] += value
        packed = pack_directory(unpacked, out)
    return {
        "source": str(src),
        **totals,
        "parts_touched": parts_touched,
        "output": packed["output"],
        "size_bytes": packed["size_bytes"],
    }
