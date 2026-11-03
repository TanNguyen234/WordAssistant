"""Playwright Human-Like Automation and Screenshot Capture for StrongWine.

Executes real browser interaction across Customer, Shipper, and Admin roles.
Captures full-page and viewport screenshots for 1-1 visual comparison with DOCX figures.
"""

import os
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get("STRONGWINE_URL", "http://localhost:8080")
OUT_DIR = Path(r"D:\Download\WordAssistant\artifacts\course-essay\strongwine-revision-20261027\captures\live-runtime-20261103")
OUT_DIR.mkdir(parents=True, exist_ok=True)

def run_strongwine_live_test():
    print(f"Connecting to StrongWine at: {BASE_URL}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # -------------------------------------------------------------
        # Persona 1: Customer (Guest & Logged In)
        # -------------------------------------------------------------
        print("\n--- Testing Persona 1: Customer ---")
        customer_ctx = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = customer_ctx.new_page()

        # 1. Customer: Home Page
        print("1. Customer: Visiting Home Page...")
        resp = page.goto(f"{BASE_URL}/home", wait_until="networkidle")
        assert resp.status == 200, f"Failed to load home page, status: {resp.status}"
        page.evaluate("window.scrollTo(0, 400)")
        time.sleep(0.5)
        page.screenshot(path=str(OUT_DIR / "01_customer_home.png"), full_page=True)

        # 2. Customer: Wines Catalog
        print("2. Customer: Browsing Wines Catalog...")
        resp = page.goto(f"{BASE_URL}/wines", wait_until="networkidle")
        time.sleep(0.5)
        page.screenshot(path=str(OUT_DIR / "02_customer_catalog.png"), full_page=True)

        # 3. Customer: Wine Detail
        print("3. Customer: Inspecting Wine Detail...")
        first_wine = page.locator("a[href*='/wines/']").first
        if first_wine.is_visible():
            first_wine.click()
            page.wait_for_load_state("networkidle")
        else:
            page.goto(f"{BASE_URL}/wines/1", wait_until="networkidle")
        time.sleep(0.5)
        page.screenshot(path=str(OUT_DIR / "03_customer_wine_detail.png"), full_page=True)

        # 4. Customer: Cart Drawer / Page
        print("4. Customer: Viewing Cart...")
        # Try clicking add to cart button if present
        add_btn = page.locator("button:has-text('Thêm vào giỏ'), form[action*='/cart'] button, .btn-add-cart").first
        if add_btn.is_visible():
            try:
                add_btn.click()
                time.sleep(0.5)
            except Exception:
                pass
        page.goto(f"{BASE_URL}/cart", wait_until="networkidle")
        time.sleep(0.5)
        page.screenshot(path=str(OUT_DIR / "04_customer_cart.png"), full_page=True)

        # 5. Customer: Checkout
        print("5. Customer: Viewing Checkout...")
        page.goto(f"{BASE_URL}/checkout", wait_until="networkidle")
        time.sleep(0.5)
        page.screenshot(path=str(OUT_DIR / "05_customer_checkout.png"), full_page=True)
        customer_ctx.close()

        # -------------------------------------------------------------
        # Persona 2: Shipper (Mobile Cockpit)
        # -------------------------------------------------------------
        print("\n--- Testing Persona 2: Shipper (Mobile Viewport) ---")
        shipper_ctx = browser.new_context(
            viewport={"width": 390, "height": 844},
            is_mobile=True,
            has_touch=True
        )
        shipper_page = shipper_ctx.new_page()

        # Shipper Login
        print("6. Shipper: Logging into Mobile Cockpit...")
        shipper_page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded")
        shipper_page.fill("input#username", "shipper1")
        shipper_page.fill("input#password", "shipper123")
        shipper_page.click("button[type='submit']")
        shipper_page.wait_for_load_state("load")
        time.sleep(2)

        # Go to Shipper Dashboard
        shipper_page.goto(f"{BASE_URL}/shipper/dashboard", wait_until="domcontentloaded")
        time.sleep(2)
        shipper_page.screenshot(path=str(OUT_DIR / "06_shipper_dashboard_mobile.png"), full_page=True)
        shipper_ctx.close()

        # -------------------------------------------------------------
        # Persona 3: Admin (Backoffice & Warehouse Operations)
        # -------------------------------------------------------------
        print("\n--- Testing Persona 3: Admin ---")
        admin_ctx = browser.new_context(
            viewport={"width": 1920, "height": 1080}
        )
        admin_page = admin_ctx.new_page()

        # Admin Login
        print("7. Admin: Logging in...")
        admin_page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded")
        admin_page.fill("input#username", "admin")
        admin_page.fill("input#password", "admin123")
        admin_page.click("button[type='submit']")
        admin_page.wait_for_load_state("load")
        time.sleep(2)

        # 7. Admin: Dashboard
        print("8. Admin: Dashboard...")
        admin_page.goto(f"{BASE_URL}/admin", wait_until="domcontentloaded")
        time.sleep(2)
        admin_page.screenshot(path=str(OUT_DIR / "07_admin_dashboard.png"), full_page=True)

        # 8. Admin: Orders
        print("9. Admin: Orders Management...")
        admin_page.goto(f"{BASE_URL}/admin/orders", wait_until="domcontentloaded")
        time.sleep(2)
        admin_page.screenshot(path=str(OUT_DIR / "08_admin_orders.png"), full_page=True)

        # 9. Admin: Inventory
        print("10. Admin: Inventory Management...")
        admin_page.goto(f"{BASE_URL}/admin/inventory", wait_until="domcontentloaded")
        time.sleep(2)
        admin_page.screenshot(path=str(OUT_DIR / "09_admin_inventory.png"), full_page=True)

        # 10. Admin: Bulk Import
        print("11. Admin: Bulk Wine Import...")
        admin_page.goto(f"{BASE_URL}/admin/wines/import", wait_until="domcontentloaded")
        time.sleep(2)
        admin_page.screenshot(path=str(OUT_DIR / "10_admin_wines_import.png"), full_page=True)

        # 11. Admin: Shipments
        print("12. Admin: Shipments Dispatch Board...")
        admin_page.goto(f"{BASE_URL}/admin/shipments", wait_until="domcontentloaded")
        time.sleep(2)
        admin_page.screenshot(path=str(OUT_DIR / "11_admin_shipments.png"), full_page=True)
        admin_ctx.close()

        browser.close()
        print(f"\nSUCCESS: All live runtime screenshots captured in {OUT_DIR}")

if __name__ == "__main__":
    run_strongwine_live_test()
