"""Local HTTPS server for testing the Excel add-in on this machine.

Serves integrations/excel/src at https://localhost:3000 and forwards /api/* to a
local PIM API (default http://127.0.0.1:8092), so the add-in calls its own origin
exactly as it will in production. Uses the Office dev certificates
(npx office-addin-dev-certs install).

    python integrations/excel/dev_server.py [--api http://127.0.0.1:8092]
"""
import argparse
import http.server
import ssl
import urllib.error
import urllib.request
from functools import partial
from pathlib import Path

SRC = Path(__file__).parent / "src"
CERTS = Path.home() / ".office-addin-dev-certs"


class Handler(http.server.SimpleHTTPRequestHandler):
    api = "http://127.0.0.1:8092"

    def _proxy(self, method):
        n = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(n) if n else None
        req = urllib.request.Request(self.api + self.path[len("/api"):], data=body, method=method)
        for h in ("Content-Type", "X-API-Key", "Authorization", "X-Request-ID"):
            if self.headers.get(h):
                req.add_header(h, self.headers[h])
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                code, data, ctype = r.status, r.read(), r.headers.get("Content-Type", "application/json")
        except urllib.error.HTTPError as e:
            code, data, ctype = e.code, e.read(), e.headers.get("Content-Type", "application/json")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path.startswith("/api/"):
            return self._proxy("GET")
        return super().do_GET()

    def do_POST(self):
        if self.path.startswith("/api/"):
            return self._proxy("POST")
        self.send_error(405)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=3000)
    ap.add_argument("--api", default="http://127.0.0.1:8092")
    a = ap.parse_args()
    Handler.api = a.api.rstrip("/")
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", a.port), partial(Handler, directory=str(SRC)))
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(CERTS / "localhost.crt", CERTS / "localhost.key")
    httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)
    print(f"add-in at https://localhost:{a.port}/taskpane.html, /api -> {Handler.api}")
    httpd.serve_forever()


if __name__ == "__main__":
    main()
