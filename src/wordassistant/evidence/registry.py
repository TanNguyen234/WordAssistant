from __future__ import annotations
from pathlib import Path
import json,os,tempfile
class EvidenceError(ValueError):pass
class EvidenceRegistry:
    def __init__(self,path): self.path=Path(path)
    def _load(self):
        if not self.path.exists():return {}
        data=json.loads(self.path.read_text(encoding='utf-8'))
        if not isinstance(data,dict):raise EvidenceError('Registry must be a JSON object')
        return data
    def add(self,record):
        for k in ('id','title','authors','year','url','verified_by'):
            if k not in record: raise EvidenceError(f'Missing evidence field: {k}')
        if not isinstance(record['authors'],list) or not record['authors']:raise EvidenceError('authors must be a non-empty array')
        if not str(record['url']).startswith(('http://','https://')):raise EvidenceError('url must be absolute http(s) URL')
        data=self._load(); data[str(record['id'])]=record; self.path.parent.mkdir(parents=True,exist_ok=True)
        fd,tmp=tempfile.mkstemp(prefix=self.path.name,suffix='.tmp',dir=self.path.parent); os.close(fd)
        Path(tmp).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8'); os.replace(tmp,self.path)
    def get(self,key):return self._load()[key]
    def list(self):return list(self._load().values())
