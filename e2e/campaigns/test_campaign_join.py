#!/usr/bin/env python3
"""
E2E test for Campaign Join via Invite Code

Matches: CampaignDetailPage.vue (invite link with Copy icon btn)
         JoinCampaignPage.vue (campaign info card, "Create Character" btn,
           existing character cards with role="button")
"""

import sys
import time
import traceback

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import expect, sync_playwright

from e2e.auth.auth_manager import authenticate_for_testing
from e2e.common.config import get_config
from e2e.common.helpers import (
    cleanup_test_campaign,
    click_button,
    confirm_dialog,
    fill_input,
    fill_textarea,
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


def test_campaign_join():
    """Test campaign join page via invite link"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=config["headless"], slow_mo=config["slow_mo"])

        print("\n=== CAMPAIGN JOIN E2E TEST ===\n")

        page = None
        context = None
        campaign_name = None
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

            fill_input(page, "Campaign Name", campaign_name)
            fill_textarea(page, "Description", "Join test campaign")

            click_button(page, "Create")
            wait_for_page_load(page)
            print(f"   [OK] Campaign created: {campaign_name}")

            # Step 2: Get invite link
            print("\n2. Getting invite link...")
            invite_link = page.locator('a[href*="/join/"]').first
            invite_link.wait_for(state="visible", timeout=10000)
            join_url = invite_link.get_attribute("href")
            if not join_url:
                raise AssertionError("Invite link visible but href attribute is missing")
            print(f"   [OK] Invite link: {join_url}")

            take_screenshot(page, "join_02_detail", "Campaign detail")

            # Step 3: Navigate to join page
            print("\n3. Testing join page...")
            navigate_to(page, BASE_URL, join_url)
            wait_for_page_load(page)
            wait_for_spinner_gone(page)

            take_screenshot(page, "join_03_page", "Join page")

            # Step 4: Verify join page content
            print("\n4. Verifying join page...")
            verify_text_visible(page, campaign_name)

            verify_element_exists(
                page, '.q-btn:has-text("Create Character")', "Create Character button"
            )
            char_cards = page.locator('.card-interactive[role="button"]')
            if char_cards.count() > 0:
                print(f"   [OK] Existing character cards: {char_cards.count()}")

            # --- HERO ASSIGNMENT ---

            # Step 5: Assign a character to the campaign
            print("\n5. Assigning character to campaign...")
            character_assigned = False
            hero_removed = False
            char_cards = page.locator('.card-interactive[role="button"]')
            if char_cards.count() > 0:
                char_cards.first.click()

                # Confirm assignment if dialog appears
                dialog_appeared = False
                try:
                    wait_for_dialog(page, timeout=3000)
                    dialog_appeared = True
                except PlaywrightTimeoutError:
                    pass  # No dialog -- assignment may not require confirmation

                if dialog_appeared:
                    confirm_dialog(page, "OK")

                wait_for_page_load(page)
                wait_for_spinner_gone(page)

                # Assignment redirects to character sheet -- verify redirect
                page.wait_for_url("**/characters/**", timeout=10000)
                print("   [OK] Character assignment submitted (redirected to sheet)")
                take_screenshot(page, "join_05_assigned", "Character assigned")

                # Step 6: Navigate to campaign detail to verify hero
                print("\n6. Verifying hero in campaign detail...")
                navigate_to(page, BASE_URL, "/campaigns")
                wait_for_spinner_gone(page)

                campaign_card = page.locator(f'.card-interactive:has-text("{campaign_name}")')
                if campaign_card.count() == 0:
                    raise AssertionError(f"Campaign '{campaign_name}' not found in list")
                campaign_card.first.click()
                wait_for_page_load(page)
                wait_for_spinner_gone(page)

                # Verify hero is shown on campaign detail (wait for async load)
                remove_locator = page.locator('[aria-label*="Remove"][aria-label*="from campaign"]')
                remove_locator.first.wait_for(state="visible", timeout=10000)
                assert (
                    remove_locator.count() > 0
                ), "Hero not visible on campaign detail after assignment"
                character_assigned = True
                print("   [OK] Hero confirmed on campaign detail")
                take_screenshot(page, "join_06_detail", "Campaign with hero")

                # --- HERO REMOVAL ---

                # Step 7: Remove hero from campaign
                print("\n7. Removing hero from campaign...")
                remove_locator = page.locator('[aria-label*="Remove"][aria-label*="from campaign"]')
                if remove_locator.count() > 0:
                    remove_locator.first.click()

                    # Step 8: Confirm removal dialog
                    print("\n8. Confirming removal...")
                    wait_for_dialog(page)
                    verify_text_visible(page, "Remove Character")
                    take_screenshot(page, "join_08_confirm", "Removal confirmation")
                    confirm_dialog(page, "OK")
                    wait_for_spinner_gone(page)
                    hero_removed = True
                    print("   [OK] Hero removed from campaign")

                    # Step 9: Verify hero removed
                    print("\n9. Verifying hero removed...")
                    remaining = page.locator('[aria-label*="Remove"][aria-label*="from campaign"]')
                    expect(remaining).to_have_count(0)
                    print("   [OK] No heroes remaining in campaign")
                    take_screenshot(page, "join_09_removed", "Hero removed")
                else:
                    print("   [INFO] Remove button not found (may not be owner)")
            else:
                print("   [INFO] No characters available to assign")

            summary_steps = [
                "Campaign created",
                "Invite link found",
                "Join page navigated",
                "Join page content verified",
            ]
            if character_assigned:
                summary_steps.append("Character assigned to campaign")
                summary_steps.append("Hero visible in campaign detail")
            if hero_removed:
                summary_steps.append("Hero removal confirmed")
                summary_steps.append("Hero removed from campaign")
            print_test_summary("CAMPAIGN JOIN", summary_steps)

        except Exception as e:
            print(f"\n[ERROR] {e}")
            if page is not None:
                take_screenshot(page, "join_error", "Error")
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
        test_campaign_join()
    except Exception:
        sys.exit(1)
