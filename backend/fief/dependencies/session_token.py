from typing import Optional

from fastapi import Cookie, Depends

from fief.crypto.token import get_token_hash
from fief.dependencies.workspace_repositories import get_session_token_repository
from fief.models import SessionToken
from fief.repositories import SessionTokenRepository
from fief.settings import settings


async def get_session_token(
    token: Optional[str] = Cookie(None, alias=settings.session_cookie_name),
    repository: SessionTokenRepository = Depends(get_session_token_repository),
) -> Optional[SessionToken]:
    if token is not None:
        token_hash = get_token_hash(token)
        return await repository.get_by_token(token_hash)
    return None
