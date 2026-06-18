import os
import sys

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

def check_academic_format(docx_path):
    if not os.path.exists(docx_path):
        print(f"Error: File '{docx_path}' does not exist.")
        return False
        
    doc = Document(docx_path)
    issues = []
    
    print(f"=== Auditing Document: {os.path.basename(docx_path)} ===")
    
    # 1. Check Page setup (A4 & Margins)
    for idx, section in enumerate(doc.sections):
        # A4 Size: 8.27 x 11.69 inches (~21.0 x 29.7 cm)
        width_in = round(section.page_width.inches, 2)
        height_in = round(section.page_height.inches, 2)
        
        # Standard: Top=2cm (0.79"), Bottom=2cm (0.79"), Left=3cm (1.18"), Right=2cm (0.79")
        top_in = round(section.top_margin.inches, 2)
        bottom_in = round(section.bottom_margin.inches, 2)
        left_in = round(section.left_margin.inches, 2)
        right_in = round(section.right_margin.inches, 2)
        
        if width_in != 8.27 or height_in != 11.69:
            issues.append(f"Section {idx}: Page size is not standard A4 ({width_in}x{height_in} in, expected 8.27x11.69 in)")
            
        if top_in != 0.79:
            issues.append(f"Section {idx}: Top margin is {top_in} in (expected 0.79 in / 2.0 cm)")
        if bottom_in != 0.79:
            issues.append(f"Section {idx}: Bottom margin is {bottom_in} in (expected 0.79 in / 2.0 cm)")
        if left_in != 1.18:
            issues.append(f"Section {idx}: Left margin is {left_in} in (expected 1.18 in / 3.0 cm)")
        if right_in != 0.79:
            issues.append(f"Section {idx}: Right margin is {right_in} in (expected 0.79 in / 2.0 cm)")

    # 2. Check Paragraph formatting
    heading_styles = [f'Heading {i}' for i in range(1, 10)]
    checked_paragraphs = 0
    font_issues = 0
    spacing_issues = 0
    alignment_issues = 0
    
    for idx, para in enumerate(doc.paragraphs):
        text = para.text.strip()
        if not text:
            continue
            
        checked_paragraphs += 1
        style_name = para.style.name
        
        # Extract font name and size from runs
        font_names = set()
        font_sizes = set()
        
        for run in para.runs:
            if run.font.name:
                font_names.add(run.font.name)
            if run.font.size:
                font_sizes.add(run.font.size.pt)
                
        # If not specified in runs, check style font
        if not font_names and para.style.font.name:
            font_names.add(para.style.font.name)
        if not font_sizes and para.style.font.size:
            font_sizes.add(para.style.font.size.pt)
            
        # Default fallback to Times New Roman if completely empty
        font_name = list(font_names)[0] if font_names else "Unknown (Inherited)"
        font_size = list(font_sizes)[0] if font_sizes else 13.0 # Standard body size
        
        # Check font face
        if font_name != "Times New Roman" and font_name != "Unknown (Inherited)":
            font_issues += 1
            if font_issues <= 5: # Limit reports
                issues.append(f"Para {idx} ('{text[:30]}...'): Non-standard font '{font_name}' (expected Times New Roman)")
                
        # Check alignment & spacing for body text (Normal style)
        if style_name == 'Normal':
            # Size check
            if font_size != 13.0 and font_size != 12.0: # Vietnamese standard allows 12 or 13pt
                issues.append(f"Para {idx} ('{text[:30]}...'): Body font size is {font_size} pt (expected 13.0 or 12.0 pt)")
                
            # Alignment check: should be Justified
            alignment = para.alignment or para.style.element.xpath('w:pPr/w:jc/@w:val')
            alignment_val = alignment[0] if isinstance(alignment, list) and alignment else alignment
            
            # python-docx alignment representation
            if para.alignment is not None:
                if para.alignment != WD_ALIGN_PARAGRAPH.JUSTIFY:
                    alignment_issues += 1
                    if alignment_issues <= 3:
                        issues.append(f"Para {idx} ('{text[:30]}...'): Alignment is not Justify")
                        
            # Spacing checks
            p_format = para.paragraph_format
            line_spacing = p_format.line_spacing
            space_after = p_format.space_after
            
            # Line spacing standard: 1.3 to 1.5
            if line_spacing is not None:
                # If it's a Pt object or similar, check value
                val = line_spacing if isinstance(line_spacing, float) else line_spacing.pt / 12.0 if hasattr(line_spacing, 'pt') else 1.0
                if not (1.29 <= val <= 1.51):
                    spacing_issues += 1
                    if spacing_issues <= 3:
                        issues.append(f"Para {idx} ('{text[:30]}...'): Line spacing is {val} (expected 1.3 - 1.5)")
                        
            # Space after standard: 6pt
            if space_after is not None and space_after.pt != 6.0:
                spacing_issues += 1
                if spacing_issues <= 3:
                    issues.append(f"Para {idx} ('{text[:30]}...'): Spacing After is {space_after.pt} pt (expected 6 pt)")
                    
    print(f"Checked {checked_paragraphs} non-empty paragraphs.")
    
    # 3. Report Results
    if not issues:
        print("\nCongratulations! The document conforms to all Checked Academic Standards.")
        return True
    else:
        print(f"\nFound {len(issues)} academic formatting issues:")
        for issue in issues[:15]:
            print(f" - {issue}")
        if len(issues) > 15:
            print(f" ... and {len(issues) - 15} more issues.")
        return False

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python format_checker.py <path_to_docx>")
        sys.exit(1)
    check_academic_format(sys.argv[1])
