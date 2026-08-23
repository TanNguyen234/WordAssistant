from __future__ import annotations
from .backends.status import get_backend_status
from .doctor import status

def capabilities() -> dict:
    doc_status = status()
    backend_status = get_backend_status()
    return {
        'core': {
            'ready': doc_status['core_ready'],
            'commands': ['doctor', 'capabilities', 'profiles', 'init', 'inspect', 'context', 'scaffold', 'replace', 'validate', 'verify', 'render', 'evidence'],
            'api_key_required': False
        },
        'advanced_word': backend_status
    }
