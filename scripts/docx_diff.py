import os
import sys

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# Add docx-mcp folder to Python path as a fallback
sys.path.append(os.path.join(os.path.dirname(__file__), '../docx-mcp'))

try:
    from docx_mcp.document import DocxDocument
except ImportError:
    print("Error: Could not import docx_mcp library. Please run 'pip install -e docx-mcp' first.")
    sys.exit(1)

def compare_files(base_path, revised_path, output_prefix=""):
    if not os.path.exists(base_path):
        print(f"Error: Base file '{base_path}' does not exist.")
        return
    if not os.path.exists(revised_path):
        print(f"Error: Revised file '{revised_path}' does not exist.")
        return
        
    base_dir = os.path.dirname(base_path) or "."
    base_name = os.path.splitext(os.path.basename(base_path))[0]
    
    if not output_prefix:
        docx_output = os.path.join(base_dir, f"{base_name}_compared.docx")
        text_output = os.path.join(base_dir, f"{base_name}_changes.txt")
    else:
        docx_output = f"{output_prefix}.docx"
        text_output = f"{output_prefix}_summary.txt"
        
    print(f"Comparing: '{base_path}' vs '{revised_path}'...")
    
    try:
        res = DocxDocument.diff_to_text(
            base_path=base_path,
            revised_path=revised_path,
            docx_output=docx_output,
            text_output=text_output
        )
        print(f"Comparison completed successfully!")
        print(f" - Tracked changes docx: {res.get('docx_path')}")
        print(f" - Text summary: {res.get('text_path')}")
        print(f" - Total changes detected: {res.get('change_count')}")
    except Exception as e:
        print(f"An error occurred during comparison: {e}")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python docx_diff.py <base_file.docx> <revised_file.docx> [<output_prefix>]")
        sys.exit(1)
        
    output_pref = sys.argv[3] if len(sys.argv) > 3 else ""
    compare_files(sys.argv[1], sys.argv[2], output_pref)
