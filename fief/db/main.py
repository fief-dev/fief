from fief.db.engine import create_async_session_maker, create_engine
from fief.settings import settings


def create_main_async_session_maker():
    main_engine = create_engine(settings.get_database_connection_parameters())
    return create_async_session_maker(main_engine)


__all__ = [
    "create_main_async_session_maker",
]
