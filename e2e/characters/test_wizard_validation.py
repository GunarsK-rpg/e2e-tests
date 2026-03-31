#!/usr/bin/env python3
"""
E2E test for Character Creation Wizard validation

Matches: BasicSetupStep.vue (Character Name required, ancestry required)
         StepNavigation.vue (.status-message.text-negative for validation errors)
         CharacterCreationPage.vue (step does not advance when invalid)
"""

import sys
import traceback

from playwright.sync_api import expect, sync_playwright

from e2e.auth.auth_manager import authenticate_for_testing
from e2e.common.config import get_config
from e2e.common.helpers import (
    BTN_NEXT_STEP,
    click_next_step,
    fill_input,
    navigate_to,
    print_test_summary,
    select_first_card,
    take_screenshot,
    verify_element_exists,
    wait_for_spinner_gone,
)

config = get_config()
BASE_URL = config["web_url"]

# Wizard footer shows validation errors in this element
STATUS_MESSAGE = ".status-message.text-negative"


def test_wizard_validation():
    """Test character creation wizard form validation"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=config["headless"], slow_mo=config["slow_mo"])

        print("\n=== WIZARD VALIDATION E2E TEST ===\n")

        page = None
        context = None
        try:
            page, context = authenticate_for_testing(browser)

            # Step 1: Navigate to creation wizard
            print("1. Navigating to character creation...")
            navigate_to(page, BASE_URL, "/characters/new")
            wait_for_spinner_gone(page)
            verify_element_exists(page, "input.q-field__native", "Character name field")
            take_screenshot(page, "validation_01_start", "Wizard start")

            # Step 2: Click Next with empty name -- validation error in footer
            print("\n2. Testing empty name validation...")
            page.locator(BTN_NEXT_STEP).first.click()
            wait_for_spinner_gone(page)

            # Footer shows "Name is required" in status-message
            status_msg = page.locator(STATUS_MESSAGE)
            expect(status_msg.first).to_be_visible(timeout=5000)
            msg_text = status_msg.first.inner_text().strip()
            assert "name" in msg_text.lower(), f"Expected name error, got: {msg_text}"
            print(f"   [OK] Validation error: {msg_text}")

            # Still on Basic Setup (step did not advance)
            active_tab = page.locator(".q-tab--active .q-tab__label").first
            assert (
                active_tab.inner_text().strip().upper() == "BASIC SETUP"
            ), "Should still be on Basic Setup"
            print("   [OK] Step did not advance")
            take_screenshot(page, "validation_02_name_error", "Name validation")

            # Step 3: Fill name but skip ancestry -- should still block
            print("\n3. Testing missing ancestry validation...")
            fill_input(page, "Character Name", "Validation Test")

            selected = page.locator(".q-card[role='radio'].card-selected")
            if selected.count() == 0:
                page.locator(BTN_NEXT_STEP).first.click()
                wait_for_spinner_gone(page)

                # Should still be on Basic Setup
                tab_text = (
                    page.locator(".q-tab--active .q-tab__label").first.inner_text().strip().upper()
                )
                assert tab_text == "BASIC SETUP", f"Expected Basic Setup, got {tab_text}"
                print("   [OK] Missing ancestry blocks advancement")
            else:
                print("   [INFO] Ancestry pre-selected, skipping")

            # Step 4: Select ancestry and advance -- should succeed
            print("\n4. Selecting ancestry and advancing...")
            select_first_card(page, "Ancestry")
            click_next_step(page)
            wait_for_spinner_gone(page)

            # Should now be on Culture step
            culture_field = page.locator(
                '.q-field:has(.q-field__label:has-text("Primary Culture"))'
            )
            expect(culture_field.first).to_be_visible(timeout=5000)
            print("   [OK] Advanced to Culture step")
            take_screenshot(page, "validation_04_culture", "Culture step")

            print_test_summary(
                "WIZARD VALIDATION",
                [
                    "Wizard loads",
                    "Empty name shows footer validation error",
                    "Step does not advance with invalid data",
                    "Missing ancestry blocks advancement",
                    "Valid form advances to next step",
                ],
            )
            return True

        except Exception as e:
            print(f"\n[ERROR] {e}")
            if page is not None:
                take_screenshot(page, "validation_error", "Error")
            traceback.print_exc()
            return False
        finally:
            if context is not None:
                context.close()
            browser.close()


if __name__ == "__main__":
    success = test_wizard_validation()
    sys.exit(0 if success else 1)
