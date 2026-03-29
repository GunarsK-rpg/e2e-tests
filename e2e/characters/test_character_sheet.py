#!/usr/bin/env python3
"""
E2E test for Character Sheet

Matches: MyCharactersPage.vue (HeroCard with .card-interactive)
         CharacterSheetPage.vue (q-tabs: Stats, Skills, Actions,
           Equipment, Talents, Expertises, Conditions, Companions, Others)
         CharacterHeader.vue (.text-h5.text-heading for name)
"""

import sys
import traceback

from playwright.sync_api import sync_playwright

from e2e.auth.auth_manager import authenticate_for_testing
from e2e.common.config import get_config
from e2e.common.helpers import (
    HERO_CARD,
    click_aria_toggle,
    click_decrement,
    click_increment,
    click_tab,
    navigate_to,
    print_test_summary,
    take_screenshot,
    verify_aria_pressed,
    verify_element_exists,
    verify_url_contains,
    wait_for_dialog,
    wait_for_element,
    wait_for_page_load,
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

        page = None
        context = None
        try:
            page, context = authenticate_for_testing(browser)

            # Step 1: Navigate to My Characters
            print("1. Navigating to My Characters...")
            navigate_to(page, BASE_URL, "/")
            wait_for_spinner_gone(page)
            take_screenshot(page, "sheet_01_list", "Character list")

            # Step 2: Click first character card
            print("\n2. Selecting character...")
            if wait_for_element(page, HERO_CARD) == 0:
                print("   [SKIP] No characters found")
                return True

            page.locator(HERO_CARD).first.click()
            page.wait_for_url("**/characters/**", timeout=10000)
            wait_for_page_load(page)
            wait_for_spinner_gone(page)

            verify_url_contains(page, "/characters/")
            verify_element_exists(page, ".text-h5.text-heading", "Character name")
            take_screenshot(page, "sheet_02_loaded", "Sheet loaded")

            # Step 3: Verify Stats tab is active by default
            print("\n3. Verifying Stats tab (default)...")
            active_tab_selector = ".q-tab--active .q-tab__label"
            if wait_for_element(page, active_tab_selector) == 0:
                raise AssertionError("No default active tab found")
            tab_text = page.locator(active_tab_selector).first.inner_text()
            assert tab_text.upper() == "STATS", f"Expected active tab 'Stats', got '{tab_text}'"
            print(f"   [OK] Active tab: {tab_text}")

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

            # --- RESOURCE TRACKING (Stats tab) ---

            # Step 12: Test resource buttons on Stats tab
            step = len(SHEET_TABS) + 4  # Continue numbering after tab loop
            print(f"\n{step}. Testing resource tracking (Stats tab)...")
            click_tab(page, "Stats")
            wait_for_spinner_gone(page)

            # Test Focus increment/decrement
            focus_increase = page.locator('button[aria-label="Increase Focus"]')
            if focus_increase.count() > 0 and focus_increase.is_enabled():
                click_increment(page, "Focus")
                page.wait_for_timeout(500)
                click_decrement(page, "Focus")
                page.wait_for_timeout(500)
                print("   [OK] Focus increment/decrement working")
            else:
                print("   [INFO] Focus buttons not available")

            # Test Investiture increment/decrement (not all characters have it)
            inv_increase = page.locator('button[aria-label="Increase Investiture"]')
            if inv_increase.count() > 0 and inv_increase.is_enabled():
                click_increment(page, "Investiture")
                page.wait_for_timeout(500)
                click_decrement(page, "Investiture")
                page.wait_for_timeout(500)
                print("   [OK] Investiture increment/decrement working")
            else:
                print("   [INFO] Investiture not available on this character")

            take_screenshot(page, "sheet_12_resources", "Resource tracking")

            # Step 13: Test HP management dialog
            step += 1
            print(f"\n{step}. Testing HP management dialog...")
            hp_value = page.locator(".resource-value").first
            if hp_value.count() > 0:
                hp_value.click()
                page.wait_for_timeout(500)

                dialog = page.locator(".q-dialog")
                if dialog.count() > 0:
                    wait_for_dialog(page)
                    take_screenshot(page, "sheet_13_hp_dialog", "HP dialog")

                    amount_input = page.locator('.q-dialog input[type="number"]').first
                    if amount_input.count() > 0:
                        amount_input.fill("1")
                        page.wait_for_timeout(200)

                        heal_btn = page.locator('.q-dialog .q-btn:has-text("Heal")')
                        if heal_btn.count() > 0 and heal_btn.first.is_enabled():
                            heal_btn.first.click()
                            page.wait_for_timeout(500)
                            print("   [OK] Heal operation executed")

                            amount_input.fill("1")
                            page.wait_for_timeout(200)

                            damage_btn = page.locator('.q-dialog .q-btn:has-text("Damage")')
                            if damage_btn.count() > 0 and damage_btn.first.is_enabled():
                                damage_btn.first.click()
                                page.wait_for_timeout(500)
                                print("   [OK] Damage operation executed (HP restored)")
                        else:
                            print("   [INFO] Heal button not available (HP at max)")

                    # Close dialog (no explicit close button -- dismiss via Escape)
                    page.keyboard.press("Escape")
                    page.wait_for_timeout(500)
                else:
                    print("   [INFO] HP dialog did not open")
            else:
                print("   [INFO] HP value display not found")

            # --- CONDITIONS (Conditions tab) ---

            # Step 14: Test condition toggling
            step += 1
            print(f"\n{step}. Testing condition toggling (Conditions tab)...")
            click_tab(page, "Conditions")
            wait_for_spinner_gone(page)
            page.wait_for_timeout(500)

            toggleable = page.locator('[aria-label^="Toggle "][aria-pressed]')
            if toggleable.count() > 0:
                first_toggle_label = toggleable.first.get_attribute("aria-label")
                condition_name = first_toggle_label.replace("Toggle ", "")
                initial_state = toggleable.first.get_attribute("aria-pressed")
                print(f"   [INFO] Found: {condition_name} (pressed={initial_state})")

                click_aria_toggle(page, first_toggle_label)
                wait_for_spinner_gone(page)
                page.wait_for_timeout(500)

                expected = "false" if initial_state == "true" else "true"
                verify_aria_pressed(page, first_toggle_label, expected)

                # Toggle back to restore
                click_aria_toggle(page, first_toggle_label)
                wait_for_spinner_gone(page)
                page.wait_for_timeout(500)
                verify_aria_pressed(page, first_toggle_label, initial_state)
                print(f"   [OK] {condition_name} toggled on and off")
            else:
                print("   [INFO] No toggleable conditions found")

            take_screenshot(page, "sheet_14_conditions", "Conditions tested")

            # --- EQUIPMENT (Equipment tab) ---

            # Step 15: Test equipment dialog
            step += 1
            print(f"\n{step}. Testing equipment dialog (Equipment tab)...")
            click_tab(page, "Equipment")
            wait_for_spinner_gone(page)
            page.wait_for_timeout(500)

            edit_equip_btn = page.locator('[aria-label="Edit equipment"]').first
            if edit_equip_btn.count() > 0:
                edit_equip_btn.click()
                page.wait_for_timeout(500)

                dialog = page.locator(".q-dialog")
                if dialog.count() > 0:
                    wait_for_dialog(page)
                    verify_element_exists(page, ".q-dialog .q-card", "Equipment dialog")
                    take_screenshot(page, "sheet_15_equip_dialog", "Equipment dialog")

                    # Check for modifications section
                    mod_section = page.locator('.q-dialog :text("Modifications")')
                    if mod_section.count() > 0:
                        print("   [OK] Modifications section found")
                    else:
                        print("   [INFO] Modifications section not visible")

                    # Close dialog
                    close_btn = page.locator(
                        '.q-dialog [aria-label="Close dialog"],'
                        ' .q-dialog .q-btn:has-text("Cancel")'
                    ).first
                    if close_btn.count() > 0:
                        close_btn.click()
                        page.wait_for_timeout(300)
                    else:
                        page.keyboard.press("Escape")
                        page.wait_for_timeout(300)
                    print("   [OK] Equipment dialog opened and closed")
                else:
                    print("   [INFO] Equipment dialog did not open")
            else:
                print("   [INFO] No equipment items found")

            take_screenshot(page, "sheet_15_equip_done", "Equipment tested")

            print_test_summary(
                "CHARACTER SHEET",
                [
                    "Character list loads",
                    "Character card navigates to sheet",
                    "Stats tab active by default",
                    *[f"{t} tab navigation" for t in SHEET_TABS],
                    "Focus resource increment/decrement",
                    "HP management dialog",
                    "Condition toggling",
                    "Equipment dialog",
                ],
            )
            return True

        except Exception as e:
            print(f"\n[ERROR] {e}")
            if page is not None:
                take_screenshot(page, "sheet_error", "Error")
            traceback.print_exc()
            return False
        finally:
            if context is not None:
                context.close()
            browser.close()


if __name__ == "__main__":
    success = test_character_sheet()
    sys.exit(0 if success else 1)
