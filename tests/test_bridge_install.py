"""Synthetic source-install test; does not touch a real core."""
from pathlib import Path
import subprocess
import tempfile
import sys

root = Path(__file__).resolve().parent.parent
# Just enough of the upstream handler structure to exercise the safe anchor logic.
source = '''#include "Player.h"
#include "WorldSession.h"
void WorldSession::HandleAddonMessageOpcode()
{
    // Disabled addon channel?
    if (!sWorld->getBoolConfig(CONFIG_ADDON_CHANNEL))
        return;

    switch (type)
    {
        case CHAT_MSG_WHISPER: break;
    }
}
'''
with tempfile.TemporaryDirectory() as directory:
    core = Path(directory)
    handlers = core / 'src/server/game/Handlers'
    handlers.mkdir(parents=True)
    chat = handlers / 'ChatHandler.cpp'
    chat.write_text(source)
    cmd = [sys.executable, str(root / 'tools/install_bridge.py'), '--core', str(core)]
    first = subprocess.run(cmd, capture_output=True, text=True)
    assert first.returncode == 0, first.stdout + first.stderr
    content = chat.read_text()
    assert content.count('if (prefix == "NECROBUG")') == 1
    assert content.count('extern bool NecroBugHandleAddon') == 1
    assert (handlers / 'necro_bug_addon_bridge.cpp').exists()
    second = subprocess.run(cmd, capture_output=True, text=True)
    assert second.returncode != 0
    assert chat.read_text() == content
    print('PASS conservative bridge installer / second-run refusal')
