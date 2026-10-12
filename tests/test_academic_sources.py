from __future__ import annotations

import hashlib
import json

import pytest
from docx import Document

from wordassistant.evidence.registry import EvidenceError, EvidenceRegistry
from wordassistant.operations.citations import insert_citation
from wordassistant.evidence.research import (
    SourceResearchError,
    _source_record,
    download_open_access_pdf,
    import_crossref_doi,
    find_open_access,
    review_downloaded_source,
    search_crossref,
    search_source_excerpts,
)


def _crossref_item():
    return {
        "DOI": "10.5555/example.1",
        "title": ["A source title"],
        "author": [{"given": "Văn A", "family": "Nguyễn"}],
        "language": "vi",
        "type": "journal-article",
        "published": {"date-parts": [[2024, 5, 1]]},
        "container-title": ["Tạp chí Khoa học"],
        "volume": "12",
        "issue": "2",
        "page": "21-34",
        "publisher": "Nhà xuất bản thử nghiệm",
    }


def _metadata_transport(data):
    body = json.dumps(data).encode("utf-8")

    def request(url, headers, max_bytes):
        assert "email=" not in url
        return url, {"Content-Type": "application/json"}, body

    return request


def test_crossref_discovery_is_a_candidate_and_vietnamese_sort_key_uses_given_name(tmp_path):
    record = _source_record(_crossref_item())
    assert record["review_status"] == "candidate"
    assert record["author_sort_key"] == "Văn A"
    assert record["authors"] == ["Nguyễn Văn A"]
    assert record["container_title"] == "Tạp chí Khoa học"
    assert record["volume"] == "12"
    assert record["issue"] == "2"
    assert record["pages"] == "21-34"
    assert record["publisher"] == "Nhà xuất bản thử nghiệm"

    english_item = _crossref_item()
    english_item["language"] = "en"
    english_item["author"] = [{"given": "John Paul", "family": "Smith"}]
    english = _source_record(english_item)
    assert english["authors"] == ["Smith J.P."]
    assert english["author_sort_key"] == "Smith"

    search_transport = _metadata_transport({"message": {"items": [_crossref_item()]}})
    candidates = search_crossref("test query", transport=search_transport)
    assert len(candidates) == 1
    assert candidates[0]["doi"] == "10.5555/example.1"

    doi_transport = _metadata_transport({"message": _crossref_item()})
    registry_path = tmp_path / ".wordassistant" / "evidence.json"
    imported = import_crossref_doi(
        imported_doi := "10.5555/example.1",
        evidence_registry=registry_path,
        transport=doi_transport,
    )
    assert imported["doi"] == imported_doi
    with pytest.raises(EvidenceError, match="discovery metadata only"):
        EvidenceRegistry(registry_path).assert_citable(imported)

    source_docx = tmp_path / "draft.docx"
    Document().save(source_docx)
    with pytest.raises(EvidenceError, match="discovery metadata only"):
        insert_citation(
            source_docx,
            output_path=tmp_path / "cited.docx",
            evidence_registry=registry_path,
            evidence_id=imported["id"],
        )


def test_download_requires_an_explicit_license_and_records_source_hash(tmp_path):
    registry_path = tmp_path / ".wordassistant" / "evidence.json"
    record = _source_record(_crossref_item())
    record["oa_url"] = "https://repository.example.org/paper.pdf"
    EvidenceRegistry(registry_path).add(record)
    with pytest.raises(SourceResearchError, match="explicit supported reuse license"):
        download_open_access_pdf(record["id"], evidence_registry=registry_path)
    record["oa_license"] = "CC-BY-4.0"
    EvidenceRegistry(registry_path).add(record, replace=True)
    payload = b"%PDF-1.4\nsource bytes"

    def transport(url, headers, max_bytes):
        return url, {"Content-Type": "application/pdf", "Content-Length": str(len(payload))}, payload

    result = download_open_access_pdf(
        record["id"], evidence_registry=registry_path, transport=transport
    )
    updated = EvidenceRegistry(registry_path).get(record["id"])
    assert result["sha256"] == hashlib.sha256(payload).hexdigest()
    assert updated["source_file"] == f"{record['id']}.pdf"
    assert updated["source_sha256"] == result["sha256"]
    with pytest.raises(EvidenceError, match="discovery metadata only"):
        EvidenceRegistry(registry_path).assert_citable(updated)


