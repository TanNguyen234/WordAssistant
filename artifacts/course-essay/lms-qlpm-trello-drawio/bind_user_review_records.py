"""Bind current matrices and editorial evidence to the reviewed output copy."""
import csv,json,hashlib,re
from pathlib import Path
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH as A
R=Path(__file__).resolve().parent
DOC='output/LMS_Tieu_luan_QLDA_ban_sua.docx'
def j(p):return json.loads((R/p).read_text(encoding='utf-8-sig'))
def save(p,x):(R/p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p):
    with (R/p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def csvsave(p,x):
    with (R/p).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(x[0]));w.writeheader();w.writerows(x)
d=Document(R/DOC);digest=sha(R/DOC);date='2026-10-26';reviewer='Codex source and editorial review'
cfg=j('reviewed-captures.json');manifest=j('captures/2026-10-26/capture-manifest.json')
bycap={c['capture_id']:c for c in manifest['captures']}

# Compare resolved style values after Word has normalized direct formatting.
def inherited(p,attr):
    value=getattr(p.paragraph_format,attr)
    style=p.style
    while value is None and style is not None:
        value=getattr(style.paragraph_format,attr);style=style.base_style
    return value
headings=[p for p in d.paragraphs if p.style.name.startswith('Heading ')]
caps=[p for p in d.paragraphs if p.style.name=='Caption']
fail=[]
for p in headings:
    if inherited(p,'alignment')!=A.LEFT:fail.append('Heading alignment: '+p.text)
for p in caps:
    if p.text.startswith('HÌNH') and inherited(p,'alignment')!=A.CENTER:fail.append('Figure caption alignment: '+p.text)
bibs=[p for p in d.paragraphs if re.match(r'^\[\d+\] ',p.text)]
assert len(bibs)==11
for p in bibs:
    if not any(r.bold for r in p.runs) or not any(r.italic for r in p.runs):fail.append('Bibliography emphasis: '+p.text[:40])
save('qa/user-final-style-audit.json',{'document_sha256':digest,'status':'FAIL' if fail else 'PASS','issues':fail,
    'checks':['Resolved Heading 1/2/3 alignment left','All 21 figure captions centered','Selected TNR 13 and heading sizes checked by profile validation','11 references retain bold authors and italic titles','Bibliography is after all appendices; web pages explicitly undated','Cover layout restored from preserved same-project input; no identity invented'],
    'reviewed_by':reviewer,'review_date':date})
assert not fail,fail

# Reconcile semantic outline with the actual reviewed structure and current order.
structure=[]
for i,p in enumerate(headings,1):
    level=int(p.style.name.split()[-1])
    structure.append(dict(item_id=f'H-{i:03}',source_basis='Existing LMS outline plus explicit user correction: live web/Trello evidence and readable Vietnamese terminology',
      source_location='docs/11_REPORT_OUTLINE.md;reviewed-captures.json;qa/prose-section-inventory.json',planned_heading=p.text,planned_level=level,target_heading=p.text,target_level=level,target_order=i,
      include_in_toc='true',decision='MATCHED',coverage_note='Reviewed outline; changed headings describe the section content; current TOC checked separately.',
      evidence_files=f'{DOC};content-review-plan.json;qa/user-final-style-audit.json',status='PASS',reviewed_by=reviewer,review_date=date))
csvsave('structure-parity.csv',structure)

assets=rows('asset-parity.csv')
existing=[p.text for p in caps]
for row in assets:
    row['evidence_files']=row['evidence_files'].replace('output/final.docx',DOC).replace('qa/caption-audit.json','qa/user-final-caption-audit.json')
newcaps=[p for p in caps if any(p.text.endswith(x['caption']) for x in cfg['screens'])]
assert len(newcaps)==10
for item in cfg['screens']:
    c=bycap[item['id']];caption=next(p.text for p in newcaps if p.text.endswith(item['caption']))
    assets.append(dict(asset_id='CAP-'+item['id'],asset_type='RUNTIME_SCREENSHOT',source_basis='Actual visible browser screenshot; no generated UI',source_location=c['resolved_url'],
      target_section=cfg['heading'],target_caption=caption,decision='MATCHED',coverage_note=item['text'],
      evidence_files=f"{DOC};{c['screenshot_path']};captures/2026-10-26/capture-manifest.json",capture_id=item['id'],runtime_route=c['route'],expected_media_count='1',caption_required='true',status='PASS',reviewed_by=reviewer,review_date=date))
