from fastapi import Depends

from fief.dependencies.tenant import get_current_tenant
from fief.dependencies.workspace_repositories import get_workspace_repository
from fief.models import Tenant, Theme
from fief.repositories import ThemeRepository


async def get_current_theme(
    tenant: Tenant = Depends(get_current_tenant),
    repository: ThemeRepository = Depends(get_workspace_repository(ThemeRepository)),
) -> Theme:
    if tenant.theme_id is not None:
        theme = await repository.get_by_id(tenant.theme_id)
    else:
        theme = await repository.get_default()

    if theme is None:
        return Theme.build_default()

    return theme
