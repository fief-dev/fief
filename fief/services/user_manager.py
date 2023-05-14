import json
import uuid

from fastapi import Request
from furl import furl
from jwcrypto import jwt
from pydantic import UUID4

from fief import schemas
from fief.crypto.password import PasswordHelper
from fief.dependencies.webhooks import TriggerWebhooks
from fief.logger import AuditLogger
from fief.models import (
    AuditLogMessage,
    Tenant,
    User,
    UserField,
    UserFieldValue,
    Workspace,
)
from fief.repositories import UserRepository
from fief.services.password import PasswordValidation
from fief.services.webhooks.models import (
    UserCreated,
    UserForgotPasswordRequested,
    UserPasswordReset,
    UserUpdated,
)
from fief.tasks import SendTask, on_after_forgot_password, on_after_register

RESET_PASSWORD_TOKEN_AUDIENCE = "fief:reset"


class UserManagerError(Exception):
    pass


class UserDoesNotExistError(UserManagerError):
    pass


class UserAlreadyExistsError(UserManagerError):
    pass


class UserInactiveError(UserManagerError):
    pass


class InvalidResetPasswordTokenError(UserManagerError):
    pass


class InvalidPasswordError(UserManagerError):
    def __init__(self, messages: list[str]) -> None:
        super().__init__(messages)
        self.messages = messages


