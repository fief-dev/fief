from fastapi import APIRouter, Depends, Request, status, Header
from fastapi.responses import RedirectResponse

from fief.repositories import ClientRepository, TenantRepository
from fief.dependencies.logger import get_audit_logger
from fief.logger import AuditLogger
from fief.dependencies.workspace_repositories import get_workspace_repository
from fief.dependencies.admin_session import get_admin_session_token
from fief.dependencies.client import get_paginated_clients, get_client_by_id_or_404
from fief.dependencies.tenant import get_paginated_tenants
from fief.dependencies.pagination import PaginatedObjects
from fief.dependencies.pagination import RawOrdering, get_raw_ordering
from fief.models import Client, AuditLogMessage, ClientType, Tenant
from fief.templates import templates
from fief.dependencies.pagination import Pagination, get_pagination
from fief.apps.admin_htmx.dependencies import get_base_context, BaseContext
from fief.forms import FormHelper
from fief.apps.admin_htmx.forms.client import ClientCreateForm

router = APIRouter(dependencies=[Depends(get_admin_session_token)])


async def get_list_context(
    pagination: Pagination = Depends(get_pagination),
    raw_ordering: RawOrdering = Depends(get_raw_ordering),
    paginated_tenants: PaginatedObjects[Tenant] = Depends(get_paginated_tenants),
):
    tenants, count = paginated_tenants
    limit, skip = pagination
    return {
        "tenants": tenants,
        "count": count,
        "limit": limit,
        "skip": skip,
        "ordering": raw_ordering,
    }


async def get_list_template(hx_combobox: bool = Header(False)) -> str:
    if hx_combobox:
        return "admin/tenants/list_combobox.html"
    return "admin/tenants/list.html"


@router.get("/", name="dashboard:tenants:list")
async def list_tenants(
    template: str = Depends(get_list_template),
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
):
    return templates.TemplateResponse(template, {**context, **list_context})
