# NecroCore Bug Tracker — Community Edition

A self-hosted in-game **bug and idea tracker** for compatible World of Warcraft **Battle for Azeroth 8.3.7** private servers. It consists of a WoW Lua addon, C++ worldserver chat bridge, and Python web dashboard.

**[⬇ Download Community Edition v1.0 (ZIP)](https://github.com/necrosaro710/NecroCore-BugTracker/releases/download/1.0/NecroCore_BugTracker_Community_Edition_v1.0.zip)**

**Installation guide:** [README_START_HERE.md](README_START_HERE.md) — setup, build instructions, data locations and upgrades.

## Screenshots

![NecroCore Bug Tracker — screenshot 1](InGameUIscreenshot.png)

![NecroCore Bug Tracker — screenshot 2](TicketUI.png)

## Quick start

1. Download the [source ZIP](../../archive/refs/heads/main.zip) or GitHub release, and **extract everything**.
2. Run `01_Setup_Dashboard.cmd` and then `02_Start_Dashboard.cmd`. The local dashboard defaults to `127.0.0.1:8088`.
3. On a compatible core source tree, run `03_Install_Server_Source.cmd`, reconfigure CMake, **rebuild worldserver**, and set `NECROBUG_INBOX` to match the absolute dashboard incoming-log path.
4. Install the client Lua addon with `04_Install_Client_Addon.cmd`, log in, and try `/bug` and `/idea`.

**Warning:** Web dashboard is for the local machine or a **trusted private LAN**, not public internet hosting. Do not expose the web port or publish private `web/config.json`, `bugs.sqlite3`, or report logs. Use a dedicated test server first; only one BfA 8.3.7-derived core implementation has been verified.

Licensed original source: GPL-3.0-or-later, with upstream license notices preserved. Not affiliated with Blizzard Entertainment. Contributions/issues are welcome on a **best-effort** basis; update and response times are not guaranteed.

Official project: https://github.com/necrosaro710/NecroCore-BugTracker
