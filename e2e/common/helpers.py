"""
Common helper functions for E2E tests
Quasar-aware UI interaction helpers for the RPG frontend

Selectors live here -- tests should call helpers, not build selectors.
"""

from pathlib import Path
from typing import Optional

from playwright.sync_api import Locator, Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import expect

# ========================================
# SELECTORS (centralised)
# ========================================

# Quasar field by label: .q-field wrapping a .q-field__label containing text
# Uses :has-text() not :text-is() because Quasar appends " *" to required field labels
FIELD_BY_LABEL = '.q-field:has(.q-field__label:has-text("{label}"))'

# SelectableCard: .q-card with role radio/checkbox, selected state via .card-selected
# Quasar renders <q-card> as <div class="q-card">, so use class selector not element
SELECTABLE_CARD = ".q-card[role='radio'], .q-card[role='checkbox']"
SELECTABLE_CARD_UNSELECTED = ", ".join(
    [
        ".q-card[role='radio']:not(.card-selected)",
        ".q-card[role='checkbox']:not(.card-selected)",
    ]
)

# Wizard navigation (StepNavigation.vue)
BTN_NEXT_STEP = 'button[aria-label="Next step"]'
BTN_FINISH = '.q-btn:has-text("Finish")'

# Account menu / logout (MainLayout.vue)
BTN_ACCOUNT_MENU = 'button[aria-label="Account menu"]'
MENU_LOGOUT = '.q-menu .q-item:has-text("Logout")'

# Character list (MyCharactersPage / HeroCard)
HERO_CARD = ".card-interactive"

# Delete hero dialog (DeleteHeroDialog.vue)
DELETE_CONFIRM_INPUT = 'input[aria-label="Type delete to confirm"]'

# Increment/decrement buttons (AttributesStep, SkillsStep)
BTN_INCREMENT = 'button[aria-label="Increase {name}"]'
BTN_INCREMENT_RANK = 'button[aria-label="Increase {name} rank"]'
BTN_DECREMENT = 'button[aria-label="Decrease {name}"]'

# Expertise checkbox
EXPERTISE_CHECKBOX = ".q-checkbox"

# Listbox items in dialogs (paths, starting kits, radiant orders)
LISTBOX_ITEM = '.q-item[role="option"]'

# Spinners
SPINNER = ".q-spinner-dots, .q-spinner, .q-loading"


# ========================================
# PAGE & SCREENSHOT HELPERS
# ========================================


def wait_for_page_load(page: Page) -> None:
    """Wait for page to fully load"""
    page.wait_for_load_state("networkidle")


def take_screenshot(page: Page, name: str, description: str = "") -> str:
    """Take a screenshot with consistent naming, grouped by test prefix"""
    import re

    from e2e.common.config import get_config

    screenshot_dir = Path(get_config()["screenshot_dir"])
    match = re.match(r"^([a-z_]+?)_\d", name)
    subfolder = match.group(1) if match else "misc"
    target_dir = screenshot_dir / subfolder
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / f"{name}.png"
    page.screenshot(path=str(path))
    if description:
        print(f"   [SCREENSHOT] {description}: {path}")
    return str(path)


def wait_for_spinner_gone(page: Page, timeout: int = 10000) -> None:
    """Wait for Quasar spinner to disappear"""
    spinner = page.locator(SPINNER)
    try:
        spinner.first.wait_for(state="hidden", timeout=timeout)
    except PlaywrightTimeoutError:
        pass


# ========================================
# QUASAR FORM INPUT HELPERS
# ========================================


def fill_input(page: Page, label: str, value: str, wait_ms: int = 200) -> None:
    """Fill a q-input by its label text. Raises if field not found."""
    field = page.locator(FIELD_BY_LABEL.format(label=label)).first
    if field.count() == 0:
        raise AssertionError(f"Input '{label}' not found")
    input_el = field.locator("input.q-field__native").first
    input_el.click()
    input_el.fill(value or "")
    page.wait_for_timeout(wait_ms)


def fill_textarea(page: Page, label: str, value: str, wait_ms: int = 200) -> None:
    """Fill a q-input[type=textarea] by its label text. Raises if not found."""
    field = page.locator(FIELD_BY_LABEL.format(label=label)).first
    if field.count() == 0:
        raise AssertionError(f"Textarea '{label}' not found")
    textarea = field.locator("textarea.q-field__native").first
    textarea.click()
    textarea.fill(value or "")
    page.wait_for_timeout(wait_ms)


