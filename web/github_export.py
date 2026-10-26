"""Safe, credential-free GitHub issue draft helpers for NecroCore v1.1.

No report is submitted to GitHub automatically. An admin reviews a draft and
clicks 'Submit new issue' on GitHub. The resulting issue URL can be linked back
locally afterward.
"""
import re
from urllib.parse import urlencode, urlsplit

CATEGORIES = ('Auto', 'Quest', 'NPC', 'Spell', 'Dungeon', 'Item', 'GameObject', 'Other')
_REPO = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,38}/[A-Za-z0-9_.-]{1,100}\Z')
_ISSUE = re.compile(r'/([A-Za-z0-9][A-Za-z0-9_.-]{0,38})/([A-Za-z0-9_.-]{1,100})/issues/([1-9][0-9]*)/?\Z')


def valid_repo(repo):
    """Canonical owner/repo only: never allow arbitrary redirect targets."""
    repo = str(repo or '').strip()
    if not _REPO.fullmatch(repo) or '..' in repo or repo.endswith('.'):
        return ''
    return repo


def valid_issue_url(url):
    """Allow only GitHub issue links, not arbitrary URLs or webhooks."""
    url = str(url or '').strip()
    if len(url) > 400:
        return ''
    try:
        parsed = urlsplit(url)
        if (parsed.scheme != 'https' or parsed.hostname != 'github.com' or parsed.port not in (None, 443)
                or parsed.username or parsed.password or parsed.query or parsed.fragment):
            return ''
    except ValueError:
        return ''
    match = _ISSUE.fullmatch(parsed.path)
    return 'https://github.com' + parsed.path.rstrip('/') if match and valid_repo(match[1] + '/' + match[2]) else ''


def classify(report):
    explicit = (report['issue_category'] or 'Auto').strip()
    if explicit in CATEGORIES and explicit != 'Auto':
        return explicit
    if report['kind'] == 'Idea':
        return 'Other'
    if (report['quest'] or '').strip():
        return 'Quest'
    typ = (report['typ'] or '').strip().lower().replace(' ', '')
    if typ in ('creature', 'unit', 'npc'):
        return 'NPC'
    if typ in ('gameobject', 'object'):
        return 'GameObject'
    if typ == 'item':
        return 'Item'
    if typ == 'spell':
        return 'Spell'
    return 'Other'


def brief(text, limit=110):
    text = ' '.join(str(text or '').split())
    return text[:limit].rstrip(' -,:') if text else ''


def title(report):
    category = classify(report)
    kind = 'Idea' if report['kind'] == 'Idea' else category
    zone = brief(report['zone'], 46)
    subject = brief(report['quest'] or report['target'] or report['notes'], 105) or ('Suggestion' if kind == 'Idea' else 'Unspecified issue')
    return '[{}] {}{}'.format(kind, (zone + ': ') if zone else '', subject)[:240]


def body(report, server_name='WoW server', include_reporter=False):
    def value(name):
        return str(report[name] or '').strip() or 'Not recorded'
    lines = [
        '## Description',
        str(report['notes'] or '').strip() or 'No description supplied.',
        '', '## Report context',
        '- Type: ' + value('kind'),
        '- Category: ' + classify(report),
        '- Priority: ' + value('priority'),
        '- Zone: ' + value('zone'),
        '- Subzone: ' + value('subzone'),
        '- Related quest: ' + value('quest'),
        '- Target: ' + value('target'),
        '- Target type: ' + value('typ'),
        '- Target entry ID: ' + value('entry'),
        '- Map ID: ' + value('map'),
        '- Player map position (%): ' + value('x') + ', ' + value('y'),
        '- Source ticket: #' + str(report['id']) + ' (local NecroCore Bug Tracker)',
        '- Client era: Battle for Azeroth 8.3.7',
    ]
    if include_reporter:
        lines += ['- Submitted by character: ' + value('char'), '- Realm: ' + value('realm')]
    if (report['questlog'] or '').strip():
        lines += ['', '## Reporter quest log snapshot', str(report['questlog']).strip()]
    lines += ['', '---', 'Exported from NecroCore Bug Tracker. Please verify details before submitting.']
    return '\n'.join(lines)


def draft_link(repo, title_text, body_text):
    repo = valid_repo(repo)
    if not repo:
        return '', False
    # Keep query below conservative browser/proxy request-size limits. For large
    # reports, do not truncate: require manual paste of the full body.
    full = 'https://github.com/{}/issues/new?{}'.format(repo, urlencode({'title': title_text, 'body': body_text}))
    if len(full) <= 4500:
        return full, True
    return 'https://github.com/{}/issues/new?{}'.format(repo, urlencode({'title': title_text})), False
