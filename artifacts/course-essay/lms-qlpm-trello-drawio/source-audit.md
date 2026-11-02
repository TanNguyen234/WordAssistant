# Source audit and authoring decisions

Date: 2026-10-25

## Authority
Yêu cầu trực tiếp là dùng workflow/style WordAssistant, lập báo cáo quản lý dự án phần mềm cho LMS, bổ sung Trello và Draw.io; người dùng loại trừ n8n. Guide đính kèm là hướng dẫn thao tác và capture evidence, không thay direct request. WordAssistant repo kiểm soát cách author/format/QA; repo LMS cung cấp project facts; ZIP cung cấp snapshot và diagram assets.

## Reconciliation
- Baseline hiện hành trong docs/08_PROJECT_MANAGEMENT.md và docs/audit/06_PM_DOCUMENT_RECONCILIATION.md: 20 tuần, 1.200.000.000 VNĐ, 8,5 FTE.
- Snapshot Trello ngày 2026-10-23 có 9 lists/39 cards, 8 milestone cards đề xuất, 3 simulated cards; To Do có 25 cards; Doing, Review, Done rỗng; Blocked có yêu cầu hỏi rubric. Hình kèm ZIP là dựng từ dữ liệu API, không phải screenshot UI.
- Kịch bản 8 mốc Oct-Nov và ngân sách 27M trong ZIP là phương án nhóm đề xuất riêng, chưa được đối chiếu/phê duyệt để thay baseline LMS.
- Có 15 source diagrams .drawio và 15 PNG; manifest paths cũ (diagrams/, images/) không trỏ tới vị trí thật (drawio/, anh_so_do/). Workspace dùng path thực, không sửa ZIP.
- UAT sample, EVM, sign-off, outcomes đều là mô phỏng/kế hoạch; không coi là evidence thực tế.
- Guide yêu cầu Trello T01-T05, Draw.io export, LMS L01-L07. Computer-use UI state timeout hai lần; ZIP không có screenshot runtime LMS mới. Report ghi checklist NOT_RUN, không thay bằng ảnh khác.
- DOCX cũ chỉ tham khảo nội dung, không tái sử dụng layout/hình thức; DOCX mới dùng heading Word thật, captions, tables, lists of figures/tables, citation registry.

## Sources
Project files và archive giữ read-only. Nguồn ngoài trong bibliography là trang hỗ trợ chính thức của Atlassian, draw.io và PMI; bản tải và SHA-256 nằm trong workspace sources. Cover identity và rubric còn thiếu; submission readiness INCOMPLETE.

## Verification trail
- WordAssistant doctor/capabilities: core ready; Word 2013 native backend operational; LibreOffice/docx-mcp unavailable.
- WordAssistant inspect: archived report/guide inventory checked.
- Computer Use: app inventory visible; two window-state reads timed out; no runtime screenshot was captured or claimed.

## Updated workflow continuation 2026-10-25
Three compact models were entered and exported in the Draw.io browser editor using local Download export and light PNG appearance. Editable mxfile XML was recovered from each included PNG metadata and parsed. Added model assets are source-based static figures, not captured application states. Checked roles, SQL schema and assignment endpoints; preserved the LMS checkout read-only. Corrected reduced RACI rows against the full source to remove double-A aggregation. The original LMS_07 POST label is stale against the PUT endpoint and remains unused. Trello board UI was observed in the in-app browser, but no qualifying saved capture/arrival manifest exists; T/D/L capture requirements remain NOT_RUN. The current Python bundle supports authoring but lacks pythoncom; the existing WordAssistant .venv is the verified native Word integration host.

## User correction and actual capture session 2026-10-26
The user rejected the prior handoff for missing web/Trello images, inadequate style, prose and citations. Prior layout-only acceptance is superseded for these content/presentation requirements. Actual images now exist in captures/2026-10-26: Trello board/workflow, PM-04 WBS checklist 0/7, milestone/empty-Done view and SIM-01 explicitly marked not a real acceptance; LMS login, Admin users, Lecturer assignment/submission views and Student assignment/grades. Ten selected captures are embedded with analysis in Appendix E. No Trello card was moved or checked off; no grade, submission or account was edited. An empty add-card composer caused by a mis-targeted UI click was dismissed without submission.

The existing disposable database UniversityLms_Test_Repeat_20261021_1027 was selected using a read-only database boundary check. It contains Admin/Lecturer/Student demo roles. The existing backend and frontend dependencies were used without installation. API health returned HTTP 200 with database_connected=true. Browser capture console had no LMS errors or warnings; Trello produced one generic asset warning without a visible page error. The browser API did not expose original document HTTP response statuses, so these remain UNKNOWN in the capture manifest. No HTTP status is invented from a loaded UI. Calendar/Timeline, Draw.io editor captures and L06/L07 remain outstanding; Done is observed empty.

Forty-seven main paragraphs were rewritten as connected Vietnamese analysis; headings explain their content; a glossary was added. Project claims now carry visible source-linked citation controls. Six project primary records were copied from checked local sources into the source store and added to the five existing external records. GitHub URLs identify the source repository/commit; remote byte parity was not claimed. Atlassian/Draw.io pages and the PMI scheduling standard were reopened; the CPM discussion was checked against PMI sections 3.4.1–3.4.2. Undated web sources are shown without an invented publication year, with access date 26/10/2026. Author names are bold and titles italic; the bibliography is last, after appendices.

Style fixes reconcile direct overrides with real styles: left headings, centered figure captions, Times New Roman 13 body, 16/14/13 headings, 1.5 prose and source-note spacing, A4/mixed orientation and 3/2/2/2 cm margins. Native tables retain 13pt and 1.15 spacing as a deliberate compact-table choice. Cover alignment was restored from the preserved same-project input. Image, caption and source-note groups were kept together after visual review found orphan source pages. Two Trello dialog images are cropped only through Word picture layout; original embedded and saved full-context screenshot bytes are retained.

## Full HCMUNRE scope confirmed 2026-10-26
The user explicitly superseded style-only use: selected full HCMUNRE presentation and supplied exact course/topic. Both covers now contain the bundled university logo; the outer frame is copied from the official guide. All twelve front-matter components are present. Complete official assessment prompts pass exact paragraph parity; no scored course rubric, names, signatures or approvals are invented. Updated native Word deliverable: output/LMS_HCMUNRE_day_du.docx, SHA-256 8d8061ac370722f40b784746f1db336de3bd176a19875608a27ac684b9f52459. All 64 rendered pages reviewed; native delivery PASS. The earlier final.docx and prior scope/QA are historical. Ten actual UI screenshots are embedded; Calendar/Timeline, Draw.io editor, API 403 and terminal evidence remain missing, and original browser document HTTP response status is UNKNOWN. LMS Git working tree remains clean.
