#!/usr/bin/env python3
"""SPA static file server with optional API reverse-proxy for Aulos portals."""

from __future__ import annotations

import argparse
import functools
import http.client
import logging
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

_DEPLOY_DIR = Path(__file__).resolve().parent
if str(_DEPLOY_DIR) not in sys.path:
    sys.path.insert(0, str(_DEPLOY_DIR))

from rate_gate import RateGate, client_ip, rule_for  # noqa: E402

NO_CACHE = "no-cache, no-store, must-revalidate"
IMMUTABLE_ASSET = "public, max-age=31536000, immutable"
SHORT_CACHE = "public, max-age=3600"
PROXY_PREFIXES = ("/v1", "/health", "/docs", "/openapi.json")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("aulos.serve")


def cache_control_for(path: str) -> str:
    raw = urlparse(path).path
    lower = raw.lower()
    name = Path(lower).name
    if raw.startswith("/v1/") or raw.startswith("/g/") or raw in {"/health", "/docs", "/openapi.json"}:
        return NO_CACHE
    if name.endswith(".html") or name in {"sw.js", "manifest.webmanifest", "version.json"}:
        return NO_CACHE
    if "/assets/" in lower:
        return IMMUTABLE_ASSET
    return SHORT_CACHE


def public_guide_upstream_path(path: str) -> str | None:
    """Map pretty share URLs /g/{slug} → API public guide HTML (full page, no SPA shell)."""
    raw = urlparse(path).path.rstrip("/")
    if not raw.startswith("/g/"):
        return None
    slug = raw[len("/g/") :].strip("/")
    if not slug or "/" in slug or "." in slug:
        return None
    return f"/v1/public/guides/{slug}"


