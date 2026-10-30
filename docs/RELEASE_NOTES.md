# v1.1 — GitHub issue workflow (dashboard-only)

- Standardized GitHub titles: `[Quest] Westfall: Treasure Hunting` and similar.
- Automatic category suggestions from captured quest/target type, with editable category override.
- Review/approve GitHub issue draft in a browser; no credentials stored, no automatic public submissions.
- Optional copy-full-body flow when report exceeds safe GitHub URL lengths.
- Store a validated GitHub issue URL on the existing local ticket.
- Backed-up website-only installer; no worldserver or addon rebuild.
- Automatic non-destructive SQLite migration for two new fields; pre-v1.1 tickets preserved.

# v1.0 — Community Edition (2026-10-21)

First Community Edition source release. Includes the client addon, C++ bridge installer, Python dashboard, source, themes, and Windows CMD launchers.

- `/bug` and `/idea` report submission, dashboard import, and Received acknowledgments tested on a BfA 8.3.7 HavenCore-derived test server.
- Web dashboard setup can be edited later and preserves existing configuration/data.
- Green Open status, fixed GitHub footer hyperlink, and local/trusted-LAN bind options.
- See README_START_HERE.md for setup. This is not guaranteed to work on unrelated emulator forks and is not hardened for public internet hosting.


## v1.2 — In-game screenshots (2026-10-30)
Added an in-game **Take Screenshot** button, hidden-window capture, and an optional Windows companion for private screenshot upload to matching dashboard tickets. The dashboard accepts one JPEG/PNG screenshot per report (8 MiB maximum), with a private upload key and conservative character/time matching. No C++ worldserver rebuild is needed for existing installations. Tested end-to-end on the BfA test client with the bug window absent from the image. See docs/SCREENSHOTS_V1_2.md.
