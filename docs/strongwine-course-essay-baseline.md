# StrongWine structural baseline provenance

This is the fixed structure and artifact-count baseline for the user's software course/capstone reports. It is independent of `document_type`: course essay and đồ án chuyên ngành use the same complete baseline.

## Source and extraction

- Source DOCX: `D:\Projects\strongwine_2\Wine-website\docs\Tieu-luan-Phat-trien-phan-mem-huong-doi-tuong-StrongWine-ban-hoan-chinh-final.docx`
- Source SHA-256: `56f150fe21920e91f3283ad5ae576747eecc5d60e763ea59a0b655e6665f365`
- Read operation: `wordassistant inspect SOURCE.docx --json`; no source DOCX was changed.
- Heading baseline: every outline heading at levels 1–3, excluding the TOC copy that carries a tab-separated page number. This yields 204 ordered heading rows, including the front matter, seven chapters, conclusion, recommendations, references, appendices, and academic-integrity statement.
- Asset baseline: every inline image occurrence and every table reported by inspect: 65 image instances and 44 tables. Repeated use of the same media hash remains a separate occurrence.
- `docs/strongwine-course-essay-structure-baseline.csv` SHA-256: `d9ca607623378dac0d9e5b8f065748406b74a636e93ec059baa131723569bd33`
- `docs/strongwine-course-essay-asset-baseline.csv` SHA-256: `68424c135917a2814a4c893a4bb3b9ce0f12d1626bbf12090bf92ea6d9a5d04a`

The readiness checker pins both baseline hashes. If a baseline is intentionally refreshed, review the new reference, regenerate both seeded matrices, update the checker hashes and tests together, and record the new source SHA here.

## How to reuse it

Use the IDs and hierarchy as a completeness contract. Each new report must provide an evidence-backed equivalent for every heading and each image/table slot. A target heading may be renamed for the new system, but the analysis scope and depth must remain. A target artifact must be newly sourced or drawn for that system. Never copy StrongWine identities, cover metadata, source claims, routes, table data, screenshots, logos, signatures, or results.

The checker verifies baseline integrity, row coverage, mapping fields, evidence-file existence, reviewer/date, and non-omission decisions. It cannot judge whether prose or a diagram truly covers the mapped topic; the manual parity acceptance checks and visual review remain mandatory. If a complete equivalent cannot be supported without inventing facts, keep readiness `INCOMPLETE` and report the blocked rows.
