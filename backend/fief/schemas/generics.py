from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar

import phonenumbers
import pycountry
import pytz
from pydantic import UUID4
from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field, PydanticValueError
from pydantic.generics import GenericModel


class BaseModel(PydanticBaseModel):
    class Config:
        orm_mode = True


PM = TypeVar("PM", bound=BaseModel)


class UUIDSchema(BaseModel):
    id: UUID4


class CreatedUpdatedAt(BaseModel):
    created_at: datetime
    updated_at: datetime


class PaginatedResults(GenericModel, Generic[PM]):
    count: int
    results: List[PM]


class TrueBooleanError(PydanticValueError):
    code = "boolean.must_be_true"
    msg_template = "value must be true"


def true_bool_validator(cls, v: bool):
    if v is False:
        raise TrueBooleanError()
    return v


class PhoneNumberError(PydanticValueError):
    code = "phone_number.invalid"
    msg_template = "value is not a valid phone number"


class PhoneNumberMissingRegionError(PhoneNumberError):
    code = "phone_number.missing_region"
    msg_template = "value is missing the country code"


class PhoneNumber(str):
    @classmethod
    def __modify_schema__(cls, field_schema: Dict[str, Any]) -> None:
        field_schema.update(type="string")

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value: str) -> str:
        try:
            parsed = phonenumbers.parse(value)
        except phonenumbers.phonenumberutil.NumberParseException as e:
            raise PhoneNumberMissingRegionError() from e
        if not phonenumbers.is_valid_number(parsed):
            raise PhoneNumberError()
        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)


class CountryCodeError(PydanticValueError):
    code = "country_code.invalid"
    msg_template = "value is not a valid country code"


class CountryCode(str):
    @classmethod
    def __modify_schema__(cls, field_schema: Dict[str, Any]) -> None:
        countries = sorted(pycountry.countries, key=lambda c: c.name)
        field_schema.update(
            type="enum",
            enum=[country.alpha_2 for country in countries],
            countries=[
                {"name": country.name, "alpha_2": country.alpha_2}
                for country in countries
            ],
        )

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value: str) -> str:
        if pycountry.countries.get(alpha_2=value) is None:
            raise CountryCodeError()
        return value


class Address(BaseModel):
    line1: str = Field(..., min_length=1)
    line2: Optional[str] = Field(None, min_length=1)
    postal_code: str = Field(..., min_length=1)
    city: str = Field(..., min_length=1)
    state: Optional[str] = Field(None, min_length=1)
    country: CountryCode


class TimezoneError(PydanticValueError):
    code = "timezone.invalid"
    msg_template = "value is not a valid timezone"


class Timezone(str):
    @classmethod
    def __modify_schema__(cls, field_schema: Dict[str, Any]) -> None:
        field_schema.update(
            type="enum", enum=sorted(pytz.common_timezones), title="timezone"
        )

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value: Any) -> str:
        if not isinstance(value, str):
            raise TypeError()
        try:
            timezone = pytz.timezone(value)
        except pytz.exceptions.UnknownTimeZoneError as e:
            raise TimezoneError() from e
        else:
            return str(timezone)
