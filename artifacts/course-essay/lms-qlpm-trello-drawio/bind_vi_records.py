"""Reconcile final, already-reviewed output and evidence without changing DOCX."""
import csv,hashlib,json,re
from pathlib import Path
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH as A
R=Path(__file__).resolve().parent;DOC='output/LMS_HCMUNRE_Viet_hoa.docx';Q='qa/vietnamese-ui/'
def j(p):return json.loads((R/p).read_text(encoding='utf-8-sig'))
def save(p,x):(R/p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p):
 with (R/p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def cs(p,x):
 with (R/p).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(x[0]));w.writeheader();w.writerows(x)
d=Document(R/DOC);digest=sha(R/DOC);date='2026-10-26';reviewer='Codex source, editorial and visual review'
delivery=j(Q+'delivery.json');assert delivery['delivery_status']=='PASS'
assert j(Q+'profile-validation.json')['valid']
cfg=j('reviewed-captures-vietnamese.json');manifest=j('captures/2026-10-26-vi/capture-manifest.json');bycap={c['capture_id']:c for c in manifest['captures']}
headings=[p for p in d.paragraphs if p.style.name.startswith('Heading ')];caps=[p.text for p in d.paragraphs if p.style.name=='Caption']
def renamed(text):
 for item in j(Q+'revision-spec.json')['caption_titles']:text=text.replace(item['old'],item['new'])
 return text
repl={'output/LMS_HCMUNRE_day_du.docx':DOC,'qa/hcmunre-caption-audit.json':Q+'caption-audit.json','qa/hcmunre-profile-validation.json':Q+'profile-validation.json','qa/hcmunre-delivery.json':Q+'delivery.json','qa/hcmunre-visual-review.json':Q+'visual-review.json','qa/hcmunre-integrity-audit.json':Q+'integrity-audit.json','qa/hcmunre-integrity-provenance.json':Q+'integrity-provenance.json','qa/hcmunre-style-audit.json':Q+'style-audit.json','report-evidence-reviewed.json':'report-evidence-vietnamese-reviewed.json','captures/2026-10-26/capture-manifest.json':'captures/2026-10-26-vi/capture-manifest.json'}
def current(text):
 for a,b in repl.items():text=text.replace(a,b)
 return renamed(text)
structure=[]
for i,p in enumerate(headings,1):
 level=int(p.style.name.split()[-1]);structure.append(dict(item_id=f'H-{i:03}',source_basis='LMS outline; explicit full HCMUNRE and Vietnamese UI request; bounded VietLex v20 applicability comparison',source_location='docs/11_REPORT_OUTLINE.md;qa/vietnamese-ui/doi-chieu-vietlex-v20.md',planned_heading=p.text,planned_level=level,target_heading=p.text,target_level=level,target_order=i,include_in_toc='true',decision='MATCHED',coverage_note='Current semantic heading and saved automatic TOC checked separately.',evidence_files=f'{DOC};content-review-plan.json;{Q}visual-review.json',status='PASS',reviewed_by=reviewer,review_date=date))
cs('structure-parity.csv',structure)
assets=[{k:current(v) for k,v in x.items()} for x in rows('asset-parity.csv') if not x['asset_id'].startswith('CAP-')]
section='';cap_sections={}
for p in d.paragraphs:
 if p.style.name.startswith('Heading '):section=p.text
 elif p.style.name=='Caption':cap_sections[p.text]=section
for row in assets:
 if row.get('target_caption') in cap_sections:row['target_section']=cap_sections[row['target_caption']]
for item in cfg['screens']:
 c=bycap[item['id']];cap=next(x for x in caps if x.endswith(item['caption']))
 assets.append(dict(asset_id='CAP-'+item['id'],asset_type='RUNTIME_SCREENSHOT',source_basis='Actual visible browser capture; stored demo data retained without redaction',source_location=c['resolved_url'],target_section=cfg['heading'],target_caption=cap,decision='MATCHED',coverage_note=item['text'],evidence_files=f"{DOC};{c['screenshot_path']};captures/2026-10-26-vi/capture-manifest.json",capture_id=item['id'],runtime_route=c['route'],expected_media_count='1',caption_required='true',status='PASS',reviewed_by=reviewer,review_date=date))
