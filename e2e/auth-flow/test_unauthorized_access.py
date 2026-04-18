#!/usr/bin/env python3
"""
E2E test for Unauthorized Access

Matches: router/index.ts (auth guard redirects unauthenticated users to /login)
         ErrorNotFound.vue (404 for non-existent character/campaign IDs)
"""

import sys
import traceback

from playwright.sync_api import sync_playwright

from e2e.common.config import get_config
from e2e.common.helpers import (
    navigate_to,
    print_test_summary,
    take_screenshot,
    verify_url_contains,
    wait_for_page_load,
    wait_for_spinner_gone,
)

config = get_config()
BASE_URL = config["web_url"]


def test_unauthorized_access():
    """Test that protected routes redirect to login when unauthenticated"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=config["headless"], slow_mo=config["slow_mo"])

        print("\n=== UNAUTHORIZED ACCESS E2E TEST ===\n")

        page = None
        context = None
        try:
            # Create context WITHOUT authentication
            context = browser.new_context(
                ignore_https_errors=config.get("ignore_https_errors", False)
            )
            page = context.new_page()

            # Step 1: Access home page (requires auth)
            print("1. Accessing home page without auth...")
            navigate_to(page, BASE_URL, "/")
            # Vue Router's client-side redirect can fire after networkidle; wait for URL
            page.wait_for_url("**/login**", timeout=10000)
            wait_for_spinner_gone(page)

            verify_url_contains(page, "/login", "Redirected to login")
            take_screenshot(page, "unauth_01_home", "Home redirects to login")

            # Step 2: Access character sheet directly
            print("\n2. Accessing character sheet without auth...")
            navigate_to(page, BASE_URL, "/characters/99999")
            page.wait_for_url("**/login**", timeout=10000)
            wait_for_spinner_gone(page)

            verify_url_contains(page, "/login", "Redirected to login")
            print("   [OK] Character sheet redirects to login")

            # Step 3: Access campaign detail directly
            print("\n3. Accessing campaign detail without auth...")
            navigate_to(page, BASE_URL, "/campaigns/99999")
            page.wait_for_url("**/login**", timeout=10000)
            wait_for_spinner_gone(page)

            verify_url_contains(page, "/login", "Redirected to login")
            print("   [OK] Campaign detail redirects to login")

            # Step 4: Access account page directly
            print("\n4. Accessing account page without auth...")
            navigate_to(page, BASE_URL, "/account")
            page.wait_for_url("**/login**", timeout=10000)
            wait_for_spinner_gone(page)

            verify_url_contains(page, "/login", "Redirected to login")
            print("   [OK] Account page redirects to login")

            # Step 5: Access character creation
            print("\n5. Accessing character creation without auth...")
            navigate_to(page, BASE_URL, "/characters/new")
            page.wait_for_url("**/login**", timeout=10000)
            wait_for_spinner_gone(page)

            verify_url_contains(page, "/login", "Redirected to login")
            print("   [OK] Character creation redirects to login")

            # Step 6: Verify public pages remain accessible
            print("\n6. Verifying public pages accessible...")
            navigate_to(page, BASE_URL, "/login")
            wait_for_page_load(page)
            verify_url_contains(page, "/login")
            print("   [OK] Login page accessible without auth")

            navigate_to(page, BASE_URL, "/register")
            wait_for_page_load(page)
            verify_url_contains(page, "/register")
            print("   [OK] Register page accessible without auth")

            navigate_to(page, BASE_URL, "/forgot-password")
            wait_for_page_load(page)
            verify_url_contains(page, "/forgot-password")
            print("   [OK] Forgot password page accessible without auth")

            take_screenshot(page, "unauth_06_done", "Test complete")

            print_test_summary(
                "UNAUTHORIZED ACCESS",
                [
                    "Home redirects to login",
                    "Character sheet redirects to login",
                    "Campaign detail redirects to login",
                    "Account page redirects to login",
                    "Character creation redirects to login",
                    "Login page accessible without auth",
                    "Register page accessible without auth",
                    "Forgot password page accessible without auth",
                ],
            )

        except Exception as e:
            print(f"\n[ERROR] {e}")
            if page is not None:
                take_screenshot(page, "unauth_error", "Error")
            traceback.print_exc()
            raise
        finally:
            if context is not None:
                context.close()
            browser.close()


if __name__ == "__main__":
    try:
        test_unauthorized_access()
    except Exception:
        sys.exit(1)
