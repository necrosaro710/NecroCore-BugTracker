"""NecroCore multi-character, multi-PC LAN screenshot companion (local client only).

Polls the existing production /_screenshot/pending API, matches only a unique
local WoW screenshot to a unique pending ticket by timestamp, mirrors the picture
to the already-authenticated Windows SMB share using a character/ticket name,
then uploads it via the official ticket attachment API. Originals are untouched.
No server code, database or addon is modified by this program.
"""
import argparse
import getpass
import hashlib
import json
import os
import re
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "client_private_config.json"
STATUS = ROOT / "client_status.json"
LOCK = ROOT / ".client_running.lock"
STOP = ROOT / ".stop_requested"
DEFAULT_URL = "http://127.0.0.1:8088"
DEFAULT_SHARE = r"\\SERVER-IP\BugTrackerShots"
LOCAL_SERVER_HOME = Path(r"C:\BFA-HavenCore\NecroBugTracker")
MAX_IMAGE = 8 * 1024 * 1024
MAX_MATCH_DELTA = 20
POLL_SECONDS = 6
WOW_NAME = re.compile(r"^WoWScrnShot[_-].*\.(?:jpg|jpeg|png)$", re.I)


def safe_name(s):
    s = re.sub(r"[^A-Za-z0-9_-]", "_", str(s or "Unknown")).strip("._-")[:48]
    if s.upper() in {"CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "LPT1", "LPT2"}:
        s += "_"
    return s or "Unknown"


def read_config():
    if not CONFIG.is_file():
        raise RuntimeError("Not configured. Run 01_Setup_On_This_WoW_PC.cmd first.")
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    for k in ("dashboard_url", "screenshots", "share", "key"):
        if not config.get(k):
            raise RuntimeError("Missing configuration: " + k)
    return config


def api_json(url, key, path, data=None, extra_headers=None):
    headers = {"X-NecroScreenshot-Key": key, "User-Agent": "NecroBugMultiPC/68"}
    if extra_headers:
        headers.update(extra_headers)
    req = urllib.request.Request(url.rstrip("/") + path,
                                 data=data, method="POST" if data is not None else "GET",
                                 headers=headers)
    with urllib.request.urlopen(req, timeout=18 if data is not None else 7) as resp:
        return json.loads(resp.read(100000).decode("utf-8"))


def pending_requests(config):
    body = api_json(config["dashboard_url"], config["key"], "/_screenshot/pending")
    if not isinstance(body, dict) or not isinstance(body.get("pending"), list):
        raise ValueError("Dashboard did not return a pending screenshot list")
    return [r for r in body["pending"] if valid_ticket(r)]


def valid_ticket(r):
    try:
        return (isinstance(r, dict) and int(r["id"]) > 0 and
                1600000000 <= int(r["captured_at"]) <= int(time.time()) + 300 and
                bool(str(r["character"]).strip()))
    except (KeyError, TypeError, ValueError, OverflowError):
        return False


def local_images(folder):
    now = time.time()
    items = []
    for file in Path(folder).iterdir():
        if not file.is_file() or not WOW_NAME.fullmatch(file.name):
            continue
        try:
            stat = file.stat()
        except OSError:
            continue
        if 24 <= stat.st_size <= MAX_IMAGE and 2 <= now - stat.st_mtime <= 48 * 3600:
            items.append((file, stat.st_mtime, stat.st_size))
    return items


def unique_pairs(pending, images):
    """Skip ambiguity BOTH ways, even when it involves different characters/PCs."""
    relevant = [(int(r["id"]), int(r["captured_at"]), r) for r in pending]
    candidates = {}
    reverse = {}
    for ident, epoch, record in relevant:
        hits = [file for file, mtime, _ in images if abs(mtime - epoch) <= MAX_MATCH_DELTA]
        if len(hits) == 1:
            candidates[ident] = (record, hits[0])
            reverse.setdefault(hits[0], []).append(ident)
    return [(rec, file) for ident, (rec, file) in candidates.items()
            if len(reverse[file]) == 1 and
            sum(1 for _id, epoch, _rec in relevant if abs(file.stat().st_mtime-epoch) <= MAX_MATCH_DELTA) == 1]


def sha256_bytes(blob):
    return hashlib.sha256(blob).hexdigest()


def named_copy_path(config, item, source):
    stamp = datetime.fromtimestamp(int(item["captured_at"])).strftime("%Y-%m-%d_%H-%M-%S")
    name = "{}__{}__{}__Ticket-{}__{}{}".format(
        safe_name(item["character"]), safe_name(item.get("realm") or "Realm"),
        stamp, int(item["id"]), safe_name(socket.gethostname()),
        ".jpg" if source.suffix.lower() == ".jpeg" else source.suffix.lower())
    return Path(config["share"]) / name


def mirror_verified(config, item, source, blob):
    dest = named_copy_path(config, item, source)
    digest = sha256_bytes(blob)
    if dest.exists():
        if sha256_bytes(dest.read_bytes()) != digest:
            raise RuntimeError("Refusing to overwrite differing existing screenshot: " + str(dest))
        return dest
    created = False
    try:
        with dest.open("xb") as stream:
            created = True
            stream.write(blob)
            stream.flush()
            os.fsync(stream.fileno())
        if sha256_bytes(dest.read_bytes()) != digest:
            raise RuntimeError("Mirror integrity check failed: " + str(dest))
    except Exception:
        if created:
            try:
                dest.unlink()
            except OSError:
                pass
        raise
    return dest


def upload_ticket(config, item, source, blob):
    mime = "image/png" if source.suffix.lower() == ".png" else "image/jpeg"
    result = api_json(config["dashboard_url"], config["key"],
                      "/_screenshot/upload/" + str(int(item["id"])), data=blob,
                      extra_headers={
                          "Content-Type": mime,
                          "X-NecroScreenshot-Character": str(item["character"]),
                          "X-NecroScreenshot-Epoch": str(int(item["captured_at"])),
                      })
    if result.get("attached") is not True or int(result.get("ticket", 0)) != int(item["id"]):
        raise RuntimeError("Server did not confirm ticket attachment")
    return result


def write_status(state):
    try:
        old = json.loads(STATUS.read_text(encoding="utf-8")) if STATUS.is_file() else {}
        if not state.get("last_uploaded") and old.get("last_uploaded"):
            state["last_uploaded"] = old["last_uploaded"]
    except (OSError, ValueError):
        pass
    state["updated"] = datetime.now().astimezone().isoformat(timespec="seconds")
    temp = STATUS.with_suffix(".json.tmp")
    try:
        temp.write_text(json.dumps(state, indent=2), encoding="utf-8")
        temp.replace(STATUS)
    except OSError:
        pass


def process_once(config, show=True):
    state = {"last_check": datetime.now().astimezone().isoformat(timespec="seconds"),
             "ok": False, "pending": 0, "attached": 0, "ambiguous_or_missing": 0, "error": ""}
    try:
        reqs = pending_requests(config)
        state["pending"] = len(reqs)
        images = local_images(config["screenshots"])
        matches = unique_pairs(reqs, images)
        state["ambiguous_or_missing"] = len(reqs) - len(matches)
        for item, file in matches:
            before = file.stat()
            blob = file.read_bytes()
            after = file.stat()
            if (before.st_size != after.st_size or before.st_mtime_ns != after.st_mtime_ns
                    or not 24 <= len(blob) <= MAX_IMAGE):
                continue
            named = mirror_verified(config, item, file, blob)
            upload_ticket(config, item, file, blob)
            state["attached"] += 1
            state["last_uploaded"] = f"ticket {item['id']} ({item['character']}): {named.name}"
            if show:
                print("UPLOADED to ticket #{} and saved: {}".format(item["id"], named))
        state["ok"] = True
        if show:
            print("Checked: {} pending request(s), {} uploaded, {} unmatched/ambiguous.".format(
                  state["pending"], state["attached"], state["ambiguous_or_missing"]))
    except Exception as exc:
        state["error"] = str(exc)[:240]
        if show:
            print("CHECK FAILED (no originals deleted): " + state["error"])
    write_status(state)
    return state


def verify_share(share):
    share = Path(share)
    if not share.is_dir():
        raise RuntimeError("Screenshot network share not available: " + str(share))
    import secrets
    probe = share / ("_necro_probe_" + secrets.token_hex(6) + ".tmp")
    try:
        with probe.open("xb") as f:
            f.write(b"NecroCore screenshot share test\n")
        if probe.read_bytes() != b"NecroCore screenshot share test\n":
            raise RuntimeError("Failed to verify read-back from screenshot share")
    finally:
        try:
            probe.unlink(missing_ok=True)
        except OSError:
            pass


def ask(prompt, default=""):
    value = input("{}{}: ".format(prompt, " [" + default + "]" if default else "")).strip().strip('"')
    return value or default


def get_windows_clipboard_text():
    """Read Windows CF_UNICODETEXT without echoing typed contents in CMD."""
    if os.name != "nt":
        raise RuntimeError("Windows clipboard input is available only on Windows")
    import ctypes
    from ctypes import wintypes
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    user32.OpenClipboard.argtypes = [wintypes.HWND]
    user32.OpenClipboard.restype = wintypes.BOOL
    user32.GetClipboardData.argtypes = [wintypes.UINT]
    user32.GetClipboardData.restype = wintypes.HANDLE
    user32.CloseClipboard.argtypes = []
    user32.CloseClipboard.restype = wintypes.BOOL
    kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalUnlock.restype = wintypes.BOOL
    opened = False
    for _ in range(6):
        if user32.OpenClipboard(None):
            opened = True
            break
        time.sleep(0.1)
    if not opened:
        raise RuntimeError("Windows clipboard is busy; copy the key again and retry")
    try:
        handle = user32.GetClipboardData(13)
        if not handle:
            raise RuntimeError("Clipboard contains no text; copy the upload key first")
        pointer = kernel32.GlobalLock(handle)
        if not pointer:
            raise RuntimeError("Clipboard text is currently unavailable")
        try:
            return ctypes.wstring_at(pointer)
        finally:
            kernel32.GlobalUnlock(handle)
    finally:
        user32.CloseClipboard()


def obtain_private_key(server_home):
    path = server_home / ".screenshot_upload_key"
    if path.is_file():
        key = path.read_text(encoding="ascii").strip()
        if len(key) < 32:
            raise RuntimeError("Local server upload key is unexpectedly short; no changes made")
        print("Found the existing server upload key locally; no typing or pasting needed.")
        return key
    print("This PC is not the NecroCore server, so the key must be supplied privately.")
    print("Copy the upload key into the Windows clipboard, then press ENTER below.")
    choice = input("Press ENTER to use clipboard, or M to type the key manually: ").strip().lower()
    if choice == "m":
        key = getpass.getpass("Private screenshot upload key (hidden): ").strip()
    elif choice == "":
        key = get_windows_clipboard_text().strip()
    else:
        raise RuntimeError("Choose ENTER for clipboard or M for manual input")
    if len(key) < 32:
        raise RuntimeError("Key missing or too short; please copy the actual key and retry")
    return key


def setup():
    print("NECROCORE MULTI-PC SCREENSHOT CLIENT - SETUP ON THIS WOW PC")
    print("Your existing dashboard, database, reports, and screenshots are untouched.\n")
    server_home = LOCAL_SERVER_HOME
    server_key = server_home / ".screenshot_upload_key"
    local_server = server_key.is_file() and (server_home / "Screenshots").is_dir()
    default_folder = next((str(Path(p)) for p in
                           (r"E:\BFA-Client\Screenshots", r"D:\BFA-Client-Full\Screenshots",
                            r"C:\BFA-Client-Full\Screenshots") if Path(p).is_dir()), "")
    screenshots = Path(ask("WoW Screenshots directory", default_folder))
    if not screenshots.is_dir():
        raise RuntimeError("WoW Screenshots folder not found; enter the directory containing WoWScrnShot files")
    destination = str(server_home / "Screenshots") if local_server else DEFAULT_SHARE
    share = ask("Server screenshot destination", destination)
    if not (share.startswith("\\\\") or Path(share).is_dir()):
        raise RuntimeError("Destination must be an existing local folder or a Windows network share")
    url = ask("Dashboard LAN URL", DEFAULT_URL).rstrip("/")
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "http" or not parsed.netloc or parsed.path or parsed.query or parsed.fragment or "@" in parsed.netloc:
        raise RuntimeError("Enter the trusted-LAN http://IP:port dashboard URL")
    key = obtain_private_key(server_home)
    candidate = {"dashboard_url": url, "screenshots": str(screenshots.resolve()), "share": share, "key": key}
    print("Checking screenshot dashboard authentication...")
    reqs = pending_requests(candidate)
    print("Dashboard accepted key. {} screenshot request(s) pending.".format(len(reqs)))
    print("Checking destination write/read/remove permissions...")
    verify_share(share)
    print("Destination access verified.")
    if CONFIG.exists():
        print("Existing configuration detected. Keeping the old one unless setup completes.")
        backup = CONFIG.with_suffix(".json.previous")
        if backup.exists():
            raise RuntimeError("A previous config backup already exists; refusing to overwrite it")
        CONFIG.replace(backup)
    CONFIG.write_text(json.dumps(candidate, indent=2), encoding="utf-8")
    print("SETUP SUCCESS. All characters supported; no per-character setup needed.")
    print("Next run 05_Transfer_One_Pass_Visible.cmd to recover the pending screenshot.")


def acquire_lock():
    f = open(LOCK, "a+b")
    f.seek(0)
    f.write(b"0")
    f.flush()
    f.seek(0)
    try:
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        f.close()
        return None
    return f


def main(argv=None):
    p = argparse.ArgumentParser(description="NecroCore local screenshot-to-ticket transfer")
    g = p.add_mutually_exclusive_group(required=True)
    for opt in ("setup", "check", "once", "run", "stop"):
        g.add_argument("--" + opt, action="store_true")
    args = p.parse_args(argv)
    if args.stop:
        STOP.touch()
        print("Stop requested for this PC's screenshot client.")
        return 0
    try:
        if args.setup:
            setup()
            return 0
        config = read_config()
        if args.check:
            print("Screenshots:", config["screenshots"])
            print("Share:", config["share"])
            print("Dashboard:", config["dashboard_url"])
            print("Config key: stored privately; value NOT displayed")
            print("Source exists:", Path(config["screenshots"]).is_dir())
            print("Share available:", Path(config["share"]).is_dir())
            if STATUS.exists():
                print("Previous run:\n" + STATUS.read_text(encoding="utf-8"))
            print("Dashboard pending requests:", len(pending_requests(config)))
            return 0
        lock = acquire_lock()
        if lock is None:
            print("Screenshot client is already running; no second copy started.")
            return 0
        if STOP.exists():
            STOP.unlink()
        if args.once:
            state = process_once(config)
            return 0 if state["ok"] else 1
        while not STOP.exists():
            process_once(config, show=False)
            for _ in range(POLL_SECONDS * 2):
                if STOP.exists():
                    break
                time.sleep(0.5)
        STOP.unlink(missing_ok=True)
        return 0
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError, urllib.error.URLError) as exc:
        print("STOPPED SAFELY:", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
