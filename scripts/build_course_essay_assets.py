#!/usr/bin/env python3
"""Build source-checked, monochrome course-essay wireframes and screen trees."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
FONT_CANDIDATES = (
    Path(r"C:\Windows\Fonts\arial.ttf"),
    Path(r"C:\Windows\Fonts\calibri.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
)
ROLE_LABELS = {"customer": "khách hàng", "admin": "quản trị", "shipper": "giao hàng"}


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = list(FONT_CANDIDATES)
    if bold:
        candidates = [
            Path(r"C:\Windows\Fonts\arialbd.ttf"),
            Path(r"C:\Windows\Fonts\calibrib.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
            *candidates,
        ]
    for path in candidates:
        if path.is_file():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def _wrapped(text: str, font: ImageFont.ImageFont, max_width: int, draw: ImageDraw.ImageDraw) -> list[str]:
    words = str(text).split()
    if not words:
        return [""]
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if draw.textbbox((0, 0), candidate, font=font)[2] <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def _draw_wrapped(
    draw: ImageDraw.ImageDraw,
    text: str,
    xy: tuple[int, int],
    font: ImageFont.ImageFont,
    max_width: int,
    fill: str = "black",
    line_gap: int = 8,
    align: str = "left",
) -> int:
    x, y = xy
    lines = _wrapped(text, font, max_width, draw)
    line_height = max(font.getbbox("Ag")[3] - font.getbbox("Ag")[1], 1) + line_gap
    for line in lines:
        width = draw.textbbox((0, 0), line, font=font)[2]
        line_x = x + (max_width - width) // 2 if align == "center" else x
        draw.text((line_x, y), line, fill=fill, font=font)
        y += line_height
    return y


def _draw_centered_block(
    draw: ImageDraw.ImageDraw,
    text: str,
    box: tuple[int, int, int, int],
    font: ImageFont.ImageFont,
    fill: str = "black",
    line_gap: int = 4,
) -> None:
    left, top, right, bottom = box
    lines = _wrapped(text, font, right - left - 18, draw)
    line_height = max(font.getbbox("Ag")[3] - font.getbbox("Ag")[1], 1) + line_gap
    total_height = len(lines) * line_height - line_gap
    y = top + max((bottom - top - total_height) // 2, 4)
    for line in lines:
        width = draw.textbbox((0, 0), line, font=font)[2]
        draw.text((left + max((right - left - width) // 2, 8), y), line, fill=fill, font=font)
        y += line_height


def _draw_table(
    draw: ImageDraw.ImageDraw,
    columns: list[str],
    x: int,
    y: int,
    width: int,
    rows: int,
    small_font: ImageFont.ImageFont,
) -> int:
    if not columns:
        return y
    col_width = width / len(columns)
    header_height = 96 if len(columns) <= 5 else 112
    row_height = 54
    draw.rectangle((x, y, x + width, y + header_height + rows * row_height), outline="black", width=3)
    for index, label in enumerate(columns):
        lx = round(x + index * col_width)
        rx = round(x + (index + 1) * col_width)
        if index:
            draw.line((lx, y, lx, y + header_height + rows * row_height), fill="black", width=2)
        _draw_centered_block(draw, label, (lx + 3, y + 2, rx - 3, y + header_height - 2), small_font)
    draw.line((x, y + header_height, x + width, y + header_height), fill="black", width=3)
    for row in range(1, rows + 1):
        row_y = y + header_height + row * row_height
        draw.line((x, row_y, x + width, row_y), fill="black", width=2)
    return y + header_height + rows * row_height


def _draw_fields(draw: ImageDraw.ImageDraw, fields: list[str], x: int, y: int, width: int) -> int:
    gap = 34
    column_width = (width - gap) // 2
    label_font = _font(27)
    per_row = 2
    for index in range(0, len(fields), per_row):
        row_fields = fields[index : index + per_row]
        for column, label in enumerate(row_fields):
            left = x + column * (column_width + gap)
            label_y = y + 3
            _draw_wrapped(draw, label, (left, label_y), label_font, column_width - 8, line_gap=3)
            box_y = y + 43
            draw.rectangle((left, box_y, left + column_width - 6, box_y + 47), outline="black", width=3)
        y += 108
    return y


def render_wireframe(spec: dict[str, Any], output_path: Path) -> dict[str, Any]:
    """Render a plain form-style wireframe with blank controls and no sample data."""
    width, height = 1800, 1400
    margin = 55
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    title_font = _font(43, bold=True)
    route_font = _font(26)
    section_font = _font(31, bold=True)
    body_font = _font(27)
    small_font = _font(23)
    action_font = _font(25, bold=True)

    title = f"MÀN HÌNH — {spec['screen_title']}"
    _draw_wrapped(draw, title, (margin, 30), title_font, width - 2 * margin, align="center")
    _draw_wrapped(draw, spec.get("route", ""), (margin, 91), route_font, width - 2 * margin, align="center")
    frame = (margin, 145, width - margin, height - margin)
    draw.rectangle(frame, outline="black", width=4)
    y = frame[1] + 32
    content_x = frame[0] + 42
    content_width = frame[2] - frame[0] - 84

    note = spec.get("inline_state_note")
    if note:
        draw.rectangle((content_x, y, frame[2] - 42, y + 68), outline="black", width=2)
        _draw_centered_block(draw, note, (content_x + 10, y + 4, frame[2] - 52, y + 64), small_font)
        y += 91

    for section in spec.get("sections", []):
        if y + 70 >= frame[3] - 26:
            raise ValueError(f"Wireframe content exceeds the canvas: {spec.get('id', spec.get('screen_title'))}")
        draw.text((content_x, y), section.get("title", ""), fill="black", font=section_font)
        y += 48
        draw.line((content_x, y, frame[2] - 42, y), fill="black", width=2)
        y += 18

        text_items = section.get("text_items", [])
        for item in text_items:
            y = _draw_wrapped(draw, item, (content_x + 8, y), body_font, content_width - 16, line_gap=6) + 7

        fields = section.get("fields", [])
        if fields:
            y = _draw_fields(draw, fields, content_x + 8, y, content_width - 16) + 8

        panels = section.get("panels", [])
        if panels:
            gap = 20
            panel_width = (content_width - gap * (min(2, len(panels)) - 1)) // min(2, len(panels))
            for index, label in enumerate(panels):
                column = index % 2
                row = index // 2
                px = content_x + column * (panel_width + gap)
                py = y + row * 150
                draw.rectangle((px, py, px + panel_width, py + 132), outline="black", width=3)
                _draw_centered_block(draw, label, (px + 8, py + 8, px + panel_width - 8, py + 124), body_font)
            y += ((len(panels) + 1) // 2) * 150 + 8

        table_columns = section.get("table_columns", [])
        if table_columns:
            y = _draw_table(
                draw,
                table_columns,
                content_x + 4,
                y,
                content_width - 8,
                max(1, min(int(section.get("rows", 3)), 3)),
                small_font,
            ) + 18

        cards = section.get("cards")
        if cards:
            count = max(1, int(cards.get("count", 1)))
            columns = min(4, count)
            rows = (count + columns - 1) // columns
            gap = 20
            card_width = (content_width - gap * (columns - 1)) // columns
            card_height = 184
            labels = cards.get("items", [])
            for index in range(count):
                row, column = divmod(index, columns)
                left = content_x + column * (card_width + gap)
                top = y + row * (card_height + gap)
                draw.rectangle((left, top, left + card_width, top + card_height), outline="black", width=3)
                image_height = 78
                draw.rectangle((left + 10, top + 10, left + card_width - 10, top + image_height), outline="black", width=2)
                _draw_centered_block(draw, labels[0] if labels else "Ảnh", (left + 14, top + 12, left + card_width - 14, top + image_height - 2), small_font)
                card_y = top + image_height + 9
                for label in labels[1:]:
                    if card_y + 28 >= top + card_height:
                        break
                    _draw_wrapped(draw, label, (left + 12, card_y), small_font, card_width - 24, line_gap=2)
                    card_y += 29
            y += rows * (card_height + gap) + 4

        buttons = section.get("buttons", [])
        if buttons:
            gap = 18
            button_height = 56
            available = content_width - 16
            widths = [min(available, max(190, draw.textbbox((0, 0), label, font=action_font)[2] + 48)) for label in buttons]
            if sum(widths) + gap * (len(widths) - 1) > available:
                y += 5
                for label in buttons:
                    button_width = min(available, max(230, draw.textbbox((0, 0), label, font=action_font)[2] + 44))
                    draw.rectangle((content_x + 8, y, content_x + 8 + button_width, y + button_height), outline="black", width=3)
                    _draw_centered_block(draw, label, (content_x + 14, y + 4, content_x + button_width + 2, y + button_height - 4), action_font)
                    y += button_height + 12
            else:
                x = content_x + 8
                for label, button_width in zip(buttons, widths):
                    draw.rectangle((x, y, x + button_width, y + button_height), outline="black", width=3)
                    _draw_centered_block(draw, label, (x + 5, y + 3, x + button_width - 5, y + button_height - 3), action_font)
                    x += button_width + gap
                y += button_height + 15
        else:
            y += 8

    if y > frame[3] - 18:
        raise ValueError(f"Wireframe content is clipped: {spec.get('id', spec.get('screen_title'))} ends at {y}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, format="PNG", optimize=True)
    return {"id": spec.get("id"), "path": str(output_path.resolve()), "width": width, "height": height}


def _matching_paren(text: str, open_index: int) -> int:
    depth = 0
    quote = None
    escaped = False
    for index in range(open_index, len(text)):
        char = text[index]
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in ('"', "'"):
            quote = char
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return index
    raise ValueError("Unclosed Java annotation or method parameter list")


def _annotation_arg(source: str, match: re.Match[str]) -> str:
    cursor = match.end()
    while cursor < len(source) and source[cursor].isspace():
        cursor += 1
    if cursor >= len(source) or source[cursor] != "(":
        return ""
    open_index = cursor
    return source[open_index + 1 : _matching_paren(source, open_index)]


def _quoted_values(value: str) -> list[str]:
    return re.findall(r'"((?:\\.|[^"\\])*)"', value)


def _method_body(source: str, open_brace: int) -> str:
    depth = 0
    quote = None
    escaped = False
    for index in range(open_brace, len(source)):
        char = source[index]
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in ('"', "'"):
            quote = char
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return source[open_brace : index + 1]
    return source[open_brace:]


def discover_mvc_get_views(project_root: Path, template_root: str = "src/main/resources/templates") -> list[dict[str, str]]:
    """Find non-API MVC GET methods whose return value names an existing view template."""
    root = project_root / "src" / "main" / "java"
    template_dir = project_root / template_root
    discovered: list[dict[str, str]] = []
    method_pattern = re.compile(r"\b(?:public|protected)\s+([\w<>.?]+)\s+[A-Za-z_$][\w$]*\s*\(")

    for controller_path in root.rglob("*Controller.java"):
        relative = controller_path.relative_to(root).as_posix()
        if "/api/" in f"/{relative}/" or "RestController" in controller_path.read_text(encoding="utf-8", errors="replace"):
            continue
        source = controller_path.read_text(encoding="utf-8", errors="replace")
        class_position = re.search(r"\bclass\s+[A-Za-z_$][\w$]*", source)
        prefix = source[: class_position.start()] if class_position else source
        class_bases: list[str] = []
        for request_match in re.finditer(r"@RequestMapping\b", prefix):
            class_bases.extend(_quoted_values(_annotation_arg(prefix, request_match)))
        if not class_bases:
            class_bases = [""]

        for get_match in re.finditer(r"@(?:[A-Za-z_$][\w$]*\.)*GetMapping\b", source):
            annotation_args = _annotation_arg(source, get_match)
            suffixes = _quoted_values(annotation_args) or [""]
            search_start = get_match.end()
            signature = method_pattern.search(source, search_start, min(len(source), search_start + 1200))
            if not signature or signature.group(1) != "String":
                continue
            parameter_open = source.find("(", signature.start())
            parameter_close = _matching_paren(source, parameter_open)
            body_open = source.find("{", parameter_close)
            if body_open < 0:
                continue
            body = _method_body(source, body_open)
            returned_views = [
                value for value in re.findall(r"\breturn\s+\"([^\"]+)\"\s*;", body)
                if not value.startswith("redirect:") and (template_dir / f"{value}.html").is_file()
            ]
            if not returned_views:
                continue
            view = returned_views[0]
            for base in class_bases:
                for suffix in suffixes:
                    route = "/".join(part.strip("/") for part in (base, suffix) if part.strip("/"))
                    route = f"/{route}" if route else "/"
                    discovered.append({"method": "GET", "route": route, "view": view, "controller": relative})

    unique = {(item["method"], item["route"], item["view"], item["controller"]): item for item in discovered}
    return sorted(unique.values(), key=lambda item: (item["route"], item["controller"]))


def _all_routes(screen: dict[str, Any]) -> list[str]:
    routes = screen.get("routes")
    if isinstance(routes, str):
        routes = [routes]
    if not routes and screen.get("route"):
        routes = [screen["route"]]
    return [str(route).strip() for route in routes or []]


def _walk_dicts(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_dicts(child)


def validate_inventory(project_root: Path, inventory: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if inventory.get("schema_version") != 1:
        errors.append("screen inventory schema_version must be 1")
    screens = inventory.get("screens", [])
    wireframes = inventory.get("wireframes", [])
    ids = [screen.get("id") for screen in screens]
    if len(ids) != len(set(ids)):
        errors.append("screen ids must be unique")
    known_ids = set(ids)
    template_root = inventory.get("template_root", "src/main/resources/templates")

    declared_routes: set[str] = set()
    for screen in screens:
        screen_id = screen.get("id", "<missing id>")
        for route in _all_routes(screen):
            if not route.startswith("GET ") or "POST " in route:
                errors.append(f"{screen_id}: screen route must be a rendered GET view: {route}")
                continue
            declared_routes.add(route[4:].strip())
        controller_path = project_root / screen.get("controller", "")
        if not controller_path.is_file():
            errors.append(f"{screen_id}: controller source is missing: {screen.get('controller')}")
            continue
        controller_source = controller_path.read_text(encoding="utf-8", errors="replace")
        for token in screen.get("mapping_tokens", []):
            if token not in controller_source:
                errors.append(f"{screen_id}: controller mapping evidence is missing: {token}")
        view_token = screen.get("view_token", "")
        if not view_token or view_token not in controller_source:
            errors.append(f"{screen_id}: controller view return evidence is missing: {view_token!r}")
        template_path = project_root / template_root / screen.get("template", "")
        if not template_path.is_file():
            errors.append(f"{screen_id}: view template is missing: {template_path}")
        for role in screen.get("roles", []):
            if not isinstance(role, str) or not role.strip():
                errors.append(f"{screen_id}: role must be a non-empty string: {role!r}")
                continue
            if not re.fullmatch(r"[A-Za-z0-9_-]+", role):
                errors.append(f"{screen_id}: role id must contain only letters, numbers, underscores, or hyphens: {role!r}")
                continue
            if role not in screen.get("modules", {}):
                errors.append(f"{screen_id}: module label missing for role {role!r}")

    discovered = discover_mvc_get_views(project_root, template_root)
    discovered_routes = {item["route"] for item in discovered}
    for route in sorted(discovered_routes - declared_routes):
        errors.append(f"MVC GET view route is missing from the screen inventory: GET {route}")
    for route in sorted(declared_routes - discovered_routes):
        errors.append(f"Inventory route is not a discovered MVC GET view: GET {route}")

    wireframe_ids: set[str] = set()
    filenames: set[str] = set()
    for wireframe in wireframes:
        wireframe_id = wireframe.get("id", "<missing id>")
        if wireframe_id in wireframe_ids:
            errors.append(f"wireframe id must be unique: {wireframe_id}")
        wireframe_ids.add(wireframe_id)
        filename = wireframe.get("file", "")
        if not filename or Path(filename).name != filename or filename in filenames:
            errors.append(f"wireframe file must be a unique filename: {filename!r}")
        filenames.add(filename)
        missing_screens = [item for item in wireframe.get("screen_ids", []) if item not in known_ids]
        if missing_screens:
            errors.append(f"{wireframe_id}: unknown screen ids: {missing_screens}")
        if not wireframe.get("caption") or not wireframe.get("screen_title"):
            errors.append(f"{wireframe_id}: caption and screen_title are required")
        source_routes = {
            route
            for screen_id in wireframe.get("screen_ids", [])
            for route in _all_routes(next((item for item in screens if item.get("id") == screen_id), {}))
        }
        declared_wireframe_routes = set()
        for route_part in re.split(r"\s*[·;]\s*", wireframe.get("route", "")):
            route_part = re.sub(r"\s+\([^)]*\)\s*$", "", route_part.strip())
            if not route_part:
                continue
            if not route_part.startswith("GET "):
                route_part = f"GET {route_part}"
            declared_wireframe_routes.add(route_part)
        if not declared_wireframe_routes:
            errors.append(f"{wireframe_id}: wireframe must name at least one source-backed GET route")
        elif not declared_wireframe_routes.issubset(source_routes):
            errors.append(
                f"{wireframe_id}: wireframe routes do not match its linked screen routes; "
                f"declared={sorted(declared_wireframe_routes)}, source={sorted(source_routes)}"
            )
        for item in _walk_dicts(wireframe):
            if any(key in item for key in ("sample_values", "example_values", "data_records", "metric_values")):
                errors.append(f"{wireframe_id}: wireframes must not contain unsupported sample data")
                break
    return errors


def _role_label(role: str) -> str:
    return ROLE_LABELS.get(role, role.replace("_", " ").replace("-", " "))


def _system_title(inventory: dict[str, Any]) -> str:
    return str(inventory.get("system_title") or "Hệ thống").strip()


def _hierarchy_puml(inventory: dict[str, Any], role: str) -> str:
    role_title = _role_label(role).upper()
    root_title = f"{_system_title(inventory)} — {_role_label(role)}"
    screens = [screen for screen in inventory.get("screens", []) if role in screen.get("roles", [])]
    groups: dict[str, list[dict[str, Any]]] = {}
    for screen in screens:
        groups.setdefault(screen["modules"][role], []).append(screen)
    lines = [
        "@startwbs",
        "skinparam monochrome true",
        "skinparam backgroundColor white",
        "skinparam shadowing false",
        "skinparam defaultFontName Arial",
        "skinparam defaultFontSize 12",
        "skinparam dpi 160",
        f"title CÂY PHÂN RÃ MÀN HÌNH — {role_title} (MVC GET)",
        f"* {root_title}",
    ]
    for module in sorted(groups):
        lines.append(f"** {module}")
        for screen in sorted(groups[module], key=lambda item: (item["label"], item["id"])):
            lines.append(f"*** {screen['label']}")
    lines.append("@endwbs")
    return "\n".join(lines) + "\n"


def _render_hierarchy(inventory: dict[str, Any], role: str, output_path: Path) -> dict[str, Any]:
    """Draw the supplied root → module → page hierarchy in black and white.

    Exact routes stay in the validated inventory. The reference hierarchy uses
    screen names in its boxes, so long route strings are omitted here to keep the
    diagram readable at report-page size.
    """
    role_title = _role_label(role).upper()
    root_title = f"{_system_title(inventory)} — {_role_label(role)}"
    screens = [screen for screen in inventory.get("screens", []) if role in screen.get("roles", [])]
    groups: dict[str, list[dict[str, Any]]] = {}
    for screen in screens:
        groups.setdefault(screen["modules"][role], []).append(screen)
    ordered_groups = [(name, sorted(items, key=lambda item: (item["label"], item["id"]))) for name, items in sorted(groups.items())]
    width, margin = 1600, 38
    column_width = (width - 2 * margin) / max(len(ordered_groups), 1)
    node_height, row_step, page_start = 170, 190, 388
    max_pages = max((len(items) for _, items in ordered_groups), default=1)
    height = page_start + max_pages * row_step + 45
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    title_font = _font(40, bold=True)
    root_font = _font(38, bold=True)
    module_font = _font(32, bold=True)
    page_font = _font(38, bold=True)

    title = f"CÂY PHÂN RÃ MÀN HÌNH — {role_title} (MVC GET)"
    _draw_wrapped(draw, title, (margin, 16), title_font, width - 2 * margin, align="center")

    root_box_width, root_box_height = 720, 84
    root_left = (width - root_box_width) // 2
    root_top = 84
    draw.rectangle((root_left, root_top, root_left + root_box_width, root_top + root_box_height), outline="black", fill="white", width=3)
    _draw_centered_block(draw, root_title, (root_left + 10, root_top + 6, root_left + root_box_width - 10, root_top + root_box_height - 6), root_font)

    module_top, module_height = 218, 126
    module_centers: list[int] = []
    columns: list[tuple[int, int, str, list[dict[str, Any]]]] = []
    for index, (module_name, module_screens) in enumerate(ordered_groups):
        col_left = round(margin + index * column_width)
        col_right = round(margin + (index + 1) * column_width)
        module_width = col_right - col_left - 18
        module_left = col_left + (col_right - col_left - module_width) // 2
        center = module_left + module_width // 2
        module_centers.append(center)
        columns.append((col_left, col_right, module_name, module_screens))
        draw.rectangle((module_left, module_top, module_left + module_width, module_top + module_height), outline="black", fill="white", width=3)
        _draw_centered_block(draw, module_name, (module_left + 8, module_top + 5, module_left + module_width - 8, module_top + module_height - 5), module_font)

    branch_y = 190
    draw.line((width // 2, root_top + root_box_height, width // 2, branch_y), fill="black", width=3)
    if module_centers:
        draw.line((min(module_centers), branch_y, max(module_centers), branch_y), fill="black", width=3)
        for center in module_centers:
            draw.line((center, branch_y, center, module_top), fill="black", width=3)

    for col_left, col_right, _module_name, module_screens in columns:
        box_width = col_right - col_left - 40
        spine_x = col_left + 12
        first_center_y = page_start + node_height // 2
        last_center_y = page_start + (len(module_screens) - 1) * row_step + node_height // 2
        module_center = round((col_left + col_right) / 2)
        draw.line((module_center, module_top + module_height, module_center, module_top + module_height + 16), fill="black", width=3)
        draw.line((module_center, module_top + module_height + 16, spine_x, module_top + module_height + 16), fill="black", width=3)
        draw.line((spine_x, module_top + module_height + 16, spine_x, last_center_y), fill="black", width=3)

        for page_index, screen in enumerate(module_screens):
            top = page_start + page_index * row_step
            center_y = top + node_height // 2
            left = col_left + 28
            right = min(left + box_width, col_right - 8)
            draw.line((spine_x, center_y, left, center_y), fill="black", width=3)
            draw.rectangle((left, top, right, top + node_height), outline="black", fill="white", width=3)
            title_lines = _wrapped(screen["label"], page_font, right - left - 18, draw)
            total_height = len(title_lines) * 46
            text_y = top + max((node_height - total_height) // 2, 5)
            _draw_wrapped(draw, screen["label"], (left + 9, text_y), page_font, right - left - 18, align="center", line_gap=1)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, format="PNG", optimize=True)
    return {"role": role, "path": str(output_path.resolve()), "width": width, "height": height}


def build_assets(
    project_root: Path,
    inventory_path: Path,
    wireframe_dir: Path,
    diagram_dir: Path,
    report_path: Path | None = None,
) -> dict[str, Any]:
    inventory = json.loads(inventory_path.read_text(encoding="utf-8-sig"))
    errors = validate_inventory(project_root, inventory)
    if errors:
        report = {"status": "FAIL", "errors": errors, "inventory": str(inventory_path.resolve())}
        if report_path:
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        raise ValueError(json.dumps(report, ensure_ascii=False, indent=2))

    wireframes = [render_wireframe(item, wireframe_dir / item["file"]) for item in inventory["wireframes"]]
    hierarchies = []
    roles = sorted({role for screen in inventory.get("screens", []) for role in screen.get("roles", [])})
    for role in roles:
        path = diagram_dir / f"screen_hierarchy_{role}.puml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_hierarchy_puml(inventory, role), encoding="utf-8")
        image_path = diagram_dir / f"screen_hierarchy_{role}.png"
        hierarchies.append({"plantuml_source": str(path.resolve()), **_render_hierarchy(inventory, role, image_path)})

    report = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS",
        "project_root": str(project_root.resolve()),
        "inventory": str(inventory_path.resolve()),
        "screen_count": len(inventory.get("screens", [])),
        "mvc_get_view_routes": discover_mvc_get_views(project_root, inventory.get("template_root", "src/main/resources/templates")),
        "wireframes": wireframes,
        "hierarchy_sources": hierarchies,
        "style": "black and white line wireframes; blank fields and rows; no sample values; no browser chrome",
    }
    if report_path:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def initialize_project(template_dir: Path, destination: Path, project_title: str) -> Path:
    """Copy starter files to a new directory and set only the verified project title."""
    if not project_title.strip():
        raise ValueError("A verified project title is required")
    template_dir = template_dir.resolve()
    destination = destination.resolve()
    if not template_dir.is_dir():
        raise FileNotFoundError(f"Starter template directory does not exist: {template_dir}")
    if not destination.parent.is_dir():
        raise FileNotFoundError(f"Destination parent directory does not exist: {destination.parent}")
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite existing project directory: {destination}")
    shutil.copytree(template_dir, destination)
    project_json = destination / "project.json"
    data = json.loads(project_json.read_text(encoding="utf-8"))
    data["project_title"] = project_title.strip()
    project_json.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    build = subparsers.add_parser("build", help="Audit route/template inventory and render assets")
    build.add_argument("--project-root", type=Path, required=True)
    build.add_argument("--inventory", type=Path, required=True)
    build.add_argument("--wireframe-dir", type=Path, required=True)
    build.add_argument("--diagram-dir", type=Path, required=True)
    build.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = build_assets(args.project_root, args.inventory, args.wireframe_dir, args.diagram_dir, args.report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
