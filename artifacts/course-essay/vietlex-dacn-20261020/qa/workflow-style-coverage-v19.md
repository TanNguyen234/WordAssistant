# Kiểm tra workflow và style — VietLex v19

DOCX: `output/VietLex_DoAnChuyenNganh_20261025_v19-final.docx`. SHA-256: `a83d7b9163740ea92b04082a97fa7a51f6c0a6bbe718cc780ee114180f0c2732`.

Kết luận: bản trước chưa kiểm tự động căn lề heading/caption. v19 đã bổ sung kiểm tra này, sửa DOCX và profile HCMUNRE report; không áp quy tắc căn lề của báo cáo này lên mọi profile khác. Workflow đủ các bước kiểm cho phạm vi hiện tại, nhưng không thể chứng minh chất lượng nội dung chỉ bằng phần mềm.

| Hạng mục | Cách kiểm hiện có | Kết quả/phạm vi |
|---|---|---|
| Yêu cầu, nguồn kiểm soát | task-brief, crosswalk, guide/profile, source/evidence hash | Yêu cầu mới ghi trước khi sửa; trường hợp thiếu rubric vẫn INCOMPLETE |
| Heading đúng nghĩa, cấp và thứ tự | Word Heading, numbering, outline/TOC parity, hierarchy guard | 111 heading; giữ 1.1/1.1.1; NỘI DUNG ngoài TOC |
| Căn lề heading | **Mới:** style inheritance + conflicting paragraph overrides; style.update alignment | 111 heading LEFT trong Word đã lưu; style Heading 1–3 LEFT, zero indents |
| Font/cỡ chữ/giãn dòng/thụt đầu dòng | Profile validation, style-size inheritance, run checks và audit thân bài | Font/cỡ/giãn dòng theo phạm vi profile; 214 đoạn thân bài vẫn 1 cm. Đậm/nghiêng và bố cục nhìn thấy được rà trên trang; không tuyên bố mọi thuộc tính style đã có bộ kiểm tự động |
| Caption hình | **Mới:** captions.figure_alignment và kiểm caption theo nhãn hình | 14 caption CENTER; không ép caption bảng thành CENTER |
| Tên hình | Review biên tập từng tên + plan exact hash giữ SEQ | Tên ngắn; bỏ GET/route/ID, trạng thái runtime và giải thích ký pháp khỏi tên; giữ thông tin đó trong thân bài/registry. Chưa có suy luận tự động về tên có đúng nghĩa/đủ gọn |
| Hình, bảng và số thứ tự | Asset matrix, embedded media counts, SEQ/native lists, table geometry, keep-with-next/repeating headers | 31 asset, 16 media placement, 15 bảng editable; không suy ngữ nghĩa hình từ số lượng |
| Lưu và mở lại bằng Word | field update-all vào bản mới; native verify; render bản đã lưu | PASS; Word tự bỏ LEFT override dư và kế thừa đúng từ Heading styles |
| Phân trang và hình thức | Xem đủ 93 trang của bản render cuối | PASS: caption giữa, heading trái; không thấy crop, đè chữ hoặc trang trắng ngoài ý muốn |
| Lập luận, mô hình, nguồn | Content-review plan, source hashes, reviewed academic evidence, integrity warning dispositions | PASS hồ sơ kiểm; ý nghĩa mô hình/claim support cần review đã ghi, không phải tác vụ detector |
| Sẵn sàng nộp | Readiness tách Word delivery/content/submission | Word PASS; rubric học phần và người duyệt vẫn còn thiếu |

## File thay đổi lần này

- `src/wordassistant/operations/styles.py`: lưu alignment trong Word style; từ chối giá trị sai.
- `src/wordassistant/cli_contracts.py`: công khai alignment trong hợp đồng style.update.
- `src/wordassistant/document/validate.py`: kiểm alignment kế thừa của style đang dùng, direct overrides và caption hình theo profile.
- `src/wordassistant/profiles/loader.py`: schema figure_alignment, từ chối kiểu/giá trị không hợp lệ.
- `profiles/hcmunre_dacn_2026_2027.json` và bản packaged: report heading LEFT, figure CENTER theo yêu cầu người dùng; ghi provenance của lựa chọn.
- `src/wordassistant/document/scaffold.py`: tiêu đề phần đầu kế thừa căn lề được cấu hình; giữ fallback cũ khi profile không chọn căn lề.
- `tests/test_style_alignment.py`: kiểm kế thừa, override sai, persistent style sai dù đoạn nhìn đúng, caption hình/bảng khác nhau, input cấu hình sai, style.update roundtrip.
- `.agents/skills/wordassistant/SKILL.md`, `docs/course-report-workflow.md`: thêm bước kiểm căn lề và tên hình ngắn; nội dung phụ thuộc môn/profile.
- Hai plan trong `qa/plans/`: chỉ đổi title suffix sau SEQ và alignment; giữ bản v18 làm input.

## Kiểm chứng

- Focused pytest cho style/profile/CLI contract: PASS; ca kiểm căn lề sai đã thất bại trước khi triển khai và đạt sau sửa.
- Profile validate: PASS (`qa/validate-v19.json`). Native fields/render/visual delivery: PASS (`qa/verify-v19-delivery.json`).
- `python scripts/sync_package_data.py --check`: PASS. Skill quick_validate: PASS. `git diff --check`: PASS, chỉ thông báo LF/CRLF.
- Full suite đầu phát hiện scaffold ép CENTER cho 10 tiêu đề dù profile LEFT. Đã thêm regression test (thất bại trước sửa), sửa scaffold và chạy lại focused tests: PASS. Full suite sau sửa đang chờ kết quả cuối.
- Mức kiểm chứng: unit/integration và Microsoft Word cục bộ thật; source/diff review vì CRG không khả dụng. Không commit/push, không gọi model provider, không giả credentials/deployment hay phê duyệt của giảng viên.

Giới hạn: hiệu lực luật hiện hành, benchmark VietLex mới, tuyến cần quyền riêng và deployment parity chưa được chạy lại. Những giới hạn này không được chuyển thành PASS bởi sửa style.
