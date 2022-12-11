from fastapi.responses import RedirectResponse
from starlette.datastructures import URL
from starlette.background import BackgroundTask


class HXRedirectResponse(RedirectResponse):
    def __init__(
        self,
        url: str | URL,
        status_code: int = 200,
        headers: dict[str, str] | None = None,
        background: BackgroundTask | None = None,
    ) -> None:
        super().__init__(url, status_code, headers, background)
        self.headers["HX-Redirect"] = self.headers["location"]
