from __future__ import annotations


GENERIC_FAMILIES = (
    "edit",
    "format",
    "list",
    "table",
    "image",
    "section",
    "page-number",
    "field",
    "toc",
    "caption",
    "reference",
    "comment",
    "revision",
    "protect",
    "properties",
    "mail-merge",
)


OPERATION_ALIASES = {
    ("edit", "replace"): "text.edit",
    ("edit", "append"): "text.edit",
    ("edit", "prepend"): "text.edit",
    ("edit", "insert"): "text.edit",
    ("format", "run"): "format.run",
    ("format", "paragraph"): "format.paragraph",
    ("format", "style_create"): "style.create",
    ("format", "style_update"): "style.update",
    ("format", "style_clone"): "style.clone",
    ("format", "style_apply"): "style.apply",
    ("format", "style_delete"): "style.delete",
    ("list", "heading_numbering_apply"): "heading.numbering_apply",
    ("list", "heading_numbering_remove"): "heading.numbering_remove",
    ("list", "heading_numbering_inspect"): "heading.numbering_inspect",
    ("page-number", "apply"): "page-number.apply",
    ("page-number", "inspect"): "page-number.inspect",
    ("reference", "bookmark_create"): "bookmark.create",
    ("reference", "bookmark_rename"): "bookmark.rename",
    ("reference", "bookmark_delete"): "bookmark.delete",
    ("reference", "bookmark_inspect"): "bookmark.inspect",
    ("reference", "hyperlink"): "reference.hyperlink",
    ("reference", "cross_reference"): "reference.cross_reference",
    ("reference", "citation_insert"): "citation.insert",
    ("reference", "citation_remove"): "citation.remove",
    ("reference", "citation_list"): "citation.list",
    ("reference", "bibliography"): "bibliography.generate",
    ("reference", "equation_insert"): "equation.insert",
    ("field", "content_control_create"): "content-control.create",
    ("field", "content_control_set"): "content-control.set",
    ("field", "content_control_delete"): "content-control.delete",
    ("field", "content_control_list"): "content-control.list",
    ("section", "header_text"): "header-footer.set_text",
    ("section", "footer_text"): "header-footer.set_text",
    ("protect", "protect"): "protection.protect",
    ("protect", "unprotect"): "protection.unprotect",
    ("protect", "inspect"): "protection.inspect",
    ("properties", "set"): "properties.set",
    ("properties", "get"): "properties.get",
    ("field", "update_all"): "field.update_all",
    ("mail-merge", "execute"): "mail-merge.execute",
    ("image", "chart_insert"): "chart.insert",
    ("protect", "native"): "protect.native",
}


NATIVE_OPTION_CONTRACTS = {
    "field.update_all": [],
    "comment.create": [
        ("text", True, None, "string"),
        ("start", False, 0, "integer"),
        ("end", False, None, "integer"),
        ("author", False, None, "string"),
    ],
    "comment.list": [],
    "comment.delete": [("index", True, None, "integer")],
    "comment.reply": [("index", True, None, "integer"), ("text", True, None, "string")],
    "comment.resolve": [("index", True, None, "integer")],
    "comment.reopen": [("index", True, None, "integer")],
    "revision.enable": [],
    "revision.disable": [],
    "revision.list": [],
    "revision.accept": [("index", True, None, "integer")],
    "revision.reject": [("index", True, None, "integer")],
    "revision.accept_all": [],
    "revision.reject_all": [],
    "protect.native": [
        ("type", True, None, "integer"),
        ("password", False, "", "string"),
    ],
    "mail-merge.execute": [("data_source", True, None, "path")],
    "chart.insert": [
        ("chart_type", False, 51, "integer"),
        ("title", False, "Chart", "string"),
    ],
}


