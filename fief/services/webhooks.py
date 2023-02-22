import hmac
import time
from enum import StrEnum
from hashlib import sha256
from typing import Generic

import httpx
from pydantic.generics import GenericModel

from fief.models import Webhook, WebhookLog
from fief.repositories import WebhookLogRepository
from fief.schemas.generics import PM


class WebhookEventType(StrEnum):
    USER_REGISTERED = "USER_REGISTERED"


class WebhookEvent(GenericModel, Generic[PM]):
    event: WebhookEventType
    object: PM


class WebhookDeliveryError(Exception):
    def __init__(self, message: str, response: httpx.Response) -> None:
        super().__init__(message)
        self.response = response


class WebhookDelivery:
    def __init__(self, webhook_log_repository: WebhookLogRepository) -> None:
        self.webhook_log_repository = webhook_log_repository

    async def send(self, webhook: Webhook, event: WebhookEvent, attempt: int = 1):
        async with httpx.AsyncClient() as client:
            payload = event.json()
            signature, ts = self._get_signature(payload, webhook.secret)
            response = await client.post(
                webhook.url,
                content=payload,
                headers={
                    "Content-Type": "application/json",
                    "X-Fief-Webhook-Signature": signature,
                    "X-Fief-Webhook-Timestamp": str(ts),
                },
                follow_redirects=False,
            )

            webhook_log = WebhookLog(
                webhook_id=webhook.id,
                attempt=attempt,
                payload=payload,
                status_code=response.status_code,
                success=response.is_success,
            )
            await self.webhook_log_repository.create(webhook_log)

            if not response.is_success:
                raise WebhookDeliveryError(
                    "Received an non-success status code", response=response
                )

    def _get_signature(self, payload: str, secret: str) -> tuple[str, int]:
        ts = int(time.time())
        message = f"{ts}.{payload}"

        hash = hmac.new(
            secret.encode("utf-8"),
            msg=message.encode("utf-8"),
            digestmod=sha256,
        )
        signature = hash.hexdigest()
        return signature, ts
