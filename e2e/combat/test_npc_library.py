#!/usr/bin/env python3
"""
E2E test for NPC Library

Matches: CampaignDetailPage.vue (CampaignNpcList at bottom)
         CampaignNpcList.vue ("Create NPC" btn, search input, q-virtual-scroll
           with q-item clickable, filter chips)
         NpcDetailPage.vue (NpcStatBlock for edit, Save/Cancel buttons)
         NpcStatBlock.vue (q-input Name, q-select Tier/Type/Size,
           ResourcesBar for HP/Focus/Investiture)
"""

import sys
import time
import traceback

from playwright.sync_api import sync_playwright

from e2e.auth.auth_manager import authenticate_for_testing
from e2e.common.config import get_config
from e2e.common.helpers import (
    cleanup_test_campaign,
    click_button,
    confirm_dialog,
    fill_input,
    navigate_to,
    print_test_summary,
    select_first_option,
    take_screenshot,
    verify_element_exists,
    verify_text_visible,
    wait_for_dialog,
    wait_for_element,
    wait_for_page_load,
    wait_for_spinner_gone,
)

config = get_config()
BASE_URL = config["web_url"]


def test_npc_library():
    """Test NPC create, edit, and archive within a campaign"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=config["headless"], slow_mo=config["slow_mo"])

        print("\n=== NPC LIBRARY E2E TEST ===\n")

        page = None
        context = None
        campaign_name = None
        try:
            page, context = authenticate_for_testing(browser)
            unique_suffix = str(int(time.time()))[-6:]
            campaign_name = f"E2E NPC {unique_suffix}"
            npc_name = f"Test Goblin {unique_suffix}"
            updated_name = f"Test Orc {unique_suffix}"

            # Step 1: Create campaign
            print("1. Creating campaign...")
            navigate_to(page, BASE_URL, "/campaigns")
            wait_for_spinner_gone(page)

            click_button(page, "Create Campaign")
            wait_for_page_load(page)

            fill_input(page, "Campaign Name", campaign_name)
            click_button(page, "Create")
            wait_for_page_load(page)
            print(f"   [OK] Campaign: {campaign_name}")

            # Step 2: Create NPC
            print("\n2. Creating NPC...")
            click_button(page, "Create NPC")
            wait_for_page_load(page)
            print("   [OK] NPC creation page opened")

            # Step 3: Fill NPC form (requires name, tier, type, size)
            print("\n3. Filling NPC form...")
            fill_input(page, "Name", npc_name)
            select_first_option(page, "Tier")
            select_first_option(page, "Type")
            select_first_option(page, "Size")
            print(f"   [OK] Name: {npc_name}")
            take_screenshot(page, "npc_03_form", "NPC form")

            # Step 4: Save NPC
            print("\n4. Saving NPC...")
            click_button(page, "Save")
            wait_for_page_load(page)
            wait_for_spinner_gone(page)
            print("   [OK] NPC saved")

            # Step 5: Search for NPC in virtual scroll list
            print("\n5. Searching for NPC...")
            verify_element_exists(
                page, '.q-field:has(.q-field__label:has-text("Search NPCs"))', "Search field"
            )
            fill_input(page, "Search NPCs", npc_name)

            npc_selector = f'.q-item:has-text("{npc_name}")'
            if wait_for_element(page, npc_selector) == 0:
                take_screenshot(page, "npc_04_not_found", "NPC not found")
                raise AssertionError(f"NPC not found in list: {npc_name}")
            print(f"   [OK] NPC found: {npc_name}")

            take_screenshot(page, "npc_05_found", "NPC in list")

            # Step 6: Click NPC to view detail
            print("\n6. Viewing NPC detail...")
            page.locator(npc_selector).first.click()
            wait_for_page_load(page)
            print("   [OK] NPC detail loaded")
            take_screenshot(page, "npc_06_detail", "NPC detail")

            # Step 7: Edit NPC name
            print("\n7. Editing NPC...")
            click_button(page, "Edit")
            wait_for_spinner_gone(page)

            fill_input(page, "Name", updated_name)
            print(f"   [OK] Name changed to: {updated_name}")

            click_button(page, "Save")
            wait_for_spinner_gone(page)
            print("   [OK] NPC updated")

            # Step 8: Verify updated name (stays on detail page after edit-save)
            print("\n8. Verifying update...")
            verify_text_visible(page, updated_name)

            # Step 9: Archive NPC
            print("\n9. Archiving NPC...")
            click_button(page, "Archive")
            wait_for_dialog(page)
            confirm_dialog(page, "OK")
            print("   [OK] NPC archived")

            take_screenshot(page, "npc_09_archived", "After archive")

            print_test_summary(
                "NPC LIBRARY",
                [
                    "Campaign created",
                    "NPC creation page opened",
                    "NPC form filled",
                    "NPC saved",
                    "NPC visible in list",
                    "NPC detail loaded",
                    "NPC name edited",
                    "Updated name verified",
                    "NPC archived",
                ],
            )

        except Exception as e:
            print(f"\n[ERROR] {e}")
            if page is not None:
                take_screenshot(page, "npc_error", "Error")
            traceback.print_exc()
            raise
        finally:
            if page is not None and campaign_name:
                cleanup_test_campaign(page, BASE_URL, campaign_name)
            if context is not None:
                context.close()
            browser.close()


if __name__ == "__main__":
    try:
        test_npc_library()
    except Exception:
        sys.exit(1)
