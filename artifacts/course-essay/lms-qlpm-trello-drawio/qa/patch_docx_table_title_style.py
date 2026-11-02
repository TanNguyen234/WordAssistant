from __future__ import annotations
import hashlib, json, sys
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from lxml import etree

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
NS = {'w': W}
q = lambda tag: f'{{{W}}}{tag}'
source = Path(sys.argv[1])
output = Path(sys.argv[2])
if output.exists():
    raise SystemExit(f'Output already exists: {output}')
count = 0
border_removed = False
with ZipFile(source, 'r') as zin, ZipFile(output, 'w', ZIP_DEFLATED) as zout:
    for item in zin.infolist():
        data = zin.read(item.filename)
        if item.filename == 'word/document.xml':
            root = etree.fromstring(data)
            tables = root.xpath('./w:body/w:tbl', namespaces=NS)
            for table in tables:
                count += 1
                tbl_pr = table.find('w:tblPr', NS)
                if tbl_pr is None:
                    tbl_pr = etree.Element(q('tblPr'))
                    table.insert(0, tbl_pr)
                old_borders = tbl_pr.find('w:tblBorders', NS)
                if old_borders is not None:
                    tbl_pr.remove(old_borders)
                borders = etree.Element(q('tblBorders'))
                for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
                    node = etree.SubElement(borders, q(edge))
                    node.set(q('val'), 'single')
                    node.set(q('sz'), '6')
                    node.set(q('space'), '0')
                    node.set(q('color'), 'D9D9D9')
                layout = tbl_pr.find('w:tblLayout', NS)
                tbl_pr.insert(tbl_pr.index(layout) if layout is not None else len(tbl_pr), borders)
                rows = table.findall('w:tr', NS)
                for row_index, row in enumerate(rows):
                    for cell in row.findall('w:tc', NS):
                        tc_pr = cell.find('w:tcPr', NS)
                        if tc_pr is None:
                            tc_pr = etree.Element(q('tcPr'))
                            cell.insert(0, tc_pr)
                        if row_index == 0:
                            shd = tc_pr.find('w:shd', NS)
                            if shd is None:
                                shd = etree.Element(q('shd'))
                                tc_mar = tc_pr.find('w:tcMar', NS)
                                tc_pr.insert(tc_pr.index(tc_mar) if tc_mar is not None else len(tc_pr), shd)
                            shd.set(q('val'), 'clear')
                            shd.set(q('color'), 'auto')
                            shd.set(q('fill'), 'DDEBF7')
                        valign = tc_pr.find('w:vAlign', NS)
                        if valign is None:
                            valign = etree.Element(q('vAlign'))
                            tc_pr.append(valign)
                        valign.set(q('val'), 'center')
            if count != 19:
                raise ValueError(f'Expected 19 body tables, found {count}')
            data = etree.tostring(root, encoding='UTF-8', xml_declaration=True, standalone=True)
        elif item.filename == 'word/styles.xml':
            root = etree.fromstring(data)
            matches = root.xpath('./w:style[@w:styleId="Title"]', namespaces=NS)
            if len(matches) != 1:
                raise ValueError(f'Expected one Title style, found {len(matches)}')
            ppr = matches[0].find('w:pPr', NS)
            if ppr is not None:
                p_bdr = ppr.find('w:pBdr', NS)
                if p_bdr is not None:
                    ppr.remove(p_bdr)
                    border_removed = True
            data = etree.tostring(root, encoding='UTF-8', xml_declaration=True, standalone=True)
        zout.writestr(item, data)
if not border_removed:
    raise ValueError('Expected decorative border on Title style was not found')
hash_value = hashlib.sha256(output.read_bytes()).hexdigest()
print(json.dumps({'status':'SUCCESS','output':str(output.resolve()),'tables_styled':count,'title_border_removed':border_removed,'sha256':hash_value}))