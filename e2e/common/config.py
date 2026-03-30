"""
Configuration manager for E2E tests
Loads settings from .env file and environment variables
"""

import os
import re
import tempfile
import threading
from pathlib import Path
from typing import Any, Dict, Optional


class TestConfig:
    """Manages test configuration from .env file and environment variables"""

    def __init__(self):
        self.config = self._load_config()

    def _load_env_file(self) -> Dict[str, str]:
        """Load variables from .env file"""
        config_file_path = Path(__file__).resolve()
        project_dir = config_file_path.parent.parent.parent
        env_file = project_dir / ".env"
        env_vars = {}

        if env_file.exists():
            try:
                with open(env_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, value = line.split("=", 1)
                            # Strip inline comments - only if # is preceded by whitespace
                            # This preserves URLs with hash fragments
                            value = re.sub(r"\s+#.*$", "", value)
                            env_vars[key.strip()] = value.strip().strip("\"'")
            except Exception as e:
                print(f"[WARN] Could not read .env file: {e}")

        return env_vars

    def _get_value(
        self, key: str, default: Any = None, env_vars: Optional[Dict[str, str]] = None
    ) -> Any:
        """Get value from environment or .env file, with fallback to default"""
        value = os.getenv(key)
        if value is not None:
            return value

        if env_vars and key in env_vars:
            return env_vars[key]

        return default

    @staticmethod
    def _parse_int(value: Any, default: int) -> int:
        """Parse integer from string, returning default on failure"""
        try:
            return int(value)
        except ValueError, TypeError:
            return default

    def _parse_bool(self, value: Any) -> bool:
        """Parse boolean from string"""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes", "on")
        return bool(value)

    def _load_config(self) -> Dict[str, Any]:
        """Load all configuration"""
        env_vars = self._load_env_file()

        return {
            # Authentication
            "username": self._get_value("TEST_USERNAME", env_vars=env_vars),
            "password": self._get_value("TEST_PASSWORD", env_vars=env_vars),
            # URLs
            "web_url": self._get_value("TEST_WEB_URL", "https://localhost:8543", env_vars),
            "api_url": self._get_value("TEST_API_URL", "https://localhost:8543/api/v1", env_vars),
            "auth_url": self._get_value(
                "TEST_AUTH_URL", "https://localhost:8443/auth/v1", env_vars
            ),
            # Test behavior
            "headless": self._parse_bool(self._get_value("TEST_HEADLESS", "false", env_vars)),
            "screenshot_dir": self._get_value(
                "TEST_SCREENSHOT_DIR", tempfile.gettempdir(), env_vars
            ),
            "slow_mo": self._parse_int(self._get_value("TEST_SLOW_MO", "0", env_vars), 0),
            "timeout": self._parse_int(self._get_value("TEST_TIMEOUT", "30000", env_vars), 30000),
            # Browser options
            "browser": self._get_value("TEST_BROWSER", "chromium", env_vars),
            "ignore_https_errors": self._parse_bool(
                self._get_value("TEST_IGNORE_HTTPS_ERRORS", "true", env_vars)
            ),
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config.get(key, default)

    def __getitem__(self, key: str) -> Any:
        """Allow dict-like access"""
        return self.config[key]

    def __str__(self) -> str:
        """String representation (with password masked)"""
        safe_config = self.config.copy()
        if "password" in safe_config:
            safe_config["password"] = "***"
        return str(safe_config)


# Global config instance
_config = None
_config_lock = threading.Lock()


def get_config() -> TestConfig:
    """Get global config instance (singleton)"""
    global _config
    if _config is None:
        with _config_lock:
            if _config is None:
                _config = TestConfig()
    return _config
