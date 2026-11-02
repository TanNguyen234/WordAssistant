# Ba báo cáo học phần — brief công việc hiện hành (2026-10-27)

## Yêu cầu
Hoàn thiện cả ba báo cáo LMS, VietLex và StrongWine; không kết thúc sau khi chỉ sửa một báo cáo. Dùng StrongWine v3 làm tham chiếu bố cục chung cho cùng sinh viên, không sao chép dữ kiện giữa các project. Sinh viên cả ba bài: Nguyễn Thành Duy Tân, MSSV 1250080266, lớp 12_ĐH_CNPM3. GVHD LMS và VietLex: ThS. Định Thị Hồng Loan; StrongWine giữ GVHD Th.S. Ngô Tân Khai.

## Bản đầu vào cần bảo toàn và ứng viên hiện hành
- LMS nguồn: `artifacts/course-essay/lms-qlpm-trello-drawio/output/LMS_HCMUNRE_Viet_hoa.docx` — SHA-256 `6f68151f42380f8935737823c2a55f6cd37a55b5023ec7c707d4f7d4dffeaf5b`. Ứng viên đang rà: `output/LMS_wbs_can_chinh_dang_kiem_tra.docx` — `8c7f2242d1948a8776c043737d296515d4253c8b57416623de0e2a8551623694`; `project.json` hiện trỏ đúng file này, brief LMS cũ còn mâu thuẫn và phải cập nhật.
- StrongWine nguồn: `artifacts/strongwine_course_essay_final_checked_v3.docx` — SHA-256 `a931f779627763dba4d50847c277e3702f32b04d648be9e3752154d5eb70ffe5`. Ứng viên: `artifacts/course-essay/strongwine-revision-20261027/StrongWine_field_300.docx` — `cdde02c878e6766dd3ec5a7dd28f7ecc0a14a45b78f93887e09b9450d741d526`.
- VietLex nguồn: `D:/Download/ProfessionalLegalRAG/artifacts/course-essay-vietlex-20261020/output/VietLex_DoAnChuyenNganh_20261025_v20-final.docx` — SHA-256 `aa6bae6a26b3d077d6d90d7282b0c724a09bec6ba0e5415ebff6f15082dd6c9b`. Ứng viên: `output/VietLex_20261027_dang_kiem_tra.docx` — `b8490a3766649c05ca5ac4d3de49d144376d8149bbb2862dc4871f380a68a7cf`.

## Phát hiện hiện tại và thứ tự xử lý
- Render mới nhất của ba ứng viên cho thấy mỗi bài đều có hai bìa nội dung gần như trùng nhau liên tiếp. Sửa cấu trúc trang bìa và bỏ trang bìa lặp trên bản sao, giữ nguyên section break cần thiết, cập nhật trường Word sau đó.
- Bìa LMS cần đưa tên học phần lên vị trí và kiểu chữ tương tự StrongWine, căn lại thông tin tác giả, mã số, lớp và giảng viên; giữ logo, trường/khoa, tên đề tài, loại bài, GVHD và hồ sơ HCMUNRE đúng.
- LMS: đối soát đủ 8 nhóm WBS theo nguồn; làm hình WBS dễ đọc ở kích thước in; tiếp tục so nội dung 10 chương với outline và hồ sơ dự án.
- VietLex: bản ứng viên có một chỉnh sửa về lưu lịch sử hội thoại; rà tiếp các claim/source hashes đã đổi, không khẳng định trạng thái pháp luật hoặc runtime chưa được kiểm tra.
- StrongWine: xử lý các góp ý giảng viên còn điền sẵn và tuyên bố liêm chính; rà lại nội dung/source, fields, bảng/hình và các mục NOT_RUN.

## Tiêu chí hoàn tất và giới hạn
Bảo toàn mọi đầu vào; làm việc trên output bản sao duy nhất mỗi lần; bố cục bìa/heading/caption hài hòa theo StrongWine trong khi giữ facts và profile riêng; kiểm tra outline/TOC, hình/bảng/caption, claims/evidence, integrity warnings, cập nhật field bằng Word, render đầu ra cuối và rà từng trang. Rà soát cover đang phát hiện và sửa cả ba. Chạy readiness cho từng workspace và báo riêng Word delivery, content/source review, submission readiness.

