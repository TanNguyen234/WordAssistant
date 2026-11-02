from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parent


def add_node(root, node_id, value, style, x, y, width, height):
    cell = ET.SubElement(root, "mxCell", {
        "id": node_id, "value": value, "style": style,
        "vertex": "1", "parent": "1",
    })
    ET.SubElement(cell, "mxGeometry", {
        "x": str(x), "y": str(y), "width": str(width),
        "height": str(height), "as": "geometry",
    })


def add_edge(root, edge_id, source, target, value="", style=None, points=None):
    attrs = {"id": edge_id, "value": value,
             "style": style or "endArrow=none;startArrow=none;html=1;strokeColor=#64748b;strokeWidth=2;",
             "edge": "1", "parent": "1"}
    if source and target:
        attrs.update(source=source, target=target)
    cell = ET.SubElement(root, "mxCell", attrs)
    geom = ET.SubElement(cell, "mxGeometry", {"relative": "1", "as": "geometry"})
    if points:
        ET.SubElement(geom, "mxPoint", {"x": str(points[0][0]), "y": str(points[0][1]), "as": "sourcePoint"})
        ET.SubElement(geom, "mxPoint", {"x": str(points[1][0]), "y": str(points[1][1]), "as": "targetPoint"})


def save_drawio(filename, name, page_width, page_height, nodes, edges):
    mxfile = ET.Element("mxfile", {"host": "app.diagrams.net", "type": "device", "version": "24.7.17"})
    diagram = ET.SubElement(mxfile, "diagram", {"id": filename.replace(".drawio", ""), "name": name})
    model = ET.SubElement(diagram, "mxGraphModel", {
        "dx": str(page_width), "dy": str(page_height), "grid": "1", "gridSize": "10",
        "guides": "1", "tooltips": "1", "connect": "1", "arrows": "1",
        "fold": "1", "page": "1", "pageScale": "1", "pageWidth": str(page_width),
        "pageHeight": str(page_height), "math": "0", "shadow": "0",
    })
    root = ET.SubElement(model, "root")
    ET.SubElement(root, "mxCell", {"id": "0"})
    ET.SubElement(root, "mxCell", {"id": "1", "parent": "0"})
    for node in nodes:
        add_node(root, *node)
    for edge in edges:
        add_edge(root, *edge)
    ET.indent(mxfile, space="  ")
    (ROOT / filename).write_bytes(b'<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(mxfile, encoding="utf-8"))


TITLE = "text;html=1;align=center;verticalAlign=middle;fontSize=28;fontStyle=1;fontColor=#111827;"
LANE = "rounded=0;whiteSpace=wrap;html=1;fillColor=none;strokeColor=#cbd5e1;strokeWidth=2;dashed=1;"
ACTOR = "shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;outlineConnect=0;strokeColor=#1d4ed8;fillColor=#eff6ff;fontSize=17;fontStyle=1;"
USECASE = "ellipse;whiteSpace=wrap;html=1;fillColor=#eef2ff;strokeColor=#1d4ed8;strokeWidth=2;fontSize=16;fontColor=#111827;"


def build_use_case():
    nodes = [("title", "Use Case LMS theo vai trò", TITLE, 240, 22, 870, 48)]
    edges = []
    groups = [
        ("admin", "ADMIN", ["Quản lý tài khoản", "Tạo và quản lý khóa học", "Ghi danh sinh viên"]),
        ("lecturer", "GIẢNG VIÊN", ["Xuất bản bài giảng", "Tạo bài tập và quiz", "Chấm bài và phản hồi"]),
        ("student", "SINH VIÊN", ["Xem bài giảng", "Nộp bài văn bản và làm quiz", "Xem điểm và phản hồi"]),
    ]
    for index, (prefix, actor_name, cases) in enumerate(groups):
        x = 25 + index * 445
        nodes.append((prefix + "-lane", "", LANE, x, 98, 415, 565))
        actor_id = prefix + "-actor"
        nodes.append((actor_id, actor_name, ACTOR, x + 22, 335, 82, 110))
        for i, case in enumerate(cases):
            case_id = f"{prefix}-uc-{i+1}"
            y = 177 + i * 145
            nodes.append((case_id, case, USECASE, x + 128, y, 260, 82))
            edges.append((f"assoc-{prefix}-{i+1}", actor_id, case_id, "",
                          "endArrow=none;startArrow=none;html=1;strokeColor=#64748b;strokeWidth=2;"))
    save_drawio("LMS_Use_Case_Compact.drawio", "Use Case", 1385, 710, nodes, edges)


def build_sequence():
    nodes = [("title", "Trình tự chấm bài của giảng viên", TITLE, 250, 20, 880, 48)]
    participants = [
        ("lecturer", "Giảng viên", 90),
        ("react", "React / Vite", 410),
        ("api", "FastAPI", 730),
        ("sql", "SQL Server", 1050),
    ]
    centers = {}
    for pid, label, x in participants:
        nodes.append((pid, label, "rounded=1;whiteSpace=wrap;html=1;fillColor=#eff6ff;strokeColor=#1d4ed8;strokeWidth=2;fontSize=18;fontStyle=1;", x, 105, 210, 58))
        centers[pid] = x + 105
    messages = [
        ("lecturer", "react", "Mở danh sách bài cần chấm"),
        ("react", "api", "GET /assignments/{assignment_id}/submissions"),
        ("api", "sql", "Kiểm tra quyền sở hữu khóa học; đọc bài nộp"),
        ("sql", "api", "Trả danh sách bài nộp"),
        ("api", "react", "Trả dữ liệu để hiển thị"),
        ("lecturer", "react", "Nhập điểm và phản hồi"),
        ("react", "api", "PUT /submissions/{submission_id}/grade"),
        ("api", "sql", "Kiểm tra quyền, giới hạn điểm; cập nhật Submission và Grades; tạo Notification"),
        ("sql", "api", "Commit dữ liệu"),
        ("api", "react", "Trả kết quả chấm"),
        ("react", "lecturer", "Hiển thị điểm và phản hồi"),
    ]
    edges = []
    for i, (source, target, label) in enumerate(messages):
        y = 220 + i * 56
        edges.append((f"msg-{i+1}", "", "", label,
                      "edgeStyle=none;endArrow=block;html=1;strokeColor=#475569;strokeWidth=2;fontSize=14;fontColor=#111827;labelBackgroundColor=#ffffff;",
                      [(centers[source], y), (centers[target], y)]))
    for i, (pid, _label, _x) in enumerate(participants):
        x = centers[pid]
        edges.append((f"life-{i+1}", "", "", "",
                      "edgeStyle=none;endArrow=none;html=1;strokeColor=#94a3b8;strokeWidth=1.5;dashed=1;",
                      [(x, 163), (x, 850)]))
    save_drawio("LMS_Sequence_Grade_Compact.drawio", "Sequence Grade", 1350, 900, nodes, edges)


def build_class():
    nodes = [("title", "Mô hình lớp khái niệm LMS", TITLE, 300, 18, 760, 48),
             ("note", "Trích lớp nghiệp vụ cốt lõi; không thể hiện phương thức triển khai", "text;html=1;align=center;verticalAlign=middle;fontSize=15;fontColor=#475569;", 220, 65, 920, 30)]
    class_style = "rounded=0;whiteSpace=wrap;html=1;fillColor=#f8fafc;strokeColor=#334155;strokeWidth=2;fontSize=16;fontColor=#111827;align=left;verticalAlign=top;spacing=8;"
    entities = [
        ("user", "<b>User</b><br/>UserId (PK)<br/>Role, StudentCode", 40, 130),
        ("course", "<b>Course</b><br/>CourseId (PK)<br/>LecturerId (FK), Status", 480, 130),
        ("assignment", "<b>Assignment</b><br/>AssignmentId (PK)<br/>CourseId (FK), MaxScore", 920, 130),
        ("enrollment", "<b>Enrollment</b><br/>CourseId + StudentId (unique)<br/>Status", 40, 315),
        ("module", "<b>Module</b><br/>ModuleId (PK)<br/>CourseId (FK), Title", 480, 315),
        ("submission", "<b>Submission</b><br/>SubmissionId (PK)<br/>AssignmentId, StudentId, Status", 920, 315),
        ("quiz", "<b>Quiz</b><br/>QuizId (PK)<br/>CourseId (FK), Status", 40, 500),
        ("lesson", "<b>Lesson</b><br/>LessonId (PK)<br/>ModuleId (FK), Title", 480, 500),
        ("grade", "<b>Grade</b><br/>GradeId (PK)<br/>CourseId, StudentId, SourceType / SourceId", 920, 500),
        ("attempt", "<b>QuizAttempt</b><br/>AttemptId (PK)<br/>QuizId, StudentId, Status", 260, 685),
        ("notification", "<b>Notification</b><br/>NotificationId (PK)<br/>UserId (FK), Type", 700, 685),
    ]
    for entity in entities:
        nodes.append((entity[0], entity[1], class_style, entity[2], entity[3], 370, 130))
    edge_style = "endArrow=none;startArrow=none;html=1;strokeColor=#64748b;strokeWidth=2;fontSize=13;fontColor=#334155;labelBackgroundColor=#ffffff;"
    edges = [
        ("r1", "user", "course", "lecturer", edge_style),
        ("r2", "course", "assignment", "1 : N", edge_style),
        ("r3", "course", "enrollment", "1 : N", edge_style),
        ("r4", "user", "enrollment", "student", edge_style),
        ("r5", "course", "module", "1 : N", edge_style),
        ("r6", "module", "lesson", "1 : N", edge_style),
        ("r7", "assignment", "submission", "1 : N", edge_style),
        ("r8", "course", "quiz", "1 : N", edge_style),
        ("r9", "quiz", "attempt", "1 : N", edge_style),
        ("r10", "submission", "grade", "assignment grade", edge_style),
        ("r11", "user", "notification", "recipient", edge_style),
    ]
    save_drawio("LMS_Class_Domain_Compact.drawio", "Class Domain", 1350, 850, nodes, edges)


if __name__ == "__main__":
    ROOT.mkdir(parents=True, exist_ok=True)
    build_use_case()
    build_sequence()
    build_class()
    print("Created 3 editable Draw.io sources in", ROOT)
