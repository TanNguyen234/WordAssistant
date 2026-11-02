from pathlib import Path
import argparse
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def ensure_flag(parent, tag, value=None):
    element = parent.find(qn(tag))
    if element is None:
        element = OxmlElement(tag)
        parent.append(element)
    if value is not None:
        element.set(qn("w:val"), value)
    return element

def set_numbering_suffix(level, value):
    suffix = level.find(qn("w:suff"))
    if suffix is None:
        suffix = OxmlElement("w:suff")
        text = level.find(qn("w:lvlText"))
        level.insert(level.index(text) if text is not None else len(level), suffix)
    suffix.set(qn("w:val"), value)

def set_numbering_indent(level, left, hanging):
    p_pr = level.find(qn("w:pPr"))
    if p_pr is None:
        p_pr = OxmlElement("w:pPr")
        level.append(p_pr)
    tabs = p_pr.find(qn("w:tabs"))
    if tabs is not None:
        p_pr.remove(tabs)
    indent = p_pr.find(qn("w:ind"))
    if indent is None:
        indent = OxmlElement("w:ind")
        p_pr.append(indent)
    indent.set(qn("w:left"), str(left))
    indent.set(qn("w:hanging"), str(hanging))

def format_heading_numbering(doc):
    numbered_ids = set()
    for paragraph in doc.paragraphs:
        if paragraph.style is None or paragraph.style.name not in {"Heading 1", "Heading 2"}:
            continue
        properties = paragraph._p.pPr
        num_pr = properties.find(qn("w:numPr")) if properties is not None else None
        num_id = num_pr.find(qn("w:numId")) if num_pr is not None else None
        if num_id is not None:
            numbered_ids.add(num_id.get(qn("w:val")))
    numbering = doc.part.numbering_part.element
    for num in numbering.findall(qn("w:num")):
        if num.get(qn("w:numId")) not in numbered_ids:
            continue
        abstract_ref = num.find(qn("w:abstractNumId"))
        if abstract_ref is None:
            continue
        abstract_id = abstract_ref.get(qn("w:val"))
        for abstract in numbering.findall(qn("w:abstractNum")):
            if abstract.get(qn("w:abstractNumId")) != abstract_id:
                continue
            for level in abstract.findall(qn("w:lvl")):
                index = int(level.get(qn("w:ilvl"), "0"))
                if index == 0:
                    set_numbering_suffix(level, "nothing")
                    set_numbering_indent(level, 0, 0)
                elif index == 1:
                    set_numbering_suffix(level, "space")
                    set_numbering_indent(level, 360, 360)

def format_tables(source: Path, output: Path) -> int:
    doc = Document(source)
    format_heading_numbering(doc)
    for table in doc.tables:
        for row_index, row in enumerate(table.rows):
            tr_pr = row._tr.get_or_add_trPr()
            ensure_flag(tr_pr, "w:cantSplit")
            if row_index == 0:
                ensure_flag(tr_pr, "w:tblHeader", "true")
            for cell in row.cells:
                cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP
                for paragraph in cell.paragraphs:
                    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
                    if row_index == 0:
                        for run in paragraph.runs:
                            run.bold = True
    doc.save(output)
    return len(doc.tables)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    count = format_tables(args.input, args.output)
    print(f"formatted_tables={count} output={args.output.resolve()}")
