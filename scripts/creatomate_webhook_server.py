from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer

from creatomate_webhook_handler import handle_creatomate_webhook


class CreatomateWebhookRequestHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        if self.path != "/webhooks/creatomate":
            self.send_response(404)
            self.end_headers()
            return
        length = int(self.headers.get("Content-Length", "0"))
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            result = handle_creatomate_webhook(payload)
            body = json.dumps(result).encode("utf-8")
            self.send_response(200 if result.get("success") else 400)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except Exception as exc:
            body = json.dumps({"success": False, "error": str(exc)}).encode("utf-8")
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)


def run(port: int = 8080) -> None:
    HTTPServer(("0.0.0.0", port), CreatomateWebhookRequestHandler).serve_forever()


if __name__ == "__main__":
    run()
