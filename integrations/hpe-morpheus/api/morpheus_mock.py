"""Mock HPE Morpheus API.

A stdlib ``http.server`` implementation that speaks the same wire protocol the
governed client uses against real Morpheus:

    GET  /health             -> 200 {"status": "ok"}
    POST /api/auth/token     -> {"accessToken": "...", "expiresIn": 3600}
    POST /api/vms            -> {"id": "vm-<seq>"}  (requires Authorization)

Every action is recorded in ``server.actions`` and offered to a webhook hook,
so tests can assert both sides of the governance flow.
"""

from __future__ import annotations

import argparse
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class MockMorpheusServer(ThreadingHTTPServer):
    def __init__(self, address, handler) -> None:
        super().__init__(address, handler)
        self.actions: list[dict] = []
        self.lock = threading.Lock()
        self.webhook = None
        self.vm_seq = 0

    def record(self, action: dict) -> None:
        with self.lock:
            self.actions.append(action)
            if self.webhook:
                self.webhook(action)


class _Handler(BaseHTTPRequestHandler):
    server: MockMorpheusServer

    def log_message(self, *args):  # silence request logging
        pass

    def _json(self, code: int, obj: dict) -> None:
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            return json.loads(raw or b"{}")
        except json.JSONDecodeError:
            return {}

    def do_GET(self):
        if self.path == "/health":
            self._json(200, {"status": "ok", "service": "morpheus-mock"})
            return
        self._json(404, {"error": "not found"})

    def do_POST(self):
        if self.path == "/api/auth/token":
            self._json(200, {"accessToken": "mock-token", "expiresIn": 3600})
            return
        if self.path == "/api/vms":
            auth = self.headers.get("Authorization", "")
            if not auth.startswith("Bearer "):
                self._json(401, {"error": "unauthorized"})
                return
            body = self._read_body()
            with self.server.lock:
                self.server.vm_seq += 1
                vm_id = f"vm-{1000 + self.server.vm_seq}"
            action = {"path": self.path, "body": body, "vm_id": vm_id}
            self.server.record(action)
            self._json(201, {"id": vm_id, "status": "provisioning", "spec": body})
            return
        self._json(404, {"error": "not found"})


def make_server(port: int = 0) -> MockMorpheusServer:
    return MockMorpheusServer(("127.0.0.1", port), _Handler)


def main() -> None:
    parser = argparse.ArgumentParser(description="Mock HPE Morpheus API")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8548)
    args = parser.parse_args()
    server = MockMorpheusServer((args.host, args.port), _Handler)
    print(f"Mock Morpheus listening on http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
