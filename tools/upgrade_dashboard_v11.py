"""Backed-up, web-only upgrade. Never edits worldserver, addon, reports, or config."""
import shutil
import sys
from datetime import datetime
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent.parent
FILES = (
    'web/dashboard.py',
    'web/launch_dashboard.py',
    'web/github_export.py',
    'web/necrocore_assets/necrocore.js',
    'tools/setup.py',
)


def main():
    print('NecroCore Bug Tracker v1.1 — existing-dashboard update')
    print('Stop the old dashboard first (Ctrl+C).')
    print('No ticket, configuration, MySQL, addon or worldserver files will be changed.')
    raw = input('Full path to your existing Community Edition folder: ').strip().strip('"')
    target = Path(raw).expanduser().resolve()
    if not raw or not (target/'web/dashboard.py').is_file() or not (target/'web/launch_dashboard.py').is_file():
        print('ERROR: Enter the extracted Community Edition folder containing the web and tools folders.')
        return 1
    if target == PACKAGE or PACKAGE == target.parent:
        print('ERROR: Source and destination must be different extracted folders.')
        return 1
    for name in FILES:
        if not (PACKAGE/name).is_file():
            print('ERROR: Incomplete v1.1 package (missing {}).'.format(name))
            return 1
    print('Existing website:', target)
    print('New website code:', PACKAGE)
    if input('Install v1.1 web files into this folder? (Y/N): ').strip().lower() not in ('y','yes'):
        print('Cancelled. No files changed.')
        return 0
    backup = target/('v1.1_dashboard_backup_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    backed_up=[]; installed=[]
    try:
        backup.mkdir()
        for name in FILES:
            dest = target/name
            if dest.is_file():
                saved = backup/name
                saved.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(dest,saved)
                backed_up.append(name)
        for name in FILES:
            dest=target/name
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(PACKAGE/name,dest)
            installed.append(name)
    except OSError as err:
        print('ERROR: Update interrupted:', err)
        for name in reversed(installed):
            try:
                saved=backup/name
                if saved.is_file():shutil.copy2(saved,target/name)
                else:(target/name).unlink(missing_ok=True)
            except OSError as err2:print('Restoration problem for {}: {}'.format(name,err2))
        print('Please inspect the backup folder:', backup)
        return 1
    print('SUCCESS: v1.1 dashboard update applied.')
    print('Previous website code saved in:', backup)
    print('Your config, reports database and WoW core were NOT changed.')
    print('Restart your ORIGINAL 02_Start_Dashboard.cmd; for a default GitHub repo, rerun original 01_Setup_Dashboard.cmd.')
    return 0


if __name__=='__main__':
    try:sys.exit(main())
    except (EOFError,KeyboardInterrupt):
        print('\nCancelled. No update confirmed.')
        sys.exit(1)
