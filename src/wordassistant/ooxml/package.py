"""Safe unpack, pack and structural validation for DOCX packages.

Untrusted packages are read defensively: entry names must be relative and must
not climb out of the destination, symlink entries are refused, and extraction
is bounded by entry count and total uncompressed size.
"""

from __future__ import annotations

import difflib
import hashlib
import os
import posixpath
import re
import stat
import tempfile
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from lxml import etree

MAX_ENTRIES = 5000
MAX_UNCOMPRESSED_BYTES = 512 * 1024 * 1024
CONTENT_TYPES_PART = "[Content_Types].xml"
WML_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
XML_NS = "http://www.w3.org/XML/1998/namespace"
PACKAGE_RELS_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CONTENT_TYPES_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
_DRIVE_RE = re.compile(r"^[A-Za-z]:")


class OOXMLError(ValueError):
    """Raised when a package is unsafe, malformed or cannot be written."""


@dataclass(frozen=True)
class PartInfo:
    name: str
    size: int
    sha256: str


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _checked_member_name(name: str) -> str:
    if not name or name.startswith("/") or "\\" in name or _DRIVE_RE.match(name):
        raise OOXMLError(f"unsafe package entry name: {name!r}")
    if any(part == ".." for part in PurePosixPath(name).parts):
        raise OOXMLError(f"package entry climbs out of its root: {name!r}")
    return name


def _is_symlink_entry(info: zipfile.ZipInfo) -> bool:
    return stat.S_ISLNK(info.external_attr >> 16)


def unpack_docx(source: str | Path, destination: str | Path) -> list[PartInfo]:
    """Extract a DOCX into an empty (or absent) directory."""
    src = Path(source)
    dest = Path(destination)
    if not src.is_file():
        raise FileNotFoundError(f"DOCX not found: {src}")
    if dest.exists() and any(dest.iterdir()):
        raise OOXMLError(f"destination must be empty: {dest}")
    dest.mkdir(parents=True, exist_ok=True)
    root = dest.resolve()
    parts: list[PartInfo] = []
    total = 0
    with zipfile.ZipFile(src) as archive:
        infos = archive.infolist()
        if len(infos) > MAX_ENTRIES:
            raise OOXMLError(f"package has {len(infos)} entries; limit is {MAX_ENTRIES}")
        for info in infos:
            name = _checked_member_name(info.filename)
            if info.is_dir():
                continue
            if _is_symlink_entry(info):
                raise OOXMLError(f"symlink entry refused: {name}")
            total += info.file_size
            if total > MAX_UNCOMPRESSED_BYTES:
                raise OOXMLError("package exceeds the uncompressed size limit")
            target = (dest / name).resolve()
            if root not in target.parents:
                raise OOXMLError(f"package entry escapes destination: {name}")
            data = archive.read(info)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            parts.append(PartInfo(name=name, size=len(data), sha256=_sha256(data)))
    return parts


def _package_order(relative: str) -> tuple[int, str]:
    if relative == CONTENT_TYPES_PART:
        return (0, relative)
    if relative == "_rels/.rels":
        return (1, relative)
    return (2, relative)


