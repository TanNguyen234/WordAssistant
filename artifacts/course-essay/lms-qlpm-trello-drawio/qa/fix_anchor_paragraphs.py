from pathlib import Path
import json

W=Path(r"D:\Download\WordAssistant\artifacts\course-essay\lms-qlpm-trello-drawio")
cp=W/"content.json"
op=W/"operations-plan.json"
d=json.loads(cp.read_text(encoding="utf-8"))
plan=json.loads(op.read_text(encoding="utf-8"))
dest={
"Mỗi gói việc cần một A duy nhất. Sponsor là vai trò giả định trong mô hình.":"2.2. RACI và escalation",
"Trong phạm vi là LMS core; các khả năng mở rộng được đưa ngoài phạm vi.":"3.1. Ranh giới và acceptance",
"WBS là cấu trúc công việc, không chứng minh gói việc đã hoàn tất.":"3.2. Work breakdown",
"Mạng LMS_14 không gán ngày; bảng này là nguồn duration/float baseline.":"4.1. Danh sách hoạt động và phụ thuộc",
"Mốc tuần là baseline kế hoạch, không phải actual date.":"4.2. Theo dõi sai lệch",
"Tổng phân bổ 8,5 FTE; không suy ra số đầu người.":"5.1. Resource breakdown",
"Sáu khoản mục cộng đúng 1,2 tỷ VNĐ; contingency không phải chi phí đã tiêu.":"5.2. Kiểm soát chi phí",
"Risk register là kế hoạch mô phỏng; score không chứng minh sự kiện.":"6.1. Giám sát và ứng phó",
"Gate là điều kiện kế hoạch; trạng thái phê duyệt chưa được xác nhận.":"7.1. Gate và DoD",
"Mười AC được định nghĩa; số đã xác minh chạy là 0.":"7.2. UAT và triage",
"Dữ liệu API không phải ảnh UI và không chứng minh Done.":"8.1. Luồng board và quy ước",
"Cards/lists/checklists hỗ trợ công việc; approval/evidence vẫn riêng.":"8.1. Luồng board và quy ước",
"Kiến trúc là thiết kế trong repo, không phải runtime.":"9.1. Kiến trúc và dữ liệu",
"Không có invoice/timesheet hoặc kỳ đo thực tế gắn EVM.":"10.1. Tiêu chí nghiệm thu",
"Năm PNG được chèn; các source khác giữ trong archive.":"Phụ lục A. Danh mục sơ đồ Draw.io",
"Checklist hướng dẫn không thay ảnh; mọi capture hiện chưa thực hiện.":"Phụ lục B. Checklist ảnh Trello, Draw.io và LMS",
"Kế hoạch, snapshot, mô phỏng, runtime là loại chứng cứ khác nhau.":"Phụ lục C. Loại bằng chứng và giới hạn",
"WBS được lấy từ ZIP, là cấu trúc bàn giao đề xuất chứ không phải rubric.":"3.2. Work breakdown",
"Sơ đồ Draw.io quy trình nối yêu cầu, Trello, review và thay đổi.":"8.1. Luồng board và quy ước",
"LMS_14 không gán ngày; bảng CPM mới là nguồn duration/float.":"4.1. Danh sách hoạt động và phụ thuộc",
"Sơ đồ architecture trong repo mô tả thiết kế, không phải runtime.":"9.1. Kiến trúc và dữ liệu",
"ERD có quan hệ giản lược; đọc cùng schema SQL nguồn.":"9.1. Kiến trúc và dữ liệu",
"Snapshot không chứng minh phần việc đã hoàn thành.":"8.1. Luồng board và quy ước"
}
seen=set()
for s in d["sections"]:
    for p in s.get("paragraphs",[]):
        if isinstance(p,str): seen.add(p)
    for q in s.get("subsections",[]):
        for p in q.get("paragraphs",[]):
            if isinstance(p,str): seen.add(p)
for step in plan["steps"]:
    if step.get("operation") not in {"table.create","caption.insert","image.insert"}: continue
    anchor=step["selector"]["text"]
    if anchor in seen: continue
    target=dest.get(anchor)
    if target is None: raise ValueError("No destination for anchor: "+anchor)
    found=False
    for s in d["sections"]:
        for q in s.get("subsections",[]):
            if q["title"]==target:
                q.setdefault("paragraphs",[]).append(anchor)
                found=True; break
        if found: break
    if not found: raise ValueError("Missing subsection "+target)
    seen.add(anchor)
cp.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("Added exact semantic anchors:",len(dest))

