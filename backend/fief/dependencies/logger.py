from fastapi import Request

from fief.logger import logger


async def get_logger_request(request: Request):
    context_logger = logger.bind(
        method=request.method,
        path=request.url.path,
        client_addr="%s:%d" % request.client if request.client else "",
    )
    return context_logger
