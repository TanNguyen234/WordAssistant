from pathlib import Path
import csv, hashlib, json
from datetime import datetime

W = Path(r'D:\Download\ProfessionalLegalRAG\artifacts\course-essay-vietlex-20261020')
ROOT = Path(r'D:\Download\ProfessionalLegalRAG')
DOC = W/'output'/'VietLex_DoAnChuyenNganh_RubricCriteria_FinalQA_20261025_v6.docx'
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write_json(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
def read_csv(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f)), list(csv.DictReader(Path(path).open(encoding='utf-8-sig', newline='')))[0].keys()
def write_csv(path, rows, fields):
    with Path(path).open('w', encoding='utf-8-sig', newline='') as f:
        w=csv.DictWriter(f, fieldnames=list(fields), extrasaction='ignore')
        w.writeheader(); w.writerows(rows)

doc_hash=sha(DOC)
sm=json.loads((W/'source'/'source_manifest.json').read_text(encoding='utf-8'))
revision=f"{sm['git_head']} ({sm['git_worktree']} source worktree; status SHA-256 {sm['git_status_sha256']})"
source_hashes={x['path']:x['sha256'] for x in sm['files']}
capture_path='assets/runtime-captures-clickthrough-20261023/capture-manifest.json'
old_screen=json.loads((W/'screen-inventory-clickthrough-v12.json').read_text(encoding='utf-8'))
manifest_path=W/capture_path
manifest_hash=sha(manifest_path)
selected={'F06','F07','R03'}
source_routes_path=W/'qa'/'route-source-inventory-v13.json'
route_records=json.loads(source_routes_path.read_text(encoding='utf-8'))
full_templates={
 '/':'index.html','/search':'legal_search.html','/documents/{document_id}':'legal_document.html',
 '/legal-status':'legal_status.html','/privacy':'privacy.html','/terms':'terms.html',
 '/evaluation-lab':'evaluation_lab.html','/workspaces':'research_workspaces.html',
 '/workspaces/{workspace_id}':'research_workspace.html','/login':'account_form.html',
 '/register':'account_form.html','/verify-email':'account_form.html',
 '/forgot-password':'account_form.html','/reset-password':'account_form.html','/settings':'settings.html',
 '/admin':'admin.html','/admin/requests':'admin_requests_page.html',
 '/admin/usage':'admin_usage_page.html','/admin/providers':'admin_providers_page.html',
 '/admin/system':'admin_system_page.html','/admin/evaluations':'evaluation_lab.html',
 '/admin/legal-registry':'admin_legal_registry.html','/admin/corpus':'admin_corpus_queue.html',
 '/admin/feedback':'admin_feedback_queue.html','/admin/users':'admin_users_page.html',
 '/admin/audit':'admin_audit_page.html'
}
partial_templates={
 '/sessions':'sidebar_sessions.html','/sessions/{session_id}':'chat_history_messages.html',
 '/admin/stats':'admin_stats.html','/admin/logs':'admin_logs.html',
 '/admin/details/{trace_id}':'admin_details.html'
}
downloads={'/admin/export.csv':'CSV attachment','/sessions/{session_id}/export':'session export'}
access={}
for r in full_templates:
    access[r]='admin_required' if r.startswith('/admin') else 'public'
access.update({'/settings':'authenticated_user_required',
 '/verify-email':'email_token_required for successful verification',
 '/reset-password':'reset_token_required for successful password update',
 '/workspaces/{workspace_id}':'owner_scoped_or_anonymous_client_scoped'})
for route in ['/','/search','/documents/{document_id}','/legal-status','/privacy','/terms','/evaluation-lab','/workspaces','/login','/register','/forgot-password']:
    access[route]='public or anonymous flow; endpoint may show unavailable state by environment/config'
