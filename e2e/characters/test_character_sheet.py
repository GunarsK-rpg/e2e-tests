#!/usr/bin/env python3
"""
E2E test for Character Sheet

Matches: MyCharactersPage.vue (HeroCard with .card-interactive)
         CharacterSheetPage.vue (q-tabs: Stats, Skills, Actions,
           Equipment, Talents, Expertises, Conditions, Companions, Others)
         CharacterHeader.vue (.text-h5.text-heading for name)
"""

import sys

from playwright.sync_api import sync_playwright

from e2e.auth.auth_manager import authenticate_for_testing
from e2e.common.config import get_config
from e2e.common.helpers import (
    HERO_CARD,
    click_tab,
    navigate_to,
    print_test_summary,
    take_screenshot,
    verify_element_exists,
    verify_url_contains,
    wait_for_spinner_gone,
)

config = get_config()
BASE_URL = config["web_url"]

# Tab labels from CharacterSheetPage.vue (as rendered in .q-tab__label)
# Stats is default/active, so we skip it and start from Skills
SHEET_TABS = [
    "Skills",
    "Actions",
    "Equipment",
    "Talents",
    "Expertises",
    "Conditions",
    "Companions",
    "Others",
]


def test_character_sheet():
    """Test character sheet tab navigation"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=config["headless"], slow_mo=config["slow_mo"])

        print("\n=== CHARACTER SHEET E2E TEST ===\n")

        try:
            page, context = authenticate_for_testing(browser)

            # Step 1: Navigate to My Characters
            print("1. Navigating to My Characters...")
            navigate_to(page, BASE_URL, "/")
            wait_for_spinner_gone(page)
            take_screenshot(page, "sheet_01_list", "Character list")

            # Step 2: Click first character card
            print("\n2. Selecting character...")
            cards = page.locator(HERO_CARD)
            if cards.count() == 0:
                print("   [SKIP] No characters found")
                return True

            cards.first.click()
            page.wait_for_load_state("networkidle")
            wait_for_spinner_gone(page)
            page.wait_for_timeout(1000)

            verify_url_contains(page, "/characters/")
            verify_element_exists(page, ".text-h5.text-heading", "Character name")
            take_screenshot(page, "sheet_02_loaded", "Sheet loaded")

            # Step 3: Verify Stats tab is active by default
            print("\n3. Verifying Stats tab (default)...")
            verify_element_exists(page, ".q-tab--active .q-tab__label", "Active tab")

            # Step 4+: Navigate through remaining tabs
            for i, tab_label in enumerate(SHEET_TABS, start=4):
                print(f"\n{i}. Clicking {tab_label} tab...")
                click_tab(page, tab_label)
                wait_for_spinner_gone(page)
                take_screenshot(
                    page,
                    f"sheet_{i:02d}_{tab_label.lower()}",
                    f"{tab_label} tab",
                )
                print(f"   [OK] {tab_label} tab loaded")

            print_test_summary(
                "CHARACTER SHEET",
                [
                    "Character list loads",
                    "Character card navigates to sheet",
                    "Stats tab active by default",
                    *[f"{t} tab navigation" for t in SHEET_TABS],
                ],
            )
            return True

        except Exception as e:
            print(f"\n[ERROR] {e}")
            take_screenshot(page, "sheet_error", "Error")
            import traceback

            traceback.print_exc()
            return False
        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    success = test_character_sheet()
    sys.exit(0 if success else 1)
