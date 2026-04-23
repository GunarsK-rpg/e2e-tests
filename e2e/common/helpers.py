"""
Common helper functions for E2E tests
Quasar-aware UI interaction helpers for the RPG frontend

Selectors live here -- tests should call helpers, not build selectors.
"""

import re
import traceback
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

# Character sheet tab content (StatsTab, SkillsTab, TalentsTab, ExpertisesTab, CompanionsTab)
ATTRIBUTE_CARD = ".attribute-card"
DEFENSE_CARD = ".defense-card"
SKILL_CATEGORY = ".skill-category"
SKILL_ITEM = ".skills-tab .q-item"
SKILL_ITEM_LABEL = ".q-item__label"
SKILL_PIP_FILLED = ".skills-tab .pip.filled"
TALENT_TAB = ".talents-tab .q-tab"
EXPERTISE_SECTION = ".expertises-tab .category-section"
EXPERTISE_CHIP = ".expertises-tab .q-chip"
COMPANION_TILE = ".combat-npc-tile"

# Error pages (ErrorNotFound, ErrorForbidden, ErrorServer)
ERROR_CODE = ".error-code"
ERROR_TITLE = ".error-title"

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


def fill_input(page: Page, label: str, value: str) -> None:
    """Fill a q-input by its label text. Waits for field to appear."""
    field = page.locator(FIELD_BY_LABEL.format(label=label)).first
    try:
        field.wait_for(state="visible", timeout=10000)
    except PlaywrightTimeoutError as exc:
        raise AssertionError(f"Input '{label}' not found") from exc
    input_el = field.locator("input.q-field__native").first
    input_el.click()
    input_el.fill(value or "")
    expect(input_el).to_have_value(value or "")


def fill_textarea(page: Page, label: str, value: str) -> None:
    """Fill a q-input[type=textarea] by its label text. Waits for field to appear."""
    field = page.locator(FIELD_BY_LABEL.format(label=label)).first
    try:
        field.wait_for(state="visible", timeout=10000)
    except PlaywrightTimeoutError as exc:
        raise AssertionError(f"Textarea '{label}' not found") from exc
    textarea = field.locator("textarea.q-field__native").first
    textarea.click()
    textarea.fill(value or "")
    expect(textarea).to_have_value(value or "")


def fill_input_by_aria(page: Page, aria_label: str, value: str) -> None:
    """Fill an input by its aria-label attribute. Waits for field to appear."""
    input_el = page.locator(f'input[aria-label="{aria_label}"]').first
    try:
        input_el.wait_for(state="visible", timeout=10000)
    except PlaywrightTimeoutError as exc:
        raise AssertionError(f"Input with aria-label '{aria_label}' not found") from exc
    input_el.click()
    input_el.fill(value or "")
    expect(input_el).to_have_value(value or "")


# ========================================
# QUASAR SELECT HELPERS
# ========================================


def select_first_option(page: Page, label: str) -> None:
    """Click q-select by label, pick the first available option from menu"""
    field = page.locator(FIELD_BY_LABEL.format(label=label)).first
    field.click()
    menu = page.locator(".q-menu")
    menu.first.wait_for(state="visible", timeout=5000)
    menu.locator(".q-item").first.click()
    expect(menu).to_have_count(0, timeout=5000)


# ========================================
# QUASAR BUTTON HELPERS
# ========================================


def submit_form(page: Page) -> None:
    """Click the form submit button (button[type=submit])"""
    page.locator('button[type="submit"]').first.click()
    wait_for_spinner_gone(page)


def click_button(page: Page, label: str) -> None:
    """Click a q-btn by label text. Caller must wait for the expected result."""
    page.locator(f'.q-btn:has-text("{label}")').first.click()


def click_button_by_aria(page: Page, aria_label: str) -> None:
    """Click a button or link by its aria-label attribute. Caller must wait."""
    page.locator(f'[aria-label="{aria_label}"]').first.click()


def click_button_if_visible(page: Page, label: str, timeout: int = 3000) -> bool:
    """Wait for q-btn to appear, click if found. Returns whether clicked."""
    btn = page.locator(f'.q-btn:has-text("{label}")').first
    try:
        btn.wait_for(state="visible", timeout=timeout)
    except PlaywrightTimeoutError:
        return False
    btn.click()
    return True


# ========================================
# WIZARD NAVIGATION HELPERS
# ========================================


def click_next_step(page: Page) -> None:
    """Click the Next step arrow button in wizard footer"""
    page.locator(BTN_NEXT_STEP).first.click()
    wait_for_spinner_gone(page)


