#!/usr/bin/env python3
"""
E2E test for Error Pages (404, 403, 500)

Matches: ErrorNotFound.vue (.error-code "404", .error-title "Page Not Found")
         ErrorForbidden.vue (.error-code "403", .error-title "Access Forbidden")
         ErrorServer.vue (.error-code "500", .error-title "Server Error")
"""

import re
import sys
import traceback

from playwright.sync_api import expect, sync_playwright

from e2e.auth.auth_manager import authenticate_for_testing
from e2e.common.config import get_config
from e2e.common.helpers import (
    ERROR_CODE,
    click_button,
    navigate_to,
    print_test_summary,
    take_screenshot,
    verify_error_page,
    wait_for_page_load,
    wait_for_spinner_gone,
)

config = get_config()
BASE_URL = config["web_url"]


def test_error_pages():
    """Test error pages render correctly and navigation works"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=config["headless"], slow_mo=config["slow_mo"])

        print("\n=== ERROR PAGES E2E TEST ===\n")

        page = None
        context = None
        try:
            page, context = authenticate_for_testing(browser)

            # Step 1: Test 404 page (any non-existent route)
            print("1. Testing 404 Not Found page...")
            navigate_to(page, BASE_URL, "/this-page-does-not-exist")
            wait_for_spinner_gone(page)

            verify_error_page(page, "404", "Page Not Found")
            take_screenshot(page, "error_01_404", "404 page")

            # Step 2: Verify Back to Home button works
            print("\n2. Testing Back to Home from 404...")
            click_button(page, "Back to Home")
            wait_for_page_load(page)
            wait_for_spinner_gone(page)
            # Error page should disappear after navigation
            expect(page.locator(ERROR_CODE)).to_have_count(0, timeout=10000)
            # 404 catch-all may not change URL on client-side nav
            print("   [OK] Back to Home navigates away from 404")

            # Step 3: Test 403 page
            print("\n3. Testing 403 Forbidden page...")
            navigate_to(page, BASE_URL, "/forbidden")
            wait_for_spinner_gone(page)

            verify_error_page(page, "403", "Access Forbidden")
            take_screenshot(page, "error_03_403", "403 page")

            # Step 4: Verify Back to Home from 403
            print("\n4. Testing Back to Home from 403...")
            click_button(page, "Back to Home")
            wait_for_page_load(page)
            wait_for_spinner_gone(page)
            expect(page.locator(ERROR_CODE)).to_have_count(0, timeout=10000)
            expect(page).to_have_url(re.compile(r"/$"), timeout=10000)
            print("   [OK] Back to Home navigates away from 403")

            # Step 5: Test 500 page
            print("\n5. Testing 500 Server Error page...")
            navigate_to(page, BASE_URL, "/error")
            wait_for_spinner_gone(page)

            verify_error_page(page, "500", "Server Error")
            take_screenshot(page, "error_05_500", "500 page")

            # Step 6: Verify Back to Home from 500
            print("\n6. Testing Back to Home from 500...")
            click_button(page, "Back to Home")
            wait_for_page_load(page)
            wait_for_spinner_gone(page)
            expect(page.locator(ERROR_CODE)).to_have_count(0, timeout=10000)
            expect(page).to_have_url(re.compile(r"/$"), timeout=10000)
            print("   [OK] Back to Home navigates away from 500")

            take_screenshot(page, "error_06_done", "Test complete")

            print_test_summary(
                "ERROR PAGES",
                [
                    "404 page renders (code, title, message)",
                    "404 Back to Home works",
                    "403 page renders (code, title, message)",
                    "403 Back to Home works",
                    "500 page renders (code, title, message)",
                    "500 Back to Home works",
                ],
            )
            return True

        except Exception as e:
            print(f"\n[ERROR] {e}")
            if page is not None:
                take_screenshot(page, "error_error", "Error")
            traceback.print_exc()
            return False
        finally:
            if context is not None:
                context.close()
            browser.close()


if __name__ == "__main__":
    success = test_error_pages()
    sys.exit(0 if success else 1)