def pack_directory(source_dir: str | Path, output: str | Path) -> dict[str, Any]:
    """Zip an unpacked package. XML and relationship parts must be well formed."""
    root = Path(source_dir)
    if not (root / CONTENT_TYPES_PART).is_file():
        raise OOXMLError(f"{CONTENT_TYPES_PART} is missing from {root}")
    files: list[Path] = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise OOXMLError(f"symlink refused while packing: {path.name}")
        if path.is_file():
            files.append(path)
    relatives = [p.relative_to(root).as_posix() for p in files]
    for path, relative in zip(files, relatives):
        if Path(relative).suffix.lower() in {".xml", ".rels"}:
            try:
                etree.parse(str(path))
            except etree.XMLSyntaxError as exc:
                raise OOXMLError(f"malformed XML in {relative}: {exc}") from exc
    order = sorted(zip(relatives, files), key=lambda item: _package_order(item[0]))
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, staging_name = tempfile.mkstemp(
        prefix=f".{target.stem}.pack-", suffix=".docx", dir=target.parent
    )
    os.close(descriptor)
    staging = Path(staging_name)
    try:
        with zipfile.ZipFile(staging, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for relative, path in order:
                archive.write(path, arcname=relative)
        if staging.stat().st_size == 0:
            raise OOXMLError("packing produced an empty file")
        os.replace(staging, target)
    finally:
        staging.unlink(missing_ok=True)
    return {"output": str(target), "entries": len(order), "size_bytes": target.stat().st_size}


def _zip_text(archive: zipfile.ZipFile, name: str) -> bytes | None:
    try:
        return archive.read(name)
    except KeyError:
        return None


def _resolve_relationship_target(rels_part: str, target: str) -> str:
    """Resolve a relationship target against the part that owns the .rels file."""
    if rels_part == "_rels/.rels":
        base = ""
    else:
        owner_dir = posixpath.dirname(posixpath.dirname(rels_part))
        owner = posixpath.join(owner_dir, posixpath.basename(rels_part)[: -len(".rels")])
        base = posixpath.dirname(owner)
    if target.startswith("/"):
        return target.lstrip("/")
    return posixpath.normpath(posixpath.join(base, target))


def _visible_paragraph_texts(root: etree._Element, *, baseline: bool) -> list[str]:
    """Text per paragraph. baseline=True keeps deleted text and drops inserted text."""
    texts: list[str] = []
    for paragraph in root.iter(f"{{{WML_NS}}}p"):
        chunks: list[str] = []
        for node in paragraph.iter(f"{{{WML_NS}}}t", f"{{{WML_NS}}}delText"):
            inside_ins = any(a.tag == f"{{{WML_NS}}}ins" for a in node.iterancestors())
            inside_del = any(a.tag == f"{{{WML_NS}}}del" for a in node.iterancestors())
            if node.tag == f"{{{WML_NS}}}t" and baseline and inside_ins:
                continue
            if node.tag == f"{{{WML_NS}}}t" and not baseline and inside_del:
                continue
            chunks.append(node.text or "")
        texts.append("".join(chunks))
    return texts


def _schema_check(document_xml: bytes, schema_dir: Path) -> dict[str, Any]:
    wml = schema_dir / "wml.xsd"
    if not wml.is_file():
        return {"status": "NOT_RUN", "reason": f"wml.xsd not found in {schema_dir}"}
    try:
        schema = etree.XMLSchema(etree.parse(str(wml)))
    except (etree.XMLSchemaParseError, etree.XMLSyntaxError) as exc:
        return {"status": "NOT_RUN", "reason": f"schema could not be loaded: {exc}"}
    document = etree.fromstring(document_xml)
    if schema.validate(document):
        return {"status": "PASS", "reason": "word/document.xml validates against wml.xsd"}
    errors = [str(error.message) for error in list(schema.error_log)[:10]]
    return {"status": "FAIL", "reason": "schema violations", "errors": errors}


def validate_docx(
    path: str | Path,
    *,
    original: str | Path | None = None,
    schema_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Check package structure, relationships and optional tracked-text drift.

    The result is a report, not a delivery verdict. ``valid`` is False when any
    error-level issue is found. Schema validation is reported as NOT_RUN unless
    a directory containing wml.xsd is supplied.
    """
    target = Path(path)
    issues: list[dict[str, str]] = []

    def add(severity: str, code: str, message: str) -> None:
        issues.append({"severity": severity, "code": code, "message": message})

    if not target.is_file():
        raise FileNotFoundError(f"DOCX not found: {target}")
    try:
        archive = zipfile.ZipFile(target)
    except zipfile.BadZipFile as exc:
        raise OOXMLError(f"not a valid DOCX/ZIP package: {target.name}") from exc
    with archive:
        bad_member = archive.testzip()
        if bad_member is not None:
            add("error", "zip_crc", f"CRC mismatch in {bad_member}")
        names = archive.namelist()
        for info in archive.infolist():
            try:
                _checked_member_name(info.filename)
            except OOXMLError as exc:
                add("error", "unsafe_entry", str(exc))
            if _is_symlink_entry(info):
                add("error", "symlink_entry", f"symlink entry: {info.filename}")
        name_set = set(names)
        content_types = _zip_text(archive, CONTENT_TYPES_PART)
        if content_types is None:
            add("error", "content_types_missing", "[Content_Types].xml is missing")
        else:
            ct_root = etree.fromstring(content_types)
            defaults = {
                el.get("Extension", "").lower()
                for el in ct_root.iter(f"{{{CONTENT_TYPES_NS}}}Default")
            }
            overrides = {
                el.get("PartName", "").lstrip("/")
                for el in ct_root.iter(f"{{{CONTENT_TYPES_NS}}}Override")
            }
            for name in names:
                if name.endswith("/") or name == CONTENT_TYPES_PART:
                    continue
                base_name = posixpath.basename(name)
                # posixpath.splitext treats ".rels" as a bare name, so split on the dot here.
                suffix = base_name.rsplit(".", 1)[1].lower() if "." in base_name else ""
                if name not in overrides and suffix not in defaults:
                    add("error", "content_type_missing", f"no content type for {name}")
        if _zip_text(archive, "_rels/.rels") is None:
            add("error", "package_rels_missing", "_rels/.rels is missing")
        for name in names:
            if not (name.endswith(".xml") or name.endswith(".rels")):
                continue
            try:
                etree.fromstring(archive.read(name))
            except etree.XMLSyntaxError as exc:
                add("error", "xml_malformed", f"{name}: {exc}")
        for name in names:
            if not name.endswith(".rels"):
                continue
            try:
                rels_root = etree.fromstring(archive.read(name))
            except etree.XMLSyntaxError:
                continue
            for rel in rels_root.iter(f"{{{PACKAGE_RELS_NS}}}Relationship"):
                if rel.get("TargetMode") == "External":
                    continue
                resolved = _resolve_relationship_target(name, rel.get("Target", ""))
                if resolved not in name_set:
                    add("error", "relationship_target_missing", f"{name} -> {resolved}")
        document_xml = _zip_text(archive, "word/document.xml")
        doc_root = None
        if document_xml is None:
            add("error", "document_part_missing", "word/document.xml is missing")
            schema_result = {"status": "NOT_RUN", "reason": "word/document.xml is missing"}
            tracked = {"status": "NOT_RUN", "reason": "no document part"}
        else:
            try:
                doc_root = etree.fromstring(document_xml)
            except etree.XMLSyntaxError:
                schema_result = {"status": "NOT_RUN", "reason": "word/document.xml is malformed"}
                tracked = {"status": "NOT_RUN", "reason": "word/document.xml is malformed"}
        if doc_root is not None:
            if doc_root.tag != f"{{{WML_NS}}}document":
                add("error", "document_root", "word/document.xml root is not w:document")
            schema_result = (
                _schema_check(document_xml, Path(schema_dir))
                if schema_dir is not None
                else {"status": "NOT_RUN", "reason": "no --schema-dir supplied"}
            )
            if schema_result["status"] == "FAIL":
                add("error", "schema_invalid", schema_result["reason"])
            tracked = {"status": "NOT_RUN", "reason": "no --original supplied"}
            if original is not None:
                tracked = _tracked_drift(doc_root, Path(original), add)

    error_count = sum(1 for issue in issues if issue["severity"] == "error")
    return {
        "file": str(target),
        "valid": error_count == 0,
        "error_count": error_count,
        "issues": issues,
        "schema": schema_result,
        "tracked_text": tracked,
    }


def _tracked_drift(doc_root: etree._Element, original: Path, add) -> dict[str, Any]:
    if not original.is_file():
        add("error", "original_missing", f"original not found: {original}")
        return {"status": "FAIL", "reason": "original missing"}
    with zipfile.ZipFile(original) as archive:
        raw = _zip_text(archive, "word/document.xml")
    if raw is None:
        add("error", "original_document_missing", "original has no word/document.xml")
        return {"status": "FAIL", "reason": "original has no document part"}
    before = _visible_paragraph_texts(etree.fromstring(raw), baseline=True)
    after = _visible_paragraph_texts(doc_root, baseline=True)
    if before == after:
        return {"status": "PASS", "reason": "no untracked text change", "changed_paragraphs": []}
    changed: list[int] = []
    matcher = difflib.SequenceMatcher(a=before, b=after, autojunk=False)
    for tag, i1, i2, _j1, _j2 in matcher.get_opcodes():
        if tag != "equal":
            changed.extend(range(i1, i2))
    add(
        "error",
        "untracked_text_change",
        f"{len(changed)} paragraph(s) of the original changed without w:ins/w:del markup",
    )
    return {
        "status": "FAIL",
        "reason": "untracked text change",
        "changed_paragraphs": changed[:20],
        "changed_paragraph_count": len(changed),
    }


def part_inventory(path: str | Path) -> list[dict[str, Any]]:
    """Return name, size and hash for every package entry (read-only)."""
    with zipfile.ZipFile(path) as archive:
        result = []
        for info in archive.infolist():
            if info.is_dir():
                continue
            data = archive.read(info)
            result.append(asdict(PartInfo(name=info.filename, size=len(data), sha256=_sha256(data))))
    return result
