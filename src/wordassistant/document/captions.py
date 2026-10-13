from __future__ import annotations

from pathlib import Path
import re

from docx import Document
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph


_LITERAL_CAPTION = re.compile(
    r"^\s*(?P<label>hình|figure|fig\.?|bảng|table|sơ\s*đồ|diagram|chart)"
    r"\s+\d+(?:[.:]\d+)*\s*[:.)–—-](?:\s+|$)",
    re.IGNORECASE,
)
_CAPTION_SEQUENCE_KINDS = {
    "caption": "generic",
    "figure": "figure",
    "fig": "figure",
    "hinh": "figure",
    "illustration": "figure",
    "diagram": "figure",
    "sodo": "figure",
    "chart": "figure",
    "bieudo": "figure",
    "table": "table",
    "bang": "table",
}
_LITERAL_KINDS = {
    "hình": "figure",
    "figure": "figure",
    "fig": "figure",
    "fig.": "figure",
    "bảng": "table",
    "table": "table",
    "sơ đồ": "figure",
    "diagram": "figure",
    "chart": "figure",
}


def _field_instructions(paragraph_element) -> list[str]:
    """Reassemble complex field instructions that Word split across runs."""
    instructions = []
    stack: list[dict] = []
    for element in paragraph_element.iter():
        if element.tag == qn("w:fldChar"):
            kind = element.get(qn("w:fldCharType"))
            if kind == "begin":
                stack.append({"begin": element, "parts": [], "separated": False})
            elif kind == "separate" and stack:
                stack[-1]["separated"] = True
            elif kind == "end" and stack:
                context = stack.pop()
                instruction = "".join(context["parts"]).strip()
                if instruction:
                    instructions.append(instruction)
        elif element.tag == qn("w:instrText") and stack and not stack[-1]["separated"]:
            stack[-1]["parts"].append(element.text or "")
        elif element.tag == qn("w:fldSimple"):
            instruction = (element.get(qn("w:instr")) or "").strip()
            if instruction:
                instructions.append(instruction)
    return instructions


def _paragraph_caption(paragraph_element, document) -> dict | None:
    paragraph = Paragraph(paragraph_element, document)
    style_name = paragraph.style.name if paragraph.style is not None else None
    style_id = paragraph.style.style_id if paragraph.style is not None else None
    text = paragraph.text.strip()
    sequence_ids = []
    sequence_kinds = []
    for instruction in _field_instructions(paragraph_element):
        match = re.match(r"^SEQ\s+([^\s\\]+)", instruction, re.IGNORECASE)
        if match:
            identifier = match.group(1)
            sequence_ids.append(identifier)
            sequence_kinds.append(
                _CAPTION_SEQUENCE_KINDS.get(identifier.casefold())
            )
    detected_by = []
    if (style_name and style_name.casefold() == "caption") or (
        style_id and style_id.casefold() == "caption"
    ):
        detected_by.append("caption_style")
    if any(kind is not None for kind in sequence_kinds):
        detected_by.append("seq_field")
    literal_match = _LITERAL_CAPTION.match(text)
    literal_kind = None
    if literal_match:
        detected_by.append("literal_label")
        literal_kind = _LITERAL_KINDS[literal_match.group("label").casefold()]
    if not detected_by:
        return None
    explicit_kinds = {
        kind for kind in sequence_kinds if kind in {"figure", "table"}
    }
    if literal_kind:
        explicit_kinds.add(literal_kind)
    caption_kind = (
        next(iter(explicit_kinds))
        if len(explicit_kinds) == 1
        else "conflict"
        if len(explicit_kinds) > 1
        else "generic"
    )
    return {
        "text": text,
        "style": style_name,
        "sequence_ids": list(dict.fromkeys(sequence_ids)),
        "detected_by": detected_by,
        "caption_kind": caption_kind,
        "is_empty": not bool(text),
    }


def _image_count(paragraph_element) -> int:
    drawing_images = sum(
        bool(drawing.xpath(".//a:blip"))
        for drawing in paragraph_element.xpath(".//w:drawing")
    )
    vml_images = len(paragraph_element.xpath(".//w:pict[.//v:imagedata]"))
    return drawing_images + vml_images


def _table_caption_metadata(table_element) -> str | None:
    properties = table_element.find(qn("w:tblPr"))
    if properties is None:
        return None
    caption = properties.find(qn("w:tblCaption"))
    return caption.get(qn("w:val")) if caption is not None else None


