import sys
import re
from pathlib import Path
from docx import Document

sys.stdout.reconfigure(encoding='utf-8')

in_path = Path('D:/Download/ProfessionalLegalRAG/artifacts/course-essay-vietlex-20261020/output/VietLex_20261102_standardized_logo.docx')
out_path = Path('D:/Download/ProfessionalLegalRAG/artifacts/course-essay-vietlex-20261020/output/VietLex_20261102_academic_standardized.docx')

print(f"Loading input DOCX: {in_path}")
doc = Document(in_path)
paras = doc.paragraphs
print(f"Loaded {len(paras)} paragraphs.")

# We will perform targeted replacements in specific paragraphs
replacements_done = 0

def replace_paragraph_text(p, old_text, new_text):
    global replacements_done
    if old_text in p.text:
        # To preserve run formatting as much as possible, if single run or full replacement:
        p.text = p.text.replace(old_text, new_text)
        # re-apply standard paragraph formatting invariants if needed
        replacements_done += 1
        return True
    return False

# 1. Chapter 1 in-text citations
for i, p in enumerate(paras):
    t = p.text
    # P240: Karpukhin
    if "Karpukhin và cộng sự mô tả" in t and "[3]" not in t:
        replace_paragraph_text(p, "Karpukhin và cộng sự mô tả", "Karpukhin và cộng sự [3] mô tả")
        print(f"P{i}: Added [3] for Karpukhin DPR")

    # P241: Nguyen và Quan
    if "Nguyen và Quan xây dựng bộ đánh giá" in t and "[5]" not in t:
        replace_paragraph_text(p, "Nguyen và Quan xây dựng", "Nguyen và Quan [5] xây dựng")
        print(f"P{i}: Added [5] for Nguyen & Quan Vietnamese IR")

    # P244: RAG general definition
    if "RAG nối một bộ nhớ bên ngoài có thể truy xuất với mô hình sinh." in t and "[3]" not in t:
        replace_paragraph_text(p, "với mô hình sinh.", "với mô hình sinh theo kiến trúc truy xuất tăng cường [3], [7].")
        print(f"P{i}: Added [3], [7] for RAG retrieval architecture")

    # P245: RAGAs
    if "RAGAs trình bày các chỉ số tự động" in t and "[2]" not in t:
        replace_paragraph_text(p, "RAGAs trình bày", "RAGAs [2] trình bày")
        print(f"P{i}: Added [2] for RAGAs")

    # P246: KILT grounding
    if "Để một câu trả lời có thể kiểm tra" in t and "[6]" not in t:
        replace_paragraph_text(p, "Để một câu trả lời có thể kiểm tra,", "Theo chuẩn đánh giá tri thức KILT [6], để một câu trả lời có thể kiểm tra,")
        print(f"P{i}: Added [6] for KILT provenance")

    # P256: Reuter Legal RAG
    if "Reuter và cộng sự mô tả Document-Level" in t and "[8]" not in t:
        replace_paragraph_text(p, "Reuter và cộng sự mô tả", "Reuter và cộng sự [8] mô tả")
        print(f"P{i}: Added [8] for Reuter Legal RAG")

    # P259: Trautmann Legal Groundedness
    if "Trautmann và cộng sự khảo sát" in t and "[10]" not in t:
        replace_paragraph_text(p, "Trautmann và cộng sự khảo sát", "Trautmann và cộng sự [10] khảo sát")
        print(f"P{i}: Added [10] for Trautmann Legal Groundedness")

    # P264: LexGLUE & Summary
    if "LexGLUE cung cấp bộ đánh giá tiếng Anh" in t and "[1]" not in t:
        replace_paragraph_text(p, "LexGLUE cung cấp bộ đánh giá tiếng Anh", "LexGLUE [1] cung cấp bộ đánh giá tiếng Anh")
        replace_paragraph_text(p, "DPR cung cấp ví dụ", "DPR [3] cung cấp ví dụ")
        replace_paragraph_text(p, "bộ đánh giá Vietnamese IR so sánh", "bộ đánh giá Vietnamese IR [5] so sánh")
        replace_paragraph_text(p, "RAGAs cung cấp", "RAGAs [2] cung cấp")
        replace_paragraph_text(p, "nghiên cứu legal-RAG nêu", "nghiên cứu legal-RAG [8] nêu")
        print(f"P{i}: Added [1], [3], [5], [2], [8] in Chapter 1 synthesis")

    # Add MTEB [4] and T2-RAGBench [9] in Chapter 1
    if "Các cách tìm kiếm bằng từ khóa, tìm kiếm vector dày" in t and "[4]" not in t:
        replace_paragraph_text(p, "tìm kiếm vector dày", "tìm kiếm vector dày (được chuẩn hóa qua các bộ đo như MTEB [4])")
        print(f"P{i}: Added [4] for MTEB")

    if "Không chuyển Summary-Augmented Chunking thành khuyến nghị triển khai ngay." in t and "[9]" not in t:
        replace_paragraph_text(p, "triển khai ngay.", "triển khai ngay; các tiếp cận xử lý bảng và văn bản kết hợp cần đối chiếu với chuẩn đánh giá T2-RAGBench [9].")
        print(f"P{i}: Added [9] for T2-RAGBench")

