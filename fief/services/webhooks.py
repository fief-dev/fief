import hmac
import time
from enum import StrEnum
from hashlib import sha256
from typing import Generic

import httpx
from pydantic.generics import GenericModel

from fief.schemas.generics import PM


class WebhookEventType(StrEnum):
    USER_REGISTERED = "USER_REGISTERED"


class WebhookEvent(GenericModel, Generic[PM]):
    event: WebhookEventType
    object: PM


class Webhook:
    url: str
    secret: str


class WebhookLog:
    attempt: int
    status_code: str
    payload: str


class WebhookDeliveryError(Exception):
    pass


class WebhookDelivery:
    def __init__(self) -> None:
        pass

    async def send(self, webhook: Webhook, event: WebhookEvent, attempt=1):
        async with httpx.AsyncClient() as client:
            payload = event.json()
            signature, ts = self._get_signature(webhook.secret)
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

            WebhookLog(
                status_code=response.status_code, attempt=attempt, payload=payload
            )
            # await save_webhook_log()

            if not response.is_success:
                raise WebhookDeliveryError()

    def _get_signature(payload: str, secret: str) -> tuple[str, int]:
        ts = int(time.time())
        message = f"{ts}.{payload}"

        hash = hmac.new(
            secret.encode("utf-8"),
            msg=message.encode("utf-8"),
            digestmod=sha256,
        )
        signature = hash.hexdigest()
        return signature, ts
