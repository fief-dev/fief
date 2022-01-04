from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base

from fief.settings import settings

GlobalBase = declarative_base()


class AccountMeta(DeclarativeMeta):
    def __init__(cls, name, bases, dict_):
        try:
            cls.__tablename__ = dict_[
                "__tablename__"
            ] = f"{settings.account_table_prefix}{dict_['__tablename__']}"
        except KeyError:
            pass
        return super().__init__(name, bases, dict_)


AccountBase = declarative_base(metaclass=AccountMeta)
