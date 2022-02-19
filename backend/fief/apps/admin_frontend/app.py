import os
import stat

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from fief.paths import STATIC_DIRECTORY

app = FastAPI()

app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIRECTORY / "frontend" / "static", html=True),
    name="admin_frontend:static",
)

app.mount(
    "/locales",
    StaticFiles(directory=STATIC_DIRECTORY / "frontend" / "locales", html=True),
    name="admin_frontend:locales",
)


@app.get("/{path:path}", name="admin_frontend:index")
async def main(path: str):
    full_path = STATIC_DIRECTORY / "frontend" / path

    try:
        path_stat = os.stat(full_path)
        if stat.S_ISREG(path_stat.st_mode):
            return FileResponse(full_path)
    except FileNotFoundError:
        pass

    return FileResponse(STATIC_DIRECTORY / "frontend" / "index.html")
