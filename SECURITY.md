# Security

NecroCore Bug Tracker's Python dashboard is designed for a **single PC or trusted LAN** only. It is **not hardened for deployment on the public internet** and does not provide HTTPS.

If you disable admin login, anyone who can reach the dashboard can inspect, modify, or delete reports. Keep your local firewall and binding options restricted.

Never publish your `web/config.json`, databases, inbox logs, passwords or player details. Report suspected security flaws privately to the repository maintainer before public disclosure.
