from pathlib import Path
from PIL import Image, ImageDraw
import json, hashlib
reports = [Path('artifacts/course-essay/lms-qlpm-trello-drawio/qa/verify-LMS_20261028_chantrang_bang.json'), Path('D:/Download/ProfessionalLegalRAG/artifacts/course-essay-vietlex-20261020/qa/verify-VietLex_20261028_truong.json')]
for report in reports:
    data = json.loads(report.read_text(encoding='utf8'))
    pages = data['render_reuse_manifest']['pages']
    folder = report.parent / (report.stem + '-contact')
    folder.mkdir(exist_ok=True)
    for start in range(0, len(pages), 16):
        canvas = Image.new('RGB', (1080, 1560), 'white')
        draw = ImageDraw.Draw(canvas)
        for i, item in enumerate(pages[start:start+16]):
            path = Path(item['path'])
            if hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
                raise ValueError(f'Page hash mismatch: {path}')
            img = Image.open(path).convert('RGB')
            img.thumbnail((260, 360))
            x, y = (i % 4) * 270, (i // 4) * 390
            canvas.paste(img, (x, y))
            draw.text((x, y + 362), str(item['page']), fill='black')
        canvas.save(folder / f'sheet-{start+1:03}.jpg', quality=90)
    print(folder, len(pages))
