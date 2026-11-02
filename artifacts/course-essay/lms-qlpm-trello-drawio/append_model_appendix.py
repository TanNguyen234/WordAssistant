"""Append reviewed, configurable model pages using native Word headings/SEQ fields."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re

from docx import Document
from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt
from PIL import Image
from wordassistant.operations.fields import append_caption_content


def heading(doc, text, level):
    p = doc.add_paragraph(text, style=f'Heading {level}')
    num = OxmlElement('w:numPr')
    item = OxmlElement('w:numId')
    item.set(qn('w:val'), '0')
    num.append(item)
    p._p.get_or_add_pPr().append(num)
    p.paragraph_format.page_break_before = False
    p.paragraph_format.keep_with_next = True
    return p


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input', type=Path)
    parser.add_argument('config', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    if args.output.exists() or args.input.resolve() == args.output.resolve():
        raise ValueError('Output must be a distinct new file')
    config = json.loads(args.config.read_text(encoding='utf-8'))
    base = args.config.parent
    doc = Document(args.input)
    figure = next(p for p in doc.paragraphs if p.style.name == 'Caption' and p.text.startswith('HÌNH'))
    instruction = ' '.join(figure._p.xpath('.//w:instrText/text()'))
    sequence = re.search(r'\bSEQ\s+(\w+)', instruction).group(1)
    records = []
    for index, model in enumerate(config['models']):
        section = doc.add_section(WD_SECTION.NEW_PAGE)
        boundary = doc.paragraphs[-1]
        boundary.paragraph_format.space_before = Pt(0)
        boundary.paragraph_format.space_after = Pt(0)
        boundary.paragraph_format.line_spacing = Pt(1)
        boundary.paragraph_format.keep_with_next = False
        landscape = model['orientation'] == 'landscape'
        section.orientation = WD_ORIENT.LANDSCAPE if landscape else WD_ORIENT.PORTRAIT
        section.page_width, section.page_height = (Cm(29.7), Cm(21)) if landscape else (Cm(21), Cm(29.7))
        section.top_margin = section.bottom_margin = Cm(2)
        section.left_margin, section.right_margin = Cm(3), Cm(2)
        section.different_first_page_header_footer = False
        for element in section._sectPr.findall(qn('w:pgNumType')):
            element.attrib.pop(qn('w:start'), None)
        if index == 0:
            heading(doc, config['appendix_heading'], 2)
        heading(doc, model['heading'], 3)
        for text in model['paragraphs']:
            p = doc.add_paragraph(text, style='Normal')
            p.paragraph_format.keep_with_next = False
            p.paragraph_format.first_line_indent = Cm(0)
        image = base / model['image']
        width_px, height_px = Image.open(image).size
        width_cm = min(model['max_width_cm'], model['max_height_cm'] * width_px / height_px)
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(3)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1
        p.paragraph_format.keep_with_next = True
        picture = p.add_run().add_picture(str(image), width=Cm(width_cm))
        picture._inline.docPr.set('descr', model['alt'])
        picture._inline.docPr.set('title', model['caption'])
        cap = doc.add_paragraph(style='Caption')
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.paragraph_format.keep_with_next = False
        cap.paragraph_format.space_before = Pt(4)
        cap.paragraph_format.space_after = Pt(4)
        append_caption_content(doc, cap, 'HÌNH', model['caption'], sequence)
        records.append({'heading': model['heading'], 'caption': model['caption'], 'image': model['image'],
                        'sha256': hashlib.sha256(image.read_bytes()).hexdigest(), 'width_cm': width_cm})
    for update in config.get('table_updates', []):
        tables = [t for t in doc.tables if any(c.text == update['match_cell'] for row in t.rows for c in row.cells)]
        if len(tables) != 1 or len(tables[0].rows) != len(update['rows']) + 1:
            raise ValueError('Table update is ambiguous or has a different row count')
        for row, values in zip(tables[0].rows[1:], update['rows']):
            if len(row.cells) != len(values):
                raise ValueError('Table update has a different column count')
            for cell, text in zip(row.cells, values):
                p = cell.paragraphs[0]
                rpr = deepcopy(p.runs[0]._r.rPr) if p.runs and p.runs[0]._r.rPr is not None else None
                p.clear()
                run = p.add_run(text)
                if rpr is not None:
                    run._r.insert(0, rpr)
    # Reconcile the source-diagram inventory with the actual appendix additions.
    inventory = next(t for t in doc.tables if any(c.text == 'LMS_03' for row in t.rows for c in row.cells))
    updates = {'LMS_03': 'Bản bố cục gọn; Phụ lục D', 'LMS_05': 'PNG; Phụ lục D',
               'LMS_07': 'Nguồn lưu; HTTP method cần đối chiếu trước khi dùng',
               'LMS_08': 'Bản bố cục gọn; Phụ lục D',
               'LMS_10': 'Bản trích luồng bài tập; Phụ lục D', 'LMS_11': 'PNG; Phụ lục D'}
    for row in inventory.rows:
        if row.cells[0].text in updates:
            row.cells[2].text = updates[row.cells[0].text]
            for p in row.cells[2].paragraphs:
                p.paragraph_format.line_spacing = 1
                for run in p.runs:
                    run.font.name = 'Times New Roman'
                    run.font.size = Pt(10)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    doc.save(args.output)
    print(json.dumps({'status': 'SUCCESS', 'output': str(args.output), 'models': records}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
