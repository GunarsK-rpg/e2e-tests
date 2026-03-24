#!/usr/bin/env python3
"""
RPG E2E Test Suite Runner
Runs E2E tests in order: auth -> characters -> campaigns -> combat
"""

import argparse
import os
import subprocess
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path


class TestRunner:
    """Manages and runs RPG E2E tests"""

    def __init__(self):
        self.testing_dir = Path(__file__).parent
        self.results = []
        self.start_time = None
        self.end_time = None

    def run_test(self, test_path, test_name):
        """Run a single test file"""
        print("\n" + "=" * 70)
        print(f"Running: {test_name}")
        print("=" * 70)

        try:
            env = os.environ.copy()
            env["PYTHONPATH"] = str(self.testing_dir)

            result = subprocess.run(
                [sys.executable, str(test_path)],
                cwd=str(self.testing_dir),
                capture_output=False,
                timeout=300,
                check=False,
                env=env,
            )

            success = result.returncode == 0
            self.results.append(
                {
                    "name": test_name,
                    "path": test_path,
                    "success": success,
                    "returncode": result.returncode,
                }
            )

            return success

        except subprocess.TimeoutExpired:
            print("\n[TIMEOUT] Test exceeded 5 minute timeout")
            self.results.append(
                {
                    "name": test_name,
                    "path": test_path,
                    "success": False,
                    "returncode": -1,
                    "error": "Timeout",
                }
            )
            return False

        except (OSError, PermissionError) as e:
            print(f"\n[ERROR] Failed to run test: {e}")
            print(f"Traceback:\n{traceback.format_exc()}")
            self.results.append(
                {
                    "name": test_name,
                    "path": test_path,
                    "success": False,
                    "returncode": -1,
                    "error": str(e),
                }
            )
            return False

    def get_tests(self):
        """Get ordered list of all tests"""
        base = self.testing_dir / "e2e"
        return [
            # Registration must run first -- creates test user for all tests
            (base / "auth-flow" / "test_register.py", "Registration Flow"),
            (base / "auth-flow" / "test_login.py", "Login Flow"),
            # Character tests
            (base / "characters" / "test_character_creation.py", "Character Creation"),
            (base / "characters" / "test_character_sheet.py", "Character Sheet"),
            (base / "characters" / "test_character_deletion.py", "Character Deletion"),
            # Campaign tests
            (base / "campaigns" / "test_campaign_crud.py", "Campaign CRUD"),
            (base / "campaigns" / "test_campaign_join.py", "Campaign Join"),
            # Combat tests
            (base / "combat" / "test_npc_library.py", "NPC Library"),
            (base / "combat" / "test_combat_encounter.py", "Combat Encounter"),
        ]

    def run_tests(self, skip_missing=False):
        """Run all tests in order"""
        self.start_time = datetime.now(timezone.utc)

        tests = self.get_tests()

        print("\n" + "=" * 70)
        print("RPG E2E TEST SUITE")
        print("=" * 70)
        print(f"Starting test run at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total tests: {len(tests)}")

        for test_path, test_name in tests:
            if test_path.exists():
                self.run_test(test_path, test_name)
            elif skip_missing:
                print(f"\n[SKIP] Test not found (skipped): {test_path}")
            else:
                print(f"\n[SKIP] Test not found: {test_path}")
                self.results.append(
                    {
                        "name": test_name,
                        "path": test_path,
                        "success": False,
                        "error": "Test file not found",
                    }
                )

        self.end_time = datetime.now(timezone.utc)
        return self.print_summary()

    def print_summary(self):
        """Print test execution summary"""
        duration = (self.end_time - self.start_time).total_seconds()

        print("\n" + "=" * 70)
        print("RPG E2E TEST SUITE SUMMARY")
        print("=" * 70)

        passed = sum(1 for r in self.results if r["success"])
        failed = len(self.results) - passed

        print(f"\nTotal Tests: {len(self.results)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Duration: {duration:.2f} seconds")

        if failed > 0:
            print("\nFailed Tests:")
            for result in self.results:
                if not result["success"]:
                    error_msg = result.get(
                        "error", f"Exit code: {result.get('returncode', 'unknown')}"
                    )
                    print(f"  - {result['name']}: {error_msg}")

        print("\nPassed Tests:")
        for result in self.results:
            if result["success"]:
                print(f"  - {result['name']}")

        print("\n" + "=" * 70)

        return passed == len(self.results)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Run RPG E2E tests")
    parser.add_argument(
        "--no-confirm",
        action="store_true",
        help="Skip confirmation prompt",
    )
    parser.add_argument(
        "--skip-missing",
        action="store_true",
        help="Skip missing test files instead of reporting them as failures",
    )

    args = parser.parse_args()

    runner = TestRunner()

    if args.no_confirm or not sys.stdin.isatty():
        print("\n" + "=" * 70)
        print("RPG E2E TEST SUITE")
        print("=" * 70)
        print("\nRunning RPG E2E tests...")
    else:
        print("\n" + "=" * 70)
        print("RPG E2E TEST SUITE")
        print("=" * 70)
        print("\nThis will run RPG E2E tests.")
        print("Requires RPG services running via docker-compose.")
        print("\nPress Enter to continue or Ctrl+C to cancel...")

        try:
            input()
        except KeyboardInterrupt:
            print("\n\nTest run cancelled.")
            return 1

    all_passed = runner.run_tests(skip_missing=args.skip_missing)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
