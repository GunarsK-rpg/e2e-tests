# E2E Tests

End-to-end tests for the Cosmere RPG application using Playwright and Python.

## Quick Start

```bash
# Setup
pip install -r requirements.txt
playwright install chromium
task setup:env                    # Create .env from template

# Run tests (registration creates a fresh user automatically)
task test:all                     # All tests (browser visible)
task test:all:headless            # All tests (headless mode)
task test:characters:creation     # Individual test suite
```

## Prerequisites

- Python 3.12+
- Running services via Docker Compose

Start services:

```bash
cd ../infrastructure
docker-compose up -d
```

## Available Commands

### Testing

```bash
# All tests
task test:all                     # Run all E2E tests (browser visible)
task test:all:headless            # Run all tests headless
task test:all:interactive         # Run with confirmation prompt

# Auth tests
task test:auth                    # Registration + Login
task test:auth:register           # Registration flow
task test:auth:login              # Login flow

# Character tests
task test:characters              # All character tests
task test:characters:creation     # Character creation wizard
task test:characters:sheet        # Character sheet tabs
task test:characters:deletion     # Character deletion

# Campaign tests
task test:campaigns               # All campaign tests
task test:campaigns:crud          # Campaign CRUD
task test:campaigns:join          # Campaign join via invite

# Combat tests
task test:combat                  # All combat tests
task test:combat:npc              # NPC library
task test:combat:encounter        # Combat encounter
```

### Code Quality

```bash
task lint                         # Run all linters (black, flake8, isort, pylint, mypy)
task format                       # Auto-format code
task ci:all                       # Run all CI checks
```

### Maintenance

```bash
task setup                        # Install dependencies
task setup:env                    # Create .env
task clean                        # Clean screenshots and auth context
task clean:cache                  # Clean Python cache
task list                         # List all test suites
```

## Test Suites

Tests run in order: registration creates the test user, then all subsequent tests authenticate with those credentials.

### Auth Flow (2 suites)

- **Registration Flow** - Register new user, save credentials, verify login
- **Login Flow** - Login, session persistence, unauthorized redirect, logout, access denied

### Character Tests (3 suites)

- **Character Creation** - 10-step wizard: name, ancestry, culture, attributes, skills, expertises, paths, starting kit, equipment, personal details, review
- **Character Sheet** - Tab navigation: Stats, Skills, Actions, Equipment, Talents, Expertises, Conditions, Companions, Others
- **Character Deletion** - Edit mode, navigate to Review step, delete with confirmation

### Campaign Tests (2 suites)

- **Campaign CRUD** - Create, verify detail page, edit description, delete, verify redirect
- **Campaign Join** - Create campaign, get invite link, navigate join page, verify content, cleanup

### Combat Tests (2 suites)

- **NPC Library** - Create campaign, create NPC (name, tier, type, size), search, edit name, archive, cleanup
- **Combat Encounter** - Create campaign + combat, verify detail, add NPC via dialog, check tiles, phase toggle, active toggle, cleanup

## Authentication

Tests use a multi-strategy auth system:

1. **Explicit credentials** - From `.env` (optional, skips registration)
2. **Saved test user** - Created by registration test, persisted to `e2e/auth/.auth/`
3. **Saved browser context** - Reuses session cookies from previous run

By default, the registration test runs first and creates a fresh `e2e_test_<timestamp>` user. All subsequent tests authenticate with those saved credentials.

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `TEST_USERNAME` | Skip registration, use existing account | - |
| `TEST_PASSWORD` | Skip registration, use existing account | - |
| `TEST_WEB_URL` | Frontend URL | `https://localhost:8543` |
| `TEST_API_URL` | API URL | `https://localhost:8543/api/v1` |
| `TEST_AUTH_URL` | Auth service URL | `https://localhost:8443/auth/v1` |
| `TEST_BROWSER` | Browser engine | `chromium` |
| `TEST_HEADLESS` | Run headless | `false` |
| `TEST_IGNORE_HTTPS_ERRORS` | Skip TLS verification | `true` |
| `TEST_TIMEOUT` | Default timeout (ms) | `30000` |
| `TEST_SLOW_MO` | Slow motion delay (ms) | `0` |
| `TEST_SCREENSHOT_DIR` | Screenshot output dir | System temp |

## Project Structure

```text
e2e-tests/
├── e2e/
│   ├── auth/                 # Auth manager and context persistence
│   ├── auth-flow/            # Registration and login tests
│   ├── campaigns/            # Campaign CRUD and join tests
│   ├── characters/           # Character creation, sheet, deletion
│   ├── combat/               # NPC library and combat encounters
│   └── common/               # Shared config, helpers, selectors
├── run_tests.py              # Test runner (ordered execution)
├── Taskfile.yml              # Task commands
├── requirements.txt          # Python dependencies
└── pyproject.toml            # Linter configuration
```

## CI/CD

GitHub Actions workflow (`.github/workflows/ci.yml`) runs on push/PR:

- black, flake8, isort formatting checks
- pylint static analysis
- mypy type checking
- Test compilation verification

## Linting

All code passes with **pylint 10.00/10**:

- **black** - Code formatting (100 char line length)
- **flake8** - Style and syntax
- **isort** - Import sorting
- **pylint** - Static analysis
- **mypy** - Type checking

## Development

Add a new test:

```python
from e2e.auth.auth_manager import authenticate_for_testing
from e2e.common.config import get_config
from playwright.sync_api import sync_playwright

config = get_config()

def test_new_feature():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=config["headless"])
        page = None
        context = None
        try:
            page, context = authenticate_for_testing(browser)
            # Test logic here
            return True
        except Exception as e:
            print(f"\n[ERROR] {e}")
            if page is not None:
                take_screenshot(page, "error", "Error")
            return False
        finally:
            if context is not None:
                context.close()
            browser.close()
```

Add task to `Taskfile.yml`:

```yaml
test:new-feature:
  desc: Run new feature test
  cmds:
    - python e2e/path/test_new_feature.py
```

## Notes

- Tests run with browser visible by default
- Screenshots saved to system temp directory (configurable via `TEST_SCREENSHOT_DIR`)
- Registration must run first to create the test user
- Test data uses timestamps for uniqueness to avoid collisions
- Campaign/combat tests clean up after themselves
- Helper-based selectors in `e2e/common/helpers.py` avoid raw CSS selectors in tests
