"""NecroCore v1.2 private screenshot handoff; no image bytes transit the WoW chat bridge.

A trusted, explicitly configured companion polls requests associated with a verified
in-game character and sends at most one JPEG/PNG to each screenshot-requested ticket.
"""
import hmac
import os
import re
import secrets
import sqlite3
import struct
from pathlib import Path

MAX_IMAGE = 8 * 1024 * 1024
MAX_AGE_SECONDS = 2 * 86400
_ALLOWED_EXT = {"image/jpeg": ".jpg", "image/png": ".png"}


def private_key(data_dir):
    path = Path(data_dir) / '.screenshot_upload_key'
    try:
        return path.read_text(encoding='ascii').strip()
    except FileNotFoundError:
        pass
    key = secrets.token_urlsafe(36)
    try:
        fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w', encoding='ascii') as out:
            out.write(key + '\n')
    except FileExistsError:
        return path.read_text(encoding='ascii').strip()
    return key


def authorize(provided, expected):
    return bool(provided and expected) and hmac.compare_digest(str(provided), str(expected))


def image_type(payload):
    if len(payload) > MAX_IMAGE or len(payload) < 16:
        return None
    if payload.startswith(b'\x89PNG\r\n\x1a\n') and len(payload) >= 33:
        width, height = struct.unpack('>II', payload[16:24])
        if (payload[12:16] == b'IHDR' and 1 <= width <= 16384 and 1 <= height <= 16384
                and payload[-12:-8] == b'\x00\x00\x00\x00' and payload[-8:-4] == b'IEND'):
            return 'image/png'
    if payload[:3] == b'\xff\xd8\xff' and payload[-2:] == b'\xff\xd9':
        return 'image/jpeg'
    return None


def migrate(db):
    cols = {row[1] for row in db.execute('PRAGMA table_info(reports)')}
    if 'screenshot_epoch' not in cols:
        db.execute('ALTER TABLE reports ADD COLUMN screenshot_epoch INTEGER NOT NULL DEFAULT 0')
    db.execute('''CREATE TABLE IF NOT EXISTS screenshots (
        report_id INTEGER PRIMARY KEY,
        stored_file TEXT NOT NULL UNIQUE,
        bytes INTEGER NOT NULL,
        uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP)''')


def pending(db):
    return [dict(id=i, character=c, realm=r or '', captured_at=int(t)) for i,c,r,t in db.execute('''
        SELECT id,char,realm,screenshot_epoch FROM reports
        WHERE screenshot_epoch > 0 AND screenshot_epoch >= CAST(strftime('%s','now') AS INTEGER) - ?
        AND NOT EXISTS(SELECT 1 FROM screenshots s WHERE s.report_id=reports.id)
        ORDER BY screenshot_epoch DESC LIMIT 100''', (MAX_AGE_SECONDS,))]


def store(db, base, ident, character, epoch, content):
    """Write one screenshot for the requested ticket, retaining existing tickets and DB."""
    mimetype = image_type(content)
    if not mimetype:
        raise ValueError('Only JPEG or PNG screenshots up to 8 MiB are accepted')
    row = db.execute('SELECT char,screenshot_epoch FROM reports WHERE id=?', (ident,)).fetchone()
    if not row or row[1] == 0:
        raise ValueError('Ticket is not awaiting a screenshot')
    if row[0] != character or int(row[1]) != int(epoch):
        raise ValueError('Character or capture time does not match this ticket')
    if db.execute('SELECT 1 FROM screenshots WHERE report_id=?', (ident,)).fetchone():
        raise ValueError('Screenshot already attached to ticket')
    folder = Path(base) / 'attachments'
    folder.mkdir(parents=True, exist_ok=True)
    filename = secrets.token_hex(24) + _ALLOWED_EXT[mimetype]
    target = folder / filename
    try:
        with target.open('xb') as output:
            output.write(content)
        db.execute('INSERT INTO screenshots(report_id,stored_file,bytes) VALUES(?,?,?)',
                   (ident, filename, len(content)))
        db.commit()
    except Exception:
        target.unlink(missing_ok=True)
        raise
    return mimetype


def attachment(db, base, ident):
    row = db.execute('SELECT stored_file FROM screenshots WHERE report_id=?', (ident,)).fetchone()
    if not row:
        return None
    name = row[0]
    if not re.fullmatch(r'[0-9a-f]{48}\.(jpg|png)', name):
        return None
    path = Path(base) / 'attachments' / name
    if not path.is_file() or not path.resolve().is_relative_to((Path(base)/'attachments').resolve()):
        return None
    return path
