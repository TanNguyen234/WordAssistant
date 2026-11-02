from __future__ import annotations

import hashlib
import json
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "LMS_20261027_wbs_revised_prefields.docx"
OUTPUT = ROOT / "LMS_20261027_wbs_geometry.docx"
EXPECTED_SOURCE_SHA256 = "674C302B22B78DFA222BCB540C30790A50680E34A6736ECBF928446AA4D80047".lower()
TABLE_INDEX = 6
WIDTHS_CM = (1.5, 4.5, 10.0)
EXPECTED_HEADERS = ("WBS", "Gói", "Đầu ra")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


actual_hash = sha256(SOURCE)
if actual_hash != EXPECTED_SOURCE_SHA256:
    raise SystemExit(f"Input hash mismatch: expected {EXPECTED_SOURCE_SHA256}, got {actual_hash}")

document = Document(SOURCE)
table = document.tables[TABLE_INDEX]
headers = tuple(cell.text.strip() for cell in table.rows[0].cells)
if headers != EXPECTED_HEADERS:
    raise SystemExit(f"Unexpected table headers: {headers!r}")
if len(table.columns) != len(WIDTHS_CM):
    raise SystemExit(f"Unexpected table width: {len(table.columns)} columns")

# WordAssistant table text operations normalize the grid. Restore the reviewed
# 1.5/4.5/10 cm layout explicitly after the content pass.
table.autofit = False
tbl_pr = table._tbl.tblPr
tbl_w = tbl_pr.find(qn("w:tblW"))
if tbl_w is None:
    raise SystemExit("Table has no w:tblW property")
tbl_w.set(qn("w:w"), str(Cm(sum(WIDTHS_CM)).twips))
tbl_w.set(qn("w:type"), "dxa")
tbl_layout = tbl_pr.find(qn("w:tblLayout"))
if tbl_layout is None:
    from docx.oxml import OxmlElement

    tbl_layout = OxmlElement("w:tblLayout")
    tbl_pr.append(tbl_layout)
tbl_layout.set(qn("w:type"), "fixed")

grid_columns = table._tbl.tblGrid.gridCol_lst
if len(grid_columns) != len(WIDTHS_CM):
    raise SystemExit(f"Unexpected grid width: {len(grid_columns)} columns")
for index, width_cm in enumerate(WIDTHS_CM):
    width_twips = Cm(width_cm).twips
    table.columns[index].width = Cm(width_cm)
    grid_columns[index].set(qn("w:w"), str(width_twips))
    for row in table.rows:
        cell = row.cells[index]
        cell.width = Cm(width_cm)
        tc_w = cell._tc.tcPr.tcW
        tc_w.set(qn("w:w"), str(width_twips))
        tc_w.set(qn("w:type"), "dxa")
        alignment = WD_ALIGN_PARAGRAPH.CENTER if index == 0 else WD_ALIGN_PARAGRAPH.LEFT
        for paragraph in cell.paragraphs:
            paragraph.alignment = alignment

document.save(OUTPUT)

verified = Document(OUTPUT).tables[TABLE_INDEX]
grid_twips = [int(column.get(qn("w:w"))) for column in verified._tbl.tblGrid.gridCol_lst]
expected_twips = [Cm(width).twips for width in WIDTHS_CM]
if grid_twips != expected_twips:
    raise SystemExit(f"Grid verification failed: {grid_twips!r} != {expected_twips!r}")
cell_widths = [int(cell._tc.tcPr.tcW.get(qn("w:w"))) for cell in verified.rows[1].cells]
if cell_widths != expected_twips:
    raise SystemExit(f"Cell verification failed: {cell_widths!r} != {expected_twips!r}")

print(json.dumps({
    "status": "SUCCESS",
    "input": str(SOURCE),
    "input_sha256": actual_hash,
    "output": str(OUTPUT),
    "output_sha256": sha256(OUTPUT),
    "table_index": TABLE_INDEX,
    "headers": headers,
    "widths_cm": WIDTHS_CM,
    "grid_twips": grid_twips,
    "cell_widths_row_1_twips": cell_widths,
    "body_alignment": ["center", "left", "left"],
}, ensure_ascii=False, indent=2))
