# Installing the server-side bridge

This is a **source integration**, not a DLL/plug-and-play module. Compile only with your own compatible BfA core source and preserve any existing customizations.

## Automatic conservative installer

Run `03_Install_Server_Source.cmd` on Windows and enter the **source root** (not the `build` folder). It checks for `src/server/game/Handlers/ChatHandler.cpp`, refuses to overwrite an existing bridge, backs up ChatHandler.cpp under your chosen core directory, and adds:

- `src/server/game/Handlers/necro_bug_addon_bridge.cpp`
- A `NecroBugHandleAddon` declaration and the specific NECROBUG dispatch hook in ChatHandler.cpp.

It does **not** change MySQL tables, build executables, or touch any existing web database.

If it reports incompatible core source, stop and manually integrate the minimal hook in `ChatHandler.cpp` in the appropriate addon-message handler (after the addon channel availability check and before the ordinary chat forwarding switch):

    extern bool NecroBugHandleAddon(Player* player, std::string const& text);

    if (prefix == "NECROBUG") {
        NecroBugHandleAddon(sender, text);
        return;
    }

Copy the bridge source and register it in your build if your CMake files do not discover new CPPs automatically. **Never replace your core's entire ChatHandler.cpp with a file from another server.**

## Report-log location — essential

The bridge checks the **NECROBUG_INBOX** environment variable for a full path. Otherwise it writes relative to the `worldserver.exe` process's **working directory**:

    NecroBugTracker\inbox\received.log

Set the dashboard `web/config.json` `inbox_path` to point to the **same exact file** (absolute path recommended). To start worldserver with a custom path from CMD, run these commands from its normal executable folder, adjusting both paths for your installation:

    set "NECROBUG_INBOX=C:\MyServer\NecroBugTracker\inbox\received.log"
    worldserver.exe

If you launch via shortcut or Windows Service, configure its environment separately. A variable set in one CMD window does not automatically apply to a service or another preexisting process.

The bridge creates the parent directory if needed. Make sure worldserver can write and the Python dashboard can read the file.

## Compile

Use your core's existing configured compiler/toolchain and CMake build. You may need a CMake reconfigure to discover the new `.cpp`. Build the actual **worldserver** target. Do not interpret source install or a CMake configuration pass as a successful build.

- Verify the bridge CPP is present in the built target.
- Launch the new worldserver executable from its normal path.
- In WoW `/bug`, submit a test report, verify the dashboard imports it, and verify the client's "saved" receipt.
- If the addon says waiting for verification, check that the **running executable** (not only the source) contains the new bridge and that the `NECROBUG` whisper packet path is supported by this core.

## Compatibility

The included bridge uses core classes `WorldPackets::Chat::Chat`, `Player`, `WorldSession`, the `LANG_ADDON` whisper channel, and C++17 `<filesystem>`. These APIs must be available (or adapted) on the target fork. This bridge has not been verified on every server distribution.
