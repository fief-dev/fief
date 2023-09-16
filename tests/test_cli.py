from pydantic import ValidationError
from pytest_mock import MockerFixture
from typer.testing import CliRunner

from fief.cli import app

runner = CliRunner()


class TestCLIInfo:
    def test_missing_settings(self, mocker: MockerFixture):
        mocked_get_settings = mocker.patch("fief.cli.get_settings")
        mocked_get_settings.side_effect = ValidationError.from_exception_data(
            "Error", []
        )

        result = runner.invoke(app, ["info"])
        assert result.exit_code == 1
        assert "❌ Some environment variables are missing or invalid." in result.stdout

    def test_valid_settings(self):
        result = runner.invoke(app, ["info"])
        assert result.exit_code == 0
        assert "Fief version" in result.stdout
