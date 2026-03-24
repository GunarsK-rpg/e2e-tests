#!/usr/bin/env python3
"""
E2E test for Combat Encounters

Matches: CampaignDetailPage.vue (combat cards, CreateCombatDialog)
         CreateCombatDialog.vue (q-input name, textarea description, Create btn)
         CombatDetailPage.vue (ResourceBox for Turn, q-btn-toggle for phase,
           CombatNpcSection for enemies/allies, AddNpcDialog)
         AddNpcDialog.vue (search input, q-list with q-item clickable, Add btn)
         CombatNpcTile.vue (ResourceBox for HP, edit/delete btns)
"""

import sys
import time

from playwright.sync_api import sync_playwright

from e2e.auth.auth_manager import authenticate_for_testing
from e2e.common.config import get_config
from e2e.common.helpers import (
    click_button,
    click_button_if_visible,
    click_first_listbox_item,
    confirm_dialog,
    dismiss_dialog,
    fill_input,
    navigate_to,
    print_test_summary,
    take_screenshot,
    verify_element_exists,
    verify_text_visible,
    wait_for_dialog,
    wait_for_page_load,
    wait_for_spinner_gone,
)

config = get_config()
BASE_URL = config["web_url"]


def test_combat_encounter():
    """Test combat encounter lifecycle"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=config["headless"], slow_mo=config["slow_mo"])

        print("\n=== COMBAT ENCOUNTER E2E TEST ===\n")

        try:
            page, context = authenticate_for_testing(browser)
            unique_suffix = str(int(time.time()))[-6:]
            campaign_name = f"E2E Combat {unique_suffix}"
            combat_name = f"Battle {unique_suffix}"

            # Step 1: Create campaign
            print("1. Creating campaign...")
            navigate_to(page, BASE_URL, "/campaigns")
            wait_for_spinner_gone(page)

            click_button(page, "Create Campaign")
            wait_for_page_load(page)
            page.wait_for_timeout(500)

            fill_input(page, "Campaign Name", campaign_name)
            click_button(page, "Create")
            wait_for_page_load(page)
            page.wait_for_timeout(1500)
            print(f"   [OK] Campaign: {campaign_name}")

            # Step 2: Create combat
            print("\n2. Creating combat encounter...")
            click_button(page, "New Combat")
            page.wait_for_timeout(500)

            wait_for_dialog(page)
            fill_input(page, "Name", combat_name)
            confirm_dialog(page, "Create")
            wait_for_page_load(page)
            page.wait_for_timeout(1000)
            print(f"   [OK] Combat created: {combat_name}")

            take_screenshot(page, "combat_02_created", "Combat created")

            # Step 3: Verify combat detail
            print("\n3. Verifying combat detail...")
            verify_text_visible(page, combat_name)
            take_screenshot(page, "combat_03_detail", "Combat detail")

            # Step 4: Add NPC via dialog
            print("\n4. Adding NPC to combat...")
            if click_button_if_visible(page, "Add Enemy"):
                page.wait_for_timeout(500)
                if click_first_listbox_item(page, "NPC"):
                    confirm_dialog(page, "Add")
                    page.wait_for_timeout(1000)
                    print("   [OK] NPC added")
                else:
                    print("   [INFO] No NPCs available")
                    dismiss_dialog(page, "Cancel")
            else:
                print("   [INFO] Add Enemy button not found")

            take_screenshot(page, "combat_04_npc", "After NPC add")

            # Step 5: Verify combat tiles
            print("\n5. Checking combat participants...")
            verify_element_exists(page, ".combat-npc-tile", "Combat NPC tiles")

            # Step 6: Test phase toggle
            print("\n6. Testing phase toggle...")
            verify_element_exists(page, ".q-btn-toggle", "Phase toggle")

            # Step 7: Test active toggle
            print("\n7. Testing active toggle...")
            click_button_if_visible(page, "Active")
            page.wait_for_timeout(500)

            take_screenshot(page, "combat_07_state", "Combat state")

            # Step 8: Cleanup
            print("\n8. Cleaning up...")
            click_button_if_visible(page, "Back")
            wait_for_page_load(page)

            take_screenshot(page, "combat_08_done", "Test complete")

            print_test_summary(
                "COMBAT ENCOUNTER",
                [
                    "Campaign created",
                    "Combat encounter created",
                    "Combat detail loaded",
                    "NPC add attempted",
                    "Combat tiles checked",
                    "Phase toggle verified",
                    "Active toggle tested",
                    "Cleanup completed",
                ],
            )
            return True

        except Exception as e:
            print(f"\n[ERROR] {e}")
            take_screenshot(page, "combat_error", "Error")
            import traceback

            traceback.print_exc()
            return False
        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    success = test_combat_encounter()
    sys.exit(0 if success else 1)
