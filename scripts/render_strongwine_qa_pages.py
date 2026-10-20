#!/usr/bin/env python3
"""Render and visually audit selected pages from the Word-produced essay PDF."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

try:
    import fitz
    from PIL import Image, ImageDraw
except ImportError as exc:  # pragma: no cover - environment gate
    raise SystemExit(f"Required PDF preview dependency unavailable: {exc}") from exc


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().casefold()


def find_anchor_pages(document: fitz.Document, anchors: list[str]) -> dict[str, int]:
    pages: dict[str, int] = {}
    normalized_anchors = {anchor: normalize_text(anchor) for anchor in anchors}
    for page_index, page in enumerate(document):
        text = normalize_text(page.get_text("text"))
        for anchor, normalized in normalized_anchors.items():
            if normalized in text:
                # Captions can also appear in the list of figures. Prefer the
                # last occurrence, which is the in-body figure after front matter.
                pages[anchor] = page_index + 1
    return pages


def page_border_evidence(image_path: Path) -> dict[str, Any]:
    image = Image.open(image_path).convert("RGB")
    width, height = image.size
    pixels = image.load()
    dark_threshold = 80
    # The page is A4. Search for a frame 12–50 mm inside the paper edge;
    # this rejects the old page-relative frame that Word placed almost flush.
    min_x = max(1, round(width * 12 / 210))
    max_x = round(width * 50 / 210)
    min_y = max(1, round(height * 12 / 297))
    max_y = round(height * 50 / 297)
    coverage_threshold = 0.70

    def dark(x: int, y: int) -> bool:
        return max(pixels[x, y]) < dark_threshold

    top = [y for y in range(min_y, max_y) if sum(dark(x, y) for x in range(width)) / width >= coverage_threshold]
    bottom = [y for y in range(height - max_y, height - min_y) if sum(dark(x, y) for x in range(width)) / width >= coverage_threshold]
    left = [x for x in range(min_x, max_x) if sum(dark(x, y) for y in range(height)) / height >= coverage_threshold]
    right = [x for x in range(width - max_x, width - min_x) if sum(dark(x, y) for y in range(height)) / height >= coverage_threshold]
    sides = {"top": top, "bottom": bottom, "left": left, "right": right}
    inset_mm = {
        "top": round(min(top) * 297 / height, 1) if top else None,
        "bottom": round((height - 1 - max(bottom)) * 297 / height, 1) if bottom else None,
        "left": round(min(left) * 210 / width, 1) if left else None,
        "right": round((width - 1 - max(right)) * 210 / width, 1) if right else None,
    }
    return {
        "present": all(sides.values()) and all(12 <= value <= 50 for value in inset_mm.values() if value is not None),
        "detected_lines_px": {name: lines for name, lines in sides.items()},
        "inset_mm": inset_mm,
        "target_inset_mm": {"min": 12, "max": 50},
        "image_size_px": [width, height],
        "dark_pixel_threshold": dark_threshold,
        "line_coverage_threshold": coverage_threshold,
    }


def render_contact_sheets(
    document: fitz.Document,
    output_dir: Path,
    pages_per_sheet: int = 12,
    scale: float = 0.5,
) -> list[dict[str, Any]]:
    if pages_per_sheet < 1:
        raise ValueError("pages_per_sheet must be positive")
    if scale <= 0:
        raise ValueError("contact-sheet scale must be positive")
    output_dir.mkdir(parents=True, exist_ok=True)
    columns = 3
    records = []
    page_count = len(document)
    for start in range(0, page_count, pages_per_sheet):
        page_numbers = list(range(start + 1, min(start + pages_per_sheet, page_count) + 1))
        thumbnails = []
        for page_number in page_numbers:
            pixmap = document[page_number - 1].get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
            thumbnails.append(Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples))
        thumb_width = max(image.width for image in thumbnails)
        thumb_height = max(image.height for image in thumbnails)
        label_height = 28
        rows = math.ceil(len(thumbnails) / columns)
        sheet = Image.new("RGB", (columns * thumb_width, rows * (thumb_height + label_height)), "white")
        draw = ImageDraw.Draw(sheet)
        for index, (page_number, thumbnail) in enumerate(zip(page_numbers, thumbnails)):
            col, row = index % columns, index // columns
            x, y = col * thumb_width, row * (thumb_height + label_height)
            draw.text((x + 6, y + 5), f"Physical page {page_number}", fill="black")
            sheet.paste(thumbnail, (x, y + label_height))
        path = output_dir / f"contact-sheet-{page_numbers[0]:03d}-{page_numbers[-1]:03d}.png"
        sheet.save(path, format="PNG", optimize=True)
        records.append({
            "pages": page_numbers,
            "image": str(path.resolve()),
            "sha256": sha256(path),
            "width_px": sheet.width,
            "height_px": sheet.height,
        })
    return records


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--pages", type=int, nargs="*", default=[])
    parser.add_argument("--anchor", action="append", default=[])
    parser.add_argument("--check-cover-borders", action="store_true")
    parser.add_argument("--scale", type=float, default=1.8)
    parser.add_argument("--all-pages", action="store_true", help="Create low-resolution contact sheets covering every physical PDF page")
    parser.add_argument("--contact-sheet-pages", type=int, default=12)
    parser.add_argument("--contact-sheet-scale", type=float, default=0.5)
    args = parser.parse_args()

    if not args.pdf.is_file():
        raise SystemExit(f"Rendered PDF not found: {args.pdf}")
    if args.scale <= 0:
        raise SystemExit("--scale must be greater than zero")
    if args.contact_sheet_scale <= 0 or args.contact_sheet_pages <= 0:
        raise SystemExit("Contact sheet scale and pages per sheet must be positive")

    document = fitz.open(args.pdf)
    anchor_pages = find_anchor_pages(document, args.anchor)
    missing_anchors = [anchor for anchor in args.anchor if anchor not in anchor_pages]
    selected_pages = set(args.pages)
    selected_pages.update(anchor_pages.values())
    if args.check_cover_borders:
        selected_pages.update((1, 2, 3))
    if not selected_pages:
        raise SystemExit("Provide at least one --page or --anchor")
    invalid_pages = sorted(page for page in selected_pages if page < 1 or page > len(document))
    if invalid_pages:
        raise SystemExit(f"Requested pages outside PDF range 1..{len(document)}: {invalid_pages}")

    args.outdir.mkdir(parents=True, exist_ok=True)
    page_records = []
    rendered_paths: dict[int, Path] = {}
    for page_number in sorted(selected_pages):
        page = document[page_number - 1]
        pixmap = page.get_pixmap(matrix=fitz.Matrix(args.scale, args.scale), alpha=False)
        path = args.outdir / f"page-{page_number:03d}.png"
        pixmap.save(path)
        rendered_paths[page_number] = path
        page_records.append({
            "page": page_number,
            "image": str(path.resolve()),
            "sha256": sha256(path),
            "width_px": pixmap.width,
            "height_px": pixmap.height,
        })

    contact_sheet_records = render_contact_sheets(
        document,
        args.outdir / "contact-sheets",
        pages_per_sheet=args.contact_sheet_pages,
        scale=args.contact_sheet_scale,
    ) if args.all_pages else []

    border_checks = None
    if args.check_cover_borders:
        border_checks = {
            str(number): page_border_evidence(rendered_paths[number])
            for number in (1, 2, 3)
        }

    passed = not missing_anchors
    if border_checks is not None:
        passed = passed and border_checks["1"]["present"] and border_checks["2"]["present"]
        passed = passed and not border_checks["3"]["present"]

    report = {
        "pdf": str(args.pdf.resolve()),
        "pdf_sha256": sha256(args.pdf),
        "page_count": len(document),
        "status": "PASS" if passed else "FAIL",
        "missing_anchors": missing_anchors,
        "anchor_pages": anchor_pages,
        "cover_border_checks": border_checks,
        "rendered_pages": page_records,
        "all_pages_contacted": args.all_pages,
        "contact_sheets": contact_sheet_records,
        "visual_review_required": True,
        "note": "Pixel checks confirm frame lines only; a person must still review the rendered page images for content, clipping, and legibility.",
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
