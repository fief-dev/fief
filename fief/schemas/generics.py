from datetime import datetime
from typing import Annotated, Generic, TypeVar

import phonenumbers
import pycountry
import pytz
from pydantic import UUID4, AfterValidator, ConfigDict, Field, StringConstraints
from pydantic import BaseModel as PydanticBaseModel
from pydantic_core import PydanticCustomError


class BaseModel(PydanticBaseModel):
    model_config = ConfigDict(from_attributes=True)


PM = TypeVar("PM", bound=BaseModel)


class UUIDSchema(BaseModel):
    id: UUID4


class CreatedUpdatedAt(BaseModel):
    created_at: datetime
    updated_at: datetime


class PaginatedResults(BaseModel, Generic[PM]):
    count: int
    results: list[PM]


NonEmptyString = Annotated[str, StringConstraints(min_length=1)]


def true_only_boolean(v: bool):
    if v is False:
        raise PydanticCustomError("boolean.must_be_true", "value must be true")
    return v


TrueOnlyBoolean = Annotated[bool, AfterValidator(true_only_boolean)]


def validate_phone_number(v: str) -> str:
    try:
        parsed = phonenumbers.parse(v)
    except phonenumbers.phonenumberutil.NumberParseException as e:
        raise PydanticCustomError(
            "phone_number.missing_region", "value is missing the country code"
        ) from e
    if not phonenumbers.is_valid_number(parsed):
        raise PydanticCustomError(
            "phone_number.invalid", "value is not a valid phone number"
        )
    return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)


PhoneNumber = Annotated[str, AfterValidator(validate_phone_number)]


def validate_country_code(v: str) -> str:
    country = pycountry.countries.get(alpha_2=v)
    if country is None:
        raise PydanticCustomError(
            "country_code.invalid", "value is not a valid country code"
        )
    return country.alpha_2


class CountryCodeSchema:
    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema, handler):
        countries = sorted(pycountry.countries, key=lambda c: c.name)
        field_schema = handler(core_schema)
        field_schema.update(
            enum=[country.alpha_2 for country in countries],
        )
        return field_schema


CountryCode = Annotated[str, CountryCodeSchema, AfterValidator(validate_country_code)]


class Address(BaseModel):
    line1: str = Field(..., min_length=1)
    line2: str | None = Field(None, min_length=1)
    postal_code: str = Field(..., min_length=1)
    city: str = Field(..., min_length=1)
    state: str | None = Field(None, min_length=1)
    country: CountryCode


def validate_timezone(v: str) -> str:
    try:
        timezone = pytz.timezone(v)
    except pytz.exceptions.UnknownTimeZoneError as e:
        raise PydanticCustomError(
            "timezone.invalid", "value is not a valid timezone"
        ) from e
    else:
        return str(timezone)


class TimezoneSchema:
    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema, handler):
        field_schema = handler(core_schema)
        field_schema.update(enum=sorted(pytz.common_timezones), title="timezone")
        return field_schema


Timezone = Annotated[str, TimezoneSchema, AfterValidator(validate_timezone)]
