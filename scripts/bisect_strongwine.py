import copy
import os
import shutil
import tempfile
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
import win32com.client as win32

f_bad = Path(r"artifacts/course-essay/strongwine-revision-20261027/output/StrongWine_20261102_academic_standardized.docx").resolve()
f_good = Path(r"artifacts/course-essay/strongwine-revision-20261027/StrongWine_20261027_pagebreak_final.docx").resolve()

print("Loading documents...")
with zipfile.ZipFile(f_bad) as z:
    xml_bad = z.read("word/document.xml")
with zipfile.ZipFile(f_good) as z:
    xml_good = z.read("word/document.xml")

root_bad = ET.fromstring(xml_bad)
root_good = ET.fromstring(xml_good)

NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
body_bad = root_bad.find("w:body", NS)
body_good = root_good.find("w:body", NS)

# The sectPr is always the last element of body in Word openxml
sectPr_good = body_good[-1]
sectPr_bad = body_bad[-1]

word = win32.Dispatch("Word.Application")
word.Visible = False
word.DisplayAlerts = 0

def test_children(children, label="test"):
    # Construct a new document.xml with root_good
    new_root = copy.deepcopy(root_good)
    new_body = new_root.find("w:body", NS)
    new_body.clear()
    for c in children:
        new_body.append(c)
    # Ensure sectPr is at end
    new_body.append(sectPr_good)
    
    xml_bytes = ET.tostring(new_root, encoding="utf-8", xml_declaration=True)
    
    tmp_dir = Path(tempfile.mkdtemp())
    tmp_docx = tmp_dir / f"{label}.docx"
    
    # Copy good docx and replace word/document.xml
    with zipfile.ZipFile(f_good, "r") as zin:
        with zipfile.ZipFile(tmp_docx, "w") as zout:
            for item in zin.infolist():
                if item.filename == "word/document.xml":
                    zout.writestr(item, xml_bytes)
                else:
                    zout.writestr(item, zin.read(item.filename))
                    
    ok = False
    try:
        doc = word.Documents.Open(str(tmp_docx))
        ok = True
        doc.Close(False)
    except Exception as e:
        ok = False
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
    return ok

print("Testing baseline good...")
print("Good baseline ok:", test_children(list(body_good)[:-1], "baseline_good"))

print("Testing elements 0..668 of bad...")
bad_children = list(body_bad)[:-1]
print("0..668 bad ok:", test_children(bad_children[:669], "bad_0_668"))

# Binary search within bad_children[:669]
# Find smallest range [low, high] that causes corruption when tested alone
low = 0
high = 668

print(f"Starting binary search in range [{low}, {high}]...")
while low < high:
    mid = (low + high) // 2
    # Test if bad_children[low:mid+1] has corruption
    is_ok = test_children(bad_children[low:mid+1], f"test_{low}_{mid}")
    print(f"Testing slice [{low}..{mid}] (size {mid - low + 1}): {'PASS' if is_ok else 'FAIL'}")
    if not is_ok:
        # Corruption is in [low..mid]
        high = mid
    else:
        # Corruption must be in [mid+1..high]
        print(f"Corruption not in [{low}..{mid}], moving to [{mid+1}..{high}]")
        low = mid + 1

print(f"EXACT CORRUPT INDEX: {low}")
# Inspect element
bad_elem = bad_children[low]
print(f"Tag: {bad_elem.tag}")
print(f"XML: {ET.tostring(bad_elem, encoding='utf-8')[:500]}")

word.Quit()
