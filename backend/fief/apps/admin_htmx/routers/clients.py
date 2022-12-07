from fastapi import APIRouter, Depends

from fief.dependencies.admin_session import get_admin_session_token
from fief.dependencies.client import get_paginated_clients
from fief.dependencies.pagination import PaginatedObjects
from fief.models import Client
from fief.apps.admin_htmx.templates import templates
from fief.dependencies.pagination import Pagination, get_pagination
from fief.apps.admin_htmx.dependencies import get_base_context, BaseContext

router = APIRouter(dependencies=[Depends(get_admin_session_token)])


@router.get("/", name="clients:list")
async def list_clients(
    pagination: Pagination = Depends(get_pagination),
    paginated_clients: PaginatedObjects[Client] = Depends(get_paginated_clients),
    context: BaseContext = Depends(get_base_context),
):
    clients, count = paginated_clients
    limit, skip = pagination
    return templates.TemplateResponse(
        "clients/index.html",
        {
            **context,
            "clients": clients,
            "count": count,
            "limit": limit,
            "skip": skip,
        },
    )
