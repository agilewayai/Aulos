#!/usr/bin/env python3
"""SPA static file server with optional API reverse-proxy for Aulos portals."""

from __future__ import annotations

import argparse
import functools
import http.client
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


NO_CACHE = "no-cache, no-store, must-revalidate"
IMMUTABLE_ASSET = "public, max-age=31536000, immutable"
SHORT_CACHE = "public, max-age=3600"
PROXY_PREFIXES = ("/v1", "/health", "/docs", "/openapi.json")


def cache_control_for(path: str) -> str:
    raw = urlparse(path).path
    lower = raw.lower()
    name = Path(lower).name
    if name.endswith(".html") or name in {"sw.js", "manifest.webmanifest"}:
        return NO_CACHE
    if "/assets/" in lower:
        return IMMUTABLE_ASSET
    return SHORT_CACHE


class AulosHandler(SimpleHTTPRequestHandler):
    proxy_host: str = "127.0.0.1"
    proxy_port: int = 5090

    def end_headers(self) -> None:
        self.send_header("Cache-Control", cache_control_for(self.path))
        super().end_headers()

    def _should_proxy(self) -> bool:
        path = urlparse(self.path).path
        return any(path == p or path.startswith(p + "/") for p in PROXY_PREFIXES)

    def _proxy(self) -> None:
        length = int(self.headers.get("Content-Length", "0") or "0")
        body = self.rfile.read(length) if length > 0 else None
        conn = http.client.HTTPConnection(self.proxy_host, self.proxy_port, timeout=60)
        headers = {
            key: value
            for key, value in self.headers.items()
            if key.lower() not in {"host", "connection", "content-length"}
        }
        try:
            conn.request(self.command, self.path, body=body, headers=headers)
            upstream = conn.getresponse()
            payload = upstream.read()
            self.send_response(upstream.status)
            for key, value in upstream.getheaders():
                if key.lower() in {"transfer-encoding", "connection", "content-length"}:
                    continue
                self.send_header(key, value)
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
        if self._should_proxy():
            return self._proxy()
        path_only = self.path.split("?", 1)[0].split("#", 1)[0]
        candidate = Path(self.directory) / path_only.lstrip("/")
        if path_only in {"/", ""} or (not candidate.exists() and "." not in Path(path_only).name):
            self.path = "/index.html"
        return super().do_GET()

    def do_HEAD(self) -> None:  # noqa: N802
        if self._should_proxy():
            return self._proxy()
        return super().do_HEAD()

    def do_POST(self) -> None:  # noqa: N802
        if self._should_proxy():
            return self._proxy()
        self.send_error(405, "Method Not Allowed")

    def do_OPTIONS(self) -> None:  # noqa: N802
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
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.is_dir():
        raise SystemExit(f"static root not found: {root}")

    AulosHandler.proxy_host = args.proxy_host
    AulosHandler.proxy_port = args.proxy_port
    handler = functools.partial(AulosHandler, directory=str(root))
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(
        f"Serving {root} on http://{args.host}:{args.port} "
        f"(proxy -> {args.proxy_host}:{args.proxy_port})",
        flush=True,
    )
    server.serve_forever()


if __name__ == "__main__":
    main()
