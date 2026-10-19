import os
import re
import tempfile
from collections.abc import Generator
from contextlib import contextmanager
from contextvars import ContextVar, Token
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import dotenv_values
from google import genai




ENVIRONMENT_SETTINGS_FILE = Path("/data/env.txt")
ENVIRONMENT_SETTINGS = (
    "GOOGLE_API_KEY",
    "URI",
    "DB_NAME",
    "COLLECTION_NAME",
)
_google_api_key: ContextVar[str | None] = ContextVar("google_api_key", default=None)
_google_client: ContextVar[genai.Client | None] = ContextVar("google_client", default=None)


def get_google_api_key() -> str | None:
    return _google_api_key.get() or get_configured_google_api_key()


def get_saved_google_api_key() -> str | None:
    return get_saved_environment_setting("GOOGLE_API_KEY")


def get_configured_google_api_key() -> str | None:
    return get_environment_setting("GOOGLE_API_KEY")


def get_saved_environment_setting(name: str) -> str | None:
    if name not in ENVIRONMENT_SETTINGS or not ENVIRONMENT_SETTINGS_FILE.exists():
        return None
    return dotenv_values(ENVIRONMENT_SETTINGS_FILE).get(name)


def get_environment_setting(name: str) -> str | None:
    if name not in ENVIRONMENT_SETTINGS:
        raise ValueError(f"Unsupported environment setting: {name}")
    return get_saved_environment_setting(name) or os.environ.get(name)


def is_google_api_key_saved() -> bool:
    return get_saved_google_api_key() is not None


def _write_env_file(contents: str) -> None:
    ENVIRONMENT_SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=ENVIRONMENT_SETTINGS_FILE.parent,
            prefix=".env-",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            os.fchmod(temporary_file.fileno(), 0o600)
            temporary_file.write(contents)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        temporary_path.replace(ENVIRONMENT_SETTINGS_FILE)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink(missing_ok=True)


def save_environment_settings(settings: dict[str, str]) -> None:
    existing_lines = []
    if ENVIRONMENT_SETTINGS_FILE.exists():
        existing_lines = [
            line
            for line in ENVIRONMENT_SETTINGS_FILE.read_text(encoding="utf-8").splitlines()
            if not any(
                re.match(rf"^\s*(?:export\s+)?{re.escape(name)}\s*=", line)
                for name in settings
            )
        ]
    for name, value in settings.items():
        escaped_value = value.replace("\\", "\\\\").replace('"', '\\"')
        existing_lines.append(f'{name}="{escaped_value}"')
    _write_env_file("\n".join(existing_lines) + "\n")


def save_google_api_key(api_key: str) -> None:
    save_environment_settings({"GOOGLE_API_KEY": api_key})


def remove_environment_setting(name: str) -> bool:
    if name not in ENVIRONMENT_SETTINGS:
        raise ValueError(f"Unsupported environment setting: {name}")
    if not ENVIRONMENT_SETTINGS_FILE.exists():
        return False
    contents = ENVIRONMENT_SETTINGS_FILE.read_text(encoding="utf-8")
    existing_lines = [
        line
        for line in contents.splitlines()
        if not re.match(rf"^\s*(?:export\s+)?{re.escape(name)}\s*=", line)
    ]
    if len(existing_lines) == len(contents.splitlines()):
        return False
    if any(line.strip() for line in existing_lines):
        _write_env_file("\n".join(existing_lines) + "\n")
    else:
        ENVIRONMENT_SETTINGS_FILE.unlink()
    return True


def remove_google_api_key() -> bool:
    return remove_environment_setting("GOOGLE_API_KEY")


def environment_settings_file_has_data() -> bool:
    saved_settings = (
        dotenv_values(ENVIRONMENT_SETTINGS_FILE)
        if ENVIRONMENT_SETTINGS_FILE.exists()
        else {}
    )
    return any(
        isinstance(value, str) and value.strip()
        for value in saved_settings.values()
    )


def environment_settings_status() -> dict[str, dict[str, bool]]:
    saved_settings = (
        dotenv_values(ENVIRONMENT_SETTINGS_FILE)
        if ENVIRONMENT_SETTINGS_FILE.exists()
        else {}
    )
    return {
        name: {
            "saved": bool(saved_settings.get(name)),
            "configured": bool(saved_settings.get(name) or os.environ.get(name)),
            "valid": bool(saved_settings.get(name))
            and validate_environment_setting(name, saved_settings[name]) is None,
        }
        for name in ENVIRONMENT_SETTINGS
    }


def validate_environment_setting(name: str, value: str) -> str | None:
    if not value:
        return "This setting is required."
    if len(value) > (512 if name == "GOOGLE_API_KEY" else 4096):
        return "Value is too long."
    if "\n" in value or "\r" in value:
        return "Line breaks are not allowed."
    if name == "URI":
        try:
            parsed_uri = urlsplit(value)
            if parsed_uri.scheme not in ("mongodb", "mongodb+srv") or not parsed_uri.hostname:
                return "Enter a valid MongoDB URI starting with mongodb:// or mongodb+srv://."
        except ValueError:
            return "Enter a valid MongoDB URI."
    elif name == "DB_NAME":
        if len(value) > 63 or any(character in value for character in '/\\."$*<>:|?\0'):
            return "Enter a valid MongoDB database name (1–63 characters, without reserved characters)."
    elif name == "COLLECTION_NAME":
        if len(value) > 120 or "\0" in value or value.startswith("system."):
            return "Enter a valid MongoDB collection name (up to 120 characters)."
    return None


@lru_cache(maxsize=1)
def _configured_google_client(api_key: str | None) -> genai.Client:
    return genai.Client(api_key=api_key) if api_key else genai.Client()


def get_google_client() -> genai.Client:
    return _google_client.get() or _configured_google_client(get_configured_google_api_key())


@contextmanager
def use_google_api_key(api_key: str | None) -> Generator[None, None, None]:
    key_token: Token[str | None] = _google_api_key.set(api_key)
    client = None
    client_token: Token[genai.Client | None] | None = None
    try:
        if api_key:
            client = genai.Client(api_key=api_key)
        client_token = _google_client.set(client)
        yield
    finally:
        if client_token is not None:
            _google_client.reset(client_token)
        _google_api_key.reset(key_token)
        if client:
            client.close()
