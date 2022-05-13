from typing import Any, List, Optional, Tuple, Type

from fastapi import Depends, HTTPException, status
from pydantic import UUID4, create_model, validator
from sqlalchemy import select

from fief.dependencies.pagination import (
    Ordering,
    Pagination,
    get_ordering,
    get_paginated_objects,
    get_pagination,
)
from fief.dependencies.workspace_managers import get_user_field_manager
from fief.managers import UserFieldManager
from fief.models import UserField
from fief.models.user_field import UserFieldType
from fief.schemas.generics import true_bool_validator
from fief.schemas.user import UF, UserCreate, UserCreateInternal, UserFields
from fief.schemas.user_field import USER_FIELD_TYPE_MAP


async def get_paginated_user_fields(
    pagination: Pagination = Depends(get_pagination),
    ordering: Ordering = Depends(get_ordering),
    manager: UserFieldManager = Depends(get_user_field_manager),
) -> Tuple[List[UserField], int]:
    statement = select(UserField)
    return await get_paginated_objects(statement, pagination, ordering, manager)


async def get_user_field_by_id_or_404(
    id: UUID4,
    manager: UserFieldManager = Depends(get_user_field_manager),
) -> UserField:
    user_field = await manager.get_by_id(id)

    if user_field is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return user_field


async def get_registration_user_fields(
    manager: UserFieldManager = Depends(get_user_field_manager),
) -> List[UserField]:
    return await manager.get_registration_fields()


def _get_pydantic_specification(user_fields: List[UserField]) -> Tuple[Any, Any]:
    fields: Any = {}
    validators: Any = {}
    for field in user_fields:
        field_type = USER_FIELD_TYPE_MAP[field.type]
        required = field.get_required()
        default = None

        if field.type == UserFieldType.BOOLEAN:
            """
            Special handling for booleans that are passed through HTML checkboxes.

            For the browser, when unchecked, the value is simply not passed.
            That's why we make it not required with a default at "False".

            When checked, the value is "on" by default, which is handled natively by Pydantic.

            Besides, we attach a special meaning to "required" booleans:
            it means that the value MUST BE "True".
            It can be useful for consent checkboxes for example.
            That's why in this case, we add a custom validator checking the value
            is only "True".
            """
            if required:
                validators[f"{field.slug}_validator"] = validator(
                    field.slug, allow_reuse=True, always=True
                )(true_bool_validator)
            required = False
            default = False

        fields[field.slug] = (
            field_type if required else Optional[field_type],
            default if default is not None else (... if required else None),
        )
    return fields, validators


async def get_user_create_model(
    registration_user_fields: List[UserField] = Depends(get_registration_user_fields),
) -> Type[UserCreate[UF]]:
    fields, validators = _get_pydantic_specification(registration_user_fields)
    user_fields_model = create_model(
        "UserFields",
        **fields,
        __validators__=validators,
        __base__=UserFields,  # type: ignore
    )
    return UserCreate[user_fields_model]  # type: ignore


async def get_user_create_internal_model(
    registration_user_fields: List[UserField] = Depends(get_registration_user_fields),
) -> Type[UserCreateInternal[UF]]:
    fields, validators = _get_pydantic_specification(registration_user_fields)
    user_fields_model = create_model(
        "UserFields",
        **fields,
        __validators__=validators,
        __base__=UserFields,  # type: ignore
    )
    return UserCreateInternal[user_fields_model]  # type: ignore
