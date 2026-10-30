# NecroCore Bug Tracker — Community Edition v1.2

**Status:** Community Edition v1.2, tested on one compatible BfA 8.3.7 Windows test server. Compatibility with other core forks is not guaranteed. The website is for a local PC or trusted LAN only.

A self-hosted bug and idea reporting system for **World of Warcraft Battle for Azeroth 8.3.7** servers using a compatible BFA-HavenCore/BfaCore chat implementation. It contains:

- **WoW addon**: `/bug` and `/idea` windows, Low/Medium/High priority, server receipts after a report is saved.
- **Python dashboard**: dark NecroCore design, Bugs / Ideas / All / Closed tabs, search, filtering, edit, exports, bulk delete, move category, reopen archived tickets.
- **C++ bridge source**: receives NECROBUG addon fragments and appends submissions to a log; sends confirmation after successful append.
- **Windows CMD setup**: portable directories, no MySQL changes, and **no third-party Python packages** for the dashboard.

## New in v1.2 — screenshots

The `/bug` addon has a **Take Screenshot** button. The report window hides before the screenshot is captured. To attach the image to a submitted ticket, run the optional Windows screenshot companion on the same PC as the WoW client (or another authorized client PC). The dashboard and companion use a private upload key; **do not publish it**. See [the complete screenshot guide](docs/SCREENSHOTS_V1_2.md) for the exact order of installation and the `07_`, `08_` and `09_` CMD launchers. Existing v1.1 installations need only a dashboard and addon update—**no worldserver rebuild**.

## Quick install (on a NEW server)

1. Install **Python 3.9 or newer**. Unzip the release to a folder you own, e.g. `C:\NecroBugTracker`.
2. **Right-click the ZIP and choose Extract All first.** Open the extracted `NecroCore_Bug_Tracker_Community_Edition` folder (containing `tools`, `web`, and `client`) and double-click **`01_Setup_Dashboard.cmd`**. Choose your own server name (e.g. Frosthold), local-only or trusted-LAN access, port, reports storage folder, and whether to require a password. The installer explains each choice. The site header and page title use **your** name.
3. Run **`02_Start_Dashboard.cmd`**. It will print the local URL.
4. On the **worldserver source PC**, run **`03_Install_Server_Source.cmd`** only on a compatible, *unmodified* BFA-HavenCore chat bridge. It refuses to overwrite an existing NecroBug installation. Then follow `docs/SERVER_INTEGRATION.md` to set the log location and build worldserver.
5. On each WoW PC run **`04_Install_Client_Addon.cmd`**, or copy `client/NecroBugTracker/{NecroBugTracker.lua,NecroBugTracker.toc}` to `WoW/Interface/AddOns/NecroBugTracker`. Restart WoW (`/reload`).
6. Submit a **test** `/bug`, confirm it appears on the dashboard, and check that WoW receives an acknowledgment; then test `/idea` and the Closed tab.

**Already running a customized NecroCore production install? Back up and test before changing it.** This is an independent release package for other owners; follow `docs/UPGRADES_AND_BACKUPS.md` before migrating data.

## Upgrading an existing RC dashboard without changing the core

**Do NOT reset the test server again and do NOT rebuild the worldserver just to get clearer setup wording or the green Open status.** These changes are in the Python dashboard and CSS, not the C++ bridge.

To update the website installer: stop the old dashboard, extract this release to a NEW directory, copy your existing `web/config.json` from the old release to the new release's `web` folder (do not upload your config publicly), and run `01_Setup_Dashboard.cmd` in the new folder. Choose 1 to edit and verify the new prompts, keeping the same **absolute** reports storage location. Then run `02_Start_Dashboard.cmd` in the new folder and check your old tickets are still visible. Keep the prior release folder until confirmed.

If the current `web/config.json` uses `data_directory` of `.` or `data` instead of an absolute path, your tickets may be stored under the old release folder. **Do not delete that folder.** Read `docs/UPGRADES_AND_BACKUPS.md` and migrate the data with a verified backup before changing the storage location.

For a plain-English explanation of every setup question, read **`docs/SETUP_EXPLAINED.md`**.

## Optional administrator login

- **Default: OFF.** Choose ON in setup to create a password stored as a salted PBKDF2 hash.
- Default bind address is `127.0.0.1` (same PC only); select trusted-LAN mode to bind `0.0.0.0`.
- When login is OFF in LAN mode, **any network user who can reach the dashboard can read, edit, and delete tickets**. This is intended only for a trusted private network.
- The Python server **does not provide HTTPS**. Even with admin login, do not expose it to the public internet; reverse-proxy security / HTTPS and further hardening are needed for that.
- For an existing install, config is in `web/config.json`; or rerun `01_Setup_Dashboard.cmd` to change it. Setup backs up your existing `config.json` automatically and never clears your ticket database.

## Dependencies

