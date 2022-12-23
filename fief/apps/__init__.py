from fief.apps.admin.app import app as admin_app
from fief.apps.admin_dashboard.app import app as admin_dashboard_app
from fief.apps.auth.app import app as auth_app

__all__ = ["admin_app", "auth_app", "admin_dashboard_app"]
