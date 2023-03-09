import pytest

from fief.services.localhost import is_localhost


@pytest.mark.parametrize(
    "host,result",
    [
        ("127.0.0.1", True),
        ("localhost", True),
        ("192.168.0.42", True),
        ("192.168.1.1", True),
        ("www.bretagne.duchy", False),
        ("www.fief.dev", False),
    ],
)
def test_is_localhost(host: str, result: bool):
    assert is_localhost(host) == result
