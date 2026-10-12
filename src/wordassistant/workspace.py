from __future__ import annotations
from pathlib import Path
from typing import Any
import json
from wordassistant.document.model import DocumentSection

# Bump when indexing semantics change; DOCX hashes alone cannot invalidate
# section boundaries computed by older indexers.
DOCUMENT_INDEX_SCHEMA_VERSION = 2

ALLOWED_CONFIG_KEYS = {
    'schema_version',
    'profile',
    'variant',
    'primary_document',
    'context_budget',
    'language',
    'title',
    'author',
    'student',
    'supervisor'
}

def init_workspace(path: str | Path) -> Path:
    root = Path(path).resolve()
    wa = root / '.wordassistant'
    wa.mkdir(parents=True, exist_ok=True)
    
    project = wa / 'project.json'
    if not project.exists():
        project.write_text(
            json.dumps({
                'schema_version': 1,
                'profile': 'generic',
                'variant': 'default',
                'title': 'UNTITLED DOCUMENT',
                'author': '',
                'supervisor': '',
                'context_budget': 12000
            }, indent=2),
            encoding='utf-8'
        )
        
    ev = wa / 'evidence.json'
    if not ev.exists():
        ev.write_text('{}\n', encoding='utf-8')
        
    (wa / 'cache').mkdir(exist_ok=True)
    (wa / 'checkpoints').mkdir(exist_ok=True)
    (wa / 'profiles').mkdir(exist_ok=True)
    return wa

def find_workspace(start_path: str | Path | None = None) -> Path | None:
    curr = Path(start_path or Path.cwd()).resolve()
    for parent in [curr] + list(curr.parents):
        wa_dir = parent / '.wordassistant'
        if wa_dir.exists() and wa_dir.is_dir():
            return wa_dir
    return None

def load_project_config(start_path: str | Path | None = None) -> dict[str, Any]:
    wa = find_workspace(start_path)
    default_cfg: dict[str, Any] = {'schema_version': 1, 'profile': 'generic', 'variant': 'default', 'context_budget': 12000}
    if not wa:
        return default_cfg
    proj_file = wa / 'project.json'
    if not proj_file.exists():
        return default_cfg
    try:
        data = json.loads(proj_file.read_text(encoding='utf-8'))
        if 'context_budget' in data:
            try:
                data['context_budget'] = int(data['context_budget'])
            except Exception:
                data['context_budget'] = 12000
        else:
            data['context_budget'] = 12000
        return data
    except Exception:
        return default_cfg

def save_project_config(start_path: str | Path | None, config: dict[str, Any]) -> None:
    wa = find_workspace(start_path)
    if not wa:
        wa = init_workspace(start_path or Path.cwd())
    proj_file = wa / 'project.json'
    proj_file.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding='utf-8')

def set_project_config_value(start_path: str | Path | None, key: str, value: Any) -> dict[str, Any]:
    if key not in ALLOWED_CONFIG_KEYS:
        raise ValueError(f"Unknown config key: {key!r}. Allowed keys are: {sorted(ALLOWED_CONFIG_KEYS)}")
        
    cfg = load_project_config(start_path)
    
    if key == 'context_budget':
        try:
            val_int = int(value)
        except (ValueError, TypeError) as exc:
            raise ValueError(f"context_budget must be an integer >= 100, got {value!r}") from exc
        if val_int < 100:
            raise ValueError(f"context_budget must be >= 100, got {val_int}")
        cfg[key] = val_int
    elif key == 'schema_version':
        try:
            cfg[key] = int(value)
        except (ValueError, TypeError) as exc:
            raise ValueError(f"schema_version must be an integer, got {value!r}") from exc
    elif key in ('profile', 'variant'):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{key} must be a non-empty string")
        cfg[key] = value.strip()
    else:
        cfg[key] = str(value)
        
    save_project_config(start_path, cfg)
    return cfg

def get_workspace_status(start_path: str | Path | None = None) -> dict[str, Any]:
    wa = find_workspace(start_path)
    if not wa:
        return {'is_workspace': False, 'workspace_root': None}
    
    cfg = load_project_config(start_path)
    cache_dir = wa / 'cache'
    cache_count = len(list(cache_dir.glob('*.json'))) if cache_dir.exists() else 0
    
    ev_file = wa / 'evidence.json'
    ev_count = 0
    if ev_file.exists():
        try:
            ev_data = json.loads(ev_file.read_text(encoding='utf-8'))
            ev_count = len(ev_data)
        except Exception:
            pass
            
    checkpoints_dir = wa / 'checkpoints'
    checkpoints_count = len(list(checkpoints_dir.glob('*.docx'))) if checkpoints_dir.exists() else 0
    
    return {
        'is_workspace': True,
        'workspace_dir': str(wa),
        'workspace_root': str(wa.parent),
        'profile': cfg.get('profile', 'generic'),
        'variant': cfg.get('variant', 'default'),
        'context_budget': cfg.get('context_budget', 12000),
        'cache_entries': cache_count,
        'evidence_records': ev_count,
        'checkpoints': checkpoints_count
    }

def get_cached_document_index(start_path: str | Path | None, sha256_hash: str) -> list[DocumentSection] | None:
    wa = find_workspace(start_path)
    if not wa:
        return None
    cache_file = wa / 'cache' / f"{sha256_hash}.json"
    if not cache_file.exists():
        return None
    try:
        data = json.loads(cache_file.read_text(encoding='utf-8'))
        if not isinstance(data, dict) or data.get('schema_version') != DOCUMENT_INDEX_SCHEMA_VERSION:
            return None
        sections = []
        for item in data['sections']:
            sections.append(
                DocumentSection(
                    section_id=item['section_id'],
                    title=item['title'],
                    text=item['text'],
                    level=item['level'],
                    parent_id=item.get('parent_id'),
                    source_index=item.get('source_index', 0),
                    metadata=item.get('metadata', {})
                )
            )
        return sections
    except Exception:
        return None

def put_cached_document_index(start_path: str | Path | None, sha256_hash: str, sections: list[DocumentSection]) -> None:
    wa = find_workspace(start_path)
    if not wa:
        return
    cache_dir = wa / 'cache'
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"{sha256_hash}.json"
    
    data = [
        {
            'section_id': s.section_id,
            'title': s.title,
            'text': s.text,
            'level': s.level,
            'parent_id': s.parent_id,
            'source_index': s.source_index,
            'metadata': s.metadata
        }
        for s in sections
    ]
    payload = {'schema_version': DOCUMENT_INDEX_SCHEMA_VERSION, 'sections': data}
    cache_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
