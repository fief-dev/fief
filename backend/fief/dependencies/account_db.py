from fief.services.account_db import AccountDatabase


async def get_account_db() -> AccountDatabase:
    return AccountDatabase()
