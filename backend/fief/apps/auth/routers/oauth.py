from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import RedirectResponse
from httpx_oauth.oauth2 import GetAccessTokenError

from fief.dependencies.auth import get_login_session
from fief.dependencies.authentication_flow import get_authentication_flow
from fief.dependencies.oauth import get_oauth_provider
from fief.dependencies.oauth_provider import get_oauth_providers
from fief.dependencies.register import get_registration_flow
from fief.dependencies.session_token import get_session_token
from fief.dependencies.tenant import get_current_tenant
from fief.dependencies.workspace_repositories import (
    get_oauth_account_repository,
    get_oauth_session_repository,
)
from fief.exceptions import OAuthException
from fief.locale import gettext_lazy as _
from fief.models import (
    LoginSession,
    OAuthAccount,
    OAuthProvider,
    OAuthSession,
    RegistrationSessionFlow,
    SessionToken,
    Tenant,
)
from fief.repositories import OAuthAccountRepository, OAuthSessionRepository
from fief.schemas.oauth import OAuthError
from fief.services.authentication_flow import AuthenticationFlow
from fief.services.oauth_provider import get_oauth_id_email, get_oauth_provider_service
from fief.services.registration_flow import RegistrationFlow

router = APIRouter(prefix="/oauth")


@router.get("/authorize", name="oauth:authorize")
async def authorize(
    request: Request,
    login_session: LoginSession = Depends(get_login_session),
    oauth_provider: OAuthProvider = Depends(get_oauth_provider),
    oauth_session_repository: OAuthSessionRepository = Depends(
        get_oauth_session_repository
    ),
):
    redirect_uri = request.url_for("oauth:callback")

    oauth_session = OAuthSession(
        redirect_uri=redirect_uri,
        oauth_provider=oauth_provider,
        login_session=login_session,
    )
    oauth_session = await oauth_session_repository.create(oauth_session)
    state = oauth_session.token

    oauth_provider_service = get_oauth_provider_service(oauth_provider)
    authorize_url = await oauth_provider_service.get_authorization_url(
        redirect_uri, state=state, scope=oauth_provider.scopes
    )

    return RedirectResponse(authorize_url, status_code=status.HTTP_302_FOUND)


@router.get("/callback", name="oauth:callback")
async def callback(
    request: Request,
    code: Optional[str] = Query(None),
    code_verifier: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    login_session: LoginSession = Depends(get_login_session),
    oauth_providers: Optional[List[OAuthProvider]] = Depends(get_oauth_providers),
    oauth_session_repository: OAuthSessionRepository = Depends(
        get_oauth_session_repository
    ),
    oauth_account_repository: OAuthAccountRepository = Depends(
        get_oauth_account_repository
    ),
    authentication_flow: AuthenticationFlow = Depends(get_authentication_flow),
    registration_flow: RegistrationFlow = Depends(get_registration_flow),
    session_token: Optional[SessionToken] = Depends(get_session_token),
    tenant: Tenant = Depends(get_current_tenant),
):
    if error is not None:
        raise OAuthException(
            OAuthError.get_oauth_error(error),
            oauth_providers=oauth_providers,
            tenant=tenant,
        )

    if code is None:
        raise OAuthException(
            OAuthError.get_missing_code(_("Missing authorization code.")),
            oauth_providers=oauth_providers,
            tenant=tenant,
        )

    oauth_session = (
        await oauth_session_repository.get_by_token(state)
        if state is not None
        else None
    )
    if oauth_session is None or login_session.id != oauth_session.login_session_id:
        raise OAuthException(
            OAuthError.get_invalid_session(_("Invalid OAuth session.")),
            oauth_providers=oauth_providers,
            tenant=tenant,
        )

    oauth_provider = oauth_session.oauth_provider
    oauth_provider_service = get_oauth_provider_service(oauth_provider)

    try:
        access_token_dict = await oauth_provider_service.get_access_token(
            code, oauth_session.redirect_uri, code_verifier
        )
    except GetAccessTokenError as e:
        raise OAuthException(
            OAuthError.get_access_token_error(
                _("An error occurred while getting the access token.")
            ),
            oauth_providers=oauth_providers,
            tenant=tenant,
        ) from e

    access_token = access_token_dict["access_token"]
    refresh_token = access_token_dict.get("refresh_token")
    try:
        expires_at = datetime.fromtimestamp(
            access_token_dict["expires_at"], tz=timezone.utc
        )
    except KeyError:
        expires_at = None

    account_id, account_email = await get_oauth_id_email(oauth_provider, access_token)
    oauth_account = await oauth_account_repository.get_by_provider_and_account_id(
        oauth_provider.id, account_id
    )

    # Existing account
    if oauth_account is not None and oauth_account.user is not None:
        user = oauth_account.user
        if not user.is_active:
            raise OAuthException(
                OAuthError.get_inactive_user(_("Your account is inactive.")),
                oauth_providers=oauth_providers,
                tenant=tenant,
            )

        # Update tokens
        oauth_account.access_token = access_token  # type: ignore
        oauth_account.refresh_token = refresh_token  # type: ignore
        oauth_account.expires_at = expires_at
        await oauth_account_repository.update(oauth_account)

        # Redirect to consent
        response = RedirectResponse(
            tenant.url_path_for(request, "auth:consent"),
            status_code=status.HTTP_302_FOUND,
        )
        response = await authentication_flow.rotate_session_token(
            response, user.id, session_token=session_token
        )
        return response

    # New account to create
    oauth_account = OAuthAccount(
        access_token=access_token,
        expires_at=expires_at,
        refresh_token=refresh_token,
        account_id=account_id,
        account_email=account_email,
        oauth_provider=oauth_provider,
        tenant_id=tenant.id,
    )
    oauth_account = await oauth_account_repository.create(oauth_account)
    oauth_session.oauth_account = oauth_account
    await oauth_session_repository.update(oauth_session)

    response = RedirectResponse(
        tenant.url_path_for(request, "register:register"),
        status_code=status.HTTP_302_FOUND,
    )

    await registration_flow.create_registration_session(
        response,
        RegistrationSessionFlow.OAUTH,
        tenant=tenant,
        oauth_account=oauth_account,
    )

    return response
