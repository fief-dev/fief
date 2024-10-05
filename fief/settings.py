import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fief.settings_class import Settings


def _get_settings() -> "Settings":
    try:
        stronghold_settings_module = importlib.import_module(
            "fief_stronghold.settings_class"
        )
        SettingsClass = getattr(stronghold_settings_module, "Settings")
    except (ImportError, AttributeError):
        base_settings_module = importlib.import_module("fief.settings_class")
        SettingsClass = getattr(base_settings_module, "Settings")
    return SettingsClass()  # pyright: ignore


settings = _get_settings()
