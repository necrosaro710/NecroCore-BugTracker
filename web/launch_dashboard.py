"""Portable NecroCore Bug Tracker web launcher. Python 3.9+, standard library only."""
import base64
import hashlib
import hmac
import html
import json
import os
import secrets
import sys
import threading
import time
from http.cookies import SimpleCookie
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import dashboard

PACKAGE = Path(__file__).resolve().parent
CONFIG_PATH = PACKAGE / 'config.json'


def load_config():
    if not CONFIG_PATH.exists():
        raise SystemExit('Missing web/config.json. Run 01_Setup_Dashboard.cmd first.')
    cfg = json.loads(CONFIG_PATH.read_text(encoding='utf-8'))
    bind = str(cfg.get('bind_address', '127.0.0.1'))
    if bind not in ('127.0.0.1', '0.0.0.0'):
        raise SystemExit('bind_address must be 127.0.0.1 or 0.0.0.0 (LAN).')
    port = int(cfg.get('port', 8088))
    if not 1024 <= port <= 65535:
        raise SystemExit('port must be 1024-65535.')
    if cfg.get('admin_login', False) and not cfg.get('password_hash'):
        raise SystemExit('Admin login is enabled but no password is configured.')
    if not cfg.get('admin_login', False) and bind == '0.0.0.0':
        print('WARNING: Anyone who can reach this port can view/change/delete tickets.')
        print('For trusted LAN only; do not forward this port to the internet.')
    return cfg, bind, port


CONFIG, BIND, PORT = load_config()
DATA_DIR = Path(CONFIG.get('data_directory') or '.').expanduser()
if not DATA_DIR.is_absolute():
    DATA_DIR = PACKAGE / DATA_DIR
DATA_DIR = DATA_DIR.resolve()
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG = Path(CONFIG.get('inbox_path') or 'inbox/received.log').expanduser()
if not LOG.is_absolute():
    LOG = DATA_DIR / LOG
LOG.parent.mkdir(parents=True, exist_ok=True)
dashboard.BASE = DATA_DIR
dashboard.DB = DATA_DIR / 'bugs.sqlite3'
dashboard.LOG = LOG
dashboard.ASSETS = PACKAGE / 'necrocore_assets'
# Configured name is used only for customer-facing UI. The footer's
# "Powered by NecroCore Bug Tracker" credit is NOT a configurable field.
SITE_NAME = str(CONFIG.get('server_name', 'NecroCore')).strip()[:48] or 'NecroCore'
dashboard.BRAND_NAME = SITE_NAME

# The official project URL is the default. An optional, valid config override
# remains supported for mirrors, but blank/older configs still link to the official repo.
def validated_repository_link(value):
    value = str(value or '').strip()
    if not value:
        return ''
    try:
        info = urlsplit(value)
    except ValueError:
        return ''
    parts = [p for p in info.path.strip('/').split('/') if p]
    if (info.scheme != 'https' or info.hostname not in ('github.com', 'www.github.com')
            or info.port not in (None, 443) or info.username or info.password
            or len(parts) != 2 or info.query or info.fragment):
        return ''
    return value

dashboard.ATTRIBUTION_URL = validated_repository_link(CONFIG.get('attribution_repo_url')) or dashboard.ATTRIBUTION_URL

LOGIN_ENABLED = bool(CONFIG.get('admin_login', False))
USERNAME = str(CONFIG.get('admin_username', 'admin'))
SECRET_HASH = str(CONFIG.get('password_hash', ''))
SESSION_LIFETIME = 12 * 3600
SESSIONS = {}
FAILURES = {}
LOCK = threading.Lock()


def valid_password(password):
    try:
        kind, rounds, salt_hex, hash_hex = SECRET_HASH.split('$', 3)
        if kind != 'pbkdf2_sha256':
            return False
        derived = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt_hex), int(rounds))
        return hmac.compare_digest(derived, bytes.fromhex(hash_hex))
    except (ValueError, TypeError):
        return False


