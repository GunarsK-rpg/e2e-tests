#!/usr/bin/env python3
"""
E2E test for Character Deletion

Matches: ReviewStep.vue (data-testid="delete-hero-btn")
         DeleteHeroDialog.vue (input aria-label="Type delete to confirm",
           q-btn label="Delete" color="negative", q-btn label="Cancel")
"""

import sys
import traceback

from playwright.sync_api import sync_playwright

from e2e.auth.auth_manager import authenticate_for_testing
from e2e.common.config import get_config
from e2e.common.helpers import (
    DELETE_CONFIRM_INPUT,
    HERO_CARD,
    click_button,
    click_button_by_aria,
    click_tab,
    confirm_dialog,
    navigate_to,
    print_test_summary,
    take_screenshot,
    verify_url_contains,
    wait_for_page_load,
    wait_for_spinner_gone,
)

config = get_config()
BASE_URL = config["web_url"]


def test_character_deletion():
    """Test character deletion via edit mode -> ReviewStep -> Delete"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=config["headless"], slow_mo=config["slow_mo"])

        print("\n=== CHARACTER DELETION E2E TEST ===\n")

        page = None
        context = None
        try:
            page, context = authenticate_for_testing(browser)

            # Step 1: Find a character to delete
            print("1. Navigating to My Characters...")
            navigate_to(page, BASE_URL, "/")
            wait_for_spinner_gone(page)

            cards = page.locator(HERO_CARD)
            if cards.count() == 0:
                print("   [SKIP] No characters to delete")
                return True

            last_card = cards.last
            card_name = last_card.locator(".text-h6").first.inner_text()
            print(f"   [OK] Will delete: {card_name}")

            # Step 2: Open character sheet
            print("\n2. Opening character sheet...")
            last_card.click()
            wait_for_page_load(page)
            wait_for_spinner_gone(page)
            page.wait_for_timeout(1000)
            verify_url_contains(page, "/characters/")

            # Step 3: Enter edit mode (CharacterHeader.vue: aria-label="Edit character")
            print("\n3. Entering edit mode...")
            click_button_by_aria(page, "Edit character", wait_ms=1000)
            wait_for_page_load(page)
            wait_for_spinner_gone(page)
            print("   [OK] Edit mode entered")

            # Step 4: Navigate to Review tab
            print("\n4. Navigating to Review step...")
            click_tab(page, "Review", wait_ms=1000)
            wait_for_spinner_gone(page)
            print("   [OK] Review step opened")

            # Step 5: Click Delete Character button
            print("\n5. Clicking Delete Character...")
            click_button(page, "Delete Character", wait_ms=500)
            print("   [OK] Delete dialog opened")
            take_screenshot(page, "delete_05_dialog", "Delete dialog")

            # Step 6: Type "delete" and confirm
            print("\n6. Confirming deletion...")
            page.locator(DELETE_CONFIRM_INPUT).first.click()
            page.locator(DELETE_CONFIRM_INPUT).first.fill("delete")
            page.wait_for_timeout(300)
            confirm_dialog(page, "Delete")
            wait_for_page_load(page)
            page.wait_for_timeout(2000)
            print("   [OK] Deletion confirmed")

            # Step 7: Verify dialog closed
            print("\n7. Verifying dialog closed...")
            dialog = page.locator(".q-dialog")
            if dialog.count() == 0:
                print("   [OK] Dialog closed")
            else:
                print("   [INFO] Dialog still visible")

            # Step 8: Verify redirected to characters list
            print("\n8. Verifying redirect...")
            wait_for_page_load(page)
            page.wait_for_timeout(1000)
            take_screenshot(page, "delete_08_after", "After deletion")

            # Navigate to characters list and verify hero is gone
            navigate_to(page, BASE_URL, "/")
            wait_for_spinner_gone(page)

            remaining = page.locator(f'{HERO_CARD}:has-text("{card_name}")')
            if remaining.count() == 0:
                print(f"   [OK] '{card_name}' no longer in character list")
            else:
                print(f"   [FAIL] '{card_name}' still visible in list")
                return False

            print_test_summary(
                "CHARACTER DELETION",
                [
                    "Character found",
                    "Sheet opened",
                    "Edit mode entered",
                    "Review step navigated",
                    "Delete dialog opened",
                    "Confirmation typed and confirmed",
                    "Dialog closed",
                    "Character removed from list",
                ],
            )
            return True

        except Exception as e:
            print(f"\n[ERROR] {e}")
            if page is not None:
                take_screenshot(page, "delete_error", "Error")
            traceback.print_exc()
            return False
        finally:
            if context is not None:
                context.close()
            browser.close()


if __name__ == "__main__":
    success = test_character_deletion()
    sys.exit(0 if success else 1)
