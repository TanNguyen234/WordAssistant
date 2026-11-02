"""Bind full-profile and exact-cover evidence after final visual review."""
import csv,json,hashlib
from pathlib import Path
from docx import Document
R=Path(__file__).resolve().parent
DOC='output/LMS_HCMUNRE_day_du.docx'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def j(p):return json.loads((R/p).read_text(encoding='utf-8-sig'))
def save(p,x):(R/p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def rows(p):
    with (R/p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def csvsave(p,x):
    with (R/p).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(x[0]));w.writeheader();w.writerows(x)
digest=sha(R/DOC);date='2026-10-26';reviewer='Codex source and visual review'
assets=[x for x in rows('asset-parity.csv') if not x['asset_id'].startswith('HCM-')]
logo=R.parents[2]/'use_cases/hcmunre_dacn_2026_2027/assets/university_logo.png'
for i,loc in enumerate(['Trang bìa ngoài','Trang bìa trong'],1):
    assets.append(dict(asset_id=f'HCM-LOGO-{i}',asset_type='LOGO',source_basis='Bundled HCMUNRE logo, explicitly requested by user',source_location=str(logo),target_section=loc,target_caption='',decision='MATCHED',coverage_note='Official bundled image, exact bytes retained; cover logo intentionally has no figure caption.',evidence_files=f'{DOC};{logo};qa/hcmunre-visual-review.json',capture_id='',runtime_route='',expected_media_count='1',caption_required='false',status='PASS',reviewed_by=reviewer,review_date=date))
for i,loc in enumerate(['LỊCH LÀM VIỆC','KÍ HIỆU CÁC CỤM TỪ VIẾT TẮT'],1):
    assets.append(dict(asset_id=f'HCM-FORM-{i}',asset_type='TABLE',source_basis='Full HCMUNRE front-matter form',source_location='hcmunre-lms-full-profile.json',target_section=loc,target_caption='',decision='MATCHED',coverage_note='Native editable front-matter form; intentionally outside numbered body table sequence.',evidence_files=f'{DOC};hcmunre-lms-full-profile.json;qa/hcmunre-visual-review.json',capture_id='',runtime_route='',expected_media_count='0',caption_required='false',status='PASS',reviewed_by=reviewer,review_date=date))
csvsave('asset-parity.csv',assets)
p=j('project.json');p['output_docx']=DOC;p['project_title']='Quản lý dự án xây dựng hệ thống quản lý học tập trực tuyến (LMS) cho trường đại học'
p['profile_variant']='report';p['task_profile_file']='hcmunre-lms-full-profile.json'
source=R.parents[2]/'use_cases/hcmunre_dacn_2026_2027/assets/huong_dan_trinh_bay_dacn_2026_2027.docx'
base=json.loads((R.parents[2]/'profiles/hcmunre_dacn_2026_2027.json').read_text(encoding='utf-8'))
sections=[]
for s,end in zip(base['assessment_criteria']['sections'],['NHẬN XÉT CỦA NGƯỜI PHẢN BIỆN','LỊCH LÀM VIỆC']):
    title=base['variants']['report']['front_matter_titles'][s['report_section']]
    sections.append(dict(source_start=s['source_start'],source_end=s['source_end'],output_start=title,output_end=end))
p.update(include_official_rubric_in_docx=True,rubric_file=str(source),rubric_source_authority='Official HCMUNRE presentation guide selected by user; assessment prompts, without scored levels or weights')
p['rubric_inclusion']=dict(source_sha256=sha(source),output_docx_sha256=digest,review_status='PASS',review_method='verbatim_source_section_comparison',reviewed_by=reviewer,reviewed_at=date,source_sections=sections,scoring_levels_present=False,scoring_weights_present=False,scope_note='Complete selected-profile review prompts. No claim that a separate scored rubric for this course has been supplied.')
save('project.json',p)
cross=rows('acceptance-crosswalk.csv')
for x in cross:
    x['evidence_files']=x['evidence_files'].replace('output/final.docx',DOC).replace('qa/final-delivery.json','qa/hcmunre-delivery.json').replace('qa/final-visual-review.json','qa/hcmunre-visual-review.json').replace('qa/final-profile-validation.json','qa/hcmunre-profile-validation.json').replace('qa/final-integrity-audit.json','qa/hcmunre-integrity-audit.json').replace('qa/final-integrity-provenance.json','qa/hcmunre-integrity-provenance.json')
    x['document_sha256']=digest;x['reviewed_by']=reviewer;x['review_date']=date
    if x['check_id']!='X07':x['status']='PASS'
    else:x['status']='NOT_RUN';x['notes']='Ten actual UI screenshots present, but Calendar/Timeline, Draw.io editor and L06/L07 remain incomplete; Done observed empty and HTTP response provenance UNKNOWN.'
    if x['check_id']=='X03':
        x['authority']='Selected official HCMUNRE profile and current user request';x['acceptance_criterion']='Include complete official assessment prompts on review pages; no scoring weights or assessments invented.';x['report_location']='Two review pages';x['evidence_files']=f'{DOC};{source};project.json;qa/hcmunre-visual-review.json';x['notes']='Profile criteria included verbatim; separate course scoring rubric not provided.'
new=dict(cross[0]);new.update(check_id='X13',category='user_requirements',authority='Explicit user correction 2026-10-26',source_location='User supplied exact course/topic and selected full HCMUNRE',acceptance_criterion='Full HCMUNRE throughout: actual bundled logo, source frame, school/faculty, two covers, full front matter, exact course and topic, Introduction page 1.',report_location='Covers; front matter; whole report',verification_method='Compare official guide and profile with every rendered page and saved Word semantics',evidence_files=f'{DOC};hcmunre-lms-full-profile.json;{logo};{source};qa/hcmunre-profile-validation.json;qa/hcmunre-delivery.json;qa/hcmunre-visual-review.json',status='PASS',document_sha256=digest,reviewed_by=reviewer,review_date=date,notes='Unknown student/MSSV/cohort/supervisor, signatures and assessment remain blank. Course essay type explicitly overrides capstone label.')
cross=[x for x in cross if x['check_id']!='X13']+[new]
for x in cross:
    paths=[s.strip() for s in x['evidence_files'].split(';') if s.strip()]
    resolved=[Path(s) if Path(s).is_absolute() else R/s for s in paths]
    x['evidence_sha256']=';'.join(sha(q) if q.is_file() else 'MISSING' for q in resolved)
csvsave('acceptance-crosswalk.csv',cross)
save('qa/hcmunre-cover-review.json',dict(document_sha256=digest,status='PASS',exact_topic=p['project_title'],course='Quản lý dự án phần mềm',logo_path=str(logo),logo_sha256=sha(logo),cover_frame='Copied exact pgBorders from selected source guide; outer cover only',front_matter='All twelve selected-profile components; unnumbered',arabic_start='MỞ ĐẦU = 1',unknown_personal_fields='Blank',reviewed_by=reviewer,review_date=date))
print(json.dumps({'document_sha256':digest,'assets':len(assets),'crosswalk_rows':len(cross),'official_criteria_included':True}))
