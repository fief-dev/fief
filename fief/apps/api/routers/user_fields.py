from fastapi import APIRouter, Depends, HTTPException, Response, status

from fief import schemas
from fief.dependencies.admin_authentication import is_authenticated_admin_api
from fief.dependencies.logger import get_audit_logger
from fief.dependencies.pagination import PaginatedObjects
from fief.dependencies.user_field import (
    get_paginated_user_fields,
    get_user_field_by_id_or_404,
    get_validated_user_field_create,
    get_validated_user_field_update,
)
from fief.dependencies.webhooks import TriggerWebhooks, get_trigger_webhooks
from fief.dependencies.workspace_repositories import get_workspace_repository
from fief.errors import APIErrorCode
from fief.logger import AuditLogger
from fief.models import AuditLogMessage, UserField
from fief.repositories import UserFieldRepository
from fief.schemas.generics import PaginatedResults
from fief.services.webhooks.models import (
    UserFieldCreated,
    UserFieldDeleted,
    UserFieldUpdated,
)

router = APIRouter(dependencies=[Depends(is_authenticated_admin_api)])


@router.get(
    "/",
    name="user_fields:list",
    response_model=PaginatedResults[schemas.user_field.UserField],
)
async def list_user_fields(
    paginated_user_fields: PaginatedObjects[UserField] = Depends(
        get_paginated_user_fields
    ),
) -> PaginatedResults[schemas.user_field.UserField]:
    user_fields, count = paginated_user_fields
    return PaginatedResults(
        count=count,
        results=[
            schemas.user_field.UserField.model_validate(user_field)
            for user_field in user_fields
        ],
    )


@router.get(
    "/{id:uuid}", name="user_fields:get", response_model=schemas.user_field.UserField
)
async def get_user_field(
    user_field: UserField = Depends(get_user_field_by_id_or_404),
) -> UserField:
    return user_field


@router.post(
    "/",
    name="user_fields:create",
    response_model=schemas.user_field.UserField,
    status_code=status.HTTP_201_CREATED,
)
async def create_user_field(
    user_field_create: schemas.user_field.UserFieldCreate = Depends(
        get_validated_user_field_create
    ),
    repository: UserFieldRepository = Depends(
        get_workspace_repository(UserFieldRepository)
    ),
    audit_logger: AuditLogger = Depends(get_audit_logger),
    trigger_webhooks: TriggerWebhooks = Depends(get_trigger_webhooks),
) -> schemas.user_field.UserField:
    existing_user_field = await repository.get_by_slug(user_field_create.slug)
    if existing_user_field is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=APIErrorCode.USER_FIELD_SLUG_ALREADY_EXISTS,
        )

    user_field = UserField(**user_field_create.model_dump())
    user_field = await repository.create(user_field)
    audit_logger.log_object_write(AuditLogMessage.OBJECT_CREATED, user_field)
    trigger_webhooks(UserFieldCreated, user_field, schemas.user_field.UserField)

    return schemas.user_field.UserField.model_validate(user_field)


@router.patch(
    "/{id:uuid}", name="user_fields:update", response_model=schemas.user_field.UserField
)
async def update_user_field(
    user_field_update: schemas.user_field.UserFieldUpdate = Depends(
        get_validated_user_field_update
    ),
    user_field: UserField = Depends(get_user_field_by_id_or_404),
    repository: UserFieldRepository = Depends(
        get_workspace_repository(UserFieldRepository)
    ),
    audit_logger: AuditLogger = Depends(get_audit_logger),
    trigger_webhooks: TriggerWebhooks = Depends(get_trigger_webhooks),
) -> schemas.user_field.UserField:
    updated_slug = user_field_update.slug
    if updated_slug is not None and updated_slug != user_field.slug:
        existing_user_field = await repository.get_by_slug(updated_slug)
        if existing_user_field is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=APIErrorCode.USER_FIELD_SLUG_ALREADY_EXISTS,
            )

    user_field_update_dict = user_field_update.model_dump(exclude_unset=True)
    for field, value in user_field_update_dict.items():
        setattr(user_field, field, value)

    await repository.update(user_field)
    audit_logger.log_object_write(AuditLogMessage.OBJECT_UPDATED, user_field)
    trigger_webhooks(UserFieldUpdated, user_field, schemas.user_field.UserField)

    return schemas.user_field.UserField.model_validate(user_field)


@router.delete(
    "/{id:uuid}",
    name="user_fields:delete",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_user_field(
    user_field: UserField = Depends(get_user_field_by_id_or_404),
    repository: UserFieldRepository = Depends(
        get_workspace_repository(UserFieldRepository)
    ),
    audit_logger: AuditLogger = Depends(get_audit_logger),
    trigger_webhooks: TriggerWebhooks = Depends(get_trigger_webhooks),
):
    await repository.delete(user_field)
    audit_logger.log_object_write(AuditLogMessage.OBJECT_DELETED, user_field)
    trigger_webhooks(UserFieldDeleted, user_field, schemas.user_field.UserField)
