"""Playwright Human-Like Automation and Screenshot Capture for University LMS.

Tests 3 distinct personas: Admin, Lecturer, and Student.
Captures full-page screenshots for 1-1 visual parity checking with LMS DOCX figures.
"""

import os
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get("LMS_FRONTEND_URL", "http://localhost:5173")
OUT_DIR = Path(r"D:\Download\WordAssistant\artifacts\course-essay\lms-qlpm-trello-drawio\captures\live-runtime-20261103")
OUT_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_PASSWORD = "Demo@123"

def run_lms_live_test():
    print(f"Connecting to University LMS at: {BASE_URL}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        # 1. Login Page
        print("1. Testing Login Page...")
        page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded")
        time.sleep(1)
        page.screenshot(path=str(OUT_DIR / "01_login_page.png"), full_page=True)

        # -------------------------------------------------------------
        # Persona 1: Admin Flow
        # -------------------------------------------------------------
        print("\n--- Testing Persona 1: Admin (admin@university.edu.vn) ---")
        page.fill("input#login-email", "admin@university.edu.vn")
        page.fill("input#login-password", DEFAULT_PASSWORD)
        page.click("button[type='submit']")
        page.wait_for_load_state("load")
        time.sleep(2)

        # Admin: Dashboard
        print("2. Admin: Dashboard...")
        page.goto(f"{BASE_URL}/dashboard", wait_until="domcontentloaded")
        time.sleep(2)
        page.screenshot(path=str(OUT_DIR / "02_admin_dashboard.png"), full_page=True)

        # Admin: User Management (/users)
        print("3. Admin: Users Management...")
        page.goto(f"{BASE_URL}/users", wait_until="domcontentloaded")
        time.sleep(2)
        page.screenshot(path=str(OUT_DIR / "03_admin_user_management.png"), full_page=True)

        # Admin: Courses (/courses)
        print("4. Admin: Courses Management...")
        page.goto(f"{BASE_URL}/courses", wait_until="domcontentloaded")
        time.sleep(2)
        page.screenshot(path=str(OUT_DIR / "04_admin_courses_management.png"), full_page=True)

        # Logout Admin
        context.clear_cookies()
        page.evaluate("() => localStorage.clear()")
        page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded")
        time.sleep(1)

        # -------------------------------------------------------------
        # Persona 2: Lecturer Flow
        # -------------------------------------------------------------
        print("\n--- Testing Persona 2: Lecturer (lecturer1@university.edu.vn) ---")
        page.fill("input#login-email", "lecturer1@university.edu.vn")
        page.fill("input#login-password", DEFAULT_PASSWORD)
        page.click("button[type='submit']")
        page.wait_for_load_state("load")
        time.sleep(2)

        # Lecturer: Dashboard
        print("5. Lecturer: Dashboard...")
        page.goto(f"{BASE_URL}/dashboard", wait_until="domcontentloaded")
        time.sleep(2)
        page.screenshot(path=str(OUT_DIR / "05_lecturer_dashboard.png"), full_page=True)

        # Lecturer: Assignments
        print("6. Lecturer: Assignments & Grading...")
        page.goto(f"{BASE_URL}/assignments", wait_until="domcontentloaded")
        time.sleep(2)
        page.screenshot(path=str(OUT_DIR / "06_lecturer_assignments.png"), full_page=True)

        # Logout Lecturer
        context.clear_cookies()
        page.evaluate("() => localStorage.clear()")
        page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded")
        time.sleep(1)

        # -------------------------------------------------------------
        # Persona 3: Student Flow
        # -------------------------------------------------------------
        print("\n--- Testing Persona 3: Student (student1@university.edu.vn) ---")
        page.fill("input#login-email", "student1@university.edu.vn")
        page.fill("input#login-password", DEFAULT_PASSWORD)
        page.click("button[type='submit']")
        page.wait_for_load_state("load")
        time.sleep(2)

        # Student: Dashboard
        print("7. Student: Dashboard...")
        page.goto(f"{BASE_URL}/dashboard", wait_until="domcontentloaded")
        time.sleep(2)
        page.screenshot(path=str(OUT_DIR / "07_student_dashboard.png"), full_page=True)

        # Student: Courses
        print("8. Student: Courses...")
        page.goto(f"{BASE_URL}/courses", wait_until="domcontentloaded")
        time.sleep(2)
        page.screenshot(path=str(OUT_DIR / "08_student_courses.png"), full_page=True)

        # Student: Grades
        print("9. Student: Grades...")
        page.goto(f"{BASE_URL}/grades", wait_until="domcontentloaded")
        time.sleep(2)
        page.screenshot(path=str(OUT_DIR / "09_student_grades.png"), full_page=True)

        # Student: Quizzes
        print("10. Student: Quizzes...")
        page.goto(f"{BASE_URL}/quizzes", wait_until="domcontentloaded")
        time.sleep(2)
        page.screenshot(path=str(OUT_DIR / "10_student_quizzes.png"), full_page=True)

        browser.close()
        print(f"\nSUCCESS: All LMS live runtime screenshots captured in {OUT_DIR}")

if __name__ == "__main__":
    run_lms_live_test()
