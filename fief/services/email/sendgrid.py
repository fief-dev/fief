import json
from typing import Any

from python_http_client.exceptions import HTTPError
from sendgrid import SendGridAPIClient, SendGridException
from sendgrid.helpers.mail import Mail

from fief.services.email.base import (
    CreateDomainError,
    EmailDomain,
    EmailDomainDNSRecord,
    EmailProvider,
    SendEmailError,
    VerifyDomainError,
    format_address,
)


class DomainDoesNotExistError(CreateDomainError):
    def __init__(self, domain: str):
        super().__init__(f'The domain "{domain}" does not exist on this provider.')


class Sendgrid(EmailProvider):
    DOMAIN_AUTHENTICATION = True

    def __init__(self, api_key: str) -> None:
        self._client = SendGridAPIClient(api_key=api_key)

    def send_email(
        self,
        *,
        sender: tuple[str, str | None],
        recipient: tuple[str, str | None],
        subject: str,
        html: str | None = None,
        text: str | None = None,
    ):
        from_email, from_name = sender
        to_email, to_name = recipient
        try:
            message = Mail(
                from_email=format_address(from_email, from_name),
                to_emails=format_address(to_email, to_name),
                subject=subject,
                html_content=html,
                plain_text_content=text,
            )

            self._client.send(message)

        except (SendGridException, HTTPError) as e:
            raise SendEmailError(str(e)) from e

    def create_domain(self, domain: str) -> EmailDomain:
        try:
            response = self._client.client.whitelabel.domains.post(
                request_body={
                    "domain": domain,
                    "subdomain": "fief",
                    "custom_spf": False,
                    "default": False,
                    "automatic_security": True,
                }
            )
        except HTTPError as e:
            # Domain might exist on Sengrid but not on this Fief server
            # e.g. it has been added on another server
            # or it has been lost in the void.
            if self._is_domain_already_exists_error(e):
                return self._retrieve_existing_domain(domain)

            raise CreateDomainError(e.body.decode("utf-8")) from e
        except Exception as e:
            raise CreateDomainError(str(e)) from e

        data = json.loads(response.body)
        return self._domain_data_to_email_domain(data)

    def verify_domain(self, email_domain: EmailDomain) -> EmailDomain:
        try:
            response = self._client.client.whitelabel.domains._(
                int(email_domain.domain_id)
            ).validate.post()
        except Exception as e:
            raise VerifyDomainError(str(e)) from e

        data = json.loads(response.body)
        records = email_domain.records
        for record in records:
            record.verified = data["validation_results"][record.id]["valid"]
        email_domain.records = records

        return email_domain

    def _is_domain_already_exists_error(self, error: HTTPError) -> bool:
        if error.status_code == 400:
            data = json.loads(error.body)
            for error in data["errors"]:
                if "domain already exists" in error["message"]:
                    return True
        return False

    def _retrieve_existing_domain(self, domain: str) -> EmailDomain:
        response = self._client.client.whitelabel.domains.get(
            query_params={"domain": domain}
        )
        data = json.loads(response.body)

        if len(data) == 0:
            raise DomainDoesNotExistError(domain)

        return self._domain_data_to_email_domain(data[0])

    def _domain_data_to_email_domain(self, data: dict[str, Any]) -> EmailDomain:
        records: list[EmailDomainDNSRecord] = []
        for key, dns in data["dns"].items():
            records.append(
                EmailDomainDNSRecord(
                    id=key,
                    type=dns["type"],
                    host=dns["host"],
                    value=dns["data"],
                    verified=dns["valid"],
                )
            )
        return EmailDomain(
            domain_id=str(data["id"]), domain=data["domain"], records=records
        )