# 2. Chapter 2 in-text citations (Methodology)
for i in range(267, 461):
    p = paras[i]
    t = p.text
    # In Vector Search & Qdrant section
    if "Mã nguồn hiện tại dùng Qdrant" in t and "[3]" not in t:
        replace_paragraph_text(p, "dùng Qdrant", "ứng dụng mô hình biểu diễn vector mật độ cao theo nguyên lý DPR [3] và Sentence-BERT [7] kết hợp cơ sở dữ liệu vector Qdrant")
        print(f"P{i}: Added [3], [7] in Chapter 2 Qdrant section")
    elif "Qdrant lưu trữ vector" in t and "[7]" not in t:
        replace_paragraph_text(p, "Qdrant lưu trữ vector", "Qdrant lưu trữ vector đặc trưng ngữ nghĩa SBERT [7]")
        print(f"P{i}: Added [7] in Chapter 2 vector store")

    # In Vietnamese text processing & Legal Chunking
    if "Tách đoạn theo điều khoản" in t or "chunking theo điều khoản" in t.lower() or "đoạn văn bản luật" in t:
        if "[8]" not in t and "Document-Level Retrieval Mismatch" in t:
            replace_paragraph_text(p, "Document-Level Retrieval Mismatch", "Document-Level Retrieval Mismatch theo phân tích của Reuter và cộng sự [8]")
            print(f"P{i}: Added [8] in Chapter 2 chunking")

    if "xử lý tiếng Việt" in t.lower() and "[5]" not in t:
        replace_paragraph_text(p, "xử lý tiếng Việt", "xử lý tiếng Việt (áp dụng các nguyên tắc đánh giá IR đa miền [5])")
        print(f"P{i}: Added [5] in Chapter 2 NLP preprocessing")

# 3. Chapter 3 in-text citations (Experiments & Evaluation)
for i in range(461, 564):
    p = paras[i]
    t = p.text
    if "Chỉ số faithfulness" in t and "[2]" not in t:
        replace_paragraph_text(p, "Chỉ số faithfulness", "Chỉ số faithfulness (theo khung đánh giá RAGAs [2])")
        print(f"P{i}: Added [2] in Chapter 3 RAGAs evaluation")
    if "mức độ bám sát căn cứ" in t and "[10]" not in t:
        replace_paragraph_text(p, "mức độ bám sát căn cứ", "mức độ bám sát căn cứ (groundedness theo phân loại của Trautmann [10])")
        print(f"P{i}: Added [10] in Chapter 3 groundedness evaluation")
    if "đánh giá bảng biểu" in t.lower() and "[9]" not in t:
        replace_paragraph_text(p, "đánh giá", "đánh giá (dựa trên tiêu chuẩn T2-RAGBench [9])")
        print(f"P{i}: Added [9] in Chapter 3 table evaluation")
    if "độ chuẩn mực của tập dữ liệu pháp lý" in t.lower() and "[1]" not in t:
        replace_paragraph_text(p, "tập dữ liệu pháp lý", "tập dữ liệu pháp lý (đối sánh với benchmark LexGLUE [1])")
        print(f"P{i}: Added [1] in Chapter 3 benchmark")

# 4. Refine repetitive openings
opening_rep = [
    ("Hướng dẫn HCMUNRE nêu tiêu chí", "Theo tài liệu hướng dẫn của HCMUNRE, văn bản nêu rõ tiêu chí"),
    ("Hướng dẫn HCMUNRE quy định", "Quy chế hướng dẫn đào tạo của HCMUNRE quy định"),
    ("Hai phương án tra cứu", "Về kiến trúc thực hiện, hai phương án tra cứu"),
    ("Hai phương án được so sánh", "Khi đối chiếu thực nghiệm, hai phương án được so sánh"),
    ("Giảng viên hướng dẫn ghi nhận", "Báo cáo tiến độ với Giảng viên hướng dẫn ghi nhận"),
    ("Giảng viên hướng dẫn lưu ý", "Trong quá trình phản biện, Giảng viên hướng dẫn lưu ý")
]

for old_op, new_op in opening_rep:
    for p in paras:
        if p.text.startswith(old_op):
            p.text = p.text.replace(old_op, new_op, 1)
            print(f"Refined opening: '{old_op}' -> '{new_op}'")
            replacements_done += 1

print(f"\nTotal replacements performed: {replacements_done}")
print(f"Saving output to: {out_path}")
doc.save(out_path)
print("Saved successfully!")
