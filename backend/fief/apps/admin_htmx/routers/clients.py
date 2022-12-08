from fastapi import APIRouter, Depends, Header

from fief.dependencies.admin_session import get_admin_session_token
from fief.dependencies.client import get_paginated_clients, get_client_by_id_or_404
from fief.dependencies.pagination import PaginatedObjects
from fief.dependencies.pagination import RawOrdering, get_raw_ordering
from fief.models import Client
from fief.apps.admin_htmx.templates import templates
from fief.dependencies.pagination import Pagination, get_pagination
from fief.apps.admin_htmx.dependencies import get_base_context, BaseContext

router = APIRouter(dependencies=[Depends(get_admin_session_token)])


async def get_list_context(
    pagination: Pagination = Depends(get_pagination),
    raw_ordering: RawOrdering = Depends(get_raw_ordering),
    paginated_clients: PaginatedObjects[Client] = Depends(get_paginated_clients),
):
    clients, count = paginated_clients
    limit, skip = pagination
    return {
        "clients": clients,
        "count": count,
        "limit": limit,
        "skip": skip,
        "ordering": raw_ordering,
    }


@router.get("/", name="clients:list")
async def list_clients(
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
):
    return templates.TemplateResponse("clients/list.html", {**context, **list_context})


@router.get("/{id:uuid}", name="clients:get")
async def get_client(
    client: Client = Depends(get_client_by_id_or_404),
    list_context=Depends(get_list_context),
    context: BaseContext = Depends(get_base_context),
):
    return templates.TemplateResponse(
        "clients/get.html", {**context, **list_context, "client": client, "aside": True}
    )
