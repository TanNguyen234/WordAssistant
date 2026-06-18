# MỞ ĐẦU

Ngày nay, sự phát triển vượt bậc của Trí tuệ Nhân tạo (AI) và Xử lý Ngôn ngữ Tự nhiên (NLP) đã làm thay đổi hoàn toàn cách con người tương tác với máy tính. Trong đó, mô hình Transformer [@vaswani2017attention] là một trong những cột mốc vĩ đại nhất, đóng vai trò nền tảng cho hầu hết các kiến trúc LLM hiện đại.

Mục tiêu của nghiên cứu này là ứng dụng các mô hình học sâu tiên tiến để xây dựng một trợ lý hỗ trợ viết tài liệu học thuật đạt tiêu chuẩn Việt Nam.

# CHƯƠNG 1: CƠ SỞ LÝ THUYẾT NỀN TẢNG

## 1.1. Kiến trúc Transformer
Kiến trúc Transformer do Vaswani và các cộng sự [@vaswani2017attention] đề xuất đã loại bỏ hoàn toàn các mạng tuần hoàn (RNN) truyền thống, thay thế bằng cơ chế Self-Attention. Cơ chế này cho phép mô hình xử lý song song toàn bộ chuỗi đầu vào, giúp tăng tốc độ huấn luyện đáng kể.

## 1.2. Mô hình BERT
BERT [@devlin2018bert] (Bidirectional Encoder Representations from Transformers) được thiết kế để huấn luyện trước các biểu diễn ngữ cảnh hai chiều từ văn bản chưa được gán nhãn. Khác với các mô hình một chiều truyền thống, BERT đọc toàn bộ chuỗi từ trái sang phải và từ phải sang trái đồng thời.

*Bảng 1.1: So sánh hiệu năng các dòng mô hình ngôn ngữ*

| Tên Mô Hình | Kiến Trúc | Số Tham Số | Độ Chính Xác (GLUE) |
|---|---|---|---|
| BERT-Base | Encoder-only | 110M | 79.6 |
| GPT-2 | Decoder-only | 1.5B | 70.2 |
| Transformer-Base | Encoder-Decoder | 65M | 68.9 |

Nghiên cứu ứng dụng tại Việt Nam của Nguyễn Văn Tấn [@nguyen2023rag] cũng chứng minh rằng việc kết hợp Transformer với cơ sở dữ liệu tri thức ngoài giúp tối ưu hóa đáng kể khả năng trả lời câu hỏi tự động.
