"""
Authentication Manager for RPG E2E Tests

Strategies (in order):
1. Explicit credentials from .env (TEST_USERNAME/TEST_PASSWORD)
2. Saved test user credentials from registration (test_user.json)
3. Saved browser context (cookies/session)

No manual login -- all automated.
"""

import json
from pathlib import Path

from e2e.common.config import get_config
from e2e.common.helpers import click_button, fill_input, wait_for_page_load

AUTH_DIR = Path(__file__).parent / ".auth"
TEST_USER_PATH = AUTH_DIR / "test_user.json"
CONTEXT_PATH = AUTH_DIR / "context.json"


def save_test_user(username: str, password: str) -> None:
    """Save test user credentials for reuse across tests"""
    AUTH_DIR.mkdir(parents=True, exist_ok=True)
    TEST_USER_PATH.write_text(
        json.dumps({"username": username, "password": password}),
        encoding="utf-8",
    )
    print(f"   [OK] Saved test user credentials to {TEST_USER_PATH}")


def load_test_user() -> dict[str, str] | None:
    """Load saved test user credentials"""
    if TEST_USER_PATH.exists():
        try:
            data: dict[str, str] = json.loads(TEST_USER_PATH.read_text(encoding="utf-8"))
            if data.get("username") and data.get("password"):
                return data
        except (json.JSONDecodeError, KeyError):
            pass
    return None


class AuthManager:
    """Manages authentication for E2E tests"""

    def __init__(self, base_url=None, username=None, password=None) -> None:
        self.config = get_config()
        self.base_url = base_url or self.config["web_url"]
        self.context_path = CONTEXT_PATH

        # Priority: explicit args > .env config > saved test user
        if username and password:
            self.credentials = {"username": username, "password": password}
        elif self.config["username"] and self.config["password"]:
            self.credentials = {
                "username": self.config["username"],
                "password": self.config["password"],
            }
        else:
            self.credentials = load_test_user() or {
                "username": None,
                "password": None,
            }

    def save_context(self, context):
        """Save browser context (cookies/session) for reuse"""
        AUTH_DIR.mkdir(parents=True, exist_ok=True)
        context.storage_state(path=str(self.context_path))
        print(f"   [OK] Saved auth context to {self.context_path}")

    def load_context(self, browser):
        """Load saved browser context if available"""
        if not self.context_path.exists():
            return None
        try:
            context = browser.new_context(
                storage_state=str(self.context_path),
                ignore_https_errors=self.config.get("ignore_https_errors", False),
            )
            print("   [OK] Loaded saved auth context")
            return context
        except Exception as e:
            print(f"   [WARN] Could not load saved context: {e}")
            return None

    def login_with_credentials(self, page, username=None, password=None):
        """Login using Quasar form on /login page"""
        creds = (
            {"username": username, "password": password}
            if username and password
            else self.credentials
        )

        if not creds["username"] or not creds["password"]:
            print("   [FAIL] No credentials available")
            return False

        print(f"   [INFO] Logging in as: {creds['username']}")

        page.goto(f"{self.base_url}/login")
        wait_for_page_load(page)

        fill_input(page, "Username", creds["username"])
        fill_input(page, "Password", creds["password"])
        click_button(page, "Login")

        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000)

        if "/login" not in page.url:
            print("   [OK] Login successful")
            return True

        print("   [FAIL] Login failed - still on login page")
        return False

    def authenticate(self, browser, strategy="auto"):
        """
        Authenticate using specified strategy.

        Strategies:
        - 'auto': Try credentials first, fallback to saved context
        - 'context': Use saved context only
        - 'credentials': Use credentials only
        """
        print("\n[AUTH] Starting authentication...")
        print(f"[AUTH] Base URL: {self.base_url}")

        # Try credentials (from .env or saved test user)
        if strategy in ["auto", "credentials"] and self.credentials.get("username"):
            context = browser.new_context(
                ignore_https_errors=self.config.get("ignore_https_errors", False)
            )
            page = context.new_page()

            if self.login_with_credentials(page):
                self.save_context(context)
                return page, context

            page.close()
            context.close()

            if strategy == "credentials":
                raise RuntimeError(
                    "Authentication failed: Invalid credentials. "
                    "Check .env or run registration test first."
                )

        # Try saved browser context
        if strategy in ["auto", "context"]:
            context = self.load_context(browser)
            if context:
                page = context.new_page()
                page.goto(self.base_url)
                wait_for_page_load(page)

                if "/login" not in page.url:
                    print("   [OK] Authenticated via saved context")
                    return page, context

                print("   [INFO] Saved context expired")
                page.close()
                context.close()

        raise RuntimeError(
            "Authentication failed: No valid credentials or context. "
            "Run registration test first, or configure .env credentials."
        )


def authenticate_for_testing(browser, base_url=None, strategy="auto"):
    """
    Convenience function for test scripts.

    Raises RuntimeError if authentication fails.
    Returns: (page, context) tuple
    """
    auth_manager = AuthManager(base_url)
    return auth_manager.authenticate(browser, strategy)
