from fastapi import APIRouter, Depends, Response, status
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from fief import schemas
from fief.dependencies.admin_authentication import is_authenticated_admin
from fief.dependencies.oauth_provider import (
    get_oauth_provider_by_id_or_404,
    get_paginated_oauth_providers,
)
from fief.dependencies.pagination import PaginatedObjects
from fief.dependencies.workspace_repositories import get_oauth_provider_repository
from fief.models import OAuthProvider
from fief.repositories import OAuthProviderRepository
from fief.schemas.generics import PaginatedResults

router = APIRouter(dependencies=[Depends(is_authenticated_admin)])


@router.get(
    "/",
    name="oauth_providers:list",
    response_model=PaginatedResults[schemas.oauth_provider.OAuthProvider],
)
async def list_oauth_providers(
    paginated_oauth_providers: PaginatedObjects[OAuthProvider] = Depends(
        get_paginated_oauth_providers
    ),
) -> PaginatedResults[schemas.oauth_provider.OAuthProvider]:
    oauth_providers, count = paginated_oauth_providers
    return PaginatedResults(
        count=count,
        results=[
            schemas.oauth_provider.OAuthProvider.from_orm(oauth_provider)
            for oauth_provider in oauth_providers
        ],
    )


@router.post(
    "/",
    name="oauth_providers:create",
    response_model=schemas.oauth_provider.OAuthProvider,
    status_code=status.HTTP_201_CREATED,
)
async def create_oauth_provider(
    oauth_provider_create: schemas.oauth_provider.OAuthProviderCreate,
    repository: OAuthProviderRepository = Depends(get_oauth_provider_repository),
) -> schemas.oauth_provider.OAuthProvider:
    oauth_provider = OAuthProvider(**oauth_provider_create.dict())
    oauth_provider = await repository.create(oauth_provider)

    return schemas.oauth_provider.OAuthProvider.from_orm(oauth_provider)


@router.patch(
    "/{id:uuid}",
    name="oauth_providers:update",
    response_model=schemas.oauth_provider.OAuthProvider,
)
async def update_oauth_provider(
    oauth_provider_update: schemas.oauth_provider.OAuthProviderUpdate,
    oauth_provider: OAuthProvider = Depends(get_oauth_provider_by_id_or_404),
    repository: OAuthProviderRepository = Depends(get_oauth_provider_repository),
) -> schemas.oauth_provider.OAuthProvider:
    oauth_provider_update_dict = oauth_provider_update.dict(exclude_unset=True)

    try:
        oauth_provider_update_provider = (
            schemas.oauth_provider.OAuthProviderUpdateProvider.from_orm(oauth_provider)
        )
        schemas.oauth_provider.OAuthProviderUpdateProvider(
            **oauth_provider_update_provider.copy(
                update=oauth_provider_update_dict
            ).dict()
        )
    except ValidationError as e:
        raise RequestValidationError(e.raw_errors) from e

    for field, value in oauth_provider_update_dict.items():
        setattr(oauth_provider, field, value)

    await repository.update(oauth_provider)

    return schemas.oauth_provider.OAuthProvider.from_orm(oauth_provider)


@router.delete(
    "/{id:uuid}",
    name="oauth_providers:delete",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_permission(
    oauth_provider: OAuthProvider = Depends(get_oauth_provider_by_id_or_404),
    repository: OAuthProviderRepository = Depends(get_oauth_provider_repository),
):
    await repository.delete(oauth_provider)
