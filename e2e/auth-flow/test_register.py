#!/usr/bin/env python3
"""
E2E test for Registration Flow
Must run FIRST -- creates test user and saves credentials for all subsequent tests.

Matches: RegisterPage.vue (q-form with q-input fields, q-btn type=submit)
"""

import sys
import time
import traceback

from playwright.sync_api import expect, sync_playwright

from e2e.auth.auth_manager import AuthManager, save_test_user
from e2e.common.config import get_config
from e2e.common.helpers import (
    fill_input,
    navigate_to,
    print_test_summary,
    submit_form,
    take_screenshot,
    verify_element_exists,
    wait_for_page_load,
)

config = get_config()
BASE_URL = config["web_url"]


def test_register_flow():
    """Register a new user and save credentials for the test suite"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=config["headless"], slow_mo=config["slow_mo"])
        context = None
        page = None
        context = browser.new_context(ignore_https_errors=config.get("ignore_https_errors", False))
        page = context.new_page()

        print("\n=== REGISTRATION FLOW E2E TEST ===\n")

        unique_suffix = str(int(time.time()))[-6:]
        test_username = f"e2e_test_{unique_suffix}"
        test_email = f"e2e_test_{unique_suffix}@test.local"
        test_password = f"TestPass{unique_suffix}!"

        try:
            # Step 1: Navigate to register page
            print("1. Navigating to register page...")
            navigate_to(page, BASE_URL, "/register")
            expect(page).to_have_url(f"{BASE_URL}/register")
            print("   [OK] Register page loaded")

            # Step 2: Verify form elements
            print("\n2. Verifying form elements...")
            for label in ["Username", "Email", "Password", "Confirm Password"]:
                verify_element_exists(
                    page,
                    f'.q-field:has(.q-field__label:has-text("{label}"))',
                    f"{label} field",
                )

            # Step 3: Empty form validation
            print("\n3. Testing empty form validation...")
            submit_form(page, wait_ms=500)
            expect(page).to_have_url(f"{BASE_URL}/register")
            print("   [OK] Empty form rejected")

            # Step 4: Fill registration form
            print("\n4. Filling registration form...")
            fill_input(page, "Username", test_username)
            fill_input(page, "Email", test_email)
            fill_input(page, "Password", test_password)
            fill_input(page, "Confirm Password", test_password)
            print(f"   [OK] Username: {test_username}")
            take_screenshot(page, "register_04_filled", "Form filled")

            # Step 5: Submit registration
            print("\n5. Submitting registration...")
            submit_form(page)
            wait_for_page_load(page)

            if "/login" in page.url:
                print("   [OK] Redirected to login")
                verify_element_exists(page, '[role="status"]', "Success message")
            else:
                print(f"   [OK] Registration processed: {page.url}")

            take_screenshot(page, "register_05_submitted", "After submit")

            # Step 6: Verify login with new account
            print("\n6. Logging in with new account...")
            navigate_to(page, BASE_URL, "/login")
            fill_input(page, "Username", test_username)
            fill_input(page, "Password", test_password)
            submit_form(page)
            wait_for_page_load(page)

            if "/login" not in page.url:
                print("   [OK] Login successful")
            else:
                take_screenshot(page, "register_06_login_fail", "Login failed")
                print("   [FAIL] Could not login with new account")
                return False

            # Step 7: Save credentials for other tests
            print("\n7. Saving credentials...")
            save_test_user(test_username, test_password)
            AuthManager().save_context(context)

            print_test_summary(
                "REGISTRATION FLOW",
                [
                    "Register page loads",
                    "Form elements visible",
                    "Empty form validation",
                    "Form fills with valid data",
                    "Registration submits",
                    "Login with new account",
                    "Credentials saved",
                ],
            )
            return True

        except Exception as e:
            print(f"\n[ERROR] {e}")
            if page is not None:
                take_screenshot(page, "register_error", "Error")
            traceback.print_exc()
            return False
        finally:
            if context is not None:
                context.close()
            browser.close()


if __name__ == "__main__":
    success = test_register_flow()
    sys.exit(0 if success else 1)
