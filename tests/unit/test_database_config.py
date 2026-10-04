import os
import sys
import unittest
from unittest.mock import Mock, patch

from backend.app.config import DEFAULT_DATABASE_URL, Settings
from backend.app.persistence.database import DEFAULT_CONNECT_TIMEOUT_SECONDS, connect


class DatabaseConfigTests(unittest.TestCase):
    def test_container_host_handles_password_without_uri_interpolation(self):
        from unittest.mock import patch
        from psycopg.conninfo import conninfo_to_dict
        from backend.app.config import Settings
        with patch.dict("os.environ",{"DATA_QA_DATABASE_HOST":"postgres","POSTGRES_PASSWORD":"a@b:c / d","DATABASE_URL":"postgresql://wrong"}):
            settings=Settings.from_env()
        parts=conninfo_to_dict(settings.database_url)
        self.assertEqual(parts["host"],"postgres")
        self.assertEqual(parts["password"],"a@b:c / d")
    def test_default_url_matches_ipv4_only_compose_binding(self):
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings.from_env()

        self.assertEqual(settings.database_url, DEFAULT_DATABASE_URL)
        self.assertIn("@127.0.0.1:5432/", settings.database_url)
        self.assertNotIn("@localhost:", settings.database_url)

    def test_environment_url_still_overrides_default(self):
        custom_url = "postgresql://example.invalid/custom"
        with patch.dict(os.environ, {"DATABASE_URL": custom_url}, clear=True):
            self.assertEqual(Settings.from_env().database_url, custom_url)

    def test_connect_applies_bounded_timeout(self):
        fake_psycopg = Mock()
        database_url = "postgresql://example.invalid/test"

        with patch.dict(sys.modules, {"psycopg": fake_psycopg}):
            connect(database_url)

        fake_psycopg.connect.assert_called_once_with(
            database_url,
            connect_timeout=DEFAULT_CONNECT_TIMEOUT_SECONDS,
        )
        self.assertEqual(DEFAULT_CONNECT_TIMEOUT_SECONDS, 5)


if __name__ == "__main__":
    unittest.main()