Không bịa kết quả, chữ ký, phê duyệt, đánh giá, nguồn hỗ trợ hoặc ảnh chụp runtime. LMS còn UAT/loại capture/HTTP provenance chưa đủ; VietLex còn rubric môn học và kiểm chứng current law/protected routes/benchmark chưa chạy; StrongWine còn rubric/chạy profile môn học/ảnh runtime mới chưa có. Giữ các cổng đó INCOMPLETE/NOT_RUN, không biến Word PASS thành sẵn sàng nộp. Không commit, xóa đầu vào, gửi thông báo hay ghi lên Trello/dịch vụ ngoài.

## QA hiện hành
- LMS `qa/strongwine-reference-20261027/readiness-wbs-grid.json` khóa SHA `8c7f...`; hiện FAIL. Rà hình hiện chỉ bao quát trang 22.
- StrongWine `readiness-field.json` khóa SHA `cdde...`; hiện FAIL. Render 175 trang; so 144 dpi cho thấy trang 5–9 đổi; chưa có xác nhận rà toàn bộ bản cuối.
- VietLex `qa/readiness-20261027-draft.json` khóa SHA `b849...`; hiện FAIL. Render 93 trang; rà ảnh contact-sheet chưa đủ để kết luận chất lượng hình/luận điểm.

## Bước kế tiếp
Cập nhật crosswalk và project pointers theo hashes trên; lập chỉnh sửa native Word có kiểm soát để bỏ bìa lặp và căn bìa theo StrongWine; tạo output mới, cập nhật trường, render và so lại; sau đó rà nội dung/hình/QA theo từng bài cho đến khi đủ cả ba.

## Tiếp tục 28/10 — trạng thái đối soát
- LMS: ứng viên `output/LMS_HCMUNRE_Viet_hoa_hoan_thien_20261027.docx`, SHA-256 `ce49b7607740c4364f5a99666ee157ef1328cde0905a60441cc7c4fe5abf69f4`; WBS đủ tám nhóm, hình và bảng đã đối chiếu nguồn; bản render 70 trang chỉ mới rà chọn trang. Bìa còn khác khung và logo mẫu StrongWine.
- StrongWine: `artifacts/course-essay/strongwine-revision-20261027/StrongWine_20261027_pagebreak_final.docx`, SHA-256 `ea7c4f45cdb4d8009a7184b57f6db2eee701f8589fe5bd1eb7e4dfa6e267f8bd` (xem project pointer khi cập nhật; hash thực tế sẽ kiểm lại).
- VietLex: `output/VietLex_20261027_bia_chuan_final.docx`, SHA-256 `32f2da9018a37c39997c7867dd73a5baa2793e525a5afad9dd085b0c3f71eee3`.
- Tiếp theo: đồng bộ khung/logo bìa, cập nhật trường bằng Word, render và rà từng trang; cập nhật project pointers và readiness theo hash cuối. Các QA cũ là lịch sử, chưa chứng nhận bản mới.

- LMS ứng viên mới: `output/LMS_20261028_bia_dong_bo.docx`, SHA-256 `864c61d92cabef2ecd98cccb629004c8b6e22b22338adbf3a5114232a0b0c621`. Đã thay khung bìa theo StrongWine, tăng logo lên 3,2 cm, tách bốn dòng thông tin và cập nhật fields bằng Word thành công. Render đang chạy; chưa chứng nhận trang bìa hay cập nhật project pointer. QA `qa/final-review-20261027/field-cover-20261028.json`.

- LMS ứng viên mới nhất `output/LMS_20261028_bia_can_chinh.docx`, SHA-256 `653b9ad354d8480c90da0d472820aeceaa9bfe233639607ad250ce335514f4b7`. Word đã cập nhật fields, render 70 trang; đã xem trang bìa: khung đôi, logo 3,2 cm, thông tin và ngày không tràn. Cần xem trang 2 và toàn bộ trang, cập nhật các ma trận/project pointer cùng QA trước khi kết luận. Render: `qa/final-review-20261027/render-cover-spacing-20261028/`. VietLex và StrongWine vẫn cần hoàn tất rà và QA.

- Rà contact-sheet toàn bộ LMS 70, VietLex 92, StrongWine 174 trang: `artifacts/course-essay/visual-triage-20261028.json` gắn hash. LMS hình 2 trang 24, hình 5–6 trang 40 chữ quá nhỏ; cần dựng/bố trí lại theo nguồn. VietLex/StrongWine còn ảnh và bảng cần rà cận cảnh. Không coi contact-sheet là kiểm tra nội dung hay PASS. Bước tiếp theo: xử lý hình LMS rồi rà lại ba bản và readiness.

