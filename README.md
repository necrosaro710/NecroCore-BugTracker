# NecroCore Bug Tracker — Community Edition

A self-hosted in-game **bug and idea tracker** for compatible World of Warcraft **Battle for Azeroth 8.3.7** private servers. Includes a WoW Lua addon, C++ worldserver chat bridge, and Python web dashboard.

**[⬇ Download the latest release](https://github.com/necrosaro710/NecroCore-BugTracker/releases/latest)** · **[Installation guide](README_START_HERE.md)**

## Screenshots

![In-game reporting UI](InGameUIscreenshot.png)

![NecroCore ticket dashboard](TicketUI.png)

### GitHub issue integration (v1.1)

Turn a gameplay report into a reviewed, prefilled GitHub issue, with standardized titles and report context. Publishing is manual, and reporter identity is excluded by default.

![GitHub issue created from a tracker ticket](screenshots/GitHub_Issue_Export_Test.png)

[View our verified test issue #2](https://github.com/necrosaro710/NecroCore-BugTracker/issues/2) (closed after testing).

### Screenshot attachments (new in v1.2)

The in-game `/bug` window includes **Take Screenshot**. It hides itself before capture and returns afterward. An optional Windows screenshot companion matches the image to the submitted report and attaches it to the local dashboard ticket. **The companion must be running for automatic uploads.** Screenshot upload is available only on the local PC or a trusted LAN, not via a public Internet service.

See [v1.2 screenshot setup, privacy limits and upgrade steps](docs/SCREENSHOTS_V1_2.md).

## Quick start

1. Download the latest tagged release and **extract the entire ZIP** (do not run CMD files inside a ZIP).
2. Run `01_Setup_Dashboard.cmd`, then `02_Start_Dashboard.cmd` on the dashboard PC. By default it serves `http://127.0.0.1:8088`.
3. On a compatible BFA-HavenCore source tree, run `03_Install_Server_Source.cmd`, reconfigure CMake, **rebuild worldserver**, and point `NECROBUG_INBOX` to the dashboard's absolute incoming log path. (Existing compatible v1.x installations do not need a C++ rebuild for v1.2.)
4. Install the addon with `04_Install_Client_Addon.cmd` on the WoW client. Log in and try `/bug` and `/idea`.
5. Optional screenshots: on an existing v1.1 dashboard, run `09_Update_Existing_Dashboard_v1.2.cmd`; then use `07_Show_Server_Screenshot_Key.cmd` on the dashboard PC and `08_Start_Screenshot_Companion_CLIENT.cmd` on the WoW client PC.

**Security:** The dashboard is intended only for a local computer or a **trusted private LAN**. Do not expose it to the public internet, upload private `web/config.json`, SQLite reports, inbox logs, upload keys, or screenshot companion configuration. Test on a nonproduction server first. Compatibility has been verified with one BfA 8.3.7-derived core only.

Original source under GPL-3.0-or-later, with upstream notices preserved. Not affiliated with Blizzard Entertainment. Contributions and bug reports are welcome on a **best-effort** basis without guaranteed response times.

Thanks to [HavenWoW BFA-HavenCore](https://github.com/HavenWoW/BFA-HavenCore) for core development and BfA fixes.
