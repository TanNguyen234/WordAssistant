from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

from lxml import etree

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import strongwine_course_essay as essay  # noqa: E402
import render_strongwine_qa_pages as qa_renderer  # noqa: E402


def paragraph(text: str, with_section: bool = False) -> etree._Element:
    node = etree.Element(essay.W + "p")
    if with_section:
        ppr = etree.SubElement(node, essay.W + "pPr")
        section = etree.SubElement(ppr, essay.W + "sectPr")
        margins = etree.SubElement(section, essay.W + "pgMar")
        margins.set(essay.W + "top", "1134")
        margins.set(essay.W + "bottom", "1134")
        margins.set(essay.W + "header", "720")
        margins.set(essay.W + "footer", "720")
    run = etree.SubElement(node, essay.W + "r")
    value = etree.SubElement(run, essay.W + "t")
    value.text = text
    return node


def synthetic_png(path: Path, color: tuple[int, int, int]) -> bytes:
    image = essay.Image.new("RGB", (320, 240), color)
    image.save(path, format="PNG")
    return path.read_bytes()


class StrongWineCourseEssayTests(unittest.TestCase):
    def test_misplaced_caption_sequence_field_is_repaired_and_audited(self) -> None:
        root = etree.Element(essay.W + "document", nsmap={"w": essay.NS["w"]})
        body = etree.SubElement(root, essay.W + "body")
        caption = etree.SubElement(body, essay.W + "p")
        ppr = etree.SubElement(caption, essay.W + "pPr")
        style = etree.SubElement(ppr, essay.W + "pStyle")
        style.set(essay.W + "val", "FigureCaptionList")
        bookmark_start = etree.SubElement(caption, essay.W + "bookmarkStart")
        bookmark_start.set(essay.W + "id", "375")
        bookmark_start.set(essay.W + "name", "_Toc243387850")

        def run_with(child_tag: str, value: str | None = None, field_type: str | None = None) -> etree._Element:
            run = etree.SubElement(caption, essay.W + "r")
            child = etree.SubElement(run, essay.W + child_tag)
            if value is not None:
                child.text = value
            if field_type is not None:
                child.set(essay.W + "fldCharType", field_type)
            return run

        text_run = run_with("t", "Hình 5.10: Giao diện chỉnh sửa hồ sơ Shipper (ảnh giao diện từ bộ tài liệu dự án)")
        run_with("fldChar", field_type="begin")
        run_with("instrText", " SEQ Hinh \\* ARABIC \\s 1")
        run_with("fldChar", field_type="separate")
        run_with("t", "10")
        bookmark_end = etree.SubElement(caption, essay.W + "bookmarkEnd")
        bookmark_end.set(essay.W + "id", "375")
        run_with("fldChar", field_type="end")

        self.assertEqual(essay.literal_paragraph_text(caption),
                         "Hình 5.10: Giao diện chỉnh sửa hồ sơ Shipper (ảnh giao diện từ bộ tài liệu dự án)")
        self.assertEqual(essay.audit_sequence_caption_fields([caption])["status"], "FAIL")
        result = essay.repair_misplaced_shipper_caption_sequence(root)
        self.assertEqual(result["status"], "repaired")
        self.assertEqual(essay.authored_paragraph_text(caption), "Hình 5.10: Giao diện chỉnh sửa hồ sơ Shipper")
        self.assertEqual("".join(caption.xpath(".//w:t/text()", namespaces=essay.NS)),
                         "Hình 5.10: Giao diện chỉnh sửa hồ sơ Shipper")
        self.assertEqual(essay.audit_sequence_caption_fields([caption])["status"], "PASS")
        self.assertEqual(essay.repair_misplaced_shipper_caption_sequence(root)["status"], "already_correct")

    def test_enum_extractors_read_exact_literals(self) -> None:
        java = """public enum ShipmentStatus {
            PENDING_ASSIGNMENT,
            ASSIGNED,
            FAILED
        }"""
        puml = "enum ShipmentStatus {\n PENDING_ASSIGNMENT\n ASSIGNED\n FAILED\n}"
        self.assertEqual(essay.parse_java_enum(java, "ShipmentStatus"), {"PENDING_ASSIGNMENT", "ASSIGNED", "FAILED"})
        self.assertEqual(essay.parse_puml_enum(puml, "ShipmentStatus"), {"PENDING_ASSIGNMENT", "ASSIGNED", "FAILED"})
        self.assertEqual(
            essay.parse_puml_enum("ShipmentStatus: PENDING_ASSIGNMENT, ASSIGNED, FAILED", "ShipmentStatus"),
            {"PENDING_ASSIGNMENT", "ASSIGNED", "FAILED"},
        )

    def test_cover_fix_centers_both_blocks_and_limits_page_borders(self) -> None:
        root = etree.Element(essay.W + "document", nsmap={"w": essay.NS["w"]})
        body = etree.SubElement(root, essay.W + "body")
        body.append(paragraph(essay.SCHOOL))
        body.append(paragraph("Course title"))
        body.append(paragraph("TP. Hồ Chí Minh, tháng 10 năm 2026", with_section=True))
        body.append(paragraph(essay.SCHOOL))
        body.append(paragraph("Inner cover title"))
        body.append(paragraph("TP. Hồ Chí Minh, tháng 10 năm 2026"))
        body.append(paragraph("Acknowledgments", with_section=True))
        final_section = etree.SubElement(body, essay.W + "sectPr")
        final_margins = etree.SubElement(final_section, essay.W + "pgMar")
        final_margins.set(essay.W + "top", "1134")
        final_margins.set(essay.W + "bottom", "1134")
        final_margins.set(essay.W + "header", "720")
        final_margins.set(essay.W + "footer", "720")

        fixed, result = essay.fix_cover_xml(essay.xml_bytes(root))
        fixed_root = etree.fromstring(fixed)
        fixed_body = fixed_root.find("w:body", essay.NS)
        paragraphs = fixed_body.xpath("./w:p", namespaces=essay.NS)
        sections = fixed_body.xpath(".//w:sectPr", namespaces=essay.NS)

        self.assertEqual(result["centered_paragraph_count"], 6)
        self.assertTrue(all(p.find("w:pPr/w:jc", essay.NS).get(essay.W + "val") == "center" for p in paragraphs[:6]))
        self.assertEqual(len(sections), 4)
        self.assertEqual([s.find("w:pgBorders", essay.NS).get(essay.W + "display") for s in sections[:2]], ["firstPage", "allPages"])
        self.assertTrue(all(s.find("w:vAlign", essay.NS).get(essay.W + "val") == "center" for s in sections[:2]))
        self.assertIsNotNone(sections[1].find("w:titlePg", essay.NS))
        self.assertIsNone(sections[2].find("w:pgBorders", essay.NS))
        self.assertIsNone(sections[3].find("w:pgBorders", essay.NS))
        self.assertEqual(sections[0].find("w:pgBorders/w:top", essay.NS).get(essay.W + "space"), "4")
        self.assertEqual(sections[0].find("w:pgBorders", essay.NS).get(essay.W + "offsetFrom"), "text")
        self.assertEqual([s.find("w:pgMar", essay.NS).get(essay.W + "header") for s in sections], ["900", "900", "720", "720"])
        self.assertEqual([s.find("w:pgMar", essay.NS).get(essay.W + "footer") for s in sections], ["900", "900", "720", "720"])

    def test_cover_range_fails_closed_when_cover_is_ambiguous(self) -> None:
        with self.assertRaises(ValueError):
            essay.cover_ranges([paragraph(essay.SCHOOL)])

    def test_admin_illustrations_move_to_chapter_five_in_workflow_order(self) -> None:
        root = etree.Element(essay.W + "document", nsmap={"w": essay.NS["w"]})
        body = etree.SubElement(root, essay.W + "body")
        entries = [
            "CHƯƠNG 4: LUỒNG NGHIỆP VỤ KHÁCH HÀNG",
            "Customer order detail",
            "Dashboard wireframe intro",
            "",
            "Hình 5.3: Wireframe Bảng điều khiển quản trị Dashboard KPI (Grayscale Web Mockup)",
            "Customer review heading",
            "Customer review details",
            "",
            "Hình 5.4: Wireframe Quản lý danh mục và sản phẩm rượu vang (Grayscale Web Mockup)",
            "Wine form intro",
            "",
            "Hình 5.5: Wireframe Thêm mới và chỉnh sửa thông tin rượu (Grayscale Web Mockup)",
            "Admin sitemap intro",
            "",
            "Hình 5.0: Sơ đồ phân rã màn hình phân hệ Quản trị và Thủ kho (Admin & Warehouse Screen Hierarchy Tree)",
            "Admin use case intro",
            "",
            "Hình 5.0b: Sơ đồ Use Case chi tiết phân hệ Quản trị và Thủ kho",
            "Admin overview details",
            "CHƯƠNG 5: LUỒNG NGHIỆP VỤ QUẢN TRỊ VÀ KHO",
            "Dashboard và quản lý danh mục, sản phẩm",
            "Admin content",
            "Hình 5.1: Sơ đồ hoạt động (Activity Diagram) Quản trị viên thêm rượu và upload ảnh",
            "Hình 5.2: Sơ đồ tuần tự (Sequence Diagram) Admin thêm rượu và lưu ảnh qua FileStorageService",
        ]
        for value in entries:
            body.append(paragraph(value))

        result = essay.reorder_admin_illustrations(root)
        essay.apply_verified_text_edits(root, {
            "Hình 5.2: Sơ đồ tuần tự (Sequence Diagram) Admin thêm rượu và lưu ảnh qua FileStorageService":
            "Hình 5.2: Sơ đồ tuần tự Admin tạo rượu qua form MVC và FileStorageService",
        })
        paragraphs = body.xpath("./w:p", namespaces=essay.NS)
        order = essay.audit_admin_figure_order(paragraphs)
        self.assertEqual(len(result["moved_groups"]), 3)
        self.assertTrue(order["ordered"], order)
        texts = ["".join(p.xpath(".//w:t/text()", namespaces=essay.NS)).strip() for p in paragraphs]
        self.assertLess(texts.index("Customer review heading"), texts.index("CHƯƠNG 5: LUỒNG NGHIỆP VỤ QUẢN TRỊ VÀ KHO"))

    def test_verified_paragraph_replacement_preserves_xml_and_is_idempotent(self) -> None:
        root = etree.Element(essay.W + "document", nsmap={"w": essay.NS["w"]})
        body = etree.SubElement(root, essay.W + "body")
        body.append(paragraph("Old route description"))
        edits = essay.apply_verified_text_edits(root, {"Old route description": "Verified route description"})
        self.assertEqual(len(edits), 1)
        self.assertEqual("".join(root.xpath(".//w:t/text()", namespaces=essay.NS)), "Verified route description")

        repeated = essay.apply_verified_text_edits(root, {"Old route description": "Verified route description"})
        self.assertEqual(repeated, [])

    def test_runtime_and_customer_tree_text_claims_are_corrected_idempotently(self) -> None:
        root = etree.Element(essay.W + "document", nsmap={"w": essay.NS["w"]})
        body = etree.SubElement(root, essay.W + "body")
        declaration_anchor = next(
            old for old in essay.VERIFIED_TEXT_EDITS if old.startswith("Thông tin về Trường Đại học")
        )
        tree_anchor = next(
            old for old in essay.VERIFIED_TEXT_EDITS if old.startswith("Sơ đồ cây phân cấp màn hình phân hệ Khách hàng")
        )
        tree_alias = essay.VERIFIED_TEXT_EDIT_ALIASES[tree_anchor][0]
        body.append(paragraph(declaration_anchor))
        body.append(paragraph(tree_alias))

        replacements = {anchor: essay.VERIFIED_TEXT_EDITS[anchor] for anchor in (declaration_anchor, tree_anchor)}
        edits = essay.apply_verified_text_edits(root, replacements)

        self.assertEqual(2, len(edits))
        revised = ["".join(p.xpath(".//w:t/text()", namespaces=essay.NS)) for p in body.xpath("./w:p", namespaces=essay.NS)]
        self.assertIn("chưa được chụp lại từ runtime trong lượt hiệu đính này", revised[0])
        self.assertIn("quên mật khẩu và đặt lại mật khẩu", revised[1])
        self.assertIn("xác nhận đơn hàng", revised[1])
        self.assertEqual(
            [], essay.apply_verified_text_edits(root, replacements)
        )

    def test_caption_edit_preserves_table_of_figures_page_field(self) -> None:
        root = etree.Element(essay.W + "document", nsmap={"w": essay.NS["w"]})
        body = etree.SubElement(root, essay.W + "body")
        caption = etree.Element(essay.W + "p")
        hyperlink = etree.SubElement(caption, essay.W + "hyperlink")
        run = etree.SubElement(hyperlink, essay.W + "r")
        text = etree.SubElement(run, essay.W + "t")
        text.text = "Old wireframe caption"
        for kind, value in [("fldChar", None), ("instrText", " PAGEREF _Toc1 \\h "),
                            ("fldChar", None), ("t", "107"), ("fldChar", None)]:
            field_run = etree.SubElement(hyperlink, essay.W + "r")
            field_node = etree.SubElement(field_run, essay.W + kind)
            if kind == "fldChar":
                field_node.set(essay.W + "fldCharType", {1: "begin", 3: "separate", 5: "end"}[hyperlink.index(field_run)])
            elif value is not None:
                field_node.text = value
        body.append(caption)

        result = essay.apply_caption_text_edits(root, {"Old wireframe caption": "Corrected wireframe caption"})

        self.assertEqual(result[0]["paragraphs_updated"], 1)
        self.assertEqual(essay.authored_paragraph_text(caption), "Corrected wireframe caption")
        self.assertEqual(caption.xpath(".//w:t/text()", namespaces=essay.NS)[-1], "107")
        self.assertEqual(len(caption.xpath(".//w:hyperlink", namespaces=essay.NS)), 1)

    def test_known_misleading_figure_removal_checks_caption_relationship_and_source_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = Path(temporary_directory)
            source_path = project_root / "docs" / "source.png"
            source_path.parent.mkdir(parents=True)
            source_bytes = synthetic_png(source_path, (21, 45, 99))
            caption = "Known wrong caption"
            root = etree.Element(essay.W + "document", nsmap={"w": essay.NS["w"], "r": essay.NS["r"]})
            body = etree.SubElement(root, essay.W + "body")
            image_paragraph = etree.SubElement(body, essay.W + "p")
            run = etree.SubElement(image_paragraph, essay.W + "r")
            drawing = etree.SubElement(run, essay.W + "drawing")
            inline = etree.SubElement(drawing, "{" + essay.NS["wp"] + "}inline")
            graphic = etree.SubElement(inline, "{" + essay.NS["a"] + "}graphic")
            graphic_data = etree.SubElement(graphic, "{" + essay.NS["a"] + "}graphicData")
            blip = etree.SubElement(graphic_data, "{" + essay.NS["a"] + "}blip")
            blip.set(essay.R + "embed", "rId1")
            body.append(paragraph(caption))
            rules = {caption: {"source": "docs/source.png", "expected_sha256": essay.sha256(source_bytes), "reason": "test"}}

            with patch.dict(essay.MISLEADING_FIGURE_RULES, rules, clear=True):
                result = essay.remove_known_misleading_figures(
                    root, {"rId1": "media/current.png"}, {"word/media/current.png": source_bytes}, project_root
                )

            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["caption"], caption)
            self.assertEqual(len(body), 0)

            # Same caption with changed bytes is a hard stop and leaves the document intact.
            root = etree.Element(essay.W + "document", nsmap={"w": essay.NS["w"], "r": essay.NS["r"]})
            body = etree.SubElement(root, essay.W + "body")
            image_paragraph = etree.SubElement(body, essay.W + "p")
            run = etree.SubElement(image_paragraph, essay.W + "r")
            drawing = etree.SubElement(run, essay.W + "drawing")
            inline = etree.SubElement(drawing, "{" + essay.NS["wp"] + "}inline")
            graphic = etree.SubElement(inline, "{" + essay.NS["a"] + "}graphic")
            graphic_data = etree.SubElement(graphic, "{" + essay.NS["a"] + "}graphicData")
            blip = etree.SubElement(graphic_data, "{" + essay.NS["a"] + "}blip")
            blip.set(essay.R + "embed", "rId1")
            body.append(paragraph(caption))
            with patch.dict(essay.MISLEADING_FIGURE_RULES, rules, clear=True):
                with self.assertRaisesRegex(ValueError, "does not match the reviewed source asset"):
                    essay.remove_known_misleading_figures(
                        root, {"rId1": "media/current.png"}, {"word/media/current.png": b"changed"}, project_root
                    )
            self.assertEqual(len(body), 2)

    def test_restore_authored_media_replaces_word_recompressed_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            diagram_root = root / "diagrams"
            project_root = root / "project"
            diagram_root.mkdir()
            project_root.mkdir()
            docx_path = root / "reviewed.docx"
            media_sources = {}
            document_root = etree.Element(essay.W + "document", nsmap={"w": essay.NS["w"], "r": essay.NS["r"]})
            body = etree.SubElement(document_root, essay.W + "body")
            rels_root = etree.Element("{http://schemas.openxmlformats.org/package/2006/relationships}Relationships")
            package_parts = {}
            semantic_parts = {}
            media_index = 0

            authored_figures = [
                (caption, diagram_root / f"{diagram_name}.png", (30 + i, 80, 120), "diagram")
                for i, (diagram_name, caption) in enumerate(essay.DIAGRAM_CAPTIONS.items())
            ]
            authored_figures.extend(
                (caption, project_root / Path(relative_path), (140, 50 + i, 60), "project")
                for i, (caption, relative_path) in enumerate(essay.PROJECT_MEDIA_CAPTIONS.items())
            )

            for caption, source, color, _kind in authored_figures:
                source.parent.mkdir(parents=True, exist_ok=True)
                expected = synthetic_png(source, color)
                part = f"word/media/renamed-by-word-{media_index}.png"
                rel_id = f"rId{media_index + 1}"
                relationship = etree.SubElement(
                    rels_root,
                    "{http://schemas.openxmlformats.org/package/2006/relationships}Relationship",
                )
                relationship.set("Id", rel_id)
                relationship.set("Type", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image")
                relationship.set("Target", f"media/renamed-by-word-{media_index}.png")

                image_paragraph = etree.SubElement(body, essay.W + "p")
                run = etree.SubElement(image_paragraph, essay.W + "r")
                drawing = etree.SubElement(run, essay.W + "drawing")
                inline = etree.SubElement(drawing, "{" + essay.NS["wp"] + "}inline")
                extent = etree.SubElement(inline, "{" + essay.NS["wp"] + "}extent")
                extent.set("cx", "4000000")
                extent.set("cy", "3000000")
                graphic = etree.SubElement(inline, "{" + essay.NS["a"] + "}graphic")
                graphic_data = etree.SubElement(graphic, "{" + essay.NS["a"] + "}graphicData")
                blip = etree.SubElement(graphic_data, "{" + essay.NS["a"] + "}blip")
                blip.set(essay.R + "embed", rel_id)
                body.append(paragraph(caption))

                package_parts[part] = b"Word-recompressed-or-renamed-by-native-save"
                media_sources[part] = expected
                semantic_parts[caption] = part
                media_index += 1

            wrong_legacy_part = "word/media/image32.png"
            wrong_legacy_bytes = b"must-not-be-used-as-a-semantic-map"
            package_parts[wrong_legacy_part] = wrong_legacy_bytes
            package_parts["word/document.xml"] = essay.xml_bytes(document_root)
            package_parts["word/_rels/document.xml.rels"] = etree.tostring(rels_root, xml_declaration=True, encoding="UTF-8")

            with ZipFile(docx_path, "w") as archive:
                for part, content in package_parts.items():
                    archive.writestr(part, content)

            result = essay.restore_authored_media(docx_path, project_root, diagram_root)

            with ZipFile(docx_path) as archive:
                for part, expected in media_sources.items():
                    self.assertEqual(archive.read(part), expected)
                self.assertEqual(archive.read(wrong_legacy_part), wrong_legacy_bytes)
                restored_parts = {item["part"] for item in result["restored_media"]}
                self.assertEqual(restored_parts, set(semantic_parts.values()))
            self.assertEqual(len(result["restored_media"]), len(media_sources))
            self.assertFalse(docx_path.with_name("reviewed.media-restore.tmp.docx").exists())

    def test_cover_frame_audit_requires_visible_inset_not_page_edge(self) -> None:
        from PIL import ImageDraw

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            correct = root / "inset-frame.png"
            image = essay.Image.new("RGB", (1072, 1516), "white")
            draw = ImageDraw.Draw(image)
            draw.rectangle((153, 102, 970, 1414), outline="black", width=3)
            image.save(correct)
            evidence = qa_renderer.page_border_evidence(correct)
            self.assertTrue(evidence["present"], evidence)
            self.assertEqual(evidence["inset_mm"]["left"], 30.0)

            near_edge = root / "near-edge-frame.png"
            image = essay.Image.new("RGB", (1072, 1516), "white")
            ImageDraw.Draw(image).rectangle((7, 7, 1063, 1507), outline="black", width=3)
            image.save(near_edge)
            self.assertFalse(qa_renderer.page_border_evidence(near_edge)["present"])

    def test_stray_number_before_home_wireframe_is_removed_without_removing_image(self) -> None:
        root = etree.Element(essay.W + "document", nsmap={"w": essay.NS["w"], "r": essay.NS["r"]})
        body = etree.SubElement(root, essay.W + "body")
        image_paragraph = etree.SubElement(body, essay.W + "p")
        ppr = etree.SubElement(image_paragraph, essay.W + "pPr")
        num_pr = etree.SubElement(ppr, essay.W + "numPr")
        etree.SubElement(num_pr, essay.W + "ilvl").set(essay.W + "val", "1")
        etree.SubElement(num_pr, essay.W + "numId").set(essay.W + "val", "1")
        run = etree.SubElement(image_paragraph, essay.W + "r")
        drawing = etree.SubElement(run, essay.W + "drawing")
        inline = etree.SubElement(drawing, "{" + essay.NS["wp"] + "}inline")
        graphic = etree.SubElement(inline, "{" + essay.NS["a"] + "}graphic")
        graphic_data = etree.SubElement(graphic, "{" + essay.NS["a"] + "}graphicData")
        blip = etree.SubElement(graphic_data, "{" + essay.NS["a"] + "}blip")
        blip.set(essay.R + "embed", "rId1")
        body.append(paragraph(
            "Hình 4.1: Wireframe Trang chủ sàn thương mại điện tử StrongWine (Grayscale Web Mockup)"
        ))

        result = essay.remove_stray_number_before_home_wireframe(root, {"rId1": "media/home.png"})

        self.assertEqual(result["status"], "removed")
        self.assertIsNone(image_paragraph.find("w:pPr/w:numPr", essay.NS))
        self.assertEqual(len(image_paragraph.xpath(".//w:drawing", namespaces=essay.NS)), 1)
        self.assertEqual(essay.remove_stray_number_before_home_wireframe(root, {"rId1": "media/home.png"})["status"],
                         "already_correct")

    def test_contact_sheets_cover_each_physical_pdf_page(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            pdf_path = root / "small.pdf"
            document = qa_renderer.fitz.open()
            document.new_page(width=595, height=842)
            document.new_page(width=595, height=842)
            document.new_page(width=595, height=842)
            document.save(pdf_path)
            document.close()
            with qa_renderer.fitz.open(pdf_path) as rendered:
                sheets = qa_renderer.render_contact_sheets(rendered, root / "sheets", pages_per_sheet=2, scale=0.2)
            self.assertEqual([item["pages"] for item in sheets], [[1, 2], [3]])
            self.assertTrue(all(Path(item["image"]).is_file() for item in sheets))


if __name__ == "__main__":
    unittest.main()
