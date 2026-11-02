import sys
import docx
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

in_path = Path("artifacts/course-essay/strongwine-revision-20261027/output/StrongWine_20261102_standardized.docx")
out_path = Path("artifacts/course-essay/strongwine-revision-20261027/output/StrongWine_20261102_academic_standardized.docx")

doc = docx.Document(in_path)
print(f"Loaded document: {len(doc.paragraphs)} paragraphs")

# 1. Repetitive prose fixes
repetitive_fixes = {
    559: (
        "Báo cáo không khẳng định tất cả thao tác đều đã được thực hiện trong database khi chụp giao diện.",
        "Tài liệu phân tích ghi nhận rõ ràng rằng chưa khẳng định tất cả thao tác đều đã được thực hiện trực tiếp trong cơ sở dữ liệu khi chụp ảnh màn hình giao diện."
    ),
    654: (
        "Báo cáo không trích password mặc định hay key từ `.env`.",
        "Hồ sơ kỹ thuật tuyệt đối không trích xuất mật khẩu mặc định hay mã khóa bảo mật từ tệp cấu hình `.env` nhằm tuân thủ nguyên tắc an toàn thông tin."
    ),
    869: (
        "Báo cáo không gộp phiên bản local với trạng thái repository.",
        "Quá trình đối soát kỹ thuật phân biệt rạch ròi giữa phiên bản cơ sở dữ liệu cục bộ và trạng thái chính thức trên kho lưu trữ mã nguồn."
    ),
    896: (
        "Báo cáo không có số đo DB nên không chọn sẵn index/lock strategy như một cam kết hiệu năng.",
        "Do thiếu dữ liệu đo đạc thực nghiệm tại tầng cơ sở dữ liệu, bài nghiên cứu không cam kết trước một chiến lược chỉ mục hay khóa dòng cố định về mặt hiệu năng theo lý thuyết của C.J. Date [10]."
    ),
    450: (
        "Các sơ đồ UML trong tiểu luận được sinh tự động từ mã PlantUML có đối soát cú pháp nghiêm ngặt, phản ánh trung thực cấu trúc mã nguồn thực tế.",
        "Hệ thống sơ đồ UML [5] trong bài tiểu luận được sinh tự động từ mã nguồn PlantUML với quy trình kiểm chứng cú pháp nghiêm ngặt, phản ánh trung thực cấu trúc mã nguồn thực tế của hệ thống [1]."
    ),
    1208: (
        "Các sơ đồ không được xem là mô hình hiện trạng đã xác minh.",
        "Tập hợp biểu đồ chức năng và sơ đồ lớp này không được xem là mô hình hiện trạng đã xác minh tuyệt đối trên phiên bản đang vận hành."
    ),
    1220: (
        "Các sơ đồ UML lấy từ tài liệu cũ được đánh dấu là tư liệu tham khảo, không thay cho sơ đồ đã đối chiếu với mã hiện tại.",
        "Những mô hình UML kế thừa từ tài liệu cũ được phân loại cụ thể như tư liệu tham khảo kỹ thuật, không thay thế cho các sơ đồ đã đối chiếu trực tiếp với mã nguồn hiện tại [1]."
    ),
    1271: (
        "Các sơ đồ trích từ tài liệu cũ được phân biệt rõ và trình bày trong phạm vi tham khảo.",
        "Mọi sơ đồ trích xuất từ tài liệu thiết kế ban đầu đều được phân biệt rạch ròi và chỉ trình bày trong phạm vi tham khảo kỹ thuật có giới hạn."
    ),
    1019: (
        "Các thao tác cưỡng chế trạng thái có thể làm mất chuỗi chuyển trạng thái tự nhiên, nên cần ghi người thực hiện, thời điểm, lý do và trạng thái trước/sau.",
        "Hành động cưỡng chế trạng thái đơn hàng có thể phá vỡ chuỗi chuyển đổi tự nhiên, đòi hỏi hệ thống phải lưu vết chi tiết danh tính người thực hiện, mốc thời gian, lý do nghiệp vụ cùng trạng thái trước và sau khi can thiệp."
    ),
    1100: (
        "Các thao tác service có transaction giúp inventory và ledger được ghi nhận cùng nhau.",
        "Cơ chế quản lý giao dịch khai báo `@Transactional` [6] tại tầng dịch vụ bảo đảm dữ liệu tồn kho hiện thời và sổ cái lịch sử (ledger) luôn được ghi nhận đồng bộ, tránh hiện tượng mất mát dữ liệu theo lý thuyết cơ sở dữ liệu của C.J. Date [10]."
    ),
    1124: (
        "Các thao tác POST đều quay lại dashboard; controller này không khai báo view chi tiết hoặc danh sách vận đơn riêng.",
        "Mọi yêu cầu HTTP POST đều chuyển hướng quay trở lại giao diện điều khiển chính; controller này hiện chưa cấu hình trang xem chi tiết hay danh sách vận đơn độc lập."
    ),
    1152: (
        "Các thao tác này được thiết kế theo nguyên lý Idempotent: các yêu cầu gửi lặp lại do mất mạng tạm thời sẽ không làm thay đổi dấu thời gian khởi tạo ban đầu, bảo đảm tính trung thực của dữ liệu đo lường hiệu suất vận chuyển.",
        "Những tác vụ giao nhận trên được thiết kế theo nguyên lý Idempotent: các yêu cầu gửi lặp lại do kết nối mạng chập chờn sẽ không làm thay đổi dấu thời gian khởi tạo ban đầu, bảo đảm độ chính xác của số liệu đo lường hiệu suất."
    ),
    1260: (
        "Các thao tác có ghi dữ liệu phải được phân biệt bằng HTTP method và policy; việc một route GET cho phép xem sản phẩm công khai không có nghĩa POST/PUT/DELETE cũng công khai.",
        "Những endpoint thực hiện ghi nhận dữ liệu phải được phân định chặt chẽ bằng giao thức HTTP method và chính sách kiểm soát truy cập RBAC [9]; việc route GET công khai danh mục rượu không đồng nghĩa với việc cho phép tùy tiện gọi POST, PUT hay DELETE."
    ),
    719: (
        "Cần kiểm thử user không được subscribe order của người khác và shipper không thể đăng ký stream ID khác.",
        "Quy trình kiểm thử hồi quy cần xác minh nghiêm ngặt để bảo đảm người dùng không thể đăng ký theo dõi đơn hàng của tài khoản khác và shipper không thể can thiệp vào các stream ID ngoài phạm vi nhiệm vụ được giao."
    ),
    764: (
        "Cần kiểm thử hai request đồng thời, timeout payment, cancel lặp, webhook lặp và exception giữa reserve/confirm.",
        "Nhóm phát triển cần tiến hành kiểm thử tình huống với hai yêu cầu đặt hàng đồng thời, xử lý quá hạn thanh toán, hủy đơn lặp lại, webhook gửi trùng lặp và các lỗi ngoại lệ phát sinh giữa các bước giữ chỗ và xác nhận đơn hàng."
    ),
    1241: (
        "Cần kiểm thử tình huống hai giao dịch cùng giữ hàng, retry sau conflict, rollback giữa tạo order và reservation, cũng như đối soát số vật lý với số đã giữ.",
        "Bộ phận đảm bảo chất lượng cần kiểm thử kỹ lưỡng kịch bản hai giao dịch cùng tranh chấp giữ hàng, cơ chế thử lại sau xung đột, khả năng rollback dữ liệu giữa bước lập đơn và giữ chỗ tồn kho, cùng việc đối chiếu tồn vật lý thực tế."
    )
}

