from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.oxml import parse_xml
from docx.opc.packuri import PackURI
from docx.opc.part import Part
from lxml import etree

from .common import atomic_save
from .models import Fidelity, OperationResult


CUSTOM_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/custom-properties"
CUSTOM_CONTENT = "application/vnd.openxmlformats-officedocument.custom-properties+xml"
CUSTOM_NS = "http://schemas.openxmlformats.org/officeDocument/2006/custom-properties"
VT_NS = "http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"
FMTID = "{D5CDD505-2E9C-101B-9397-08002B2CF9AE}"


def _custom_part(document, create=False):
    for relationship in document.part.package.rels.values():
        if relationship.reltype == CUSTOM_REL:
            return relationship.target_part
    if not create:
        return None
    root = etree.Element(f"{{{CUSTOM_NS}}}Properties", nsmap={None: CUSTOM_NS, "vt": VT_NS})
    part = Part(PackURI("/docProps/custom.xml"), CUSTOM_CONTENT, etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True), document.part.package)
    document.part.package.relate_to(part, CUSTOM_REL)
    return part


def _read_custom(document):
    part = _custom_part(document)
    if part is None:
        return {}
    root = etree.fromstring(part.blob)
    result = {}
    for prop in root.findall(f"{{{CUSTOM_NS}}}property"):
        child = prop[0] if len(prop) else None
        if child is None:
            continue
        value = child.text or ""
        if child.tag == f"{{{VT_NS}}}i4":
            value = int(value)
        elif child.tag == f"{{{VT_NS}}}bool":
            value = value.lower() == "true"
        result[prop.get("name")] = value
    return result


def set_properties(input_path, *, output_path, custom=None, dry_run=False, **properties):
    document = Document(input_path)
    core = document.core_properties
    allowed = {"title", "subject", "author", "keywords", "category", "comments", "last_modified_by"}
    unknown = set(properties) - allowed
    if unknown:
        raise ValueError(f"Unsupported core properties: {sorted(unknown)}")
    for key, value in properties.items():
        setattr(core, key, value)
    if custom:
        part = _custom_part(document, create=True)
        root = etree.fromstring(part.blob)
        existing = {element.get("name"): element for element in root.findall(f"{{{CUSTOM_NS}}}property")}
        next_pid = max([int(element.get("pid")) for element in existing.values()], default=1) + 1
        for name, value in custom.items():
            if name in existing:
                root.remove(existing[name])
            prop = etree.SubElement(root, f"{{{CUSTOM_NS}}}property", fmtid=FMTID, pid=str(next_pid), name=str(name))
            next_pid += 1
            if isinstance(value, bool):
                child = etree.SubElement(prop, f"{{{VT_NS}}}bool")
                child.text = "true" if value else "false"
            elif isinstance(value, int):
                child = etree.SubElement(prop, f"{{{VT_NS}}}i4")
                child.text = str(value)
            else:
                child = etree.SubElement(prop, f"{{{VT_NS}}}lpwstr")
                child.text = str(value)
        part._blob = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
    output = Path(output_path).resolve()
    if not dry_run:
        atomic_save(document, output)
    return OperationResult.success("properties.set", "ooxml", Fidelity.HIGH, {"custom": list((custom or {}).keys())}, output_path=None if dry_run else output)


def get_properties(input_path):
    document = Document(input_path)
    core = document.core_properties
    return {
        "title": core.title,
        "subject": core.subject,
        "author": core.author,
        "keywords": core.keywords,
        "category": core.category,
        "comments": core.comments,
        "last_modified_by": core.last_modified_by,
        "custom": _read_custom(document),
    }