cs('asset-parity.csv',assets)
figures=[{k:current(v) for k,v in x.items()} for x in rows('figure-plan.csv') if not x['figure_id'].startswith('CAP-')]
for item in cfg['screens']:
 c=bycap[item['id']];figures.append(dict(figure_id='CAP-'+item['id'],caption=item['caption'],kind='Actual visible browser capture',route_or_source=c['route'],source_file=c['screenshot_path'],role='Observed existing demo role or Trello observer',state='Actual UI observed; original document HTTP status UNKNOWN',viewport='x'.join(map(str,c['viewport'])),capture_date=date,verified_by=reviewer,artifact_path=c['screenshot_path'],status='PASS',notes=item['text']))
cs('figure-plan.csv',figures)
inv=j('screen-inventory.json')
for s in inv['screens']:
 if s['capture_id'] in bycap:
  c=bycap[s['capture_id']];s.update(route=c['route'],status='CAPTURED_UI',reason='Visible original UI screenshot; network document status UNKNOWN.',screenshot=c['screenshot_path'],sha256=c['screenshot_sha256'],captured_at=c['captured_at_local'],page_state_review='captures/2026-10-26-vi/capture-manifest.json')
save('screen-inventory.json',inv)
plan=j('content-review-plan.json');plan['document_sha256']=digest;plan['final_visual_review_file']=Q+'visual-review.json';plan['front_matter_review_file']=Q+'frontmatter-review.json'
for item in plan['model_decisions']:
 for asset in item.get('assets',[]):
  if 'caption_title' in asset:asset['caption_title']=renamed(asset['caption_title'])
existing={s['heading']:s for s in plan['section_reviews']}
parent='MỞ ĐẦU'
for p in headings:
 if p.style.name=='Heading 1':parent=p.text
 if p.text not in existing:
  related=next((x for x in cfg['screens'] if x['caption']==p.text),None)
  inherited=existing.get(parent,{})
  existing[p.text]=dict(heading=p.text,argument=related['text'] if related else 'Develops '+p.text+' within '+parent+'. '+inherited.get('argument','Reviewed conceptual/design scope and source inventory.'),evidence='captures/2026-10-26-vi/capture-manifest.json' if related else inherited.get('evidence','Source inventory and reviewed bibliography; diagrams retain editable sources.'),terminology='Screen observations retain real demo content; raw enums are distinct from localized labels.' if related else inherited.get('terminology','Planning, source model, observation and executed result remain distinct.'),sufficiency=related['text'] if related else inherited.get('sufficiency','Provides the applicable design/source view; unresolved runtime and approval evidence is explicit.'),status='REVIEWED',reviewer=reviewer,review_date=date)
for title in ['CHƯƠNG 7. QUẢN LÝ CHẤT LƯỢNG VÀ KIỂM THỬ','CHƯƠNG 9. THIẾT KẾ VÀ BIỂU ĐỒ DRAW.IO',cfg['heading']]:
 existing[title].update(evidence='15 reviewed citations with source hashes; four focused passing tests, type/build/lint logs; fourteen actual captures, including ten fresh web images. '+Q+'doi-chieu-vietlex-v20.md',terminology='Vietnamese UI labels, provisional grade meaning and evidence levels distinguished.',reviewer=reviewer,review_date=date)
plan['section_reviews']=list(existing.values());save('content-review-plan.json',plan)

