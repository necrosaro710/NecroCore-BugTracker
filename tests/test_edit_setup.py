"""End-to-end setup/edit/cancel/backup regression tests on disposable folder."""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent


def execute(tmp, answers):
    cmd = [sys.executable, str(tmp / 'tools' / 'setup.py')]
    result = subprocess.run(cmd, input=answers, text=True, capture_output=True, timeout=15)
    assert result.returncode == 0, result.stdout + '\n' + result.stderr
    return result.stdout


with tempfile.TemporaryDirectory(prefix='necro_setup_test_') as d:
    base = Path(d) / 'Package Release Folder'
    shutil.copytree(PKG / 'tools', base / 'tools', ignore=shutil.ignore_patterns('__pycache__'))
    (base / 'web').mkdir()
    config_path = base / 'web' / 'config.json'
    # Fresh install with all defaults; no absolute Windows-only dependencies.
    output = execute(base, '\n\n\n\n\n\n\n')
    data = json.loads(config_path.read_text(encoding='utf-8'))
    assert data['data_directory'] == 'data', data
    assert data['inbox_path'] == 'inbox/received.log'
    assert data['admin_login'] is False
    assert 'Full' not in output or 'folder' in output
    assert 'SETUP SAVED:' in output
    assert str(base / 'web' / 'data' / 'inbox' / 'received.log') in output
    first_bytes = config_path.read_bytes()
    # Choice 2 = keep settings, unchanged, no backup.
    output = execute(base, '2\n')
    assert 'unchanged' in output
    assert config_path.read_bytes() == first_bytes
    assert not list((base / 'web').glob('config.before_edit_*'))
    # Choice 3 = cancellation, unchanged.
    execute(base, '3\n')
    assert config_path.read_bytes() == first_bytes
    # Existing edit default selection; change only title and port, preserve unknown.
    data['a_future_setting'] = {'preserve': True}
    config_path.write_text(json.dumps(data), encoding='utf-8')
    output = execute(base, '\nTesties Testies\n\n8089\n\n\n\n\n')
    changed = json.loads(config_path.read_text(encoding='utf-8'))
    assert changed['server_name'] == 'Testies Testies', changed
    assert changed['port'] == 8089
    assert changed['data_directory'] == 'data'
    assert changed['a_future_setting'] == {'preserve': True}
    backups = list((base / 'web').glob('config.before_edit_*'))
    assert len(backups) == 1
    assert 'Testies Testies' in output
    # Data path change rejected: config still uses original storage path.
    new_path = str(Path(d) / 'other_folder')
    output = execute(base, '\n\n\n\n' + new_path + '\nn\n\n\n\n')
    changed = json.loads(config_path.read_text(encoding='utf-8'))
    assert changed['data_directory'] == 'data', changed
    assert 'Keeping your original reports folder' in output
    # Data path change explicitly accepted. The tool must not create or remove tickets.
    db_path = base / 'web' / 'data' / 'bugs.sqlite3'
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.write_bytes(b'dummy preserve test')
    output = execute(base, '\n\n\n\n' + new_path + '\ny\n\n\n\n')
    assert json.loads(config_path.read_text(encoding='utf-8'))['data_directory'] == new_path
    assert db_path.read_bytes() == b'dummy preserve test'
    assert not Path(new_path).exists()
    # Simulate already-configured protected login: changing name must retain hash.
    changed = json.loads(config_path.read_text(encoding='utf-8'))
    changed['admin_login'] = True
    changed['admin_username'] = 'existing_admin'
    changed['password_hash'] = 'pbkdf2_sha256$300000$salt$hash'
    config_path.write_text(json.dumps(changed), encoding='utf-8')
    output = execute(base, '\nSafe Realm\n\n\n\n\n\n\n\n\n')
    updated = json.loads(config_path.read_text(encoding='utf-8'))
    assert updated['admin_login'] is True
    assert updated['admin_username'] == 'existing_admin'
    assert updated['password_hash'] == changed['password_hash']
    assert 'SETUP SAVED' in output
    print('PASS setup: new install, edit, keep, cancel, backups, data safety, preserve admin credentials')
