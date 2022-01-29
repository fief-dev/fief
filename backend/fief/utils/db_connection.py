def get_database_url(url: str, asyncio=True) -> str:
    """
    Return a proper database URL depending on the async context.
    """
    if asyncio:
        if url.startswith("sqlite://"):
            return url.replace("sqlite://", "sqlite+aiosqlite://", 1)
        elif url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url
