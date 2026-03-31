#!/usr/bin/env python3
"""
E2E test for Character Creation Wizard

Wizard steps (CharacterCreationPage.vue):
  1. BasicSetupStep   - name, level, ancestry (SelectableCard)
  2. CultureStep      - primary culture (q-select), secondary (q-select)
  3. AttributesStep   - +/- buttons + slider (no number input)
  4. SkillsStep       - +/- buttons for rank
  5. ExpertisesStep   - q-checkbox list
  6. PathsStep        - "Add Path" btn -> dialog with q-list[role=listbox]
  7. StartingKitStep  - "Choose Starting Kit" btn -> dialog with q-list[role=listbox]
  8. EquipmentStep    - q-select dropdowns (starting kit items pre-loaded)
  9. PersonalDetailsStep - textarea fields for bio, appearance, notes
 10. ReviewStep       - summary + Finish button
"""

import sys
import time
import traceback

from playwright.sync_api import sync_playwright

from e2e.auth.auth_manager import authenticate_for_testing
from e2e.common.config import get_config
from e2e.common.helpers import (
    ATTRIBUTE_CARD,
    EXPERTISE_CHIP,
    SKILL_ITEM,
    TALENT_TAB,
    click_finish,
    click_first_checkbox,
    click_increment,
    click_increment_rank,
    click_next_step,
    click_tab,
    fill_input,
    fill_textarea,
    navigate_to,
    open_dialog_and_select_first,
    print_test_summary,
    select_first_card,
    select_first_option,
    take_screenshot,
    verify_element_exists,
    verify_text_visible,
    verify_url_contains,
    wait_for_page_load,
    wait_for_spinner_gone,
)

config = get_config()
BASE_URL = config["web_url"]


