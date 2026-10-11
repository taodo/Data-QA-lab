import os
import unittest
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
from types import SimpleNamespace
from unittest.mock import patch
from backend.app import demo, public_demo


class PublicDemoConfigurationTests(unittest.TestCase):
    def test_operator_failure_does_not_log_credential_details(self):
        from backend.app.main import main
        output, errors = StringIO(), StringIO()
        marker = "credential-detail-must-not-be-logged"
        with patch("sys.argv", ["dqa", "public-demo", "provision"]), \
             patch("backend.app.main.Settings.from_env", return_value=SimpleNamespace(database_url="unused")), \
             patch("backend.app.public_demo.provision", side_effect=RuntimeError(marker)), \
             redirect_stdout(output), redirect_stderr(errors):
            with self.assertRaises(SystemExit) as exc:
                main()
        self.assertTrue(marker not in str(exc.exception) + output.getvalue() + errors.getvalue())
        self.assertIn("PUBLIC_DEMO_OPERATION_FAILED", str(exc.exception))

    def test_bounded_account_cap(self):
        for value in ("10", "15", "50"):
            with patch.dict(os.environ, {"DATA_QA_DEMO_MAX_ACCOUNTS": value}):
                self.assertEqual(demo.account_limit(), int(value))
        for value in ("0", "5", "51", "", "ten", "10.0", " 10", "١٠"):
            with patch.dict(os.environ, {"DATA_QA_DEMO_MAX_ACCOUNTS": value}):
                with self.assertRaises(ValueError):
                    demo.account_limit()

    def test_explicit_demo_and_public_opt_in_required(self):
        for demo_mode, public_mode, expected in (("0", "1", False), ("1", "0", False), ("1", "1", True)):
            with patch.dict(os.environ, {"DATA_QA_DEMO_MODE": demo_mode, "DATA_QA_PUBLIC_DEMO_ENABLED": public_mode}):
                self.assertEqual(public_demo.enabled(), expected)