def audit_captions(path: str | Path) -> dict:
    """Report adjacent caption evidence for body-level images and top-level tables.

    This is read-only. It never infers caption text or changes the document.
    Only immediately adjacent body paragraphs with Caption style, a SEQ field,
    or a recognized literal figure/table label count as visible caption evidence.
    """
    source = Path(path).resolve()
    document = Document(source)
    children = list(document.element.body.iterchildren())
    captions = {
        index: caption
        for index, child in enumerate(children)
        if child.tag == qn("w:p")
        and (caption := _paragraph_caption(child, document)) is not None
    }

    candidates = []
    figure_index = 0
    table_index = 0
    for index, child in enumerate(children):
        if child.tag == qn("w:p"):
            count = _image_count(child)
            if not count:
                continue
            candidates.append(
                {
                    "kind": "figure",
                    "index": figure_index,
                    "body_child_index": index,
                    "image_count": count,
                    "paragraph_text": "".join(
                        node.text or "" for node in child.iter(qn("w:t"))
                    ).strip(),
                    "caption_metadata": None,
                }
            )
            figure_index += 1
        elif child.tag == qn("w:tbl"):
            candidates.append(
                {
                    "kind": "table",
                    "index": table_index,
                    "body_child_index": index,
                    "image_count": None,
                    "paragraph_text": None,
                    "caption_metadata": _table_caption_metadata(child),
                }
            )
            table_index += 1

    caption_usage: dict[int, int] = {}
    for candidate in candidates:
        index = candidate["body_child_index"]
        adjacent = []
        for neighbor in (index - 1, index + 1):
            if neighbor in captions:
                adjacent.append(neighbor)
        compatible = [
            neighbor
            for neighbor in adjacent
            if captions[neighbor]["caption_kind"]
            in {"generic", candidate["kind"]}
        ]
        incompatible = [neighbor for neighbor in adjacent if neighbor not in compatible]
        for neighbor in compatible:
            caption_usage[neighbor] = caption_usage.get(neighbor, 0) + 1
        candidate["caption_paragraph_indexes"] = adjacent
        candidate["compatible_caption_indexes"] = compatible
        candidate["incompatible_caption_indexes"] = incompatible

    figures = []
    tables = []
    issues = []
    for candidate in candidates:
        adjacent = candidate.pop("caption_paragraph_indexes")
        compatible_indexes = candidate.pop("compatible_caption_indexes")
        incompatible_indexes = candidate.pop("incompatible_caption_indexes")
        adjacent_captions = [
            {"body_child_index": index, **captions[index]}
            for index in adjacent
        ]
        matched = [
            caption
            for caption in adjacent_captions
            if caption["body_child_index"] in compatible_indexes
        ]
        mismatched = [
            caption
            for caption in adjacent_captions
            if caption["body_child_index"] in incompatible_indexes
        ]
        if len(matched) > 1 or any(
            caption_usage[caption["body_child_index"]] > 1 for caption in matched
        ):
            status = "AMBIGUOUS"
        elif matched and matched[0]["is_empty"]:
            status = "EMPTY"
        elif matched:
            status = "PRESENT"
        elif mismatched:
            status = "TYPE_MISMATCH"
        elif candidate["caption_metadata"]:
            status = "METADATA_ONLY"
        else:
            status = "MISSING"
        item = {
            **candidate,
            "caption_status": status,
            "captions": matched,
            "adjacent_captions": adjacent_captions,
            "mismatched_captions": mismatched,
        }
        (figures if candidate["kind"] == "figure" else tables).append(item)
        if status in {"MISSING", "EMPTY", "AMBIGUOUS", "METADATA_ONLY"}:
            issues.append(
                {
                    "severity": "WARNING",
                    "code": f"caption_{status.casefold()}",
                    "object_kind": candidate["kind"],
                    "object_index": candidate["index"],
                    "message": {
                        "MISSING": "No immediately adjacent visible caption evidence was found.",
                        "EMPTY": "An adjacent caption paragraph has no visible text.",
                        "AMBIGUOUS": "More than one adjacent caption may refer to this object, or one caption is shared by multiple objects.",
                        "METADATA_ONLY": "Table caption metadata exists, but no adjacent visible caption paragraph was found.",
                    }[status],
                }
            )
        if mismatched:
            issues.append(
                {
                    "severity": "WARNING",
                    "code": "caption_type_mismatch",
                    "object_kind": candidate["kind"],
                    "object_index": candidate["index"],
                    "caption_paragraph_indexes": [
                        caption["body_child_index"] for caption in mismatched
                    ],
                    "message": "An adjacent caption has an explicit type that does not match this object.",
                }
            )

    def counts(items):
        return {
            "total": len(items),
            "present": sum(item["caption_status"] == "PRESENT" for item in items),
            "missing": sum(item["caption_status"] == "MISSING" for item in items),
            "empty": sum(item["caption_status"] == "EMPTY" for item in items),
            "ambiguous": sum(item["caption_status"] == "AMBIGUOUS" for item in items),
            "type_mismatch": sum(
                bool(item["mismatched_captions"]) for item in items
            ),
            "metadata_only": sum(item["caption_status"] == "METADATA_ONLY" for item in items),
        }

    return {
        "version": 1,
        "file": str(source),
        "status": "REVIEW_REQUIRED" if issues else "PASS",
        "scope": {
            "figures": "images in direct body paragraphs, grouped by paragraph",
            "tables": "top-level body tables",
            "visible_caption_rule": "immediately adjacent body paragraph detected by Caption style, SEQ field, or common Vietnamese/English literal label; explicit figure/table types must match the object",
            "excludes": ["headers and footers", "images inside tables", "nested tables", "objects inside content controls or custom XML wrappers"],
            "mutates_document": False,
            "infers_caption_text": False,
        },
        "summary": {"figures": counts(figures), "tables": counts(tables)},
        "figures": figures,
        "tables": tables,
        "issues": issues,
    }
