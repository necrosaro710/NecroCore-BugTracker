"""Web-only v1.2 updater, no game-core or ticket-data reset.

Installs server-side screenshot handling without touching client addon,
user settings, ticket database or inbox log. Creates dated source backups.
"""
from pathlib import Path
from datetime import datetime
import shutil
import sys

SOURCE = Path(__file__).resolve().parent.parent
FILES = ('web/dashboard.py', 'web/launch_dashboard.py', 'web/screenshot_uploads.py',
         'tools/show_screenshot_key.py', '07_Show_Server_Screenshot_Key.cmd')


def main():
    print('NecroCore Bug Tracker v1.2 — WEB ONLY update')
    print('Stop the existing dashboard first. Existing tickets and web/config.json will NOT be edited.')
    folder = input('Full path to your existing Community Edition folder: ').strip().strip('"')
    target = Path(folder).expanduser().resolve()
    if not folder or not (target/'web/dashboard.py').is_file() or not (target/'web/github_export.py').is_file():
        print('ERROR: Expected an extracted v1.1 Community Edition folder with web/github_export.py.')
        return 1
    if not all((SOURCE / f).is_file() for f in FILES):
        print('ERROR: Incomplete v1.2 source package. Extract the ZIP first.')
        return 1
    if SOURCE == target:
        print('ERROR: Select your existing installation, not the update folder.')
        return 1
    print('Existing:', target)
    if input('Update website code and create a dated backup? (Y/N): ').strip().lower() not in ('y','yes'):
        return 0
    backup = target / ('v1.2_dashboard_backup_' + datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    installed = []
    try:
        backup.mkdir()
        for rel in FILES:
            previous = target / rel
            if previous.is_file():
                saved = backup / rel
                saved.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(previous,saved)
        for rel in FILES:
            destination = target / rel
            destination.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(SOURCE / rel,destination)
            installed.append(rel)
    except OSError as e:
        print('ERROR:', e)
        for rel in reversed(installed):
            existing = backup / rel
            destination = target / rel
            if existing.is_file():
                shutil.copy2(existing,destination)
            else:
                destination.unlink(missing_ok=True)
        print('Original website files restored where possible. Backup at',backup)
        return 1
    print('SUCCESS: v1.2 website update installed.')
    print('Previous website files backed up to:', backup)
    print('Next: restart original 02_Start_Dashboard.cmd, then run the server key utility.')
    print('Then update the addon and set up the companion ON THE WOW CLIENT PC.')
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except (EOFError, KeyboardInterrupt):
        print('Cancelled.')
        sys.exit(1)
