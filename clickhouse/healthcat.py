#!/usr/bin/env python3
"""HTTP proxy on :8123 that handles /api/health and proxies other requests to clickhouse on :8124."""
import http.server
import urllib.request
import urllib.error
import threading
import time
import os

CLICKHOUSE_HOST = "127.0.0.1"
CLICKHOUSE_PORT = 8124
PROXY_PORT = 8123
HEALTH_PATH = "/api/health"

class ProxyHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == HEALTH_PATH:
            # Check if clickhouse is alive
            try:
                url = f"http://{CLICKHOUSE_HOST}:{CLICKHOUSE_PORT}/ping"
                req = urllib.request.Request(url, method="GET")
                with urllib.request.urlopen(req, timeout=3) as resp:
                    if resp.status == 200:
                        self.send_response(200)
                        self.send_header("Content-Type", "text/plain")
                        self.end_headers()
                        self.wfile.write(b"OK")
                        return
            except Exception:
                pass
            self.send_response(503)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Service Unavailable")
        else:
            # Proxy to clickhouse
            try:
                url = f"http://{CLICKHOUSE_HOST}:{CLICKHOUSE_PORT}{self.path}"
                req = urllib.request.Request(url, method="GET")
                with urllib.request.urlopen(req, timeout=30) as resp:
                    self.send_response(resp.status)
                    for header, value in resp.getheaders():
                        if header.lower() not in ('transfer-encoding', 'connection'):
                            self.send_header(header, value)
                    if 'Content-Type' not in [h[0] for h in resp.getheaders()]:
                        self.send_header('Content-Type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(resp.read())
            except urllib.error.HTTPError as e:
                self.send_response(e.code)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(e.read())
            except Exception as e:
                self.send_response(502)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(f"Bad Gateway: {e}".encode())

    def do_POST(self):
        # Proxy POST to clickhouse
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else b""
            url = f"http://{CLICKHOUSE_HOST}:{CLICKHOUSE_PORT}{self.path}"
            req = urllib.request.Request(url, data=body, method="POST")
            req.add_header("Content-Type", self.headers.get("Content-Type", "application/octet-stream"))
            with urllib.request.urlopen(req, timeout=60) as resp:
                self.send_response(resp.status)
                for header, value in resp.getheaders():
                    if header.lower() not in ('transfer-encoding', 'connection'):
                        self.send_header(header, value)
                self.end_headers()
                self.wfile.write(resp.read())
        except Exception as e:
            self.send_response(502)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(f"Bad Gateway: {e}".encode())

    def log_message(self, format, *args):
        pass  # Suppress logs

if __name__ == "__main__":
    server = http.server.HTTPServer(("0.0.0.0", PROXY_PORT), ProxyHandler)
    print(f"Healthcat proxy listening on :{PROXY_PORT}")
    server.serve_forever()
