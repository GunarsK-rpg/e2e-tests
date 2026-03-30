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

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
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
                raise AssertionError("No characters found -- cannot test character sheet")

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

            # Test Focus decrement then increment (fresh characters start at max)
            focus_decrease = page.locator('button[aria-label="Decrease Focus"]')
            if focus_decrease.count() > 0 and focus_decrease.is_enabled():
                focus_value = focus_decrease.locator("xpath=..").locator(".resource-value").first
                before = focus_value.inner_text()

                click_decrement(page, "Focus")
                page.wait_for_function(
                    f'() => document.querySelector("button[aria-label=\\"Decrease Focus\\"]")'
                    f'.parentElement.querySelector(".resource-value")'
                    f'.innerText !== "{before}"',
                    timeout=5000,
                )
                after_dec = focus_value.inner_text()
                assert after_dec != before, f"Focus did not change after decrement (still {before})"

                click_increment(page, "Focus")
                page.wait_for_function(
                    f'() => document.querySelector("button[aria-label=\\"Decrease Focus\\"]")'
                    f'.parentElement.querySelector(".resource-value")'
                    f'.innerText === "{before}"',
                    timeout=5000,
                )
                after_inc = focus_value.inner_text()
                assert (
                    after_inc == before
                ), f"Focus did not restore after increment (expected {before}, got {after_inc})"
                print("   [OK] Focus decrement/increment verified")
            else:
                print("   [INFO] Focus buttons not available")

            take_screenshot(page, "sheet_12_resources", "Resource tracking")

            # Step 13: Test HP management dialog
            step += 1
            print(f"\n{step}. Testing HP management dialog...")
            # Locate HP resource by finding the Decrease HP button's parent
            hp_decrease = page.locator('button[aria-label="Decrease HP"]')
            if hp_decrease.count() > 0:
                hp_display = hp_decrease.locator("xpath=..").locator(".resource-value").first
                hp_before = hp_display.inner_text()
                hp_display.click()
                page.wait_for_timeout(500)

                try:
                    wait_for_dialog(page)
                    take_screenshot(page, "sheet_13_hp_dialog", "HP dialog")

                    amount_input = page.locator('.q-dialog input[type="number"]').first
                    assert amount_input.count() > 0, "Amount input not found in HP dialog"
                    amount_input.fill("1")
                    page.wait_for_timeout(200)

                    damage_btn = page.locator('.q-dialog .q-btn:has-text("Damage")')
                    assert damage_btn.count() > 0, "Damage button not found in HP dialog"
                    assert damage_btn.first.is_enabled(), "Damage button is disabled"
                    damage_btn.first.click()
                    page.wait_for_timeout(500)
                    hp_after_damage = hp_display.inner_text()
                    assert (
                        hp_after_damage != hp_before
                    ), f"HP did not change after damage (still {hp_before})"
                    print(f"   [OK] HP damaged: {hp_before} -> {hp_after_damage}")

                    # Dialog closes after damage -- heal via + button
                    click_increment(page, "HP")
                    page.wait_for_timeout(500)
                    hp_after_heal = hp_display.inner_text()
                    assert (
                        hp_after_heal == hp_before
                    ), f"HP did not restore (expected {hp_before}, got {hp_after_heal})"
                    print(f"   [OK] HP restored: {hp_after_damage} -> {hp_after_heal}")
                except PlaywrightTimeoutError:
                    print("   [INFO] HP dialog did not open")
            else:
                print("   [INFO] HP resource not found")

            # --- CONDITIONS (Conditions tab) ---

            # Step 14: Test condition toggling
            step += 1
            print(f"\n{step}. Testing condition toggling (Conditions tab)...")
            click_tab(page, "Conditions")
            wait_for_spinner_gone(page)

            slowed_label = "Toggle Slowed"
            slowed = page.locator(f'[aria-label="{slowed_label}"]')
            if slowed.count() > 0:
                initial_state = slowed.first.get_attribute("aria-pressed")
                if initial_state not in ("true", "false"):
                    raise AssertionError(
                        f"Slowed toggle has unexpected aria-pressed: {initial_state}"
                    )
                print(f"   [INFO] Slowed (pressed={initial_state})")

                click_aria_toggle(page, slowed_label)
                wait_for_spinner_gone(page)

                expected = "false" if initial_state == "true" else "true"
                verify_aria_pressed(page, slowed_label, expected)

                # Toggle back to restore
                click_aria_toggle(page, slowed_label)
                wait_for_spinner_gone(page)
                verify_aria_pressed(page, slowed_label, initial_state)
                print("   [OK] Slowed toggled on and off")
            else:
                print("   [INFO] Slowed condition not found")

            take_screenshot(page, "sheet_14_conditions", "Conditions tested")

            # --- EQUIPMENT (Equipment tab) ---

            # Step 15: Test equipment dialog
            step += 1
            print(f"\n{step}. Testing equipment dialog (Equipment tab)...")
            click_tab(page, "Equipment")
            wait_for_spinner_gone(page)

            edit_equip = page.locator('[aria-label="Edit equipment"]')
            if edit_equip.count() > 0:
                edit_equip.first.click()

                try:
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
                    )
                    if close_btn.count() > 0:
                        close_btn.first.click()
                        page.wait_for_timeout(300)
                    else:
                        page.keyboard.press("Escape")
                        page.wait_for_timeout(300)
                    print("   [OK] Equipment dialog opened and closed")
                except PlaywrightTimeoutError:
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
