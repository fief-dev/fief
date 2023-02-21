from typing import Any

from fastapi import APIRouter, Depends, Header, Request, status
from fastapi.responses import RedirectResponse
from pydantic import ValidationError

from fief.apps.dashboard.forms.workspace import (
    WorkspaceCreateStep1Form,
    WorkspaceCreateStep2Form,
    WorkspaceCreateStep3Form,
    WorkspaceCreateStep4Form,
)
from fief.db.types import UNSAFE_SSL_MODES, create_database_connection_parameters
from fief.dependencies.admin_session import get_admin_session_token
from fief.dependencies.workspace_creation import get_workspace_creation
from fief.dependencies.workspace_db import get_workspace_db
from fief.forms import FormHelper
from fief.models import AdminSessionToken
from fief.schemas.workspace import WorkspaceCreate
from fief.services.workspace_creation import WorkspaceCreation
from fief.services.workspace_db import (
    WorkspaceDatabase,
    WorkspaceDatabaseConnectionError,
)

CREATE_WORKSPACE_DATA_SESSION_KEY = "create_workspace"
CREATE_WORKSPACE_NB_STEPS = 4

router = APIRouter(dependencies=[Depends(get_admin_session_token)])


async def get_base_context(request: Request, hx_request: bool = Header(False)):
    layout = "admin/workspaces/create/layout.html"
    if hx_request:
        layout = "admin/workspaces/create/layout_boost.html"
    return {"request": request, "layout": layout, "steps": CREATE_WORKSPACE_NB_STEPS}


async def get_create_workspace_session_data(request: Request) -> dict[str, Any]:
    return request.session.get(CREATE_WORKSPACE_DATA_SESSION_KEY, {})


@router.get("/create", name="dashboard.workspaces:create")
async def create_workspace(request: Request):
    return RedirectResponse(request.url_for("dashboard.workspaces:create.step1"))


@router.api_route(
    "/create/step1", methods=["GET", "POST"], name="dashboard.workspaces:create.step1"
)
async def create_workspace_step1(
    request: Request,
    session_data: dict[str, Any] = Depends(get_create_workspace_session_data),
    context=Depends(get_base_context),
):
    form_helper = FormHelper(
        WorkspaceCreateStep1Form,
        "admin/workspaces/create/step1.html",
        data=session_data,
        request=request,
        context={**context, "active": 0},
    )

    if await form_helper.is_submitted_and_valid():
        form = await form_helper.get_form()
        data = form.data
        data.pop("csrf_token")

        request.session[CREATE_WORKSPACE_DATA_SESSION_KEY] = {
            **session_data,
            **data,
        }

        return RedirectResponse(
            request.url_for("dashboard.workspaces:create.step2"),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return await form_helper.get_response()


@router.api_route(
    "/create/step2", methods=["GET", "POST"], name="dashboard.workspaces:create.step2"
)
async def create_workspace_step2(
    request: Request,
    context=Depends(get_base_context),
):
    form_helper = FormHelper(
        WorkspaceCreateStep2Form,
        "admin/workspaces/create/step2.html",
        request=request,
        context={**context, "active": 1},
    )

    if await form_helper.is_submitted_and_valid():
        form = await form_helper.get_form()
        data = form.data

        redirect_url = request.url_for("dashboard.workspaces:create.step3")
        if data["database"] == "cloud":
            redirect_url = request.url_for("dashboard.workspaces:create.step4")

        return RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)

    return await form_helper.get_response()


@router.api_route(
    "/create/step3", methods=["GET", "POST"], name="dashboard.workspaces:create.step3"
)
async def create_workspace_step3(
    request: Request,
    hx_trigger: str | None = Header(None),
    session_data: dict[str, Any] = Depends(get_create_workspace_session_data),
    context=Depends(get_base_context),
):
    form_helper = FormHelper(
        WorkspaceCreateStep3Form,
        "admin/workspaces/create/step3.html",
        request=request,
        data=session_data,
        context={**context, "active": 2, "UNSAFE_SSL_MODES": UNSAFE_SSL_MODES},
    )
    form = await form_helper.get_form()
    form.prefill_from_database_type()

    if hx_trigger is None and await form_helper.is_submitted_and_valid():
        data = form.data
        data.pop("csrf_token")

        request.session[CREATE_WORKSPACE_DATA_SESSION_KEY] = {
            **session_data,
            **data,
        }

        return RedirectResponse(
            request.url_for("dashboard.workspaces:create.step4"),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return await form_helper.get_response()


@router.post(
    "/create/step3/check-connection",
    name="dashboard.workspaces:create.step3.check_connection",
)
async def create_workspace_step3_check_connection(
    request: Request,
    context=Depends(get_base_context),
    workspace_db: WorkspaceDatabase = Depends(get_workspace_db),
):
    form_helper = FormHelper(
        WorkspaceCreateStep3Form,
        "admin/workspaces/create/step3.html",
        request=request,
        context={**context, "active": 2, "UNSAFE_SSL_MODES": UNSAFE_SSL_MODES},
    )
    form = await form_helper.get_form()
    form.prefill_from_database_type()

    if await form_helper.is_submitted_and_valid():
        data = form.data

        database_connection_parameters = create_database_connection_parameters(
            data["database_type"],
            asyncio=False,
            username=data["database_username"],
            password=data["database_password"],
            host=data["database_host"],
            port=data["database_port"],
            database=data["database_name"],
            ssl_mode=data["database_ssl_mode"],
        )
        valid, message = workspace_db.check_connection(database_connection_parameters)
        if not valid:
            return await form_helper.get_error_response(
                message or "Unknown error", "database_connection_error"
            )
        else:
            form_helper.context.update({"database_connection_success": True})

    return await form_helper.get_response()


@router.api_route(
    "/create/step4", methods=["GET", "POST"], name="dashboard.workspaces:create.step4"
)
async def create_workspace_step4(
    request: Request,
    session_data: dict[str, Any] = Depends(get_create_workspace_session_data),
    workspace_creation: WorkspaceCreation = Depends(get_workspace_creation),
    admin_session_token: AdminSessionToken = Depends(get_admin_session_token),
    context=Depends(get_base_context),
):
    form_helper = FormHelper(
        WorkspaceCreateStep4Form,
        "admin/workspaces/create/step4.html",
        request=request,
        context={**context, "active": 3},
    )

    if await form_helper.is_submitted_and_valid():
        try:
            workspace_create = WorkspaceCreate(**session_data)
            workspace = await workspace_creation.create(
                workspace_create, user_id=admin_session_token.user_id
            )
        except ValidationError:
            request.session[CREATE_WORKSPACE_DATA_SESSION_KEY] = {}
            return RedirectResponse(
                request.url_for("dashboard.workspaces:create"),
                status_code=status.HTTP_303_SEE_OTHER,
            )
        except WorkspaceDatabaseConnectionError as e:
            return await form_helper.get_error_response(
                e.message, "database_connection_error"
            )

        request.session[CREATE_WORKSPACE_DATA_SESSION_KEY] = {}
        return RedirectResponse(
            f"{request.url.scheme}://{workspace.domain}/admin/",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return await form_helper.get_response()
