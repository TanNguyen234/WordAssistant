---
name: docx-academic-writing
description: "Kỹ năng hành văn, lập luận khoa học và cấu trúc nội dung cho tiểu luận, đồ án và khóa luận tốt nghiệp theo chuẩn đại học Việt Nam."
---

# Kỹ Năng Viết Tài Liệu Học Thuật (docx-academic-writing)

## 1. Cấu Trúc Đoạn Văn Khoa Học Tiêu Chuẩn (Paragraph Structure)

Một đoạn văn học thuật chuẩn không bao giờ được viết tùy tiện hay quá ngắn/quá dài. Mỗi đoạn văn lý tưởng dài từ **4 đến 8 dòng**, tập trung giải quyết duy nhất một tiểu luận điểm và tuân theo cấu trúc **TEEL**:

1. **T - Topic Sentence (Câu chủ đề)**: Câu đầu tiên nêu rõ luận điểm chính của đoạn văn.
2. **E - Explanation (Giải thích)**: Diễn giải chi tiết hơn về câu chủ đề, làm rõ khái niệm.
3. **E - Evidence / Example (Bằng chứng / Ví dụ thực tế)**: Đưa ra số liệu, công thức, mô hình, hình vẽ hoặc trích dẫn học thuật từ `references.json` để chứng minh luận điểm.
4. **L - Link (Liên kết)**: Câu cuối cùng tóm lại vấn đề và tạo bước đệm chuyển tiếp sang đoạn tiếp theo.

---

## 2. Văn Phong Khoa Học Tiếng Việt (Academic Tone & Style)

Agent viết tài liệu học thuật bắt buộc phải tuân thủ nghiêm ngặt các quy tắc văn phong dưới đây:

### A. Tính Khách Quan (Objectivity)
* **Tuyệt đối cấm** sử dụng ngôi thứ nhất hoặc đại từ nhân xưng cá nhân như: *"tôi", "chúng em", "nhóm tác giả chúng tôi", "người viết nghĩ là..."*.
* **Thay thế bằng**: Các cấu trúc câu vô nhân xưng hoặc khách quan:
  - *Thay vì*: *"Chúng em đề xuất kiến trúc mạng..."*
  - *Sửa thành*: *"Nghiên cứu này đề xuất kiến trúc mạng..."* hoặc *"Kiến trúc mạng được đề xuất bao gồm..."*
  - *Thay vì*: *"Tôi thấy rằng mô hình BERT chạy rất nhanh..."*
  - *Sửa thành*: *"Kết quả thực nghiệm cho thấy mô hình BERT đạt tốc độ xử lý..."*

### B. Ngôn Từ Học Thuật (Formal Language)
* Tránh các từ ngữ cảm xúc, cảm tính hoặc mơ hồ: *"rất tốt", "cực kỳ mạnh", "khủng khiếp", "tuyệt vời", "có lẽ là"*.
* Sử dụng ngôn từ chính xác, khoa học: *"tối ưu hơn", "đạt hiệu suất cao hơn X%", "độ chính xác trung bình (mAP) đạt Y%"*.

### C. Sự Mạch Lạc & Chặt Chẽ (Coherence & Cohesion)
* Sử dụng linh hoạt các liên từ chuyển ý phù hợp:
  - *Bổ sung ý kiến*: "Hơn thế nữa", "Bên cạnh đó", "Ngoài ra", "Đồng thời".
  - *Mối quan hệ nhân quả*: "Do đó", "Vì vậy", "Kết quả là", "Hệ quả từ việc...".
  - *Mối quan hệ đối lập*: "Tuy nhiên", "Ngược lại", "Mặc dù vậy", "Trái lại".

---

## 3. Chỉ Dẫn Viết Chi Tiết Cho Từng Phần Báo Cáo

### A. Phần Mở Đầu (Introduction)
* Phải nêu bật được **Tính cấp thiết của đề tài** (Tại sao bài toán này lại quan trọng? Hiện tại đang gặp khó khăn gì?).
* Chỉ ra rõ ràng **Mục tiêu nghiên cứu** và **Phạm vi giới hạn** của đồ án (Đồ án giải quyết cái gì và không giải quyết cái gì).

### B. Các Chương Cơ Sở Lý Thuyết (Literature Review)
* Không chép lại toàn bộ tài liệu giáo trình một cách máy móc.
* Phải có sự tổng hợp, phân tích, so sánh ưu-nhược điểm của các công nghệ hiện tại (sử dụng Bảng biểu so sánh).
* Trích dẫn nguồn gốc đầy đủ bằng mã trích dẫn `[@cite_key]`.

### C. Chương Thiết Kế & Đề Xuất Giải Pháp (Proposed Solution)
* Tập trung mô tả đóng góp chính của sinh viên (kiến trúc đề xuất, sơ đồ khối, cơ sở dữ liệu).
* Mọi sơ đồ, hình vẽ thiết kế phải được đánh số và giải thích cặn kẽ từng thành phần cấu tạo.

### D. Chương Thực Nghiệm & Đánh Giá (Evaluation)
* Nêu rõ môi trường thử nghiệm (cấu hình phần cứng, tập dữ liệu sử dụng).
* Phải có các bảng số liệu đo lường cụ thể và đồ thị trực quan.
* Nhận xét sâu sắc về các con số đạt được, giải thích nguyên nhân tại sao mô hình đạt được kết quả đó và chỉ ra các trường hợp mô hình dự đoán sai (Error Analysis).