def click_finish(page: Page) -> None:
    """Click the Finish button and wait for redirect away from edit page"""
    page.locator(BTN_FINISH).first.click()
    page.wait_for_url("**/characters/**", timeout=10000)
    expect(page).not_to_have_url(re.compile(r"/edit"), timeout=10000)
    wait_for_spinner_gone(page)


# ========================================
# SELECTABLE CARD HELPERS
# ========================================


def select_first_card(page: Page, name: str) -> None:
    """Click the first unselected SelectableCard. Raises if none found."""
    cards = page.locator(SELECTABLE_CARD_UNSELECTED)
    if cards.count() > 0:
        # Use nth(0) for a stable positional locator that won't shift
        all_cards = page.locator(SELECTABLE_CARD)
        first_idx = 0
        for i in range(all_cards.count()):
            cls = all_cards.nth(i).get_attribute("class") or ""
            if "card-selected" not in cls:
                first_idx = i
                break
        all_cards.nth(first_idx).click()
        expect(all_cards.nth(first_idx)).to_have_attribute("aria-checked", "true", timeout=5000)
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


def click_increment(page: Page, name: str) -> None:
    """Click increment button by aria-label 'Increase {name}'"""
    btn = page.locator(BTN_INCREMENT.format(name=name)).first
    if btn.count() > 0:
        btn.click()
        wait_for_spinner_gone(page)
        print(f"   [OK] Incremented {name}")
        return
    raise AssertionError(f"Cannot increment {name}: button not found")


def click_increment_rank(page: Page, name: str) -> None:
    """Click increment button by aria-label 'Increase {name} rank'"""
    btn = page.locator(BTN_INCREMENT_RANK.format(name=name)).first
    if btn.count() > 0:
        btn.click()
        wait_for_spinner_gone(page)
        print(f"   [OK] Incremented {name} rank")
        return
    raise AssertionError(f"Cannot increment {name} rank: button not found")


def click_decrement(page: Page, name: str) -> None:
    """Click decrement button by aria-label 'Decrease {name}'"""
    btn = page.locator(BTN_DECREMENT.format(name=name)).first
    if btn.count() > 0:
        btn.click()
        wait_for_spinner_gone(page)
        print(f"   [OK] Decremented {name}")
        return
    raise AssertionError(f"Cannot decrement {name}: button not found")


# ========================================
# QUASAR TAB HELPERS
# ========================================


def click_tab(page: Page, tab_label: str) -> None:
    """Click a q-tab by label text and wait for it to become active"""
    tab = page.locator(f'.q-tab:has-text("{tab_label}")').first
    tab.click()
    expect(tab).to_have_attribute("class", re.compile(r"q-tab--active"), timeout=5000)


# ========================================
# QUASAR DIALOG HELPERS
# ========================================


def wait_for_dialog(page: Page, timeout: int = 5000) -> Locator:
    """Wait for q-dialog to be visible and return it"""
    dialog = page.locator(".q-dialog").first
    dialog.wait_for(state="visible", timeout=timeout)
    return dialog


def confirm_dialog(page: Page, button_label: str = "OK") -> None:
    """Click confirm button in dialog and wait for it to close"""
    dialog = page.locator(".q-dialog")
    dialog.first.locator(f'.q-btn:has-text("{button_label}")').first.click()
    expect(dialog).to_have_count(0, timeout=5000)


def dismiss_dialog(page: Page, button_label: str = "Cancel") -> None:
    """Click cancel button in dialog and wait for it to close"""
    dialog = page.locator(".q-dialog")
    dialog.first.locator(f'.q-btn:has-text("{button_label}")').first.click()
    expect(dialog).to_have_count(0, timeout=5000)


# ========================================
# LISTBOX / LIST ITEM HELPERS
# ========================================


def open_dialog_and_select_first(page: Page, button_text: str, name: str) -> None:
    """Click button to open dialog, select first listbox item, close dialog"""
    btn = page.locator(f'.q-btn:has-text("{button_text}")').first
    if btn.count() == 0:
        raise AssertionError(f"{name} button not found")
    btn.click()
    wait_for_dialog(page)
    items = page.locator(LISTBOX_ITEM)
    try:
        items.first.wait_for(state="visible", timeout=5000)
    except PlaywrightTimeoutError as exc:
        raise AssertionError(f"No {name} list items found") from exc
    items.first.click()
    wait_for_spinner_gone(page)
    print(f"   [OK] {name} selected from list")
    # Close dialog if still open
    dialog = page.locator(".q-dialog")
    if dialog.count() > 0:
        done_btn = dialog.first.locator('.q-btn:has-text("Done"), .q-btn:has-text("Close")').first
        if done_btn.count() > 0:
            done_btn.click()
            expect(dialog).to_have_count(0, timeout=5000)


