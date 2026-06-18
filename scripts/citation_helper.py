import os
import sys
import json
import requests
from dotenv import load_dotenv

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# Load environment variables from .env
load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

TAVILY_API_KEY = os.getenv("TAVILY_API")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_BASE_URL = os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta")

def search_tavily(query):
    """Searches Tavily API for academic/general results."""
    if not TAVILY_API_KEY:
        print("Error: TAVILY_API key not found in .env")
        sys.exit(1)
        
    url = "https://api.tavily.com/search"
    payload = {
        "api_key": TAVILY_API_KEY,
        "query": query + " site:arxiv.org OR site:scholar.google.com OR site:researchgate.net OR site:ieee.org",
        "search_depth": "advanced",
        "max_results": 5
    }
    
    try:
        response = requests.post(url, json=payload, timeout=15)
        response.raise_for_status()
        return response.json().get("results", [])
    except Exception as e:
        print(f"Error searching Tavily: {e}")
        return []

def extract_metadata_with_gemini(query, search_results):
    """Uses Gemini API to extract proper academic metadata from search results."""
    if not GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY not found in .env")
        sys.exit(1)
        
    endpoint = f"{GEMINI_BASE_URL}/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    
    # Format the results for Gemini
    results_text = ""
    for idx, r in enumerate(search_results):
        results_text += f"[{idx+1}] Title: {r.get('title')}\nURL: {r.get('url')}\nContent: {r.get('content')}\n\n"
        
    prompt = f"""
You are an academic citation extraction expert. Your job is to extract the most accurate, real bibliographic metadata for the user's query from the search results provided.

User Query: "{query}"

Search Results:
{results_text}

Analyze the search results. Find the one that matches the query best and is a real academic paper/book/website.
Extract and return the metadata in JSON format. Do not invent details. Only extract real information. If a field is missing, leave it as an empty string.

Expected Output JSON structure:
{{
  "cite_key": "lowercase_lastname_year_keyword (e.g. devlin2018bert, vaswani2017attention)",
  "author": "List of authors in 'LastName, FirstName and LastName, FirstName' or 'FirstName LastName, FirstName LastName' format",
  "title": "Title of the paper/book/document",
  "journal": "Journal name, arXiv preprint, or publisher",
  "year": "Year of publication (4 digits)",
  "volume": "Volume number (optional, empty string if none)",
  "number": "Issue number (optional, empty string if none)",
  "pages": "Page numbers (optional, e.g. 45-52, empty string if none)",
  "url": "Direct URL of the paper/document (e.g. PDF or ArXiv page)"
}}
"""
    
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }],
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }
    
    try:
        response = requests.post(endpoint, json=payload, timeout=20)
        response.raise_for_status()
        
        response_json = response.json()
        candidates = response_json.get("candidates", [])
        if candidates:
            text_response = candidates[0]["content"]["parts"][0]["text"]
            return json.loads(text_response)
        return None
    except Exception as e:
        print(f"Error calling Gemini: {e}")
        return None

def add_reference_to_db(metadata, ref_db_path="../references.json"):
    """Adds the extracted reference metadata to references.json database."""
    if not os.path.exists(ref_db_path):
        db = {"citation_style": "IEEE", "sources": {}}
    else:
        with open(ref_db_path, 'r', encoding='utf-8') as f:
            try:
                db = json.load(f)
            except json.JSONDecodeError:
                db = {"citation_style": "IEEE", "sources": {}}
                
    cite_key = metadata.get("cite_key")
    if not cite_key:
        print("Error: Extracted metadata has no cite_key")
        return False
        
    # Remove cite_key from the payload inserted into database
    payload = metadata.copy()
    del payload["cite_key"]
    
    db["sources"][cite_key] = payload
    
    with open(ref_db_path, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
        
    print(f"Successfully added reference '{cite_key}' to '{os.path.basename(ref_db_path)}'")
    return cite_key

def main():
    if len(sys.argv) < 2:
        print("Usage: python citation_helper.py <search_query>")
        sys.exit(1)
        
    query = " ".join(sys.argv[1:])
    print(f"Searching online for: '{query}'...")
    
    results = search_tavily(query)
    if not results:
        print("No results found.")
        sys.exit(1)
        
    print(f"Found {len(results)} results on Tavily. Processing with Gemini...")
    
    metadata = extract_metadata_with_gemini(query, results)
    if not metadata:
        print("Failed to extract metadata with Gemini.")
        sys.exit(1)
        
    print("\nExtracted Academic Metadata:")
    print(json.dumps(metadata, indent=2, ensure_ascii=False))
    
    ref_path = os.path.join(os.path.dirname(__file__), '../references.json')
    add_reference_to_db(metadata, ref_path)

if __name__ == '__main__':
    main()
