from fastapi.templating import Jinja2Templates

from fief.paths import ADMIN_TEMPLATES_DIRECTORY


templates = Jinja2Templates(directory=ADMIN_TEMPLATES_DIRECTORY)