- LMS ứng viên `output/LMS_20261028_kientruc_giu_chuthich.docx`, SHA-256 `ac8d69095d25fec2b107b98704ca5f9851d7ea106a9513c1c77ad0ba0548d084`. Hình 5 được dựng lại bằng Archify theo `docs/03_ARCHITECTURE.md` commit 41935af, xác định là thiết kế; Word field update thành công và render 72 trang. Trang 41 hình/chú thích/nguồn cùng trang; đoạn dẫn ERD cuối trang 41 còn tách hình, cần ghép khi xử lý hình 6. Hình 2 và 6 vẫn nhỏ. Xem `.archify/architecture-lms-readable-20261028/` và `qa/final-review-20261027/render-architecture-keep-20261028/`. QA và các pointers trước vẫn chưa áp dụng hash mới.

- LMS ứng viên `output/LMS_20261028_phuthuoc.docx` SHA-256 `0067266030bf04985b463b5cefd0408543e5d03a28fa0e7cb0ec33e13c294119`; Word update thành công, render 73 trang. Hình 2 được dựng theo 7 nút và 7 cạnh của `LMS_14.drawio`, bằng chứng `.archify/architecture-lms-dependencies-20261028/`, hình/chú thích/nguồn trên trang 25. Nhãn vẫn nhỏ khi in, cần tiếp tục tối ưu; Hình 6 ERD chưa thay. Các kiểm tra trước gắn hash cũ.

- Đang đồng bộ bìa VietLex theo mẫu StrongWine: khung đôi hiện có, logo 3,2 cm, chữ thông tin 13 pt và vị trí ngày cuối bìa; giữ nguyên tên đề tài/loại báo cáo/GVHD. Nguồn ứng viên `VietLex_20261027_bia_chuan_final.docx` SHA `32f2da9018a37c39997c7867dd73a5baa2793e525a5afad9dd085b0c3f71eee3`; tạo bản mới và cập nhật trường, render trước khi thay pointer.

- VietLex ứng viên `output/VietLex_20261028_bia_dong_bo.docx` SHA-256 `23abd0e334c41ecaf928ac91e75a9a8999b928868828e30102853b1f7cd68210`; Word update thành công và render 92 trang. Đã xem trang 1–3: bìa một trang, thông tin và ngày không tràn, tiếp theo lời cảm ơn và mẫu cam đoan. Render `qa/render-cover-20261028/`; chưa rà toàn trang sau thay đổi và chưa cập nhật project pointer/QA.

- Cập nhật `project.json` ba workspace trỏ lần lượt LMS `006726...`, StrongWine `ea7c4f...`, VietLex `23abd0...`. Đã chạy readiness theo từng bản ngày 28/10: cả ba FAIL do QA/validate cũ khác hash; LMS còn thiếu HTTP capture và kiểm tra rubric theo hash; VietLex thiếu 1 hình theo asset matrix và nhiều hash mã nguồn đã thay đổi; StrongWine thiếu rubric/hồ sơ review. Kết quả `qa/readiness-current-20261028.json` (StrongWine ở workspace root). Không chuyển các mục sang PASS khi chưa có chứng cứ mới. Bước tiếp: kiểm tra các thay đổi nguồn VietLex và sơ đồ LMS, khôi phục parity hình, rà và verify từng bản.

- VietLex `asset-parity-20261028.csv` thay matrix cũ, chỉ bỏ LOGO-002 tương ứng bìa lặp đã bỏ; F01 vẫn đúng ảnh nguồn. Readiness `qa/readiness-asset-20261028.json`: media PASS 15/15, submission còn FAIL. `qa/validate-cover-20261028.json`: valid true nhưng báo thiếu dòng header trường theo profile và thiếu bìa trong; cần đối chiếu hướng dẫn gốc và lựa chọn StrongWine, không tự coi warning là PASS. Sáu source files đổi hash so với snapshot; xem `qa/source-hash-triage-20261028.json`, chưa rebind claim.

- Đối chiếu hướng dẫn trường: mục “Trang bìa trong (trình bày giống trang bìa)” yêu cầu hai trang; sẽ bổ sung bìa trong VietLex cùng thông tin, không bịa khóa hoặc phê duyệt. Dòng tên trường hiện viết đầy đủ tương đương tên viết tắt trong profile; giữ đồng nhất mẫu StrongWine và ghi nhận warning kiểm tra exact text.

