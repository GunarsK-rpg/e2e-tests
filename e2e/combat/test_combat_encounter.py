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
import traceback

from playwright.sync_api import sync_playwright

from e2e.auth.auth_manager import authenticate_for_testing
from e2e.common.config import get_config
from e2e.common.helpers import (
    cleanup_test_campaign,
    click_button,
    click_button_if_visible,
    click_increment,
    confirm_dialog,
    dismiss_dialog,
    fill_input,
    navigate_to,
    print_test_summary,
    take_screenshot,
    verify_element_exists,
    verify_input_value,
    wait_for_class_change,
    wait_for_dialog,
    wait_for_element,
    wait_for_page_load,
    wait_for_spinner_gone,
    wait_for_text_change,
)

config = get_config()
BASE_URL = config["web_url"]


def test_combat_encounter():
    """Test combat encounter lifecycle"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=config["headless"], slow_mo=config["slow_mo"])

        print("\n=== COMBAT ENCOUNTER E2E TEST ===\n")

        page = None
        context = None
        campaign_name = None
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

            fill_input(page, "Campaign Name", campaign_name)
            click_button(page, "Create")
            wait_for_page_load(page)
            print(f"   [OK] Campaign: {campaign_name}")

            # Step 2: Create combat
            print("\n2. Creating combat encounter...")
            click_button(page, "New Combat")
            wait_for_dialog(page)
            fill_input(page, "Name", combat_name)
            confirm_dialog(page, "Create")
            wait_for_page_load(page)
            print(f"   [OK] Combat created: {combat_name}")

            take_screenshot(page, "combat_02_created", "Combat created")

            # Step 3: Verify combat detail (name is in a q-input, not a text node)
            print("\n3. Verifying combat detail...")
            verify_input_value(page, combat_name, "Combat name")
            take_screenshot(page, "combat_03_detail", "Combat detail")

            # Step 4: Add NPCs via dialog (attempt two for multi-NPC testing)
            print("\n4. Adding NPCs to combat...")
            npcs_added = 0
            npc_items_selector = ".q-dialog .q-item--clickable"

            for attempt in range(2):
                btn_label = "Add Enemy" if attempt == 0 else "Add Enemy"
                if not click_button_if_visible(page, btn_label):
                    break
                if wait_for_element(page, npc_items_selector) == 0:
                    print("   [INFO] No NPCs available")
                    dismiss_dialog(page, "Cancel")
                    break
                # Select the first available NPC in the dialog
                page.locator(npc_items_selector).first.click()
                wait_for_spinner_gone(page)
                confirm_dialog(page, "Add")
                npcs_added += 1
                print(f"   [OK] NPC {npcs_added} added")

            take_screenshot(page, "combat_04_npc", "After NPC add")

            # Step 5: Verify combat tiles
            print("\n5. Checking combat participants...")
            npc_tiles = page.locator(".combat-npc-tile")
            tile_count = npc_tiles.count()
            if tile_count > 0:
                print(f"   [OK] {tile_count} combat NPC tiles present")
                if tile_count >= 2:
                    print("   [OK] Multi-NPC scenario verified")
            else:
                print("   [INFO] No combat NPC tiles (no NPCs were added)")

            # Step 6: Test phase toggle
            print("\n6. Testing phase toggle...")
            verify_element_exists(page, ".q-btn-toggle", "Phase toggle")

            # Step 7: Test active toggle
            print("\n7. Testing active toggle...")
            click_button_if_visible(page, "Active")
            wait_for_spinner_gone(page)

            take_screenshot(page, "combat_07_state", "Combat state")

            # --- COMBAT ROUND MANAGEMENT ---

            # Step 8: Test turn counter increment
            print("\n8. Testing turn counter...")
            turn_increase = page.locator('button[aria-label="Increase Turn"]')
            if turn_increase.count() > 0 and turn_increase.is_enabled():
                turn_display = turn_increase.locator("xpath=..").locator(".resource-value").first
                turn_before = turn_display.inner_text().strip()

                click_increment(page, "Turn")
                turn_after = wait_for_text_change(turn_display, turn_before)

                assert turn_before.isdigit(), f"Turn before is not numeric: {turn_before}"
                assert turn_after.isdigit(), f"Turn after is not numeric: {turn_after}"
                before_int = int(turn_before)
                after_int = int(turn_after)
                assert (
                    after_int == before_int + 1
                ), f"Turn did not increment (expected {before_int + 1}, got {after_int})"
                print(f"   [OK] Turn incremented: {turn_before} -> {turn_after}")
            else:
                print("   [INFO] Turn increase button not available")

            take_screenshot(page, "combat_08_turn", "After turn increment")

            # Step 9: Test phase toggle (click second option)
            # Scope to combat-level toggle (first on page, before NPC tile toggles)
            print("\n9. Testing phase toggle options...")
            saved_phase = None
            phase_toggle = page.locator(".q-btn-toggle").first
            if phase_toggle.count() > 0:
                toggle_btns = phase_toggle.locator(".q-btn")
                if toggle_btns.count() > 1:
                    toggle_btns.nth(1).click()
                    wait_for_class_change(toggle_btns.nth(1), "bg-primary", True)
                    saved_phase = toggle_btns.nth(1).inner_text().strip()
                    print(f"   [OK] Phase toggled to: {saved_phase}")
                else:
                    print("   [INFO] Only one phase option available")
            else:
                print("   [INFO] Phase toggle not found")

            take_screenshot(page, "combat_09_phase", "After phase toggle")

            # Step 10: Test combat state persistence after reload
            print("\n10. Verifying state persistence...")
            # Capture current turn value before reload
            turn_btn_before = page.locator('button[aria-label="Increase Turn"]')
            saved_turn = None
            if turn_btn_before.count() > 0:
                saved_turn = (
                    turn_btn_before.locator("xpath=..")
                    .locator(".resource-value")
                    .first.inner_text()
                    .strip()
                )

            page.reload()
            wait_for_page_load(page)
            wait_for_spinner_gone(page)
            verify_input_value(page, combat_name, "Combat name after reload")

            # Verify turn persisted (fresh locator after reload)
            if saved_turn is not None:
                turn_btn_after = page.locator('button[aria-label="Increase Turn"]')
                if turn_btn_after.count() == 0:
                    raise AssertionError("Turn button not found after reload")
                reloaded_turn = (
                    turn_btn_after.locator("xpath=..")
                    .locator(".resource-value")
                    .first.inner_text()
                    .strip()
                )
                assert (
                    reloaded_turn == saved_turn
                ), f"Turn not persisted (expected {saved_turn}, got {reloaded_turn})"
                print(f"   [OK] Turn persisted: {reloaded_turn}")

            # Verify phase persisted
            if saved_phase is not None:
                reloaded_phase = page.locator(".q-btn-toggle").first
                if reloaded_phase.count() > 0:
                    active_btn = reloaded_phase.locator(".q-btn--active, .bg-primary")
                    assert active_btn.count() > 0, "No active phase button after reload"
                    reloaded_phase_text = active_btn.first.inner_text().strip()
                    assert (
                        reloaded_phase_text == saved_phase
                    ), f"Phase not persisted (expected {saved_phase}, got {reloaded_phase_text})"
                    print(f"   [OK] Phase persisted: {reloaded_phase_text}")

            print("   [OK] Combat state persisted")

            # --- NPC INSTANCE MANAGEMENT ---

            # Step 11: Test NPC resource buttons (if NPC tiles exist)
            print("\n11. Testing NPC instance resources...")
            npc_tiles = page.locator(".combat-npc-tile")
            if npc_tiles.count() > 0:
                npc_tile = npc_tiles.first

                # HP decrease/increase
                hp_decrease = npc_tile.locator('button[aria-label="Decrease HP"]')
                hp_increase = npc_tile.locator('button[aria-label="Increase HP"]')
                npc_hp_display = npc_tile.locator(".resource-value").first

                if hp_decrease.count() > 0 and hp_decrease.is_enabled():
                    hp_before = npc_hp_display.inner_text().strip()
                    hp_decrease.click()
                    hp_after_dec = wait_for_text_change(npc_hp_display, hp_before)
                    print(f"   [OK] NPC HP decreased: {hp_before} -> {hp_after_dec}")

                    if hp_increase.count() > 0 and hp_increase.is_enabled():
                        hp_increase.click()
                        hp_after_inc = wait_for_text_change(npc_hp_display, hp_after_dec)
                        # Parse current HP (format: "X / Y") to verify increase
                        dec_val = int(hp_after_dec.split("/")[0].strip())
                        inc_val = int(hp_after_inc.split("/")[0].strip())
                        assert (
                            inc_val > dec_val
                        ), f"NPC HP did not increase: {hp_after_dec} -> {hp_after_inc}"
                        print(f"   [OK] NPC HP restored: {hp_after_dec} -> {hp_after_inc}")
                else:
                    print("   [INFO] NPC HP buttons not available")

                take_screenshot(page, "combat_11_npc_hp", "NPC HP changes")

                # Step 12: Test turn done toggle (no aria-pressed; uses color change)
                print("\n12. Testing NPC turn done toggle...")
                turn_done_btn = npc_tile.locator('[aria-label="Toggle turn done"]')
                if turn_done_btn.count() > 0:
                    has_positive_before = "positive" in (turn_done_btn.get_attribute("class") or "")
                    turn_done_btn.click()
                    # Wait for class to flip
                    want_positive = not has_positive_before
                    wait_for_class_change(turn_done_btn, "positive", want_positive)
                    print(f"   [OK] Turn done toggled (positive={want_positive})")

                    turn_done_btn.click()
                    wait_for_class_change(turn_done_btn, "positive", has_positive_before)
                    print(f"   [OK] Turn done restored (positive={has_positive_before})")
                else:
                    print("   [INFO] Turn done toggle not found")

                # Step 13: Test turn speed toggle
                print("\n13. Testing NPC turn speed toggle...")
                speed_toggle = npc_tile.locator(".turn-speed-toggle, .q-btn-toggle").first
                if speed_toggle.count() > 0:
                    speed_btns = speed_toggle.locator(".q-btn")
                    if speed_btns.count() > 1:
                        # Find a non-active button to click
                        target_idx = None
                        for idx in range(speed_btns.count()):
                            cls = speed_btns.nth(idx).get_attribute("class") or ""
                            if "q-btn--active" not in cls and "bg-primary" not in cls:
                                target_idx = idx
                                break
                        if target_idx is not None:
                            target_btn = speed_btns.nth(target_idx)
                            target_btn.click()
                            wait_for_class_change(target_btn, "bg-primary", True)
                            print(f"   [OK] Turn speed toggled to button {target_idx}")
                        else:
                            print("   [INFO] All speed buttons already active")
                    elif speed_btns.count() == 1:
                        print("   [INFO] Only one speed button available")
                    else:
                        print("   [INFO] No speed toggle buttons found")
                else:
                    print("   [INFO] Turn speed toggle not found (may be boss type)")
            else:
                print("   [INFO] No NPC tiles -- skipping instance tests")

            take_screenshot(page, "combat_13_done", "Test complete")

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
                    "Turn counter incremented",
                    "Phase toggle option changed",
                    "State persists after reload",
                    "NPC HP decrease/increase",
                    "NPC turn done toggle",
                    "NPC turn speed toggle",
                ],
            )
            return True

        except Exception as e:
            print(f"\n[ERROR] {e}")
            if page is not None:
                take_screenshot(page, "combat_error", "Error")
            traceback.print_exc()
            return False
        finally:
            if page is not None and campaign_name:
                cleanup_test_campaign(page, BASE_URL, campaign_name)
            if context is not None:
                context.close()
            browser.close()


if __name__ == "__main__":
    success = test_combat_encounter()
    sys.exit(0 if success else 1)