route_by_key={}
for rr in route_records:
    rel=rr['file']
    fp=ROOT/rel
    if fp.is_file():
        rr['sha256']=sha(fp)
    route=rr['route']; method=rr['method']
    rr['template']=None
    if method=='GET' and route in full_templates:
        rr['classification']='full_html_page'
        rr['template']=full_templates[route]
        rr['access']=access.get(route,'source-defined')
    elif method=='GET' and route in partial_templates:
        rr['classification']='html_partial'
        rr['template']=partial_templates[route]
        rr['access']='admin_required' if route.startswith('/admin') else 'session_or_anonymous_owner_scoped'
    elif method=='GET' and route in downloads:
        rr['classification']='download'
        rr['template']=None
        rr['access']='admin_required' if route.startswith('/admin') else 'owner_or_client_scoped'
    elif 'JSONResponse' in rr.get('response_calls',[]):
        rr['classification']='json_api'
    elif 'RedirectResponse' in rr.get('response_calls',[]):
        rr['classification']='redirect'
    elif method!='GET':
        rr['classification']='action'
    elif rr.get('html_view') and route.startswith('/admin'):
        rr['classification']='admin_html_or_endpoint_requires_review'
    elif not rr.get('html_view'):
        rr['classification']='api_or_operational_non_screen'
    else:
        rr['classification']='other_html_handler_not_mapped'
    route_by_key[(method,route)]=rr

route_details=[]
for route,template in full_templates.items():
    rr=route_by_key.get(('GET',route))
    if rr is None: raise AssertionError(f'missing source route {route}')
    tp=Path('app/templates')/template
    template_file=ROOT/tp
    if not template_file.is_file(): raise FileNotFoundError(template_file)
    runtime_records=[x for x in old_screen['screens'] if
        (route=='/' and x.get('asset_id')=='F06') or
        (route=='/search' and x.get('asset_id')=='F07') or
        (route=='/documents/{document_id}' and x.get('asset_id')=='R03')]
    route_details.append({
        'route':route,'method':'GET','classification':'full_html_page',
        'handler':rr['handler'],'source_file':rr['file'],'source_line':rr['line'],
        'source_sha256':rr['sha256'],'template':str(tp).replace('\\','/'),
        'template_sha256':sha(template_file),'access':access.get(route,'source-defined'),
        'runtime_capture_ids':[x['asset_id'] for x in runtime_records],
        'included_in_docx':bool(runtime_records),'runtime_capture_status':'CAPTURED' if runtime_records else 'NOT_CAPTURED'
    })
partial_details=[]
for route,template in partial_templates.items():
    rr=route_by_key.get(('GET',route))
    if rr is None: raise AssertionError(f'missing partial route {route}')
    tp=Path('app/templates')/template
    partial_details.append({
        'route':route,'method':'GET','classification':'html_partial',
        'handler':rr['handler'],'source_file':rr['file'],'source_line':rr['line'],
        'source_sha256':rr['sha256'],'template':str(tp).replace('\\','/'),
        'template_sha256':sha(ROOT/tp),'access':'admin_required' if route.startswith('/admin') else 'session_or_anonymous_owner_scoped',
        'count_as_screen':False
    })

# Check embedded image blobs against the image files and selected runtime capture hashes.
from docx import Document
doc=Document(DOC)
def sha_bytes(data): return hashlib.sha256(data).hexdigest()
shape_part_hashes=[]
for shape in doc.inline_shapes:
    blip=shape._inline.graphic.graphicData.pic.blipFill.blip
    shape_part_hashes.append(sha_bytes(doc.part.rels[blip.embed].target_part.blob))
def sha_bytes(data): return hashlib.sha256(data).hexdigest()
asset_png={
 'F01':'assets/uml/01-screen-map-v14.png','F02':'assets/uml/02-use-cases.png',
 'F05':'assets/uml/05-retrieval-classes.png','F04':'assets/uml/04-retrieval-architecture.png',
 'F08':'assets/uml/06-ingestion-dataflow.png','F03':'assets/uml/03-chat-sequence.png',
 'F09':'assets/uml/07-official-source-read-sequence.png'
}
shape_for={'LOGO-001':0,'LOGO-002':1,'F01':2,'F02':3,'F05':4,'F04':5,'F08':6,'F03':7,'F06':8,'F07':9,'F09':10,'R03':11}
for aid,path in asset_png.items():
    expected=sha(W/path)
    if shape_part_hashes[shape_for[aid]]!=expected:
        raise AssertionError(f'embedded PNG mismatch for {aid}')
capture_by_id={x['asset_id']:x for x in old_screen['screens']}
for aid in selected:
    c=capture_by_id[aid]
    actual=sha(W/c['screenshot_path'])
    if actual!=c['screenshot_sha256']: raise AssertionError(f'capture hash mismatch for {aid}')
    if not c.get('arrived_via_visible_ui') or c.get('http_status')!=200 or c.get('document_status')!=200:
        raise AssertionError(f'capture acceptance failed for {aid}')
    if c.get('console_errors') or c.get('console_warnings'):
        raise AssertionError(f'capture console not clear for {aid}')

