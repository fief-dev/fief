from pathlib import Path

from fastapi import FastAPI, Response, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException

from fief.paths import STATIC_DIRECTORY


class StaticFilesFallback(StaticFiles):
    def __init__(self, *args, fallback: Path, **kwargs) -> None:
        self.fallback = fallback
        super().__init__(*args, **kwargs)

    async def get_response(self, *args, **kwargs) -> Response:
        try:
            return await super().get_response(*args, **kwargs)
        except HTTPException as e:
            if e.status_code == status.HTTP_404_NOT_FOUND:
                return FileResponse(self.fallback)
            raise


app = FastAPI()

app.mount(
    "/",
    StaticFilesFallback(
        directory=STATIC_DIRECTORY / "frontend",
        fallback=STATIC_DIRECTORY / "frontend" / "index.html",
        html=False,
        check_dir=False,
    ),
    name="admin_frontend:frontend",
)
