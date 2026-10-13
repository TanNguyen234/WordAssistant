# Academic report workflow for agents

This guide shows how an agent can use WordAssistant to create an editable report from a selected institutional profile, inspect academic sources, and produce citations tied to downloaded evidence. The HCMUNRE profile is only for that school's ĐACN 2026–2027 report. For another institution, use its controlling guide and a matching profile.

## 1. Confirm the environment and profile

```powershell
wordassistant doctor --json
wordassistant profile validate profiles/hcm-university-dacn-2026-2027.json --json
```

Inspect the source guide with `wordassistant inspect`. For long reports (over 40 pages or unknown length), use `wordassistant inspect FILE --summary --json` so the agent receives counts and a bounded heading outline without every paragraph's text. Use bounded context to retrieve only the active report section. The report profile cites only the presentation guide. The separate proposal document is not a formatting authority for this report.

For a long DOCX, do not paste the file or full `inspect --json` response into the LLM context. Use a focused query, one section at a time, with no more than 4,000 tokens per retrieval and 8,000 tokens combined in one task turn:

```powershell
wordassistant inspect report.docx --summary --json
wordassistant context report.docx --query "method for evaluating model performance" --max-tokens 4000 --json
wordassistant context report.docx --query "method for evaluating model performance" --max-tokens 4000 --only-section methods --json
```

The first context call can return a relevant section ID; pass that ID to `--only-section` to exclude neighboring sections. `--section` and `--active-section-id` only prioritize a section and can return neighbors. The CLI may index the full DOCX locally, but only the bounded result is returned to the agent. For section-wide text replacement, use the heading selector to confine the mutation to that section:

```powershell
wordassistant edit replace report.docx --output report-revised.docx `
  --selector '{"type":"heading","text":"PHƯƠNG PHÁP THỰC HIỆN"}' `
  --options '{"pattern":"old phrase","replacement":"new phrase"}' --dry-run --json
```

Without `--selector`, a text replacement can affect matching text throughout the document. Save the final operation to a separate output copy after reviewing the dry-run result.

### Course-essay acceptance matrix (required before composition)

For a user-defined course essay, write a requirement/evidence matrix before creating or editing the DOCX. Keep the user's profile separate from school-specific profiles in this repository; do not silently apply HCMUNRE rules to another school.

When an older DOCX is supplied as a read-only reference, record the permitted facts and assets and keep its chapter order, layout, and stale application screenshots out of the new report unless the user explicitly requests them. Use current project/database evidence for the implementation being described.

The matrix must include:

- **Database coverage:** every current database table, its purpose, all columns and SQL types, primary and foreign keys, nullability, defaults, unique constraints, indexes, relationships, and representative sample rows. Mark unavailable evidence; never infer schema details. Remove credentials, tokens, and unnecessary personal data from samples.
- **Interface coverage:** every distinct implemented function and each applicable role/persona. Capture fresh desktop screenshots at 1366 px wide or above, showing the whole browser tab content at normal web size. Do not use mobile emulation, cropped fragments, or screenshots from the old reference. Embed every required image in the DOCX and track its route, persona, state, resolution, and caption.
- **Demo content and role context:** prefer records confirmed as demo data or synthetic fixtures and show them in context without forced masks. A shipper delivery view should make the recipient, full destination, item names and quantities, shipment status, and call/map actions readable. If a live database record is not confirmed as demo data, use a synthetic fixture instead of exposing it as an example. When authentication blocks a live route, render the same project template with a verified fixture and record the screenshot source and state in the matrix.
- **Cover and typography:** when two covers are required, verify both are distinct. Keep a cover frame visibly inset (target at least 12 mm from the page edge); for an existing page-relative frame, `section.layout` accepts `page_border_space_pt` to set all four border edges. Use real Word heading styles with consistent level indentation and true multilevel numbering when requested. `style.update` supports font color and paragraph indents for existing styles. Apply the specified body size and black heading/caption text when required.
- **Pagination and captions:** list every required page boundary, including declarations and major sections. Respect the requested minimum length without an artificial upper limit or filler. When the caption form is `Hình x.x: Tên hình`, keep only that title in the caption.