def test_unpaywall_email_is_runtime_only_and_only_licensed_pdf_is_selected(tmp_path):
    registry_path = tmp_path / ".wordassistant" / "evidence.json"
    record = _source_record(_crossref_item())
    EvidenceRegistry(registry_path).add(record)
    body = json.dumps({
        "best_oa_location": {
            "url_for_pdf": "https://repository.example.org/article.pdf",
            "license": "https://creativecommons.org/licenses/by/4.0/",
        },
        "oa_locations": [],
    }).encode("utf-8")
    seen = {}

    def transport(url, headers, max_bytes):
        seen["url"] = url
        return url, {"Content-Type": "application/json"}, body

    result = find_open_access(
        record["id"],
        evidence_registry=registry_path,
        email="researcher@example.org",
        transport=transport,
    )
    saved = EvidenceRegistry(registry_path).get(record["id"])
    assert "email=researcher%40example.org" in seen["url"]
    assert "researcher@example.org" not in json.dumps(saved)
    assert result["license"].endswith("by/4.0/")
    assert saved["review_status"] == "candidate"


def test_download_refuses_unsafe_final_url_and_non_pdf_content(tmp_path):
    registry_path = tmp_path / ".wordassistant" / "evidence.json"
    record = _source_record(_crossref_item())
    record.update({"oa_url": "https://repository.example.org/paper.pdf", "oa_license": "CC-BY-4.0"})
    EvidenceRegistry(registry_path).add(record)

    def private_redirect(url, headers, max_bytes):
        return "https://127.0.0.1/private.pdf", {"Content-Type": "application/pdf"}, b"%PDF-1.4"

    with pytest.raises(SourceResearchError, match="IP addresses"):
        download_open_access_pdf(record["id"], evidence_registry=registry_path, transport=private_redirect)

    def html_response(url, headers, max_bytes):
        return url, {"Content-Type": "text/html"}, b"%PDF-1.4"

    with pytest.raises(SourceResearchError, match="content type"):
        download_open_access_pdf(record["id"], evidence_registry=registry_path, transport=html_response)


def test_review_requires_an_exact_source_excerpt_and_citable_hash(tmp_path, monkeypatch):
    import wordassistant.evidence.research as research

    registry_path = tmp_path / ".wordassistant" / "evidence.json"
    item = _crossref_item()
    item.pop("language")
    record = _source_record(item)
    record.update({"oa_url": "https://repository.example.org/paper.pdf", "oa_license": "CC-BY-4.0"})
    EvidenceRegistry(registry_path).add(record)
    payload = b"%PDF-1.4\nsource bytes"

    def transport(url, headers, max_bytes):
        return url, {"Content-Type": "application/pdf"}, payload

    download_open_access_pdf(record["id"], evidence_registry=registry_path, transport=transport)
    monkeypatch.setattr(
        research,
        "_extract_source_pages",
        lambda path: [("Page 1", "Results section: the measured value was 42 units.")],
    )
    excerpt_result = search_source_excerpts(
        record["id"],
        evidence_registry=registry_path,
        query="measured value was 42 units",
        context_chars=100,
    )
    assert excerpt_result["matches"][0]["location"] == "Page 1"
    assert "42 units" in excerpt_result["matches"][0]["excerpt"]

    with pytest.raises(SourceResearchError, match="Set the checked source language"):
        review_downloaded_source(
            record["id"],
            evidence_registry=registry_path,
            claim="The measured value was 42 units.",
            support_excerpt="the measured value was 42 units.",
            support_location="Page 1",
            reviewed_by="Researcher",
            confirm_support=True,
        )

    with pytest.raises(SourceResearchError, match="not found"):
        review_downloaded_source(
            record["id"],
            evidence_registry=registry_path,
            claim="The measured value was 42 units.",
            support_excerpt="The value was 24 units.",
            support_location="Results, paragraph 2",
            reviewed_by="Researcher",
            confirm_support=True,
            language="vi",
        )

    reviewed = review_downloaded_source(
        record["id"],
        evidence_registry=registry_path,
        claim="The measured value was 42 units.",
        support_excerpt="the measured value was 42 units.",
        support_location="Results, paragraph 2",
        reviewed_by="Researcher",
        confirm_support=True,
        language="vi",
    )
    registry = EvidenceRegistry(registry_path)
    reviewed_record = registry.get(record["id"])
    assert reviewed["review_status"] == "reviewed"
    assert reviewed_record["language"] == "vi"
    assert reviewed_record["authors"] == ["Nguyễn Văn A"]
    assert reviewed_record["author_sort_key"] == "Văn A"
    registry.assert_citable(reviewed_record)

    (registry_path.parent / "sources" / reviewed_record["source_file"]).write_bytes(b"changed")
    with pytest.raises(EvidenceError, match="hash changed"):
        registry.assert_citable(reviewed_record)
