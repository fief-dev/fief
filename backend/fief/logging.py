import logging

from uvicorn.logging import DefaultFormatter

from fief.settings import settings

formatter = DefaultFormatter(fmt="%(levelprefix)s %(message)s")
handler = logging.StreamHandler()
handler.setFormatter(formatter)

logger = logging.getLogger("fief")
logger.setLevel(settings.log_level)
logger.addHandler(handler)
