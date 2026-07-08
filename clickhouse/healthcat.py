#!/usr/bin/env python3
"""Tiny HTTP server on :8080 that returns 200 for /api/health if clickhouse /ping responds."""
import http.server
import urllib.request
import threading
import time
import subprocess
import os

CLICKHOUSE_HOST = "127.0.0.1"
CLICKHOUSE_PORT = 8123
PROXY_PORT = 8080
PING_PATH = "/ping"
HEALTH_PATH = "/api/health"

class HealthHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == HEALTH_PATH:
            # Check clickhouse /ping
            try:
                url = f"http://{CLICKHOUSE_HOST}:{CLICKHOUSE_PORT}{PING_PATH}"
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
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Suppress logs

def wait_for_clickhouse():
    """Wait until clickhouse /ping responds."""
    for _ in range(60):
        try:
            url = f"http://{CLICKHOUSE_HOST}:{CLICKHOUSE_PORT}{PING_PATH}"
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=2) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(2)
    return False

if __name__ == "__main__":
    # Wait for clickhouse to start
    if not wait_for_clickhouse():
        print("Warning: clickhouse did not become ready, starting proxy anyway")

    # Start HTTP server
    server = http.server.HTTPServer(("0.0.0.0", PROXY_PORT), HealthHandler)
    print(f"Healthcat proxy listening on :{PROXY_PORT}")
    server.serve_forever()
