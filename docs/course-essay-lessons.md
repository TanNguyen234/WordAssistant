# Bài học đã xác nhận — quy trình tiểu luận phần mềm

Các mục dưới đây là lỗi đã quan sát trong các lần chạy cụ thể, không phải nhận định chung về mọi tài liệu. Chỉ thêm bài học mới sau khi đã xác nhận biểu hiện, nguyên nhân và cách phòng ngừa.

| Lỗi đã thấy | Nguyên nhân đã xác nhận | Cách ngăn tái diễn |
|---|---|---|
| Workspace VietLex có một báo cáo 9 trang cạnh bài tiểu luận 41 trang, không có README chỉ rõ bản chuẩn. | Hai lượt tạo Word dùng hai workspace/tên output khác nhau; thiếu manifest handoff chỉ ra một canonical `output_docx`. | Ghi một đường dẫn canonical trong `project.json`, README tại workspace, và task plan. Bản khác phải được gắn `superseded` hoặc chuyển khỏi `output/`; không dùng QA report của file khác. |
| Integrity audit citation bị gọi bằng registry bằng chứng code của project. | `evidence.json` cho claim-to-source của project và WordAssistant `report-evidence.json` cho trích dẫn học thuật có schema/ý nghĩa khác nhau. | Dùng `evidence_registry_file` cho claim project; thêm `report_citation_registry_file` cho citation Word; `compose`/`integrity audit` nhận `report-evidence.json`. Checker phải hash-bind đúng registry và so citation IDs với số citation trong tài liệu. |
| Readiness checker báo render không bind với DOCX dù WordAssistant reuse render hiện tại. | Hash nằm ở `render_reuse_manifest.document_sha256`, không phải `render.document_sha256` như schema cũ giả định. | Đọc cả hai schema an toàn; có regression test cho manifest reuse; sau sửa source chạy focused tests rồi kiểm tra readiness JSON mới. |
| `capture_source_snapshot.py --help` đã ghi đè trạng thái project. | Script chạy ngay khi import, không có argparse, và cập nhật hàng loạt metadata/default acceptance checks. | Chỉ chạy công việc dưới `if __name__ == "__main__"`; parse arguments trước mọi thao tác ghi; giữ `--help` không có side effect; khi cập nhật snapshot chỉ sửa trường source revision/manifest, không chạm output, evidence registries hay acceptance checks. |
| Một asset builder có thể bị hiểu nhầm là đã kiểm route của framework bất kỳ. | Adapter hiện tự phát hiện route/template chỉ cho Java Spring MVC; chế độ render ảnh không thể chứng minh route hoặc template. | Tách `build` (Java scanner) khỏi `render` (vẽ từ inventory đã kiểm thủ công). Ghi `source_verification=NOT_RUN_MANUAL_REVIEW_REQUIRED` ở report render-only; chỉ reviewer source mới đánh dấu hình verified. |
| Bản Word có thể bị gọi là sẵn sàng nộp chỉ vì render/verify đạt. | Word delivery, học thuật/nguồn, và tuân thủ rubric là các cổng khác nhau. | Chạy `check_course_essay_readiness.py`; báo riêng cả ba cổng. Thiếu rubric, AI-disclosure policy hoặc evidence bắt buộc thì giữ `submission_readiness=INCOMPLETE`. |

## Bằng chứng của bài VietLex ngày 2026-10-20

Hồ sơ `D:\Download\ProfessionalLegalRAG\artifacts\course-essay-vietlex-20261020` ghi rõ DOCX `Final_v5` là canonical, hash của DOCX/PDF, ba registry/QA gate, danh sách nguồn và review trực quan. `qa/readiness-final.json` ghi Word delivery `PASS`, content/source `INCOMPLETE`, submission readiness `INCOMPLETE` vì rubric chưa được cung cấp. Các warning trong integrity audit vẫn là warning sau khi disposition, không được diễn giải thành xác nhận nội dung.

## Dùng với bài khác

- Đọc `docs/strongwine-course-essay-workflow.md` và starter README trước khi tạo workspace.
- Không dùng script/manifest theo framework cụ thể nếu chưa xác nhận adapter.
- Bài học không phải rubric; nguồn/project mới cần tự xác minh.
- Ghi `PASS`, `WARN`, `NOT_RUN`, `BLOCKED` dựa trên artifact thực tế; không đoán kết quả khi thiếu file hoặc log.
