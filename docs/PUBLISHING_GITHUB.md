# Publishing checklist (after the release candidate is verified)

1. Official repository created: **https://github.com/necrosaro710/NecroCore-BugTracker**. Keep it private until the final security and license review; make it public when ready to publish.
2. Verify source and image license permissions. The code patches a GPL-covered BfA core and its license obligations apply to derivatives. Supply appropriate licensing and attribution for the separate Python, Lua, and artwork too.
3. Confirm the newest release package works on Windows: setup, edit, dashboard start, addon, bridge, compile, `/bug` receipt, `/idea` receipt, ticket close/reopen, backups.
4. Check the archive contains **no** `web/config.json`, private password hashes, `.sqlite3`, `received.log`, account data, hostnames, or individual users' source/custom patches.
5. Configure GitHub **Issues** and include clear bug / feature issue templates. Development may be maintained on a **best-effort** basis; updates, troubleshooting, or individual replies are not guaranteed.
6. The official URL is now linked automatically in the footer, even for older, blank configurations. No edit to `web/config.json` is necessary. The private repository may display 404 to non-collaborators until made public.
7. Mark builds as a **release candidate** until the outstanding compatibility, security, and licensing items are completed. Do not call the package officially supported by Blizzard, TrinityCore, or BfaCore.

The Community Edition is a community project, offered as available. Bug reports, suggestions, pull requests, and forks are welcome; response and update times are **not guaranteed**.
