from collections import defaultdict
from typing import Any, Dict

from fastapi import Request


def recursive_defaultdict_factory():
    return defaultdict(recursive_defaultdict_factory)


async def get_form_data_dict(request: Request) -> Dict[str, Any]:
    form = await request.form()
    form_data_dict: Dict[str, Any] = defaultdict(recursive_defaultdict_factory)

    for field in form:
        data_dict = form_data_dict
        path = field.split(".")
        for key in path[:-1]:
            data_dict = data_dict[key]
        data_dict[path[-1]] = form[field]

    return form_data_dict
