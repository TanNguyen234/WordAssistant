import json
from pathlib import Path
p=Path(r'D:\Download\ProfessionalLegalRAG\artifacts\course-essay-vietlex-20261020\profiles\vietlex-course-essay-style-v9.json')
d=json.loads(p.read_text(encoding='utf-8'))
t=d['variants']['capstone']['typography']
t.pop('line_spacing',None)
t['styles']['Normal']['line_spacing']=1.15
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('profile now audits visible typography; default body spacing remains 1.15')
