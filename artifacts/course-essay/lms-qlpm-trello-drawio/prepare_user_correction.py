"""Prepare a scoped editorial plan; no application source changes."""
import hashlib, json
from pathlib import Path
from docx import Document

R=Path(__file__).resolve().parent
d=Document(R/'output/final.docx')
sections={}; current=None
for p in d.paragraphs:
    if p.style.name.startswith('Heading '): current=p.text; sections[current]=[]
    elif current: sections[current].append(p)

texts={
'MỞ ĐẦU': [
'Trong hoạt động đào tạo đại học, tài liệu học tập, bài nộp và điểm số thường đi qua nhiều kênh trao đổi. Khi các kênh này thiếu liên kết, giảng viên khó theo dõi tiến độ và sinh viên khó xác định thông tin nào đang có hiệu lực. Đề tài LMS được xây dựng để tập trung nội dung học phần, quản lý bài tập và cung cấp bảng điểm theo vai trò. Quy mô 10.000 sinh viên và 500 giảng viên trong điều lệ là giả định thiết kế, chưa phải quy mô triển khai đã được đo lường.',
'Bài tiểu luận phân tích cách quản lý dự án LMS từ xác lập mục tiêu đến nghiệm thu sản phẩm. Trọng tâm là sự nhất quán giữa phạm vi, công việc, nguồn lực và điều kiện chấp nhận. Trello được sử dụng để quan sát trạng thái công việc; Draw.io giúp diễn giải cấu trúc và quy tắc nghiệp vụ. Hai công cụ có ý nghĩa khi từng thẻ và sơ đồ liên kết được với một đầu ra cụ thể trong kế hoạch.',
'Phương pháp thực hiện gồm đối chiếu hồ sơ quản lý dự án với mã nguồn, kiểm tra các số liệu kế hoạch và quan sát ứng dụng trong môi trường thử nghiệm. Bộ hồ sơ đối soát ngày 21/10/2026 được dùng làm căn cứ cho đường cơ sở. Ảnh Trello và website LMS được chụp trực tiếp ngày 26/10/2026 để bổ sung bằng chứng về trạng thái giao diện; việc quan sát này không thay thế kiểm thử chấp nhận toàn bộ hệ thống.',
'Phạm vi đánh giá dừng ở kế hoạch học thuật và bản mẫu phần mềm trong môi trường cục bộ. Những biểu mẫu nghiệm thu, chỉ số chi phí và vai trò phê duyệt trong hồ sơ được phân biệt với kết quả thực tế. Thông tin nhận dạng sinh viên, lớp và giảng viên hướng dẫn chưa được cung cấp nên không được suy đoán từ tài liệu mẫu.'
],
'CHƯƠNG 1. TỔNG QUAN VÀ KHỞI TẠO DỰ ÁN':[
'Dự án PRJ-LMS-2026 hướng đến một hệ thống học tập trên web phục vụ quản trị viên, giảng viên và sinh viên. Vấn đề đặt ra không chỉ là xây dựng các màn hình chức năng mà còn là tổ chức luồng thông tin xuyên suốt từ giao bài, nộp bài đến phản hồi và tổng hợp điểm. Điều lệ vì vậy cần nêu rõ sản phẩm tối thiểu, người có trách nhiệm quyết định và giới hạn nguồn lực trước khi nhóm lập kế hoạch chi tiết.',
'Bảng điều lệ tóm tắt các ràng buộc dùng để đối chiếu tiến độ và chi phí. Đây là đường cơ sở của bài toán học thuật. Các đại diện nghiệp vụ và quyền phê duyệt trong mô hình cần được xác nhận khi chuyển sang triển khai thực tế.'
],
'Business case và mục tiêu':[
'Phạm vi chức năng bao gồm quản lý tài khoản, khóa học, ghi danh, nội dung học tập, bài tập, bài kiểm tra, điểm và thông báo. Mười kịch bản AC-01 đến AC-10 cụ thể hóa điều kiện chấp nhận cho các nhóm chức năng này. Cách xác định mục tiêu theo hành vi có thể kiểm tra giúp nhóm tránh đánh giá sản phẩm chỉ bằng số màn hình đã xây dựng.',
'Để giữ quy mô khả thi, bản mẫu sử dụng giao diện web, dịch vụ API và SQL Server. Đăng nhập một lần, thanh toán, hội nghị video, trò chuyện thời gian thực và ứng dụng di động riêng chưa nằm trong phạm vi. Việc loại trừ này tạo ranh giới để đánh giá yêu cầu phát sinh, thay vì coi mọi chức năng có ích đều là cam kết của dự án.'
],
'Giả định và ràng buộc':[
'Đường cơ sở được đối soát là 20 tuần, 1,2 tỷ đồng và tổng phân bổ 8,5 nhân sự toàn thời gian quy đổi (FTE). FTE biểu thị khối lượng thời gian lao động, không xác định số người trong nhóm. Kế hoạch còn phụ thuộc vào khả năng cung cấp yêu cầu của đại diện nghiệp vụ, năng lực chuyên môn và việc chuẩn bị môi trường thử nghiệm; thay đổi các giả định này có thể làm thay đổi lịch hoặc chi phí.',
'Kiến trúc ứng dụng tổ chức giao diện React, dịch vụ FastAPI và lớp dữ liệu SQL Server. Việc phân chia này giúp nhóm xác định các đầu ra thiết kế, phát triển và kiểm thử riêng, đồng thời phải lập kế hoạch cho phần tích hợp giữa chúng. Ảnh giao diện trong báo cáo phản ánh môi trường thử nghiệm cục bộ, chưa xác nhận khả năng vận hành sản xuất.'
],
'CHƯƠNG 2. CÁC BÊN LIÊN QUAN VÀ TỔ CHỨC DỰ ÁN':[
'Các bên liên quan có nhu cầu và quyền quyết định khác nhau. Phòng Đào tạo cung cấp yêu cầu về quy trình học vụ; bộ phận công nghệ thông tin quan tâm đến kiến trúc và vận hành; giảng viên, sinh viên phản hồi trải nghiệm sử dụng. Người quản lý dự án cần tổng hợp các yêu cầu này và xử lý xung đột giữa lợi ích nghiệp vụ với giới hạn nguồn lực.',
'Nhóm có quyền lực và mức quan tâm cao cần tham gia ở các mốc quyết định về phạm vi, thiết kế và nghiệm thu. Người sử dụng trực tiếp cần được mời quan sát bản mẫu để phát hiện bất tiện trước khi hoàn tất sản phẩm. Phản hồi sử dụng và quyết định phê duyệt là hai loại đầu vào khác nhau, vì vậy kế hoạch truyền thông phải xác định rõ mục đích của từng cuộc trao đổi.'
],
'Sổ stakeholder':[
'Sổ các bên liên quan dưới đây giữ lại nhóm vai trò và cách tham gia được mô tả trong hồ sơ nguồn. Việc ghi nhận theo vai trò giúp lập kế hoạch tham vấn khi chưa có người đại diện được chỉ định; bảng không tự xác nhận rằng các đơn vị đã đồng ý tham gia dự án.'
],
'RACI và escalation':[
'Ma trận RACI phân biệt người thực hiện (Responsible), người chịu trách nhiệm cuối cùng (Accountable), người được tham vấn (Consulted) và người được thông báo (Informed). Mỗi đầu ra chỉ nên có một vai trò Accountable để tránh bỏ sót hoặc chồng chéo quyền quyết định. Bảng rút gọn tách việc soạn hồ sơ khỏi việc ký phê duyệt, bởi người tạo ra tài liệu và người chấp thuận tài liệu có thể khác nhau.'
],
'CHƯƠNG 3. QUẢN LÝ PHẠM VI VÀ WBS':[
'Phạm vi sản phẩm xác định LMS phải làm được gì, còn phạm vi dự án xác định nhóm cần thực hiện những công việc nào để bàn giao sản phẩm đó. Trong bản mẫu, luồng cốt lõi bao gồm quản lý khóa học, ghi danh, cung cấp nội dung, nộp bài văn bản, làm bài kiểm tra và xem điểm. Công việc thiết kế, chuẩn bị dữ liệu, kiểm thử và viết hướng dẫn cũng phải được tính vào phạm vi dự án dù không trực tiếp tạo thêm màn hình.',
'Bên cạnh chức năng, nhóm cần kiểm soát phân quyền tại máy chủ, tính toàn vẹn dữ liệu và các trạng thái giao diện khi tải, thành công, rỗng hoặc lỗi. Chẳng hạn, việc sinh viên nhìn thấy nút nộp bài chưa đủ để kết luận yêu cầu được đáp ứng: API còn phải kiểm tra ghi danh, hạn nộp và quyền sửa bài. Các điều kiện này cần được chuyển thành tiêu chí kiểm thử.',
'Cấu trúc phân chia công việc (WBS) trong hồ sơ nhóm các đầu ra từ khởi tạo, phân tích, thiết kế đến phát triển, kiểm thử và bàn giao. Cách phân rã theo đầu ra hỗ trợ giao việc và ước lượng. Khi liên kết WBS với thẻ Trello, nhóm có thể theo dõi sản phẩm còn thiếu thay vì chỉ đếm số thao tác đã thực hiện.'
],
'Ranh giới và acceptance':[
'Mỗi yêu cầu cần có mã truy vết, điều kiện kiểm tra và bằng chứng dự kiến. Khi phát sinh yêu cầu mới, nhóm lập đề nghị thay đổi, phân tích tác động lên phạm vi, tiến độ, chi phí và chất lượng rồi trình người có thẩm quyền quyết định. Ví dụ, bổ sung tải tệp cho bài nộp không phải một chỉnh sửa giao diện đơn lẻ: nó còn kéo theo lưu trữ, giới hạn tệp và kiểm soát truy cập. Vì bản mẫu hiện nhận nội dung văn bản, chức năng tải tệp được giữ ngoài phạm vi đã thống nhất.'
],
'Work breakdown':[
'Một gói công việc chỉ có thể được quản lý khi xác định được đầu ra, người phụ trách, đầu vào và điều kiện hoàn tất. Với luồng bài tập, nhóm có thể phân chia thành đặc tả quy tắc nộp, thiết kế giao diện, xử lý API và kiểm tra quyền. Sự phân chia này giúp tìm nguyên nhân khi một luồng chưa hoạt động đầy đủ, thay vì xem việc có giao diện là đã bàn giao toàn bộ chức năng.'
],
'CHƯƠNG 4. QUẢN LÝ TIẾN ĐỘ VÀ CPM':[
'Kế hoạch tiến độ gồm 19 hoạt động liên kết theo quan hệ kết thúc trước khi bắt đầu. Phương pháp đường găng (CPM) tính thời điểm bắt đầu và kết thúc sớm theo chiều thuận, sau đó tính thời điểm muộn từ mốc kết thúc dự kiến. Độ dự trữ toàn phần là chênh lệch giữa thời điểm bắt đầu muộn và sớm; chỉ số này cho biết khả năng dịch chuyển hoạt động mà chưa làm trễ dự án theo mạng lịch đã lập. [1]',
'Kết quả đối soát cho thấy mốc kết thúc kế hoạch ở tuần 20. ACT-04 có một tuần dự trữ và ACT-16 có hai tuần; các hoạt động còn lại trong bảng có độ dự trữ bằng không. Vì vậy, chậm một hoạt động không có dự trữ có thể tác động trực tiếp đến mốc kết thúc nếu các giả định khác giữ nguyên.',
'Các mốc điều lệ được đặt ở tuần 2, 4, 6, 12, 15, 16, 18 và 20 để tạo điểm kiểm soát từ khởi tạo đến đóng dự án. Sơ đồ mạng minh họa thứ tự phụ thuộc, còn bảng CPM là căn cứ cho thời lượng và độ dự trữ. Lịch theo tháng trong Trello là kế hoạch riêng của nhóm và không tự thay thế đường cơ sở này.'
],
'Theo dõi sai lệch':[
'Ở mỗi kỳ báo cáo, người quản lý dự án cần so sánh thời điểm dự báo với lịch cơ sở, xác định hoạt động gây chậm và người xử lý. Việc khôi phục lịch có thể đòi hỏi điều chỉnh thứ tự, bổ sung nguồn lực hoặc thu hẹp phạm vi, nhưng mỗi phương án đều phải xem xét tác động chi phí và chất lượng. Khi chưa có nhật ký bắt đầu và kết thúc thực tế, báo cáo chỉ phân tích kế hoạch, chưa tính tỷ lệ hoàn thành thực hiện.'
],
'CHƯƠNG 5. QUẢN LÝ NGUỒN LỰC VÀ CHI PHÍ':[
'Dự toán kết hợp phân rã công việc với đơn giá theo vai trò. Tổng phân bổ là 8,5 FTE trên chín dòng vai trò; một người có thể đảm nhiệm nhiều vai trò theo giai đoạn. Sáu khoản mục gồm lao động 840 triệu, hạ tầng 120 triệu, công cụ 48 triệu, đào tạo 40 triệu, hành chính 32 triệu và dự phòng 120 triệu đồng, cộng thành ngân sách cơ sở 1,2 tỷ đồng.',
'Dòng tiền dự kiến chia thành năm giai đoạn với các mức 180, 150, 450, 240 và 180 triệu đồng. Giai đoạn phát triển chiếm mức cao nhất, vì vậy chậm thiết kế hoặc thiếu đầu vào trước phát triển có thể làm nguồn lực được bố trí nhưng chưa sử dụng hiệu quả. Khoản dự phòng cần gắn với rủi ro hoặc thay đổi được chấp thuận, không mặc nhiên coi là tiền đã chi.',
'Đánh giá chi phí trong quá trình thực hiện cần phân biệt ngân sách, giá trị công việc đã hoàn thành và chi phí thực tế có chứng từ. Ví dụ EVM ở Chương 10 chỉ minh họa phép tính theo số liệu giả định. Báo cáo không sử dụng ví dụ này để kết luận dự án đã tiết kiệm ngân sách.'
],
'Resource breakdown':[
'Nguồn lực được bố trí cho quản lý dự án, phân tích nghiệp vụ, thiết kế trải nghiệm, phát triển, kiểm thử và vận hành. Kiểm thử cần tham gia từ giai đoạn đặc tả để làm rõ tiêu chí chấp nhận; vận hành cần chuẩn bị môi trường trước thời điểm tích hợp. Việc bố trí theo giai đoạn giúp hạn chế tình trạng phát triển xong nhưng chưa có dữ liệu hoặc môi trường để kiểm tra.'
],
'Kiểm soát chi phí':[
'Kiểm soát chi phí cần đối chiếu ngân sách được duyệt với chi phí phát sinh có căn cứ, đồng thời cập nhật dự báo phần việc còn lại. Thẻ Trello có thể liên kết đến mã WBS và đề nghị thay đổi, nhưng không thay sổ theo dõi chi phí. Khi một yêu cầu làm tăng khối lượng phát triển hoặc kiểm thử, quyết định chấp thuận phải chỉ ra nguồn kinh phí và ảnh hưởng đến lịch.'
],
'CHƯƠNG 6. QUẢN LÝ RỦI RO':[
'Sổ rủi ro sử dụng thang điểm khả năng xảy ra và mức tác động từ 1 đến 5 để sắp xếp ưu tiên. Tích hai điểm hỗ trợ so sánh trong phạm vi kế hoạch, không phải xác suất thống kê. Mỗi rủi ro cần có dấu hiệu kích hoạt, người theo dõi và phương án ứng phó để việc đánh giá dẫn đến hành động cụ thể.',
'Những rủi ro đáng chú ý gồm mở rộng phạm vi, truy cập sai quyền, trễ phát triển và phản hồi nghiệm thu muộn. Ví dụ, kỳ vọng nộp tệp trong khi bản mẫu chỉ nhận văn bản có thể tạo tranh luận về phạm vi ở cuối kỳ. Nhóm cần giải thích giới hạn này ngay từ đặc tả và đối chiếu nó khi trình diễn sản phẩm.',
'Biện pháp ứng phó phải gắn với nguyên nhân rủi ro. Kiểm soát thay đổi xử lý yêu cầu ngoài phạm vi; kiểm tra quyền ở API và kịch bản từ chối truy cập xử lý nguy cơ phân quyền; trình diễn sớm giúp phát hiện khác biệt kỳ vọng. Khoản dự phòng 120 triệu đồng chỉ được sử dụng theo quyết định kiểm soát, chưa có bằng chứng giải ngân thực tế.'
],
'Giám sát và ứng phó':[
'Theo kế hoạch, sổ rủi ro được rà soát hằng tuần. Khi dấu hiệu kích hoạt xuất hiện, người phụ trách ghi nhận tình hình, đánh giá ảnh hưởng và chuyển thành vấn đề cần xử lý nếu sự kiện đã xảy ra. Những vấn đề tác động đến đường găng hoặc ngân sách phải được báo lên cấp quyết định; việc có tên trong sổ không chứng minh rằng rủi ro đã phát sinh hay đã được khắc phục.'
],
'CHƯƠNG 7. QUẢN LÝ CHẤT LƯỢNG VÀ KIỂM THỬ':[
'Chất lượng được quản lý bằng điều kiện đầu ra và các cổng kiểm soát. Định nghĩa hoàn tất yêu cầu chức năng đúng đặc tả, có kiểm tra trường hợp hợp lệ và bị từ chối, API có tài liệu và giao diện xử lý được các trạng thái cần thiết. Mục tiêu không còn lỗi nghiêm trọng P0/P1 là điều kiện của kế hoạch, chưa phải kết quả kiểm thử được xác nhận.',
'Năm cổng chất lượng lần lượt kiểm soát phạm vi, thiết kế, chức năng, mức sẵn sàng kiểm thử chấp nhận và hồ sơ đóng dự án. Cổng không đạt phải tạo công việc khắc phục với người xử lý rõ ràng. Do đó, chuyển thẻ sang Done không thay được việc kiểm tra các tiêu chí đầu ra.',
'Kế hoạch kiểm thử chấp nhận người dùng (UAT) gồm mười kịch bản cho ba vai trò. Trong lần quan sát ngày 26/10/2026, báo cáo đã ghi nhận giao diện đăng nhập, quản trị tài khoản, xem bài nộp và bảng điểm trên dữ liệu kiểm thử. Những ảnh này xác nhận các trạng thái đã quan sát, nhưng chưa đủ để đánh dấu cả mười kịch bản UAT là đạt.'
],
'Gate và DoD':[
'Các cổng được đặt tại tuần 4, 6, 12, 15 và 20 của đường cơ sở. Cổng đầu kiểm tra yêu cầu và phạm vi; cổng thiết kế kiểm tra kiến trúc, dữ liệu và API; các cổng sau kiểm tra chức năng, dữ liệu thử nghiệm và khả năng bàn giao. Việc đặt điều kiện tại từng mốc giúp phát hiện thiếu sót trước khi chuyển sang giai đoạn có chi phí sửa lỗi lớn hơn.'
],
'UAT và triage':[
'Mỗi kịch bản UAT cần dữ liệu đầu vào, bước thao tác, kết quả mong đợi và bằng chứng thực hiện. Khi xuất hiện lỗi, nhóm phân loại mức ảnh hưởng, xác định người sửa và kiểm tra lại trước khi đóng. Các mẫu kết quả trong hồ sơ vẫn được giữ nhãn mô phỏng; ảnh quan sát giao diện trong phụ lục không tự chuyển các mẫu đó thành biên bản nghiệm thu.'
],
'CHƯƠNG 8. TRUYỀN THÔNG, THAY ĐỔI VÀ TRELLO':[
'Truyền thông dự án cần bảo đảm mỗi quyết định đến đúng người và có thể truy lại căn cứ. Kế hoạch tổ chức họp nhóm hằng tuần, báo cáo theo mốc và trao đổi nghiệp vụ theo đầu ra cần xem xét. Biên bản cần ghi rõ quyết định, công việc tiếp theo, người phụ trách và thời hạn để tránh tình trạng đã trao đổi nhưng chưa có người thực hiện.',
'Khi phát sinh thay đổi, nhóm ghi nhận đề nghị, phân tích tác động rồi trình người có thẩm quyền quyết định. Quyết định được chấp thuận mới là căn cứ cập nhật đường cơ sở. Trello phản ánh việc đang được xử lý và liên kết đến hồ sơ thay đổi, nên có vai trò hỗ trợ thực hiện và truy vết.',
'Trello tổ chức công việc bằng bảng, danh sách và thẻ. Mỗi thẻ có thể chứa mô tả, nhãn, ngày và tài liệu đính kèm; danh sách kiểm tra chia đầu ra thành những điều kiện nhỏ hơn để rà soát. Trong dự án LMS, cách tổ chức này giúp nối thẻ quản lý dự án với sơ đồ Draw.io và bằng chứng sản phẩm. [2] [3]',
'Snapshot ngày 23/10/2026 ghi nhận 9 danh sách và 39 thẻ. Quan sát trực tiếp ngày 26/10/2026 cho thấy To Do có 25 thẻ, các cột Doing, Review và Done đang trống, còn Blocked chứa yêu cầu xác nhận rubric. Vì vậy, board phản ánh việc đã được tổ chức và các câu hỏi còn tồn đọng, chưa cho phép kết luận công việc đã hoàn thành.'
],
'Luồng board và quy ước':[
'Luồng quản lý đề xuất đi từ Backlog qua To Do, Doing, Review rồi Done; Blocked tách những công việc chưa thể tiếp tục. Trong thẻ PM-04 được chụp trực tiếp, checklist WBS có bảy mục chưa đánh dấu hoàn tất. Nội dung yêu cầu phân biệt phạm vi sản phẩm với phạm vi dự án, xác định đầu ra và người phụ trách. Đây là minh chứng về tiêu chí quản lý đã có trên công cụ, đồng thời cho thấy việc kiểm tra hoàn tất vẫn còn mở.'
],
'Kết nối Trello — WBS — Draw.io — Word':[
'Một đầu ra chỉ truy vết được khi tên và mã công việc giữ nhất quán giữa WBS, thẻ Trello, tệp sơ đồ và báo cáo. Chẳng hạn, thẻ thiết kế luồng nộp bài cần liên kết với sơ đồ và tiêu chí kiểm tra hạn nộp trong API. Lịch nhóm tháng 10–11 và ngân sách 27 triệu đồng trong kịch bản ZIP thuộc bối cảnh khác với đường cơ sở 20 tuần, 1,2 tỷ đồng; báo cáo không cộng gộp hoặc thay thế hai tập số liệu.'
],
'CHƯƠNG 10. NGHIỆM THU VÀ ĐÓNG DỰ ÁN':[
'Nghiệm thu cần đối chiếu từng yêu cầu với kết quả chạy và bằng chứng tương ứng. Hồ sơ đóng dự án phải tập hợp phiên bản nguồn, kết quả kiểm thử, các vấn đề còn mở, hướng dẫn vận hành và quyết định chấp thuận. Khi thiếu chữ ký hoặc kết quả UAT, nhóm chỉ có thể trình bày mức sẵn sàng bàn giao, chưa xác nhận nghiệm thu chính thức.'
],
'Lessons learned và hướng phát triển':[
'Qua đối chiếu hồ sơ và quan sát công cụ, bài học chính là cần quản lý thống nhất kế hoạch, trạng thái công việc và bằng chứng sản phẩm. Một thẻ có checklist chưa đủ để xác nhận đầu ra; một màn hình hiển thị được chưa đủ để xác nhận toàn bộ luồng nghiệp vụ. Ở giai đoạn tiếp theo, nhóm cần hoàn tất người phụ trách và tiêu chí review trên Trello, thực hiện các kịch bản UAT còn mở, rồi mới xem xét mở rộng tải tệp, đăng nhập một lần hoặc tích hợp lớp học.'
],
'KẾT LUẬN VÀ KIẾN NGHỊ':[
'Bài tiểu luận đã đối chiếu kế hoạch quản lý LMS với hồ sơ dự án, mô hình thiết kế và ứng dụng thử nghiệm. Đường cơ sở 20 tuần, 1,2 tỷ đồng và 8,5 FTE được giữ nhất quán; WBS, RACI, mạng lịch, dự toán và sổ rủi ro tạo căn cứ phân công và kiểm soát thay đổi. Trello thể hiện cách tổ chức công việc, còn bộ mô hình Draw.io làm rõ phạm vi vai trò, dữ liệu và luồng bài tập.',
'Ảnh chụp trực tiếp đã bổ sung bằng chứng về board Trello, checklist WBS và các màn hình LMS theo ba vai trò. Tuy vậy, Done còn trống và các kịch bản nghiệm thu vẫn chưa được xác nhận đầy đủ. Trước khi nộp, cần bổ sung thông tin bìa và tiêu chí môn học chính thức, hoàn tất những minh chứng còn thiếu rồi đối chiếu lại với yêu cầu của giảng viên.'
]
}
rewrites=[]; complex_rewrites=[]
for heading, newtexts in texts.items():
    ps=sections[heading]
    eligible=[(i,p) for i,p in enumerate(ps) if p.text and p.style.name!='Caption' and not p._p.xpath('.//w:drawing')]
    assert len(eligible)>=len(newtexts),heading
    for (i,p),text in zip(eligible,newtexts):
        item={'section':heading,'paragraph_index':i,'text':text}
        (complex_rewrites if p._p.xpath('.//w:sdt') else rewrites).append(item)
spec={'input_sha256':hashlib.sha256((R/'output/final.docx').read_bytes()).hexdigest(),
'scope_start':'MỞ ĐẦU','scope_end':'Trạng thái bài nộp','rewrites':rewrites}
(R/'user-correction-prose.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2),encoding='utf-8')
(R/'user-correction-citation-paragraphs.json').write_text(json.dumps(complex_rewrites,ensure_ascii=False,indent=2),encoding='utf-8')
print('Prepared',len(rewrites),'scoped paragraph rewrites')
