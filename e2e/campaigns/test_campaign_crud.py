#!/usr/bin/env python3
"""
E2E test for Campaign CRUD

Matches: CampaignsPage.vue (q-btn "Create Campaign" with Plus icon)
         CampaignFormPage.vue (q-input "Campaign Name", textarea "Description",
           number inputs for modifier fields, Cancel/Create buttons)
         CampaignDetailPage.vue (edit btn Pencil, delete btn Trash2,
           invite link with Copy icon)
"""

import sys
import time
import traceback

from playwright.sync_api import sync_playwright

from e2e.auth.auth_manager import authenticate_for_testing
from e2e.common.config import get_config
from e2e.common.helpers import (
    click_button,
    click_button_by_aria,
    confirm_dialog,
    fill_input,
    fill_textarea,
    navigate_to,
    print_test_summary,
    take_screenshot,
    verify_text_visible,
    verify_url_contains,
    wait_for_page_load,
    wait_for_spinner_gone,
)

config = get_config()
BASE_URL = config["web_url"]

# Wait durations (ms) for UI transitions
WAIT_SHORT = 500


def test_campaign_crud():
    """Test campaign create, edit, and delete"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=config["headless"], slow_mo=config["slow_mo"])

        print("\n=== CAMPAIGN CRUD E2E TEST ===\n")

        page = None
        context = None
        try:
            page, context = authenticate_for_testing(browser)
            unique_suffix = str(int(time.time()))[-6:]
            campaign_name = f"E2E Campaign {unique_suffix}"
            updated_desc = f"Updated desc {unique_suffix}"

            # Step 1: Navigate to campaigns
            print("1. Navigating to campaigns...")
            navigate_to(page, BASE_URL, "/campaigns")
            wait_for_spinner_gone(page)
            print("   [OK] Campaigns page loaded")

            # Step 2: Create campaign
            print("\n2. Creating campaign...")
            click_button(page, "Create Campaign")
            wait_for_page_load(page)

            fill_input(page, "Campaign Name", campaign_name)
            fill_textarea(page, "Description", f"Test campaign {unique_suffix}")
            print(f"   [OK] Name: {campaign_name}")
            take_screenshot(page, "campaign_02_form", "Campaign form")

            # Step 3: Save
            print("\n3. Saving campaign...")
            click_button(page, "Create")
            wait_for_page_load(page)
            print("   [OK] Campaign created")

            # Step 4: Verify detail page
            print("\n4. Verifying campaign detail...")
            assert verify_text_visible(
                page, campaign_name
            ), f"Campaign '{campaign_name}' not visible"
            verify_url_contains(page, "/campaigns/")
            take_screenshot(page, "campaign_04_detail", "Campaign detail")

            # Step 5: Edit (pencil button aria-label)
            print("\n5. Editing campaign...")
            click_button_by_aria(page, "Edit campaign")
            wait_for_page_load(page)

            fill_textarea(page, "Description", updated_desc)
            click_button(page, "Save")
            wait_for_page_load(page)
            print("   [OK] Campaign updated")

            # Step 6: Verify update
            print("\n6. Verifying update...")
            assert verify_text_visible(page, updated_desc), "Updated description not visible"

            # Step 7: Delete (trash button aria-label)
            print("\n7. Deleting campaign...")
            click_button_by_aria(page, "Delete campaign")
            page.wait_for_timeout(WAIT_SHORT)
            confirm_dialog(page, "OK")
            wait_for_page_load(page)
            print("   [OK] Campaign deleted")

            # Step 8: Verify redirect
            print("\n8. Verifying redirect...")
            verify_url_contains(page, "/campaigns")
            take_screenshot(page, "campaign_08_deleted", "After delete")

            print_test_summary(
                "CAMPAIGN CRUD",
                [
                    "Campaigns page loads",
                    "Campaign form fills",
                    "Campaign creates",
                    "Detail page shows campaign",
                    "Campaign edits",
                    "Updated description visible",
                    "Campaign deletes",
                    "Redirect to campaigns list",
                ],
            )
            return True

        except Exception as e:
            print(f"\n[ERROR] {e}")
            if page is not None:
                take_screenshot(page, "campaign_error", "Error")
            traceback.print_exc()
            return False
        finally:
            if context is not None:
                context.close()
            browser.close()


if __name__ == "__main__":
    success = test_campaign_crud()
    sys.exit(0 if success else 1)
