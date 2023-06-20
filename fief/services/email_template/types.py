from enum import StrEnum


class EmailTemplateType(StrEnum):
    BASE = "BASE"
    WELCOME = "WELCOME"
    VERIFY_EMAIL = "VERIFY_EMAIL"
    FORGOT_PASSWORD = "FORGOT_PASSWORD"

    def get_display_name(self) -> str:
        display_names = {
            EmailTemplateType.BASE: "Base",
            EmailTemplateType.WELCOME: "Welcome",
            EmailTemplateType.VERIFY_EMAIL: "Verify email",
            EmailTemplateType.FORGOT_PASSWORD: "Forgot password",
        }
        return display_names[self]
