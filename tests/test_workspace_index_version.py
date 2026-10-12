import json
import pytest

from wordassistant.document.model import DocumentSection
from wordassistant.workspace import get_cached_document_index, put_cached_document_index


def test_legacy_heading_cache_is_rebuilt_after_indexer_upgrade(tmp_path):
    cache = tmp_path / '.wordassistant' / 'cache'
    cache.mkdir(parents=True)
    (cache / 'document-hash.json').write_text(json.dumps([{
        'section_id': '__preamble__', 'title': 'Preamble',
        'text': 'Custom heading previously merged here', 'level': 0,
    }]), encoding='utf-8')
    assert get_cached_document_index(tmp_path, 'document-hash') is None


def test_current_heading_index_cache_round_trips(tmp_path):
    (tmp_path / '.wordassistant').mkdir()
    sections = [DocumentSection('acknowledgements', 'Acknowledgements', 'Text', 1)]
    put_cached_document_index(tmp_path, 'document-hash', sections)
    assert get_cached_document_index(tmp_path, 'document-hash') == sections


@pytest.mark.parametrize('version', [0, 1, 999])
def test_other_index_schemas_are_cache_misses(tmp_path, version):
    cache = tmp_path / '.wordassistant' / 'cache'
    cache.mkdir(parents=True)
    (cache / 'document-hash.json').write_text(json.dumps({
        'schema_version': version, 'sections': [],
    }), encoding='utf-8')
    assert get_cached_document_index(tmp_path, 'document-hash') is None
