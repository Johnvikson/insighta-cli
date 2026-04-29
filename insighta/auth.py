import json
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

CREDENTIALS_PATH = Path.home() / ".insighta" / "credentials.json"
CALLBACK_PORT = 8888
API_BASE = "https://profile-api-zeta.vercel.app"


def save_credentials(data: dict) -> None:
    CREDENTIALS_PATH.parent.mkdir(parents=True, exist_ok=True)
    CREDENTIALS_PATH.write_text(json.dumps(data, indent=2))


def load_credentials() -> dict | None:
    if not CREDENTIALS_PATH.exists():
        return None
    try:
        return json.loads(CREDENTIALS_PATH.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def delete_credentials() -> None:
    if CREDENTIALS_PATH.exists():
        CREDENTIALS_PATH.unlink()


def login_flow() -> dict:
    """
    Opens the GitHub OAuth page in the browser and starts a local HTTP server
    on port 8888 to catch the callback with access_token and refresh_token.
    Returns {"access_token": str, "refresh_token": str}.
    Raises RuntimeError on timeout or missing tokens.
    """
    received: dict = {}

    class _Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urlparse(self.path)
            if not parsed.path.startswith("/callback"):
                self.send_response(404)
                self.end_headers()
                return

            params = parse_qs(parsed.query)
            received["access_token"] = params.get("access_token", [None])[0]
            received["refresh_token"] = params.get("refresh_token", [None])[0]

            body = (
                b"<html><body style='font-family:sans-serif;text-align:center;"
                b"padding:60px'><h2>Logged in!</h2>"
                b"<p>You can close this tab and return to your terminal.</p>"
                b"</body></html>"
            )
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, fmt, *args):  # suppress access logs
            pass

    server = HTTPServer(("localhost", CALLBACK_PORT), _Handler)
    server.timeout = 120  # 2-minute window

    webbrowser.open(f"{API_BASE}/auth/github")

    server.handle_request()
    server.server_close()

    if not received.get("access_token") or not received.get("refresh_token"):
        raise RuntimeError("Login timed out or tokens were not received. Please try again.")

    return received
