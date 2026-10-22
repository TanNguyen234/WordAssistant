from __future__ import annotations
import argparse
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def main() -> None:
    parser = argparse.ArgumentParser(description="Create page contact sheets from a WordAssistant verify report.")
    parser.add_argument("verify_report", type=Path, help="JSON path written by wordassistant verify --render")
    parser.add_argument("output_dir", type=Path, help="Directory for review sheets")
    parser.add_argument("--columns", type=int, default=2)
    parser.add_argument("--rows", type=int, default=2)
    parser.add_argument("--page-width", type=int, default=460)
    args = parser.parse_args()
    if args.columns < 1 or args.rows < 1 or args.page_width < 100:
        parser.error("columns/rows must be positive and page-width must be at least 100")
    report = json.loads(args.verify_report.read_text(encoding="utf-8-sig"))
    paths = [Path(p) for p in report.get("render", {}).get("page_images", [])]
    if not paths:
        raise SystemExit("Verify report has no render.page_images; run verify --render first.")
    missing = [str(p) for p in paths if not p.is_file()]
    if missing:
        raise SystemExit("Missing rendered page images:\n" + "\n".join(missing))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    per_sheet = args.columns * args.rows
    cell_w = args.page_width + 20
    cell_h = round(args.page_width * 1.4142) + 42
    font = ImageFont.load_default()
    outputs = []
    for offset in range(0, len(paths), per_sheet):
        group = paths[offset:offset + per_sheet]
        sheet = Image.new("RGB", (args.columns * cell_w, args.rows * cell_h), "white")
        draw = ImageDraw.Draw(sheet)
        for local_index, path in enumerate(group):
            page_index = offset + local_index + 1
            with Image.open(path) as source:
                page = source.convert("RGB")
                height = round(page.height * args.page_width / page.width)
                page = page.resize((args.page_width, height), Image.Resampling.LANCZOS)
            col = local_index % args.columns
            row = local_index // args.columns
            x = col * cell_w + 10
            y = row * cell_h + 30
            draw.text((x, row * cell_h + 8), f"Page {page_index}", fill="black", font=font)
            sheet.paste(page, (x, y))
            draw.rectangle((x - 1, y - 1, x + page.width, y + page.height), outline="#777777", width=1)
        first = offset + 1
        last = offset + len(group)
        target = args.output_dir / f"contact-{first:03d}-{last:03d}.png"
        sheet.save(target, optimize=True)
        outputs.append(str(target))
    print(json.dumps({"status": "CREATED", "page_count": len(paths), "sheets": outputs}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
