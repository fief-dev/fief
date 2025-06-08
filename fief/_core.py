import contextlib
import typing
from collections.abc import Sequence

import dishka

from fief._exceptions import FiefException
from fief.methods import (
    AMP,
    MM,
    MP,
    AsyncMethodProtocol,
    AsyncMethodProvider,
    AuthenticateKwargs,
    EnrollKwargs,
    MethodProtocol,
    MethodProvider,
)
from fief.storage import (
    AsyncStorageProtocol,
    AsyncStorageProvider,
    M,
    StorageProtocol,
    StorageProvider,
)

if typing.TYPE_CHECKING:
    from dishka.provider import BaseProvider


class MissingIdentifierFieldsException(FiefException):
    """Exception raised when required identifier fields are missing."""

    def __init__(self, fields: list[str]) -> None:
        self.fields = fields
        super().__init__(f"Missing identifier fields: {fields}")


class UserAlreadyExistsException(FiefException):
    """Exception raised when a user already exists with the given identifier fields."""

    def __init__(self, fields: dict[str, typing.Any]) -> None:
        self.fields = fields
        super().__init__(f"User already exists with identifier fields: {fields}")


class UserProtocol(typing.Protocol):
    id: typing.Any

    @classmethod
    def identifier_fields(cls) -> tuple[str, ...]:  # pragma: no cover
        """
        Return the identifier fields of the user model.

        The values of those fields are used to uniquely identify the user in the system.
        """
        ...


U = typing.TypeVar("U", bound=UserProtocol)
"""Generic type variable for user models."""


class _FiefRequestBase(typing.Generic[U]):
    """Base class for Fief requests."""

    user_model: type[U]

    def _validate_identifier_fields(
        self, fields: dict[str, typing.Any]
    ) -> tuple[str, ...]:
        identifier_fields = self.user_model.identifier_fields()
        missing_fields = [field for field in identifier_fields if field not in fields]
        if len(missing_fields) > 0:
            raise MissingIdentifierFieldsException(missing_fields)
        return identifier_fields


class FiefRequest(_FiefRequestBase[U], typing.Generic[U]):
    def __init__(self, fief: "Fief[U]", container: dishka.Container) -> None:
        self.fief = fief
        self.user_model = fief.user_model
        self.container = container

    def get_storage(self, model: type[M]) -> StorageProtocol[M]:
        component_key = self.fief._model_component_map.get(model)
        return self.container.get(StorageProtocol[model], component_key)  # type: ignore[valid-type]

    def get_method(self, type: type[MP], name: str | None = None) -> MP:
        names = self.fief._method_map.get(type, [])
        if name is not None and name not in names:
            raise ValueError(  # noqa: TRY003
                f"Method {name} is not registered for type {type.__name__}"
            )
        if name is None and len(names) > 1:
            raise ValueError(  # noqa: TRY003
                f"Multiple methods registered for type {type.__name__}, specify a name"
            )
        return self.container.get(type, names[0] if name is None else name)

    def get_user_storage(self) -> StorageProtocol[U]:
        return self.get_storage(self.user_model)

    def signup(
        self,
        method_cls: type[MethodProtocol[EnrollKwargs, AuthenticateKwargs]],
        enroll_data: EnrollKwargs,
        **fields: typing.Any,
    ) -> U:
        """
        Sign up a new user using the specified authentication method and fields.

        Args:
            method_cls: The authentication method class to use.
            enroll_data: The data for the method's enroll function.
            **fields: The user fields to create the new user. It must contain
                all the identifier fields.

        Returns:
            The newly created user.

        Raises:
            UserAlreadyExistsException: If a user already exists with the given identifier fields.
            MissingIdentifierFieldsException: If any of the identifier fields are missing.
            UnknownMethodException: If the authentication method is unknown.
        """
        user_storage = self.get_user_storage()
        method = self.get_method(method_cls)
        identifier_fields = self._validate_identifier_fields(fields)

        existing_user = user_storage.get_one(
            **{field: fields[field] for field in identifier_fields}
        )
        if existing_user is not None:
            raise UserAlreadyExistsException(
                {field: fields[field] for field in identifier_fields}
            )

        user = user_storage.create(**fields)
        method.enroll(user.id, enroll_data)

        return user

    def signin(
        self,
        method_cls: type[MethodProtocol[EnrollKwargs, AuthenticateKwargs]],
        auth_data: AuthenticateKwargs,
        **fields: typing.Any,
    ) -> U | None:
        """
        Sign in a user using the specified authentication method and fields.

        Args:
            method_cls: The authentication method class to use.
            auth_data: The data for the method's authenticate function.
            **fields: The fields to identify the user.

        Returns:
            The authenticated user or None if authentication fails.

        Raises:
            MissingIdentifierFieldsException: If any of the identifier fields are missing.
            UnknownMethodException: If the authentication method is unknown.
        """
        method = self.get_method(method_cls)
        user_storage = self.get_user_storage()
        identifier_fields = self._validate_identifier_fields(fields)

        user = user_storage.get_one(
            **{field: fields[field] for field in identifier_fields}
        )
        user_id = user.id if user else None

        if method.authenticate(user_id, auth_data) and user is not None:
            return user

        return None


