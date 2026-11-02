import sys
import json
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

projects = {
    'StrongWine': Path('artifacts/course-essay/strongwine-revision-20261027'),
    'LMS': Path('artifacts/course-essay/lms-qlpm-trello-drawio'),
    'VietLex': Path('D:/Download/ProfessionalLegalRAG/artifacts/course-essay-vietlex-20261020'),
}

for name, base in projects.items():
    print(f'=== {name} ({base}) ===')
    pj = base / 'project.json'
    if pj.is_file():
        try:
            pj_data = json.loads(pj.read_text(encoding='utf-8'))
            print(f'project.json found! Keys: {list(pj_data.keys())}')
            print(f'  output_docx: {pj_data.get("output_docx")}')
            print(f'  evidence_registry: {pj_data.get("evidence_registry")}')
            print(f'  source_assets: {pj_data.get("source_assets")}')
        except Exception as e:
            print(f'Error reading project.json: {e}')
    else:
        print('project.json NOT found!')
        
    ev = base / 'evidence.json'
    if not ev.is_file():
        # try finding any evidence.json in base
        ev_candidates = list(base.glob('evidence*.json'))
        if ev_candidates:
            ev = ev_candidates[0]
            print(f'Using candidate evidence file: {ev.name}')
            
    if ev.is_file():
        try:
            ev_data = json.loads(ev.read_text(encoding='utf-8'))
            records = ev_data if isinstance(ev_data, list) else list(ev_data.values())
            print(f'evidence.json found! Total records: {len(records)}')
            for r in records[:5]:
                print(f'  Record ID: {r.get("id")}, Title: {r.get("title")}, Status: {r.get("review_status")}')
        except Exception as e:
            print(f'Error reading evidence.json: {e}')
    else:
        print('evidence.json NOT found!')
        
    # Check sources / corpus
    sources_dir = base / 'sources'
    if sources_dir.is_dir():
        files = list(sources_dir.glob('*'))
        print(f'sources/ dir found! Files count: {len(files)}')
        for f in files[:5]:
            print(f'  Source: {f.name} ({f.stat().st_size} bytes)')
    else:
        print(f'sources/ dir NOT found at {sources_dir}')
    print()
