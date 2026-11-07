"""Detect verbatim code paragraphs so prose checks do not treat them as body text.

Source-code listings in academic reports are reproduced exactly: they contain
bracket subscripts such as ``job.payload['name']`` and Jinja2 markers such as
``{{ vlan_id }}``, and they use a monospace face. Prose checks (draft
placeholders, body font and size, line spacing) must skip them. A paragraph is
code when its style is a known code style, or when every visible run is set in
a monospace font.
"""

from __future__ import annotations

from typing import Any

CODE_STYLE_NAMES = frozenset({
    "code",
    "code listing",
    "source code",
    "verbatim",
    "preformatted",
    "html preformatted",
    "plain text",
    "macro text",
})

MONOSPACE_FONTS = frozenset({
    "courier",
    "courier new",
    "consolas",
    "lucida console",
    "menlo",
    "monaco",
    "cascadia mono",
    "cascadia code",
    "source code pro",
})


def is_code_style_name(name: str | None) -> bool:
    return bool(name) and name.strip().lower() in CODE_STYLE_NAMES


def is_code_paragraph(paragraph: Any) -> bool:
    style = getattr(paragraph, "style", None)
    if style is not None and is_code_style_name(getattr(style, "name", None)):
        return True
    runs = [run for run in paragraph.runs if run.text.strip()]
    if not runs:
        return False
    style_font = None
    if style is not None and getattr(style, "font", None) is not None:
        style_font = style.font.name
    for run in runs:
        face = run.font.name or style_font
        if not face or face.strip().lower() not in MONOSPACE_FONTS:
            return False
    return True
