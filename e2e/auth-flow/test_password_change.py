#!/usr/bin/env python3
"""
E2E test for Password Change Flow

Matches: AccountPage.vue (PasswordForm with title="Change Password")
         PasswordForm.vue (Current Password, New Password, Confirm New Password,
           Change Password submit, validation rules, success/error messages)
"""

import re
import sys
import traceback

from playwright.sync_api import expect, sync_playwright

from e2e.auth.auth_manager import authenticate_for_testing
from e2e.common.config import get_config
from e2e.common.helpers import (
    navigate_to,
    print_test_summary,
    take_screenshot,
    verify_element_exists,
    verify_text_visible,
    wait_for_spinner_gone,
)

config = get_config()
BASE_URL = config["web_url"]

# PasswordForm fields are within a q-card with title "Change Password"
CHANGE_PWD_CARD = '.q-card:has(.text-h6:has-text("Change Password"))'


def test_password_change():
    """Test password change form validation on account page"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=config["headless"], slow_mo=config["slow_mo"])

        print("\n=== PASSWORD CHANGE E2E TEST ===\n")

        page = None
        context = None
        try:
            page, context = authenticate_for_testing(browser)

            # Step 1: Navigate to account page
            print("1. Navigating to account page...")
            navigate_to(page, BASE_URL, "/account")
            wait_for_spinner_gone(page)
            verify_text_visible(page, "Account Settings")
            take_screenshot(page, "pwdchange_01_loaded", "Account page loaded")

            # Step 2: Verify Change Password section exists
            print("\n2. Verifying Change Password section...")
            verify_element_exists(page, CHANGE_PWD_CARD, "Change Password card")

            pwd_card = page.locator(CHANGE_PWD_CARD).first
            verify_element_exists(
                page,
                f'{CHANGE_PWD_CARD} input[autocomplete="current-password"]',
                "Current Password field",
            )
            verify_element_exists(
                page,
                f'{CHANGE_PWD_CARD} input[autocomplete="new-password"]',
                "New Password field",
            )
            print("   [OK] Change Password form fields visible")

            # Step 3: Test empty form submission
            print("\n3. Testing empty form validation...")
            submit_btn = pwd_card.locator('button[type="submit"]').first
            submit_btn.click()
            wait_for_spinner_gone(page)

            # Should show validation errors
            error_fields = pwd_card.locator(".q-field--error")
            expect(error_fields.first).to_be_visible(timeout=5000)
            print("   [OK] Empty form shows validation errors")
            take_screenshot(page, "pwdchange_03_validation", "Empty form validation")

            # Step 4: Test password too short
            print("\n4. Testing short password validation...")
            current_pwd = pwd_card.locator('input[autocomplete="current-password"]').first
            new_pwd_inputs = pwd_card.locator('input[autocomplete="new-password"]')
            new_pwd = new_pwd_inputs.first
            confirm_pwd = new_pwd_inputs.nth(1)

            current_pwd.fill("currentpass123")
            new_pwd.fill("short")
            confirm_pwd.fill("short")
            submit_btn.click()
            wait_for_spinner_gone(page)

            # Check for "at least 8 characters" validation
            pwd_field = new_pwd.locator("xpath=ancestor::*[contains(@class, 'q-field')]").first
            expect(pwd_field).to_have_class(re.compile(r"q-field--error"), timeout=5000)
            print("   [OK] Short password shows validation error")

            # Step 5: Test password mismatch
            print("\n5. Testing password mismatch validation...")
            new_pwd.fill("ValidPassword123")
            confirm_pwd.fill("DifferentPassword123")
            submit_btn.click()
            wait_for_spinner_gone(page)

            confirm_field = confirm_pwd.locator(
                "xpath=ancestor::*[contains(@class, 'q-field')]"
            ).first
            expect(confirm_field).to_have_class(re.compile(r"q-field--error"), timeout=5000)
            print("   [OK] Password mismatch shows validation error")

            take_screenshot(page, "pwdchange_05_mismatch", "Password mismatch")

            # Step 6: Test wrong current password
            print("\n6. Testing wrong current password...")
            current_pwd.fill("definitely_wrong_password")
            new_pwd.fill("ValidPassword123")
            confirm_pwd.fill("ValidPassword123")
            submit_btn.click()
            wait_for_spinner_gone(page)

            # Should show error message (from API)
            error_msg = pwd_card.locator(".text-negative")
            expect(error_msg.first).to_be_visible(timeout=10000)
            error_text = error_msg.first.inner_text()
            print(f"   [OK] Wrong password error: {error_text}")

            take_screenshot(page, "pwdchange_06_wrong", "Wrong current password")

            print_test_summary(
                "PASSWORD CHANGE",
                [
                    "Account page loads",
                    "Change Password section visible",
                    "Empty form validation",
                    "Short password validation",
                    "Password mismatch validation",
                    "Wrong current password rejected by API",
                ],
            )
            return True

        except Exception as e:
            print(f"\n[ERROR] {e}")
            if page is not None:
                take_screenshot(page, "pwdchange_error", "Error")
            traceback.print_exc()
            return False
        finally:
            if context is not None:
                context.close()
            browser.close()


if __name__ == "__main__":
    success = test_password_change()
    sys.exit(0 if success else 1)
