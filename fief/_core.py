import contextlib
import typing
from collections.abc import Sequence

import dishka

from fief.storage import StorageProvider
from fief.storage._protocol import M, StorageProtocol

if typing.TYPE_CHECKING:
    from dishka.provider import BaseProvider


class Fief:
    _model_component_map: dict[type, str]

    def __init__(self, storage: StorageProvider | Sequence[StorageProvider]) -> None:
        providers: list[BaseProvider] = []

        storage_providers = self._init_storage(storage)
        providers.extend(storage_providers)

        self.container = dishka.make_container(*providers)
        self._request_container: dishka.Container | None = None

    def __enter__(self) -> "Fief":
        self.exit_stack = contextlib.ExitStack()
        self._request_container = self.exit_stack.enter_context(self.container())
        return self

    def __exit__(
        self,
        exc_type: type[BaseException],
        exc_value: BaseException,
        traceback: typing.Any,
    ) -> None:
        self.exit_stack.close()
        self._request_container = None

    def get_storage(self, model: type[M]) -> StorageProtocol[M]:
        component_key = self._model_component_map.get(model)
        return self.request_container.get(StorageProtocol[model], component_key)  # type: ignore[valid-type]

    @property
    def request_container(self) -> dishka.Container:
        if self._request_container is None:
            raise RuntimeError()
        return self._request_container

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