class AulosHandler(SimpleHTTPRequestHandler):
    proxy_host: str = "127.0.0.1"
    proxy_port: int = 5090
    rate_gate: RateGate = RateGate()
    rate_limit_enabled: bool = True
    trust_proxy: bool = True

    def end_headers(self) -> None:
        self.send_header("Cache-Control", cache_control_for(self.path))
        super().end_headers()

    def log_message(self, fmt: str, *args) -> None:  # noqa: A003
        logger.info("%s - %s", self.address_string(), fmt % args)

    def _client_ip(self) -> str:
        peer = self.client_address[0] if self.client_address else None
        return client_ip(self.headers, peer, trust_proxy=self.trust_proxy)

    def _check_rate_limit(self) -> bool:
        """Return False if the request was rejected with 429."""
        if not self.rate_limit_enabled:
            return True
        path = urlparse(self.path).path
        matched = rule_for(path)
        if matched is None:
            return True
        rule, limit, window = matched
        ip = self._client_ip()
        ok, retry = self.rate_gate.allow(f"{rule}:{ip}", limit=limit, window_sec=window)
        if ok:
            return True
        self.rate_gate.note_block(ip, path, rule)
        retry_s = max(1, int(retry + 0.999))
        body = b"Too many requests\n"
        self.send_response(429)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Retry-After", str(retry_s))
        self.send_header("Cache-Control", NO_CACHE)
        self.send_header("X-RateLimit-Rule", rule)
        super(SimpleHTTPRequestHandler, self).end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)
        return False

    def _proxy_target_path(self) -> str:
        mapped = public_guide_upstream_path(self.path)
        if mapped:
            return mapped
        return self.path

    def _should_proxy(self) -> bool:
        path = urlparse(self.path).path
        if public_guide_upstream_path(path):
            return True
        return any(path == p or path.startswith(p + "/") for p in PROXY_PREFIXES)

    def _proxy(self) -> None:
        length = int(self.headers.get("Content-Length", "0") or "0")
        body = self.rfile.read(length) if length > 0 else None
        upstream_path = self._proxy_target_path()
        # SSE / long chat may exceed 60s
        timeout = 180 if "/stream" in urlparse(upstream_path).path else 60
        conn = http.client.HTTPConnection(self.proxy_host, self.proxy_port, timeout=timeout)
        headers = {
            key: value
            for key, value in self.headers.items()
            if key.lower() not in {"host", "connection", "content-length"}
        }
        try:
            conn.request(self.command, upstream_path, body=body, headers=headers)
            upstream = conn.getresponse()
            content_type = (upstream.getheader("Content-Type") or "").lower()
            is_stream = "text/event-stream" in content_type or "/stream" in urlparse(upstream_path).path

            self.send_response(upstream.status)
            for key, value in upstream.getheaders():
                if key.lower() in {"transfer-encoding", "connection", "content-length"}:
                    continue
                self.send_header(key, value)
            if is_stream:
                self.send_header("Cache-Control", NO_CACHE)
                self.send_header("X-Accel-Buffering", "no")
                # Avoid Content-Length so browsers treat as streaming
                super(SimpleHTTPRequestHandler, self).end_headers()
                if self.command != "HEAD":
                    while True:
                        chunk = upstream.read(4096)
                        if not chunk:
                            break
                        self.wfile.write(chunk)
                        self.wfile.flush()
            else:
                payload = upstream.read()
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                if self.command != "HEAD":
                    self.wfile.write(payload)
        except OSError as exc:
            message = f"upstream unavailable: {exc}".encode()
            self.send_response(502)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(message)))
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(message)
        finally:
            conn.close()

    def do_GET(self) -> None:  # noqa: N802
        if not self._check_rate_limit():
            return
        if self._should_proxy():
            return self._proxy()
        path_only = self.path.split("?", 1)[0].split("#", 1)[0]
        candidate = Path(self.directory) / path_only.lstrip("/")
        if path_only in {"/", ""} or (not candidate.exists() and "." not in Path(path_only).name):
            self.path = "/index.html"
        return super().do_GET()

    def do_HEAD(self) -> None:  # noqa: N802
        if not self._check_rate_limit():
            return
        if self._should_proxy():
            return self._proxy()
        return super().do_HEAD()

    def do_POST(self) -> None:  # noqa: N802
        if not self._check_rate_limit():
            return
        if self._should_proxy():
            return self._proxy()
        self.send_error(405, "Method Not Allowed")

    def do_PUT(self) -> None:  # noqa: N802
        if not self._check_rate_limit():
            return
        if self._should_proxy():
            return self._proxy()
        self.send_error(405, "Method Not Allowed")

    def do_PATCH(self) -> None:  # noqa: N802
        if not self._check_rate_limit():
            return
        if self._should_proxy():
            return self._proxy()
        self.send_error(405, "Method Not Allowed")

    def do_DELETE(self) -> None:  # noqa: N802
        if not self._check_rate_limit():
            return
        if self._should_proxy():
            return self._proxy()
        self.send_error(405, "Method Not Allowed")

    def do_OPTIONS(self) -> None:  # noqa: N802
        if not self._check_rate_limit():
            return
        if self._should_proxy():
            return self._proxy()
        self.send_error(405, "Method Not Allowed")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="dist")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--proxy-host", default="127.0.0.1")
    parser.add_argument("--proxy-port", type=int, default=5090)
    parser.add_argument("--no-rate-limit", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.is_dir():
        raise SystemExit(f"static root not found: {root}")

    AulosHandler.proxy_host = args.proxy_host
    AulosHandler.proxy_port = args.proxy_port
    AulosHandler.rate_gate = RateGate()
    AulosHandler.rate_limit_enabled = not args.no_rate_limit
    handler = functools.partial(AulosHandler, directory=str(root))
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(
        f"Serving {root} on http://{args.host}:{args.port} "
        f"(proxy -> {args.proxy_host}:{args.proxy_port}; "
        f"rate_limit={'off' if args.no_rate_limit else 'on'})",
        flush=True,
    )
    server.serve_forever()


if __name__ == "__main__":
    main()