class Fief(typing.Generic[U]):
    _model_component_map: dict[type, str]
    _method_map: dict[type[MethodProtocol[typing.Any, typing.Any]], list[str]]

    def __init__(
        self,
        storage: StorageProvider | Sequence[StorageProvider],
        methods: Sequence[MethodProvider[MM]],
        user_model: type[U],
    ) -> None:
        self.user_model = user_model
        storage_providers = self._init_storage(storage)
        method_providers = self._init_methods(methods)
        self.container = dishka.make_container(*(*storage_providers, *method_providers))

    def __enter__(self) -> FiefRequest[U]:
        self.exit_stack = contextlib.ExitStack()
        request_container = self.exit_stack.enter_context(self.container())
        return FiefRequest(self, request_container)

    def __exit__(
        self,
        exc_type: type[BaseException],
        exc_value: BaseException,
        traceback: typing.Any,
    ) -> None:
        self.exit_stack.close()

    def close(self) -> None:
        self.container.close()

    def _init_storage(
        self, storage: StorageProvider | Sequence[StorageProvider]
    ) -> list["BaseProvider"]:
        if isinstance(storage, StorageProvider):
            storage = [storage]

        providers: list[BaseProvider] = []
        model_component_map: dict[type, str] = {}
        for i, s in enumerate(storage):
            component_key = f"storage_{i}"
            for model in s.models:
                if model in model_component_map:
                    raise ValueError(  # noqa: TRY003
                        f"Model {model} is already registered in {model_component_map[model]}"
                    )
                model_component_map[model] = component_key
            providers.append(s.to_component(component_key))

        self._model_component_map = model_component_map
        return providers

    def _init_methods(
        self, methods: Sequence[MethodProvider[MM]]
    ) -> list["BaseProvider"]:
        providers: list[BaseProvider] = []
        names: set[str] = set()
        method_map: dict[type[MethodProtocol[typing.Any, typing.Any]], list[str]] = {}
        for method in methods:
            if method.name in names:
                raise ValueError(  # noqa: TRY003
                    f"Method with name {method.name} is already registered"
                )
            model_component_key = self._model_component_map[method.model]
            provider = dishka.Provider(component=method.name)
            provider.provide(
                method.get_provider(model_component_key), scope=dishka.Scope.REQUEST
            )
            names.add(method.name)
            method_map.setdefault(method.method_type, []).append(method.name)
            providers.append(provider)
        self._method_map = method_map
        return providers


