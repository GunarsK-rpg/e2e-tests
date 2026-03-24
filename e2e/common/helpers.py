"""
Common helper functions for E2E tests
Quasar-aware UI interaction helpers for the RPG frontend

Selectors live here -- tests should call helpers, not build selectors.
"""

import tempfile
from pathlib import Path
from typing import Optional, Tuple

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
    """Take a screenshot with consistent naming"""
    temp_dir = Path(tempfile.gettempdir())
    path = temp_dir / f"test_{name}.png"
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


def fill_input(page: Page, label: str, value: str, wait_ms: int = 200) -> bool:
    """Fill a q-input by its label text. Returns False if field not found."""
    field = page.locator(FIELD_BY_LABEL.format(label=label)).first
    if field.count() == 0:
        print(f"   [INFO] Input '{label}' not found")
        return False
    input_el = field.locator("input.q-field__native").first
    input_el.click()
    input_el.fill(value or "")
    page.wait_for_timeout(wait_ms)
    return True


def fill_textarea(page: Page, label: str, value: str, wait_ms: int = 200) -> bool:
    """Fill a q-input[type=textarea] by its label text. Returns False if not found."""
    field = page.locator(FIELD_BY_LABEL.format(label=label)).first
    if field.count() == 0:
        print(f"   [INFO] Textarea '{label}' not found")
        return False
    textarea = field.locator("textarea.q-field__native").first
    textarea.click()
    textarea.fill(value or "")
    page.wait_for_timeout(wait_ms)
    return True


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


def click_button_if_visible(page: Page, label: str, wait_ms: int = 200) -> bool:
    """Click a q-btn if it exists, return whether it was clicked"""
    btn = page.locator(f'.q-btn:has-text("{label}")').first
    if btn.count() > 0:
        btn.click()
        page.wait_for_timeout(wait_ms)
        return True
    return False


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


def select_first_card(page: Page, name: str, wait_ms: int = 300) -> bool:
    """Click the first unselected SelectableCard (role=radio/checkbox)"""
    cards = page.locator(SELECTABLE_CARD_UNSELECTED)
    if cards.count() > 0:
        cards.first.click()
        page.wait_for_timeout(wait_ms)
        print(f"   [OK] {name} selected")
        return True
    all_cards = page.locator(SELECTABLE_CARD)
    if all_cards.count() > 0:
        print(f"   [OK] {name} already selected")
        return True
    print(f"   [INFO] No {name} cards found")
    return False


# ========================================
# INCREMENT / DECREMENT HELPERS
# ========================================


def click_increment(page: Page, name: str, wait_ms: int = 200) -> bool:
    """Click increment button by aria-label 'Increase {name}'"""
    btn = page.locator(BTN_INCREMENT.format(name=name)).first
    if btn.count() > 0:
        btn.click()
        page.wait_for_timeout(wait_ms)
        print(f"   [OK] Incremented {name}")
        return True
    print(f"   [INFO] Cannot increment {name}")
    return False


def click_increment_rank(page: Page, name: str, wait_ms: int = 200) -> bool:
    """Click increment button by aria-label 'Increase {name} rank'"""
    btn = page.locator(BTN_INCREMENT_RANK.format(name=name)).first
    if btn.count() > 0:
        btn.click()
        page.wait_for_timeout(wait_ms)
        print(f"   [OK] Incremented {name} rank")
        return True
    print(f"   [INFO] Cannot increment {name} rank")
    return False


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
) -> bool:
    """Click button to open dialog, select first listbox item, close dialog"""
    btn = page.locator(f'.q-btn:has-text("{button_text}")').first
    if btn.count() == 0:
        print(f"   [INFO] {name} button not found")
        return False
    btn.click()
    page.wait_for_timeout(wait_ms)
    items = page.locator(LISTBOX_ITEM)
    if items.count() > 0:
        items.first.click()
        page.wait_for_timeout(300)
        print(f"   [OK] {name} selected from list")
    else:
        print(f"   [INFO] No {name} list items found")
    # Close dialog if still open
    done_btn = page.locator(
        '.q-dialog .q-btn:has-text("Done"),' + ' .q-dialog .q-btn:has-text("Close")'
    ).first
    if done_btn.count() > 0:
        done_btn.click()
        page.wait_for_timeout(300)
    return True


def click_first_listbox_item(page: Page, name: str, wait_ms: int = 300) -> bool:
    """Click the first item in a q-list with role='option' (path/kit dialogs)"""
    items = page.locator(LISTBOX_ITEM)
    if items.count() > 0:
        items.first.click()
        page.wait_for_timeout(wait_ms)
        print(f"   [OK] {name} selected from list")
        return True
    print(f"   [INFO] No {name} list items found")
    return False


# ========================================
# CHECKBOX HELPERS
# ========================================


def click_first_checkbox(page: Page, name: str, wait_ms: int = 200) -> bool:
    """Click the first unchecked q-checkbox"""
    checkbox = page.locator(f'{EXPERTISE_CHECKBOX}[aria-checked="false"]').first
    if checkbox.count() > 0:
        checkbox.click()
        page.wait_for_timeout(wait_ms)
        print(f"   [OK] {name} checked")
        return True
    any_cb = page.locator(EXPERTISE_CHECKBOX).first
    if any_cb.count() > 0:
        print(f"   [OK] {name} already checked")
        return True
    print(f"   [INFO] No {name} checkboxes found")
    return False


# ========================================
# NAVIGATION HELPERS
# ========================================


def navigate_to(page: Page, base_url: str, path: str, wait_ms: int = 500) -> None:
    """Navigate to a page and wait for load"""
    page.goto(f"{base_url}{path}")
    wait_for_page_load(page)
    page.wait_for_timeout(wait_ms)


def do_logout(page: Page, wait_ms: int = 1500) -> None:
    """Open account menu and click Logout"""
    page.locator(BTN_ACCOUNT_MENU).first.click()
    page.wait_for_timeout(300)
    page.locator(MENU_LOGOUT).first.click()
    wait_for_page_load(page)
    page.wait_for_timeout(wait_ms)


# ========================================
# VERIFICATION HELPERS
# ========================================


def verify_text_visible(page: Page, text: str, timeout: int = 5000) -> bool:
    """Assert text is visible on page"""
    element = page.locator(f'text="{text}"').first
    if element.count() > 0:
        expect(element).to_be_visible(timeout=timeout)
        print(f"   [OK] Text visible: {text}")
        return True
    print(f"   [INFO] Text not found: {text}")
    return False


def verify_url_contains(page: Page, path: str, description: Optional[str] = None) -> bool:
    """Check current URL contains path"""
    current_url = page.url
    if path in current_url:
        msg = description or f"URL contains '{path}'"
        print(f"   [OK] {msg}: {current_url}")
        return True
    print(f"   [INFO] Expected '{path}' in URL, got: {current_url}")
    return False


def verify_input_value(page: Page, value: str, name: str) -> bool:
    """Check that an input element contains the expected value"""
    el = page.locator(f'input[value="{value}"]')
    if el.count() > 0:
        print(f"   [OK] {name}: {value}")
        return True
    print(f"   [INFO] {name} not found in any input")
    return False


def verify_element_exists(page: Page, selector: str, name: str) -> Tuple[bool, int]:
    """Check if element exists and log result"""
    elements = page.locator(selector)
    count = elements.count()
    if count > 0:
        print(f"   [OK] {name} visible")
        return True, count
    print(f"   [INFO] {name} not found")
    return False, 0


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
