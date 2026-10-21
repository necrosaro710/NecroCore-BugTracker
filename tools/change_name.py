"""Rename the public dashboard without modifying tickets or other config."""
import json
from pathlib import Path
BASE = Path(__file__).resolve().parent.parent
config_path = BASE / 'web' / 'config.json'
if not config_path.is_file():
    raise SystemExit('No web/config.json found. Run 01_Setup_Dashboard.cmd first.')
config = json.loads(config_path.read_text(encoding='utf-8'))
old = config.get('server_name', 'NecroCore')
print('Existing dashboard name:', old)
print('Attribution stays: Powered by NecroCore Bug Tracker')
new_name = input('New server / dashboard name (2-48 characters; blank to cancel): ').strip()
if not new_name:
    print('Cancelled, no changes made.')
elif not (2 <= len(new_name) <= 48) or any(ord(c) < 32 for c in new_name):
    raise SystemExit('Invalid name. Must be 2-48 printable characters. No changes made.')
else:
    config_path.with_name('config.json.before_name_change.bak').write_bytes(config_path.read_bytes())
    config['server_name'] = new_name
    temp = config_path.with_name('config.json.tmp')
    temp.write_text(json.dumps(config, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    temp.replace(config_path)
    print('Updated display name to:', new_name)
    print('Restart 02_Start_Dashboard.cmd to apply the new name.')
