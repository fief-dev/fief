import asyncio
import contextlib
from typing import Any, AsyncContextManager, AsyncGenerator, Callable, ClassVar, Dict
from urllib.parse import urlparse

import dramatiq
import jinja2
from dramatiq.brokers.redis import RedisBroker
from pydantic import UUID4

from fief.db import AsyncSession
from fief.db.main import create_main_async_session_maker
from fief.db.workspace import WorkspaceEngineManager, get_workspace_session
from fief.locale import BabelMiddleware, Translations, get_babel_middleware_kwargs
from fief.logger import init_audit_logger, logger
from fief.models import Tenant, User, Workspace
from fief.paths import EMAIL_TEMPLATES_DIRECTORY
from fief.repositories import TenantRepository, UserRepository, WorkspaceRepository
from fief.services.email import EmailProvider
from fief.settings import settings

redis_parameters = urlparse(settings.redis_url)
redis_broker = RedisBroker(
    host=redis_parameters.hostname,
    port=redis_parameters.port,
    username=redis_parameters.username,
    password=redis_parameters.password,
    # Heroku Redis with TLS use self-signed certs, so we need to tinker a bit
    ssl=redis_parameters.scheme == "rediss",
    ssl_cert_reqs=None,
)
dramatiq.set_broker(redis_broker)


SendTask = Callable[..., None]


def send_task(task: dramatiq.Actor, *args, **kwargs):
    logger.debug("Send task", task=task.actor_name)
    task.send(*args, **kwargs)


def get_main_session_task() -> AsyncContextManager[AsyncSession]:
    return create_main_async_session_maker()()


@contextlib.asynccontextmanager
async def get_workspace_session_task(
    workspace: Workspace,
) -> AsyncGenerator[AsyncSession, None]:
    workspace_engine_manager = WorkspaceEngineManager()
    async with get_workspace_session(workspace, workspace_engine_manager) as session:
        yield session
    await workspace_engine_manager.close_all()


email_provider = settings.get_email_provider()


class TaskError(Exception):
    pass


class TaskBase:
    __name__: ClassVar[str]

    def __init__(
        self,
        get_main_session: Callable[
            ..., AsyncContextManager[AsyncSession]
        ] = get_main_session_task,
        get_workspace_session: Callable[
            ..., AsyncContextManager[AsyncSession]
        ] = get_workspace_session_task,
        email_provider: EmailProvider = email_provider,
    ) -> None:
        self.get_main_session = get_main_session
        self.get_workspace_session = get_workspace_session
        self.email_provider = email_provider

        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(EMAIL_TEMPLATES_DIRECTORY), autoescape=True
        )
        self.jinja_env.add_extension("jinja2.ext.i18n")

    def __call__(self, *args, **kwargs):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # The default policy doesn't create a loop by default for threads (only for main process)
            # Thus, we create one here and set it for future works.
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        init_audit_logger(self.get_main_session, self.get_workspace_session, loop)
        BabelMiddleware(app=None, **get_babel_middleware_kwargs())
        logger.info("Start task", task=self.__name__)
        result = loop.run_until_complete(self.run(*args, **kwargs))
        logger.info("Done task", task=self.__name__)
        return result

    async def _get_workspace(self, workspace_id: UUID4) -> Workspace:
        async with self.get_main_session() as session:
            repository = WorkspaceRepository(session)
            workspace = await repository.get_by_id(workspace_id)
            if workspace is None:
                raise TaskError()
            return workspace

    async def _get_user(self, user_id: UUID4, workspace: Workspace) -> User:
        async with self.get_workspace_session(workspace) as session:
            repository = UserRepository(session)
            user = await repository.get_by_id(user_id)
            if user is None:
                raise TaskError()
            return user

    async def _get_tenant(self, tenant_id: UUID4, workspace: Workspace) -> Tenant:
        async with self.get_workspace_session(workspace) as session:
            repository = TenantRepository(session)
            tenant = await repository.get_by_id(tenant_id)
            if tenant is None:
                raise TaskError()
            return tenant

    def _render_email_template(
        self, template: str, translations: Translations, context: Dict[str, Any]
    ) -> str:
        self.jinja_env.install_gettext_translations(translations, newstyle=True)  # type: ignore
        template_object = self.jinja_env.get_template(template)
        return template_object.render(context)
