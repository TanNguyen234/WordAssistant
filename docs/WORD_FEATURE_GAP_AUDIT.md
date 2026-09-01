# WordAssistant Universal Core Feature Gap Audit (Historical Baseline)

> This document records the pre-implementation baseline at commit `590bb25`.
> It is not the current capability statement. Use `wordassistant capabilities
> --json` and `docs/word_feature_matrix.json` for current, operation-level status.

**Audit date:** 2026-08-26  
**Repository:** `TanNguyen234/WordAssistant`  
**Branch:** `feat/wordassistant-v2-universal-core`  
**Audited HEAD:** `590bb25`  

## Executive finding

The current repository is a tested deterministic DOCX toolkit, not yet a broad Microsoft Word automation platform. Its strongest implemented areas are profile-driven scaffolding, HCMUNRE support, bounded long-document retrieval, inspection, safe text replacement, evidence records, validation, verification, and LibreOffice-aware rendering. Most authoring and review operations required by the universal-core target are absent.

The implementation must preserve the current CLI and document behavior while adding a compact operation facade, deterministic backend routing, truthful capability discovery, selectors, transaction checkpoints, and the missing Word feature engines.

## Audit evidence

- Working tree was clean on the required branch.
- Baseline suite: 126 tests collected and 126 passed.
- `python -m wordassistant doctor --json` reports Python 3.12.4, `python-docx` available, core ready, no API key required.
- LibreOffice is not available in the current Windows environment.
- Microsoft Word is installed at an Office15 path; `pywin32` is not installed.
- `docx-mcp` is installed, but WordAssistant has no callable adapter and truthfully reports all advanced capabilities as unsupported.
- Both official HCMUNRE source assets match their required SHA-256 values.
- None of the 22 requested new high-level command families currently parse successfully.

## Capability classification

| Area | Classification | Current evidence | Required completion |
|---|---|---|---|
| Doctor, status, profiles, workspace | EXISTING | Public CLI and tests | Preserve; extend backend health reporting |
| Inspect and bounded context | EXISTING | Structural index and hard context budget tests | Extend object inventory and selectors |
| Scaffold and safe replacement | EXISTING | Public CLI and round-trip tests | Keep compatibility aliases under create/edit |
| Evidence registry | EXISTING | Validation and concurrency tests | Connect evidence IDs to citations |
| Validate and verify | EXISTING | Structural/profile delivery gates | Expand status model and feature semantics |
| LibreOffice rendering | EXISTING | Renderer and discovery tests | Add engine routing and visual checks |
| Paragraph and run editing | PARTIAL | Safe plain-text replacement and scaffold styling | Full text, formatting, style CRUD, scoped selectors |
| Styles | PARTIAL | Applies a small fixed style subset during scaffold | Heading 1-9, custom style create/update/clone/delete |
| Sections and page layout | PARTIAL | Width, height, and margins on scaffold sections | Orientation, section breaks, columns, gutter, mirrored margins |
| Headers and footers | PARTIAL | Basic semantic text and footer PAGE field in scaffold | Variants, objects, fields, section-specific linking |
| Page numbering | PARTIAL | Basic footer PAGE and one restart element | Format, position, section semantics, front/body numbering |
| Fields and TOC | PARTIAL | PAGE and TOC field construction only | Reusable field engine, inspect/edit/lock/update |
| Lists of figures/tables | MISSING | Literal placeholder paragraphs | Real TOC fields filtered by caption labels |
| Citations and bibliography | PARTIAL | Evidence records and bibliography-count validation | Deterministic citation and bibliography operations |
| Tables | MISSING | Inspection/counting only | Full table mutation and formatting engine |
| Images | MISSING | Relationship inventory only | Insert/replace/remove/resize/metadata operations |
| Lists | MISSING | No list command or numbering engine | Bullet, numbered, multilevel, restart/continue |
| Hyperlinks and bookmarks | MISSING | No callable operations | CRUD and internal links |
| Cross-references and captions | MISSING | No callable operations | SEQ/REF/PAGEREF workflows |
| Footnotes and endnotes | MISSING | No callable operations | OOXML/native CRUD and numbering |
| Comments | NATIVE_ONLY | No implementation; capability is UNSUPPORTED | Word-native CRUD/reply/resolve workflows |
| Tracked changes | NATIVE_ONLY | No implementation; capability is UNSUPPORTED | Word-native revision workflows |
| Compare and merge | NATIVE_ONLY | V1 scripts removed; no V2 commands | Restore through native backend with JSON summaries |
| Content controls | MISSING / NATIVE_ONLY | No implementation | Core OOXML where safe, native where required |
| Protection | MISSING / NATIVE_ONLY | No implementation | Truthful OOXML/native protection modes |
| Document properties | MISSING | No public facade | Core and custom properties plus DOCPROPERTY fields |
| Equations | MISSING | No implementation | Common LaTeX-to-OMML and native fallback |
| Charts | NATIVE_ONLY | No reliable package authoring | Native practical chart operations |
| Mail merge | NATIVE_ONLY | No implementation | Native merge plus deterministic data-source validation |
| Operation router | MISSING | Only backend status probe exists | Typed registry, selection policy, fidelity metadata |
| Selector model | MISSING | Optional context section ID only | Stable document object selectors |
| Transactions/checkpoints | MISSING | No rollback system | Preflight/checkpoint/mutate/validate/rollback |
| Python facade | MISSING | Private functions only | Stable `WordDocument` or equivalent facade |
| Agent manifest | MISSING | Skill exists but no JSON manifest | Machine-readable command/workflow discovery |
| Feature matrix | MISSING | No required docs/JSON matrix | Registry-backed documentation consistency |

## Confirmed implementation defects

1. `paragraph_spacing_before_pt` and `paragraph_spacing_after_pt` are parsed but not applied by scaffold styling.
2. Per-style `line_spacing`, `space_before_pt`, and `space_after_pt` are accepted but not applied.
3. Page orientation is parsed but `_apply_section_page` does not write orientation semantics.
4. `one_sided` is parsed but not honored by document layout.
5. List of Figures and List of Tables are literal placeholders.
6. Page-number validation accepts any section containing a restart instead of proving the configured named section, format, placement, and field.
7. Capability discovery has no implementation registry/backend health matrix at operation granularity.
8. The installed console entry point is unavailable in the current shell, although running from source via `PYTHONPATH=src` works. The clean-wheel gate must continue proving packaged installation.

## Immutable boundaries

| Boundary | Invariant |
|---|---|
| Official guidance asset | SHA-256 `0f3622dbcd74009fb0867e0d3fa4a1624a38983af502e55d48868edf33f74e78` |
| Official proposal asset | SHA-256 `bb291a6de459e33267170c3dd9087903a0d9f1911086bbfc935cb9f7781904e6` |
| Existing public CLI | Remains callable through V2.x compatibility aliases |
| Core runtime | Deterministic and API-key-free |
| Fidelity boundary | No silent backend substitution when semantics may change |
| Unsafe mutation | Fail closed and preserve input unless output/in-place intent is explicit |
| Native Word | Optional, health-checked, timeout-bounded, and always releases COM objects |
| Capability claims | Require callable implementation, tests, backend availability, and health evidence |

## Delivery authority

Allowed: source, tests, documentation, configuration, local logical commits, and push to the required feature branch after final verification.  
Forbidden: history rewriting, force operations, deleting working functionality, modifying official HCMUNRE assets, silently weakening tests or validation, and advertising unimplemented capabilities.
