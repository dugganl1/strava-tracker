import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

import requests

from config import (
    STRAVA_AUTH_URL,
    STRAVA_CLIENT_ID,
    STRAVA_CLIENT_SECRET,
    STRAVA_TOKEN_URL,
)


class AuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Extract authorization code from callback URL
        query_components = parse_qs(urlparse(self.path).query)
        code = query_components.get("code", [None])[0]

        if code:
            # Exchange authorization code for tokens
            token_response = requests.post(
                STRAVA_TOKEN_URL,
                data={
                    "client_id": STRAVA_CLIENT_ID,
                    "client_secret": STRAVA_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                },
            )

            if token_response.ok:
                tokens = token_response.json()
                # Save tokens to file
                with open(".strava_tokens.json", "w") as f:
                    import json

                    json.dump(tokens, f)

                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(
                    b"Authentication successful! You can close this window."
                )
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Authentication failed!")

        # Stop the server after handling the request
        self.server.server_running = False


def authenticate():
    # Construct authorization URL
    auth_params = {
        "client_id": STRAVA_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": "http://localhost:8000",
        "scope": "activity:read_all",
        "approval_prompt": "force",
    }

    auth_url = (
        f"{STRAVA_AUTH_URL}?{'&'.join(f'{k}={v}' for k, v in auth_params.items())}"
    )

    # Open browser for user authentication
    webbrowser.open(auth_url)

    # Start local server to receive callback
    server = HTTPServer(("localhost", 8000), AuthHandler)
    server.server_running = True

    print("Waiting for Strava authentication...")
    while server.server_running:
        server.handle_request()


if __name__ == "__main__":
    authenticate()
