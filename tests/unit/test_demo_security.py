"""Host/proxy boundary tests do not contact a database or public tunnel."""
import os
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.app.api import create_app
from backend.app.web_security import WebSettings, LOCAL_HOSTS

HOST = "demo-example.trycloudflare.com"
ENV = {"DATA_QA_PUBLIC_HOSTS": HOST, "DATA_QA_TRUSTED_PROXIES": "172.29.246.2"}


class DemoSecurityTests(unittest.TestCase):
    def test_defaults_and_invalid_configuration(self):
        with patch.dict(os.environ, {"DATA_QA_PUBLIC_HOSTS": "", "DATA_QA_TRUSTED_PROXIES": ""}):
            self.assertEqual(WebSettings.from_env(), WebSettings(LOCAL_HOSTS, ()))
        for host in ("*", "*.trycloudflare.com", "https://example.com", "host:443", "", "bad..host", "a" * 64 + ".com"):
            if not host:
                continue
            with self.subTest(host=host), patch.dict(os.environ, {"DATA_QA_PUBLIC_HOSTS": host}):
                with self.assertRaises(ValueError):
                    WebSettings.from_env()
        for peer in ("*", "172.29.246.0/24", "proxy", "127.0.0.1,"):
            with patch.dict(os.environ, {"DATA_QA_TRUSTED_PROXIES": peer}):
                with self.assertRaises(ValueError):
                    WebSettings.from_env()

    def client(self, peer):
        with patch.dict(os.environ, ENV):
            return TestClient(create_app("postgresql://invalid"), base_url="http://" + HOST, client=(peer, 1234))

    def test_only_exact_host_and_trusted_scheme(self):
        client = self.client("172.29.246.2")
        self.assertEqual(client.get("/api/courses", headers={"X-Forwarded-Proto": "https"}).status_code, 200)
        for proto in ("", "https,http", "ftp"):
            self.assertEqual(client.get("/api/courses", headers={"X-Forwarded-Proto": proto}).status_code, 400)
        self.assertEqual(client.get("/api/courses", headers={"X-Forwarded-Proto": "http"}).json()["error"]["code"], "HTTPS_REQUIRED")
        for host in ("evil.example", "other.trycloudflare.com", "www." + HOST):
            self.assertEqual(client.get("/api/courses", headers={"Host": host, "X-Forwarded-Proto": "https"}).status_code, 400)
        self.assertEqual(self.client("192.0.2.1").get("/api/courses", headers={"X-Forwarded-Proto": "https", "Forwarded": "proto=https"}).status_code, 400)

    def test_https_origin_uses_proxy_scheme_without_forwarded_host(self):
        client = self.client("172.29.246.2")
        headers = {"X-Forwarded-Proto": "https", "Origin": "https://" + HOST, "X-Forwarded-Host": "evil.example"}
        # Same-origin reaches the normal auth dependency; cross-origin is rejected first.
        self.assertEqual(client.post("/api/sessions", json={"lab_id": "x"}, headers=headers).status_code, 401)
        for extra in ({"Origin": "http://" + HOST}, {"Origin": "https://evil.example"}, {"Sec-Fetch-Site": "cross-site"}):
            self.assertEqual(client.post("/api/sessions", json={"lab_id": "x"}, headers={**headers, **extra}).status_code, 403)
