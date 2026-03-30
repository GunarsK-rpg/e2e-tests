#!/usr/bin/env python3
"""
E2E test for Character Editing

Matches: CharacterCreationPage.vue (edit mode via /characters/:id/edit)
         wizard.ts (startEdit loads existing hero)
         PersonalDetailsStep.vue (textarea fields for biography, appearance, notes)
         ReviewStep.vue (summary and Finish button)
"""

import sys
import time
import traceback

from playwright.sync_api import sync_playwright

from e2e.auth.auth_manager import authenticate_for_testing
from e2e.common.config import get_config
from e2e.common.helpers import (
    BTN_FINISH,
    HERO_CARD,
    click_button_by_aria,
    click_finish,
    click_tab,
    fill_textarea,
    navigate_to,
    print_test_summary,
    take_screenshot,
    verify_element_exists,
    verify_text_visible,
    verify_url_contains,
    wait_for_element,
    wait_for_page_load,
    wait_for_spinner_gone,
)

config = get_config()
BASE_URL = config["web_url"]


def test_character_editing():
    """Test editing an existing character via the wizard"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=config["headless"], slow_mo=config["slow_mo"])

        print("\n=== CHARACTER EDITING E2E TEST ===\n")

        page = None
        context = None
        try:
            page, context = authenticate_for_testing(browser)
            unique_suffix = str(int(time.time()))[-6:]

            # Step 1: Navigate to My Characters and select a character
            print("1. Navigating to My Characters...")
            navigate_to(page, BASE_URL, "/")
            wait_for_spinner_gone(page)

            if wait_for_element(page, HERO_CARD) == 0:
                raise AssertionError("No characters found -- cannot test editing")

            page.locator(HERO_CARD).first.click()
            page.wait_for_url("**/characters/**", timeout=10000)
            wait_for_page_load(page)
            wait_for_spinner_gone(page)

            verify_url_contains(page, "/characters/")
            character_url = page.url
            take_screenshot(page, "edit_01_sheet", "Character sheet")

            # Step 2: Enter edit mode
            print("\n2. Entering edit mode...")
            click_button_by_aria(page, "Edit character")
            page.wait_for_url("**/edit**", timeout=10000)
            wait_for_page_load(page)
            wait_for_spinner_gone(page)

            verify_url_contains(page, "/edit", "Edit mode")
            take_screenshot(page, "edit_02_wizard", "Edit wizard loaded")

            # Step 3: Verify wizard loaded with existing data
            print("\n3. Verifying wizard loaded with existing data...")
            verify_element_exists(page, "input.q-field__native", "Character name field")
            print("   [OK] Wizard loaded in edit mode")

            # Step 4: Navigate to Personal Details step to make a visible change
            print("\n4. Navigating to Personal Details step...")
            click_tab(page, "Details")
            wait_for_spinner_gone(page)
            verify_element_exists(page, "textarea.q-field__native", "Details textarea")
            take_screenshot(page, "edit_04_personal", "Personal Details step")

            # Step 5: Modify notes field
            print("\n5. Modifying notes field...")
            edit_text = f"E2E edit test {unique_suffix}"
            fill_textarea(page, "Additional Notes", edit_text)
            # Blur triggers a 300ms debounce in PersonalDetailsStep.vue that
            # commits the value to the wizard store. No DOM signal exists for
            # this -- the debounce updates local state silently before
            # saveCurrentStep() fires on tab navigation. 500ms covers the
            # 300ms debounce with margin.
            page.keyboard.press("Tab")
            page.wait_for_timeout(500)
            print(f"   [OK] Notes updated: {edit_text}")

            # Step 6: Navigate to Review and finish
            print("\n6. Navigating to Review step...")
            click_tab(page, "Review")
            wait_for_spinner_gone(page)
            verify_element_exists(page, BTN_FINISH, "Finish button")
            take_screenshot(page, "edit_06_review", "Review step")

            # Step 7: Click Finish to save
            print("\n7. Saving changes...")
            click_finish(page)
            wait_for_spinner_gone(page)

            # Step 8: Verify redirect back to same character sheet
            print("\n8. Verifying redirect to character sheet...")
            page.wait_for_url("**/characters/**", timeout=10000)
            if "/edit" in page.url:
                raise AssertionError(f"Still on edit page: {page.url}")
            assert (
                page.url == character_url
            ), f"Redirected to wrong character: expected {character_url}, got {page.url}"
            print("   [OK] Redirected to same character sheet")
            take_screenshot(page, "edit_08_saved", "Character saved")

            # Step 9: Verify the edit persisted after reload
            print("\n9. Verifying edit persisted...")
            page.reload()
            wait_for_page_load(page)
            wait_for_spinner_gone(page)

            click_tab(page, "Others")
            wait_for_spinner_gone(page)

            # Expand Biography panel if collapsed
            bio_section = page.locator('[aria-label="Biography section"]').first
            bio_classes = bio_section.get_attribute("class") or ""
            if "q-expansion-item--collapsed" in bio_classes:
                bio_section.locator('.q-item[role="button"]').first.click()
                wait_for_spinner_gone(page)

            verify_text_visible(page, edit_text)
            print(f"   [OK] Notes text visible: {edit_text}")

            take_screenshot(page, "edit_09_done", "Test complete")

            print_test_summary(
                "CHARACTER EDITING",
                [
                    "Character sheet loads",
                    "Edit mode entered",
                    "Wizard loads existing data",
                    "Personal Details step navigated",
                    "Notes field modified",
                    "Review step navigated",
                    "Changes saved via Finish",
                    "Redirected to character sheet",
                    "Edit persisted (visible in Others > Biography)",
                ],
            )
            return True

        except Exception as e:
            print(f"\n[ERROR] {e}")
            if page is not None:
                take_screenshot(page, "edit_error", "Error")
            traceback.print_exc()
            return False
        finally:
            if context is not None:
                context.close()
            browser.close()


if __name__ == "__main__":
    success = test_character_editing()
    sys.exit(0 if success else 1)
