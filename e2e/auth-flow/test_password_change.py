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
    FIELD_BY_LABEL,
    fill_input,
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
            # Tab through all fields to trigger blur validation on each
            required_fields = ["Current Password", "New Password", "Confirm New Password"]
            for label in required_fields:
                field = page.locator(
                    FIELD_BY_LABEL.format(label=label)
                ).first.locator("input.q-field__native").first
                field.click()
            # Click away to trigger blur on last field
            page.locator("body").click()
            submit_btn.click()
            wait_for_spinner_gone(page)

            # Should show validation errors on all required fields
            error_fields = pwd_card.locator(".q-field--error")
            expect(error_fields.first).to_be_visible(timeout=5000)
            assert error_fields.count() == len(required_fields), (
                f"Expected {len(required_fields)} field errors, got {error_fields.count()}"
            )
            for i in range(len(required_fields)):
                expect(error_fields.nth(i)).to_be_visible()
            print(f"   [OK] All {len(required_fields)} required fields show validation errors")
            take_screenshot(page, "pwdchange_03_validation", "Empty form validation")

            # Step 4: Test password too short
            print("\n4. Testing short password validation...")
            fill_input(page, "Current Password", "currentpass123")
            fill_input(page, "New Password", "short")
            fill_input(page, "Confirm New Password", "short")
            submit_btn.click()
            wait_for_spinner_gone(page)

            # Check for "at least 8 characters" validation
            pwd_field = page.locator(FIELD_BY_LABEL.format(label="New Password")).first
            expect(pwd_field).to_have_class(re.compile(r"q-field--error"), timeout=5000)
            print("   [OK] Short password shows validation error")

            # Step 5: Test password mismatch
            print("\n5. Testing password mismatch validation...")
            fill_input(page, "New Password", "ValidPassword123")
            fill_input(page, "Confirm New Password", "DifferentPassword123")
            submit_btn.click()
            wait_for_spinner_gone(page)

            confirm_field = page.locator(FIELD_BY_LABEL.format(label="Confirm New Password")).first
            expect(confirm_field).to_have_class(re.compile(r"q-field--error"), timeout=5000)
            print("   [OK] Password mismatch shows validation error")

            take_screenshot(page, "pwdchange_05_mismatch", "Password mismatch")

            # Step 6: Test wrong current password
            print("\n6. Testing wrong current password...")
            fill_input(page, "Current Password", "definitely_wrong_password")
            fill_input(page, "New Password", "ValidPassword123")
            fill_input(page, "Confirm New Password", "ValidPassword123")
            submit_btn.click()
            wait_for_spinner_gone(page)

            # Should show error message (from API)
            error_msg = pwd_card.locator(".text-negative")
            expect(error_msg.first).to_be_visible(timeout=10000)
            expect(error_msg.first).to_contain_text(
                re.compile(r"(password|incorrect|invalid)", re.IGNORECASE), timeout=5000
            )
            print(f"   [OK] Wrong password error: {error_msg.first.inner_text()}")

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

        except Exception as e:
            print(f"\n[ERROR] {e}")
            if page is not None:
                take_screenshot(page, "pwdchange_error", "Error")
            traceback.print_exc()
            raise
        finally:
            if context is not None:
                context.close()
            browser.close()


if __name__ == "__main__":
    try:
        test_password_change()
    except Exception:
        sys.exit(1)
