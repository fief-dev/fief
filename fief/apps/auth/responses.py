import json

from fastapi.datastructures import URL
from fastapi.responses import Response
from starlette.background import BackgroundTask


class HXLocationResponse(Response):
    def __init__(
        self,
        hx_path: str | URL,
        status_code: int = 200,
        hx_source: str | None = None,
        hx_event: str | None = None,
        hx_handler: str | None = None,
        hx_target: str | None = None,
        hw_swap: str | None = None,
        hx_values: str | None = None,
        hx_headers: str | None = None,
        headers: dict[str, str] | None = None,
        background: BackgroundTask | None = None,
    ) -> None:
        super().__init__(None, status_code, headers, background=background)
        hx_location_dict = {"path": str(hx_path)}
        if hx_source is not None:
            hx_location_dict["source"] = hx_source
        if hx_event is not None:
            hx_location_dict["event"] = hx_event
        if hx_handler is not None:
            hx_location_dict["handler"] = hx_handler
        if hx_target is not None:
            hx_location_dict["target"] = hx_target
        if hw_swap is not None:
            hx_location_dict["swap"] = hw_swap
        if hx_values is not None:
            hx_location_dict["values"] = hx_values
        if hx_headers is not None:
            hx_location_dict["headers"] = hx_headers
        self.headers["HX-Location"] = json.dumps(hx_location_dict)