- Web: Python 3.9+ standard library, Windows 10/11 or another OS with Python. SQLite bundled with Python.
- Client: WoW BfA client, interface 80300.
- C++: a compatible BFA-HavenCore/BfaCore tree and its normal compiler/build dependencies. **Core source changes and a real worldserver compilation are required** for new installs; this is not just a WoW addon and is not a universal drop-in module for every emulator.
- The dashboard does **not** need a MySQL connection.

## Where data goes

**Two different locations are involved:**

1. **Release folder** — where you extracted the ZIP and run the CMD launchers. Example: `C:\NecroBugTracker-Release`. You may replace this folder during upgrades.
2. **Reports storage folder** — the folder where the dashboard saves your ticket database (`bugs.sqlite3`) and receives game reports (`inbox\received.log`). **For upgrades, choose a full path OUTSIDE the release folder**, e.g. `C:\MyWoWServer\NecroBugTracker` (on the test PC: `F:\BFA-HavenCore-Test\NecroBugTracker`).

**If you press Enter at the Reports storage folder prompt**, the new-install default is `web\data` inside the extracted ZIP. It works, but if you delete the release folder during an upgrade you could lose those tickets. An absolute location outside the release directory is safer.

**The Incoming report log file** normally remains `inbox/received.log`. It resolves inside the Reports storage folder. Your worldserver must set `NECROBUG_INBOX` to **the full file path**, and the dashboard must read the exact same file; the setup tool prints that full path at the end.

**To change settings later:** Stop the dashboard, rerun `01_Setup_Dashboard.cmd`, choose **1 — Change settings**, press Enter to retain fields you don't want changed, confirm and save. The old JSON settings are backed up automatically. Existing tickets are **not deleted**, but **changing the reports storage folder does not move them**; copy the old data files yourself before restarting, or keep the original folder. You can also keep settings with choice 2 or cancel with choice 3.

## Community maintenance and contributions

Bug reports, feature suggestions, pull requests and forks are welcome. Development and support are offered on a **best-effort** basis; individual responses, updates, and timelines cannot be guaranteed. Before posting logs, remove private account details and passwords. See `docs/PUBLISHING_GITHUB.md` for publication readiness and issue templates.

## Known limits

- Compiled and tested on a second BfA 8.3.7 test server (including a dashboard receipt). The clean-room reinstallation succeeded; v1.0 dashboard setup editing was verified on the Windows test PC; other core forks remain untested.
- WoW chat APIs and engine hooks differ among core forks; some may need a manual integration.
- The web dashboard's direct-source compatibility is for the BFA-HavenCore implementation described here, not guaranteed for TrinityCore/AzerothCore revisions.
- The receipt ID from the C++ bridge identifies the log entry. The dashboard gives a separate numeric ticket ID during import.
- No internet-facing deployment security or automated user-role management included.

Read `docs/COMPATIBILITY_AND_RELEASE_CHECKLIST.md` to understand the remaining compatibility and security limits.

## Custom branding / attribution

- **Your server name is fully customizable** during setup, and can be changed later by running `05_Change_Dashboard_Name.cmd` and restarting the dashboard. No data or core rebuild is needed.
- The logo, page title, welcome message, and login screen use your configured name.
- **`Powered by NecroCore Bug Tracker`** remains as a small footer credit, including when the server name is changed. It is intentionally not exposed as a configuration option. The code is distributed as editable source, so this is an attribution convention, not tamper-proof DRM. Once your official GitHub project is published, add its real HTTPS address as `attribution_repo_url` in `web/config.json` (example format: `https://github.com/YOUR_ACCOUNT/YOUR_REPOSITORY`). The footer becomes a clickable GitHub link. **The official project URL is built in as a fallback; a valid configured URL can override it.**
- This does **not** rename your WoW server or affect any database records.



## Community Edition v1.1 GitHub workflow

- Opens a pre-filled GitHub issue draft with a consistent title (`[Quest] Zone: Quest Name`), captured context, and optional reporter identity.
- Save the resulting GitHub issue URL back to the local ticket. No GitHub token or automatic publishing.
- Choose issue categories manually or let the dashboard infer from existing quest/target fields.
- Existing installations can run `06_Update_Existing_Dashboard_v1.1.cmd` from the new package, without touching the WoW addon, C++ bridge or game server.
- See `docs/GITHUB_ISSUES.md`.

## Community Edition v1.0 changes

- Repeatable dashboard setup with edit/keep/cancel, clear reports folder prompts and configuration backups.
- Green Open status and the clickable official GitHub footer.
- Tested addon acknowledgments and bug/idea submissions after a clean installation on a compatible BfA 8.3.7 test server.

## Official GitHub project

https://github.com/necrosaro710/NecroCore-BugTracker

The website's small **Powered by NecroCore Bug Tracker** footer is a clickable link to the official repository, even when old configurations have an empty `attribution_repo_url`. The repository is the public location for project updates and issue reports. No installer or data changes are needed to enable the link.

## License and security

Community Edition original source is offered under GPL-3.0-or-later. See `LICENSE`, `docs/LICENSE_NOTICE.md`, and `SECURITY.md`. The maintainer has approved inclusion of the bundled artwork. This dashboard is not an internet-facing secure service.
