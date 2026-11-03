"""Script to update Word fields, export PDF, and render all pages of StrongWine to PNGs."""

import os
import sys
import shutil
from pathlib import Path
import fitz
import win32com.client as win32

ROOT = Path(r"D:\Download\WordAssistant")
SOURCE_REPAIRED = ROOT / "artifacts/course-essay/strongwine-revision-20261027/output/StrongWine_20261103_repaired.docx"
DOCX_PATH = ROOT / "artifacts/course-essay/strongwine-revision-20261027/output/StrongWine_20261103_verified.docx"
PDF_PATH = ROOT / "artifacts/course-essay/strongwine-revision-20261027/output/StrongWine_20261103_verified.pdf"
RENDER_DIR = ROOT / "artifacts/course-essay/strongwine-revision-20261027/renders_150dpi"

# Copy repaired to verified
shutil.copy2(SOURCE_REPAIRED, DOCX_PATH)
RENDER_DIR.mkdir(parents=True, exist_ok=True)

print(f"Opening Word document: {DOCX_PATH}")
word = win32.Dispatch("Word.Application")
word.Visible = False
word.DisplayAlerts = 0

try:
    doc = word.Documents.Open(str(DOCX_PATH.resolve()))
    print("Updating fields...")
    doc.Fields.Update()
    for toc in doc.TablesOfContents:
        toc.Update()
    for tof in doc.TablesOfFigures:
        tof.Update()
    
    print(f"Exporting PDF: {PDF_PATH}")
    # 17 = wdExportFormatPDF
    doc.ExportAsFixedFormat(str(PDF_PATH.resolve()), 17, Item=0, CreateBookmarks=1)
    doc.Save()
    doc.Close(False)
finally:
    word.Quit()

print(f"Rendering PDF pages to PNG at 150 DPI in: {RENDER_DIR}")
pdf_doc = fitz.open(str(PDF_PATH))
total_pages = len(pdf_doc)
print(f"Total pages: {total_pages}")

# Render all pages
for idx in range(total_pages):
    page = pdf_doc[idx]
    pix = page.get_pixmap(dpi=150)
    out_file = RENDER_DIR / f"page_{idx+1:03d}.png"
    pix.save(str(out_file))
    if (idx + 1) % 25 == 0 or (idx + 1) == total_pages:
        print(f"  Rendered {idx+1}/{total_pages} pages")

print(f"ALL {total_pages} PAGES RENDERED SUCCESSFULLY!")
