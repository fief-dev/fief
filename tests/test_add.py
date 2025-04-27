import pytest

from fief import add


@pytest.mark.parametrize(
    "a,b,result",
    [
        (0, 0, 0),
        (1, 1, 2),
        (3, 2, 5),
    ],
)
def test_add(a: int, b: int, result: int):
    assert add(a, b) == result
