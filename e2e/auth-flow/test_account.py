#!/usr/bin/env python3
"""
E2E test for Account Settings
Requires authenticated user (registration test must run first).

Matches: AccountPage.vue (Edit Profile form with Username, Display Name fields)
         MainLayout.vue (account menu -> Account Settings)
"""

import sys
import traceback

from playwright.sync_api import sync_playwright

from e2e.auth.auth_manager import authenticate_for_testing
from e2e.common.config import get_config
from e2e.common.helpers import (
    navigate_to,
    print_test_summary,
    submit_form,
    take_screenshot,
    verify_element_exists,
    verify_text_visible,
    wait_for_page_load,
    wait_for_spinner_gone,
    wait_for_text_change,
)

config = get_config()
BASE_URL = config["web_url"]

FIELD_BY_LABEL = '.q-field:has(.q-field__label:has-text("{label}"))'


def test_account_settings():
    """Test account settings page: username validation and profile update"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=config["headless"], slow_mo=config["slow_mo"])

        print("\n=== ACCOUNT SETTINGS E2E TEST ===\n")

        page = None
        context = None
        try:
            page, context = authenticate_for_testing(browser)

            # Step 1: Navigate to account page
            print("1. Navigating to account page...")
            navigate_to(page, BASE_URL, "/account")
            verify_text_visible(page, "Account Settings")
            take_screenshot(page, "account_01_loaded", "Account page loaded")

            # Step 2: Verify Edit Profile form elements
            print("\n2. Verifying Edit Profile form...")
            verify_text_visible(page, "Edit Profile")
            verify_element_exists(
                page,
                FIELD_BY_LABEL.format(label="Username"),
                "Username field",
            )
            verify_element_exists(
                page,
                FIELD_BY_LABEL.format(label="Display Name"),
                "Display Name field",
            )

            # Step 3: Get current username for restoration
            print("\n3. Reading current username...")
            username_input = (
                page.locator(FIELD_BY_LABEL.format(label="Username"))
                .first.locator("input.q-field__native")
                .first
            )
            original_username = username_input.input_value()
            print(f"   [OK] Current username: {original_username}")

            # Step 4: Test spaces validation
            print("\n4. Testing username with spaces rejected...")
            username_input.click()
            username_input.fill("user with spaces")
            wait_for_spinner_gone(page)
            submit_form(page, wait_ms=500)

            username_field = page.locator(FIELD_BY_LABEL.format(label="Username")).first
            error_msg = username_field.locator(".q-field__messages")
            error_msg.first.wait_for(state="visible", timeout=5000)
            error_text = error_msg.first.text_content()
            if "spaces" in error_text.lower():
                print(f"   [OK] Validation error shown: {error_text.strip()}")
            else:
                take_screenshot(page, "account_04_no_error", "Missing validation error")
                raise AssertionError(f"Expected spaces validation error, got: {error_text}")

            # Step 5: Verify form did not submit (still on account page)
            print("\n5. Verifying form did not submit...")
            wait_for_page_load(page)
            assert "/account" in page.url, f"Expected /account, got {page.url}"
            print("   [OK] Still on account page (form rejected)")

            # Step 6: Restore original username
            print("\n6. Restoring original username...")
            username_input.click()
            username_input.fill(original_username)
            wait_for_spinner_gone(page)
            take_screenshot(page, "account_06_restored", "Username restored")

            # Step 7: Test short username validation
            print("\n7. Testing short username rejected...")
            # Capture current error text so we can wait for it to change
            old_error = error_msg.first.text_content() if error_msg.count() > 0 else ""
            username_input.click()
            username_input.fill("ab")
            wait_for_spinner_gone(page)
            submit_form(page, wait_ms=500)

            # Wait for validation message to update from previous error
            error_text = wait_for_text_change(page, error_msg.first, old_error)
            if "at least 3" in error_text.lower():
                print(f"   [OK] Validation error shown: {error_text.strip()}")
            else:
                take_screenshot(page, "account_07_no_error", "Missing validation error")
                raise AssertionError(f"Expected min length error, got: {error_text}")

            # Step 8: Restore and verify Save button state
            print("\n8. Restoring username and checking Save button...")
            username_input.click()
            username_input.fill(original_username)
            wait_for_spinner_gone(page)

            save_btn = page.locator('button[type="submit"]').first
            is_disabled = save_btn.get_attribute("disabled") is not None
            assert is_disabled, "Save button must be disabled when there are no changes"
            print("   [OK] Save button disabled (no changes)")

            print_test_summary(
                "ACCOUNT SETTINGS",
                [
                    "Account page loads",
                    "Edit Profile form visible",
                    "Current username readable",
                    "Username with spaces rejected",
                    "Form does not submit with invalid data",
                    "Username restored",
                    "Short username rejected",
                    "Save button state correct",
                ],
            )
            return True

        except Exception as e:
            print(f"\n[ERROR] {e}")
            if page is not None:
                take_screenshot(page, "account_error", "Error")
            traceback.print_exc()
            return False
        finally:
            if context is not None:
                context.close()
            browser.close()


if __name__ == "__main__":
    success = test_account_settings()
    sys.exit(0 if success else 1)
