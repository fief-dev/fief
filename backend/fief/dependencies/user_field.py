from typing import Any, List, Literal, Optional, Tuple, Type

from fastapi import Depends, HTTPException, status
from fastapi.exceptions import RequestValidationError
from pydantic import UUID4, ValidationError, create_model, validator
from sqlalchemy import select

from fief.dependencies.pagination import (
    Ordering,
    Pagination,
    get_ordering,
    get_paginated_objects,
    get_pagination,
)
from fief.dependencies.workspace_repositories import get_user_field_repository
from fief.models import UserField
from fief.models.user_field import UserFieldType
from fief.repositories import UserFieldRepository
from fief.schemas.generics import true_bool_validator
from fief.schemas.user import UF, UserCreate, UserCreateInternal, UserFields, UserUpdate
from fief.schemas.user_field import (
    USER_FIELD_CAN_HAVE_DEFAULT,
    USER_FIELD_TYPE_MAP,
    UserFieldConfigurationBase,
    UserFieldConfigurationChoice,
    UserFieldConfigurationDefault,
    UserFieldCreate,
    UserFieldUpdate,
    get_user_field_pydantic_type,
)


async def get_paginated_user_fields(
    pagination: Pagination = Depends(get_pagination),
    ordering: Ordering = Depends(get_ordering),
    repository: UserFieldRepository = Depends(get_user_field_repository),
) -> Tuple[List[UserField], int]:
    statement = select(UserField)
    return await get_paginated_objects(statement, pagination, ordering, repository)


async def get_user_field_by_id_or_404(
    id: UUID4,
    repository: UserFieldRepository = Depends(get_user_field_repository),
) -> UserField:
    user_field = await repository.get_by_id(id)

    if user_field is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return user_field


async def get_user_fields(
    repository: UserFieldRepository = Depends(get_user_field_repository),
) -> List[UserField]:
    return await repository.all()


async def get_user_field_create_internal_model(user_field_create: UserFieldCreate):
    user_field_type = user_field_create.type
    configuration_type = UserFieldConfigurationBase
    if user_field_type == UserFieldType.CHOICE:
        configuration_type = UserFieldConfigurationChoice
    elif USER_FIELD_CAN_HAVE_DEFAULT[user_field_type]:
        configuration_type = UserFieldConfigurationDefault[
            USER_FIELD_TYPE_MAP[user_field_type]  # type: ignore
        ]

    return create_model(
        "UserFieldCreateInternal",
        type=(Literal[user_field_type], ...),  # type: ignore
        configuration=(configuration_type, ...),
        __base__=UserFieldCreate,
    )


async def get_validated_user_field_create(
    user_field_create: UserFieldCreate,
    user_field_create_internal_model: Type[UserFieldCreate] = Depends(
        get_user_field_create_internal_model
    ),
) -> UserFieldCreate:
    body_model = create_model(
        "UserFieldCreateInternalBody",
        body=(user_field_create_internal_model, ...),
    )
    try:
        validated_user_field_create = body_model(body=user_field_create.dict())
    except ValidationError as e:
        raise RequestValidationError(e.raw_errors) from e
    else:
        return validated_user_field_create.body  # type: ignore


async def get_user_field_update_internal_model(
    user_field: UserField = Depends(get_user_field_by_id_or_404),
):
    user_field_type = user_field.type
    configuration_type = UserFieldConfigurationBase
    if user_field_type == UserFieldType.CHOICE:
        configuration_type = UserFieldConfigurationChoice
    elif USER_FIELD_CAN_HAVE_DEFAULT[user_field_type]:
        configuration_type = UserFieldConfigurationDefault[
            USER_FIELD_TYPE_MAP[user_field_type]  # type: ignore
        ]

    return create_model(
        "UserFieldUpdateInternal",
        type=(Literal[user_field_type], ...),  # type: ignore
        configuration=(Optional[configuration_type], None),
        __base__=UserFieldUpdate,
    )


async def get_validated_user_field_update(
    user_field_update: UserFieldUpdate,
    user_field: UserField = Depends(get_user_field_by_id_or_404),
    user_field_update_internal_model: Type[UserFieldUpdate] = Depends(
        get_user_field_update_internal_model
    ),
) -> UserFieldUpdate:
    body_model = create_model(
        "UserFieldUpdateInternalBody",
        body=(user_field_update_internal_model, ...),
    )
    try:
        validated_user_field_update = body_model(
            body={"type": user_field.type, **user_field_update.dict(exclude_unset=True)}
        )
    except ValidationError as e:
        raise RequestValidationError(e.raw_errors) from e
    else:
        return validated_user_field_update.body  # type: ignore


async def get_registration_user_fields(
    repository: UserFieldRepository = Depends(get_user_field_repository),
) -> List[UserField]:
    return await repository.get_registration_fields()


async def get_update_user_fields(
    repository: UserFieldRepository = Depends(get_user_field_repository),
) -> List[UserField]:
    return await repository.get_update_fields()


def _get_pydantic_specification(user_fields: List[UserField]) -> Tuple[Any, Any]:
    fields: Any = {}
    validators: Any = {}
    for field in user_fields:
        field_type = get_user_field_pydantic_type(field)
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


async def get_admin_user_create_internal_model(
    user_fields: List[UserField] = Depends(get_user_fields),
) -> Type[UserCreateInternal[UF]]:
    fields, validators = _get_pydantic_specification(user_fields)
    user_fields_model = create_model(
        "UserFields",
        **fields,
        __validators__=validators,
        __base__=UserFields,  # type: ignore
    )
    return UserCreateInternal[user_fields_model]  # type: ignore


async def get_user_update_model(
    update_user_fields: List[UserField] = Depends(get_update_user_fields),
) -> Type[UserUpdate[UF]]:
    fields, validators = _get_pydantic_specification(update_user_fields)
    user_fields_model = create_model(
        "UserFields",
        **fields,
        __validators__=validators,
        __base__=UserFields,  # type: ignore
    )
    return UserUpdate[user_fields_model]  # type: ignore


async def get_admin_user_update_model(
    user_fields: List[UserField] = Depends(get_user_fields),
) -> Type[UserUpdate[UF]]:
    fields, validators = _get_pydantic_specification(user_fields)
    user_fields_model = create_model(
        "UserFields",
        **fields,
        __validators__=validators,
        __base__=UserFields,  # type: ignore
    )
    return UserUpdate[user_fields_model]  # type: ignore