def login_html(message=''):
    warning = f'<p style="color:#ee9090">{dashboard.esc(message)}</p>' if message else ''
    return ('''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
      <title>' + dashboard.esc(SITE_NAME) + ' · Login</title><style>body{background:#080d0b;color:#e6f3e9;font-family:system-ui;display:grid;place-items:center;min-height:90vh}
      main{background:#131d18;border:1px solid #31583a;border-radius:16px;padding:35px;max-width:380px;width:90%}h1{color:#6fea8c}
      label{display:block;margin:16px 0 5px}input{box-sizing:border-box;width:100%;background:#08100b;color:white;padding:12px;border-radius:8px;border:1px solid #49654f}
      button{background:#43c768;border:0;border-radius:8px;padding:12px 22px;margin-top:20px;cursor:pointer;font-weight:bold;width:100%}</style>
      <main><h1>''' + dashboard.esc(SITE_NAME) + '''</h1><p>Bug Tracker · Administrator</p>''' + warning + '''<form method="post" action="/login">
      <label>Username</label><input name="username" autocomplete="username" required maxlength="60">
      <label>Password</label><input type="password" name="password" autocomplete="current-password" required maxlength="200">
      <button type="submit">Sign in</button></form><p style="font-size:11px;color:#769e88;margin-top:22px">''' + dashboard.footer_credit() + '''</p></main></html>''')


class App(dashboard.App):
    def authorized(self):
        if not LOGIN_ENABLED:
            return True
        cookie = SimpleCookie()
        try:
            cookie.load(self.headers.get('Cookie', ''))
            token = cookie['NecroBugSession'].value if 'NecroBugSession' in cookie else ''
        except Exception:
            return False
        if not token:
            return False
        with LOCK:
            expiration = SESSIONS.get(token, 0)
            if expiration <= time.time():
                SESSIONS.pop(token, None)
                return False
        return True

    def do_GET(self):
        path = urlsplit(self.path).path
        if LOGIN_ENABLED and path == '/login':
            return self.respond(login_html())
        if LOGIN_ENABLED and path not in dashboard.STATIC_ASSETS and not self.authorized():
            self.send_response(303)
            self.send_header('Location', '/login')
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            return
        return super().do_GET()

    def do_POST(self):
        if LOGIN_ENABLED and urlsplit(self.path).path == '/login':
            length = int(self.headers.get('Content-Length', 0))
            if length <= 0 or length > 4096:
                return self.respond('Invalid login', 400)
            data = parse_qs(self.rfile.read(length).decode('utf-8', errors='replace'))
            username = data.get('username', [''])[0]
            passwd = data.get('password', [''])[0]
            ip = self.client_address[0]
            now = time.time()
            with LOCK:
                recent = [t for t in FAILURES.get(ip, []) if now - t < 300]
                FAILURES[ip] = recent
                blocked = len(recent) >= 8
            if blocked or not hmac.compare_digest(username.encode("utf-8"), USERNAME.encode("utf-8")) or not valid_password(passwd):
                with LOCK:
                    FAILURES.setdefault(ip, []).append(now)
                return self.respond(login_html('Incorrect credentials or too many attempts.'))
            token = secrets.token_urlsafe(32)
            with LOCK:
                SESSIONS[token] = now + SESSION_LIFETIME
                FAILURES.pop(ip, None)
            self.send_response(303)
            self.send_header('Location', '/')
            self.send_header('Set-Cookie', f'NecroBugSession={token}; Path=/; HttpOnly; SameSite=Strict; Max-Age={SESSION_LIFETIME}')
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            return
        if not self.authorized():
            return self.respond('Access denied', 403)
        return super().do_POST()

    def log_message(self, fmt, *args):
        try:
            super().log_message(fmt, *args)
        except (BrokenPipeError, ConnectionError):
            pass

    def handle(self):
        try:
            super().handle()
        except (ConnectionAbortedError, BrokenPipeError, ConnectionResetError):
            # Browsers can cancel an in-flight page request during refresh/close.
            pass


def main():
    dashboard.init()
    dashboard.ingest()
    threading.Thread(target=dashboard.loop, daemon=True).start()
    print(f'{SITE_NAME} Bug Tracker at http://127.0.0.1:{PORT}/')
    if BIND == '0.0.0.0':
        print(f'LAN access: http://<SERVER-IP>:{PORT}/  (replace SERVER-IP with your server LAN IP)')
    print('Admin login:', 'ON' if LOGIN_ENABLED else 'OFF (trusted network only)')
    try:
        ThreadingHTTPServer((BIND, PORT), App).serve_forever(poll_interval=0.5)
    except KeyboardInterrupt:
        print('\nDashboard stopped.')


if __name__ == '__main__':
    main()
