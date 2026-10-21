# Your server name and NecroCore credit

During setup, enter any server/dashboard name up to 48 characters. This name appears in the sidebar, browser title, welcome banner, export heading, and optional login page. It does not change your WoW realm name.

After installation, double-click `05_Change_Dashboard_Name.cmd` and enter the new name. It backs up `web/config.json` next to the original, changes only `server_name`, and leaves all reports, passwords, bind settings, and other configuration values untouched. Restart `02_Start_Dashboard.cmd` to see it. You can also edit `server_name` in `web/config.json` while the dashboard is stopped.

The small **Powered by NecroCore Bug Tracker** credit is hard-coded in the footer and is intentionally not an editable setting. It also appears on the login page when login is enabled. The source code remains editable; this is ordinary attribution, not unremovable copy protection.

No worldserver recompilation, MySQL changes, or addon updates are needed when renaming the dashboard.

## Link the credit to your official GitHub project

The official NecroCore Bug Tracker repository is **https://github.com/necrosaro710/NecroCore-BugTracker**. The small **Powered by NecroCore Bug Tracker** footer automatically links to this page, including when an existing `web/config.json` has a blank or missing `attribution_repo_url`. The same link appears on the admin login screen.

An advanced installation may supply a validated HTTPS GitHub repository URL as `attribution_repo_url` in `web/config.json`; if blank or invalid, the official project URL is used. The dashboard requires no GitHub login to start, and the link does not load remote assets. When the repository is public, visitors can follow the footer link to project documentation.

**To update an existing dashboard:** replace only `web/dashboard.py`, `web/launch_dashboard.py`, and `web/necrocore_assets/necrocore.css` while the dashboard is stopped, then restart `02_Start_Dashboard.cmd`. No database, addons, or server rebuild required.
