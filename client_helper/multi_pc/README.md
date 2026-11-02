# Optional multi-PC screenshot client (68.1 pilot)

This is a standalone optional replacement for the v1.2 one-character screenshot companion. It works with the **existing screenshot-enabled v1.2 HTTP dashboard** (or a compatible customized dashboard). It does not replace the WoW addon, core, dashboard, or SQLite database.

**What it does:** Every WoW client computer running the companion watches its own WoW Screenshots folder. Only when the dashboard advertises a screenshot-requested ticket does it attempt a conservative timestamp match. When exactly one picture matches exactly one ticket, the companion writes a SHA-256-verified, character-named copy to the configured server folder/share, then posts the image to the existing ticket-attachment endpoint. Originals remain on the WoW PC.

## Set up on each WoW Windows PC

1. Copy the entire \`client_helper/multi_pc\` folder to a **separate** location on that PC (not inside the server dashboard folder).
2. Run \`01_Setup_On_This_WoW_PC.cmd\`. A verified official portable Python runtime downloads once.
3. Select the **local** WoW Screenshots folder (next to that PC's WoW client). On the server PC with the conventional \`C:\BFA-HavenCore\NecroBugTracker\` path, the existing upload key and local \`Screenshots\` destination are detected. On a different PC, enter that server's LAN HTTP dashboard URL (for example \`http://192.168.1.50:8088\`) and an already-permitted Windows share (for example \`\\192.168.1.50\BugTrackerShots\`). A remote PC may use clipboard input for the dashboard upload key.
4. Setup checks the upload endpoint and screenshot-folder read/write rights before saving configuration.
5. Run \`02_Start_Hidden_On_This_PC.cmd\` once to monitor invisibly. \`03_Stop_On_This_PC.cmd\` stops it. Enable login autostart only if desired via \`06_Enable_AutoStart_Optional.cmd\`.
6. If a ticket is already awaiting a screenshot, \`05_Transfer_One_Pass_Visible.cmd\` makes a single transfer attempt and shows the outcome.

**On the dashboard server:** Keep its existing dashboard running and its screenshot-upload endpoint configured. No additional screenshot-archiver window is required. No addon/worldserver rebuild is necessary for a dashboard and addon already supporting screenshot requests.

## Limits and known caveats

- Windows 10/11; JPEG/PNG up to 8 MiB; screenshot timestamp and server clock must be within roughly 20 seconds. Only one screenshot per ticket.
- The companion does **not** identify a character from pixels. If multiple pending tickets or screenshot files overlap in time, it deliberately skips ambiguous matches. It is **not** proof that every simultaneous multi-PC event will be matched correctly. Check attachments before sharing them publicly.
- Reports without the in-game **Take Screenshot** request do not trigger uploads; this does not mirror arbitrary screenshots.
- One process per client PC, normally hidden; the dashboard/server is not changed.
- Do not delete originals until verifying transfers. This script never deletes original WoW screenshots.
- A successful local simulation and live screenshots on two NecroCore LAN Windows PCs have been reported for the private 68.1 pilot; multi-character scenarios and unrelated servers remain unverified.

For the already-running private 68.1 installation, no update or reinstall is necessary just because this source folder has been published. The public copy uses generic LAN defaults rather than the private pilot's prefilled LAN address.