OPERATION_OPTION_OVERRIDES = {
    "image.insert": [
        ("image_path", True, None, "path"),
        ("width_cm", False, None, "number"),
        ("height_cm", False, None, "number"),
        ("alt_text", False, None, "string"),
        ("title", False, None, "string"),
        ("caption", False, None, "string"),
        ("caption_label", False, "Figure", "string"),
        ("caption_sequence", False, None, "string"),
        ("caption_chapter_number", False, None, "integer"),
        ("caption_separator", False, ".", "string"),
        ("placement", False, "after", "string"),
        ("alignment", False, "center", "string"),
        ("preserve_aspect_ratio", False, True, "boolean"),
        ("auto_shrink", False, True, "boolean"),
        ("inline", False, True, "boolean"),
    ],
    "format.run": [
        ("font_family", False, None, "string"),
        ("font_size_pt", False, None, "number"),
        *[(name, False, None, "boolean") for name in (
            "bold", "italic", "underline", "strike", "superscript", "subscript",
            "small_caps", "all_caps", "hidden",
        )],
        ("highlight", False, None, "string"),
        ("font_color", False, None, "string"),
    ],
    "format.paragraph": [
        ("alignment", False, None, "string"),
        *[(name, False, None, "number") for name in (
            "left_indent_cm", "right_indent_cm", "first_line_indent_cm",
            "hanging_indent_cm", "space_before_pt", "space_after_pt",
            "line_spacing", "exact_line_spacing_pt",
        )],
        *[(name, False, None, "boolean") for name in (
            "keep_with_next", "keep_lines_together", "page_break_before", "widow_orphan",
        )],
    ],
    "style.create": [
        ("name", True, None, "string"),
        ("base_style", False, "Normal", "string"),
        ("font_family", False, None, "string"),
        ("font_size_pt", False, None, "number"),
        ("bold", False, None, "boolean"),
        ("italic", False, None, "boolean"),
    ],
    "style.update": [
        ("name", True, None, "string"),
        ("font_family", False, None, "string"),
        ("font_size_pt", False, None, "number"),
        ("bold", False, None, "boolean"),
        ("italic", False, None, "boolean"),
        ("font_color", False, None, "string"),
        ("left_indent_pt", False, None, "number"),
        ("first_line_indent_pt", False, None, "number"),
    ],
    "properties.set": [
        ("custom", False, None, "object"),
        *[(name, False, None, "string") for name in (
            "title", "subject", "author", "keywords", "category", "comments",
            "last_modified_by",
        )],
    ],
    "field.unlock": [("field_type", False, None, "string")],
}


TEXT_ROUTE_OPTION_CONTRACTS = {
    "replace": [
        ("pattern", True, None, "string"),
        ("replacement", False, "", "string"),
        ("regex", False, False, "boolean"),
        ("case_sensitive", False, True, "boolean"),
        ("whole_word", False, False, "boolean"),
        ("max_count", False, None, "integer"),
    ],
    "append": [("text", True, None, "string")],
    "prepend": [("text", True, None, "string")],
    "insert": [("text", True, None, "string")],
}


def validate_overridden_options(operation: str, options: dict) -> None:
    """Enforce explicit contracts for operations whose callables use **kwargs."""
    contract = OPERATION_OPTION_OVERRIDES.get(operation)
    if contract is None:
        return
    allowed = {name for name, *_ in contract}
    unknown = sorted(set(options) - allowed)
    if unknown:
        raise ValueError(
            f"Unsupported options for {operation}: " + ", ".join(unknown)
        )
    missing = [name for name, required, *_ in contract if required and name not in options]
    if missing:
        raise ValueError(
            f"Missing required options for {operation}: " + ", ".join(missing)
        )
    specs = {name: type_name for name, _, _, type_name in contract}
    for name, value in options.items():
        expected = specs[name]
        valid = (
            (expected in {"string", "path"} and isinstance(value, str))
            or (expected == "boolean" and isinstance(value, bool))
            or (expected == "integer" and isinstance(value, int) and not isinstance(value, bool))
            or (
                expected == "number"
                and isinstance(value, (int, float))
                and not isinstance(value, bool)
            )
            or (expected == "object" and isinstance(value, dict))
            or (expected.startswith("array") and isinstance(value, list))
            or expected == "any"
        )
        if not valid:
            raise ValueError(
                f"Option {name!r} for {operation} must be {expected}"
            )


def cli_routes_for(operation: str) -> list[dict[str, str | None]]:
    routes = [
        {"family": family, "action": action.replace("_", "-")}
        for (family, action), mapped in OPERATION_ALIASES.items()
        if mapped == operation
    ]
    area, _, action = operation.partition(".")
    if area in GENERIC_FAMILIES and not routes:
        routes.append({"family": area, "action": action.replace("_", "-")})
    if operation == "compare.documents":
        routes.append({"family": "compare", "action": None})
    elif operation == "merge.documents":
        routes.append({"family": "merge", "action": None})
    elif operation == "render.pdf":
        routes.append({"family": "render", "action": None})
    return routes
