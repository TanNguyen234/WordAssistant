import zipfile
import re
from collections import Counter

f = r'artifacts/course-essay/strongwine-revision-20261027/output/StrongWine_20261102_standardized.docx'
with zipfile.ZipFile(f) as z:
    xml = z.read('word/document.xml').decode('utf-8')

ids = re.findall(r'<[^:]+:docPr[^>]*\bid="(\d+)"', xml)
counts = Counter(ids)
dups = {k: v for k, v in counts.items() if v > 1}
print('Total docPr ids:', len(ids))
print('Unique docPr ids:', len(counts))
print('Duplicates:', dups)
