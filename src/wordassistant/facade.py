from __future__ import annotations

from pathlib import Path
from typing import Callable

from .document.structure import inspect_document
from .document.verify import verify_document
from .operations.models import OperationRequest
from .operations import (
    content_controls,
    equations,
    fields,
    headers_footers,
    images,
    lists,
    notes,
    page_numbers,
    properties,
    protection,
    references,
    sections,
    tables,
)
from .operations.citations import generate_bibliography, insert_citation, list_citations, remove_citation
from .operations.paragraph import format_paragraphs, format_runs
from .operations.styles import apply_style, clone_style, create_style, delete_style, update_style
from .operations.text import edit_text


_OPERATIONS: dict[str, Callable] = {
    "text.edit": edit_text,
    "format.run": format_runs,
    "format.paragraph": format_paragraphs,
    "style.create": create_style,
    "style.update": update_style,
    "style.clone": clone_style,
    "style.apply": apply_style,
    "style.delete": delete_style,
    "list.create": lists.create_list,
    "list.set_level": lists.set_list_level,
    "list.restart": lists.restart_numbering,
    "list.continue": lists.continue_numbering,
    "heading.numbering_apply": lists.apply_heading_numbering,
    "heading.numbering_remove": lists.remove_heading_numbering,
    "table.create": tables.create_table,
    "table.delete": tables.delete_table,
    "table.insert_row": tables.insert_row,
    "table.delete_row": tables.delete_row,
    "table.insert_column": tables.insert_column,
    "table.delete_column": tables.delete_column,
    "table.set_cell": tables.set_cell_text,
    "table.set_row": tables.set_row_text,
    "table.set_column": tables.set_column_text,
    "table.merge": tables.merge_cells,
    "table.layout": tables.set_table_layout,
    "image.insert": images.insert_image,
    "image.resize": images.resize_image,
    "image.remove": images.remove_image,
    "image.replace": images.replace_image,
    "image.metadata": images.set_image_metadata,
    "section.add": sections.add_section_break,
    "section.layout": sections.set_section_layout,
    "section.link": sections.link_header_footer,
    "header-footer.set_text": headers_footers.set_header_footer_text,
    "page-number.apply": page_numbers.configure_page_numbers,
    "field.insert": fields.insert_field,
    "field.remove": fields.remove_fields,
    "field.lock": fields.lock_fields,
    "field.unlock": lambda source, **kwargs: fields.lock_fields(source, locked=False, **kwargs),
    "toc.insert": fields.insert_toc,
    "caption.insert": fields.insert_caption,
    "bookmark.create": references.create_bookmark,
    "bookmark.rename": references.rename_bookmark,
    "bookmark.delete": references.delete_bookmark,
    "reference.hyperlink": references.insert_hyperlink,
    "reference.cross_reference": references.insert_cross_reference,
    "citation.insert": insert_citation,
    "citation.remove": remove_citation,
    "bibliography.generate": generate_bibliography,
    "properties.set": properties.set_properties,
    "protection.protect": protection.protect_document,
    "protection.unprotect": protection.unprotect_document,
    "equation.insert": equations.insert_equation,
    "content-control.create": content_controls.create_content_control,
    "content-control.set": content_controls.set_content_control_value,
    "content-control.delete": content_controls.delete_content_control,
}

_READ_OPERATIONS: dict[str, Callable] = {
    "field.inspect": fields.inspect_fields,
    "bookmark.inspect": references.inspect_bookmarks,
    "citation.list": list_citations,
    "page-number.inspect": page_numbers.inspect_page_numbers,
    "heading.numbering_inspect": lists.inspect_heading_numbering,
    "properties.get": properties.get_properties,
    "protection.inspect": protection.inspect_protection,
    "content-control.list": content_controls.list_content_controls,
}


class _Namespace:
    def __init__(self, document: "WordDocument", prefix: str, aliases: dict[str, str] | None = None):
        self.document = document
        self.prefix = prefix
        self.aliases = aliases or {}

    def __getattr__(self, name: str):
        operation = self.aliases.get(name, f"{self.prefix}.{name}")

        def invoke(*, output=None, **options):
            return self.document.execute(operation, output=output, **options)

        return invoke


class WordDocument:
    """Stable high-level Python facade for deterministic Word operations."""

    def __init__(self, path: str | Path):
        self.path = Path(path).resolve()
        if not self.path.is_file():
            raise FileNotFoundError(self.path)
        self.tables = _Namespace(self, "table")
        self.text = _Namespace(self, "text")
        self.formatting = _Namespace(self, "format")
        self.styles = _Namespace(self, "style")
        self.images = _Namespace(self, "image")
        self.sections = _Namespace(self, "section")
        self.fields = _Namespace(self, "field")
        self.page_numbers = _Namespace(self, "page-number")
        self.bookmarks = _Namespace(self, "bookmark")
        self.references = _Namespace(self, "reference")
        self.citations = _Namespace(self, "citation")
        self.properties = _Namespace(self, "properties")
        self.protection = _Namespace(self, "protection")
        self.content_controls = _Namespace(self, "content-control")
        self.lists = _Namespace(self, "list")
        self.comments = _Namespace(self, "comment")
        self.revisions = _Namespace(self, "revision")
        self.headings = _Namespace(self, "heading", {"apply_numbering": "heading.numbering_apply", "remove_numbering": "heading.numbering_remove", "inspect_numbering": "heading.numbering_inspect"})

    @classmethod
    def open(cls, path: str | Path) -> "WordDocument":
        return cls(path)

    def inspect(self) -> dict:
        return inspect_document(self.path)

    def verify(self, **options) -> dict:
        return verify_document(self.path, **options)

    def execute(
        self,
        operation: str,
        *,
        output=None,
        selector=None,
        dry_run=False,
        checkpoint=None,
        **options,
    ):
        from .execution import ExecutionService

        result = ExecutionService.default().execute(
            OperationRequest(
                operation,
                input_path=self.path,
                output_path=Path(output) if output is not None else None,
                selector=selector,
                options=options,
                dry_run=dry_run,
                checkpoint=checkpoint,
            )
        )
        if operation in _READ_OPERATIONS:
            return result.data.get("result")
        if getattr(result, "output_path", None):
            self.path = Path(result.output_path).resolve()
        return result
