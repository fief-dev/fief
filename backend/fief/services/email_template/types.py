from enum import Enum


class EmailTemplateType(str, Enum):
    BASE = "BASE"
    WELCOME = "WELCOME"
    FORGOT_PASSWORD = "FORGOT_PASSWORD"
