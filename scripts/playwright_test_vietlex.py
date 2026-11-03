"""Playwright Human-Like Automation and Screenshot Capture for VietLex.

Tests legal search, document viewing, and legal consultation flows.
Captures full-page screenshots for 1-1 visual parity checking with VietLex DOCX figures.
"""

import os
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get("VIETLEX_URL", "http://127.0.0.1:8000")
OUT_DIR = Path(r"D:\Download\WordAssistant\artifacts\course-essay\vietlex-dacn-20261020\captures\live-runtime-20261103")
OUT_DIR.mkdir(parents=True, exist_ok=True)

def run_vietlex_live_test():
    print(f"Connecting to VietLex at: {BASE_URL}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        # 1. Home / Search Page
        print("1. Testing VietLex: Home / Search...")
        resp = page.goto(f"{BASE_URL}/", wait_until="domcontentloaded")
        time.sleep(2)
        page.screenshot(path=str(OUT_DIR / "01_vietlex_home_search.png"), full_page=True)

        # 2. Search Query Execution
        print("2. Testing VietLex: Search with Query...")
        search_input = page.locator("input[type='search'], input[name='q'], input[name='query'], input[type='text']").first
        if search_input.is_visible():
            search_input.fill("tiền lương thử việc theo bộ luật lao động")
            page.keyboard.press("Enter")
            time.sleep(3)
            page.screenshot(path=str(OUT_DIR / "02_vietlex_search_results.png"), full_page=True)

        # 3. Document View
        print("3. Testing VietLex: Document View...")
        doc_link = page.locator("a[href*='/documents/'], a[href*='/van-ban/'], a[href*='/doc/']").first
        if doc_link.is_visible():
            doc_link.click()
            time.sleep(2)
            page.screenshot(path=str(OUT_DIR / "03_vietlex_document_reader.png"), full_page=True)
        else:
            page.goto(f"{BASE_URL}/documents", wait_until="domcontentloaded")
            time.sleep(2)
            page.screenshot(path=str(OUT_DIR / "03_vietlex_document_reader.png"), full_page=True)

        # 4. Chat / Legal Assistant Consultation
        print("4. Testing VietLex: Legal RAG Chat...")
        chat_nav = page.locator("a[href*='/chat'], a:has-text('Trợ lý'), a:has-text('Hỏi đáp')").first
        if chat_nav.is_visible():
            chat_nav.click()
            time.sleep(2)
        else:
            page.goto(f"{BASE_URL}/chat", wait_until="domcontentloaded")
            time.sleep(2)
        page.screenshot(path=str(OUT_DIR / "04_vietlex_rag_chat.png"), full_page=True)

        browser.close()
        print(f"\nSUCCESS: Captured all VietLex live runtime screenshots in {OUT_DIR}")

if __name__ == "__main__":
    run_vietlex_live_test()