Do not begin DOCX mutations while a required matrix row has no source or planned evidence. Before delivery, map every database table to its schema and sample-data content, every requested feature/persona to an image embedded in the saved DOCX, and every layout requirement to a rendered-page check. Generic `validate`/`verify` success does not replace those content checks.

## 2. Create the editable Word scaffold

Copy `examples/hcmunre/report_metadata.example.json`, fill only known metadata, and pass it to the scaffold command:

```powershell
wordassistant scaffold report.docx `
  --profile hcm-university-dacn-2026-2027 `
  --variant report `
  --title "[Verified project title]" `
  --author "[Student name]" `
  --supervisor "[Supervisor name]" `
  --cover-metadata report_metadata.json `
  --json
```

Do not leave the bracketed example values in a submitted report. The generated document stores A4 page setup, margins, Times New Roman 13 pt and 1.5 line spacing, named cover/front-matter/reference styles, the guide's first-page border, section-specific headers and footers, Arabic page numbering starting at `MỞ ĐẦU`, and editable TOC/list fields. It includes blank review pages and editable schedule/abbreviation tables; it does not invent project content, names, approvals, or results.

For images and tables, read `captions` from `wordassistant profile show hcm-university-dacn-2026-2027 --json`. This profile maps the visible labels `HÌNH`, `SƠ ĐỒ`, and `BẢNG` to Word sequence identifiers `Hinh`, `SoDo`, and `Bang`. Insert captions with both the visible `label` and matching `sequence_id` (or image `caption_label` and `caption_sequence`) so the list fields collect the captions.

The HCMUNRE guide requires chapter.sequence numbering (for example `HÌNH 2.1`).
Supply `chapter_number` for standalone captions or `caption_chapter_number`
for image captions. The nearest preceding built-in `Heading 1` must start
with the matching literal `CHƯƠNG N` or a leading chapter numeral `N`, or have
a valid decimal automatic Heading 1 number. The operation verifies that number
and inserts the verified chapter prefix plus
`SEQ Hinh \\* ARABIC \\s 1` (or `SoDo` / `Bang`); Word resets the sequence
after each Heading 1. For a user-requested colon form such as `Hình 2.1: Tên
hình`, pass `caption_separator: ":"` and use the user's requested label; the
default remains a period for compatibility with profiles that require it.
These options are explicit: selecting a profile alone does not convert
existing captions or automatically add chapter numbers.

```powershell
wordassistant caption insert report.docx --output captioned.docx `
  --selector '{"type":"text","text":"[Exact paragraph in chapter 2]"}' `
  --options '{"label":"BẢNG","sequence_id":"Bang","title":"[Verified table title]","chapter_number":2}' --json
wordassistant image insert captioned.docx --output illustrated.docx `
  --selector '{"type":"text","text":"[Exact paragraph in chapter 2]"}' `
  --options '{"image_path":"figure.png","caption":"[Verified figure title]","caption_label":"HÌNH","caption_sequence":"Hinh","caption_chapter_number":2,"caption_separator":":"}' --json
```

Update fields and save through Word before delivery. Chapter prefixes are
verified against the current literal or automatic Heading 1 number; reverify
them after renumbering headings or moving captions across chapters. OOXML
tests verify field instructions and failure gates; they do not establish
Word's updated display or rendered appearance.

## 3. Find, download, and review sources

Source discovery makes candidates. It does not make citations. Crossref metadata can be searched without a provider API key; do not treat a search result or DOI record as proof that a source supports a claim.

```powershell
wordassistant research search --query "[topic, method, or exact paper title]" --limit 10 --json
wordassistant research import-doi "10.xxxx/example" --json
$env:UNPAYWALL_EMAIL = "researcher@example.org"
wordassistant research open-access doi-10-xxxx-example --json
wordassistant research download doi-10-xxxx-example --json
wordassistant research excerpt doi-10-xxxx-example --query "[distinctive claim terms]" --json
```

The Unpaywall email is read from the named environment variable only for the request; it is not written to the evidence registry. The downloader requires an explicit supported reuse license, HTTPS, public-address resolution, safe redirects, bounded response size, PDF content type, and a PDF signature. It stores files under `.wordassistant/sources/` and records the source URL, license, retrieval time, and SHA-256. The source directory is git-ignored.

Read the returned bounded passage and compare it with the claim. Review the source record only after the passage actually supports the claim:

```powershell
wordassistant research review doi-10-xxxx-example `
  --claim "[Claim in your report]" `
  --support-excerpt "[Exact passage returned from the downloaded source]" `
  --support-location "Page 4" `
  --reviewed-by "[Reviewer or agent identity]" `
  --language en `
  --confirm-support `
  --json
```

