#!/usr/bin/env python3
"""
E2E test for Password Recovery Flow

Matches: ForgotPasswordPage.vue (email input, "Send Reset Link" submit, success state)
         ResetPasswordPage.vue (no-token error state, "Request New Link" button)
"""

import sys
import time
import traceback

from playwright.sync_api import sync_playwright

from e2e.common.config import get_config
from e2e.common.helpers import (
    click_button,
    fill_input,
    navigate_to,
    print_test_summary,
    submit_form,
    take_screenshot,
    verify_element_exists,
    verify_text_visible,
    verify_url_contains,
    wait_for_page_load,
    wait_for_spinner_gone,
)

config = get_config()
BASE_URL = config["web_url"]


def test_password_recovery():
    """Test password recovery form and reset page states"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=config["headless"], slow_mo=config["slow_mo"])

        print("\n=== PASSWORD RECOVERY E2E TEST ===\n")

        page = None
        context = None
        try:
            context = browser.new_context(
                ignore_https_errors=config.get("ignore_https_errors", False)
            )
            page = context.new_page()
            unique_suffix = str(int(time.time()))[-6:]

            # Step 1: Navigate to forgot password page
            print("1. Navigating to forgot password page...")
            navigate_to(page, BASE_URL, "/forgot-password")
            verify_url_contains(page, "/forgot-password", "Forgot password page")
            take_screenshot(page, "recovery_01_loaded", "Forgot password page")

            # Step 2: Verify form elements
            print("\n2. Verifying form elements...")
            verify_text_visible(page, "Reset Password")
            verify_element_exists(page, 'input[type="email"]', "Email input")
            verify_element_exists(page, 'button[type="submit"]', "Submit button")

            # Step 3: Submit empty form (validation)
            print("\n3. Testing empty form submission...")
            submit_form(page)
            page.wait_for_timeout(300)
            email_input = page.locator('input[type="email"]').first
            is_invalid = email_input.evaluate(
                "el => !el.validity.valid || el.closest('.q-field--error') !== null"
            )
            assert is_invalid, "Email input should be in invalid state after empty submission"
            print("   [OK] Email validation shown")
            take_screenshot(page, "recovery_03_validation", "Empty form validation")

            # Step 4: Fill email and submit
            print("\n4. Submitting forgot password form...")
            fill_input(page, "Email", f"e2e_test_{unique_suffix}@example.com")
            submit_form(page)
            wait_for_spinner_gone(page)
            page.wait_for_timeout(1000)
            take_screenshot(page, "recovery_04_submitted", "After submission")

            # Step 5: Verify success state
            print("\n5. Verifying success state...")
            verify_text_visible(page, "Check your email")
            print("   [OK] Success message displayed")

            # Step 6: Navigate to reset password page without token
            print("\n6. Testing reset password page without token...")
            navigate_to(page, BASE_URL, "/reset-password")
            wait_for_page_load(page)
            verify_text_visible(page, "Invalid link")
            take_screenshot(page, "recovery_06_no_token", "No token state")

            # Step 7: Verify "Request New Link" button navigates back
            print("\n7. Verifying navigation back to forgot password...")
            click_button(page, "Request New Link")
            wait_for_page_load(page)
            verify_url_contains(page, "/forgot-password", "Back to forgot password")

            # Step 8: Verify login link from forgot password page
            print("\n8. Verifying login link...")
            page.locator('a:has-text("Back to Login")').first.click()
            page.wait_for_url("**/login**", timeout=10000)
            verify_url_contains(page, "/login", "Login page")

            take_screenshot(page, "recovery_08_done", "Test complete")

            print_test_summary(
                "PASSWORD RECOVERY",
                [
                    "Forgot password page loads",
                    "Form elements visible",
                    "Empty form validation",
                    "Email submission succeeds",
                    "Success message displayed",
                    "Reset page shows no-token error",
                    "Request New Link navigates back",
                    "Login link works",
                ],
            )
            return True

        except Exception as e:
            print(f"\n[ERROR] {e}")
            if page is not None:
                take_screenshot(page, "recovery_error", "Error")
            traceback.print_exc()
            return False
        finally:
            if context is not None:
                context.close()
            browser.close()


if __name__ == "__main__":
    success = test_password_recovery()
    sys.exit(0 if success else 1)