- VietLex hiện `output/VietLex_20261028_bia_trong_sach.docx` SHA `c23681942320299b117e13d1493447938cea9a2c7fbb8ee0907d1f359d37a027`: bìa trong khôi phục theo hướng dẫn chính thức, chân trang bìa trong bỏ; Word cập nhật fields và render 93 trang. PDF kiểm tra trang 2 không chân trang, trang 3 vẫn có chân trang; cần rà lại toàn bộ, validate/verify theo hash, `asset-parity-inner-cover-20261028.csv` ghi lại hai logo.

- LMS chọn hướng dẫn HCMUNRE với override tiểu luận, hướng dẫn quy định bìa trong giống bìa ngoài. Thêm bìa trong trên bản sao `LMS_20261028_phuthuoc.docx`, giữ metadata đã xác nhận; kiểm tra lại trường/số trang/matrix và mọi QA sau chỉnh sửa.

- LMS ứng viên `output/LMS_20261028_bia_trong.docx` SHA `aaff90458d4ab8fe8b92d7c71eaf17b465f31a397d5233b3435aa7fab8e3d810`, render 74 trang; bìa ngoài, bìa trong, lời cảm ơn đúng thứ tự, bìa trong không tràn. `project.json` và matrix `asset-parity-20261028.csv` đã trỏ bản mới; hình 2 vẫn đánh dấu NOT_RUN về độ đọc và hình 6 cần cải thiện, QA trước lỗi thời.

- VietLex: đã rà lại hai claim GET /search và GET /documents/{document_id} ở `app/api/legal_routes.py` hiện hành, hash `7f4b0b48...`, nhánh lỗi được ghi rõ. `claim-evidence-20261028.csv` và `evidence-20261028.json` là bản sao giữ các claim khác chưa sửa; readiness `qa/readiness-legal-routes-20261028.json` xác nhận hai claim PASS. Kiểm tra này là tĩnh, các claim nguồn còn lại và runtime vẫn chưa xác nhận.

- VietLex rà thêm template hỏi đáp, `RetrievalOutcome`/`LegalRetriever`, và V3 expansion/hash theo mã hiện tại. `claim-evidence-20261028-review2.csv`, `evidence-20261028-review2.json`, `qa/source-review-template-retrieval-expansion-20261028.md`; readiness `qa/readiness-source-review2-20261028.json` xác nhận ba claim PASS ở mức mã tĩnh. POST /chat và RAG pipeline còn chờ rà lại; không coi đây là chứng cứ runtime.

- VietLex: rà POST /chat theo source hiện tại hash `3edd3d0d...`; `claim-evidence-20261028-review3.csv`, `evidence-20261028-review3.json`, `qa/source-review-chat-route-20261028.md`; có nhánh kiểm tra và cache tùy điều kiện, lỗi và local stateless. Kiểm tra readiness mới chưa chạy; RAG pipeline vẫn chờ rà.

- VietLex: bổ sung mốc đối chiếu dữ liệu 27/10 từ `docs/evaluation/runs/corpus-clean-expand-20261027T021029Z/REPORT.md` SHA `55b5a38edec62d7bb3c1e317e1f09b9fe73b1cf31f9c043e18f80dae2a2b7bd5`; giữ mốc 17/10 như lịch sử, không khẳng định độ đúng pháp lý hay nghiệm thu triển khai. Sửa bản sao và rà/field/render lại.

- VietLex mới `output/VietLex_20261028_corpus.docx` SHA `79b6c234e679c080deb9cc9dff5e3dd6ba630333e6206cc76ba77cbe50490d1f`, Word fields cập nhật và render 93 trang. Đã xem trang 58 đoạn số liệu 27/10; source hash và giới hạn ghi `claim-evidence-20261028-review6.csv`, `evidence-20261028-review6.json`. Project pointer đã chuyển; QA cũ lỗi thời, cần verify lại.

- LMS: bổ sung lời giải thích đọc được về 12 bảng và các khóa ngoại dựa trên `database/01_schema.sql`, vì hình ERD hiện chữ nhỏ và giản lược một số quan hệ. Nêu rõ hình giản lược và dẫn schema; không coi là bằng chứng runtime.

- LMS ứng viên `output/LMS_20261028_erd_giai_thich.docx` SHA `9df771ed371d62cfd542e7e1d80e651078def96a94bcdebbd216a4442eae3049`. Word đã cập nhật fields, render 74 trang; trang 44 phần giải thích 12 bảng và FK, hình 6, caption/source ở cùng trang. Hình nguyên gốc vẫn nhỏ nên cần làm rõ hình; lời giải thích không thay thế kiểm tra runtime. Project pointer đã cập nhật; QA cũ không chứng nhận hash mới.

