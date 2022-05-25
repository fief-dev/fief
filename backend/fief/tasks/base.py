import asyncio
import contextlib
from typing import Any, AsyncContextManager, AsyncGenerator, Callable, ClassVar, Dict
from urllib.parse import urlparse

import dramatiq
import jinja2
from dramatiq.brokers.redis import RedisBroker
from pydantic import UUID4
from sqlalchemy import select

from fief.db import AsyncSession
from fief.db.engine import AsyncSession, create_async_session_maker, create_engine
from fief.db.workspace import get_connection
from fief.locale import Translations
from fief.models import Tenant, User, Workspace
from fief.paths import EMAIL_TEMPLATES_DIRECTORY
from fief.repositories import TenantRepository, WorkspaceRepository
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
    task.send(*args, **kwargs)


def get_main_session_task() -> AsyncContextManager[AsyncSession]:
    main_engine = create_engine(settings.get_database_url())
    return create_async_session_maker(main_engine)()


@contextlib.asynccontextmanager
async def get_workspace_session_task(
    workspace: Workspace,
) -> AsyncGenerator[AsyncSession, None]:
    engine = create_engine(workspace.get_database_url())
    async with get_connection(engine, workspace.get_schema_name()) as connection:
        async with AsyncSession(bind=connection, expire_on_commit=False) as session:
            yield session


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
        return loop.run_until_complete(self.run(*args, **kwargs))

    async def _get_workspace(self, workspace_id: UUID4) -> Workspace:
        async with self.get_main_session() as session:
            repository = WorkspaceRepository(session)
            workspace = await repository.get_by_id(workspace_id)
            if workspace is None:
                raise TaskError()
            return workspace

    async def _get_user(self, user_id: UUID4, workspace: Workspace) -> User:
        async with self.get_workspace_session(workspace) as session:
            statement = select(User).where(User.id == user_id)
            results = await session.execute(statement)
            row = results.first()
            if row is None:
                raise TaskError()
            user = row[0]
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
