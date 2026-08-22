from __future__ import annotations
from pathlib import Path
import json

def init_workspace(path:str|Path)->Path:
    root=Path(path); wa=root/'.wordassistant'; wa.mkdir(parents=True,exist_ok=True)
    project=wa/'project.json'
    if not project.exists(): project.write_text(json.dumps({'schema_version':1,'profile':'generic','variant':'default'},indent=2),encoding='utf-8')
    ev=wa/'evidence.json'
    if not ev.exists(): ev.write_text('{}\n',encoding='utf-8')
    (wa/'cache').mkdir(exist_ok=True); (wa/'checkpoints').mkdir(exist_ok=True)
    return wa