class UserManager:
    def __init__(
        self,
        *,
        workspace: Workspace,
        password_helper: PasswordHelper,
        user_repository: UserRepository,
        user_fields: list[UserField],
        send_task: SendTask,
        audit_logger: AuditLogger,
        trigger_webhooks: TriggerWebhooks,
    ):
        self.workspace = workspace
        self.password_helper = password_helper
        self.user_repository = user_repository
        self.user_fields = user_fields
        self.send_task = send_task
        self.audit_logger = audit_logger
        self.trigger_webhooks = trigger_webhooks

    async def get(self, id: UUID4, tenant: UUID4) -> User:
        user = await self.user_repository.get_by_id_and_tenant(id, tenant)

        if user is None:
            raise UserDoesNotExistError()

        return user

    async def get_by_email(self, user_email: str, tenant: UUID4) -> User:
        user = await self.user_repository.get_by_email_and_tenant(user_email, tenant)

        if user is None:
            raise UserDoesNotExistError()

        return user

    async def create(
        self,
        user_create: schemas.user.UserCreate[schemas.user.UF],
        tenant: UUID4,
        *,
        request: Request | None = None,
    ) -> User:
        await self.validate_password(user_create.password, user_create)

        try:
            await self.get_by_email(user_create.email, tenant)
            raise UserAlreadyExistsError()  # noqa: TRY301
        except UserDoesNotExistError:
            pass

        hashed_password = self.password_helper.hash(user_create.password)
        user = User(
            **user_create.dict(exclude={"password", "fields", "tenant_id"}),
            hashed_password=hashed_password,
            tenant_id=tenant,
        )

        user = await self.user_repository.create(user)
        await self.user_repository.session.refresh(user)

        for user_field in self.user_fields:
            user_field_value = UserFieldValue(user_field=user_field)
            try:
                value = user_create.fields.get_value(user_field.slug)
                if value is not None:
                    user_field_value.value = value
                    user.user_field_values.append(user_field_value)
            except AttributeError:
                default = user_field.get_default()
                if default is not None:
                    user_field_value.value = default
                    user.user_field_values.append(user_field_value)

        await self.user_repository.update(user)
        await self.on_after_register(user, request=request)

        return user

    async def forgot_password(
        self, user: User, *, request: Request | None = None
    ) -> None:
        if not user.is_active:
            raise UserInactiveError()

        claims = {
            "sub": str(user.id),
            "password_fgpt": self.password_helper.hash(user.hashed_password),
            "aud": RESET_PASSWORD_TOKEN_AUDIENCE,
        }
        signing_key = user.tenant.get_sign_jwk()
        token = jwt.JWT(
            header={"alg": "RS256", "kid": signing_key["kid"]}, claims=claims
        )
        token.make_signed_token(signing_key)

        await self.on_after_forgot_password(user, token.serialize(), request=request)

    async def reset_password(
        self,
        token: str,
        password: str,
        tenant: Tenant,
        *,
        request: Request | None = None,
    ) -> User:
        try:
            decoded_token = jwt.JWT(
                jwt=token,
                algs=["RS256"],
                key=tenant.get_sign_jwk(),
                check_claims={"aud": RESET_PASSWORD_TOKEN_AUDIENCE},
            )
            claims = json.loads(decoded_token.claims)
        except (
            ValueError,
            jwt.JWTExpired,
            jwt.JWTMissingClaim,
            jwt.JWTInvalidClaimValue,
        ) as e:
            raise InvalidResetPasswordTokenError() from e

        try:
            user_id = claims["sub"]
            password_fingerprint = claims["password_fgpt"]
        except KeyError as e:
            raise InvalidResetPasswordTokenError() from e

        try:
            parsed_id = uuid.UUID(user_id)
        except ValueError as e:
            raise InvalidResetPasswordTokenError() from e

        user = await self.get(parsed_id, tenant.id)

        valid_password_fingerprint, _ = self.password_helper.verify_and_update(
            user.hashed_password, password_fingerprint
        )
        if not valid_password_fingerprint:
            raise InvalidResetPasswordTokenError()

        if not user.is_active:
            raise UserInactiveError()

        user = await self.set_user_attributes(user, password=password)
        await self.user_repository.update(user)

        await self.on_after_reset_password(user, request=request)

        return user

    async def update(
        self,
        user_update: schemas.user.UserUpdate[schemas.user.UF],
        user: User,
        *,
        request: Request | None = None,
    ) -> User:
        user = await self.set_user_attributes(
            user, **user_update.dict(exclude={"fields"})
        )

        if user_update.fields is not None:
            for user_field in self.user_fields:
                existing_user_field_value = user.get_user_field_value(user_field)
                # Update existing value
                if existing_user_field_value is not None:
                    try:
                        value = user_update.fields.get_value(user_field.slug)
                        if value is not None:
                            existing_user_field_value.value = value
                    except AttributeError:
                        pass
                # Create new value
                else:
                    user_field_value = UserFieldValue(user_field=user_field)
                    try:
                        value = user_update.fields.get_value(user_field.slug)
                        if value is not None:
                            user_field_value.value = value
                            user.user_field_values.append(user_field_value)
                    except AttributeError:
                        default = user_field.get_default()
                        if default is not None:
                            user_field_value.value = default
                            user.user_field_values.append(user_field_value)

        await self.on_after_update(user, request=request)
        return user

    async def on_after_register(self, user: User, *, request: Request | None = None):
        self.audit_logger(AuditLogMessage.USER_REGISTERED, subject_user_id=user.id)
        self.trigger_webhooks(UserCreated, user, schemas.user.UserRead)
        self.send_task(on_after_register, str(user.id), str(self.workspace.id))

    async def on_after_update(self, user: User, *, request: Request | None = None):
        self.audit_logger(AuditLogMessage.USER_UPDATED, subject_user_id=user.id)
        self.trigger_webhooks(UserUpdated, user, schemas.user.UserRead)

    async def on_after_forgot_password(
        self, user: User, token: str, *, request: Request | None = None
    ):
        self.audit_logger(
            AuditLogMessage.USER_FORGOT_PASSWORD_REQUESTED, subject_user_id=user.id
        )
        self.trigger_webhooks(UserForgotPasswordRequested, user, schemas.user.UserRead)

        assert request is not None
        reset_url = furl(user.tenant.url_for(request, "reset:reset"))
        reset_url.add(query_params={"token": token})
        self.send_task(
            on_after_forgot_password,
            str(user.id),
            str(self.workspace.id),
            reset_url.url,
        )

    async def on_after_reset_password(
        self, user: User, *, request: Request | None = None
    ) -> None:
        self.audit_logger(AuditLogMessage.USER_PASSWORD_RESET, subject_user_id=user.id)
        self.trigger_webhooks(UserPasswordReset, user, schemas.user.UserRead)

    async def authenticate(
        self, email: str, password: str, tenant: UUID4
    ) -> User | None:
        try:
            user = await self.get_by_email(email, tenant)
        except UserDoesNotExistError:
            # Run the hasher to mitigate timing attack
            # Inspired from Django: https://code.djangoproject.com/ticket/20760
            self.password_helper.hash(password)
            return None

        verified, updated_password_hash = self.password_helper.verify_and_update(
            password, user.hashed_password
        )
        if not verified:
            return None
        # Update password hash to a more robust one if needed
        if updated_password_hash is not None:
            user.hashed_password = updated_password_hash
            await self.user_repository.update(user)

        return user

    async def validate_password(
        self, password: str, user: schemas.user.UserCreate | User
    ) -> None:
        password_validation = PasswordValidation.validate(password)
        if not password_validation.valid:
            raise InvalidPasswordError(password_validation.messages)

    async def set_user_attributes(
        self,
        user: User,
        *,
        email: str | None = None,
        password: str | None = None,
        **kwargs,
    ) -> User:
        if email is not None and user.email != email:
            try:
                await self.get_by_email(email, user.tenant_id)
                raise UserAlreadyExistsError()  # noqa: TRY301
            except UserDoesNotExistError:
                user.email = email
                user.is_verified = False

        if password is not None:
            await self.validate_password(password, user)
            user.hashed_password = self.password_helper.hash(password)

        for field, value in kwargs.items():
            setattr(user, field, value)

        return user