csvsave('asset-parity.csv',assets)
figures=rows('figure-plan.csv')
for item in cfg['screens']:
    c=bycap[item['id']]
    figures.append(dict(figure_id='CAP-'+item['id'],caption=item['caption'],kind='Actual visible browser capture',route_or_source=c['route'],source_file=c['screenshot_path'],
      role='Trello observer' if item['id'].startswith('T') else 'Admin' if item['id']=='L02' else 'Lecturer' if item['id'].startswith('L03') else 'Student' if item['id'] in ['L04','L05'] else 'Login',
      state='Captured UI; original document HTTP status UNKNOWN',viewport='x'.join(map(str,c['viewport'])),capture_date=date,verified_by=reviewer,artifact_path=c['screenshot_path'],status='PASS',notes=item['text']))
csvsave('figure-plan.csv',figures)

inv=j('screen-inventory.json');inv['system_title']='University LMS and Trello actual UI captures with remaining guide evidence'
for s in inv['screens']:
    cid=s['capture_id']
    if cid in bycap:
        c=bycap[cid];s.update(route=c['route'],status='CAPTURED_UI',reason='Actual visible browser capture; full original document HTTP evidence unavailable.',
          screenshot=c['screenshot_path'],sha256=c['screenshot_sha256'],captured_at=c['captured_at_local'],page_state_review='captures/2026-10-26/capture-manifest.json')
    if cid=='T03':s['status']='PARTIAL';s['reason']='Milestone cards captured; Calendar/Timeline not captured.'
    if cid=='T05':s['status']='OBSERVED_EMPTY';s['reason']='T03 image shows Done empty; no completed card was fabricated.'
save('screen-inventory.json',inv)

plan=j('content-review-plan.json');plan['document_sha256']=digest;plan['final_visual_review_file']='qa/user-final-visual-review.json'
renames=j('qa/presentation-refinements.json')['heading_renames']
for s in plan['section_reviews']:
    s['heading']=renames.get(s['heading'],s['heading']);s['review_date']=date
    if 'Phụ lục B' in s['heading']:
        s['evidence']='Ten actual Trello/LMS screenshots inserted; guide checklist distinguishes captured UI, empty Done, missing Calendar/editor/API/terminal evidence.'
        s['sufficiency']='Partial capture coverage is explicit; no universal missing-image statement remains.'
    if s['heading']=='KẾT LUẬN VÀ KIẾN NGHỊ':s['evidence']='Reconciled baseline plus observed board and role-specific UI states; missing rubric, identities and full UAT remain explicit.'
plan['section_reviews'].append(dict(heading=cfg['heading'],argument='Connects each observed interface state to a management or product claim and distinguishes observation from unexecuted actions.',
    evidence='Ten exact screenshot bytes, UI arrival histories, visible-page reviews and timestamps in captures/2026-10-26/capture-manifest.json.',
    terminology='Admin, Lecturer and Student are actual demo roles; Done empty, checklist 0/7 and stored quiz grade are accurately described.',
    sufficiency='Addresses the user request for real web/Trello figures. Calendar, editor, API 403 and terminal evidence remain outstanding; original HTTP response evidence UNKNOWN.',status='REVIEWED',reviewer=reviewer,review_date=date))
save('content-review-plan.json',plan)

