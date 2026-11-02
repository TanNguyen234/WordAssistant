"""Apply a hash-bound table grid plan without changing document text or fields."""
import argparse
import hashlib
import json
from pathlib import Path
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import Cm
from docx.text.paragraph import Paragraph


def snapshot(doc):
    return ([p.text for p in doc.paragraphs],
            [[[c.text for c in r.cells] for r in t.rows] for t in doc.tables],
            doc.element.body.xpath('.//w:instrText/text()'))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('input', type=Path)
    ap.add_argument('plan', type=Path)
    ap.add_argument('output', type=Path)
    args = ap.parse_args()
    plan = json.loads(args.plan.read_text(encoding='utf-8'))
    if hashlib.sha256(args.input.read_bytes()).hexdigest() != plan['input_sha256']:
        raise ValueError('Input hash changed')
    if args.output.exists() or args.input.resolve() == args.output.resolve():
        raise ValueError('Use a distinct new output')
    doc = Document(args.input)
    before = snapshot(doc)
    for item in plan['tables']:
        table = doc.tables[item['index']]
        if [c.text for c in table.rows[0].cells] != item['headers']:
            raise ValueError('Table header changed')
        widths = [Cm(v) for v in item['widths_cm']]
        if len(widths) != len(table.columns) or abs(sum(item['widths_cm']) - 16) > .001:
            raise ValueError('Unexpected table geometry')
        table.autofit = False
        table._tbl.tblPr.find(qn('w:tblW')).set(qn('w:w'), str(sum(v.twips for v in widths)))
        for col, width in zip(table.columns, widths):
            col.width = width
        for row in table.rows:
            for cell, width in zip(row.cells, widths):
                if cell._tc.tcPr.find(qn('w:gridSpan')) is not None:
                    raise ValueError('Merged table needs a separate layout plan')
                cell.width = width
                if 'vertical_padding_twips' in item:
                    margins = cell._tc.tcPr.find(qn('w:tcMar'))
                    if margins is None:
                        margins = OxmlElement('w:tcMar')
                        cell._tc.tcPr.append(margins)
                    for side in ('top', 'bottom'):
                        element = margins.find(qn('w:' + side))
                        if element is None:
                            element = OxmlElement('w:' + side)
                            margins.append(element)
                        element.set(qn('w:w'), str(item['vertical_padding_twips']))
                        element.set(qn('w:type'), 'dxa')
            trpr = row._tr.trPr
            if trpr is not None:
                for height in list(trpr.findall(qn('w:trHeight'))):
                    trpr.remove(height)
            for index, cell in enumerate(row.cells):
                for p in cell.paragraphs:
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER if index in item['center_columns'] else WD_ALIGN_PARAGRAPH.LEFT
    if plan.get('flow_table_captions'):
        for table in doc.tables:
            previous = table._tbl.getprevious()
            if previous is not None and previous.tag == qn('w:p'):
                p = Paragraph(previous, table._parent)
                if p.style.name == 'Caption':
                    p.paragraph_format.page_break_before = False
                    p.paragraph_format.keep_with_next = True
    if before != snapshot(doc):
        raise ValueError('Layout changed text or field instructions')
    doc.save(args.output)
    if before != snapshot(Document(args.output)):
        raise ValueError('Saved layout changed text or fields')
    print(json.dumps({'status':'SUCCESS','tables':len(plan['tables']),'text_and_fields_preserved':True,
                      'output_sha256':hashlib.sha256(args.output.read_bytes()).hexdigest()}))


if __name__ == '__main__':
    main()
