"""Bounded, deterministic OOXML package operations.

This package integrates the document-skills DOCX workflow into WordAssistant as
explicit commands: unpack a package safely, edit its XML, pack it again, merge
fragmented runs, accept tracked changes, and check package structure. Every
command writes to an output copy. None of them calls Word or LibreOffice.
"""

from .package import (
    OOXMLError,
    pack_directory,
    unpack_docx,
    validate_docx,
)
from .revisions import accept_changes_docx
from .runs import merge_runs_docx

__all__ = [
    "OOXMLError",
    "accept_changes_docx",
    "merge_runs_docx",
    "pack_directory",
    "unpack_docx",
    "validate_docx",
]