def test_character_creation():
    """Test the 10-step character creation wizard"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=config["headless"], slow_mo=config["slow_mo"])

        print("\n=== CHARACTER CREATION E2E TEST ===\n")

        page = None
        context = None
        try:
            page, context = authenticate_for_testing(browser)
            unique_suffix = str(int(time.time()))[-6:]
            character_name = f"E2E Hero {unique_suffix}"

            # Step 1: BasicSetupStep (name, level, ancestry)
            print("1. Basic Setup...")
            navigate_to(page, BASE_URL, "/characters/new")
            wait_for_spinner_gone(page)

            fill_input(page, "Character Name", character_name)
            print(f"   [OK] Name: {character_name}")

            # Ancestry uses SelectableCard (role=radio, .card-selected)
            select_first_card(page, "Ancestry")

            take_screenshot(page, "cc_01_basic", "Basic setup")
            click_next_step(page)

            # Step 2: CultureStep (q-select dropdowns)
            print("\n2. Culture...")
            wait_for_spinner_gone(page)
            select_first_option(page, "Primary Culture")
            print("   [OK] Primary culture selected")

            take_screenshot(page, "cc_02_culture", "Culture")
            click_next_step(page)

            # Step 3: AttributesStep (+/- buttons, aria-label="Increase {name}")
            print("\n3. Attributes...")
            wait_for_spinner_gone(page)

            # Increment first attribute (Strength) once
            click_increment(page, "Strength")

            take_screenshot(page, "cc_03_attributes", "Attributes")
            click_next_step(page)

            # Step 4: SkillsStep (+/- buttons, aria-label="Increase {name} rank")
            print("\n4. Skills...")
            wait_for_spinner_gone(page)

            # Increment first skill rank - Athletics is typically first
            click_increment_rank(page, "Athletics")

            take_screenshot(page, "cc_04_skills", "Skills")
            click_next_step(page)

            # Step 5: ExpertisesStep (q-checkbox in q-list)
            print("\n5. Expertises...")
            wait_for_spinner_gone(page)

            click_first_checkbox(page, "Expertise")

            take_screenshot(page, "cc_05_expertises", "Expertises")
            click_next_step(page)

            # Step 6: PathsStep (btn "Add Path" -> dialog with listbox)
            print("\n6. Paths...")
            wait_for_spinner_gone(page)

            open_dialog_and_select_first(page, "Add Path", "Heroic path")

            take_screenshot(page, "cc_06_paths", "Paths")
            click_next_step(page)

            # Step 7: StartingKitStep (btn -> dialog with listbox)
            print("\n7. Starting Kit...")
            wait_for_spinner_gone(page)

            open_dialog_and_select_first(page, "Choose Starting Kit", "Starting kit")

            take_screenshot(page, "cc_07_kit", "Starting kit")
            click_next_step(page)

            # Step 8: EquipmentStep (q-select + add buttons, items from kit)
            print("\n8. Equipment...")
            wait_for_spinner_gone(page)
            # Equipment is pre-populated from starting kit, just verify and advance
            take_screenshot(page, "cc_08_equipment", "Equipment")
            print("   [OK] Equipment step loaded")
            click_next_step(page)

            # Step 9: PersonalDetailsStep (textarea fields)
            print("\n9. Personal Details...")
            wait_for_spinner_gone(page)

            fill_textarea(page, "Biography", "Born in the wilds.")
            fill_textarea(page, "Appearance", "Tall with dark hair")
            fill_textarea(page, "Notes", "E2E test character")

            take_screenshot(page, "cc_09_personal", "Personal details")
            click_next_step(page)

            # Step 10: ReviewStep (summary + Finish)
            print("\n10. Review & Finish...")
            wait_for_spinner_gone(page)

            verify_text_visible(page, character_name)
            take_screenshot(page, "cc_10_review", "Review")

            click_finish(page)

            # Verify redirect to character sheet
            print("\n11. Verifying character sheet...")
            verify_url_contains(page, "/characters/")
            verify_text_visible(page, character_name)
            take_screenshot(page, "cc_11_sheet", "Character sheet")

            # Step 12: Verify data persists after reload
            print("\n12. Verifying data persistence after reload...")
            page.reload()
            wait_for_page_load(page)
            wait_for_spinner_gone(page)

            # Character name survives reload
            verify_text_visible(page, character_name)
            print(f"   [OK] Name persisted: {character_name}")

            # Attributes present (at least 6 cards)
            attr_cards = page.locator(ATTRIBUTE_CARD)
            assert (
                attr_cards.count() >= 6
            ), f"Expected 6+ attributes after reload, got {attr_cards.count()}"
            print(f"   [OK] {attr_cards.count()} attribute cards after reload")

            # Skills tab has data
            click_tab(page, "Skills")
            wait_for_spinner_gone(page)
            skill_items = page.locator(SKILL_ITEM)
            assert (
                skill_items.count() >= 10
            ), f"Expected 10+ skills after reload, got {skill_items.count()}"
            print(f"   [OK] {skill_items.count()} skills after reload")

            # Expertises tab has chips
            click_tab(page, "Expertises")
            wait_for_spinner_gone(page)
            exp_chips = page.locator(EXPERTISE_CHIP)
            assert exp_chips.count() >= 1, "Expected at least 1 expertise chip after reload"
            print(f"   [OK] {exp_chips.count()} expertise chips after reload")

            # Talents tab has data (from path selection)
            click_tab(page, "Talents")
            wait_for_spinner_gone(page)
            talent_tabs_loc = page.locator(TALENT_TAB)
            if talent_tabs_loc.count() > 0:
                print(f"   [OK] {talent_tabs_loc.count()} talent categories after reload")
            else:
                verify_element_exists(page, ".talents-tab", "Talents tab content")
                print("   [OK] Talents tab content present after reload")

            take_screenshot(page, "cc_12_persisted", "Data persisted after reload")

            print_test_summary(
                "CHARACTER CREATION",
                [
                    "Basic Setup - name, ancestry",
                    "Culture selection (q-select)",
                    "Attributes increment (+/- buttons)",
                    "Skills increment (+/- buttons)",
                    "Expertise selection (checkbox)",
                    "Path selection (dialog listbox)",
                    "Starting kit selection (dialog listbox)",
                    "Equipment step (pre-populated)",
                    "Personal details (textarea fields)",
                    "Review and finish",
                    "Redirect to character sheet",
                    "Data persists after reload (name, attrs, skills, expertises, talents)",
                ],
            )
            return True

        except Exception as e:
            print(f"\n[ERROR] {e}")
            if page is not None:
                take_screenshot(page, "cc_error", "Error")
            traceback.print_exc()
            return False
        finally:
            if context is not None:
                context.close()
            browser.close()


if __name__ == "__main__":
    success = test_character_creation()
    sys.exit(0 if success else 1)
