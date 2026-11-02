from __future__ import annotations

import argparse
import json
import textwrap
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

GROUP_ORDER = ["Hỏi đáp", "Tra cứu văn bản", "Hồ sơ nghiên cứu", "Quản trị"]
WIDTH, HEIGHT = 1600, 850
PARENT_Y, PARENT_H = 174, 78
CARD_Y = [322, 487, 652]
CARD_H = 142
GROUP_X = [35, 425, 815, 1205]
GROUP_W = 360
CARD_X_INSET = 18
CARD_W = GROUP_W - 2 * CARD_X_INSET
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)


def load_font(path: Path, size: int, bold: bool = False):
    candidates = [
        Path(r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf"),
        Path(r"C:\Windows\Fonts\timesbd.ttf" if bold else r"C:\Windows\Fonts\times.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def wrap_to_width(text: str, font, draw: ImageDraw.ImageDraw, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textbbox((0, 0), candidate, font=font)[2] <= max_width:
            current = candidate
            continue
        if current:
            lines.append(current)
        current = word
    if current:
        lines.append(current)
    return lines or [""]


def wrap_route(method: str, route: str, font, draw: ImageDraw.ImageDraw, max_width: int) -> list[str]:
    parts = route.strip("/").split("/")
    lines: list[str] = []
    current = method
    for part in parts:
        candidate = f"{current} /{part}" if current else f"/{part}"
        if draw.textbbox((0, 0), candidate, font=font)[2] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = f"/{part}"
    if current:
        lines.append(current)
    return lines or [f"{method} {route}"]


def center_text(draw, box, text, font, fill=BLACK):
    x0, y0, x1, y1 = box
    bbox = draw.textbbox((0, 0), text, font=font)
    x = (x0 + x1 - (bbox[2] - bbox[0])) / 2
    y = (y0 + y1 - (bbox[3] - bbox[1])) / 2 - bbox[1]
    draw.text((x, y), text, font=font, fill=fill)


def draw_arrow(draw, x1, y1, x2, y2, width=5, head=14):
    draw.line((x1, y1, x2, y2), fill=BLACK, width=width)
    if y2 >= y1:
        draw.polygon([(x2, y2), (x2 - head, y2 - head), (x2 + head, y2 - head)], fill=BLACK)
    elif x2 >= x1:
        draw.polygon([(x2, y2), (x2 - head, y2 - head), (x2 - head, y2 + head)], fill=BLACK)
    else:
        draw.polygon([(x2, y2), (x2 + head, y2 - head), (x2 + head, y2 + head)], fill=BLACK)


def render(inventory_path: Path, output_path: Path) -> dict:
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    nodes = inventory.get("screens", []) + inventory.get("actions", [])
    if not nodes:
        raise ValueError("screen-inventory.json must contain screens and actions")
    grouped = {name: [] for name in GROUP_ORDER}
    for node in nodes:
        group = node.get("diagram_group")
        if group not in grouped:
            raise ValueError(f"Unknown/missing diagram_group for node {node.get('id')}")
        if not node.get("method") or not node.get("route") or not node.get("diagram_label"):
            raise ValueError(f"Node needs method, route, and diagram_label: {node.get('id')}")
        grouped[group].append(node)
    if any(not 1 <= len(grouped[group]) <= len(CARD_Y) for group in GROUP_ORDER):
        raise ValueError("Each diagram group must contain one to three route/action nodes")

    image = Image.new("RGB", (WIDTH, HEIGHT), WHITE)
    draw = ImageDraw.Draw(image)
    root_font = load_font(Path("."), 43, True)
    group_font = load_font(Path("."), 34, True)
    route_font = load_font(Path("."), 28, False)
    label_font = load_font(Path("."), 25, False)
    line_width = 4

    root_box = (550, 32, 1050, 120)
    draw.rectangle(root_box, outline=BLACK, width=line_width)
    center_text(draw, root_box, "VIETLEX WEB", root_font)

    centers = [x + GROUP_W // 2 for x in GROUP_X]
    root_center = WIDTH // 2
    bus_y = 147
    draw.line((root_center, root_box[3], root_center, bus_y), fill=BLACK, width=line_width)
    draw.line((centers[0], bus_y, centers[-1], bus_y), fill=BLACK, width=line_width)

    for index, group in enumerate(GROUP_ORDER):
        gx, center = GROUP_X[index], centers[index]
        parent_box = (gx, PARENT_Y, gx + GROUP_W, PARENT_Y + PARENT_H)
        draw_arrow(draw, center, bus_y, center, PARENT_Y, width=line_width, head=13)
        draw.rectangle(parent_box, outline=BLACK, width=line_width)
        center_text(draw, parent_box, group, group_font)

        card_left = gx + CARD_X_INSET
        trunk_x = gx + 4
        branch_y = PARENT_Y + PARENT_H + 24
        first_center_y = CARD_Y[0] + CARD_H // 2
        last_center_y = CARD_Y[len(grouped[group]) - 1] + CARD_H // 2
        draw.line((center, PARENT_Y + PARENT_H, center, branch_y), fill=BLACK, width=line_width)
        draw.line((trunk_x, branch_y, center, branch_y), fill=BLACK, width=line_width)
        draw.line((trunk_x, branch_y, trunk_x, last_center_y), fill=BLACK, width=line_width)
        for row, node in enumerate(grouped[group]):
            y = CARD_Y[row]
            card_box = (card_left, y, card_left + CARD_W, y + CARD_H)
            node_center_y = y + CARD_H // 2
            draw_arrow(draw, trunk_x, node_center_y, card_left, node_center_y, width=line_width, head=12)
            draw.rectangle(card_box, outline=BLACK, width=line_width)
            route_lines = wrap_route(node['method'], node['route'], route_font, draw, CARD_W - 28)
            label_lines = wrap_to_width(node["diagram_label"], label_font, draw, CARD_W - 28)
            all_lines = [(route_font, line) for line in route_lines] + [(label_font, line) for line in label_lines]
            line_heights = [draw.textbbox((0, 0), line, font=font)[3] - draw.textbbox((0, 0), line, font=font)[1] for font, line in all_lines]
            total = sum(line_heights) + 7 * (len(all_lines) - 1)
            y_text = y + (CARD_H - total) / 2
            for (font, line), line_height in zip(all_lines, line_heights):
                bbox = draw.textbbox((0, 0), line, font=font)
                x_text = card_left + (CARD_W - (bbox[2] - bbox[0])) / 2
                draw.text((x_text, y_text - bbox[1]), line, font=font, fill=BLACK)
                y_text += line_height + 7

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, format="PNG", optimize=True)
    return {
        "status": "SUCCESS",
        "input": str(inventory_path.resolve()),
        "output": str(output_path.resolve()),
        "image_size_px": {"width": WIDTH, "height": HEIGHT},
        "route_nodes": len(nodes),
        "groups": {name: len(grouped[name]) for name in GROUP_ORDER},
        "runtime_screenshot": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a source-backed monochrome screen/action hierarchy from screen-inventory.json.")
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(render(args.inventory, args.output), ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())