for rr in route_records:
    if rr['method']=='GET' and rr['route'] in full_templates:
        rr['screenshot_asset_ids']=[x['asset_id'] for x in old_screen['screens'] if
            x.get('asset_id') in selected and (
                (rr['route']=='/' and x['asset_id']=='F06') or
                (rr['route']=='/search' and x['asset_id']=='F07') or
                (rr['route']=='/documents/{document_id}' and x['asset_id']=='R03'))]
    else: rr['screenshot_asset_ids']=[]
inventory={
 'schema_version':3,'system_title':old_screen.get('system_title','VietLex'),
 'source_revision':revision,'source_snapshot_file':'source/source_manifest.json',
 'source_snapshot_sha256':sha(W/'source'/'source_manifest.json'),
 'document_path':'output/'+DOC.name,'document_sha256':doc_hash,
 'route_source_inventory_file':'qa/route-source-inventory-v13.json',
 'route_source_inventory_sha256':sha(source_routes_path),
 'route_count':len(route_records),'route_class_counts':{},
 'runtime_capture_manifest':capture_path,'runtime_capture_manifest_sha256':manifest_hash,
 'capture_context':old_screen.get('capture_context'),
 'runtime_capture_instances':len(capture_by_id)+len(old_screen.get('supplemental_captures',[])),
 'runtime_unique_captured_routes':old_screen.get('captured_route_count'),
 'runtime_captures':[],
 'full_html_pages':route_details,'partials':partial_details,
 'downloads':[{'route':r,'method':'GET','classification':'download','detail':v} for r,v in downloads.items()],
 'not_captured':old_screen.get('not_captured',[]),
 'live_deployment_revision_confirmation':old_screen.get('live_deployment_revision_confirmation')
}
for rr in route_records:
    inventory['route_class_counts'][rr['classification']]=inventory['route_class_counts'].get(rr['classification'],0)+1
for c in old_screen['screens']:
    c=dict(c)
    c['included_in_docx']=c.get('asset_id') in selected
    c['exclusion_reason']=None if c['included_in_docx'] else 'Captured historical UI state retained in manifest; excluded from v6 because it does not add evidence to the selected home → search results → document detail flow.'
    inventory['runtime_captures'].append(c)
inventory['non_screen_routes']=[r for r in route_records if r['classification'] not in {'full_html_page','html_partial'}]
write_json(W/'screen-inventory-v14.json',inventory)

# Structure parity: bind actual headings, actual levels/order and current Word evidence.
rows,fieldnames=read_csv(W/'structure-parity-clickthrough-v12.csv')
actual=[(p.text,p.style.name[-1]) for p in doc.paragraphs if p.style.name in {'Heading 1','Heading 2','Heading 3'}]
rows=sorted(rows,key=lambda r:int(r['target_order']))
assert len(rows)==len(actual)==105
for i,(r,(title,level)) in enumerate(zip(rows,actual),1):
    old=r['target_heading']
    if old=='Ảnh chụp runtime các trang VietLex': r['planned_heading']=r['target_heading']='Ảnh chụp runtime: luồng tra cứu chính'
    if (r['target_heading'],str(r['target_level']))!=(title,str(level)):
        raise AssertionError(f'heading mismatch {i}: {r["target_heading"]!r}/{r["target_level"]} != {title!r}/{level}')
    r['planned_heading']=r['target_heading']
    r['planned_level']=str(level)
    r['include_in_toc']='true'
    r['document_sha256']=doc_hash
    r['qa_report']='qa/verify-v6-render.json'
    r['status']='PASS'
    r['reviewed_by']='Codex source, outline and Word field review'
    r['review_date']='2026-10-25'
    r['evidence_files']=r['evidence_files'].replace('VietLex_DoAnChuyenNganh_RubricCriteria_FinalQA_20261025_v5.docx',DOC.relative_to(W).as_posix())
    r['evidence_files']=r['evidence_files'].replace('verify-vietlex-rubriccriteria-final-20261025.json','verify-v6-render.json')
write_csv(W/'structure-parity-v14.csv',rows,fieldnames)

