from pathlib import Path
import json
from wordassistant.document.verify import verify_document
from wordassistant.document.render import RenderResult
from wordassistant.profiles.loader import resolve_profile

workspace = Path(r'D:\Download\ProfessionalLegalRAG\artifacts\course-essay-vietlex-20261020')
docx = workspace / 'output' / 'VietLex_DoAnChuyenNganh_RubricCriteria_FinalQA_20261025_v6.docx'
pdf = workspace / 'qa' / 'render-v6-word-final' / 'VietLex_DoAnChuyenNganh_RubricCriteria_FinalQA_20261025_v6.pdf'
profile = resolve_profile('hcmunre_dacn_2026_2027', start_path=Path(r'D:\Download\WordAssistant'))
if not pdf.is_file() or pdf.stat().st_size == 0:
    raise SystemExit('Word-rendered PDF is missing or empty')

def use_word_render(_source, output_dir=None):
    return RenderResult(pdf_path=pdf.resolve(), file_size_bytes=pdf.stat().st_size,
                        engine='word', page_count=80, duration_seconds=0.0)

report = verify_document(docx, profile=profile, variant_name='report', render=True,
                         render_output_dir=workspace / 'qa' / 'render-v6-pages',
                         renderer=use_word_render, native_fields=True)
report_path = workspace / 'qa' / 'verify-v6-render.json'
report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({
    'overall_status': report.get('overall_status'),
    'structural_status': report.get('structural_status'),
    'format_status': report.get('format_status'),
    'field_structure_status': report.get('field_structure_status'),
    'field_freshness_status': report.get('field_freshness_status'),
    'field_evaluation_status': report.get('field_evaluation_status'),
    'native_word_status': report.get('native_word_status'),
    'render_status': report.get('render_status'),
    'visual_status': report.get('visual_status'),
    'page_count': (report.get('render') or {}).get('verified_pdf_page_count'),
    'challenge': report.get('visual_review_challenge'),
    'issues': report.get('issues'),
    'report_path': str(report_path),
}, ensure_ascii=False, indent=2))