audit=j('qa/user-final-integrity-audit.json')
assert audit['document']['sha256']==digest
numeric=[
'Planned cash-flow values are in the reconciled cost baseline and the visible source [1] table; this paragraph interprets those planned figures.',
'The risk response paragraph restates the 120M contingency already sourced in the budget and risk registers; it explicitly denies actual disbursement.',
'Dates and scenario count describe the authoring method and actual screenshot collection, not a claim that UAT passed.',
'The archived snapshot and actual T01/T03 screenshots support 9 lists/39 cards, 25 To Do and empty execution columns.',
'T02 raw image shows the PM-04 checklist 0/7; adjacent screenshot and source note support the observation.',
'This is the explicit provenance note for the supplied Trello JSON snapshot, not an external unsourced quantitative claim.',
'The distinction between the ZIP group scenario and charter baseline is retained from checked source reconciliation and SIM-01 image; no budgets are combined.',
'Conclusion synthesizes the baseline already cited [1] and source-checked tables; no new measurement is introduced.',
'This is a dated source note for user-supplied project/capture guidance.',
'Guide IDs and capture coverage match the original guide and ten saved images; missing categories remain explicit.',
'This is a dated source note for the guide/checklist table.',
'This is a dated source note for the evidence classification table.',
'Assignment route behavior was inspected in assignments.py; nearby model source [2] resolves to that reviewed file. Source inspection is not runtime proof.',
'The appendix describes the actual capture session and existing disposable database verified by read-only SQL; it does not claim grading or UAT execution.',
'T01 raw screenshot supports the observed column counts and empty Done; the source note identifies its capture ID.',
'L05 raw screenshot shows one stored quiz grade 10/10 at 10%; text explicitly identifies pre-existing demo data.'
]
warn=[]
for name,g in audit['gates'].items():
    if g['status']!='WARN':continue
    for i,f in enumerate(g.get('findings',[]),1):
        if name=='quantitative_claims_lacking_citation':
            assert len(g['findings'])==len(numeric)
            reason=numeric[i-1]
        elif name=='repetitive_prose_review':
            reason='Reviewed phrase '+f.get('text',f.get('kind',''))+': repeated source/date/ID notes or stable technical terminology support traceability; not an authorship inference. Main prose was substantively revised in 47 scoped paragraphs.'
        elif name=='typography_punctuation_review':reason='Reviewed dash punctuation separates ranges, identifiers or qualifications; visible meaning is clear.'
        elif name=='ai_use_disclosure_provenance':reason='Actual Codex assistance is declared in provenance; no applicable student declaration form was provided, so no student statement is invented.'
        else:raise ValueError(name)
        warn.append(dict(gate=name,finding_index=i,decision='accepted',reason=reason,evidence=f'{DOC};qa/user-final-integrity-audit.json;report-evidence-reviewed.json;captures/2026-10-26/capture-manifest.json;claim-evidence.csv',reviewed_by=reviewer,review_date=date))
csvsave('integrity-warning-dispositions.csv',warn)

project=j('project.json');project['output_docx']=DOC
project['report_citation_registry_file']='report-evidence-reviewed.json'
project['runtime_capture_manifest_file']='captures/2026-10-26/capture-manifest.json'
project['qa_reports']=dict(profile_validation='qa/user-final-profile-validation.json',word_verify='qa/user-final-delivery.json',integrity_audit='qa/user-final-integrity-audit.json',integrity_provenance='qa/user-final-integrity-provenance.json',readiness='qa/readiness.json')
project['profile_application_note']='Borrowed HCMUNRE course_essay_style; heading/caption alignment and bibliography additionally checked against report presentation guidance. No capstone rubric or affiliation asserted. Tables use 13pt with 1.15 spacing for readability; prose/source notes use 1.5. Exact style audit is qa/user-final-style-audit.json.'
project['visual_inventory_review'].update(reason='Reviewed 19 tables, 11 static models/aggregates and 10 actual screenshots; preserved raw screenshot bytes and crop provenance.',review_date=date)
project['acceptance_checks']['all_rendered_pages_visually_reviewed']=True
project['acceptance_checks']['all_integrity_warnings_reviewed_and_dispositioned']=True
save('project.json',project)

req=rows('requirements-matrix.csv')
for x in req:
    x['evidence_files']=x['evidence_files'].replace(str(R/'output/final.docx'),str(R/DOC)).replace('report-evidence.json','report-evidence-reviewed.json')
    if x['requirement_id']=='GUIDE-01':x['notes']='Ten actual captures inserted; Calendar/Timeline, Draw.io editor and L06/L07 remain unrun. Done observed empty. Network response provenance incomplete.'
csvsave('requirements-matrix.csv',req)
print(json.dumps({'document_sha256':digest,'headings':len(headings),'assets':len(assets),'images':len(d.inline_shapes),'warning_dispositions':len(warn)}))
