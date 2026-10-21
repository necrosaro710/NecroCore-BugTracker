"""Safe, editable dashboard configuration. Python 3.9+, standard library."""
import getpass
import hashlib
import json
import secrets
import shutil
import sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
WEB = BASE / 'web'
CFG = WEB / 'config.json'


def ask(label, default):
    response = input('{} [{}]: '.format(label, default)).strip()
    return response if response else str(default)


def yes_no(label, default=False):
    value = 'Y' if default else 'N'
    while True:
        response = ask(label + ' (Y/N)', value).lower()
        if response in ('y', 'yes'):
            return True
        if response in ('n', 'no'):
            return False
        print('Please enter Y or N.')


def full_path(value, anchor):
    result = Path(value).expanduser()
    if not result.is_absolute():
        result = anchor / result
    return result.resolve()


def show_current(cfg):
    data = full_path(cfg.get('data_directory') or '.', WEB)
    inbox = full_path(cfg.get('inbox_path') or 'inbox/received.log', data)
    print('  Dashboard title : {}'.format(cfg.get('server_name', 'NecroCore')))
    print('  Who can access  : {}'.format('Trusted local network' if cfg.get('bind_address') == '0.0.0.0' else 'This computer only'))
    print('  Web port        : {}'.format(cfg.get('port', 8088)))
    print('  Saved reports   : {}'.format(data))
    print('  Incoming reports: {}'.format(inbox))
    print('  Admin login     : {}'.format('Enabled' if cfg.get('admin_login') else 'Disabled'))


def password_hash():
    while True:
        one = getpass.getpass('New administrator password (12 or more characters): ')
        two = getpass.getpass('Repeat administrator password: ')
        if one == two and len(one) >= 12:
            break
        print('Passwords must match and be at least 12 characters. Try again.')
    rounds = 300000
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac('sha256', one.encode('utf-8'), salt, rounds)
    return 'pbkdf2_sha256${}${}${}'.format(rounds, salt.hex(), digest.hex())


