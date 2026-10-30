# v1.2 screenshot capture — Community Edition

Screenshot support is **optional**. Images are never sent through the WoW addon-chat bridge. Existing bug and idea reports work with or without the companion.

## On the dashboard / test-server PC

1. Back up the existing dashboard. Stop `02_Start_Dashboard.cmd` (Ctrl+C).
2. Extract the entire v1.2 ZIP. Run `09_Update_Existing_Dashboard_v1.2.cmd`. Enter the extracted **existing Community Edition folder**, not the BFA core folder. The updater makes a dated source-file backup and does **not** modify `web/config.json`, the worldserver, or your ticket database. On next startup, the dashboard adds a `screenshot_epoch` column and `screenshots` table without deleting existing tickets.
3. Restart your **original** `02_Start_Dashboard.cmd`, not the one from the update ZIP.
4. In that same original dashboard folder, run `07_Show_Server_Screenshot_Key.cmd`. Keep the key **private**. Do not send it in chat, Discord, or GitHub.
5. Ensure the dashboard is configured for **trusted LAN** access if your WoW client is a different computer; the `127.0.0.1` URL only works locally. Do not expose port 8088 to the internet.

## On each WoW CLIENT PC

1. Extract the **same** complete ZIP to the WoW client PC.
2. Run `04_Install_Client_Addon.cmd`; choose the WoW directory containing `Wow.exe`. Restart WoW or `/reload`.
3. Run `08_Start_Screenshot_Companion_CLIENT.cmd`. On first use it downloads ~12 MB of the official Windows embedded Python runtime into the extracted ZIP folder. The runtime file is verified against the official Python.org SHA-256 before extraction; no Python installation or administrator privileges are needed. It needs internet **once** on that client PC.
4. On first start, enter the dashboard LAN URL (for example `http://192.168.50.82:8088`, **only if that is actually your test dashboard**), the local WoW `Screenshots` directory (usually next to `Wow.exe`), exact character name, optional realm, and the private key from Step 4 on the server PC. These values are saved locally in `client_helper/companion_config.json`; keep that file private.
5. Leave the companion running while gaming (you can minimize its CMD window).
6. Open `/bug`, click **Take Screenshot**. The entire bug-report window hides for at least two rendered frames and 0.4 seconds before WoW captures the world. It stays hidden until screenshot completion (or a safe timeout), then reappears. The addon also delays chat confirmation until after capture so the screenshot does not include an extra status message. Complete notes and submit. When your worldserver confirms **Report received**, the dashboard imports the text report and the companion matches and uploads the picture. Open that ticket in the dashboard to see the image under the notes.

**No worldserver rebuild** is required: screenshot capture metadata is a 17th optional addon field, forwarded unchanged by the existing text bridge. Note that taking a screenshot using the **new** addon before upgrading the dashboard will produce a newer record format that **v1.1 cannot import**. Update the dashboard first.

## Important limits and privacy

- Only **one** screenshot per report in v1.2. JPEG/PNG only, **8 MiB maximum**. WoW normally saves `.jpg` files; if configured to output `.tga`, change WoW's screenshot format to JPEG or use a JPEG conversion.
- Auto-match requires the same character and screenshot capture timestamp, with client and game-server clocks within roughly **30 seconds** of each other. If multiple screenshots could match, the companion deliberately **does not guess**; the screenshot stays on the PC until it can be matched or manually reviewed.
- The companion never uploads arbitrary screenshots: it only selects an image near an explicitly requested in-game screenshot report from the configured character. It polls while running and can retry if the dashboard was offline, for screenshots/reports up to 48 hours old.
- The private upload key authorizes screenshot uploads but **not** ticket editing or deletion. Protect `client_helper/companion_config.json` and the server's `<reports-data-dir>/.screenshot_upload_key`.
- Do **not** publish screenshots containing passwords, chat with private information, account details, or user identities. On GitHub, images are still added **manually** when creating the issue; a LAN-only image URL is not publicly accessible.
- Dashboard's admin login and existing network access behavior are unchanged. Do not port-forward this service.

## Files changed

- `client/NecroBugTracker/NecroBugTracker.lua` and `.toc` (addon update on client only)
- `web/dashboard.py`, `web/launch_dashboard.py`, `web/screenshot_uploads.py` (dashboard update)
- `client_helper/necro_screenshot_companion.py` plus `08_Start_Screenshot_Companion_CLIENT.cmd` (client helper, isolated from game installation)
- `07_Show_Server_Screenshot_Key.cmd` and `tools/show_screenshot_key.py` (server key display)
- `09_Update_Existing_Dashboard_v1.2.cmd`, `tools/upgrade_dashboard_v12.py` (safe website upgrade)

No C++ source changes, addon protocol recompilation, MySQL updates, or full core rebuild.