def click_first_listbox_item(page: Page, name: str) -> None:
    """Click the first item in a q-list with role='option' (path/kit dialogs)"""
    items = page.locator(LISTBOX_ITEM)
    try:
        items.first.wait_for(state="visible", timeout=5000)
    except PlaywrightTimeoutError as exc:
        raise AssertionError(f"No {name} list items found") from exc
    items.first.click()
    wait_for_spinner_gone(page)
    print(f"   [OK] {name} selected from list")


# ========================================
# CHECKBOX HELPERS
# ========================================


def click_first_checkbox(page: Page, name: str) -> None:
    """Click the first unchecked q-checkbox"""
    unchecked = page.locator(f'{EXPERTISE_CHECKBOX}[aria-checked="false"]')
    if unchecked.count() > 0:
        # Get aria-label for a stable locator that won't shift after check
        label = unchecked.first.get_attribute("aria-label") or ""
        unchecked.first.click()
        if label:
            target = page.locator(f'[aria-label="{label}"]').first
            expect(target).to_have_attribute("aria-checked", "true", timeout=5000)
        else:
            wait_for_spinner_gone(page)
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


def click_aria_toggle(page: Page, aria_label: str) -> None:
    """Click a toggle element by aria-label (conditions, switches). Raises if not found."""
    el = page.locator(f'[aria-label="{aria_label}"]').first
    if el.count() == 0:
        raise AssertionError(f"Toggle '{aria_label}' not found")
    el.click()
    wait_for_spinner_gone(page)


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
    menu = page.locator(".q-menu")
    menu.first.wait_for(state="visible", timeout=5000)
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
    """Assert text is visible on page. Auto-retries until timeout."""
    element = page.locator(f'text="{text}"').first
    expect(element).to_be_visible(timeout=timeout)
    print(f"   [OK] Text visible: {text}")


def verify_url_contains(page: Page, path: str, description: Optional[str] = None) -> None:
    """Assert current URL contains path. Raises if not."""
    current_url = page.url
    if path in current_url:
        msg = description or f"URL contains '{path}'"
        print(f"   [OK] {msg}: {current_url}")
        return
    raise AssertionError(f"Expected '{path}' in URL, got: {current_url}")


def verify_input_value(page: Page, value: str, name: str, timeout: int = 5000) -> None:
    """Assert input element contains expected value with auto-retry. Raises if not found."""
    loc = page.locator(f'input[value="{value}"]')
    try:
        loc.first.wait_for(state="visible", timeout=timeout)
    except PlaywrightTimeoutError as exc:
        raise AssertionError(f"{name} not found in any input (expected value: {value})") from exc
    print(f"   [OK] {name}: {value}")


def wait_for_text_change(locator: Locator, old_text: str, timeout: int = 5000) -> str:
    """Wait until a locator's inner_text differs from old_text. Returns the new text."""
    expect(locator).not_to_have_text(old_text, timeout=timeout)
    return locator.inner_text().strip()


def wait_for_class_change(
    locator: Locator, substring: str, want_present: bool, timeout: int = 5000
) -> None:
    """Wait until a locator's class attribute contains (or stops containing) substring."""
    pattern = re.compile(rf".*{re.escape(substring)}.*")
    if want_present:
        expect(locator).to_have_attribute("class", pattern, timeout=timeout)
    else:
        expect(locator).not_to_have_attribute("class", pattern, timeout=timeout)


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


