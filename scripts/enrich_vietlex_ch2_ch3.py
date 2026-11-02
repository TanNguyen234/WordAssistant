import sys
from pathlib import Path
from docx import Document

sys.stdout.reconfigure(encoding='utf-8')

docx_path = Path('D:/Download/ProfessionalLegalRAG/artifacts/course-essay-vietlex-20261020/output/VietLex_20261102_academic_standardized.docx')
doc = Document(docx_path)
paras = doc.paragraphs

replacements = 0

def rep(p, old, new):
    global replacements
    if old in p.text:
        p.text = p.text.replace(old, new)
        replacements += 1
        return True
    return False

for i, p in enumerate(paras):
    t = p.text

    # Chapter 2: EvidenceChunk & Provenance
    if "EvidenceChunk là đối tượng dữ liệu bất biến được khai báo" in t and "[6]" not in t:
        rep(p, "bất biến được khai báo", "bất biến được thiết kế theo tiêu chuẩn lưu vết nguồn KILT [6] và kiểm soát ranh giới văn bản [8], khai báo")
        print(f"P{i}: Added [6], [8] in EvidenceChunk definition")

    # Chapter 2: V3 Dense + Sparse Retrieval on Qdrant
    if "Phương án V3 kết hợp vector dày với vector thưa IDF trên Qdrant" in t and "[3]" not in t:
        rep(p, "trên Qdrant rồi hợp nhất các danh sách xếp hạng.", "trên Qdrant (vận dụng mô hình biểu diễn mật độ cao DPR [3] cùng Sentence-BERT [7]) rồi hợp nhất danh sách xếp hạng theo đặc thù truy xuất tiếng Việt [5].")
        print(f"P{i}: Added [3], [7], [5] in V3 Hybrid Retrieval")

    # Chapter 2: Branch V3 metadata & vector dimension
    if "Trong nhánh V3, dữ liệu trả về được kiểm tra" in t and "[7]" not in t:
        rep(p, "dữ liệu trả về được kiểm tra", "dữ liệu trả về (tương ứng với không gian vector ngữ nghĩa SBERT [7]) được kiểm tra")
        print(f"P{i}: Added [7] in V3 vector data")

    # Chapter 2: Chunking and index rebuild
    if "Khi thay cách chuẩn hóa, chia đoạn, tạo vector" in t and "[8]" not in t:
        rep(p, "cấu trúc thông tin,", "cấu trúc thông tin (nhằm hạn chế lỗi Document-Level Mismatch theo Reuter [8]),")
        print(f"P{i}: Added [8] in chunking structure")

    # Chapter 3: Recall@K and provenance
    if "Đối với truy xuất, Recall@K phải dựa trên nhãn căn cứ" in t and "[6]" not in t:
        rep(p, "nhãn căn cứ đã được kiểm tra.", "nhãn căn cứ đã được kiểm tra theo chuẩn đối soát tập dữ liệu tri thức [6].")
        print(f"P{i}: Added [6] in Recall@K evaluation")

    # Chapter 3: Groundedness & Trautmann
    if "Kết quả câu trả lời cho thấy mức khớp hoàn toàn" in t and "[10]" not in t:
        rep(p, "mức khớp hoàn toàn 0/50,", "mức khớp hoàn toàn 0/50 (chứng minh sự cần thiết của thước đo mức độ bám sát căn cứ Groundedness [10]),")
        print(f"P{i}: Added [10] in Groundedness analysis")

    # Chapter 3: Document mismatch & Legal RAG
    if "Retrieval có thể tìm đúng văn bản nhưng sai điều/khoản;" in t and "[8]" not in t:
        rep(p, "sai điều/khoản;", "sai điều/khoản (hiện tượng điển hình được Reuter và cộng sự [8] chỉ ra);")
        print(f"P{i}: Added [8] in Retrieval error analysis")

    # Chapter 3: Vietnamese IR domain reference
    if "Một bộ đánh giá Vietnamese IR nhiều miền là căn cứ phù hợp" in t and "[5]" not in t:
        rep(p, "paper Nguyen và Quan", "công trình của Nguyen và Quan [5]")
        print(f"P{i}: Added [5] in Vietnamese IR reference")

    # Chapter 3: Multi-level evaluation protocol
    if "Đánh giá truy xuất nên tách các mức văn bản, điều và khoản," in t and "[1]" not in t:
        rep(p, "khi có.", "khi có, tương tự phương pháp đánh giá phân tầng của LexGLUE [1] và T2-RAGBench [9].")
        print(f"P{i}: Added [1], [9] in evaluation protocol")

print(f"Total additional replacements: {replacements}")
doc.save(docx_path)
print("Saved updated DOCX successfully!")
