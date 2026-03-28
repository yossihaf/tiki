"""
TikTok OAuth Helper
Run this to get your access token for the n8n workflow.

Usage:
  1. Fill in CLIENT_KEY and CLIENT_SECRET from your TikTok Developer app
  2. Run: python tiktok_oauth_helper.py
  3. Open the URL it prints in your browser
  4. After authorizing, you'll be redirected — copy the 'code' from the URL
  5. Paste it back into the terminal
  6. Save the access_token and refresh_token it gives you
"""

import http.server
import urllib.parse
import requests
import webbrowser
import threading

CLIENT_KEY = "YOUR_CLIENT_KEY"
CLIENT_SECRET = "YOUR_CLIENT_SECRET"
REDIRECT_URI = "http://localhost:3000/callback"
SCOPES = "user.info.basic,video.publish,video.upload"

auth_code = None

class CallbackHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)

        if "code" in params:
            auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h1>Got it! You can close this tab.</h1>")
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"<h1>Error: no code received</h1>")

    def log_message(self, format, *args):
        pass  # suppress logs


def get_auth_url():
    return (
        f"https://www.tiktok.com/v2/auth/authorize/"
        f"?client_key={CLIENT_KEY}"
        f"&scope={SCOPES}"
        f"&response_type=code"
        f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
    )


def exchange_code(code):
    resp = requests.post(
        "https://open.tiktokapis.com/v2/oauth/token/",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "client_key": CLIENT_KEY,
            "client_secret": CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI,
        },
    )
    return resp.json()


def main():
    if CLIENT_KEY == "YOUR_CLIENT_KEY":
        print("Edit this file and set CLIENT_KEY and CLIENT_SECRET first.")
        return

    auth_url = get_auth_url()
    print(f"\nOpening browser for authorization...\n")
    print(f"If it doesn't open, go to:\n{auth_url}\n")

    server = http.server.HTTPServer(("localhost", 3000), CallbackHandler)
    thread = threading.Thread(target=server.handle_request)
    thread.start()

    webbrowser.open(auth_url)
    thread.join(timeout=120)
    server.server_close()

    if auth_code:
        print(f"Authorization code received. Exchanging for token...\n")
        token_data = exchange_code(auth_code)

        if "access_token" in token_data:
            print(f"access_token:  {token_data['access_token']}")
            print(f"refresh_token: {token_data.get('refresh_token', 'N/A')}")
            print(f"expires_in:    {token_data.get('expires_in', 'N/A')} seconds")
            print(f"\nPaste the access_token into your n8n workflow.")
        else:
            print(f"Error: {token_data}")
    else:
        print("Timed out waiting for authorization.")


if __name__ == "__main__":
    main()
