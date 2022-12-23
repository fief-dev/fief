import ssl

import pytest

from fief.db.types import MySQLSSLMode, PostreSQLSSLMode, get_ssl_mode_parameters


class TestGetSSLModeParameters:
    @pytest.mark.parametrize(
        "drivername,ssl_mode",
        [
            ("postgresql", PostreSQLSSLMode.DISABLE),
            ("mysql+pymysql", MySQLSSLMode.DISABLED),
        ],
    )
    def test_disabled(self, drivername: str, ssl_mode: str):
        query, connect_args = get_ssl_mode_parameters(drivername, ssl_mode, {}, {})
        assert query == {}
        assert connect_args == {}

    @pytest.mark.parametrize(
        "ssl_mode",
        [
            PostreSQLSSLMode.ALLOW,
            PostreSQLSSLMode.PREFER,
            PostreSQLSSLMode.REQUIRE,
            PostreSQLSSLMode.VERIFY_CA,
            PostreSQLSSLMode.VERIFY_FULL,
        ],
    )
    def test_postgresql(self, ssl_mode: str):
        query, connect_args = get_ssl_mode_parameters("postgresql", ssl_mode, {}, {})
        assert query == {
            "sslmode": ssl_mode,
            "sslrootcert": ssl.get_default_verify_paths().openssl_cafile,
        }
        assert connect_args == {}

    @pytest.mark.parametrize(
        "drivername,ssl_mode",
        [
            ("postgresql+asyncpg", PostreSQLSSLMode.REQUIRE),
            ("mysql+pymysql", MySQLSSLMode.REQUIRED),
            ("mysql+aiomysql", MySQLSSLMode.REQUIRED),
        ],
    )
    def test_require(self, drivername: str, ssl_mode: str):
        query, connect_args = get_ssl_mode_parameters(drivername, ssl_mode, {}, {})
        assert query == {}

        context = connect_args["ssl"]
        assert isinstance(context, ssl.SSLContext)
        assert context.check_hostname is False
        assert context.verify_mode == ssl.CERT_NONE

    @pytest.mark.parametrize(
        "drivername,ssl_mode",
        [
            ("postgresql+asyncpg", PostreSQLSSLMode.VERIFY_CA),
            ("mysql+pymysql", MySQLSSLMode.VERIFY_CA),
            ("mysql+aiomysql", MySQLSSLMode.VERIFY_CA),
        ],
    )
    def test_verify_ca(self, drivername: str, ssl_mode: str):
        query, connect_args = get_ssl_mode_parameters(drivername, ssl_mode, {}, {})
        assert query == {}

        context = connect_args["ssl"]
        assert isinstance(context, ssl.SSLContext)
        assert context.check_hostname is False
        assert context.verify_mode == ssl.CERT_REQUIRED

    @pytest.mark.parametrize(
        "drivername,ssl_mode",
        [
            ("postgresql+asyncpg", PostreSQLSSLMode.VERIFY_FULL),
            ("mysql+pymysql", MySQLSSLMode.VERIFY_IDENTITY),
            ("mysql+aiomysql", MySQLSSLMode.VERIFY_IDENTITY),
        ],
    )
    def test_verify_full(self, drivername: str, ssl_mode: str):
        query, connect_args = get_ssl_mode_parameters(drivername, ssl_mode, {}, {})
        assert query == {}

        context = connect_args["ssl"]
        assert isinstance(context, ssl.SSLContext)
        assert context.check_hostname is True
        assert context.verify_mode == ssl.CERT_REQUIRED