- LMS ứng viên `output/LMS_20261028_phuthuoc_ro_giu.docx` SHA `bd773c1499bdad86fbf084f405176bba431516aa3d6b5685951b1cf8d0cfec6d`. Hình 2 bố trí lại, chữ lớn, giữ 7 nút và 7 cạnh từ Draw.io; đã xem trang 26 cùng chú thích và nguồn, render 74 trang. `asset-parity-readable-20261028.csv` cập nhật FIG-02; project pointer đã chuyển. ERD vẫn nhỏ, cần tiếp tục; QA tổng theo hash mới chưa chạy.

- LMS ERD: bổ sung hai hình chi tiết theo 12 bảng/16 FK của `database/01_schema.sql` SHA `025c97ac98d90caabb7787315abd00b98fd5b371a7b6a0db5595a1ffee24017a`, giữ sơ đồ gốc và diễn giải mũi tên từ bảng được tham chiếu đến bảng chứa FK. Hai FK Grades trỏ Users dùng chung một đường, nêu rõ trong nhãn. Sau chèn cập nhật fields, render, kiểm tra hình/caption và asset matrix.

- LMS ứng viên `output/LMS_20261028_erd_chitiet.docx` SHA `2188123a367a3b973cdcc1a902518291c192769f35db44a84f5950954d23fc4d`, Word fields updated, render 75 trang. Trang 45 có hai sơ đồ chi tiết theo SQL, nêu chiều mũi tên và hai FK Grades→Users; đã xem, B chữ còn nhỏ hơn A. `asset-parity-erd-detail-20261028.csv` ghi hai subfigure không caption riêng và trỏ bằng chứng. Rà gate và toàn bộ trang sau chỉnh sửa còn lại.

- Readiness `qa/readiness-erd-detail-20261028.json`: tổng 29/29 ảnh, nhưng kiểm tra ghép caption FAIL ở FIG-01, FIG-02, TBL-16 sau khi thêm hai subfigure không caption; phải điều tra thuật toán ghép và xác minh thứ tự thực tế, không đổi ma trận sai để ép PASS. Các gate khác vẫn chưa hoàn tất.

- Sửa `scripts/check_course_essay_readiness.py` để ảnh không caption ở giữa tài liệu dùng `uncaptioned_anchor` duy nhất và ảnh ngay sau nhãn; ảnh bìa cũ vẫn dùng cách prefix. Test phải từ chối nhãn thiếu/lặp/tái sử dụng và kiểm tra bố cục cũ. Matrix `asset-parity-erd-anchor-20261028.csv` ghi hai nhãn chính xác. Chưa có QA toàn diện mới cho đến khi test/kiểm tra ổn định. CRG không khả dụng, đối chiếu trực tiếp mã nguồn.

- Checker hỗ trợ `uncaptioned_anchor` chính xác/duy nhất, ảnh ngay sau nhãn; test thiếu/trùng/tái dùng và tương thích logo PASS. `python -m pytest tests/test_course_essay_readiness.py -q` PASS sau thay đổi; tài liệu `docs/course-report-workflow.md` đã cập nhật. CRG không có; rà source trực tiếp. Readiness `qa/readiness-anchored-20261028.json`: LMS media PASS 29/29; VietLex media PASS 16/16, nhưng gates tổng vẫn FAIL do verify/validate cũ hash, rubric/review/evidence còn thiếu. StrongWine thiếu matrices và rubric, tổng FAIL. VietLex `qa/readiness-source-aligned-20261028.json` cho claim số liệu 27/10 PASS sau đồng bộ support_location, không xác nhận submission. Tiếp theo: validate/verify theo hash hiện hành, rà StrongWine và khôi phục matrices, kiểm tra các phần thiếu.

- Chuẩn hóa hai dòng tên trường trên bìa LMS và VietLex đúng mẫu hướng dẫn đã chọn (“TP.HCM”), giữ tên trường và thông tin tác giả/giảng viên. Bản StrongWine giữ kiểu riêng của tiểu luận; cập nhật Word fields và render lại các bản thay đổi.

