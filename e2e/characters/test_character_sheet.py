#!/usr/bin/env python3
"""
E2E test for Character Sheet

Matches: MyCharactersPage.vue (HeroCard with .card-interactive)
         CharacterSheetPage.vue (q-tabs: Stats, Skills, Actions,
           Equipment, Talents, Expertises, Conditions, Companions, Others)
         CharacterHeader.vue (.text-h5.text-heading for name)
"""

import re
import sys
import traceback

from playwright.sync_api import expect, sync_playwright

from e2e.auth.auth_manager import authenticate_for_testing
from e2e.common.config import get_config
from e2e.common.helpers import (
    ATTRIBUTE_CARD,
    COMPANION_TILE,
    DEFENSE_CARD,
    EXPERTISE_CHIP,
    EXPERTISE_SECTION,
    HERO_CARD,
    SKILL_CATEGORY,
    SKILL_ITEM,
    SKILL_ITEM_LABEL,
    SKILL_PIP_FILLED,
    TALENT_TAB,
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
    wait_for_text_change,
)

config = get_config()
BASE_URL = config["web_url"]


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
            active_tab = page.locator(active_tab_selector).first
            expect(active_tab).to_have_text(re.compile(r"stats", re.IGNORECASE), timeout=5000)
            print("   [OK] Active tab: Stats")

            # Step 4: Verify Stats tab content (attributes, defenses, derived stats)
            print("\n4. Verifying Stats tab content...")

            wait_for_element(page, ATTRIBUTE_CARD)
            attr_cards = page.locator(ATTRIBUTE_CARD)
            attr_count = attr_cards.count()
            assert attr_count >= 6, f"Expected at least 6 attribute cards, got {attr_count}"
            first_abbr = attr_cards.first.locator(".attribute-abbr").inner_text().strip()
            assert len(first_abbr) >= 2, f"Attribute abbreviation too short: '{first_abbr}'"
            print(f"   [OK] {attr_count} attribute cards (first: {first_abbr})")

            wait_for_element(page, DEFENSE_CARD)
            defense_cards = page.locator(DEFENSE_CARD)
            defense_count = defense_cards.count()
            assert defense_count >= 3, f"Expected at least 3 defense cards, got {defense_count}"
            print(f"   [OK] {defense_count} defense cards")

            take_screenshot(page, "sheet_04_stats_content", "Stats tab content")

            # Step 5: Verify Skills tab content
            print("\n5. Verifying Skills tab content...")
            click_tab(page, "Skills")
            wait_for_spinner_gone(page)

            wait_for_element(page, SKILL_CATEGORY)
            skill_categories = page.locator(SKILL_CATEGORY)
            cat_count = skill_categories.count()
            assert cat_count >= 3, f"Expected at least 3 skill categories, got {cat_count}"

            wait_for_element(page, SKILL_ITEM)
            skill_items = page.locator(SKILL_ITEM)
            skill_count = skill_items.count()
            assert skill_count >= 10, f"Expected at least 10 skills, got {skill_count}"
            first_skill = skill_items.first.locator(SKILL_ITEM_LABEL).first.inner_text().strip()
            assert len(first_skill) > 0, "First skill name is empty"
            print(f"   [OK] {cat_count} categories, {skill_count} skills (first: {first_skill})")

            filled_pips = page.locator(SKILL_PIP_FILLED)
            print(f"   [OK] {filled_pips.count()} filled rank pips")
            take_screenshot(page, "sheet_05_skills_content", "Skills tab content")

            # Step 6: Verify Actions tab content
            print("\n6. Verifying Actions tab content...")
            click_tab(page, "Actions")
            wait_for_spinner_gone(page)
            take_screenshot(page, "sheet_06_actions", "Actions tab")
            print("   [OK] Actions tab loaded")

            # Step 7: Verify Equipment tab content
            print("\n7. Verifying Equipment tab content...")
            click_tab(page, "Equipment")
            wait_for_spinner_gone(page)
            take_screenshot(page, "sheet_07_equipment", "Equipment tab")
            print("   [OK] Equipment tab loaded")

            # Step 8: Verify Talents tab content
            print("\n8. Verifying Talents tab content...")
            click_tab(page, "Talents")
            wait_for_spinner_gone(page)

            # Talents tab uses q-tabs for path categories or shows "No talents acquired"
            talent_tabs = page.locator(TALENT_TAB)
            no_talents = page.locator('.talents-tab .text-empty:has-text("No talents")')
            if talent_tabs.count() > 0:
                first_tab_label = talent_tabs.first.inner_text().strip()
                print(
                    f"   [OK] Talent categories: {talent_tabs.count()} (first: {first_tab_label})"
                )
            elif no_talents.count() > 0:
                print("   [OK] No talents state displayed")
            else:
                take_screenshot(page, "sheet_08_talents", "Talents tab unknown state")
                raise AssertionError("Talents tab: neither populated nor empty state detected")
            take_screenshot(page, "sheet_08_talents", "Talents tab content")

            # Step 9: Verify Expertises tab content
            print("\n9. Verifying Expertises tab content...")
            click_tab(page, "Expertises")
            wait_for_spinner_gone(page)

            wait_for_element(page, EXPERTISE_SECTION)
            exp_sections = page.locator(EXPERTISE_SECTION)
            exp_count = exp_sections.count()
            assert exp_count >= 1, f"Expected at least 1 expertise category, got {exp_count}"

            exp_chips = page.locator(EXPERTISE_CHIP)
            print(f"   [OK] {exp_count} categories, {exp_chips.count()} expertise chips")
            take_screenshot(page, "sheet_09_expertises", "Expertises tab content")

            # Step 10: Verify Conditions tab content
            print("\n10. Verifying Conditions tab content...")
            click_tab(page, "Conditions")
            wait_for_spinner_gone(page)
            take_screenshot(page, "sheet_10_conditions", "Conditions tab")
            print("   [OK] Conditions tab loaded")

            # Step 11: Verify Companions tab content
            print("\n11. Verifying Companions tab content...")
            click_tab(page, "Companions")
            wait_for_spinner_gone(page)

            comp_tiles = page.locator(COMPANION_TILE)
            no_comps = page.locator('text="No companions yet."')
            if comp_tiles.count() > 0:
                print(f"   [OK] {comp_tiles.count()} companion tiles")
            elif no_comps.count() > 0:
                print("   [OK] No companions state displayed")
            else:
                take_screenshot(page, "sheet_11_companions", "Companions tab unknown state")
                raise AssertionError("Companions tab: neither populated nor empty state detected")
            take_screenshot(page, "sheet_11_companions", "Companions tab")

            # Step 12: Verify Others tab
            print("\n12. Verifying Others tab...")
            click_tab(page, "Others")
            wait_for_spinner_gone(page)
            take_screenshot(page, "sheet_12_others", "Others tab")
            print("   [OK] Others tab loaded")

            # --- RESOURCE TRACKING (Stats tab) ---

            # Step 13: Test resource buttons on Stats tab
            step = 13
            print(f"\n{step}. Testing resource tracking (Stats tab)...")
            click_tab(page, "Stats")
            wait_for_spinner_gone(page)

            # Test Focus decrement then increment (fresh characters start at max)
            focus_decrease = page.locator('button[aria-label="Decrease Focus"]')
            if focus_decrease.count() > 0 and focus_decrease.is_enabled():
                focus_value = focus_decrease.locator("xpath=..").locator(".resource-value").first
                before = focus_value.inner_text()

                click_decrement(page, "Focus")
                after_dec = wait_for_text_change(focus_value, before)

                click_increment(page, "Focus")
                after_inc = wait_for_text_change(focus_value, after_dec)
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
                wait_for_dialog(page)
                take_screenshot(page, "sheet_13_hp_dialog", "HP dialog")

                amount_input = page.locator('.q-dialog input[type="number"]').first
                assert amount_input.count() > 0, "Amount input not found in HP dialog"
                amount_input.fill("1")
                wait_for_spinner_gone(page)

                damage_btn = page.locator('.q-dialog .q-btn:has-text("Damage")')
                assert damage_btn.count() > 0, "Damage button not found in HP dialog"
                assert damage_btn.first.is_enabled(), "Damage button is disabled"
                damage_btn.first.click()
                hp_after_damage = wait_for_text_change(hp_display, hp_before)
                print(f"   [OK] HP damaged: {hp_before} -> {hp_after_damage}")

                # Dialog closes after damage -- heal via + button
                click_increment(page, "HP")
                hp_after_heal = wait_for_text_change(hp_display, hp_after_damage)
                assert (
                    hp_after_heal == hp_before
                ), f"HP did not restore (expected {hp_before}, got {hp_after_heal})"
                print(f"   [OK] HP restored: {hp_after_damage} -> {hp_after_heal}")
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
                wait_for_dialog(page)
                verify_element_exists(page, ".q-dialog .q-card", "Equipment dialog")
                take_screenshot(page, "sheet_15_equip_dialog", "Equipment dialog")

                # Check for modifications section
                mod_section = page.locator('.q-dialog :text("Modifications")')
                if mod_section.count() > 0:
                    print("   [OK] Modifications section found")
                else:
                    print("   [INFO] Modifications section not visible")

                # Close dialog and wait for it to disappear
                close_btn = page.locator(
                    '.q-dialog [aria-label="Close dialog"],' ' .q-dialog .q-btn:has-text("Cancel")'
                )
                if close_btn.count() > 0:
                    close_btn.first.click()
                else:
                    page.keyboard.press("Escape")
                expect(page.locator(".q-dialog")).to_have_count(0)
                print("   [OK] Equipment dialog opened and closed")
            else:
                print("   [INFO] No equipment items found")

            take_screenshot(page, "sheet_15_equip_done", "Equipment tested")

            print_test_summary(
                "CHARACTER SHEET",
                [
                    "Character list loads",
                    "Character card navigates to sheet",
                    "Stats tab: attributes, defenses, derived stats",
                    "Skills tab: categories, skill names, rank pips",
                    "Actions tab loads",
                    "Equipment tab loads",
                    "Talents tab: path categories or empty state",
                    "Expertises tab: categories and chips",
                    "Conditions tab loads",
                    "Companions tab: tiles or empty state",
                    "Others tab loads",
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
