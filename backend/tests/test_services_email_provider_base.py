"""We're testing the EmailProvider base class' format_address function, but
we can't instantiate an object of the base type, so we're using Null as
a proxy."""
from fief.services.email.null import Null


def test_format_address_with_only_email():
    email_provider = Null()

    formatted = email_provider.format_address("test@example.com")
    assert formatted == "test@example.com"


def test_format_address_with_name_and_address():
    email_provider = Null()

    formatted = email_provider.format_address("test@example.com", "Test Person")
    assert formatted == "Test Person <test@example.com>"
