from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping
import json

class ProfileError(ValueError):
    pass

@dataclass(frozen=True)
class Margins:
    top_cm: float; bottom_cm: float; left_cm: float; right_cm: float

@dataclass(frozen=True)
class PageSpec:
    size: str; width_cm: float; height_cm: float; margins: Margins; one_sided: bool

@dataclass(frozen=True)
class TypographySpec:
    body_font: str; body_size_pt: float; line_spacing: float | None
    styles: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)

@dataclass(frozen=True)
class Variant:
    name: str; page: PageSpec; typography: TypographySpec
    front_matter: tuple[str, ...] = ()
    section_blueprint: tuple[Mapping[str, Any], ...] = ()
    citations: Mapping[str, Any] = field(default_factory=dict)
    header_footer: Mapping[str, Any] = field(default_factory=dict)
    template_asset: str | None = None

@dataclass(frozen=True)
class DocumentProfile:
    profile_id: str; name: str; version: int; variants: Mapping[str, Variant]
    source_policy: str = "unspecified"
    source_assets: tuple[str, ...] = ()
    source_conflicts: tuple[Mapping[str, Any], ...] = ()
    def variant(self, name: str) -> Variant:
        try: return self.variants[name]
        except KeyError as exc: raise ProfileError(f"Unknown variant {name!r}; choose one of {sorted(self.variants)}") from exc


def load_profile(path: str | Path) -> DocumentProfile:
    path=Path(path)
    try: data=json.loads(path.read_text(encoding='utf-8'))
    except Exception as exc: raise ProfileError(f"Cannot read profile {path}: {exc}") from exc
    if not isinstance(data, dict): raise ProfileError("Profile root must be an object")
    _str(data,'id'); _str(data,'name')
    version=data.get('version')
    if isinstance(version,bool) or not isinstance(version,int) or version < 1: raise ProfileError('version must be an integer >= 1')
    variants_raw=data.get('variants')
    if not isinstance(variants_raw,dict) or not variants_raw: raise ProfileError('variants must be a non-empty object')
    variants={k:_parse_variant(k,v) for k,v in variants_raw.items()}
    return DocumentProfile(
        profile_id=data['id'], name=data['name'], version=version, variants=variants,
        source_policy=_optional_str(data.get('source_policy'),'source_policy') or 'unspecified',
        source_assets=_string_list(data.get('source_assets',[]),'source_assets'),
        source_conflicts=_object_list(data.get('source_conflicts',[]),'source_conflicts'),
    )


def _parse_variant(name: str, data: Any) -> Variant:
    if not isinstance(data,dict): raise ProfileError(f'variants.{name} must be an object')
    page=data.get('page'); typ=data.get('typography')
    if not isinstance(page,dict) or not isinstance(typ,dict): raise ProfileError(f'variants.{name} requires page and typography objects')
    m=page.get('margins_cm')
    if not isinstance(m,dict): raise ProfileError(f'variants.{name}.page.margins_cm must be an object')
    width=_num(page.get('width_cm'),f'{name}.page.width_cm',positive=True)
    height=_num(page.get('height_cm'),f'{name}.page.height_cm',positive=True)
    margins=Margins(*[_num(m.get(k),f'{name}.page.margins_cm.{k}',nonnegative=True) for k in ('top','bottom','left','right')])
    if margins.left_cm + margins.right_cm >= width or margins.top_cm + margins.bottom_cm >= height:
        raise ProfileError(f'variants.{name}: margins leave no printable page area')
    one=page.get('one_sided',True)
    if type(one) is not bool: raise ProfileError(f'variants.{name}.page.one_sided must be a boolean')
    body_font=_str(typ,'body_font'); body_size=_num(typ.get('body_size_pt'),f'{name}.typography.body_size_pt',positive=True)
    ls=typ.get('line_spacing')
    if ls is not None: ls=_num(ls,f'{name}.typography.line_spacing',positive=True)
    styles=typ.get('styles',{})
    if not isinstance(styles,dict): raise ProfileError(f'{name}.typography.styles must be an object')
    front=_string_list(data.get('front_matter',[]),f'{name}.front_matter')
    blueprint=_object_list(data.get('section_blueprint',[]),f'{name}.section_blueprint')
    citations=data.get('citations',{}); header=data.get('header_footer',{})
    if not isinstance(citations,dict) or not isinstance(header,dict): raise ProfileError(f'{name}: citations/header_footer must be objects')
    template=data.get('template_asset')
    if template is not None and not isinstance(template,str): raise ProfileError(f'{name}.template_asset must be string')
    return Variant(name, PageSpec(str(page.get('size','custom')),width,height,margins,one), TypographySpec(body_font,body_size,ls,styles), front, blueprint, citations, header, template)


def _str(d: Mapping[str,Any],k:str)->str:
    v=d.get(k)
    if not isinstance(v,str) or not v.strip(): raise ProfileError(f'{k} must be a non-empty string')
    return v

def _optional_str(v:Any,k:str)->str|None:
    if v is None:return None
    if not isinstance(v,str):raise ProfileError(f'{k} must be a string')
    return v

def _num(v:Any,k:str,positive=False,nonnegative=False)->float:
    if isinstance(v,bool) or not isinstance(v,(int,float)): raise ProfileError(f'{k} must be numeric')
    x=float(v)
    if positive and x<=0: raise ProfileError(f'{k} must be > 0')
    if nonnegative and x<0: raise ProfileError(f'{k} must be >= 0')
    return x

def _string_list(v:Any,k:str)->tuple[str,...]:
    if not isinstance(v,list) or any(not isinstance(x,str) for x in v): raise ProfileError(f'{k} must be an array of strings')
    return tuple(v)

def _object_list(v:Any,k:str)->tuple[Mapping[str,Any],...]:
    if not isinstance(v,list) or any(not isinstance(x,dict) for x in v): raise ProfileError(f'{k} must be an array of objects')
    return tuple(v)
