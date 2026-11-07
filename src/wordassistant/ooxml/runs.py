"""Merge adjacent identically formatted runs in word/document.xml.

Word fragments paragraph text into many ``w:r`` elements (edit history, proofing
marks, revision identifiers). Coalescing identical neighbours makes text search
on the XML reliable and shrinks the file. Rendering stays the same. Only runs
that contain plain text (``w:rPr``, ``w:t``, or ``w:delText``) are merged, and
only when they are direct siblings with identical run properties. Runs in
different ``w:ins``/``w:del`` wrappers are never merged, so separate revisions
keep their identity.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from lxml import etree

from .package import OOXMLError, pack_directory, unpack_docx

WML_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"
_TEXT_TAGS = {f"{{{WML_NS}}}t", f"{{{WML_NS}}}delText"}
_ALLOWED_RUN_CHILDREN = _TEXT_TAGS | {f"{{{WML_NS}}}rPr"}
_RUN_TAG = f"{{{WML_NS}}}r"


def _is_plain_text_run(run: etree._Element) -> bool:
    for child in run:
        if child.tag not in _ALLOWED_RUN_CHILDREN:
            return False
    return True


def _run_props_key(run: etree._Element) -> bytes | None:
    props = run.find(f"{{{WML_NS}}}rPr")
    if props is None:
        return None
    return etree.tostring(props, method="c14n")


def _can_merge(first: etree._Element, second: etree._Element) -> bool:
    if first.getparent() is not second.getparent():
        return False
    if not (_is_plain_text_run(first) and _is_plain_text_run(second)):
        return False
    return _run_props_key(first) == _run_props_key(second)


def _consolidate_text(run: etree._Element) -> None:
    texts = [child for child in run if child.tag in _TEXT_TAGS]
    if len(texts) <= 1:
        return
    tag = texts[0].tag
    same_kind = [child for child in texts if child.tag == tag]
    if len(same_kind) != len(texts):
        return
    joined = "".join(child.text or "" for child in texts)
    keep = texts[0]
    keep.text = joined
    if joined != joined.strip():
        keep.set(XML_SPACE, "preserve")
    for child in texts[1:]:
        run.remove(child)


def _merge_sibling_runs(parent: etree._Element) -> int:
    merged = 0
    index = 0
    children = list(parent)
    while index < len(children):
        current = children[index]
        if current.tag != _RUN_TAG or not _is_plain_text_run(current):
            index += 1
            continue
        probe = index + 1
        while probe < len(children):
            nxt = children[probe]
            if nxt.tag != _RUN_TAG or not _can_merge(current, nxt):
                break
            for child in list(nxt):
                if child.tag != f"{{{WML_NS}}}rPr":
                    current.append(child)
            if nxt.tail:
                current.tail = (current.tail or "") + nxt.tail
            parent.remove(nxt)
            children.pop(probe)
            merged += 1
        _consolidate_text(current)
        index += 1
    return merged


def merge_runs_xml(root: etree._Element) -> dict[str, int]:
    """Merge runs in one document tree. Returns counts for the report."""
    proof_errors = root.findall(f".//{{{WML_NS}}}proofErr")
    for element in proof_errors:
        parent = element.getparent()
        if parent is not None:
            parent.remove(element)
    runs_before = len(root.findall(f".//{{{WML_NS}}}r"))
    merged = 0
    for parent in list(root.iter()):
        if parent.find(f"{{{WML_NS}}}r") is not None:
            merged += _merge_sibling_runs(parent)
    for run in root.iter(_RUN_TAG):
        for attribute in list(run.attrib):
            if "rsid" in attribute.lower():
                del run.attrib[attribute]
    runs_after = len(root.findall(f".//{{{WML_NS}}}r"))
    return {
        "runs_before": runs_before,
        "runs_after": runs_after,
        "runs_merged": merged,
        "proof_errors_removed": len(proof_errors),
    }


def merge_runs_docx(source: str | Path, output: str | Path) -> dict[str, Any]:
    """Write a copy of ``source`` with merged runs. The source is never modified."""
    src = Path(source)
    out = Path(output)
    if out.resolve() == src.resolve():
        raise OOXMLError("output must differ from the source; keep inputs unchanged")
    with tempfile.TemporaryDirectory(prefix="wa-merge-runs-") as work:
        unpacked = Path(work) / "pkg"
        unpack_docx(src, unpacked)
        document = unpacked / "word" / "document.xml"
        if not document.is_file():
            raise OOXMLError("word/document.xml is missing")
        tree = etree.parse(str(document))
        counts = merge_runs_xml(tree.getroot())
        tree.write(str(document), xml_declaration=True, encoding="UTF-8", standalone=True)
        packed = pack_directory(unpacked, out)
    return {"source": str(src), **counts, "output": packed["output"], "size_bytes": packed["size_bytes"]}