def fill_input_by_aria(page: Page, aria_label: str, value: str, wait_ms: int = 200) -> None:
    """Fill an input by its aria-label attribute. Raises if not found."""
    input_el = page.locator(f'input[aria-label="{aria_label}"]').first
    if input_el.count() == 0:
        raise AssertionError(f"Input with aria-label '{aria_label}' not found")
    input_el.click()
    input_el.fill(value or "")
    page.wait_for_timeout(wait_ms)


# ========================================
# QUASAR SELECT HELPERS
# ========================================


def select_first_option(page: Page, label: str, wait_ms: int = 300) -> None:
    """Click q-select by label, pick the first available option from menu"""
    field = page.locator(FIELD_BY_LABEL.format(label=label)).first
    field.click()
    page.wait_for_timeout(wait_ms)
    menu = page.locator(".q-menu")
    menu.first.wait_for(state="visible", timeout=5000)
    menu.locator(".q-item").first.click()
    page.wait_for_timeout(wait_ms)


# ========================================
# QUASAR BUTTON HELPERS
# ========================================


def submit_form(page: Page, wait_ms: int = 200) -> None:
    """Click the form submit button (button[type=submit])"""
    page.locator('button[type="submit"]').first.click()
    page.wait_for_timeout(wait_ms)


def click_button(page: Page, label: str, wait_ms: int = 200) -> None:
    """Click a q-btn by label text"""
    page.locator(f'.q-btn:has-text("{label}")').first.click()
    page.wait_for_timeout(wait_ms)


def click_button_by_aria(page: Page, aria_label: str, wait_ms: int = 200) -> None:
    """Click a button or link by its aria-label attribute"""
    page.locator(f'[aria-label="{aria_label}"]').first.click()
    page.wait_for_timeout(wait_ms)


def click_button_if_visible(
    page: Page, label: str, timeout: int = 3000, wait_ms: int = 200
) -> bool:
    """Wait for q-btn to appear, click if found. Returns whether clicked."""
    btn = page.locator(f'.q-btn:has-text("{label}")').first
    try:
        btn.wait_for(state="visible", timeout=timeout)
    except PlaywrightTimeoutError:
        return False
    btn.click()
    page.wait_for_timeout(wait_ms)
    return True


# ========================================
# WIZARD NAVIGATION HELPERS
# ========================================


def click_next_step(page: Page, wait_ms: int = 500) -> None:
    """Click the Next step arrow button in wizard footer"""
    page.locator(BTN_NEXT_STEP).first.click()
    page.wait_for_timeout(wait_ms)
    wait_for_spinner_gone(page)


def click_finish(page: Page, wait_ms: int = 2000) -> None:
    """Click the Finish button on the last wizard step"""
    page.locator(BTN_FINISH).first.click()
    wait_for_page_load(page)
    page.wait_for_timeout(wait_ms)


# ========================================
# SELECTABLE CARD HELPERS
# ========================================


def select_first_card(page: Page, name: str, wait_ms: int = 300) -> None:
    """Click the first unselected SelectableCard. Raises if none found."""
    cards = page.locator(SELECTABLE_CARD_UNSELECTED)
    if cards.count() > 0:
        cards.first.click()
        page.wait_for_timeout(wait_ms)
        print(f"   [OK] {name} selected")
        return
    all_cards = page.locator(SELECTABLE_CARD)
    if all_cards.count() > 0:
        print(f"   [OK] {name} already selected")
        return
    raise AssertionError(f"No {name} cards found")


# ========================================
# INCREMENT / DECREMENT HELPERS
# ========================================


def click_increment(page: Page, name: str, wait_ms: int = 200) -> None:
    """Click increment button by aria-label 'Increase {name}'"""
    btn = page.locator(BTN_INCREMENT.format(name=name)).first
    if btn.count() > 0:
        btn.click()
        page.wait_for_timeout(wait_ms)
        print(f"   [OK] Incremented {name}")
        return
    raise AssertionError(f"Cannot increment {name}: button not found")


def click_increment_rank(page: Page, name: str, wait_ms: int = 200) -> None:
    """Click increment button by aria-label 'Increase {name} rank'"""
    btn = page.locator(BTN_INCREMENT_RANK.format(name=name)).first
    if btn.count() > 0:
        btn.click()
        page.wait_for_timeout(wait_ms)
        print(f"   [OK] Incremented {name} rank")
        return
    raise AssertionError(f"Cannot increment {name} rank: button not found")


