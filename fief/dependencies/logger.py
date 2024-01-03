from fastapi import Depends

from fief.dependencies.admin_api_key import get_optional_admin_api_key
from fief.dependencies.admin_session import get_optional_admin_session_token
from fief.logger import AuditLogger, logger
from fief.models import AdminAPIKey, AdminSessionToken


async def get_audit_logger(
    admin_session_token: AdminSessionToken | None = Depends(
        get_optional_admin_session_token
    ),
    admin_api_key: AdminAPIKey | None = Depends(get_optional_admin_api_key),
) -> AuditLogger:
    return AuditLogger(
        logger,
        admin_user_id=admin_session_token.user_id if admin_session_token else None,
        admin_api_key_id=admin_api_key.id if admin_api_key else None,
    )
