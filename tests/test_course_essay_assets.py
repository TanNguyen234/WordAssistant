from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build_course_essay_assets as assets  # noqa: E402


class CourseEssayAssetTests(unittest.TestCase):
    def test_wireframe_renderer_uses_only_monochrome_line_art(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "wireframe.png"
            assets.render_wireframe(
                {
                    "id": "demo",
                    "screen_title": "Danh sách rượu",
                    "route": "GET /wines",
                    "sections": [
                        {"title": "Bộ lọc", "fields": ["Tên rượu", "Quốc gia"]},
                        {"title": "Kết quả", "table_columns": ["Mã", "Tên", "Giá"], "rows": 2},
                        {"title": "Thao tác", "buttons": ["Áp dụng bộ lọc"]},
                    ],
                },
                output,
            )

            self.assertTrue(output.is_file())
            with Image.open(output).convert("RGB") as image:
                colors = image.getcolors(maxcolors=2_000_000)
                self.assertIsNotNone(colors)
                self.assertTrue(all(r == g == b for _count, (r, g, b) in colors))
                self.assertIn((255, 255, 255), {color for _count, color in colors})
                self.assertIn((0, 0, 0), {color for _count, color in colors})

    def test_inventory_requires_get_view_and_real_template(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            controller = root / "src/main/java/DemoController.java"
            template = root / "src/templates/demo.html"
            controller.parent.mkdir(parents=True)
            template.parent.mkdir(parents=True)
            controller.write_text(
                '@Controller\nclass DemoController {\n'
                '@GetMapping("/demo")\npublic String demo() { return "demo"; }\n'
                '}',
                encoding="utf-8",
            )
            template.write_text("<h1>Demo</h1>", encoding="utf-8")

            inventory = {
                "schema_version": 1,
                "template_root": "src/templates",
                "screens": [
                    {
                        "id": "demo",
                        "label": "Demo",
                        "roles": ["librarian"],
                        "modules": {"librarian": "Catalog"},
                        "route": "GET /demo",
                        "controller": "src/main/java/DemoController.java",
                        "mapping_tokens": ['@GetMapping("/demo")'],
                        "template": "demo.html",
                        "view_token": 'return "demo";',
                    }
                ],
                "wireframes": [],
            }
            self.assertEqual([], assets.validate_inventory(root, inventory))

            inventory["wireframes"] = [{
                "id": "demo_wireframe",
                "file": "demo.png",
                "screen_ids": ["demo"],
                "caption": "Demo wireframe",
                "screen_title": "Demo",
                "route": "GET /other",
                "sections": [],
            }]
            errors = assets.validate_inventory(root, inventory)
            self.assertTrue(any("wireframe routes do not match" in error for error in errors))
            inventory["wireframes"][0]["route"] = "GET /demo"
            self.assertEqual([], assets.validate_inventory(root, inventory))

            inventory["screens"][0]["route"] = "POST /demo"
            errors = assets.validate_inventory(root, inventory)
            self.assertTrue(any("GET" in error or "POST" in error for error in errors))

    def test_hierarchy_has_three_levels_and_only_get_screens(self) -> None:
        inventory = {
            "system_title": "Library",
            "screens": [
                {
                    "id": "demo",
                    "label": "Danh sách",
                    "roles": ["librarian"],
                    "modules": {"librarian": "Catalog"},
                    "routes": ["GET /demo"],
                }
            ]
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "hierarchy.png"
            assets._render_hierarchy(inventory, "librarian", output)
            puml = assets._hierarchy_puml(inventory, "librarian")

            self.assertTrue(output.is_file())
            self.assertIn("* Library — librarian", puml)
            self.assertIn("** Catalog", puml)
            self.assertIn("*** Danh sách", puml)
            self.assertNotIn("GET /demo", puml)
            self.assertNotIn("POST", puml)
            with Image.open(output).convert("RGB") as image:
                colors = image.getcolors(maxcolors=2_000_000)
                self.assertTrue(all(r == g == b for _count, (r, g, b) in colors))

    def test_build_assets_uses_roles_and_system_title_from_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            controller = root / "src/main/java/DemoController.java"
            template = root / "src/main/resources/templates/demo.html"
            controller.parent.mkdir(parents=True)
            template.parent.mkdir(parents=True)
            controller.write_text(
                '@Controller\nclass DemoController {\n'
                '@GetMapping("/demo")\npublic String demo() { return "demo"; }\n'
                '}',
                encoding="utf-8",
            )
            template.write_text("<h1>Demo</h1>", encoding="utf-8")
            inventory_path = root / "screen-inventory.json"
            inventory_path.write_text(json.dumps({
                "schema_version": 1,
                "system_title": "Library",
                "screens": [{
                    "id": "demo",
                    "label": "Browse books",
                    "roles": ["librarian"],
                    "modules": {"librarian": "Catalog"},
                    "routes": ["GET /demo"],
                    "controller": "src/main/java/DemoController.java",
                    "mapping_tokens": ['@GetMapping("/demo")'],
                    "template": "demo.html",
                    "view_token": 'return "demo";',
                }],
                "wireframes": [],
            }), encoding="utf-8")

            report = assets.build_assets(
                root,
                inventory_path,
                root / "wireframes",
                root / "diagrams",
                root / "build-report.json",
            )

            hierarchy_png = root / "diagrams" / "screen_hierarchy_librarian.png"
            hierarchy_puml = root / "diagrams" / "screen_hierarchy_librarian.puml"
            self.assertEqual("PASS", report["status"])
            self.assertTrue(hierarchy_png.is_file())
            self.assertIn("Library — librarian", hierarchy_puml.read_text(encoding="utf-8"))

    def test_render_only_mode_supports_manually_verified_non_spring_projects(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            inventory_path = root / "screen-inventory.json"
            inventory_path.write_text(json.dumps({
                "schema_version": 1,
                "system_title": "VietLex",
                "screens": [{
                    "id": "search",
                    "label": "Tìm văn bản",
                    "roles": ["reader"],
                    "modules": {"reader": "Tra cứu"},
                    "routes": ["GET /search"],
                    "controller": "app/api/legal_routes.py",
                    "mapping_tokens": ["@router.get('/search')"],
                    "template": "legal_search.html",
                    "view_token": "return templates.TemplateResponse",
                }],
                "wireframes": [{
                    "id": "search-form",
                    "file": "search.png",
                    "screen_ids": ["search"],
                    "caption": "Màn hình tra cứu",
                    "screen_title": "Tìm văn bản pháp luật",
                    "route": "GET /search",
                    "sections": [{"title": "Điều kiện tìm kiếm", "fields": ["Số hiệu", "Ngày"]}],
                }],
            }), encoding="utf-8")

            report = assets.render_assets(
                inventory_path,
                root / "wireframes",
                root / "diagrams",
                root / "render-report.json",
            )

            self.assertEqual("RENDERED", report["status"])
            self.assertEqual("NOT_RUN_MANUAL_REVIEW_REQUIRED", report["source_verification"])
            self.assertTrue((root / "wireframes" / "search.png").is_file())
            self.assertTrue((root / "diagrams" / "screen_hierarchy_reader.png").is_file())
            self.assertTrue((root / "diagrams" / "screen_hierarchy_reader.puml").is_file())
            hierarchy = report["hierarchy_sources"][0]
            self.assertEqual("Pillow", hierarchy["renderer"])
            self.assertTrue(hierarchy["editable_puml_source"].endswith("screen_hierarchy_reader.puml"))
            self.assertEqual(report, json.loads((root / "render-report.json").read_text(encoding="utf-8")))

            cli_report = root / "cli-render-report.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(Path(assets.__file__).resolve()),
                    "render",
                    "--inventory",
                    str(inventory_path),
                    "--wireframe-dir",
                    str(root / "wireframes"),
                    "--diagram-dir",
                    str(root / "diagrams"),
                    "--report",
                    str(cli_report),
                ],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(
                "NOT_RUN_MANUAL_REVIEW_REQUIRED",
                json.loads(completed.stdout)["source_verification"],
            )

    def test_initializer_copies_blank_starter_without_overwriting(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            template = root / "starter"
            template.mkdir()
            (template / "README.md").write_text("new project starter", encoding="utf-8")
            (template / "project.json").write_text(json.dumps({"name": ""}), encoding="utf-8")
            destination = root / "new-project"

            result = assets.initialize_project(template, destination, "Wine course essay")

            self.assertEqual(destination.resolve(), result.resolve())
            self.assertIn("Wine course essay", (destination / "project.json").read_text(encoding="utf-8"))
            with self.assertRaises(FileExistsError):
                assets.initialize_project(template, destination, "second run")
            self.assertIn("Wine course essay", (destination / "project.json").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
