import urllib.parse
from typing import Any, Literal, TypedDict

from fastapi import Depends, Header, Query, Request
from fief_client import FiefUserInfo

from fief.dependencies.admin_session import get_userinfo
from fief.dependencies.current_workspace import get_current_workspace
from fief.dependencies.pagination import (
    Ordering,
    OrderingGetter,
    Pagination,
    get_pagination,
)
from fief.dependencies.workspace import get_admin_user_workspaces
from fief.models import Workspace


async def get_layout(hx_request: bool = Header(False)) -> str:
    if hx_request:
        return "admin/layout_boost.html"
    return "admin/layout.html"


class BaseContext(TypedDict):
    request: Request
    layout: str
    hx_target: str | None
    user: FiefUserInfo
    current_workspace: Workspace
    workspaces: list[Workspace]


async def get_base_context(
    request: Request,
    hx_target: str | None = Header(None),
    layout: str = Depends(get_layout),
    userinfo: FiefUserInfo = Depends(get_userinfo),
    current_workspace: Workspace = Depends(get_current_workspace),
    workspaces: list[Workspace] = Depends(get_admin_user_workspaces),
) -> BaseContext:
    return {
        "request": request,
        "layout": layout,
        "hx_target": hx_target,
        "user": userinfo,
        "current_workspace": current_workspace,
        "workspaces": workspaces,
    }


class DatatableColumn:
    def __init__(
        self,
        title: str,
        slug: str,
        renderer_macro: str,
        *,
        ordering: str | None = None,
        renderer_macro_kwargs: dict[str, Any] | None = None,
    ) -> None:
        self.title = title
        self.slug = slug
        self.ordering = ordering
        self.renderer_macro = renderer_macro
        self.renderer_macro_kwargs = (
            renderer_macro_kwargs if renderer_macro_kwargs is not None else {}
        )


class DatatableQueryParameters:
    def __init__(
        self,
        pagination: Pagination,
        ordering: Ordering,
        columns: list[str],
        params: dict[str, Any],
    ) -> None:
        limit, skip = pagination
        self.limit = limit
        self.skip = skip
        self.ordering = ordering
        self.columns = columns
        self.params = params

    def is_ordered(self, field: str, way: Literal["asc", "desc"] = "asc") -> bool:
        field_accessor = field.split(".")
        for ordered_field, is_desc in self.ordering:
            if ordered_field == field_accessor:
                return (way == "asc" and is_desc is False) or (
                    way == "desc" and is_desc is True
                )
        return False

    def set_pagination(self, *, limit: int, skip: int) -> "DatatableQueryParameters":
        return DatatableQueryParameters(
            (limit, skip), self.ordering, self.columns, self.params
        )

    def toggle_field_ordering(self, field: str) -> "DatatableQueryParameters":
        field_accessor = field.split(".")
        if self.is_ordered(field, "asc"):
            updated_ordering = [(field_accessor, True)]
        elif self.is_ordered(field, "desc"):
            updated_ordering = []
        else:
            updated_ordering = [(field_accessor, False)]
        return DatatableQueryParameters(
            (self.limit, self.skip), updated_ordering, self.columns, self.params
        )

    def toggle_column(self, column: str) -> "DatatableQueryParameters":
        columns = self.columns
        if column in columns:
            columns = [c for c in columns if c != column]
        else:
            columns = columns + [column]
        return DatatableQueryParameters(
            (self.limit, self.skip), self.ordering, columns, self.params
        )

    def set_param(self, name: str, value: str | None) -> "DatatableQueryParameters":
        params = {**self.params}
        if value is None:
            params.pop(name, None)
        else:
            params[name] = value
        return DatatableQueryParameters(
            (self.limit, self.skip), self.ordering, self.columns, params
        )

    def __str__(self) -> str:
        ordering_params = [
            f"-{'.'.join(field)}" if is_desc else ".".join(field)
            for (field, is_desc) in self.ordering
        ]
        params = {
            "limit": self.limit,
            "skip": self.skip,
            "ordering": ",".join(ordering_params),
            **self.params,
        }
        if self.columns:
            params["columns"] = ",".join(self.columns)
        return urllib.parse.urlencode(params)


class DatatableQueryParametersGetter:
    def __init__(
        self, default_columns: list[str], params: list[str] | None = None
    ) -> None:
        self.default_columns = default_columns
        self.params = params or []

    def __call__(
        self,
        request: Request,
        pagination: Pagination = Depends(get_pagination),
        ordering: Ordering = Depends(OrderingGetter()),
        columns: str | None = Query(None),
    ) -> DatatableQueryParameters:
        columns_list = self.default_columns
        if columns is not None:
            columns_list = columns.lower().split(",")

        params = {}
        for param in self.params:
            try:
                params[param] = request.query_params[param]
            except KeyError:
                pass

        return DatatableQueryParameters(pagination, ordering, columns_list, params)
