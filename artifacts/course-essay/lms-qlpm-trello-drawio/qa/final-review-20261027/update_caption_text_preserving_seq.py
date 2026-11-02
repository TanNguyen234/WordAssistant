from __future__ import annotations

import hashlib
import json
from pathlib import Path

from docx import Document


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "LMS_wbs-text-01.docx"
OUTPUT = ROOT / "LMS_wbs-caption_updated.docx"
EXPECTED_SOURCE_SHA256 = "F41E8E35D4552625553B029CEDB46AEAF563B79F60819AB845FA87583FEABF37".lower()
PARAGRAPH_INDEX = 202
OLD = "Cấu trúc phân chia công việc LMS"
NEW = "WBS cấp 1 của dự án LMS (8 nhóm công việc; kế hoạch mô phỏng)"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


actual_hash = sha256(SOURCE)
if actual_hash != EXPECTED_SOURCE_SHA256:
    raise SystemExit(f"Input hash mismatch: expected {EXPECTED_SOURCE_SHA256}, got {actual_hash}")

document = Document(SOURCE)
paragraph = document.paragraphs[PARAGRAPH_INDEX]
matches = [run for run in paragraph.runs if OLD in run.text]
if len(matches) != 1:
    raise SystemExit(f"Expected one plain-text caption run, found {len(matches)}")
field_tags_before = sum(
    len(paragraph._p.xpath(f".//w:{tag}"))
    for tag in ("fldChar", "instrText", "fldSimple")
)
matches[0].text = matches[0].text.replace(OLD, NEW, 1)
field_tags_after = sum(
    len(paragraph._p.xpath(f".//w:{tag}"))
    for tag in ("fldChar", "instrText", "fldSimple")
)
if field_tags_after != field_tags_before:
    raise SystemExit("Caption field structure changed")
if paragraph.text != f"HÌNH 1. {NEW}":
    raise SystemExit(f"Unexpected caption result: {paragraph.text!r}")

document.save(OUTPUT)
print(json.dumps({
    "status": "SUCCESS",
    "input": str(SOURCE),
    "input_sha256": actual_hash,
    "output": str(OUTPUT),
    "output_sha256": sha256(OUTPUT),
    "paragraph_index": PARAGRAPH_INDEX,
    "caption": paragraph.text,
    "seq_field_tags_before": field_tags_before,
    "seq_field_tags_after": field_tags_after,
    "method": "replace only the plain-text caption run; preserve Word SEQ field runs",
}, ensure_ascii=False, indent=2))