def click_decrement(page: Page, name: str, wait_ms: int = 200) -> None:
    """Click decrement button by aria-label 'Decrease {name}'"""
    btn = page.locator(BTN_DECREMENT.format(name=name)).first
    if btn.count() > 0:
        btn.click()
        page.wait_for_timeout(wait_ms)
        print(f"   [OK] Decremented {name}")
        return
    raise AssertionError(f"Cannot decrement {name}: button not found")


# ========================================
# QUASAR TAB HELPERS
# ========================================


def click_tab(page: Page, tab_label: str, wait_ms: int = 300) -> None:
    """Click a q-tab by label text"""
    page.locator(f'.q-tab:has-text("{tab_label}")').first.click()
    page.wait_for_timeout(wait_ms)


# ========================================
# QUASAR DIALOG HELPERS
# ========================================


def wait_for_dialog(page: Page, timeout: int = 5000) -> Locator:
    """Wait for q-dialog to be visible and return it"""
    dialog = page.locator(".q-dialog").first
    dialog.wait_for(state="visible", timeout=timeout)
    return dialog


def confirm_dialog(page: Page, button_label: str = "OK", wait_ms: int = 500) -> None:
    """Click confirm button in dialog"""
    dialog = page.locator(".q-dialog").first
    dialog.locator(f'.q-btn:has-text("{button_label}")').first.click()
    page.wait_for_timeout(wait_ms)


def dismiss_dialog(page: Page, button_label: str = "Cancel", wait_ms: int = 300) -> None:
    """Click cancel button in dialog"""
    dialog = page.locator(".q-dialog").first
    dialog.locator(f'.q-btn:has-text("{button_label}")').first.click()
    page.wait_for_timeout(wait_ms)


# ========================================
# LISTBOX / LIST ITEM HELPERS
# ========================================


def open_dialog_and_select_first(
    page: Page, button_text: str, name: str, wait_ms: int = 500
) -> None:
    """Click button to open dialog, select first listbox item, close dialog"""
    btn = page.locator(f'.q-btn:has-text("{button_text}")').first
    if btn.count() == 0:
        raise AssertionError(f"{name} button not found")
    btn.click()
    page.wait_for_timeout(wait_ms)
    items = page.locator(LISTBOX_ITEM)
    if items.count() == 0:
        raise AssertionError(f"No {name} list items found")
    items.first.click()
    page.wait_for_timeout(300)
    print(f"   [OK] {name} selected from list")
    # Close dialog if still open
    done_btn = page.locator(
        '.q-dialog .q-btn:has-text("Done"),' + ' .q-dialog .q-btn:has-text("Close")'
    ).first
    if done_btn.count() > 0:
        done_btn.click()
        page.wait_for_timeout(300)


def click_first_listbox_item(page: Page, name: str, wait_ms: int = 300) -> None:
    """Click the first item in a q-list with role='option' (path/kit dialogs)"""
    items = page.locator(LISTBOX_ITEM)
    if items.count() > 0:
        items.first.click()
        page.wait_for_timeout(wait_ms)
        print(f"   [OK] {name} selected from list")
        return
    raise AssertionError(f"No {name} list items found")


# ========================================
# CHECKBOX HELPERS
# ========================================


def click_first_checkbox(page: Page, name: str, wait_ms: int = 200) -> None:
    """Click the first unchecked q-checkbox"""
    checkbox = page.locator(f'{EXPERTISE_CHECKBOX}[aria-checked="false"]').first
    if checkbox.count() > 0:
        checkbox.click()
        page.wait_for_timeout(wait_ms)
        print(f"   [OK] {name} checked")
        return
    any_cb = page.locator(EXPERTISE_CHECKBOX).first
    if any_cb.count() > 0:
        print(f"   [OK] {name} already checked")
        return
    raise AssertionError(f"No {name} checkboxes found")


# ========================================
# TOGGLE HELPERS
# ========================================


def click_aria_toggle(page: Page, aria_label: str, wait_ms: int = 200) -> None:
    """Click a toggle element by aria-label (conditions, switches). Raises if not found."""
    el = page.locator(f'[aria-label="{aria_label}"]').first
    if el.count() == 0:
        raise AssertionError(f"Toggle '{aria_label}' not found")
    el.click()
    page.wait_for_timeout(wait_ms)


