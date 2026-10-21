# The setup questions, in plain English

**You only need to run setup for the web dashboard.** The WoW addon and C++ bridge are installed separately. Run `01_Setup_Dashboard.cmd` in a fully extracted ZIP directory.

| Question | What it means | Normal choice |
|---|---|---|
| **Your server name** | The title at the top of your Bug Tracker website. Does **not** rename your WoW realm. | Anything you like |
| **Access choice** | 1 allows opening the site only on the same computer. 2 allows other computers on a trusted LAN to connect. | `1` for one PC, `2` for LAN |
| **Website port** | The number after the colon in the dashboard address, like `http://127.0.0.1:8088`. | `8088` |
| **Reports storage folder** | This is where the website saves the actual bug/idea database and the incoming-report log. Think of it as **your tickets folder**, not the installer folder. | A **full path** outside the download/extracted release folder (recommended) |
| **Incoming report log file** | The single file that receives reports from `worldserver.exe` before the website imports them. It normally lives **inside** your reports storage folder. | Press Enter to keep `inbox/received.log` |
| **Require a password** | If enabled, browsers must sign in before viewing or editing the website. | `N` for a private same-PC test; strongly consider `Y` for a LAN |

## Folder example for the F: test installation

For the known test PC:

- **Game server source:** `F:\BFA-HavenCore-Test`
- **Reports storage folder:** `F:\BFA-HavenCore-Test\NecroBugTracker`
- **Incoming log:** `F:\BFA-HavenCore-Test\NecroBugTracker\inbox\received.log`
- **WoW client:** `F:\BFA-Client-Test-Server`
- **Dashboard package folder:** Wherever you extracted the numbered release ZIP, e.g. `F:\download\58_...\NecroCore_Bug_Tracker_Community_Edition`

**Important:** The executable only sends tickets to the log if its `NECROBUG_INBOX` environment variable names the *same full incoming log file* that setup prints. See `SERVER_INTEGRATION.md`.

## Why a full storage-folder path is better

If you press Enter on a brand-new installation, the default is `web\data`, inside the release's extracted folder. This works, but it's easy to accidentally delete when replacing the release ZIP later. Putting reports in a separate permanent directory makes upgrades easier and safer.

You don't need to understand `relative paths`, JSON, or C++ to complete the web setup.

## Change settings after installing

1. Stop the dashboard with `Ctrl+C` in its CMD window.
2. Run **`01_Setup_Dashboard.cmd`** again from the same release folder.
3. Choose `1` to change settings, `2` to keep everything, or `3` to cancel.
4. Press Enter at any prompt to keep the value displayed in square brackets.
5. Review the summary and save. The installer makes a timestamped backup of the old `web\config.json`.
6. Start **`02_Start_Dashboard.cmd`** again.

Changing the storage location **does not move existing tickets**. You'll be warned and asked to confirm. If you need an upgrade without moving data, keep the original reports-storage path.

**Security:** The dashboard's built-in web server uses HTTP, not HTTPS. Never forward its port to the public internet. If allowing LAN access, use a trusted private network and consider enabling admin login.