# Asset parity: exactly the 15 tables and 12 embedded media objects in the current DOCX.
assets,afields=read_csv(W/'asset-parity-clickthrough-v12.csv')
keep_ids={'LOGO-001','LOGO-002','TABLE-014','TABLE-015','TABLE-001','TABLE-002','F01','F02','TABLE-003','F05','TABLE-004','F04','TABLE-005','F08','TABLE-006','F03','F06','F07','F09','R03','TABLE-007','TABLE-008','TABLE-009','TABLE-010','TABLE-011','TABLE-012','TABLE-013'}
assets=[r for r in assets if r['asset_id'] in keep_ids]
for r in assets:
    aid=r['asset_id']
    r['document_sha256']=doc_hash
    r['qa_report']='qa/verify-v6-render.json'
    r['status']='PASS'
    r['reviewed_by']='Codex document and asset review'
    r['review_date']='2026-10-25'
    r['evidence_files']=r['evidence_files'].replace('VietLex_DoAnChuyenNganh_RubricCriteria_FinalQA_20261025_v5.docx',DOC.relative_to(W).as_posix())
    r['evidence_files']=r['evidence_files'].replace('verify-vietlex-rubriccriteria-final-20261025.json','verify-v6-render.json')
    idx=shape_for.get(aid)
    r['asset_sha256']=shape_part_hashes[idx] if idx is not None else ''
    if aid in asset_png:
        r['evidence_files']=f"{asset_png[aid]};{asset_png[aid].replace('.png','.puml')};{DOC.relative_to(W).as_posix()};qa/verify-v6-render.json"
        r['source_location']=f"Source-derived diagram: {asset_png[aid].replace('.png','.puml')} and current source routes/modules"
    if aid in selected:
        c=capture_by_id[aid]
        r['capture_id']=c['screen_id']
        r['runtime_route']=c['route']
        r['screenshot_path']=c['screenshot_path']
        r['screenshot_sha256']=c['screenshot_sha256']
        r['asset_sha256']=shape_part_hashes[shape_for[aid]]
        r['evidence_files']=f"{c['screenshot_path']};{capture_path};{DOC.relative_to(W).as_posix()};qa/verify-v6-render.json"
        r['coverage_note']=f"Runtime page captured through visible UI clickthrough; final URL {c['resolved_url']}; HTTP/document 200; console clear; screenshot hash matches manifest. Included as one of three screenshots in the public search flow."
    elif aid.startswith('LOGO'):
        r['evidence_files']=f"{DOC.relative_to(W).as_posix()};profiles/hcmunre_dacn_2026_2027.json;qa/verify-v6-render.json"
    if aid=='R03':
        r['target_caption']='HÌNH 3.5. Đọc Bộ luật Lao động 2019 — GET /documents/333670'
    if aid=='F01':
        r['evidence_files']=f"{asset_png['F01']};{asset_png['F01'].replace('.png','.puml')};{DOC.relative_to(W).as_posix()};screen-inventory-v14.json;qa/verify-v6-render.json"
write_csv(W/'asset-parity-v14.csv',assets,[*afields,'asset_sha256'])

# Diagram plan and image/PUML hashes.
diagrams,dfields=read_csv(W/'diagram-plan.csv')
diagram_assets={ 'D01':'assets/uml/01-screen-map-v14.png','D02':'assets/uml/02-use-cases.png',
'D03':'assets/uml/03-chat-sequence.png','D04':'assets/uml/04-retrieval-architecture.png',
'D05':'assets/uml/05-retrieval-classes.png','D06':'assets/uml/06-ingestion-dataflow.png',
'D07':'assets/uml/07-official-source-read-sequence.png'}
for r in diagrams:
    did=r['diagram_id']; png=diagram_assets[did]; puml=png.replace('.png','.puml')
    r['puml_source']=puml; r['rendered_output']=png
    r['puml_sha256']=sha(W/puml); r['rendered_sha256']=sha(W/png)
    r['docx_location']='Chapter 2' if did in {'D01','D02','D04','D05','D06'} else 'Chapter 3'
    if did=='D01':
        r['question_or_scope']='Which routes produce full HTML pages, which GET endpoints return partials/downloads, and which routes are actions or APIs?'
        r['source_files']='app/main.py; app/api/routes.py; app/api/legal_routes.py; app/api/account_routes.py; app/api/workspace_routes.py; app/api/legal_registry_routes.py; app/api/product_quality_routes.py; app/api/evaluation_lab_routes.py; app/templates/admin_sidebar.html'
        r['evidence_symbols_or_methods']='get_index; legal_search; legal_document; account GET pages; workspace_list/workspace_detail; _admin_response; admin_stats_partial/admin_logs_partial/admin_details_partial; registry_admin; corpus_queue; feedback_queue; admin_users_partial; admin_audit_partial'
        r['status']='VERIFIED_SOURCE'
        r['verified_by']='Codex source and route/template review'
        r['notes']='Refreshed v14 route inventory against current route-module/template hashes. Separates 26 full HTML GET views from five HTML partial routes, CSV/session downloads, JSON endpoints, redirects and POST/DELETE actions. Role/token/owner protected runtime routes remain NOT_RUN.'
    r['notes']=(r.get('notes','')+'; source/output SHA-256 recorded in v14 plan').strip('; ')
