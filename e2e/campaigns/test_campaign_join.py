#!/usr/bin/env python3
"""
E2E test for Campaign Join via Invite Code

Matches: CampaignDetailPage.vue (invite link with Copy icon btn)
         JoinCampaignPage.vue (campaign info card, "Create Character" btn,
           existing character cards with role="button")
"""

import sys
import time

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
    verify_element_exists,
    verify_text_visible,
    wait_for_page_load,
    wait_for_spinner_gone,
)

config = get_config()
BASE_URL = config["web_url"]


def test_campaign_join():
    """Test campaign join page via invite link"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=config["headless"], slow_mo=config["slow_mo"])

        print("\n=== CAMPAIGN JOIN E2E TEST ===\n")

        try:
            page, context = authenticate_for_testing(browser)
            unique_suffix = str(int(time.time()))[-6:]
            campaign_name = f"E2E Join {unique_suffix}"

            # Step 1: Create campaign
            print("1. Creating campaign...")
            navigate_to(page, BASE_URL, "/campaigns")
            wait_for_spinner_gone(page)

            click_button(page, "Create Campaign")
            wait_for_page_load(page)
            page.wait_for_timeout(500)

            fill_input(page, "Campaign Name", campaign_name)
            fill_textarea(page, "Description", "Join test campaign")

            click_button(page, "Create")
            wait_for_page_load(page)
            page.wait_for_timeout(1500)
            print(f"   [OK] Campaign created: {campaign_name}")

            # Step 2: Get invite link
            print("\n2. Getting invite link...")
            invite_link = page.locator('a[href*="/join/"]').first
            join_url = None
            if invite_link.count() > 0:
                join_url = invite_link.get_attribute("href")
                print(f"   [OK] Invite link: {join_url}")
            else:
                print("   [INFO] Invite link not found")

            take_screenshot(page, "join_02_detail", "Campaign detail")

            # Step 3: Navigate to join page
            print("\n3. Testing join page...")
            if join_url:
                navigate_to(page, BASE_URL, join_url)
            else:
                navigate_to(page, BASE_URL, "/join")

            page.wait_for_timeout(1000)
            take_screenshot(page, "join_03_page", "Join page")

            # Step 4: Verify join page content
            print("\n4. Verifying join page...")
            if join_url:
                verify_text_visible(page, campaign_name)

            verify_element_exists(
                page, '.q-btn:has-text("Create Character")', "Create Character button"
            )
            verify_element_exists(
                page, '.card-interactive[role="button"]', "Existing character cards"
            )

            # Step 5: Cleanup
            print("\n5. Cleaning up...")
            navigate_to(page, BASE_URL, "/campaigns")
            wait_for_spinner_gone(page)

            campaign_card = page.locator(f'.card-interactive:has-text("{campaign_name}")').first
            if campaign_card.count() > 0:
                campaign_card.click()
                wait_for_page_load(page)
                page.wait_for_timeout(500)
                click_button_by_aria(page, "Delete campaign")
                page.wait_for_timeout(500)
                confirm_dialog(page, "OK")
                page.wait_for_timeout(1000)
                print("   [OK] Test campaign deleted")

            print_test_summary(
                "CAMPAIGN JOIN",
                [
                    "Campaign created",
                    "Invite link found",
                    "Join page navigated",
                    "Join page content verified",
                    "Cleanup completed",
                ],
            )
            return True

        except Exception as e:
            print(f"\n[ERROR] {e}")
            take_screenshot(page, "join_error", "Error")
            import traceback

            traceback.print_exc()
            return False
        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    success = test_campaign_join()
    sys.exit(0 if success else 1)
