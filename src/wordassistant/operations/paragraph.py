from __future__ import annotations

from pathlib import Path
from typing import Any

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_COLOR_INDEX, WD_LINE_SPACING
from docx.shared import Cm, Pt, RGBColor

from ..document.fonts import set_word_font
from ..selectors import Selector, resolve_paragraphs
from .common import atomic_save
from .models import Fidelity, OperationResult


_ALIGNMENTS = {
    "left": WD_ALIGN_PARAGRAPH.LEFT,
    "center": WD_ALIGN_PARAGRAPH.CENTER,
    "right": WD_ALIGN_PARAGRAPH.RIGHT,
    "justify": WD_ALIGN_PARAGRAPH.JUSTIFY,
    "distribute": WD_ALIGN_PARAGRAPH.DISTRIBUTE,
}

_HIGHLIGHTS = {
    "black": WD_COLOR_INDEX.BLACK,
    "blue": WD_COLOR_INDEX.BLUE,
    "bright_green": WD_COLOR_INDEX.BRIGHT_GREEN,
    "dark_blue": WD_COLOR_INDEX.DARK_BLUE,
    "dark_red": WD_COLOR_INDEX.DARK_RED,
    "dark_yellow": WD_COLOR_INDEX.DARK_YELLOW,
    "gray_25": WD_COLOR_INDEX.GRAY_25,
    "gray_50": WD_COLOR_INDEX.GRAY_50,
    "green": WD_COLOR_INDEX.GREEN,
    "pink": WD_COLOR_INDEX.PINK,
    "red": WD_COLOR_INDEX.RED,
    "teal": WD_COLOR_INDEX.TEAL,
    "turquoise": WD_COLOR_INDEX.TURQUOISE,
    "violet": WD_COLOR_INDEX.VIOLET,
    "white": WD_COLOR_INDEX.WHITE,
    "yellow": WD_COLOR_INDEX.YELLOW,
}


def _paragraphs(document, selector):
    return resolve_paragraphs(document, Selector.from_value(selector or {"type": "document"}))


def format_runs(
    input_path: str | Path,
    *,
    output_path: str | Path,
    selector=None,
    dry_run: bool = False,
    **formatting: Any,
) -> OperationResult:
    document = Document(input_path)
    runs = [run for paragraph in _paragraphs(document, selector) for run in paragraph.runs]
    for run in runs:
        font = run.font
        if "font_family" in formatting:
            set_word_font(font, formatting["font_family"])
        if "font_size_pt" in formatting:
            font.size = Pt(float(formatting["font_size_pt"]))
        for key in ("bold", "italic", "underline", "strike"):
            if key in formatting:
                setattr(run, key, bool(formatting[key]))
        if "superscript" in formatting:
            font.superscript = bool(formatting["superscript"])
            if formatting["superscript"]:
                font.subscript = False
        if "subscript" in formatting:
            font.subscript = bool(formatting["subscript"])
            if formatting["subscript"]:
                font.superscript = False
        if "highlight" in formatting:
            value = str(formatting["highlight"]).lower()
            if value not in _HIGHLIGHTS:
                raise ValueError(f"Unsupported highlight color: {value}")
            font.highlight_color = _HIGHLIGHTS[value]
        if "font_color" in formatting:
            value = str(formatting["font_color"]).lstrip("#")
            if len(value) != 6:
                raise ValueError("font_color must be a six-digit RGB value")
            font.color.rgb = RGBColor.from_string(value.upper())
        for key in ("small_caps", "all_caps", "hidden"):
            if key in formatting:
                setattr(font, key, bool(formatting[key]))

    output = Path(output_path).resolve()
    if not dry_run:
        atomic_save(document, output)
    return OperationResult(
        status="DRY_RUN" if dry_run else "SUCCESS",
        operation="format.run",
        backend_used="python-docx",
        fidelity=Fidelity.HIGH,
        output_path=None if dry_run else output,
        data={"runs_formatted": len(runs)},
    )


def format_paragraphs(
    input_path: str | Path,
    *,
    output_path: str | Path,
    selector=None,
    dry_run: bool = False,
    **formatting: Any,
) -> OperationResult:
    document = Document(input_path)
    paragraphs = _paragraphs(document, selector)
    for paragraph in paragraphs:
        fmt = paragraph.paragraph_format
        if "alignment" in formatting:
            value = str(formatting["alignment"]).lower()
            if value not in _ALIGNMENTS:
                raise ValueError(f"Unsupported alignment: {value}")
            paragraph.alignment = _ALIGNMENTS[value]
        for key, attribute in (
            ("left_indent_cm", "left_indent"),
            ("right_indent_cm", "right_indent"),
            ("first_line_indent_cm", "first_line_indent"),
        ):
            if key in formatting:
                setattr(fmt, attribute, Cm(float(formatting[key])))
        if "hanging_indent_cm" in formatting:
            fmt.first_line_indent = Cm(-abs(float(formatting["hanging_indent_cm"])))
        if "space_before_pt" in formatting:
            fmt.space_before = Pt(float(formatting["space_before_pt"]))
        if "space_after_pt" in formatting:
            fmt.space_after = Pt(float(formatting["space_after_pt"]))
        if "line_spacing" in formatting:
            fmt.line_spacing = float(formatting["line_spacing"])
        if "exact_line_spacing_pt" in formatting:
            fmt.line_spacing = Pt(float(formatting["exact_line_spacing_pt"]))
            fmt.line_spacing_rule = WD_LINE_SPACING.EXACTLY
        for key, attribute in (
            ("keep_with_next", "keep_with_next"),
            ("keep_lines_together", "keep_together"),
            ("page_break_before", "page_break_before"),
            ("widow_orphan", "widow_control"),
        ):
            if key in formatting:
                setattr(fmt, attribute, bool(formatting[key]))

    output = Path(output_path).resolve()
    if not dry_run:
        atomic_save(document, output)
    return OperationResult(
        status="DRY_RUN" if dry_run else "SUCCESS",
        operation="format.paragraph",
        backend_used="python-docx",
        fidelity=Fidelity.HIGH,
        output_path=None if dry_run else output,
        data={"paragraphs_formatted": len(paragraphs)},
    )
