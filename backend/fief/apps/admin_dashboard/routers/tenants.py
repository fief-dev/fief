from fastapi import APIRouter, Depends, Header

from fief.apps.admin_dashboard.dependencies import BaseContext, get_base_context
from fief.dependencies.admin_session import get_admin_session_token
from fief.dependencies.pagination import (
    PaginatedObjects,
    Pagination,
    RawOrdering,
    get_pagination,
    get_raw_ordering,
)
from fief.dependencies.tenant import get_paginated_tenants
from fief.models import Tenant
from fief.templates import templates

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