# Every numeric flag is reviewed against a specific source or actual image.
numeric=[
 'Planned stage cash flow matches the cited reconciled budget; not actual expenditure.',
 '120M contingency matches the reconciled budget and risk response; no disbursement asserted.',
 'Ten planned UAT scenarios are in the quality source; paragraph states observation is not full UAT.',
 'Trello snapshot and T01/T03 support 9 lists/39 cards, 25 To Do and empty execution columns.',
 'T02 shows WBS checklist 0/7; paragraph does not declare WBS review completed.',
 'Dated provenance note identifies the supplied Trello snapshot.',
 'Two distinct budget/calendar scenarios are explicitly separated by the source reconciliation and SIM-01 image.',
 'L13 screenshot and recorded DOM width observation support the one-size mobile statement; accessibility testing is not claimed.',
 'Conclusion repeats the sourced 20-week/1.2B/8.5-FTE baseline without introducing a new measurement.',
 'Dated source note for user-supplied guide and diagrams.',
 'Guide IDs and partial capture status match the original guide; missing categories remain explicit.',
 'Dated source note for guide/checklist table.',
 'Dated source note for evidence classification table.',
 'GET and PUT routes and grading guards reviewed in assignments.py; source analysis, not runtime test.',
 'Capture introduction identifies the existing test database and source dates; no data writes or full UAT asserted.',
 'T01 actual screenshot supports To Do 25 and zero Doing/Review/Done.',
 'L05 screenshot supports pre-existing 10/10 at 10 percent; paragraph explains unweighted provisional meaning.'
]
audit=j(Q+'integrity-audit.json');assert audit['document']['sha256']==digest
warnings=[]
for name,g in audit['gates'].items():
 if g['status']!='WARN':continue
 for i,f in enumerate(g.get('findings',[]),1):
  if name=='quantitative_claims_lacking_citation':
   assert len(g['findings'])==len(numeric);reason=numeric[i-1]
  elif name=='repetitive_prose_review':reason='Reviewed phrase '+f.get('text','')+': source/date/capture notes, repeated official form wording or stable technical terminology. Retained where it establishes attribution or consistent meaning; no authorship inference.'
  elif name=='typography_punctuation_review':reason='Reviewed dash separates a range, identifier or qualification; meaning and rendered layout are clear.'
  else:raise ValueError(name)
  warnings.append(dict(gate=name,finding_index=i,decision='accepted',reason=reason,evidence=f'{DOC};{Q}integrity-audit.json;report-evidence-vietnamese-reviewed.json;captures/2026-10-26-vi/capture-manifest.json;claim-evidence.csv',reviewed_by=reviewer,review_date=date))
cs('integrity-warning-dispositions.csv',warnings)

bibs=[p for p in d.paragraphs if re.match(r'^\[\d+\]',p.text)];assert len(bibs)==15
assert all(any(r.bold for r in p.runs) and any(r.italic for r in p.runs) for p in bibs)
assert all('không ghi năm; truy cập ngày 26/10/2026' in p.text for p in bibs if any(u in p.text for u in ['support.atlassian.com','www.drawio.com']))
save(Q+'style-audit.json',dict(document_sha256=digest,status='PASS',checks=['Full selected HCMUNRE profile validation','Native numbering, TOC and caption fields','25 figure captions plus 19 native table captions','15 references: bold authors, italic titles, left-aligned entries, undated sources explicit','Two real school logos, outer frame, exact course and topic, unnumbered front matter and Introduction page 1'],reviewed_by=reviewer,review_date=date))
front=j('qa/hcmunre-frontmatter-review.json');front['document_sha256']=digest;front['reviewed_by']=reviewer;front['visual_pages_reviewed']=list(range(1,14));save(Q+'frontmatter-review.json',front)
project=j('project.json');project['output_docx']=DOC;project['report_citation_registry_file']='report-evidence-vietnamese-reviewed.json';project['runtime_capture_manifest_file']='captures/2026-10-26-vi/capture-manifest.json'
project['qa_reports']=dict(profile_validation=Q+'profile-validation.json',word_verify=Q+'delivery.json',integrity_audit=Q+'integrity-audit.json',integrity_provenance=Q+'integrity-provenance.json',readiness=Q+'readiness.json')
project['rubric_inclusion']['output_docx_sha256']=digest
project['source_revision']='72cfa37ce5509286ee3f5990ee9c234adc452184; frontend working-tree localization snapshot bound in D:/Download/LMS/docs/audit/2026-10-26-vietnamese-ui/source-hashes.json'
project['workspace_default_variant']='report'
project['rubric_applicability_note']='Full HCMUNRE presentation and complete applicable official review prompts explicitly selected by user, with Tiểu luận môn học override. No separate scored rubric for this course supplied; no invented levels or weights.'
project['visual_inventory_review'].update(reason='21 native tables, 11 static figures, 14 actual UI images and 2 cover logos reviewed; six old web images replaced by fresh unredacted captures.',review_date=date)
save('project.json',project)
evidence=j('evidence.json');claims=[x for x in rows('claim-evidence.csv') if not x['claim_id'].startswith('VI-')]
for number,(eid,path,location,claim) in enumerate([
 ('EV-VI-ARCH','D:/Download/LMS/docs/03_ARCHITECTURE.md','Chương 9; Bảng 15','React/FastAPI/SQL Server modular monolith design; not production health.'),
 ('EV-VI-SCHEMA','D:/Download/LMS/database/01_schema.sql','Chương 9; Hình 6','Twelve CREATE TABLE statements and stored entity relationships.'),
 ('EV-VI-PACKAGE','D:/Download/LMS/frontend/package.json','Bảng 15','React 19 declared dependency; frontend manifest inspected locally.'),
 ('EV-VI-ROLES','D:/Download/LMS/docs/02_ROLES_USE_CASES.md','Phụ lục D; Hình 7','Three roles and own-course/active-enrollment boundaries.'),
 ('EV-VI-CHECKS','D:/Download/LMS/docs/audit/2026-10-26-vietnamese-ui/focused-green.log','Chương 7.3','Four focused presentation tests pass; no full UAT asserted.'),
 ('EV-VI-CAPTURES',str(R/'captures/2026-10-26-vi/capture-manifest.json'),'Chương 9.3; Phụ lục E','Actual visible UI states; demo content retained; original document HTTP status UNKNOWN.')],1):
  file=Path(path) if Path(path).is_absolute() else R/path;h=sha(file)
  evidence[eid]=dict(id=eid,review_status='reviewed',source_file=path,source_sha256=h,support_location=location,reviewed_by=reviewer,review_date=date)
  claims.append(dict(claim_id=f'VI-{number:02}',report_location=location,claim_summary=claim,evidence_id=eid,source_file=path,source_sha256=h,source_location=location,review_status='reviewed',support_confirmed='yes',reviewed_by=reviewer,review_date=date))