def wait_for_either_visible(
    populated: Locator, empty: Locator, name: str, timeout: int = 5000
) -> str:
    """Wait for either populated or empty-state locator to become visible.

    Returns 'populated' or 'empty'. Raises if neither appears.
    """
    try:
        populated.first.wait_for(state="visible", timeout=timeout)
        return "populated"
    except PlaywrightTimeoutError:
        pass
    try:
        empty.first.wait_for(state="visible", timeout=timeout // 2)
        return "empty"
    except PlaywrightTimeoutError as exc:
        raise AssertionError(f"{name}: neither populated nor empty state detected") from exc


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
# ERROR PAGE HELPERS
# ========================================


def verify_error_page(page: Page, expected_code: str, expected_title: str) -> None:
    """Verify an error page displays the expected code and title."""
    verify_element_exists(page, ERROR_CODE, "Error code")
    expect(page.locator(ERROR_CODE).first).to_have_text(expected_code, timeout=5000)
    expect(page.locator(ERROR_TITLE).first).to_have_text(expected_title, timeout=5000)
    print(f"   [OK] {expected_code} {expected_title}")


# ========================================
# EXPANSION PANEL HELPERS
# ========================================


def expand_section(page: Page, aria_label: str) -> None:
    """Expand a q-expansion-item by aria-label if it is collapsed."""
    section = page.locator(f'[aria-label="{aria_label}"]')
    try:
        section.first.wait_for(state="visible", timeout=10000)
    except PlaywrightTimeoutError as exc:
        raise AssertionError(f"Section '{aria_label}' not found on {page.url}") from exc
    el = section.first
    classes = el.get_attribute("class") or ""
    if "q-expansion-item--collapsed" in classes:
        # Click the expansion header toggle
        toggle = el.locator(".q-expansion-item__toggle")
        if toggle.count() > 0:
            toggle.first.click()
        else:
            el.locator(".q-item").first.click()
        wait_for_class_change(el, "q-expansion-item--collapsed", want_present=False)
        wait_for_spinner_gone(page)


# ========================================
# CLEANUP HELPERS
# ========================================


def select_all_checkboxes_in_dialog(page: Page) -> None:
    """Check all unchecked q-checkboxes in the currently open dialog."""
    dialog = page.locator(".q-dialog").first
    unchecked = dialog.locator(f'{EXPERTISE_CHECKBOX}[aria-checked="false"]')
    count = unchecked.count()
    if count == 0:
        raise AssertionError("No unchecked checkboxes found in dialog")
    for _ in range(count):
        unchecked.nth(0).click()  # Always click first unchecked (list shifts after check)
    remaining = dialog.locator(f'{EXPERTISE_CHECKBOX}[aria-checked="false"]').count()
    if remaining > 0:
        raise AssertionError(f"{remaining} checkboxes still unchecked after selection")
    print(f"   [OK] Selected {count} checkboxes in dialog")


def create_campaign_with_source_books(page: Page, base_url: str, campaign_name: str) -> str:
    """Create a campaign with all source books selected.

    Returns the campaign detail URL path (e.g. /campaigns/5).
    """
    navigate_to(page, base_url, "/campaigns")
    wait_for_spinner_gone(page)
    click_button(page, "Create Campaign")
    wait_for_page_load(page)

    fill_input(page, "Campaign Name", campaign_name)

    # Open source book dialog and select all
    click_button(page, "Manage Source Books")
    wait_for_dialog(page)
    select_all_checkboxes_in_dialog(page)
    confirm_dialog(page, "Confirm")

    click_button(page, "Create")
    wait_for_page_load(page)
    wait_for_spinner_gone(page)

    # Extract and validate campaign URL path
    from urllib.parse import urlparse

    path = urlparse(page.url).path
    if path in ("/campaigns", "/campaigns/new"):
        raise AssertionError(f"Campaign creation failed for '{campaign_name}': stuck on {path}")
    print(f"   [OK] Campaign '{campaign_name}' created at {path}")
    return path


def navigate_to_campaign_character_creation(page: Page, base_url: str, campaign_path: str) -> None:
    """Navigate to character creation via a campaign's join page.

    campaign_path: e.g. /campaigns/5 (from create_campaign_with_source_books)
    """
    navigate_to(page, base_url, campaign_path)
    wait_for_spinner_gone(page)

    click_button(page, "Add Character")
    wait_for_page_load(page)
    wait_for_spinner_gone(page)

    click_button(page, "Create Character")
    wait_for_page_load(page)
    wait_for_spinner_gone(page)
    print("   [OK] Character creation loaded via campaign")


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
        traceback.print_exc()


def extract_hero_id_from_url(page: Page) -> Optional[int]:
    """Extract hero ID from URLs like /characters/{id} or /characters/{id}/edit."""
    from urllib.parse import urlparse

    path = urlparse(page.url).path
    match = re.search(r"/characters/(\d+)(?:/|$)", path)
    return int(match.group(1)) if match else None


def cleanup_test_hero(page: Page, base_url: str, hero_id: int) -> None:
    """Navigate to character edit and delete via Review tab. Swallows errors."""
    try:
        navigate_to(page, base_url, f"/characters/{hero_id}/edit")
        wait_for_spinner_gone(page)
        click_tab(page, "Review")
        wait_for_spinner_gone(page)
        click_button(page, "Delete Character")
        wait_for_dialog(page)
        page.locator(DELETE_CONFIRM_INPUT).first.click()
        page.locator(DELETE_CONFIRM_INPUT).first.fill("delete")
        wait_for_spinner_gone(page)
        confirm_dialog(page, "Delete")
        wait_for_page_load(page)
        print(f"   [CLEANUP] Test hero {hero_id} deleted")
    except Exception as cleanup_err:
        print(f"   [CLEANUP WARN] {cleanup_err}")
        traceback.print_exc()


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
