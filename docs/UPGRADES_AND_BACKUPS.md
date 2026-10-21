# Backups / upgrade safety

1. Stop only the **Python dashboard** for web upgrades or editing settings. You do not need to stop worldserver unless updating its bridge.
2. Back up the **entire reports storage folder**, especially `bugs.sqlite3` and `inbox/received.log`, as well as `web/config.json`. Setup now backs up the config JSON when editing it, but does not back up the ticket database.
3. Keep earlier source, scripts, and core patches. **Do not remove your custom ChatHandler.cpp changes** or copy a new ChatHandler.cpp from this distribution.
4. Unzip updates into a new release directory. Copy your prior `web/config.json` only if necessary, then use `01_Setup_Dashboard.cmd` to inspect/update it. Keep `data_directory` pointing to the original ticket folder. Changing the folder does not migrate tickets.
5. Start once and confirm your old tickets, Bugs / Ideas / Closed tabs, report edits, and receipt flow.

The dashboard migrates `priority` and `kind` fields when needed. Its importer tracks processed log offsets, and deletion tombstones prevent old log entries from reappearing. Do not delete the database or its `meta`/`deleted` tables to "fix" an import.

This RC **must not** be overlaid on the author's working NecroCore v49 installation without a deliberate upgrade plan.
