# NecroCore Bug Tracker — Community Edition

A self-hosted **bug and idea tracker** for World of Warcraft **Battle for Azeroth 8.3.7** private servers with compatible BFA-HavenCore/BfaCore-style chat source.

**Status: private release candidate.** Working in-game submissions and saved acknowledgments were verified on a separate Windows test server. This repository is not yet a public, general-compatibility release.

## Components
- WoW client addon: `/bug` and `/idea` submissions.
- Python dashboard: view, search, manage, close/reopen tickets.
- C++ core bridge: requires source integration and rebuilding `worldserver.exe`.
- Windows CMD installers and setup/edit tools.

## Quick installation overview
1. Extract the **entire** Community Edition release ZIP.
2. Install Python 3.9+, then run `01_Setup_Dashboard.cmd`. Choose a ticket-storage directory **outside** the extracted release folder.
3. Run `02_Start_Dashboard.cmd`; by default the dashboard binds to `127.0.0.1:8088`.
4. Back up a compatible BFA core source tree; run `03_Install_Server_Source.cmd`, reconfigure CMake and rebuild worldserver.
5. Install the Lua addon using `04_Install_Client_Addon.cmd`.
6. Point `NECROBUG_INBOX` at **exactly the same absolute inbox log path** used by the dashboard. Test `/bug` and `/idea` and check for **Received** acknowledgments.

**Never run the test-only reset on a production server.** The dashboard is intended for one PC or a **trusted LAN only**, not the public internet. Local configurations, report databases, inbox logs and credentials must not be committed.

## Licensing and publication
Original project source is prepared under **GPL-3.0-or-later**, with upstream BFA core license obligations preserved. The bundled artwork's redistribution provenance still needs review before public publication. Do not consider this private repository a stable v1.0 release yet.

Community project, maintained on a **best-effort** basis. Issues, suggestions, contributions and forks are welcome; response times and updates are not guaranteed.

Official repository: https://github.com/necrosaro710/NecroCore-BugTracker