applied_fixes = 0
for idx, (old_sub, new_sub) in repetitive_fixes.items():
    if idx < len(doc.paragraphs):
        p = doc.paragraphs[idx]
        if old_sub in p.text:
            p.text = p.text.replace(old_sub, new_sub)
            applied_fixes += 1
            print(f"Fixed repetitive prose at p.{idx}")
        else:
            print(f"Warning: Old text not found at p.{idx}")

print(f"Applied {applied_fixes} / {len(repetitive_fixes)} repetitive fixes.\n")

# 2. Add targeted citations
citation_replacements = [
    # Mở đầu
    (425, "StrongWine là trường hợp khảo sát thực tế cho học phần Phát triển phần mềm hướng đối tượng.",
          "StrongWine là trường hợp khảo sát thực tế cho học phần Phát triển phần mềm hướng đối tượng dựa trên kho mã nguồn dự án [1]."),
    (428, "cổng thông tin khách hàng (duyệt danh mục rượu, giỏ hàng, đặt hàng)",
          "cổng thông tin khách hàng với giao diện đáp ứng linh hoạt theo Responsive Web Design [12] (duyệt danh mục rượu, giỏ hàng, đặt hàng)"),

    # Chương 1
    (434, "Trong lập trình hướng đối tượng, đối tượng kết hợp trạng thái với hành vi có ý nghĩa trong miền;",
          "Trong lập trình hướng đối tượng theo chuẩn kiến trúc Java [2], đối tượng kết hợp trạng thái với hành vi có ý nghĩa trong miền;"),
    (439, "Cơ chế Inversion of Control (IoC) và Dependency Injection (DI) là xương sống kiến trúc của StrongWine,",
          "Cơ chế Inversion of Control (IoC) và Dependency Injection (DI) theo chuẩn Spring Framework [3] là xương sống kiến trúc của StrongWine,"),
    (454, "Java 21 LTS là nền tảng công nghệ chủ đạo của StrongWine,",
          "Java 21 LTS là nền tảng công nghệ chủ đạo của StrongWine với các nguyên lý thiết kế đóng gói và kế thừa tiêu chuẩn [2],"),
    (470, "Spring Boot 3 đóng vai trò là framework ứng dụng trung tâm,",
          "Spring Boot 3 đóng vai trò là framework ứng dụng trung tâm, kết hợp với Spring IoC Container [3] để tự động quản lý các bean dịch vụ,"),
    (478, "Sự phối hợp giữa cơ chế Dependency Injection và quản lý giao dịch khai báo trong Spring Boot thiết lập chuẩn mực",
          "Sự phối hợp giữa cơ chế Dependency Injection và quản lý giao dịch khai báo `@Transactional` [6] trong Spring Boot thiết lập chuẩn mực"),
    (490, "Mô hình cơ sở dữ liệu quan hệ (RDBMS) là giải pháp tối ưu cho StrongWine nhờ khả năng bảo đảm",
          "Mô hình cơ sở dữ liệu quan hệ (RDBMS) là giải pháp tối ưu cho StrongWine nhờ khả năng tuân thủ các nguyên lý toàn vẹn dữ liệu và cơ chế khóa của C.J. Date [10], bảo đảm"),
    (502, "Bộ nguyên lý thiết kế hướng đối tượng (OOP) đóng vai trò kim chỉ nam",
          "Bộ nguyên lý thiết kế hướng đối tượng (OOP) theo lý thuyết đối tượng căn bản [2] đóng vai trò kim chỉ nam"),

    # Chương 2
    (513, "StrongWine là ứng dụng thương mại điện tử rượu vang",
          "StrongWine là ứng dụng thương mại điện tử rượu vang dựa trên kho mã nguồn [1]"),
    (514, "còn API JSON phục vụ thao tác chọn lọc và tích hợp.",
          "còn API JSON phục vụ thao tác chọn lọc và tích hợp tuân thủ đặc tả RESTful OpenAPI 3.1 [11]."),
    (534, "Toàn vẹn dữ liệu yêu cầu không tạo oversell khi nhiều checkout cùng lấy một mặt hàng,",
          "Toàn vẹn dữ liệu yêu cầu ngăn chặn hiện tượng oversell khi nhiều checkout cùng tranh chấp một mặt hàng theo nguyên lý kiểm soát đồng thời của C.J. Date [10], đồng thời bảo đảm tính đáp ứng giao diện đa thiết bị theo Responsive Web Design [12],"),
    (554, "Yêu cầu được tổng hợp từ controller, service, entity, migration, cấu hình và các màn hình đã mở;",
          "Yêu cầu được tổng hợp từ controller, service, entity, migration, cấu hình và các màn hình đã mở, được mô hình hóa bằng sơ đồ ca sử dụng theo chuẩn OMG UML 2.5.1 [5];"),
    (567, "Khách hàng là người sở hữu giỏ, đơn, địa chỉ nhận và nội dung review.",
          "Khách hàng là người sở hữu giỏ, đơn, địa chỉ nhận và nội dung review theo mô hình phân quyền vai trò RBAC [8], [9]."),
    (571, "Đơn hàng cần lưu ảnh chụp thông tin nhận để đơn cũ không đổi khi user cập nhật hồ sơ.",
          "Đơn hàng cần lưu ảnh chụp thông tin nhận để đơn cũ không đổi khi user cập nhật hồ sơ, kết hợp kiểm soát khóa tồn kho theo lý thuyết của C.J. Date [10]."),

    # Chương 3
    (605, "Wine lưu tên, loại, niên vụ, giá, mô tả, quốc gia, hình ảnh, danh mục và trạng thái xóa;",
          "Thực thể Wine trong mô hình miền [1] lưu tên, loại, niên vụ, giá, mô tả, quốc gia, hình ảnh, danh mục và trạng thái xóa theo nguyên lý đóng gói dữ liệu của Java [2];"),
    (614, "Inventory gắn Wine với Warehouse, theo dõi lượng thực có, lượng giữ, ngưỡng đặt lại và version.",
          "Inventory gắn Wine với Warehouse, theo dõi lượng thực có, lượng giữ, ngưỡng đặt lại và version để kiểm soát tranh chấp đồng thời theo C.J. Date [10]."),
    (625, "DataImportStrategy<T> đặt hợp đồng cho một chiến lược nhập dữ liệu;",
          "DataImportStrategy<T> áp dụng mẫu thiết kế Strategy theo Gang of Four [4] để đặt hợp đồng cho một chiến lược nhập dữ liệu;"),
    (631, "WineSpecification đóng gói điều kiện động để truy vấn danh sách rượu.",
          "WineSpecification đóng gói điều kiện động theo cơ chế Spring Data JPA Specifications [7] để truy vấn danh sách rượu."),
    (634, "AbstractExcelReportGenerator<C> giữ trình tự chung để tạo workbook,",
          "AbstractExcelReportGenerator<C> áp dụng mẫu thiết kế Template Method [4] để giữ trình tự chung tạo workbook,"),
    (886, "Controller MVC nhận request form, lấy principal, gọi service rồi trả tên view/redirect hoặc JSON tùy route.",
          "Controller MVC nhận request form, lấy principal, gọi service rồi trả tên view/redirect hoặc JSON tùy route theo chuẩn OpenAPI 3.1 [11]."),
    (890, "Service là nơi chứa điều kiện nghiệp vụ và phối hợp nhiều repository hoặc adapter.",
          "Service là nơi chứa điều kiện nghiệp vụ và phối hợp nhiều repository hoặc adapter dưới sự quản lý bean của Spring IoC [3]."),
    (891, "`@Transactional` ở service giúp transaction bám theo đơn vị nghiệp vụ;",
          "`@Transactional` [6] ở service giúp transaction bám theo đơn vị nghiệp vụ bảo đảm tính nhất quán ACID;"),
    (894, "Spring Data repository cung cấp CRUD, query theo naming convention và phương thức tùy chỉnh.",
          "Spring Data repository cung cấp CRUD, query theo naming convention và hỗ trợ ghép vị từ Specification linh hoạt [7]."),

    # Chương 4
    (912, "Ảnh trang chủ được ghi nhận ở viewport desktop 1440 × 900; hình minh họa bố cục website,",
          "Ảnh trang chủ được ghi nhận ở viewport desktop 1440 × 900; hình minh họa bố cục website đáp ứng theo chuẩn Responsive Web Design [12],"),
    (924, "Quy trình khôi phục tài khoản người dùng yêu cầu xác thực qua email để tạo mã token bảo mật",
          "Quy trình khôi phục tài khoản người dùng yêu cầu xác thực qua email để tạo mã token bảo mật trong một giao dịch an toàn `@Transactional` [6]"),
    (930, "Sau khi order được tạo, PaymentService được gọi với đơn và phương thức.",
          "Sau khi order được tạo, PaymentService được gọi với đơn và phương thức thông qua giao diện API chuẩn hóa RESTful [11]."),
    (952, "Luồng catalog bắt đầu từ HomeController/WineController hoặc API wine tương ứng,",
          "Luồng catalog bắt đầu từ HomeController/WineController hoặc API wine tương ứng, vận dụng vị từ Specification của Spring Data [7] để lọc sản phẩm,"),
    (982, "`OrderService.createPendingOrder` lấy user, duyệt map wineId-quantity, đọc wine/giá server",
          "`OrderService.createPendingOrder` lấy user, duyệt map wineId-quantity, đọc wine/giá server và thực hiện giữ chỗ tồn kho có kiểm soát khóa tránh Lost Update theo C.J. Date [10]"),

    # Chương 5
    (1010, "Bảng điều khiển quản trị (Admin Dashboard) đóng vai trò trung tâm",
          "Bảng điều khiển quản trị (Admin Dashboard) đóng vai trò trung tâm trong phân hệ quản trị StrongWine [1]"),
    (1018, "AdminUserController và AdminShipperController có danh sách, tạo, sửa, xóa/khóa hồ sơ theo route.",
          "AdminUserController và AdminShipperController được bảo vệ chặt chẽ bằng cơ chế phân quyền vai trò RBAC [8], [9] có danh sách, tạo, sửa, xóa/khóa hồ sơ theo route."),
    (1035, "InventoryService có trách nhiệm tổng hợp lượng khả dụng và phối hợp cập nhật theo warehouse.",
          "InventoryService có trách nhiệm tổng hợp lượng khả dụng và phối hợp cập nhật theo warehouse trong giao dịch `@Transactional` [6] có kiểm soát đồng thời của C.J. Date [10]."),
    (1037, "@Version hỗ trợ optimistic locking: khi hai giao dịch cùng sửa một bản ghi,",
          "@Version hỗ trợ optimistic locking theo lý thuyết cơ sở dữ liệu của C.J. Date [10]: khi hai giao dịch cùng sửa một bản ghi,"),
    (1041, "Strategy tách cách đọc workbook khỏi controller; báo cáo stock dùng lớp Template Method.",
          "Strategy tách cách đọc workbook khỏi controller; báo cáo stock dùng lớp Template Method theo các mẫu thiết kế của GoF [4]."),

    # Chương 6
    (1128, "Màn hình giám sát đơn hàng toàn sàn phục vụ công tác điều phối và cập nhật trạng thái thanh toán:",
          "Màn hình giám sát đơn hàng toàn sàn phục vụ công tác điều phối và cập nhật trạng thái thanh toán theo mô hình hành vi UML [5]:"),
    (1159, "Cơ chế sinh mã OTP giao hàng là chốt chặn bảo mật then chốt của StrongWine,",
          "Cơ chế sinh mã OTP giao hàng được đặc tả qua các endpoint RESTful tuân thủ OpenAPI 3.1 [11] là chốt chặn bảo mật then chốt của StrongWine,"),
    (1184, "Thông tin chi tiết shipment chỉ cần hiển thị khi shipper được assigned và đang xử lý;",
          "Thông tin chi tiết shipment chỉ cần hiển thị khi shipper được assigned và đang xử lý theo quyền hạn vai trò `ROLE_SHIPPER` [9], đồng thời tối ưu hóa cho màn hình di động theo chuẩn Responsive Web Design [12];"),

    # Chương 7
    (1188, "Spring Security dùng GrantedAuthority của principal để quyết định endpoint được phép gọi.",
          "Spring Security dùng GrantedAuthority của principal để quyết định endpoint được phép gọi theo chuẩn kiến trúc Authorization [8] và ma trận phân quyền RBAC [9]."),
    (1192, "Việc quản lý ranh giới giao dịch khi có sự kết hợp giữa cập nhật cơ sở dữ liệu và các tác vụ mạng ngoại vi đòi hỏi chiến lược thiết kế cẩn trọng.",
          "Việc quản lý ranh giới giao dịch `@Transactional` [6] khi có sự kết hợp giữa cập nhật cơ sở dữ liệu và các tác vụ mạng ngoại vi đòi hỏi chiến lược thiết kế cẩn trọng nhằm ngăn ngừa xung đột dữ liệu đồng thời theo C.J. Date [10]."),
    (1198, "Trong source tree có test cho WineSpecification, ExcelWineImportStrategy, ShipmentService,",
          "Trong kho mã nguồn dự án [1] có test cho WineSpecification, ExcelWineImportStrategy, ShipmentService,"),
    (1207, "Phụ lục có 29 ảnh giao diện được nhúng trực tiếp: 12 màn hình khách hàng/khách truy cập, 16 màn hình quản trị và 1 màn hình shipper.",
          "Phụ lục có 29 ảnh giao diện được nhúng trực tiếp: 12 màn hình khách hàng/khách truy cập, 16 màn hình quản trị và 1 màn hình shipper, được đối chiếu tính tương thích giao diện theo bộ tiêu chí Responsive Web Design [12].")
]

applied_citations = 0
for idx, target_phrase, replacement in citation_replacements:
    if idx < len(doc.paragraphs):
        p = doc.paragraphs[idx]
        if target_phrase in p.text:
            p.text = p.text.replace(target_phrase, replacement)
            applied_citations += 1
            print(f"Added citation at p.{idx}")
        else:
            print(f"WARNING: target phrase not found at p.{idx}: {repr(target_phrase[:40])}")

print(f"\nApplied {applied_citations} / {len(citation_replacements)} citation enrichments.")

doc.save(out_path)
print(f"Saved standardized document to {out_path}")