- LMS `output/LMS_20261028_truong.docx` SHA `c41b0d9b9ad8a8fe861159bcc25df88da68bb0c5b4f23c9563a88ac08e71f469`, render 75 trang; VietLex `output/VietLex_20261028_truong.docx` SHA `1c7d7dd24eb375138d5c8b2ba60dbe792bf4696df81c1d2483bf410fed9f7b59`, render 93 trang. Word fields cập nhật, bìa ngoài và trong đúng mẫu tên trường. VietLex validate valid true không issue; LMS valid true, warning Heading 1 căn giữa theo StrongWine và khung bìa theo mẫu cần đối chiếu offsetFrom. Project pointers đã đổi; verify chính xác còn chờ.

- LMS verify report `qa/verify-LMS_20261028_truong.json` FAIL: table 6 grid/tbl width 9071 twip, cell total 9070; footer thiếu sinh viên; heading center theo StrongWine và header học phần thay vì chuỗi title auto-extracted, border 4pt offset từ text cần phân tích, không đổi quy tắc profile để ép PASS. Sửa grid 1 twip và thêm sinh viên vào footer, giữ PAGE field, cập nhật fields/render.

- LMS bản mới output/LMS_20261028_chantrang_bang.docx SHA 46ee0217d5093ff4ba1b4184c7a2e586aac69597584b8c2704d92913df226d60; sửa tổng độ rộng bảng WBS và thêm tên/MSSV chân trang; Word fields và render 75 trang, đã xem trang mở đầu. Project pointer đã cập nhật; verify/readiness và rà toàn trang theo hash mới chưa hoàn tất.

- LMS verify theo SHA 46ee0217...: cấu trúc, đánh số, geometry, fields, Word và render 75 trang PASS; format FAIL do Heading 1 giữa theo mẫu StrongWine, border inset và header topic; visual REVIEW_REQUIRED. QA qa/verify-LMS_20261028_chantrang_bang.json; validate qa/validate-footer-grid-20261028.json. Đã đồng bộ project pointer/hash/QA. Không coi PASS giao Word hay đủ điều kiện nộp. StrongWine media-comparison-20261028.json xác nhận 62 tệp media cùng hash bản v3 và bản hiện hành, không chứng minh nội dung hay runtime. Đang verify bản StrongWine hiện hành.

- Khung bìa LMS: phép đo PDF trang 1 qa/cover-border-measurement-20261028.json cho khoảng cách top 29,16 pt, bottom 29,04 pt, left 78,14 pt, right 49,70 pt; cảnh báo 4 pt là giá trị XML space, không khớp vị trí render. Chưa xử lý heading/header. Audit integrity exact hash: LMS qa/integrity-footer-grid-20261028.json, VietLex qa/integrity-truong-20261028.json, StrongWine integrity-pagebreak-20261028.json đều WARN và chưa có registry khi chạy, cần phân loại cảnh báo; StrongWine có 4 mục tham khảo 9–12 không được phát hiện trích dẫn, cùng tuyên bố cá nhân cần người thực hiện xác nhận thực tế. Không khẳng định đã qua review nội dung.

- Đã xem contact sheets toàn bộ LMS (75 trang) và VietLex (93 trang) từ ảnh verify có hash; chỉ kết luận rà bố cục tổng thể, một số sơ đồ nhỏ cần xem cận cảnh và chưa có content audit hoàn chỉnh. StrongWine verify-pagebreak-20261028.json: Word/render PASS 174 trang, structure/numbering/fields PASS, format và table geometry FAIL, visual REVIEW_REQUIRED; nhiều lỗi format đến từ generic profile không phải rubric môn. Project pointer verify đã cập nhật, readiness-pagebreak-current-20261028.json FAIL; cần phân tích geometry, rà toàn trang và nội dung. Lời cam đoan StrongWine cần tác giả đối chiếu, không tự xác nhận.

- StrongWine inspect-full-pagebreak-20261028.json: 40/44 bảng bị checker đánh FAIL geometry; nhiều bảng Word ở chế độ auto có tblW 0, các bảng khác có tổng lưới 8957 và ô 9000 twip. Cần phân biệt auto hợp lệ với mismatch thực tế và xem các bảng 10–17 cột trước sửa; không đổi hàng loạt để ép PASS. VietLex đã xem cận cảnh trang 32, 42, 44, 52, 56: hình 2.1 phân cấp màn hình chữ quá nhỏ; các sơ đồ 2.5, 2.6, 2.8, 2.9 đọc được tại render 120 dpi. Cần xử lý hình 2.1 dựa trên nguồn và tái kiểm bản mới.
