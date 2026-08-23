import pytest
from wordassistant.context.retrieve import build_context, remove_diacritics
from wordassistant.document.model import DocumentSection

def test_remove_diacritics():
    assert remove_diacritics("Trích dẫn tài liệu tham khảo") == "Trich dan tai lieu tham khao"
    assert remove_diacritics("Đề tài đồ án chuyên ngành") == "De tai do an chuyen nganh"

def test_retrieval_with_and_without_vietnamese_diacritics():
    ss = [
        DocumentSection('s1', '17. Quy định về trích dẫn tài liệu', 'Quy định trích dẫn nguồn gốc IEEE và danh mục tài liệu tham khảo.', 1),
        DocumentSection('s2', 'Chương 2: Phương pháp thực hiện', 'Phương pháp giải thuật và các mô hình học máy.', 1),
        DocumentSection('s3', 'Chương 3: Cài đặt và thử nghiệm', 'Môi trường thực nghiệm và đánh giá kết quả.', 1)
    ]
    
    # Query with diacritics
    b1 = build_context(ss, query="trích dẫn IEEE", max_tokens=1000)
    assert b1.sections[0].section_id == 's1'
    
    # Query without diacritics (e.g. typing on ASCII keyboard)
    b2 = build_context(ss, query="trich dan IEEE", max_tokens=1000)
    assert b2.sections[0].section_id == 's1'
    
    # Another without diacritics query
    b3 = build_context(ss, query="phuong phap thuc hien", max_tokens=1000)
    assert b3.sections[0].section_id == 's2'

def test_context_composition_includes_parent_breadcrumb():
    ss = [
        DocumentSection('p1', 'Chương 1: Tổng quan', 'Nội dung tổng quan về lĩnh vực.', level=1),
        DocumentSection('c1', '1.1 Cơ sở lý thuyết', 'Chi tiết về cơ sở lý thuyết và các định lý toán học.', level=2, parent_id='p1')
    ]
    b = build_context(ss, query="cơ sở lý thuyết", max_tokens=1000)
    assert b.sections[0].section_id == 'c1'
    # Check that context text contains structural hint or breadcrumb
    assert 'Chương 1: Tổng quan' in b.text or '1.1 Cơ sở lý thuyết' in b.text
