# NecroCore Bug Tracker — Community Edition

A self-hosted **bug and idea tracker** for compatible World of Warcraft **Battle for Azeroth 8.3.7** private servers. It includes a WoW Lua addon, C++ worldserver bridge, and Python dashboard.

**Installation guide:** [README_START_HERE.md](README_START_HERE.md) (added with the full source upload).

## Quick start
1. Download and **extract the entire source ZIP**.
2. Run `01_Setup_Dashboard.cmd` and `02_Start_Dashboard.cmd`. Default URL: `http://127.0.0.1:8088`.
3. On a compatible core source tree run `03_Install_Server_Source.cmd`, reconfigure CMake, **rebuild worldserver**, and set `NECROBUG_INBOX` to the same absolute path as the dashboard inbox.
4. Install the client addon with `04_Install_Client_Addon.cmd`, then test `/bug` and `/idea`.

**Security:** Local PC/trusted LAN only. Do not expose the dashboard directly to the public internet, or upload `web/config.json`, ticket databases, or report logs.

Original Community Edition code: **GPL-3.0-or-later**, subject to upstream copyright/license obligations. Independently developed; not affiliated with Blizzard. Bug reports, suggestions and PRs are welcome on a best-effort basis, but updates and responses aren't guaranteed.

Official repository: https://github.com/necrosaro710/NecroCore-BugTracker