def verify_aria_pressed(page: Page, aria_label: str, expected: str) -> None:
    """Assert aria-pressed value of a toggle element. expected: 'true' or 'false'."""
    el = page.locator(f'[aria-label="{aria_label}"]').first
    if el.count() == 0:
        raise AssertionError(f"Toggle '{aria_label}' not found")
    expect(el).to_have_attribute("aria-pressed", expected)
    print(f"   [OK] {aria_label} pressed={expected}")


# ========================================
# NAVIGATION HELPERS
# ========================================


def navigate_to(page: Page, base_url: str, path: str) -> None:
    """Navigate to a page and wait for load"""
    page.goto(f"{base_url}{path}")
    wait_for_page_load(page)


def do_logout(page: Page) -> None:
    """Open account menu and click Logout"""
    page.locator(BTN_ACCOUNT_MENU).first.click()
    page.wait_for_timeout(300)
    page.locator(MENU_LOGOUT).first.click()
    wait_for_page_load(page)
    page.wait_for_url("**/login**", timeout=10000)


# ========================================
# VERIFICATION HELPERS
# ========================================


def wait_for_element(page: Page, selector: str, timeout: int = 5000) -> int:
    """Wait for element to appear, return count. Returns 0 on timeout (no raise)."""
    loc = page.locator(selector)
    try:
        loc.first.wait_for(state="visible", timeout=timeout)
    except PlaywrightTimeoutError:
        return 0
    return loc.count()


def verify_text_visible(page: Page, text: str, timeout: int = 5000) -> None:
    """Assert text is visible on page. Raises if not found."""
    element = page.locator(f'text="{text}"').first
    if element.count() > 0:
        expect(element).to_be_visible(timeout=timeout)
        print(f"   [OK] Text visible: {text}")
        return
    raise AssertionError(f"Text not found: {text}")


def verify_url_contains(page: Page, path: str, description: Optional[str] = None) -> None:
    """Assert current URL contains path. Raises if not."""
    current_url = page.url
    if path in current_url:
        msg = description or f"URL contains '{path}'"
        print(f"   [OK] {msg}: {current_url}")
        return
    raise AssertionError(f"Expected '{path}' in URL, got: {current_url}")


def verify_input_value(page: Page, value: str, name: str) -> None:
    """Assert input element contains expected value. Raises if not found."""
    el = page.locator(f'input[value="{value}"]')
    if el.count() > 0:
        print(f"   [OK] {name}: {value}")
        return
    raise AssertionError(f"{name} not found in any input (expected value: {value})")


def verify_element_exists(page: Page, selector: str, name: str, timeout: int = 10000) -> int:
    """Wait for element to appear, then return count. Raises if not found."""
    loc = page.locator(selector)
    try:
        loc.first.wait_for(state="visible", timeout=timeout)
    except PlaywrightTimeoutError as exc:
        raise AssertionError(f"{name} not found (selector: {selector})") from exc
    count = loc.count()
    print(f"   [OK] {name} visible")
    return count


def verify_text_not_visible(page: Page, text: str, timeout: int = 3000) -> None:
    """Assert text is NOT visible on page. Raises if any match is still visible."""
    locator = page.locator(f'text="{text}"')
    count = locator.count()
    for i in range(count):
        try:
            expect(locator.nth(i)).not_to_be_visible(timeout=timeout)
        except AssertionError as exc:
            raise AssertionError(f"Text still visible: {text} (match {i})") from exc
    print(f"   [OK] Text not visible: {text}")


# ========================================
# CLEANUP HELPERS
# ========================================


def cleanup_test_campaign(page: Page, base_url: str, campaign_name: str) -> None:
    """Navigate to campaigns list and delete a campaign by name. Swallows errors."""
    try:
        navigate_to(page, base_url, "/campaigns")
        wait_for_spinner_gone(page)
        selector = f'.card-interactive:has-text("{campaign_name}")'
        if wait_for_element(page, selector) > 0:
            page.locator(selector).first.click()
            wait_for_page_load(page)
            click_button_by_aria(page, "Delete campaign")
            wait_for_dialog(page)
            confirm_dialog(page, "OK")
            print("   [CLEANUP] Test campaign deleted")
    except Exception as cleanup_err:
        print(f"   [CLEANUP WARN] {cleanup_err}")


# ========================================
# SUMMARY HELPER
# ========================================


def print_test_summary(test_name: str, passed_tests: list[str]) -> None:
    """Print standardized test summary"""
    print("\n" + "=" * 60)
    print(f"=== {test_name} COMPLETED SUCCESSFULLY ===")
    print("=" * 60)
    print("\nTests performed:")
    for test in passed_tests:
        print(f"  [PASS] {test}")
