from docx import Document

from wordassistant.document.scaffold import scaffold_document
from wordassistant.operations.page_numbers import inspect_page_numbers
from wordassistant.profiles.loader import resolve_profile


def test_hcmunre_report_front_matter_and_introduction_pagination(tmp_path):
    output = tmp_path / "report.docx"
    scaffold_document(
        output,
        resolve_profile("hcmunre_dacn_2026_2027"),
        "report",
        title="HỆ THỐNG KIỂM THỬ",
        student="NGUYỄN VĂN A - 2351010001",
        supervisor="TS. NGUYỄN VĂN B",
    )

    sections = inspect_page_numbers(output)
    assert any(item["format"] == "lowerRoman" and item["start"] == 1 for item in sections)
    introduction = next(item for item in sections if item["first_heading"] == "MỞ ĐẦU")
    assert introduction["format"] == "decimal"
    assert introduction["start"] == 1
    assert introduction["fields"] == ["PAGE"]
    document = Document(output)
    assert all(section.orientation is not None for section in document.sections)
    front_titles = [
        "LỜI CẢM ƠN",
        "LỜI CAM ĐOAN",
        "NHẬN XÉT CỦA GIẢNG VIÊN HƯỚNG DẪN",
        "NHẬN XÉT CỦA NGƯỜI PHẢN BIỆN",
        "LỊCH LÀM VIỆC",
        "TÓM TẮT",
        "MỤC LỤC",
        "DANH MỤC SƠ ĐỒ, HÌNH",
        "DANH MỤC BẢNG",
        "KÍ HIỆU CÁC CỤM TỪ VIẾT TẮT",
    ]
    headings = {
        paragraph.text: paragraph
        for paragraph in document.paragraphs
        if paragraph.text in front_titles
    }
    assert headings[front_titles[0]].paragraph_format.page_break_before is None
    assert all(
        headings[title].paragraph_format.page_break_before is True
        for title in front_titles[1:]
    )
