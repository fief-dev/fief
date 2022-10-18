from fief.services.email.base import format_address


def test_format_address_with_only_email():
    formatted = format_address("test@example.com")
    assert formatted == "test@example.com"


def test_format_address_with_name_and_address():
    formatted = format_address("test@example.com", "Test Person")
    assert formatted == "Test Person <test@example.com>"
