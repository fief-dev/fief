from pathlib import Path

ROOT_DIR = Path(__file__).parent

ALEMBIC_CONFIG_FILE = str(ROOT_DIR / "alembic.ini")
STATIC_DIRECTORY = ROOT_DIR / "static"
LOCALE_DIRECTORY = ROOT_DIR / "locale"
TEMPLATES_DIRECTORY = ROOT_DIR / "templates"
EMAIL_TEMPLATES_DIRECTORY = ROOT_DIR / "emails"