`--language` records the language confirmed from the source; use `vi` for Vietnamese or `en` for English. When Crossref supplied raw author fields, review recalculates the display form and alphabetic sort key from that language. `review` checks the exact excerpt against the downloaded source and rechecks its hash. The explicit confirmation records that the reviewer also checked semantic support. If the source has no licensed OA PDF, use a source available through an authorized route and do not bypass access controls. A DOI, metadata record, or successful download alone cannot support a citation.

## 4. Compose and cite

Create a bounded version-1 composition JSON containing only verified report text. Attach evidence IDs to the claims they support; provide exact quotations as quotations with page/section locations. The selected profile supplies numeric citation style, author sorting, and the final bibliography heading:

```powershell
wordassistant compose report.docx `
  --output report-composed.docx `
  --content content.json `
  --evidence .wordassistant/evidence.json `
  --profile hcm-university-dacn-2026-2027 `
  --variant report `
  --json
```

For this profile, numeric citation labels are renumbered to match the bibliography order and grouped under `Tiếng Việt:` and `Tiếng Anh:`. Numbers remain unique across both groups. Crossref records display Vietnamese names in family/given order and English names as family name plus initials; bibliography paragraphs use bold author runs, italic title runs, and only publisher, publication, volume, issue, pages, year, and DOI values present in source metadata. Crossref records use their language-specific name key for author sorting. If you enter a source manually, supply `language` and `author_sort_key` in the evidence record when needed to match the guide. The profile rejects legacy and newly entered records until the source is downloaded, its supporting passage is checked, the source hash is recorded, and the record reaches `reviewed`. Do not edit the generated numbers by hand.

The final report must meet the selected profile's minimum of 10 real references. Do not create filler citations to reach the count. If a source was not checked, leave its claim unresolved and do not cite it. Citation insertion/composition reject discovery candidates and recheck reviewed source hashes; the HCMUNRE report profile requires the reviewed state for every evidence-linked citation, and the integrity audit catches missing, candidate, unreviewed, or modified linked sources.

## 5. Validate in Word

Run profile validation and the DOCX integrity audit, then render and inspect all pages. Use Microsoft Word to update TOC, figure/table lists, page numbers, and caption sequence fields; save the file, close and reopen it, and verify the styles, section breaks, border, headers/footers, fields, and layout persist. Report any unavailable native Word or visual check as not run. Do not report a fully compliant final report while required source content or required pages remain blank.

## Provider and document-format references

- [Crossref REST API](https://api.crossref.org/swagger-ui/index.html) documents the works endpoints and bibliographic query parameters. Crossref's [access documentation](https://www.crossref.org/documentation/retrieve-metadata/rest-api/access-and-authentication/) describes public API access.
- [Unpaywall REST API](https://unpaywall.org/api) documents the DOI lookup and required email query parameter. Its search endpoint was retired on 18 September 2026; this workflow uses DOI lookup only.
- [Creative Commons licenses](https://creativecommons.org/cc-licenses/) describes the license families accepted by the downloader. Recording a license does not imply permission to redistribute a downloaded copy.
- [pypdfium2 Python API](https://pypdfium2.readthedocs.io/en/stable/python_api.html) documents page text extraction used by the bounded source excerpt command.
- [python-docx sections](https://python-docx.readthedocs.io/en/stable/user/sections.html) and [styles](https://python-docx.readthedocs.io/en/stable/user/styles-using.html) describe the section and paragraph-style model used for persistent Word layout.
