import sys
import docx
import re

sys.stdout.reconfigure(encoding='utf-8')
doc = docx.Document('artifacts/course-essay/strongwine-revision-20261027/output/StrongWine_20261102_standardized.docx')

topics = {
    "1_repo": [r'nguồn', r'mã nguồn', r'github', r'repository', r'strongwine'],
    "2_oop": [r'hướng đối tượng', r'tính kế thừa', r'đa hình', r'đóng gói', r'interface'],
    "3_ioc": [r'ioc', r'tiêm phụ thuộc', r'dependency injection', r'bean', r'applicationcontext'],
    "4_patterns": [r'mẫu thiết kế', r'design pattern', r'strategy', r'template method'],
    "5_uml": [r'sơ đồ lớp', r'sơ đồ tuần tự', r'uml', r'sequence', r'ca sử dụng'],
    "6_transaction": [r'transactional', r'giao dịch', r'toàn vẹn', r'acid', r'rollback'],
    "7_spec": [r'specification', r'criteria', r'lọc', r'tìm kiếm'],
    "8_auth": [r'phân quyền', r'ủy quyền', r'authorization', r'preauthorize', r'bảo vệ'],
    "9_rbac": [r'rbac', r'vai trò', r'role', r'quyền hạn', r'admin', r'shipper'],
    "10_concurrency": [r'đồng thời', r'khóa', r'lock', r'tranh chấp', r'tồn kho'],
    "11_api": [r'rest', r'api', r'endpoint', r'openapi', r'http', r'webhook'],
    "12_rwd": [r'giao diện', r'responsive', r'di động', r'màn hình', r'ui/ux', r'thiết bị']
}

print("=== SEARCHING CANDIDATE PARAGRAPHS ===")
for t_name, kw_list in topics.items():
    pattern = re.compile(r'(' + '|'.join(kw_list) + r')', re.IGNORECASE)
    matches = []
    for idx in range(423, 1267): # Between Mở đầu and Kết luận
        p = doc.paragraphs[idx]
        text = p.text.strip()
        if len(text) > 60 and not p.style.name.startswith('Heading'):
            if pattern.search(text):
                matches.append((idx, text[:110]))
    print(f"\nTopic {t_name}: {len(matches)} matching paragraphs")
    for idx, preview in matches[:4]:
        print(f"  p.{idx}: {preview}...")
