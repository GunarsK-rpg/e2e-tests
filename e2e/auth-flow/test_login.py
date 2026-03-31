#!/usr/bin/env python3
"""
E2E test for Login Flow
Uses credentials from .env or saved test user (from registration test).

Matches: LoginPage.vue (q-form, q-input Username/Password, q-btn submit)
         MainLayout.vue (account menu -> Logout)
"""

import sys
import traceback

from playwright.sync_api import expect, sync_playwright

from e2e.auth.auth_manager import load_test_user
from e2e.common.config import get_config
from e2e.common.helpers import (
    do_logout,
    fill_input,
    navigate_to,
    print_test_summary,
    submit_form,
    take_screenshot,
    verify_element_exists,
    verify_text_visible,
    wait_for_page_load,
)

config = get_config()
BASE_URL = config["web_url"]


def _get_credentials():
    """Get credentials from .env or saved test user"""
    if config["username"] and config["password"]:
        return config["username"], config["password"]
    test_user = load_test_user()
    if test_user:
        return test_user["username"], test_user["password"]
    return None, None


def test_login_flow():
    """Test login, session persistence, and logout"""
    username, password = _get_credentials()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=config["headless"], slow_mo=config["slow_mo"])
        context = browser.new_context(ignore_https_errors=config.get("ignore_https_errors", False))
        page = context.new_page()

        print("\n=== LOGIN FLOW E2E TEST ===\n")

        try:
            # Step 1: Login page loads
            print("1. Navigating to login page...")
            navigate_to(page, BASE_URL, "/login")
            expect(page).to_have_url(f"{BASE_URL}/login")
            print("   [OK] Login page loaded")

            # Step 2: Verify form elements
            print("\n2. Verifying form elements...")
            for label in ["Username", "Password"]:
                verify_element_exists(
                    page,
                    f'.q-field:has(.q-field__label:has-text("{label}"))',
                    f"{label} field",
                )
            verify_element_exists(page, 'button[type="submit"]', "Login button")

            # Step 3: Unauthorized redirect
            print("\n3. Testing unauthorized redirect...")
            page.goto(f"{BASE_URL}/")
            wait_for_page_load(page)
            assert "/login" in page.url, f"Expected redirect to /login, got {page.url}"
            print("   [OK] Redirected to login")

            # Step 4: Login with credentials
            print("\n4. Logging in...")
            if not username or not password:
                raise AssertionError("No credentials. Run registration test first.")

            navigate_to(page, BASE_URL, "/login")
            fill_input(page, "Username", username)
            fill_input(page, "Password", password)
            submit_form(page)
            wait_for_page_load(page)

            if "/login" not in page.url:
                print(f"   [OK] Login successful: {page.url}")
            else:
                take_screenshot(page, "login_04_fail", "Login failed")
                raise AssertionError("Still on login page after login attempt")

            # Step 5: Verify landing page
            print("\n5. Verifying landing page...")
            verify_text_visible(page, "My Characters")

            # Step 6: Session persistence
            print("\n6. Testing session persistence...")
            page.reload()
            wait_for_page_load(page)
            if "/login" not in page.url:
                print("   [OK] Session persisted")
            else:
                take_screenshot(page, "login_06_session_lost", "Session lost")
                raise AssertionError("Session lost after reload")

            # Step 7: Logout
            print("\n7. Testing logout...")
            do_logout(page)
            assert "/login" in page.url, f"Expected redirect to /login after logout, got {page.url}"
            print("   [OK] Logout successful")

            # Step 8: Access denied after logout
            print("\n8. Verifying access denied...")
            page.goto(f"{BASE_URL}/")
            wait_for_page_load(page)
            assert "/login" in page.url, f"Expected /login after logout, got {page.url}"
            print("   [OK] Access denied")

            print_test_summary(
                "LOGIN FLOW",
                [
                    "Login page loads",
                    "Form elements visible",
                    "Unauthorized redirect",
                    "Successful login",
                    "Landing page verified",
                    "Session persistence",
                    "Logout works",
                    "Access denied after logout",
                ],
            )

        except Exception as e:
            print(f"\n[ERROR] {e}")
            take_screenshot(page, "login_error", "Error")
            traceback.print_exc()
            raise
        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    try:
        test_login_flow()
    except Exception:
        sys.exit(1)
