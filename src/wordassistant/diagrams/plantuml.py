from __future__ import annotations

import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from typing import Any


def find_java_executable() -> str | None:
    java_bin = shutil.which("java")
    if java_bin:
        return java_bin
    java_home = os.environ.get("JAVA_HOME")
    if java_home:
        candidate = Path(java_home) / "bin" / ("java.exe" if os.name == "nt" else "java")
        if candidate.is_file():
            return str(candidate)
    return None


def find_plantuml_jar() -> Path | None:
    env_jar = os.environ.get("PLANTUML_JAR")
    if env_jar and Path(env_jar).is_file():
        return Path(env_jar).resolve()

    # Relative to this file inside repository
    repo_root = Path(__file__).resolve().parents[3]
    candidates = [
        repo_root / "tools" / "plantuml" / "plantuml.jar",
        repo_root / "src" / "wordassistant" / "data" / "tools" / "plantuml.jar",
        Path.cwd() / "tools" / "plantuml" / "plantuml.jar",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    return None


def doctor() -> dict[str, Any]:
    java_exe = find_java_executable()
    jar_path = find_plantuml_jar()

    java_version = None
    if java_exe:
        try:
            completed = subprocess.run(
                [java_exe, "-version"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
            )
            # Java prints version to stderr
            output = completed.stderr.strip() or completed.stdout.strip()
            first_line = output.splitlines()[0] if output else "unknown"
            java_version = first_line
        except Exception as exc:
            java_version = f"error: {exc}"

    plantuml_version = None
    if java_exe and jar_path:
        try:
            completed = subprocess.run(
                [java_exe, "-Djava.awt.headless=true", "-jar", str(jar_path), "-version"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=15,
            )
            output = completed.stdout.strip()
            first_line = output.splitlines()[0] if output else "unknown"
            plantuml_version = first_line
        except Exception as exc:
            plantuml_version = f"error: {exc}"

    operational = bool(java_exe and jar_path and plantuml_version and not plantuml_version.startswith("error:"))
    reason = None
    if not java_exe:
        reason = "Java runtime executable was not found on PATH or JAVA_HOME"
    elif not jar_path:
        reason = "plantuml.jar engine was not found in tools/plantuml or PLANTUML_JAR"
    elif not operational:
        reason = f"PlantUML execution failed: {plantuml_version}"

    return {
        "status": "SUCCESS" if operational else "UNAVAILABLE",
        "operational": operational,
        "java_executable": java_exe,
        "java_version": java_version,
        "plantuml_jar": str(jar_path) if jar_path else None,
        "plantuml_version": plantuml_version,
        "reason": reason,
    }


class PlantUMLRenderer:
    def __init__(
        self,
        *,
        jar_path: Path | None = None,
        java_executable: str | None = None,
    ) -> None:
        self.jar_path = jar_path or find_plantuml_jar()
        self.java_executable = java_executable or find_java_executable()

    def health(self) -> dict[str, Any]:
        return doctor()

    def render(
        self,
        source: str | Path,
        *,
        output_path: Path | str | None = None,
        format: str = "png",
        timeout_seconds: int = 60,
    ) -> dict[str, Any]:
        if not self.java_executable:
            raise RuntimeError("Java executable was not found. Please install Java to use PlantUML.")
        if not self.jar_path or not self.jar_path.is_file():
            raise RuntimeError(
                f"PlantUML jar not found at {self.jar_path}. Check tools/plantuml/plantuml.jar."
            )

        format = format.lower().strip()
        supported_formats = {"png", "svg", "eps", "txt", "utxt", "pdf"}
        if format not in supported_formats:
            raise ValueError(f"Unsupported format '{format}'. Supported formats: {sorted(supported_formats)}")

        # PlantUML CLI flag: -tpng, -tsvg, etc.
        flag = f"-t{format}"

        with tempfile.TemporaryDirectory(prefix="wordassistant-plantuml-") as tmp_dir:
            tmp_path = Path(tmp_dir)

            if isinstance(source, Path) or (isinstance(source, str) and (Path(source).is_file() or "\n" not in source)):
                src_file = Path(source)
                if not src_file.is_file():
                    # Not a file, interpret as string content
                    puml_file = tmp_path / "diagram.puml"
                    puml_file.write_text(str(source), encoding="utf-8")
                else:
                    puml_file = src_file
            else:
                puml_file = tmp_path / "diagram.puml"
                puml_file.write_text(str(source), encoding="utf-8")

            out_dir = tmp_path / "out"
            out_dir.mkdir(exist_ok=True)

            cmd = [
                self.java_executable,
                "-Djava.awt.headless=true",
                "-jar",
                str(self.jar_path),
                "-charset",
                "UTF-8",
                flag,
                "-o",
                str(out_dir),
                str(puml_file),
            ]

            completed = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout_seconds,
            )

            if completed.returncode != 0:
                error_msg = completed.stderr.strip() or completed.stdout.strip() or f"Process exited with {completed.returncode}"
                raise RuntimeError(f"PlantUML compilation failed: {error_msg}")

            # Locate the generated file (PlantUML uses .atxt/.utxt for text formats)
            ext_map = {
                "png": [".png"],
                "svg": [".svg"],
                "eps": [".eps"],
                "pdf": [".pdf"],
                "txt": [".atxt", ".txt", ".utxt"],
                "utxt": [".utxt", ".txt"],
            }
            possible_exts = ext_map.get(format, [f".{format}"])
            generated_files = []
            for ext in possible_exts:
                generated_files.extend(out_dir.glob(f"*{ext}"))

            if not generated_files:
                stdout_err = completed.stdout.strip() + "\n" + completed.stderr.strip()
                raise RuntimeError(
                    f"PlantUML did not generate an output file in format {format}. Output: {stdout_err.strip()}"
                )

            gen_file = generated_files[0]
            if gen_file.stat().st_size == 0:
                raise RuntimeError("PlantUML generated an empty output file.")

            final_output = Path(output_path).resolve() if output_path else Path(puml_file.stem + f".{format}").resolve()
            final_output.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(gen_file, final_output)

            width, height = None, None
            if format == "png":
                try:
                    from PIL import Image
                    with Image.open(final_output) as img:
                        width, height = img.size
                except Exception:
                    pass

            return {
                "status": "SUCCESS",
                "format": format,
                "output_path": str(final_output),
                "size_bytes": final_output.stat().st_size,
                "width": width,
                "height": height,
            }


def render_plantuml(
    source: str | Path,
    *,
    output_path: Path | str | None = None,
    format: str = "png",
    timeout_seconds: int = 60,
) -> dict[str, Any]:
    renderer = PlantUMLRenderer()
    return renderer.render(
        source,
        output_path=output_path,
        format=format,
        timeout_seconds=timeout_seconds,
    )
