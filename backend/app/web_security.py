"""Explicit host/proxy boundary; forwarded hosts/IPs never become authority."""
from dataclasses import dataclass
from ipaddress import ip_address
import os
import re
from starlette.responses import JSONResponse

LOCAL_HOSTS = ("localhost", "127.0.0.1", "testserver")


@dataclass(frozen=True)
class WebSettings:
    allowed_hosts: tuple[str, ...] = LOCAL_HOSTS
    trusted_proxies: tuple[str, ...] = ()

    @classmethod
    def from_env(cls):
        extra = os.getenv("DATA_QA_PUBLIC_HOSTS", "")
        hosts = []
        for value in extra.split(",") if extra else []:
            host = value.strip().lower()
            if len(host) > 253 or not re.fullmatch(r"[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?", host):
                raise ValueError("DATA_QA_PUBLIC_HOSTS requires exact hostnames without URLs, ports or wildcards")
            if any(not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label) for label in host.split(".")):
                raise ValueError("Invalid public hostname")
            hosts.append(host)
        peers = os.getenv("DATA_QA_TRUSTED_PROXIES", "")
        proxies = tuple(str(ip_address(value.strip())) for value in peers.split(",")) if peers else ()
        return cls(tuple(dict.fromkeys((*LOCAL_HOSTS, *hosts))), proxies)


class TrustedScheme:
    def __init__(self, app, settings):
        self.app, self.settings = app, settings

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            headers = dict(scope["headers"])
            peer = (scope.get("client") or (None,))[0]
            if peer in self.settings.trusted_proxies:
                scheme = headers.get(b"x-forwarded-proto", b"")
                if scheme not in (b"http", b"https"):
                    return await JSONResponse({"error": {"code": "PROXY_INVALID"}}, 400)(scope, receive, send)
                scope = {**scope, "scheme": scheme.decode()}
            host = headers.get(b"host", b"").decode("latin1").split(":")[0].lower()
            if host in self.settings.allowed_hosts and host not in LOCAL_HOSTS and scope["scheme"] != "https":
                return await JSONResponse({"error": {"code": "HTTPS_REQUIRED"}}, 400)(scope, receive, send)
        await self.app(scope, receive, send)
