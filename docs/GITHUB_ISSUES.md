# GitHub issue export — Community Edition v1.1

**What this feature does:** A dashboard operator can preview a formatted gameplay bug report, open a pre-filled GitHub issue draft, and later paste the created issue URL back into the original ticket. **The app never submits issues automatically.** The person must be signed into GitHub and click **Submit new issue** there. No token or GitHub password is required.

## Where to send reports

Enter the **game server/source repository** where your developers track gameplay bugs, for example `my-team/my-bfa-core` (without `https://github.com/`). The NecroCore Bug Tracker software repository is for bugs *in the tracker itself*, not gameplay bugs.

To save a default destination, stop the dashboard and rerun `01_Setup_Dashboard.cmd`. At **Game source GitHub repository**, enter `owner/repo`. You can also leave it empty and specify the destination separately for each issue preview.

## How to use

1. In the dashboard, select a ticket, and click **GitHub Issue** or **Review GitHub issue**.
2. Confirm the **destination repository**, formatted title, captured game context, and whether you want to include the character name/realm (unchecked by default).
3. If necessary, click **change category** to choose `Quest`, `NPC`, `Spell`, `Dungeon`, `Item`, `GameObject`, or `Other` (the default `Auto` derives what it can from quest or target type).
4. Click **Open pre-filled GitHub draft**. Log into GitHub, review, and click **Submit new issue**. If the full report is too long for a safe URL, click **Copy description** and paste the text into the GitHub form instead.
5. Copy the resulting GitHub issue URL and paste it into **Save GitHub issue link** on your NecroCore ticket. The link is kept locally in the same SQLite database.

**Privacy/security:** Opening a prefilled link sends the title and description to the GitHub website in its URL. Preview first and never export passwords, private account details, or player-identifying data. Github issues in public repositories are public. This dashboard must remain local or on a trusted LAN. No data is sent to GitHub merely by viewing a report.

**Compatibility:** Addon and worldserver C++ bridge are unchanged. v1.1 adds two non-destructive SQLite columns (`issue_category`, `github_issue_url`) to existing reports; existing ticket IDs and information remain. Stop the dashboard and back up reports before changing versions. A GitHub issue link is saved locally; status is **not** automatically synchronized with GitHub.
