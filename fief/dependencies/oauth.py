from fastapi import Body, Cookie, Depends, HTTPException, Query, Request, status
from pydantic import UUID4

from fief.dependencies.oauth_provider import get_oauth_providers
from fief.dependencies.repositories import get_repository
from fief.exceptions import OAuthException
from fief.locale import gettext_lazy as _
from fief.models import LoginSession, OAuthProvider, OAuthSession, Tenant
from fief.repositories import (
    LoginSessionRepository,
    OAuthSessionRepository,
    TenantRepository,
)
from fief.schemas.oauth import OAuthError
from fief.schemas.oauth_callback import CallBackBody
from fief.settings import settings


async def get_tenant_by_query(
    tenant_id: UUID4 = Query(..., alias="tenant"),
    tenant_repository: TenantRepository = Depends(TenantRepository),
) -> Tenant:
    tenant = await tenant_repository.get_by_id(tenant_id)

    if tenant is None:
        raise OAuthException(
            OAuthError.get_invalid_tenant(_("Unknown tenant")), fatal=True
        )

    return tenant


async def get_optional_login_session_with_tenant_query(
    request: Request,
    token: str | None = Cookie(None, alias=settings.login_session_cookie_name),
    login_session_repository: LoginSessionRepository = Depends(
        get_repository(LoginSessionRepository)
    ),
    tenant: Tenant = Depends(get_tenant_by_query),
    oauth_providers: list[OAuthProvider] | None = Depends(get_oauth_providers),
) -> LoginSession | None:
    if token is None:
        return None

    login_session = await login_session_repository.get_by_token(token, fresh=False)
    if login_session is None or login_session.client.tenant_id != tenant.id:
        raise OAuthException(
            OAuthError.get_invalid_session(_("Invalid login session.")),
            oauth_providers=oauth_providers,
            tenant=tenant,
        )

    if login_session.is_expired:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={
                "Location": str(login_session.regenerate_authorization_url(request))
            },
        )

    return login_session


async def get_oauth_provider(
    provider: UUID4 = Query(...),
    tenant: Tenant = Depends(get_tenant_by_query),
    oauth_providers: list[OAuthProvider] | None = Depends(get_oauth_providers),
) -> OAuthProvider:
    oauth_provider = tenant.get_oauth_provider(provider)
    if oauth_provider is None:
        raise OAuthException(
            OAuthError.get_invalid_provider(_("Unknown OAuth provider")),
            oauth_providers=oauth_providers,
            tenant=tenant,
        )

    return oauth_provider


async def get_oauth_session(
    code: str | None = Query(None),
    callback_body: str | None = Body(None),
    state: str | None = Query(None),
    error: str | None = Query(None),
    oauth_session_repository: OAuthSessionRepository = Depends(
        get_repository(OAuthSessionRepository)
    ),
) -> OAuthSession:
    if callback_body:
        callback_object = CallBackBody.get_callback_body(callback_body)
        code = callback_object.code
        state = callback_object.state

    if error is not None:
        raise OAuthException(
            OAuthError.get_oauth_error(error),
            fatal=True,
        )

    if code is None:
        raise OAuthException(
            OAuthError.get_missing_code(_("Missing authorization code.")),
            fatal=True,
        )

    oauth_session = (
        await oauth_session_repository.get_by_token(state)
        if state is not None
        else None
    )
    if oauth_session is None:
        raise OAuthException(
            OAuthError.get_invalid_session(_("Invalid OAuth session.")),
            fatal=True,
        )

    return oauth_session


async def get_optional_login_session(
    token: str | None = Cookie(None, alias=settings.login_session_cookie_name),
    login_session_repository: LoginSessionRepository = Depends(
        get_repository(LoginSessionRepository)
    ),
    oauth_session: OAuthSession = Depends(get_oauth_session),
) -> LoginSession | None:
    if token is None:
        return None

    login_session = await login_session_repository.get_by_token(token)
    if (
        login_session is None
        or login_session.client.tenant_id != oauth_session.tenant_id
    ):
        raise OAuthException(
            OAuthError.get_invalid_session(_("Invalid login session.")), fatal=True
        )

    return login_session
