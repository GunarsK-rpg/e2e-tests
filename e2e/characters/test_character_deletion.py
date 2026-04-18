#!/usr/bin/env python3
"""
E2E test for Character Deletion

Matches: ReviewStep.vue (data-testid="delete-hero-btn")
         DeleteHeroDialog.vue (input aria-label="Type delete to confirm",
           q-btn label="Delete" color="negative", q-btn label="Cancel")
"""

import sys
import time
import traceback

from playwright.sync_api import expect, sync_playwright

from e2e.auth.auth_manager import authenticate_for_testing
from e2e.common.config import get_config
from e2e.common.helpers import (
    DELETE_CONFIRM_INPUT,
    HERO_CARD,
    cleanup_test_campaign,
    cleanup_test_hero,
    click_button,
    click_next_step,
    click_tab,
    confirm_dialog,
    create_campaign_with_source_books,
    extract_hero_id_from_url,
    fill_input,
    navigate_to,
    navigate_to_campaign_character_creation,
    print_test_summary,
    select_first_card,
    take_screenshot,
    wait_for_dialog,
    wait_for_page_load,
    wait_for_spinner_gone,
)

config = get_config()
BASE_URL = config["web_url"]


def test_character_deletion():
    """Test character deletion via edit mode -> ReviewStep -> Delete"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=config["headless"], slow_mo=config["slow_mo"])

        print("\n=== CHARACTER DELETION E2E TEST ===\n")

        page = None
        context = None
        hero_id = None
        unique_suffix = str(int(time.time()))[-6:]
        character_name = f"E2E Delete {unique_suffix}"
        campaign_name = f"E2E DelCamp {unique_suffix}"

        try:
            page, context = authenticate_for_testing(browser)

            # Step 0: Create campaign with source books
            print("0. Creating campaign with source books...")
            campaign_path = create_campaign_with_source_books(page, BASE_URL, campaign_name)

            # Step 1: Create character via wizard (basic setup only)
            print("\n1. Creating test character...")
            navigate_to_campaign_character_creation(page, BASE_URL, campaign_path)
            fill_input(page, "Character Name", character_name)
            select_first_card(page, "Ancestry")
            click_next_step(page)
            wait_for_spinner_gone(page)
            hero_id = extract_hero_id_from_url(page)
            if hero_id is None:
                raise AssertionError(f"Could not extract hero ID from URL: {page.url}")
            print(f"   [OK] Hero created (id={hero_id}): {character_name}")

            # Step 2: Reload to enter edit mode (wizardStore.mode -> 'edit')
            print("\n2. Entering edit mode...")
            page.reload()
            wait_for_page_load(page)
            wait_for_spinner_gone(page)
            print("   [OK] Edit mode entered")

            # Step 3: Navigate to Review tab
            print("\n3. Navigating to Review step...")
            click_tab(page, "Review")
            wait_for_spinner_gone(page)
            print("   [OK] Review step opened")

            # Step 4: Click Delete Character button
            print("\n4. Clicking Delete Character...")
            click_button(page, "Delete Character")
            wait_for_dialog(page)
            print("   [OK] Delete dialog opened")
            take_screenshot(page, "delete_04_dialog", "Delete dialog")

            # Step 5: Type "delete" and confirm
            print("\n5. Confirming deletion...")
            page.locator(DELETE_CONFIRM_INPUT).first.click()
            page.locator(DELETE_CONFIRM_INPUT).first.fill("delete")
            wait_for_spinner_gone(page)
            confirm_dialog(page, "Delete")
            wait_for_page_load(page)
            print("   [OK] Deletion confirmed")
            # Hero deleted via UI -- skip cleanup_test_hero in finally
            hero_id = None

            # Step 6: Verify dialog closed
            print("\n6. Verifying dialog closed...")
            expect(page.locator(".q-dialog")).to_have_count(0)
            print("   [OK] Dialog closed")

            # Step 7: Verify hero is gone from list
            print("\n7. Verifying removal from list...")
            navigate_to(page, BASE_URL, "/")
            wait_for_spinner_gone(page)
            take_screenshot(page, "delete_07_after", "After deletion")
            remaining = page.locator(f'{HERO_CARD}:has-text("{character_name}")')
            expect(remaining).to_have_count(0)
            print(f"   [OK] '{character_name}' no longer in character list")

            print_test_summary(
                "CHARACTER DELETION",
                [
                    "Campaign created",
                    "Character created",
                    "Edit mode entered",
                    "Review step navigated",
                    "Delete dialog opened",
                    "Confirmation typed and confirmed",
                    "Dialog closed",
                    "Character removed from list",
                ],
            )

        except Exception as e:
            print(f"\n[ERROR] {e}")
            if page is not None:
                take_screenshot(page, "delete_error", "Error")
            traceback.print_exc()
            raise
        finally:
            if page is not None:
                if hero_id is not None:
                    cleanup_test_hero(page, BASE_URL, hero_id)
                cleanup_test_campaign(page, BASE_URL, campaign_name)
            if context is not None:
                context.close()
            browser.close()


if __name__ == "__main__":
    try:
        test_character_deletion()
    except Exception:
        sys.exit(1)
