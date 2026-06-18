import os
import sys
import json
import time
from dotenv import load_dotenv

# Ensure imports can be resolved
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environmental variables
load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

from src.agents import llm
from scripts.citation_helper import search_tavily, extract_metadata_with_gemini, add_reference_to_db
from scripts.format_checker import check_academic_format
from scripts.markdown_to_docx import build_docx_from_markdown

def run_word_assistant_pipeline(topic, doc_type="Tiểu Luận"):
    print("\n" + "="*60)
    print(f"🚀 WORDASSISTANT LIGHTWEIGHT WORKFLOW STARTING")
    print(f"Topic: '{topic}'")
    print(f"Document Type: {doc_type}")
    print("="*60 + "\n")
    
    # ── PHASE 1: RESEARCH ──
    print("🤖 [Phase 1] Researcher: Querying literature and verifying citations...")
    query = f"{topic} Vaswani Devlin academic paper"
    print(f"[Research] Searching online for citation: '{query}'...")
    results = search_tavily(topic)
    
    cite_key = "vaswani2017attention" # fallback default
    if results:
        print(f"[Research] Search completed. Verifying metadata with Gemini...")
        metadata = extract_metadata_with_gemini(topic, results)
        if metadata:
            ref_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../references.json'))
            added_key = add_reference_to_db(metadata, ref_path)
            if added_key:
                cite_key = added_key
                print(f"[Research] Verified and added cite_key: '{cite_key}'")
        else:
            print("[Research] Failed to extract metadata. Using fallback cite_key.")
    else:
        print("[Research] No search results found. Using fallback cite_key.")
        
    print("-"*60 + "\n")
    
    # ── PHASE 2: WRITING (DRAFTING) ──
    print("🤖 [Phase 2] Waiting 15s for API quota to recover...")
    time.sleep(15)
    print("🤖 [Phase 2] Academic Writer: Drafting raw content...")
    write_prompt = f"""Write a detailed academic introduction paragraph and a theoretical background section in Vietnamese for the topic: '{topic}'.
Integrate the verified source by placing the appropriate [@{cite_key}] tag in your writing.
Ensure you write in a formal, objective academic tone in Vietnamese without any personal pronouns (no 'tôi', 'chúng em', 'chúng ta').
Output in clean Markdown format with proper headings (# and ##). Do not output any conversational text or explanation outside the markdown."""
    
    try:
        writer_response = llm.invoke(write_prompt)
        draft_content = writer_response.content
        print("\nAcademic Writer Output (Draft):")
        print(draft_content)
    except Exception as e:
        print(f"Error in Phase 2: {e}")
        return
        
    print("-"*60 + "\n")
    
    # ── PHASE 3: REFINEMENT (ANTI-AI & PARAPHRASING) ──
    print("🤖 [Phase 3] Waiting 15s for API quota to recover...")
    time.sleep(15)
    print("🤖 [Phase 3] Anti-AI & Plagiarism Refiner: Humanizing text...")
    refine_prompt = f"""Take the following raw academic draft and rewrite it in Vietnamese to make it look human-written.
Draft Content to rewrite:
{draft_content}

Rules:
1. Maximize Burstiness by varying sentence length drastically (mix very short 5-10 word sentences with long, complex 25-35 word sentences).
2. Maximize Perplexity by using specific scientific, domain-specific vocabulary.
3. Remove all typical AI transitional phrases (AI-isms) like 'tóm lại', 'hơn nữa', 'hành trình', 'chìa khóa', 'không thể phủ nhận', 'bên cạnh đó'.
4. Paraphrase any direct arguments to avoid plagiarism.
Keep the Markdown headings (# and ##) and original [@{cite_key}] tags intact. Return ONLY the optimized Markdown without any other text."""

    try:
        refiner_response = llm.invoke(refine_prompt)
        refined_content = refiner_response.content
        print("\nRefiner Output (Humanized & Paraphrased):")
        print(refined_content)
    except Exception as e:
        print(f"Error in Phase 3: {e}")
        return
        
    print("-"*60 + "\n")
    
    # Save the refined markdown locally for compiler tool
    temp_md_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../temp_draft.md"))
    with open(temp_md_path, 'w', encoding='utf-8') as f:
        f.write(refined_content)
        
    # ── PHASE 4: COMPILATION & AUDIT ──
    print("🤖 [Phase 4] Format & Quality Auditor: Compiling and Auditing Word file...")
    output_docx = os.path.abspath(os.path.join(os.path.dirname(__file__), "../final_essay.docx"))
    ref_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../references.json'))
    
    try:
        print(f"[Audit] Compiling '{temp_md_path}' to '{output_docx}'...")
        success = build_docx_from_markdown(temp_md_path, ref_path, output_docx)
        if success:
            print(f"[Audit] Compiled document successfully to: '{output_docx}'")
            print("[Audit] Running academic format audit...")
            check_academic_format(output_docx)
        else:
            print("[Audit] Failed to compile document.")
    except Exception as e:
        print(f"Error in Phase 4: {e}")
        
    # Cleanup temporary markdown file
    if os.path.exists(temp_md_path):
        os.remove(temp_md_path)
        
    print("="*60 + "\n")
    print(f"🎉 Workflow finished. Final document generated at: '{output_docx}'")

if __name__ == '__main__':
    test_topic = "Ứng dụng cơ chế Attention và mô hình Transformer trong NLP"
    if len(sys.argv) > 1:
        test_topic = " ".join(sys.argv[1:])
        
    run_word_assistant_pipeline(test_topic)
