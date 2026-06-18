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

def merge_multiple_files(output_path, file_list):
    if not file_list:
        print("Error: No files specified for merging.")
        return
        
    first_file = file_list[0]
    if not os.path.exists(first_file):
        print(f"Error: Base file '{first_file}' does not exist.")
        return
        
    print(f"Opening base document: '{first_file}'...")
    try:
        # docx-mcp DocxDocument is composed of raw ZIP elements
        doc = DocxDocument(first_file)
        doc.open()
        
        # Merge remaining files
        for other_file in file_list[1:]:
            if not os.path.exists(other_file):
                print(f"Warning: File '{other_file}' not found. Skipping.")
                continue
            print(f"Merging: '{other_file}'...")
            res = doc.merge_documents(other_file)
            print(f" - Added {res.get('paragraphs_added', 0)} body elements.")
            
        # Run OOXML audit to prevent corruption
        print("Running structural audit...")
        audit_res = doc.audit()
        if audit_res.get("errors"):
            print("⚠️ Audit warnings/errors detected:")
            for err in audit_res["errors"]:
                print(f"  - {err}")
                
        # Save output
        doc.save(output_path)
        doc.close()
        print(f"Successfully merged files into: '{output_path}'")
    except Exception as e:
        print(f"An error occurred during merge: {e}")

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: python docx_merge.py <output_file.docx> <base_file.docx> <file_to_merge_1.docx> [<file_to_merge_2.docx> ...]")
        sys.exit(1)
        
    output = sys.argv[1]
    files = sys.argv[2:]
    merge_multiple_files(output, files)
