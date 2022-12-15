import pytest
from starlette.datastructures import FormData
from wtforms import Form

from fief.forms import TimezoneField


class TestTimezoneField:
    class TimezoneForm(Form):
        timezone = TimezoneField()

    @pytest.mark.parametrize("timezone", ["Europe/Nantes", "US/Paris"])
    def test_invalid(self, timezone: str):
        form = TestTimezoneField.TimezoneForm(FormData({"timezone": timezone}))
        assert form.validate() is False
        assert len(form.timezone.errors) == 1

    @pytest.mark.parametrize("timezone", ["Europe/Paris", "US/Eastern"])
    def test_valid(self, timezone: str):
        form = TestTimezoneField.TimezoneForm(FormData({"timezone": timezone}))
        assert form.validate() is True
        assert form.timezone.data == timezone
