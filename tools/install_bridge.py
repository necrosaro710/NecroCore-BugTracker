"""Conservative BFA-HavenCore bridge installer; no build performed."""
import argparse
import datetime
import shutil
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description='Install source bridge into compatible BfA core')
    parser.add_argument('--core', help='Core source root (contains src/server/game/Handlers)')
    args = parser.parse_args()
    core = Path(args.core.strip('"')) if args.core else Path(input('Full core source directory: ').strip().strip('"'))
    handlers = core / 'src/server/game/Handlers'
    chat = handlers / 'ChatHandler.cpp'
    target = handlers / 'necro_bug_addon_bridge.cpp'
    if not chat.is_file():
        raise SystemExit('ERROR: ChatHandler.cpp not found; source root incorrect or incompatible. No changes made.')
    original = chat.read_bytes()
    if b'NECROBUG' in original or b'NecroBugHandleAddon' in original:
        raise SystemExit('EXISTING BRIDGE DETECTED. Do not overwrite/duplicate. Check README for manual integration.')
    if target.exists():
        raise SystemExit('A bridge file already exists; please inspect it first. No changes made.')
    text = original.decode('utf-8-sig', errors='strict')
    normalized = text.replace('\r\n', '\n')
    marker = '    // Disabled addon channel?\n'
    if normalized.count(marker) != 1:
        raise SystemExit('Incompatible ChatHandler.cpp: expected addon-channel anchor not unique. No changes made.')
    idx = normalized.index(marker)
    window = normalized[idx:idx+700]
    arm = '    switch (type)\n'
    if window.count(arm) != 1:
        raise SystemExit('Incompatible addon handler layout. Manual integration required; no changes made.')
    if '#include "Player.h"' not in normalized:
        raise SystemExit('ChatHandler.cpp lacks expected Player.h include. Manual integration required.')
    insert = '''    // NecroBugTracker: private addon message; not forwarded as ordinary chat.
    if (prefix == "NECROBUG")
    {
        NecroBugHandleAddon(sender, text);
        return;
    }

'''
    replacement = window.replace(arm, insert+arm, 1)
    result = normalized[:idx] + replacement + normalized[idx+len(window):]
    inc = '#include "Player.h"\n'
    result = result.replace(inc, inc + '\n// NecroCore Bug Tracker Community bridge (function provided by separate CPP).\nextern bool NecroBugHandleAddon(Player* player, std::string const& text);\n', 1)
    eol = '\r\n' if b'\r\n' in original else '\n'
    backup_folder = core / 'NecroBugTracker_Source_Backups' / datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_folder.mkdir(parents=True, exist_ok=False)
    shutil.copy2(chat, backup_folder / chat.name)
    source = BASE / 'server/necro_bug_addon_bridge.cpp'
    try:
        target.write_bytes(source.read_bytes())
        chat.write_bytes(result.replace('\n', eol).encode('utf-8'))
    except Exception:
        shutil.copy2(backup_folder / chat.name, chat)
        if target.exists():
            target.unlink()
        raise
    print('SERVER SOURCE INTEGRATION WRITTEN.')
    print('Backup:', backup_folder)
    print('Build is NOT done. Reconfigure CMake if necessary; rebuild worldserver.')
    print('Also configure NECROBUG_INBOX to the same absolute path as the web dashboard inbox.')


if __name__ == '__main__':
    main()
