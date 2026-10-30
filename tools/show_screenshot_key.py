"""Read the screenshot upload key on the dashboard server PC (keep it private)."""
import json
from pathlib import Path

root = Path(__file__).resolve().parent.parent
config_path = root / 'web' / 'config.json'
if not config_path.is_file():
    raise SystemExit('Run 01_Setup_Dashboard.cmd first; web/config.json is missing.')
config = json.loads(config_path.read_text(encoding='utf-8'))
storage = Path(config.get('data_directory') or 'data').expanduser()
if not storage.is_absolute():
    storage = root / 'web' / storage
keyfile = storage.resolve() / '.screenshot_upload_key'
if not keyfile.exists():
    raise SystemExit('Start v1.2 02_Start_Dashboard.cmd once to generate the upload key, then rerun this tool.')
print('\nScreenshot upload key (private):\n')
print(keyfile.read_text(encoding='ascii').strip())
print('\nCopy this value to the Screenshot Companion setup on your WoW CLIENT PC.')
print('Do NOT paste it into Discord, GitHub, or ChatGPT.')
