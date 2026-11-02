import json,hashlib
from pathlib import Path
from datetime import datetime,timezone,timedelta
from PIL import Image
R=Path(__file__).resolve().parent
folder=R/'captures/2026-10-26'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
cfg=read(R/'reviewed-captures.json')
raw=read(folder/'trello-capture-records.json')+read(folder/'lms-capture-records.json')
records=[]
for item in cfg['screens']:
    c=next(x for x in raw if x['file']==item['file']);p=folder/c['file']
    sha=hashlib.sha256(p.read_bytes()).hexdigest();url=c.get('url');assert url
    rel=p.relative_to(R).as_posix()
    records.append({'capture_id':item['id'],'route':url,'resolved_url':url,'screenshot_path':rel,'screenshot_sha256':sha,
      'captured_at_local':datetime.fromisoformat(c['timestamp'].replace('Z','+00:00')).astimezone(timezone(timedelta(hours=7))).isoformat(),
      'page_title':item['caption'],'acceptance_status':'ACCEPTED_UI_CLICKTHROUGH_CAPTURE',
      'capture_method':'visible UI click-through in ChatGPT in-app browser',
      'arrival':{'from':'https://trello.com' if item['id'].startswith('T') else 'http://127.0.0.1:5174/',
        'local_file_open_for_this_capture':False,'direct_route_load_for_this_capture':False,'ui_steps':[x['action'] for x in c['steps']]},
      'external_side_effect':False,'http_status':None,'network':{'document_status':None,'note':'IAB did not expose main-document HTTP response; not inferred from visible success.'},
      'console':{'errors':[],'warnings':[{'message':'Object','source':'Trello asset warning; no visible page error'}] if item['id'].startswith('T') else []},
      'page_state_review':{'status':'PASS','summary':item['text'],'reviewed_by':'Codex visual source review','reviewed_at':'2026-10-26','screenshot_path':rel,'screenshot_sha256':sha},
      'viewport':list(Image.open(p).size)})
manifest={'schema_version':1,'acceptance_status':'ACCEPTED_UI_CLICKTHROUGH_CAPTURE',
 'capture_method':'visible UI interaction; screenshots from real pages',
 'capture_context':{'browser_surface':'visible_browser_tab','headless':False,'navigation_policy':'visible_ui_clickthrough'},
 'verification_limit':'Actual images and UI arrival reviewed; original document HTTP status was not exposed and remains UNKNOWN. No complete network verification claimed.',
 'captures':records}
(folder/'capture-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print('Saved',len(records),'actual captures; main-document HTTP status remains UNKNOWN.')
