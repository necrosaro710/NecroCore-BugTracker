"""Client PC screenshot companion, Python 3.9+ stdlib; no background service.

Config file lives next to script. A screenshot is only uploaded when a matching
in-game report requested one; no other screenshots leave the client PC.
"""
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

CONFIG = Path(__file__).with_name('companion_config.json')
MAX_BYTES = 8 * 1024 * 1024
MAX_DELTA = 30


def request_json(url, key):
    req = urllib.request.Request(url.rstrip('/') + '/_screenshot/pending',
        headers={'X-NecroScreenshot-Key': key, 'User-Agent': 'NecroBugScreenshot/1.2'})
    with urllib.request.urlopen(req, timeout=7) as res:
        return json.loads(res.read(100000).decode('utf-8'))


def choose_match(records, files, character, realm):
    """Never auto-attach if multiple files/tickets plausibly match one another."""
    matching = [x for x in records if x.get('character', '').casefold() == character.casefold()
                and (not realm or x.get('realm', '').casefold() == realm.casefold())]
    candidates = []
    for item in matching:
        t = int(item['captured_at'])
        possibilities = [(abs(stat.st_mtime - t), file) for file, stat in files
                         if abs(stat.st_mtime - t) <= MAX_DELTA]
        possibilities.sort(key=lambda x: x[0])
        if len(possibilities) != 1:
            continue
        file = possibilities[0][1]
        overlaps = sum(1 for other in matching if abs(int(other['captured_at']) - file.stat().st_mtime) <= MAX_DELTA)
        if overlaps == 1:
            candidates.append((item, file))
    return candidates


def image_files(folder):
    result = []
    now = time.time()
    for file in Path(folder).iterdir():
        if not file.is_file() or file.suffix.lower() not in ('.jpg', '.jpeg', '.png'):
            continue
        try:
            stat = file.stat()
        except OSError:
            continue
        if (0 < stat.st_size <= MAX_BYTES and 0 <= now-stat.st_mtime <= 2*86400
                and now-stat.st_mtime >= 2):
            result.append((file, stat))
    return result


def upload(url, key, item, file, character):
    # file may change while screenshot is still being written: recheck after open.
    content = file.read_bytes()
    if len(content) > MAX_BYTES or not content:
        raise ValueError('Image too large or empty')
    mimetype = 'image/png' if file.suffix.lower() == '.png' else 'image/jpeg'
    req = urllib.request.Request(
        url.rstrip('/') + '/_screenshot/upload/' + str(int(item['id'])),
        data=content, method='POST', headers={
            'Content-Type': mimetype,
            'X-NecroScreenshot-Key': key,
            'X-NecroScreenshot-Character': character,
            'X-NecroScreenshot-Epoch': str(int(item['captured_at'])),
            'User-Agent': 'NecroBugScreenshot/1.2',
        })
    with urllib.request.urlopen(req, timeout=25) as res:
        return json.loads(res.read(10000).decode('utf-8'))


def configure():
    print('NecroCore Screenshot Companion — first-time setup (CLIENT PC)')
    print('For trusted LAN use only. Never port-forward the dashboard.')
    url = input('Dashboard URL (e.g. http://192.168.50.82:8088): ').strip().rstrip('/')
    if not url.startswith('http://') or '/' in url[7:] or '@' in url:
        raise ValueError('Enter the bare http://host:port URL from your trusted LAN')
    screenshots = Path(input('WoW Screenshots folder (full path): ').strip().strip('"'))
    if not screenshots.is_dir():
        raise ValueError('Screenshot folder not found. Start WoW and locate its Screenshots directory.')
    character = input('WoW character name (exact name): ').strip()
    realm = input('WoW realm name (optional, Enter to skip): ').strip()
    if not character or len(character) > 60:
        raise ValueError('Character name required')
    key = input('Screenshot upload key displayed on dashboard server PC: ').strip()
    if len(key) < 32:
        raise ValueError('Upload key missing/too short')
    config = dict(dashboard_url=url, folder=str(screenshots.resolve()),
                  character=character, realm=realm, key=key)
    # Warning: this file is private; do not share or upload to GitHub.
    CONFIG.write_text(json.dumps(config, indent=2), encoding='utf-8')
    print('Saved local configuration. Do NOT share companion_config.json.')
    return config


def main():
    try:
        config = json.loads(CONFIG.read_text(encoding='utf-8')) if CONFIG.exists() else configure()
        print('Monitoring:', config['folder'])
        print('Character:', config['character'], '| Realm:', config.get('realm') or '(any)')
        print('Press Ctrl+C to stop. No screenshots are uploaded without an explicit in-game request.')
        seen = set()
        while True:
            try:
                pending = request_json(config['dashboard_url'], config['key'])['pending']
                files = [(f,s) for f,s in image_files(config['folder']) if str(f) not in seen]
                for item, file in choose_match(pending, files, config['character'], config.get('realm','')):
                    result = upload(config['dashboard_url'], config['key'], item, file, config['character'])
                    seen.add(str(file))
                    print('Uploaded', file.name, 'to NecroCore ticket #' + str(item['id']),
                          'at', time.strftime('%H:%M:%S'))
            except (urllib.error.URLError, TimeoutError, OSError, ValueError, KeyError, json.JSONDecodeError) as e:
                print('Dashboard offline, upload pending, or retry required:', str(e)[:160])
            time.sleep(6)
    except KeyboardInterrupt:
        print('\nScreenshot companion stopped.')
    except (ValueError, OSError) as e:
        print('Setup error:', e)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