def main():
    print('\nNECROCORE BUG TRACKER - Community Dashboard Setup (RC1.6)')
    print('This changes only the web dashboard. It does NOT touch MySQL or the WoW server.\n')
    existing = {}
    editing = CFG.exists()
    if editing:
        try:
            existing = json.loads(CFG.read_text(encoding='utf-8'))
            if not isinstance(existing, dict):
                raise ValueError('Expected a JSON configuration object')
        except (OSError, ValueError) as err:
            print('ERROR: Cannot read existing configuration: {}'.format(err))
            print('No changes were made. Back up or repair web/config.json first.')
            return 1
        print('Your existing dashboard configuration was found:')
        show_current(existing)
        print('\n1 = Change settings (tickets will be kept)')
        print('2 = Keep settings as they are')
        print('3 = Cancel setup')
        while True:
            selection = ask('Choose an option', '1')
            if selection in ('1', '2', '3'):
                break
            print('Please choose 1, 2, or 3.')
        if selection != '1':
            print('Existing configuration unchanged.')
            return 0
        print('\nEdit settings. Press Enter to keep the value in [brackets].')
    else:
        print('First-time setup. Press Enter to accept any [default].')

    defaults = dict(server_name='NecroCore', bind_address='127.0.0.1', port=8088,
                    data_directory='data', inbox_path='inbox/received.log',
                    admin_login=False, admin_username='admin', password_hash='')
    cfg = dict(defaults)
    cfg.update(existing)  # Retain any future/extra config fields.

    while True:
        display_name = ask('Your server name (shown at the top of the website)', cfg['server_name'])
        if 2 <= len(display_name) <= 48 and all(ord(char) >= 32 for char in display_name):
            cfg['server_name'] = display_name
            break
        print('Please use 2-48 printable characters.')
    print('\nWhere will people open the dashboard?')
    print('  1 = Only on this computer (recommended / safest)')
    print('  2 = Other computers on your trusted home/local network')
    access_default = '2' if cfg.get('bind_address') == '0.0.0.0' else '1'
    while True:
        access = ask('Access choice', access_default)
        if access in ('1', '2'):
            break
        print('Please choose 1 or 2.')
    cfg['bind_address'] = '0.0.0.0' if access == '2' else '127.0.0.1'
    if access == '2':
        print('WARNING: Without admin login, anyone who can reach this dashboard')
        print('can edit and DELETE reports. Do NOT expose this port to the Internet.')

    while True:
        try:
            port = int(ask('Website port (usually keep 8088)', cfg['port']))
            if 1024 <= port <= 65535:
                cfg['port'] = port
                break
        except ValueError:
            pass
        print('Please use a port number from 1024 through 65535.')

    old_data = cfg.get('data_directory') or '.'
    print('\nWhere should your reports and ticket database be saved?')
    print('  This is the folder containing bugs.sqlite3 and incoming reports.')
    print('  For easy upgrades, use a FULL folder path outside this ZIP folder.')
    print('  Example: C:\\MyWoWServer\\NecroBugTracker')
    print('  The default is a data folder beside the website files.')
    data = ask('Reports storage folder', old_data)
    resolved_data = full_path(data, WEB)
    print('  Reports will be stored in: {}'.format(resolved_data))
    if editing and resolved_data != full_path(old_data, WEB):
        print('IMPORTANT: Changing this folder does NOT move your old tickets.')
        print('Your previous ticket files will remain in the old folder.')
        if not yes_no('Use the new folder anyway', False):
            print('Keeping your original reports folder.')
            data = old_data
            resolved_data = full_path(data, WEB)
    cfg['data_directory'] = data

    print('\nThe WoW server sends new tickets into one incoming-report log file.')
    print('Usually press Enter to keep: inbox/received.log')
    print('Your C++ bridge must write to exactly the same file.')
    cfg['inbox_path'] = ask('Incoming report log file', cfg.get('inbox_path') or 'inbox/received.log')

    previous_login = bool(existing.get('admin_login', False))
    enable_login = yes_no('Require a password to use the website', bool(cfg.get('admin_login')))
    cfg['admin_login'] = enable_login
    if enable_login:
        cfg['admin_username'] = ask('Administrator username', cfg.get('admin_username') or 'admin')
        if previous_login and existing.get('password_hash'):
            if yes_no('Change the current administrator password', False):
                cfg['password_hash'] = password_hash()
            else:
                cfg['password_hash'] = existing['password_hash']
        else:
            cfg['password_hash'] = password_hash()
    else:
        if previous_login and not yes_no('Turn off the existing password protection', False):
            print('Cancelled. Your original configuration is unchanged.')
            return 0
        # Do not retain a reusable secret hash when login is disabled.
        cfg['password_hash'] = ''

    print('\nSETUP SUMMARY')
    show_current(cfg)
    print('  Credit line     : Powered by NecroCore Bug Tracker')
    if not yes_no('Save these dashboard settings', True):
        print('Cancelled. Original configuration left unchanged.')
        return 0
    try:
        WEB.mkdir(parents=True, exist_ok=True)
        if editing:
            backup = WEB / ('config.before_edit_{}.json'.format(datetime.now().strftime('%Y%m%d_%H%M%S_%f')))
            shutil.copy2(CFG, backup)
            print('Your old settings were backed up to: {}'.format(backup))
        pending = WEB / 'config.json.tmp'
        pending.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        pending.replace(CFG)
        (BASE / 'python_path.txt').write_text(sys.executable, encoding='utf-8')
    except OSError as err:
        print('ERROR saving config: {}'.format(err))
        return 1
    print('\nSETUP SAVED: {}'.format(CFG))
    print('Restart 02_Start_Dashboard.cmd to apply changes.')
    inbox = full_path(cfg['inbox_path'], full_path(cfg['data_directory'], WEB))
    print('\nIMPORTANT FOR THE WORLD SERVER:')
    print('Set NECROBUG_INBOX to this exact full path when starting worldserver:')
    print('  set "NECROBUG_INBOX={}"'.format(inbox))
    print('See docs/SERVER_INTEGRATION.md for instructions.')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (EOFError, KeyboardInterrupt):
        print('\nSetup cancelled. No configuration changes were saved.')
        sys.exit(1)
