from __future__ import annotations
from dataclasses import dataclass, field
import json
import math
from pathlib import Path
from typing import Any, Mapping
from importlib.resources import files as resource_files

class ProfileError(ValueError):
    pass

@dataclass(frozen=True)
class Margins:
    top_cm: float
    bottom_cm: float
    left_cm: float
    right_cm: float

@dataclass(frozen=True)
class PageSpec:
    size: str
    width_cm: float
    height_cm: float
    margins: Margins
    one_sided: bool
    orientation: str = "portrait"
    provenance: str | None = None

@dataclass(frozen=True)
class TypographySpec:
    body_font: str
    body_size_pt: float
    line_spacing: float | None = None
    paragraph_spacing_before_pt: float | None = None
    paragraph_spacing_after_pt: float | None = None
    styles: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)

@dataclass(frozen=True)
class Variant:
    name: str
    page: PageSpec
    typography: TypographySpec
    front_matter: tuple[str, ...] = ()
    front_matter_titles: Mapping[str, str] = field(default_factory=dict)
    cover: Mapping[str, Any] = field(default_factory=dict)
    section_blueprint: tuple[Mapping[str, Any], ...] = ()
    citations: Mapping[str, Any] = field(default_factory=dict)
    header_footer: Mapping[str, Any] = field(default_factory=dict)
    template_asset: str | None = None
    field_requirements: Mapping[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class DocumentProfile:
    profile_id: str
    name: str
    version: int
    variants: Mapping[str, Variant]
    source_policy: str = "unspecified"
    source_assets: tuple[str, ...] = ()
    source_conflicts: tuple[Mapping[str, Any], ...] = ()

    def variant(self, name: str) -> Variant:
        try:
            return self.variants[name]
        except KeyError as exc:
            raise ProfileError(f"Unknown variant {name!r}; choose one of {sorted(self.variants)}") from exc


_ROOT_KEYS = {'id', 'name', 'version', 'variants', 'source_policy', 'source_assets', 'source_conflicts'}
_VARIANT_KEYS = {
    'page', 'typography', 'front_matter', 'front_matter_titles', 'cover',
    'section_blueprint', 'citations', 'header_footer', 'template_asset', 'field_requirements'
}
_PAGE_KEYS = {'size', 'width_cm', 'height_cm', 'margins_cm', 'one_sided', 'orientation', 'provenance'}
_MARGINS_KEYS = {'top', 'bottom', 'left', 'right'}
_TYPOGRAPHY_KEYS = {'body_font', 'body_size_pt', 'line_spacing', 'paragraph_spacing_before_pt', 'paragraph_spacing_after_pt', 'styles'}
_STYLE_KEYS = {'font', 'size_pt', 'bold', 'italic', 'alignment', 'line_spacing', 'space_before_pt', 'space_after_pt'}
_BLUEPRINT_KEYS = {'title', 'level', 'required', 'numbered', 'restart_numbering'}
_COVER_KEYS = {'institution_lines', 'document_type', 'title_prefix', 'metadata_fields', 'location_year'}
_CITATIONS_KEYS = {'style', 'in_text', 'minimum_references', 'prefer_primary_source', 'bibliography_order'}
_HEADER_FOOTER_KEYS = {'header_left', 'header_right', 'footer_left', 'footer_right', 'page_number_start'}
_FIELD_REQS_KEYS = {'table_of_contents', 'page_number', 'list_of_figures', 'list_of_tables'}
_VALID_ALIGNMENTS = {'left', 'center', 'right', 'justify'}

def _check_unknown_keys(d: Mapping[str, Any], allowed: set[str], context: str) -> None:
    unknown = set(d.keys()) - allowed
    if unknown:
        raise ProfileError(f"Unknown key(s) in {context}: {sorted(unknown)}; allowed keys are {sorted(allowed)}")

def validate_profile_dict(data: Any) -> DocumentProfile:
    if not isinstance(data, dict):
        raise ProfileError("Profile root must be an object")
    _check_unknown_keys(data, _ROOT_KEYS, "profile root")
    
    p_id = _str(data, 'id')
    p_name = _str(data, 'name')
    version = data.get('version')
    if type(version) is not int or version < 1:
        raise ProfileError("version must be an integer >= 1")
    
    variants_raw = data.get('variants')
    if not isinstance(variants_raw, dict) or not variants_raw:
        raise ProfileError("variants must be a non-empty object")
    
    variants = {}
    for v_name, v_data in variants_raw.items():
        if not isinstance(v_name, str) or not v_name.strip():
            raise ProfileError("Variant name must be a non-empty string")
        variants[v_name] = _parse_variant(v_name, v_data)
        
    return DocumentProfile(
        profile_id=p_id,
        name=p_name,
        version=version,
        variants=variants,
        source_policy=_optional_str(data.get('source_policy'), 'source_policy') or 'unspecified',
        source_assets=_string_list(data.get('source_assets', []), 'source_assets'),
        source_conflicts=_object_list(data.get('source_conflicts', []), 'source_conflicts')
    )

def load_profile(path: str | Path) -> DocumentProfile:
    path = Path(path)
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except Exception as exc:
        raise ProfileError(f"Cannot read profile {path}: {exc}") from exc
    return validate_profile_dict(data)

def _parse_variant(name: str, data: Any) -> Variant:
    if not isinstance(data, dict):
        raise ProfileError(f"variants.{name} must be an object")
    _check_unknown_keys(data, _VARIANT_KEYS, f"variants.{name}")
    
    page_data = data.get('page')
    typ_data = data.get('typography')
    if not isinstance(page_data, dict) or not isinstance(typ_data, dict):
        raise ProfileError(f"variants.{name} requires 'page' and 'typography' objects")
    
    _check_unknown_keys(page_data, _PAGE_KEYS, f"variants.{name}.page")
    page_size = str(page_data.get('size', 'custom'))
    if type(page_data.get('size', '')) not in (str,):
        raise ProfileError(f"variants.{name}.page.size must be a string")
        
    m_data = page_data.get('margins_cm')
    if not isinstance(m_data, dict):
        raise ProfileError(f"variants.{name}.page.margins_cm must be an object")
    _check_unknown_keys(m_data, _MARGINS_KEYS, f"variants.{name}.page.margins_cm")
    
    width = _num(page_data.get('width_cm'), f"{name}.page.width_cm", positive=True)
    height = _num(page_data.get('height_cm'), f"{name}.page.height_cm", positive=True)
    
    margins = Margins(*[
        _num(m_data.get(k), f"{name}.page.margins_cm.{k}", nonnegative=True)
        for k in ('top', 'bottom', 'left', 'right')
    ])
    
    if margins.left_cm + margins.right_cm >= width or margins.top_cm + margins.bottom_cm >= height:
        raise ProfileError(f"variants.{name}: margins leave no printable page area")
    
    one_sided = page_data.get('one_sided', True)
    if type(one_sided) is not bool:
        raise ProfileError(f"variants.{name}.page.one_sided must be a boolean")
        
    orientation = str(page_data.get('orientation', 'portrait'))
    if orientation not in ('portrait', 'landscape'):
        raise ProfileError(f"variants.{name}.page.orientation must be 'portrait' or 'landscape'")
        
    page_spec = PageSpec(
        size=page_size,
        width_cm=width,
        height_cm=height,
        margins=margins,
        one_sided=one_sided,
        orientation=orientation,
        provenance=_optional_str(page_data.get('provenance'), f"{name}.page.provenance")
    )
    
    _check_unknown_keys(typ_data, _TYPOGRAPHY_KEYS, f"variants.{name}.typography")
    body_font = _str(typ_data, 'body_font')
    body_size = _num(typ_data.get('body_size_pt'), f"{name}.typography.body_size_pt", positive=True)
    
    ls = typ_data.get('line_spacing')
    if ls is not None:
        ls = _num(ls, f"{name}.typography.line_spacing", positive=True)
        
    sp_before = typ_data.get('paragraph_spacing_before_pt')
    if sp_before is not None:
        sp_before = _num(sp_before, f"{name}.typography.paragraph_spacing_before_pt", nonnegative=True)
        
    sp_after = typ_data.get('paragraph_spacing_after_pt')
    if sp_after is not None:
        sp_after = _num(sp_after, f"{name}.typography.paragraph_spacing_after_pt", nonnegative=True)
        
    styles_data = typ_data.get('styles', {})
    if not isinstance(styles_data, dict):
        raise ProfileError(f"{name}.typography.styles must be an object")
    for s_name, s_val in styles_data.items():
        if not isinstance(s_val, dict):
            raise ProfileError(f"{name}.typography.styles.{s_name} must be an object")
        _check_unknown_keys(s_val, _STYLE_KEYS, f"{name}.typography.styles.{s_name}")
        if 'alignment' in s_val and s_val['alignment'] not in _VALID_ALIGNMENTS:
            raise ProfileError(f"Invalid alignment '{s_val['alignment']}' in style {s_name}; allowed are {sorted(_VALID_ALIGNMENTS)}")
        if 'size_pt' in s_val:
            _num(s_val['size_pt'], f"{name}.styles.{s_name}.size_pt", positive=True)
        if 'font' in s_val and (not isinstance(s_val['font'], str) or not s_val['font'].strip()):
            raise ProfileError(f"{name}.styles.{s_name}.font must be a non-empty string")
        if 'bold' in s_val and type(s_val['bold']) is not bool:
            raise ProfileError(f"{name}.styles.{s_name}.bold must be a boolean")
        if 'italic' in s_val and type(s_val['italic']) is not bool:
            raise ProfileError(f"{name}.styles.{s_name}.italic must be a boolean")
        if 'line_spacing' in s_val:
            _num(s_val['line_spacing'], f"{name}.styles.{s_name}.line_spacing", positive=True)
        if 'space_before_pt' in s_val:
            _num(s_val['space_before_pt'], f"{name}.styles.{s_name}.space_before_pt", nonnegative=True)
        if 'space_after_pt' in s_val:
            _num(s_val['space_after_pt'], f"{name}.styles.{s_name}.space_after_pt", nonnegative=True)
            
    typ_spec = TypographySpec(
        body_font=body_font,
        body_size_pt=body_size,
        line_spacing=ls,
        paragraph_spacing_before_pt=sp_before,
        paragraph_spacing_after_pt=sp_after,
        styles=styles_data
    )
    
    front_matter = _string_list(data.get('front_matter', []), f"{name}.front_matter")
    
    front_matter_titles = data.get('front_matter_titles', {})
    if not isinstance(front_matter_titles, dict):
        raise ProfileError(f"{name}.front_matter_titles must be an object")
    for fmt_k, fmt_v in front_matter_titles.items():
        if not isinstance(fmt_k, str) or not isinstance(fmt_v, str):
            raise ProfileError(f"{name}.front_matter_titles keys and values must be strings")
            
    cover_data = data.get('cover', {})
    if not isinstance(cover_data, dict):
        raise ProfileError(f"{name}.cover must be an object")
    if cover_data:
        _check_unknown_keys(cover_data, _COVER_KEYS, f"{name}.cover")
        if 'institution_lines' in cover_data:
            _string_list(cover_data['institution_lines'], f"{name}.cover.institution_lines")
        if 'document_type' in cover_data:
            _str(cover_data, 'document_type')
        if 'title_prefix' in cover_data and not isinstance(cover_data['title_prefix'], str):
            raise ProfileError(f"{name}.cover.title_prefix must be a string")
        if 'location_year' in cover_data and not isinstance(cover_data['location_year'], str):
            raise ProfileError(f"{name}.cover.location_year must be a string")
        if 'metadata_fields' in cover_data:
            _object_list(cover_data['metadata_fields'], f"{name}.cover.metadata_fields")
            
    blueprint_raw = _object_list(data.get('section_blueprint', []), f"{name}.section_blueprint")
    blueprint = []
    seen_titles = set()
    for idx, bp in enumerate(blueprint_raw):
        _check_unknown_keys(bp, _BLUEPRINT_KEYS, f"{name}.section_blueprint[{idx}]")
        title = _str(bp, 'title')
        if title.lower() in seen_titles:
            raise ProfileError(f"Duplicate title in section_blueprint: '{title}'")
        seen_titles.add(title.lower())
        level = bp.get('level', 1)
        if type(level) is not int or not (1 <= level <= 9):
            raise ProfileError(f"Section blueprint level must be an integer between 1 and 9, got {level!r}")
        blueprint.append(bp)
        
    citations = data.get('citations', {})
    if not isinstance(citations, dict):
        raise ProfileError(f"{name}.citations must be an object")
    if citations:
        _check_unknown_keys(citations, _CITATIONS_KEYS, f"{name}.citations")
        if 'minimum_references' in citations:
            min_r = citations['minimum_references']
            if type(min_r) is not int or min_r < 0:
                raise ProfileError(f"{name}.citations.minimum_references must be an integer >= 0, got {min_r!r}")
        if 'prefer_primary_source' in citations and type(citations['prefer_primary_source']) is not bool:
            raise ProfileError(f"{name}.citations.prefer_primary_source must be a boolean")
            
    header_footer = data.get('header_footer', {})
    if not isinstance(header_footer, dict):
        raise ProfileError(f"{name}.header_footer must be an object")
    if header_footer:
        _check_unknown_keys(header_footer, _HEADER_FOOTER_KEYS, f"{name}.header_footer")
        
    template = data.get('template_asset')
    if template is not None:
        if not isinstance(template, str) or not template.strip():
            raise ProfileError(f"{name}.template_asset must be a non-empty string")
        if '..' in Path(template).parts or Path(template).is_absolute():
            raise ProfileError(f"Path traversal or absolute path detected in template_asset: {template}")
            
    field_reqs = data.get('field_requirements', {})
    if not isinstance(field_reqs, dict):
        raise ProfileError(f"{name}.field_requirements must be an object")
    if field_reqs:
        _check_unknown_keys(field_reqs, _FIELD_REQS_KEYS, f"{name}.field_requirements")
        
    return Variant(
        name=name,
        page=page_spec,
        typography=typ_spec,
        front_matter=front_matter,
        front_matter_titles=front_matter_titles,
        cover=cover_data,
        section_blueprint=tuple(blueprint),
        citations=citations,
        header_footer=header_footer,
        template_asset=template,
        field_requirements=field_reqs
    )

def _str(d: Mapping[str, Any], k: str) -> str:
    v = d.get(k)
    if not isinstance(v, str) or not v.strip():
        raise ProfileError(f"'{k}' must be a non-empty string")
    return v

def _optional_str(v: Any, k: str) -> str | None:
    if v is None:
        return None
    if not isinstance(v, str):
        raise ProfileError(f"'{k}' must be a string")
    return v

def _num(v: Any, k: str, positive: bool = False, nonnegative: bool = False) -> float:
    if type(v) is bool or not isinstance(v, (int, float)):
        raise ProfileError(f"'{k}' must be numeric (float or int), got {v!r}")
    x = float(v)
    if math.isnan(x) or math.isinf(x):
        raise ProfileError(f"'{k}' cannot be NaN or Infinity, got {x}")
    if positive and x <= 0:
        raise ProfileError(f"'{k}' must be > 0, got {x}")
    if nonnegative and x < 0:
        raise ProfileError(f"'{k}' must be >= 0, got {x}")
    return x

def _string_list(v: Any, k: str) -> tuple[str, ...]:
    if not isinstance(v, list) or any(not isinstance(x, str) for x in v):
        raise ProfileError(f"'{k}' must be an array of strings")
    return tuple(v)

def _object_list(v: Any, k: str) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(v, list) or any(not isinstance(x, dict) for x in v):
        raise ProfileError(f"'{k}' must be an array of objects")
    return tuple(v)

def _get_project_root() -> Path:
    curr = Path(__file__).resolve()
    for parent in curr.parents:
        if (parent / 'pyproject.toml').exists() or (parent / 'profiles').is_dir():
            return parent
    return curr.parents[3]

def discover_profiles(extra_dirs: list[Path] | None = None) -> list[DocumentProfile]:
    found: dict[str, DocumentProfile] = {}
    search_dirs: list[Path] = []
    
    if extra_dirs:
        for d in extra_dirs:
            if d.exists() and d.is_dir():
                search_dirs.append(d)
                
    # Check repo profiles/ directory
    repo_profiles = _get_project_root() / 'profiles'
    if repo_profiles.exists() and repo_profiles.is_dir() and repo_profiles not in search_dirs:
        search_dirs.append(repo_profiles)
        
    for sdir in search_dirs:
        for f in sorted(sdir.glob('*.json')):
            try:
                prof = load_profile(f)
                if prof.profile_id not in found:
                    found[prof.profile_id] = prof
            except Exception:
                continue
                
    # Also check packaged data
    try:
        pkg_profiles = resource_files('wordassistant').joinpath('data', 'profiles')
        for f in pkg_profiles.iterdir():
            if f.name.endswith('.json'):
                try:
                    data = json.loads(f.read_text(encoding='utf-8'))
                    prof = validate_profile_dict(data)
                    if prof.profile_id not in found:
                        found[prof.profile_id] = prof
                except Exception:
                    continue
    except Exception:
        pass
        
    return sorted(found.values(), key=lambda p: p.profile_id)

def resolve_profile(name_or_path: str, extra_dirs: list[Path] | None = None) -> DocumentProfile:
    p = Path(name_or_path)
    if p.exists() and p.is_file():
        return load_profile(p)
        
    filename = name_or_path if name_or_path.endswith('.json') else f"{name_or_path}.json"
    
    # Check extra/workspace dirs
    if extra_dirs:
        for d in extra_dirs:
            candidate = d / filename
            if candidate.exists() and candidate.is_file():
                return load_profile(candidate)
                
    # Check repo profiles/
    candidate = _get_project_root() / 'profiles' / filename
    if candidate.exists() and candidate.is_file():
        return load_profile(candidate)
        
    # Check packaged profiles
    try:
        packaged = resource_files('wordassistant').joinpath('data', 'profiles', filename)
        if packaged.is_file():
            data = json.loads(packaged.read_text(encoding='utf-8'))
            return validate_profile_dict(data)
    except Exception:
        pass
        
    # Check by discovered profile_id
    for prof in discover_profiles(extra_dirs):
        if prof.profile_id == name_or_path:
            return prof
            
    raise ProfileError(f"Profile not found: '{name_or_path}'")