class FiefAsyncRequest(_FiefRequestBase[U], typing.Generic[U]):
    def __init__(self, fief: "FiefAsync[U]", container: dishka.AsyncContainer) -> None:
        self.fief = fief
        self.user_model = fief.user_model
        self.container = container

    async def get_storage(self, model: type[M]) -> AsyncStorageProtocol[M]:
        component_key = self.fief._model_component_map.get(model)
        return await self.container.get(AsyncStorageProtocol[model], component_key)  # type: ignore[valid-type]

    async def get_user_storage(self) -> AsyncStorageProtocol[U]:
        return await self.get_storage(self.user_model)

    async def get_method(self, type: type[AMP], name: str | None = None) -> AMP:
        names = self.fief._method_map.get(type, [])
        if name is not None and name not in names:
            raise ValueError(  # noqa: TRY003
                f"Method {name} is not registered for type {type.__name__}"
            )
        if name is None and len(names) > 1:
            raise ValueError(  # noqa: TRY003
                f"Multiple methods registered for type {type.__name__}, specify a name"
            )
        return await self.container.get(type, names[0] if name is None else name)

    async def signup(
        self,
        method_cls: type[AsyncMethodProtocol[EnrollKwargs, AuthenticateKwargs]],
        enroll_data: EnrollKwargs,
        **fields: typing.Any,
    ) -> U:
        """
        Sign up a new user using the specified authentication method and fields.

        Args:
            method_cls: The authentication method class to use.
            enroll_data: The data for the method's enroll function.
            **fields: The user fields to create the new user. It must contain
                all the identifier fields.

        Returns:
            The newly created user.

        Raises:
            UserAlreadyExistsException: If a user already exists with the given identifier fields.
            MissingIdentifierFieldsException: If any of the identifier fields are missing.
            UnknownMethodException: If the authentication method is unknown.
        """
        user_storage = await self.get_user_storage()
        method = await self.get_method(method_cls)
        identifier_fields = self._validate_identifier_fields(fields)

        existing_user = await user_storage.get_one(
            **{field: fields[field] for field in identifier_fields}
        )
        if existing_user is not None:
            raise UserAlreadyExistsException(
                {field: fields[field] for field in identifier_fields}
            )

        user = await user_storage.create(**fields)
        await method.enroll(user.id, enroll_data)

        return user

    async def signin(
        self,
        method_cls: type[AsyncMethodProtocol[EnrollKwargs, AuthenticateKwargs]],
        auth_data: AuthenticateKwargs,
        **fields: typing.Any,
    ) -> U | None:
        """
        Sign in a user using the specified authentication method and fields.

        Args:
            method_cls: The authentication method class to use.
            auth_data: The data for the method's authenticate function.
            **fields: The fields to identify the user.

        Returns:
            The authenticated user or None if authentication fails.

        Raises:
            MissingIdentifierFieldsException: If any of the identifier fields are missing.
            UnknownMethodException: If the authentication method is unknown.
        """
        user_storage = await self.get_user_storage()
        method = await self.get_method(method_cls)
        identifier_fields = self._validate_identifier_fields(fields)

        user = await user_storage.get_one(
            **{field: fields[field] for field in identifier_fields}
        )
        user_id = user.id if user else None

        if await method.authenticate(user_id, auth_data) and user is not None:
            return user

        return None


class FiefAsync(typing.Generic[U]):
    _model_component_map: dict[type, str]
    _method_map: dict[type[AsyncMethodProtocol[typing.Any, typing.Any]], list[str]]

    def __init__(
        self,
        storage: AsyncStorageProvider | Sequence[AsyncStorageProvider],
        methods: Sequence[AsyncMethodProvider[MM]],
        user_model: type[U],
    ) -> None:
        self.user_model = user_model
        storage_providers = self._init_storage(storage)
        method_providers = self._init_methods(methods)
        self.container = dishka.make_async_container(
            *(*storage_providers, *method_providers)
        )

    async def __aenter__(self) -> FiefAsyncRequest[U]:
        self.exit_stack = contextlib.AsyncExitStack()
        request_container = await self.exit_stack.enter_async_context(self.container())
        return FiefAsyncRequest(self, request_container)

    async def __aexit__(
        self,
        exc_type: type[BaseException],
        exc_value: BaseException,
        traceback: typing.Any,
    ) -> None:
        await self.exit_stack.aclose()

    async def close(self) -> None:
        await self.container.close()

    def _init_storage(
        self, storage: AsyncStorageProvider | Sequence[AsyncStorageProvider]
    ) -> list["BaseProvider"]:
        if isinstance(storage, AsyncStorageProvider):
            storage = [storage]

        providers: list[BaseProvider] = []
        model_component_map: dict[type, str] = {}
        for i, s in enumerate(storage):
            component_key = f"storage_{i}"
            for model in s.models:
                if model in model_component_map:
                    raise ValueError(  # noqa: TRY003
                        f"Model {model} is already registered in {model_component_map[model]}"
                    )
                model_component_map[model] = component_key
            providers.append(s.to_component(component_key))

        self._model_component_map = model_component_map
        return providers

    def _init_methods(
        self, methods: Sequence[AsyncMethodProvider[MM]]
    ) -> list["BaseProvider"]:
        providers: list[BaseProvider] = []
        names: set[str] = set()
        method_map: dict[
            type[AsyncMethodProtocol[typing.Any, typing.Any]], list[str]
        ] = {}
        for method in methods:
            if method.name in names:
                raise ValueError(  # noqa: TRY003
                    f"Method with name {method.name} is already registered"
                )
            model_component_key = self._model_component_map[method.model]
            provider = dishka.Provider(component=method.name)
            provider.provide(
                method.get_provider(model_component_key), scope=dishka.Scope.REQUEST
            )
            names.add(method.name)
            method_map.setdefault(method.method_type, []).append(method.name)
            providers.append(provider)
        self._method_map = method_map
        return providers