write_csv(W/'diagram-plan-v14.csv',diagrams,[*dfields,'puml_sha256','rendered_sha256'])

# Refreshed claim/source maps for only the two source files whose content hashes changed.
claims,cfields=read_csv(W/'claim-evidence.csv')
for r in claims:
    rel=r['source_file'].replace('\\','/')
    if rel in source_hashes:
        r['source_sha256']=source_hashes[rel]
    if r['claim_id']=='PROJECT-RAG-PIPELINE':
        r['source_location']='app/services/rag_pipeline.py:515-620 (bounded whole-evidence context); 632-900 (retrieval expansion, filters, official-source fallback, no-evidence handling and diagnostics)'
        r['review_date']='2026-10-25'
    elif r['claim_id']=='PROJECT-ARCHITECTURE':
        r['source_location']='docs/CURRENT_ARCHITECTURE.md:1-36'
        r['review_date']='2026-10-25'
write_csv(W/'claim-evidence-v14.csv',claims,cfields)
registry=json.loads((W/'evidence.json').read_text(encoding='utf-8'))
for eid,entry in registry.items():
    rel=str(entry.get('source_file','')).replace('\\','/')
    if rel in source_hashes:
        entry['source_sha256']=source_hashes[rel]
        entry['source_revision']=revision
        entry['source_status']=f"{sm['git_worktree']} working tree; exact status hash in source/source_manifest.json"
        if eid in {'src-vietlex-rag-pipeline','src-vietlex-architecture'}:
            entry['reviewed_at']='2026-10-25T11:12:25+07:00'
            entry['reviewed_by']='Codex source review'
            entry['verified_by']='Codex source review'
            entry['review_status']='reviewed'
            if eid=='src-vietlex-rag-pipeline':
                entry['support_location']='app/services/rag_pipeline.py:515-620; 632-900'
            else:
                entry['support_location']='docs/CURRENT_ARCHITECTURE.md:1-36'
write_json(W/'evidence-v14.json',registry)

# Refresh the file-backed source snapshot, keeping task artifacts excluded from git status scope.
snapshot={
 'schema_version':2,'captured_at_local':sm['captured_at'],'repository':sm['project_root'],
 'git_head':sm['git_head'],'worktree_state':sm['git_worktree'],
 'git_status_sha256':sm['git_status_sha256'],'git_status_entry_count':sm['git_status_line_count'],
 'relevant_file_sha256':source_hashes,
 'limitations':['Git status hash is scoped by capture_source_snapshot.py to exclude artifacts/** and .tmp-*; it describes the rest of the source worktree.','The worktree is dirty. Source claims must remain tied to the listed readable file hashes; this is not deployment verification.']
}
write_json(W/'qa'/'source-snapshot-v14.json',snapshot)

# Existing QA artifacts remain immutable; publish only the v14 sidecars.
print(json.dumps({
 'document_sha256':doc_hash,'route_count':len(route_records),
 'full_html_pages':len(route_details),'partials':len(partial_details),
 'runtime_capture_instances':inventory['runtime_capture_instances'],
 'included_runtime_captures':sum(x['included_in_docx'] for x in inventory['runtime_captures']),
 'structure_rows':len(rows),'asset_rows':len(assets),'embedded_shapes':len(shape_part_hashes),
 'diagrams':len(diagrams),'claims':len(claims),'snapshot_files':len(source_hashes)
},ensure_ascii=False,indent=2))

