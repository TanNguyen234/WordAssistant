import os
import sys
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from deepagents import create_deep_agent

# Ensure absolute paths can be resolved
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.citation_helper import search_tavily, extract_metadata_with_gemini, add_reference_to_db
from scripts.format_checker import check_academic_format
from scripts.markdown_to_docx import build_docx_from_markdown
from scripts.docx_diff import compare_files
from scripts.docx_merge import merge_multiple_files

# Load environment keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Initialize LLM
llm = ChatGoogleGenerativeAI(
    model=GEMINI_MODEL,
    google_api_key=GEMINI_API_KEY,
    temperature=0.2,
    max_retries=12
)

# ── DEFINING LANGCHAIN TOOLS ──────────────────────────────────────────────────

@tool
def search_and_verify_citation(query: str) -> str:
    """Searches online for a real academic paper/book, extracts correct metadata using Gemini,
    and automatically registers the source in references.json to prevent hallucinated citations.
    Input should be a search query (e.g. 'Attention Is All You Need Vaswani 2017')."""
    print(f"[Tool] Searching online for citation: '{query}'...")
    results = search_tavily(query)
    if not results:
        return "No results found on Tavily."
    
    metadata = extract_metadata_with_gemini(query, results)
    if not metadata:
        return "Failed to extract metadata with Gemini."
        
    ref_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../references.json'))
    cite_key = add_reference_to_db(metadata, ref_path)
    if cite_key:
        return f"Successfully verified and added '{cite_key}' to references.json."
    return "Failed to add reference to database."

@tool
def audit_docx_format(docx_path: str) -> str:
    """Audits a Word (.docx) document margins, font name, size, spacing, and alignment
    against Vietnamese university academic standards.
    Input should be the path to the DOCX file (e.g. 'output.docx')."""
    print(f"[Tool] Auditing format for: '{docx_path}'...")
    try:
        # We redirect stdout to capture the audit report print statements
        import io
        old_stdout = sys.stdout
        sys.stdout = buffer = io.StringIO()
        
        check_academic_format(docx_path)
        
        sys.stdout = old_stdout
        return buffer.getvalue()
    except Exception as e:
        return f"Error auditing document: {e}"

@tool
def compile_markdown_to_docx(md_path: str, output_path: str) -> str:
    """Compiles a Markdown file into a structured Word (.docx) file.
    Automatically formats A4 margins, Times New Roman 13pt, page breaks, tables,
    and converts [@cite_key] tags to bibliography entries using references.json.
    Input: md_path (e.g., 'report.md') and output_path (e.g., 'report.docx')."""
    print(f"[Tool] Compiling '{md_path}' to '{output_path}'...")
    ref_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../references.json'))
    try:
        success = build_docx_from_markdown(md_path, ref_path, output_path)
        if success:
            return f"Successfully compiled document to: '{output_path}'"
        return "Failed to compile document."
    except Exception as e:
        return f"Error compiling document: {e}"

@tool
def diff_word_documents(base_docx: str, revised_docx: str, output_prefix: str) -> str:
    """Compares two Word documents (e.g. base draft vs supervisor edits).
    Generates a redlined DOCX containing tracked changes and a text summary listing all insertions/deletions.
    Input: base_docx, revised_docx, and output_prefix for the output files."""
    print(f"[Tool] Diffing '{base_docx}' vs '{revised_docx}'...")
    try:
        compare_files(base_docx, revised_docx, output_prefix)
        return f"Successfully generated compared files: '{output_prefix}.docx' and '{output_prefix}_summary.txt'"
    except Exception as e:
        return f"Error comparing files: {e}"

@tool
def merge_docx_chapters(output_path: str, chapter_files: list[str]) -> str:
    """Merges multiple Word (.docx) files (e.g., individual chapters written by different agents)
    into a single cohesive document, automatically de-duplicating XML paraIds to avoid corruption.
    Input: output_path and list of chapter file paths."""
    print(f"[Tool] Merging chapters: {chapter_files} into '{output_path}'...")
    try:
        merge_multiple_files(output_path, chapter_files)
        return f"Successfully merged files into: '{output_path}'"
    except Exception as e:
        return f"Error merging files: {e}"


# ── CREATING DEEP AGENTS ──────────────────────────────────────────────────────

# 1. Researcher Agent
researcher_agent = create_deep_agent(
    model=llm,
    tools=[search_and_verify_citation],
    system_prompt="""You are the Researcher & Citation Verifier Agent for the WordAssistant system.
Your primary role is to find real academic sources for a given topic and register them in references.json.
CRITICAL RULE: Never invent, hallucinate, or fabricate references (authors, journals, years, URLs).
Always run the search_and_verify_citation tool to find real papers on Google Scholar, ArXiv, etc.
Only reply with validated citations from references.json."""
)

# 2. Academic Writer Agent
writer_agent = create_deep_agent(
    model=llm,
    tools=[],
    system_prompt="""You are the Academic Writer Agent for the WordAssistant system.
Your job is to write high-quality academic prose in Vietnamese.
Rules:
1. Always write in a formal, objective, academic tone (never use personal pronouns like 'tôi', 'chúng em').
2. Format your paragraphs using the TEEL structure: Topic Sentence -> Explanation -> Evidence -> Link.
3. Integrate sources by placing [@cite_key] tags in the text where appropriate. Ensure the cite_keys are real and exist in references.json.
4. Output your results in clean Markdown format (headings, paragraphs, lists, tables)."""
)

# 3. Anti-AI & Plagiarism Refiner Agent
refiner_agent = create_deep_agent(
    model=llm,
    tools=[],
    system_prompt="""You are the Anti-AI & Plagiarism Refiner Agent.
Your job is to rewrite and optimize Vietnamese academic text to bypass AI detectors (Turnitin, GPTZero) and avoid plagiarism.
Tactics:
1. Vary sentence lengths drastically (Burstiness): Mix very short sentences (5-10 words) with long, complex sentences (25-35 words).
2. Use sophisticated, domain-specific terminology (Perplexity) instead of generic AI words.
3. Remove AI-isms (e.g., 'tóm lại', 'hơn nữa', 'hành trình', 'chìa khóa', 'không thể phủ nhận').
4. Paraphrase all research content: rewrite the arguments with different grammatical structures and logical sequences to avoid matching Turnitin's database."""
)

# 4. Format & Quality Auditor Agent
auditor_agent = create_deep_agent(
    model=llm,
    tools=[audit_docx_format, compile_markdown_to_docx, diff_word_documents, merge_docx_chapters],
    system_prompt="""You are the Format & Quality Auditor Agent for the WordAssistant system.
Your job is to compile Markdown into Word (.docx) files, merge chapters, diff document versions, and validate formatting.
Always run compile_markdown_to_docx to build the Word file.
Then, run audit_docx_format to check for margin, font, size, and spacing issues.
Provide a clear, bulleted report of any formatting errors or structural warnings."""
)
