from fastapi import Request

from fief.apps.auth.forms.auth import LoginForm
from fief.apps.auth.forms.profile import ProfileFormBase, get_profile_form_class
from fief.apps.auth.forms.register import RegisterFormBase, get_register_form_class
from fief.apps.auth.forms.reset import ForgotPasswordForm, ResetPasswordForm
from fief.models import Tenant, Theme, User
from fief.repositories import OAuthProviderRepository, UserFieldRepository
from fief.templates import templates


class ThemePreview:
    def __init__(
        self,
        oauth_provider_repository: OAuthProviderRepository,
        user_field_repository: UserFieldRepository,
    ) -> None:
        self.oauth_provider_repository = oauth_provider_repository
        self.user_field_repository = user_field_repository

    async def preview(
        self, page: str, theme: Theme, *, tenant: Tenant, user: User, request: Request
    ) -> str:
        page_functions = {
            "login": self.preview_login,
            "register": self.preview_register,
            "forgot_password": self.preview_forgot_password,
            "reset_password": self.preview_reset_password,
            "profile": self.preview_profile,
        }
        return await page_functions[page](
            theme, tenant=tenant, user=user, request=request
        )

    async def preview_login(
        self, theme: Theme, *, tenant: Tenant, user: User, request: Request
    ) -> str:
        oauth_providers = await self.oauth_provider_repository.all()
        form = LoginForm(meta={"request": request, "csrf": False})
        context = {
            "request": request,
            "form": form,
            "oauth_providers": oauth_providers,
            "tenant": tenant,
            "theme": theme,
        }
        template = templates.get_template("auth/login.html")
        return template.render(context)

    async def preview_register(
        self, theme: Theme, *, tenant: Tenant, user: User, request: Request
    ) -> str:
        registration_user_fields = (
            await self.user_field_repository.get_registration_fields()
        )
        register_form_class: type[RegisterFormBase] = await get_register_form_class(
            registration_user_fields, None
        )
        oauth_providers = await self.oauth_provider_repository.all()
        form = register_form_class(meta={"request": request, "csrf": False})
        context = {
            "request": request,
            "form": form,
            "finalize": False,
            "oauth_providers": oauth_providers,
            "tenant": tenant,
            "theme": theme,
        }
        template = templates.get_template("auth/register.html")
        return template.render(context)

    async def preview_forgot_password(
        self, theme: Theme, *, tenant: Tenant, user: User, request: Request
    ) -> str:
        form = ForgotPasswordForm(meta={"request": request, "csrf": False})
        context = {
            "request": request,
            "form": form,
            "tenant": tenant,
            "theme": theme,
        }
        template = templates.get_template("auth/forgot_password.html")
        return template.render(context)

    async def preview_reset_password(
        self, theme: Theme, *, tenant: Tenant, user: User, request: Request
    ) -> str:
        form = ResetPasswordForm(meta={"request": request, "csrf": False})
        context = {
            "request": request,
            "form": form,
            "tenant": tenant,
            "theme": theme,
        }
        template = templates.get_template("auth/reset_password.html")
        return template.render(context)

    async def preview_profile(
        self, theme: Theme, *, tenant: Tenant, user: User, request: Request
    ) -> str:
        update_user_fields = await self.user_field_repository.get_update_fields()
        profile_form_class: type[ProfileFormBase] = await get_profile_form_class(
            update_user_fields
        )
        form = profile_form_class(meta={"request": request, "csrf": False})
        context = {
            "request": request,
            "form": form,
            "user": user,
            "tenant": tenant,
            "theme": theme,
            "current_route": "auth.dashboard:profile",
        }
        template = templates.get_template("auth/dashboard/index.html")
        return template.render(context)