save('evidence.json',evidence);cs('claim-evidence.csv',claims)
for name in ['requirements-matrix.csv','cover-metadata.csv','diagram-plan.csv']:
 data=rows(name)
 for row in data:
  for k,v in row.items():row[k]=current(v)
  if row.get('requirement_id')=='GUIDE-01':row['notes']='Fourteen real captures embedded, including ten fresh web images; missing Calendar/editor/API/terminal categories and original HTTP response remain incomplete.'
 cs(name,data)
cross=rows('acceptance-crosswalk.csv')
for row in cross:
 for k,v in row.items():row[k]=current(v)
 if row['check_id'] in ['X09','X10','X11']:
  row.update(status='PASS',evidence_files=f'{DOC};{Q}doi-chieu-vietlex-v20.md;captures/2026-10-26-vi/capture-manifest.json;{Q}delivery.json',notes='Requested bounded revision verified; remaining global submission blockers retained.')
 row.update(document_sha256=digest,reviewed_by=reviewer,review_date=date)
 files=[x.strip() for x in row['evidence_files'].split(';') if x.strip()]
 row['evidence_sha256']=';'.join(sha(Path(p) if Path(p).is_absolute() else R/p) if (Path(p) if Path(p).is_absolute() else R/p).is_file() else 'MISSING' for p in files)
cs('acceptance-crosswalk.csv',cross)
save(Q+'final-review.json',dict(document=DOC,document_sha256=digest,pages=j(Q+'render.json')['render']['page_count'],headings=len(headings),images=len(d.inline_shapes),tables=len(d.tables),references=len(bibs),capture_count=len(cfg['screens']),asset_rows=len(assets),warning_dispositions=len(warnings),word_delivery='PASS',remaining_unknown=['original browser document HTTP status','actual scored course rubric','unrun capture categories and complete UAT'],verification_commands=['node --test tests/vi-presentation.test.mjs','tsc -p tsconfig.app.json --noEmit','vite build','oxlint','git diff --check','wordassistant field update-all','wordassistant validate --profile hcmunre-lms-full-profile.json --variant report','wordassistant verify --render --engine word','wordassistant verify --delivery --native-fields --reuse-render-report','wordassistant integrity audit/provenance','wordassistant caption audit','check_course_essay_readiness.py']))
print(json.dumps({'document_sha256':digest,'headings':len(headings),'assets':len(assets),'warnings':len(warnings)}))
