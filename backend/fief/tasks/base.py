import asyncio
from typing import Any, AsyncContextManager, Callable, ClassVar, Dict, Protocol
from urllib.parse import urlparse

import dramatiq
import jinja2
from dramatiq.brokers.redis import RedisBroker
from pydantic import UUID4
from sqlalchemy import select

from fief.db import AsyncSession
from fief.locale import Translations
from fief.managers import AccountManager, TenantManager
from fief.models import Account, Tenant, User
from fief.paths import EMAIL_TEMPLATES_DIRECTORY
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


class TaskError(Exception):
    pass


class TaskBase:
    __name__: ClassVar[str]

    def __init__(
        self,
        get_global_session: Callable[..., AsyncContextManager[AsyncSession]],
        get_account_session: Callable[..., AsyncContextManager[AsyncSession]],
        email_provider: EmailProvider,
    ) -> None:
        self.get_global_session = get_global_session
        self.get_account_session = get_account_session
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

    async def _get_account(self, account_id: UUID4) -> Account:
        async with self.get_global_session() as session:
            manager = AccountManager(session)
            account = await manager.get_by_id(account_id)
            if account is None:
                raise TaskError()
            return account

    async def _get_user(self, user_id: UUID4, account: Account) -> User:
        async with self.get_account_session(account) as session:
            statement = select(User).where(User.id == user_id)
            results = await session.execute(statement)
            row = results.first()
            if row is None:
                raise TaskError()
            user = row[0]
            return user

    async def _get_tenant(self, tenant_id: UUID4, account: Account) -> Tenant:
        async with self.get_account_session(account) as session:
            manager = TenantManager(session)
            tenant = await manager.get_by_id(tenant_id)
            if tenant is None:
                raise TaskError()
            return tenant

    def _render_email_template(
        self, template: str, translations: Translations, context: Dict[str, Any]
    ) -> str:
        self.jinja_env.install_gettext_translations(translations, newstyle=True)  # type: ignore
        template_object = self.jinja_env.get_template(template)
        return template_object.render(context)
