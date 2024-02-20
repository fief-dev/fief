from collections.abc import AsyncGenerator

from fastapi import HTTPException, Request, status

from fief.db import AsyncSession
from fief.errors import APIErrorCode


async def get_main_async_session(
    request: Request,
) -> AsyncGenerator[AsyncSession, None]:
    try:
        async with request.state.main_async_session_maker() as session:
            yield session
    except ConnectionRefusedError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=APIErrorCode.SERVER_DATABASE_NOT_AVAILABLE,
        ) from e
