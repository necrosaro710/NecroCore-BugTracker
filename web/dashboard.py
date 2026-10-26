# NecroCore Bug Tracker dashboard v1.1 (GitHub issue workflow)
# Supports both existing 14-field in-game reports and new 15-field reports with priority.
# No C++ bridge changes or database reset required.
import html
import github_export
import os
import sqlite3
import threading
import time
import urllib.parse
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE = Path(__file__).resolve().parent
DB = BASE / 'bugs.sqlite3'
LOG = BASE / 'inbox' / 'received.log'
STATUSES = ('Open', 'Investigating', 'Fixed', 'Retest', 'Closed')
PRIORITIES = ('Low', 'Medium', 'High')
KINDS = ('Bug', 'Idea')
GITHUB_REPOSITORY = ''  # Optional game-core repo, owner/repo, not the Bug Tracker's own repo.
CSRF = secrets.token_urlsafe(32)
# v48 keeps assets next to this script; no CDN/internet dependencies.
ASSETS = BASE / 'necrocore_assets'
# Customizable public dashboard name. Attribution is intentionally separate.
BRAND_NAME = 'NecroCore'
ATTRIBUTION_URL = 'https://github.com/necrosaro710/NecroCore-BugTracker'  # Official project credit URL.
STATIC_ASSETS = {
    '/assets/necrocore.css': ('necrocore.css', 'text/css; charset=utf-8'),
    '/assets/necrocore.js': ('necrocore.js', 'application/javascript; charset=utf-8'),
    '/assets/hero.jpg': ('hero.jpg', 'image/jpeg'),
    '/assets/citadel.jpg': ('citadel.jpg', 'image/jpeg'),
}


def esc(s):
    return html.escape(str(s if s is not None else ''), quote=True)


def footer_credit():
    credit = 'Powered by NecroCore Bug Tracker'
    if ATTRIBUTION_URL:
        return '<a href=\"{}\" target=\"_blank\" rel=\"noopener noreferrer\"><strong>{}</strong></a>'.format(esc(ATTRIBUTION_URL), credit)
    return '<strong>{}</strong>'.format(credit)

def brand_logo():
    '''Two-tone display name in the sidebar, safely escaped and readable.''' 
    name = BRAND_NAME.strip() or 'NecroCore'
    if name.casefold() == 'necrocore':
        first, second = 'NECRO', 'CORE'
    else:
        pieces = name.rsplit(' ', 1)
        first, second = (pieces[0], pieces[1]) if len(pieces) == 2 else (name, '')
    return esc(first.upper()) + ('<span>' + esc(second.upper()) + '</span>' if second else '') + '<small>BUG TRACKER</small>'


def connect():
    return sqlite3.connect(DB, timeout=10)


def init():
    (BASE / 'inbox').mkdir(exist_ok=True)
    with connect() as db:
        db.execute('CREATE TABLE IF NOT EXISTS reports (id INTEGER PRIMARY KEY, ext TEXT UNIQUE, char TEXT, realm TEXT, target TEXT, guid TEXT, typ TEXT, entry TEXT, map TEXT, x TEXT, y TEXT, zone TEXT, subzone TEXT, quest TEXT, notes TEXT, questlog TEXT, status TEXT DEFAULT "Open", created DATETIME DEFAULT CURRENT_TIMESTAMP)')
        # Schema migration for older 0.4.x databases: every existing report defaults to Medium.
        columns = {row[1] for row in db.execute('PRAGMA table_info(reports)')}
        if 'priority' not in columns:
            db.execute('ALTER TABLE reports ADD COLUMN priority TEXT NOT NULL DEFAULT "Medium"')
        if 'kind' not in columns:
            db.execute("ALTER TABLE reports ADD COLUMN kind TEXT NOT NULL DEFAULT 'Bug'")
        if 'issue_category' not in columns:
            db.execute("ALTER TABLE reports ADD COLUMN issue_category TEXT NOT NULL DEFAULT 'Auto'")
        if 'github_issue_url' not in columns:
            db.execute("ALTER TABLE reports ADD COLUMN github_issue_url TEXT NOT NULL DEFAULT ''")
        db.execute('CREATE TABLE IF NOT EXISTS deleted (ext TEXT PRIMARY KEY)')
        db.execute('CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY,value TEXT)')


def ingest():
    if not LOG.exists():
        return
    with connect() as db:
        r = db.execute('SELECT value FROM meta WHERE key="offset"').fetchone()
        offset = int(r[0]) if r else 0
        size = LOG.stat().st_size
        if size < offset:
            offset = 0
        with LOG.open('rb') as f:
            f.seek(offset)
            while True:
                beginning = f.tell()
                raw = f.readline()
                if not raw:
                    break
                if not raw.endswith(b'\n'):
                    offset = beginning
                    break
                offset = f.tell()
                try:
                    line = raw.decode('utf-8').rstrip('\r\n')
                    fields = line.split('|')
                    # 14 fields: original bug; 15: priority; 16: priority plus type Bug/Idea.
                    # Worldserver bridge passes client report content through unchanged.
                    if len(fields) not in (17, 18, 19) or fields[0] != 'NB2':
                        continue
                    rid, actual = fields[1:3]
                    data = [urllib.parse.unquote(x) for x in fields[3:]]
                    if len(data) not in (14, 15, 16):
                        continue
                    priority = data[14] if len(data) >= 15 else 'Medium'
                    if priority not in PRIORITIES:
                        priority = 'Medium'
                    kind = data[15] if len(data) == 16 else 'Bug'
                    if kind not in KINDS:
                        kind = 'Bug'
                    external = 'server-' + rid + '-' + actual
                    if db.execute('SELECT 1 FROM deleted WHERE ext=?', (external,)).fetchone():
                        continue
                    # Never trust the client-supplied character name; use the server-verified sender.
                    db.execute('''INSERT OR IGNORE INTO reports(ext,char,realm,target,guid,typ,entry,map,x,y,zone,subzone,quest,notes,questlog,priority,kind)
                                  VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', (external, actual, *data[1:14], priority, kind))
                except (ValueError, UnicodeError, sqlite3.Error) as e:
                    print('Record import error:', e)
        db.execute('INSERT INTO meta(key,value) VALUES("offset",?) ON CONFLICT(key) DO UPDATE SET value=excluded.value', (str(offset),))


def report_export(row):
    def val(key, fallback='Not captured'):
        value = row[key]
        return str(value).strip() if value is not None and str(value).strip() else fallback

    # The x/y values come from the player's zone map, not the NPC's world XYZ.
    pos_x, pos_y = val('x'), val('y')
    pos = f'{pos_x}%, {pos_y}%' if pos_x != 'Not captured' and pos_y != 'Not captured' else 'Not captured'
    player = val('char')
    realm = val('realm')
    if player == 'Not captured' and row['ext'] and str(row['ext']).startswith('seed-'):
        player = 'Manually preloaded report'
    external = str(row['ext'] or '')
    if external.startswith('manual-'):
        origin = 'Manually entered on server-hosted web dashboard'
        coordinate_label = 'Coordinates manually entered (map %, not verified NPC world XYZ): '
    elif external.startswith('seed-'):
        origin = 'Preloaded example / previously reported issue'
        coordinate_label = 'Player map coordinates (not NPC XYZ): '
    else:
        origin = 'Submitted from WoW game client via /idea' if row['kind'] == 'Idea' else 'Submitted from WoW game client via /bug'
        coordinate_label = 'Player map coordinates (not NPC XYZ): '
    lines = [
        BRAND_NAME.upper() + ' ' + ('IDEA' if row['kind'] == 'Idea' else 'BUG REPORT') + ' — #' + str(row['id']),
        'Project: ' + BRAND_NAME + ' / BfA 8.3.7',
        'Report source: ' + origin,
        'Category: ' + val('kind', 'Bug'),
        'Status: ' + val('status'),
        'Priority: ' + val('priority', 'Medium'),
        'Report recorded (UTC): ' + val('created'),
        'Submitted by character: ' + player,
        'Realm: ' + realm,
        '',
        'TARGET / NPC / GAME OBJECT',
        'Target name: ' + val('target'),
        'Target type: ' + val('typ'),
        'Target entry ID: ' + val('entry'),
        'Target GUID: ' + val('guid'),
        '',
        'LOCATION',
        'Zone: ' + val('zone'),
        'Subzone: ' + val('subzone'),
        'Map ID: ' + val('map'),
        coordinate_label + pos,
        '',
        'QUEST CONTEXT',
        'Related quest (entered by reporter; ID if supplied): ' + val('quest'),
        'Reporter quest-log snapshot (not NPC-offered quest list):',
        val('questlog'),
        '',
        'BUG DESCRIPTION / REPRODUCTION NOTES (VERBATIM)',
        val('notes', 'No notes supplied'),
        '',
        'WHAT I NEED HELP WITH',
        'Help me diagnose and repair this bug in my ' + BRAND_NAME + ' BfA 8.3.7 server.',
        'Use the details above as the evidence. Identify likely SQL, NPC/gameobject,',
        'quest-objective, script, or core issues. Distinguish verified IDs from assumptions.',
        'Give actionable verification steps and a safe fix; request missing data if needed.',
        'Core directory and database names are specific to the server installation.',
    ]
    return '\n'.join(lines) + '\n'


# Sort keys are strictly whitelisted; never accept SQL fragments from URL parameters.
SORT_COLUMNS = {
    'id': 'id',
    'created': 'created',
    'char': 'char COLLATE NOCASE',
    'target': 'target COLLATE NOCASE',
    'quest': 'quest COLLATE NOCASE',
    'zone': 'zone COLLATE NOCASE',
    'notes': 'notes COLLATE NOCASE',
    'status': 'status COLLATE NOCASE',
    # Custom severity order: High > Medium > Low, not alphabetical.
    'priority': "CASE priority WHEN 'High' THEN 3 WHEN 'Medium' THEN 2 WHEN 'Low' THEN 1 ELSE 0 END",
}
DEFAULT_SORT_DIRECTION = {'id': 'desc', 'created': 'desc', 'priority': 'desc'}
SORT_HEADINGS = (
    ('id', 'Report #'),
    ('created', 'Date submitted'),
    ('char', 'Submitted by'),
    ('target', 'Target / ID'),
    ('quest', 'Quest'),
    ('zone', 'Location'),
    ('notes', 'Notes'),
    ('status', 'Status'),
    ('priority', 'Priority'),
)


def sort_options(query):
    key = query.get('sort', ['id'])[0]
    if key not in SORT_COLUMNS:
        key = 'id'
    direction = query.get('dir', [DEFAULT_SORT_DIRECTION.get(key, 'asc')])[0].lower()
    if direction not in ('asc', 'desc'):
        direction = DEFAULT_SORT_DIRECTION.get(key, 'asc')
    return key, direction


def order_by(key, direction):
    # SQL fragments originate only from SORT_COLUMNS; direction is normalized.
    return f' ORDER BY {SORT_COLUMNS[key]} {direction.upper()}, id DESC'


def sorted_query_params(needle, status, priority_filter, sort_key, direction, kind):
    return urllib.parse.urlencode({'q': needle, 'status': status, 'priority': priority_filter,
                                   'sort': sort_key, 'dir': direction, 'kind': kind})


def filter_sql(query):
    """Closed tickets are exclusively visible through the dedicated Closed tab.

    Even a manually edited URL cannot make a closed ticket appear in normal
    Bugs, Ideas, or All views. Legacy links to ?kind=All&status=Closed remain
    supported and display the Closed tab.
    """
    needle = query.get('q', [''])[0][:120]
    status = query.get('status', ['All'])[0]
    priority = query.get('priority', ['All'])[0]
    kind = query.get('kind', ['Bug'])[0]
    if kind not in (*KINDS, 'All', 'Closed'):
        kind = 'Bug'
    if kind == 'All' and status == 'Closed':
        kind = 'Closed'  # old v48 Closed shortcut / saved link

    sql = ' FROM reports WHERE 1=1'
    args = []
    if kind == 'Closed':
        status = 'Closed'
        sql += " AND status='Closed'"
    else:
        sql += " AND COALESCE(status, 'Open')!='Closed'"
        if kind != 'All':
            sql += ' AND kind=?'
            args.append(kind)
        if status not in STATUSES or status == 'Closed':
            status = 'All'
        if status != 'All':
            sql += ' AND status=?'
            args.append(status)
    if needle:
        sql += ' AND (char LIKE ? OR target LIKE ? OR entry LIKE ? OR zone LIKE ? OR quest LIKE ? OR notes LIKE ?)'
        args += ['%' + needle + '%'] * 6
    if priority in PRIORITIES:
        sql += ' AND priority=?'
        args.append(priority)
    return sql, args, needle, status, priority, kind


# These are existing columns in the v0.4 database. No schema change is required.
MANUAL_FIELDS = {
    'char': ('Submitted by', 100),
    'realm': ('Realm', 100),
    'target': ('NPC / object name', 200),
    'typ': ('Target type', 60),
    'entry': ('NPC / object entry ID', 80),
    'guid': ('Target GUID (if known)', 200),
    'quest': ('Quest name / ID', 300),
    'zone': ('Zone', 200),
    'subzone': ('Subzone', 200),
    'map': ('Map ID', 80),
    'x': ('Player X map %', 40),
    'y': ('Player Y map %', 40),
    'questlog': ('Other quest context', 5000),
    'notes': ('Bug description / steps to reproduce', 10000),
    'status': ('Status', 25),
    'priority': ('Priority', 10),
    'kind': ('Category (Bug or Idea)', 4),
    'issue_category': ('GitHub issue category', 10),
}


def new_report_form(values=None, error=None):
    values = values or {}
    def val(key):
        return esc(values.get(key, 'Web dashboard' if key == 'char' else ''))
    def field(key, *, full=False, required=False, placeholder=''):
        title, max_len = MANUAL_FIELDS[key]
        attr = ' required' if required else ''
        css_class = 'field full' if full else 'field'
        hint = ' <span class="help">(optional)</span>' if not required else ''
        if key in ('notes', 'questlog'):
            control = (f'<textarea id="{key}" name="{key}" maxlength="{max_len}" '
                       f'rows="{8 if key == "notes" else 3}" placeholder="{esc(placeholder)}"{attr}>{val(key)}</textarea>')
        else:
            control = (f'<input id="{key}" name="{key}" type="text" maxlength="{max_len}" '
                       f'value="{val(key)}" placeholder="{esc(placeholder)}"{attr}>')
        return f'<div class="{css_class}"><label for="{key}">{esc(title)}{hint}</label>{control}</div>'
    out = '<h2>New report — add manually</h2><p>Reports saved here appear in the same list as those submitted with /bug.</p>'
    if error:
        out += '<p role="alert" class="error">' + esc(error) + '</p>'
    out += (f'<form method="post" action="/new" class="card">'
            f'<input type="hidden" name="csrf" value="{CSRF}">'
            '<h3>Problem</h3><div class="form-grid">')
    out += field('quest', placeholder='e.g. Recruitment (quest ID if known)')
    out += field('target', placeholder='e.g. Young Nightweb Spider')
    out += field('notes', full=True, required=True, placeholder='What is broken? What should happen instead? How can we reproduce it?')
    chosen_priority = values.get('priority', 'Medium')
    out += '<div class="field"><label for="priority">Priority</label><select id="priority" name="priority">'
    for priority in PRIORITIES:
        out += f'<option value="{priority}" {"selected" if chosen_priority == priority else ""}>{priority}</option>'
    out += '</select></div>'
    out += '<div class="field"><label for="issue_category">Issue category</label><select name="issue_category" id="issue_category">'
    for option in github_export.CATEGORIES:
        out += f'<option value="{esc(option)}" {"selected" if values.get("issue_category", "Auto") == option else ""}>{esc(option)}</option>'
    out += '</select></div>'
    out += '</div><h3>Target information</h3><div class="form-grid">'
    out += field('typ', placeholder='e.g. Creature, GameObject')
    out += field('entry', placeholder='Numeric entry ID, if known')
    out += field('guid', full=True)
    out += '</div><h3>Location</h3><div class="form-grid">'
    out += field('zone', placeholder='e.g. Deathknell')
    out += field('subzone')
    out += field('map') + field('x') + field('y')
    out += ('<div class="field full help">Coordinates here are manually entered player map percentages, '
            'not verified NPC world XYZ positions. Leave unknown fields blank.</div>')
    out += '</div><h3>Reporter and additional context</h3><div class="form-grid">'
    out += field('char') + field('realm')
    out += field('questlog', full=True, placeholder='Other quests involved, prerequisite quests, or related observations')
    out += '<input type="hidden" name="kind" value="Bug">'
    out += '</div><div class="actions" style="margin-top:18px"><button type="submit">Save report</button> '
    out += '<a href="/">Cancel</a></div>'
    out += '<p class="help">At least one of Quest or NPC / object name is needed; description is required.</p></form>'
    return out


def edit_report_form(report, error=None, values=None):
    """Edit all user-facing report fields, preserving the original report ID, source, and creation time."""
    if values is None:
        values = {key: report[key] or '' for key in MANUAL_FIELDS}

    def value(key):
        return esc(values.get(key, '') or '')

    def field(key, *, full=False, placeholder=''):
        title, max_len = MANUAL_FIELDS[key]
        group = 'field full' if full else 'field'
        if key in ('notes', 'questlog'):
            control = (f'<textarea id="edit-{key}" name="{key}" maxlength="{max_len}" '
                       f'rows="{9 if key == "notes" else 4}" '
                       f'placeholder="{esc(placeholder)}">{value(key)}</textarea>')
        else:
            control = (f'<input id="edit-{key}" name="{key}" type="text" '
                       f'maxlength="{max_len}" value="{value(key)}" '
                       f'placeholder="{esc(placeholder)}">')
        return f'<div class="{group}"><label for="edit-{key}">{esc(title)}</label>{control}</div>'

    ident = report['id']
    out = (f'<div class="card"><h2>Edit report #{ident}</h2>'
           '<p>Correct details from an in-game report or a manually created report. '
           'The original report number, source identifier, and creation date are preserved.</p>'
           f'<p><a href="/report/{ident}">Cancel and return to report</a></p></div>')
    if error:
        out += '<p role="alert" class="error">' + esc(error) + '</p>'
    out += (f'<form method="post" action="/edit/{ident}" class="card">'
            f'<input type="hidden" name="csrf" value="{CSRF}">'
            '<h3>Bug and quest details</h3><div class="form-grid">')
    out += field('quest', placeholder='Quest name and ID, if known')
    out += field('target', placeholder='NPC / GameObject / Item name')
    out += field('notes', full=True, placeholder='What is broken? Expected result? Steps to reproduce?')
    out += '</div><h3>Target identifiers</h3><div class="form-grid">'
    for key in ('typ', 'entry', 'guid'):
        out += field(key, full=key == 'guid')
    out += '</div><h3>Location</h3><div class="form-grid">'
    for key in ('zone', 'subzone', 'map', 'x', 'y'):
        out += field(key)
    out += ('</div><p class="help">These X/Y values are the player map percentages; '
            'do not substitute NPC server XYZ coordinates.</p>'
            '<h3>Reporter and quest context</h3><div class="form-grid">')
    for key in ('char', 'realm', 'questlog'):
        out += field(key, full=key == 'questlog')
    out += '</div><h3>Workflow</h3><div class="form-grid">'
    for key, choices in (('status', STATUSES), ('priority', PRIORITIES), ('kind', KINDS), ('issue_category', github_export.CATEGORIES)):
        out += f'<div class="field"><label for="edit-{key}">{esc(MANUAL_FIELDS[key][0])}</label>'
        out += f'<select id="edit-{key}" name="{key}">'
        for choice in choices:
            out += f'<option value="{esc(choice)}" {"selected" if values.get(key) == choice else ""}>{esc(choice)}</option>'
        out += '</select></div>'
    out += (f'</div><div class="actions" style="margin-top:20px">'
            '<button type="submit">Save all changes</button> '
            f'<a href="/report/{ident}">Cancel</a></div>'
            '<p class="help">Changes are saved on the server and included in the next Copy for ChatGPT export.</p>'
            '</form>')
    return out


def view_params(query, **updates):
    params = {'kind': query.get('kind',['Bug'])[0], 'q':query.get('q',[''])[0],
              'status': query.get('status',['All'])[0], 'priority':query.get('priority',['All'])[0],
              'sort':query.get('sort',['id'])[0], 'dir':query.get('dir',['desc'])[0]}
    if 'page' in query:
        params['page'] = query['page'][0]
    params.update(updates)
    # Changing tabs must not carry the prior tab's closed/open status filter.
    if params['kind'] == 'All' and params['status'] == 'Closed':
        params['kind'] = 'Closed'  # keep old v48 Closed bookmarks within archive
    if params['kind'] == 'Closed':
        params['status'] = 'Closed'
    elif params['status'] == 'Closed':
        params['status'] = 'All'
    return '/?' + urllib.parse.urlencode(params)


def human_title(report):
    # Prefer quest title, then target, or a concise description. No invented report titles.
    return (report['quest'] or report['target'] or (report['notes'] or '')[:75] or 'Untitled report').strip()


def nav_sidebar():
    try:
        with connect() as db:
            bugs = db.execute("SELECT COUNT(*) FROM reports WHERE kind='Bug' AND status!='Closed'").fetchone()[0]
            ideas = db.execute("SELECT COUNT(*) FROM reports WHERE kind='Idea' AND status!='Closed'").fetchone()[0]
            closed = db.execute("SELECT COUNT(*) FROM reports WHERE status='Closed'").fetchone()[0]
            total = db.execute("SELECT COUNT(*) FROM reports WHERE COALESCE(status,'Open')!='Closed'").fetchone()[0]
    except sqlite3.Error:
        bugs=ideas=closed=total=0
    return f'''<aside class="sidebar" aria-label="Main navigation">
        <a class="brand" href="/"><span class="brand-mark">☠</span><span class="brand-name">{brand_logo()}</span></a>
        <div class="sidebar-caption">WORKSPACE</div>
        <nav class="sidebar-nav">
        <a href="/" data-nav="home"><span>⌂</span> Dashboard</a>
        <a href="/?kind=Bug" data-nav="Bug"><span>✳</span> Bugs <em>{bugs}</em></a>
        <a href="/?kind=Idea" data-nav="Idea"><span>♧</span> Ideas <em>{ideas}</em></a>
        <a href="/?kind=All" data-nav="All"><span>▤</span> All Tickets <em>{total}</em></a>
        <a href="/?kind=Closed" data-nav="Closed"><span>✓</span> Closed <em>{closed}</em></a>
        </nav>
        <div class="side-art" role="img" aria-label="Green-lit gothic fortress"></div>
        <div class="sidebar-foot"><span class="online-dot"></span> {esc(BRAND_NAME)} <small>BfA 8.3.7 · LAN Dashboard</small></div>
        </aside>'''


def page(contents):
    title = esc(BRAND_NAME)
    return (f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
        <title>{title} · Bug Tracker</title><link rel="stylesheet" href="/assets/necrocore.css"><script defer src="/assets/necrocore.js"></script></head>
        <body><div class="site-shell">''' + nav_sidebar() + f'''<div class="body-column">
        <header class="topbar"><div class="top-title"><span class="eyebrow">{title} REALM</span><strong>Issue Control Center</strong></div>
        <div class="top-search">☠ &nbsp; BATTLE FOR AZEROTH <span>8.3.7</span></div>
        <span class="network-label"><i class="online-dot"></i> Local network</span></header>
        <main class="workspace" id="main-content">''' + contents + f'''</main>
        <footer class="site-footer">{footer_credit()} <span>Reports stored locally on your server · Timestamps: UTC</span></footer>
        </div></div></body></html>''').encode('utf-8')


def render_dashboard(query):
    sql, args, needle, status, priority_filter, kind = filter_sql(query)
    sort_key, direction = sort_options(query)
    raw_page=query.get('page',['1'])[0]
    try: page_number=max(1,min(100000,int(raw_page)))
    except ValueError: page_number=1
    PAGE_SIZE=35
    with connect() as db:
        db.row_factory=sqlite3.Row
        all_count=db.execute("SELECT COUNT(*) FROM reports WHERE COALESCE(status,'Open')!='Closed'").fetchone()[0]
        bug_count=db.execute("SELECT COUNT(*) FROM reports WHERE kind='Bug' AND status!='Closed'").fetchone()[0]
        idea_count=db.execute("SELECT COUNT(*) FROM reports WHERE kind='Idea' AND status!='Closed'").fetchone()[0]
        closed_count=db.execute("SELECT COUNT(*) FROM reports WHERE status='Closed'").fetchone()[0]
        in_view=db.execute('SELECT COUNT(*)' + sql,args).fetchone()[0]
        page_count=max(1,(in_view+PAGE_SIZE-1)//PAGE_SIZE)
        page_number=min(page_number,page_count)
        rows=db.execute('SELECT *'+sql+order_by(sort_key,direction)+' LIMIT ? OFFSET ?',(*args,PAGE_SIZE,(page_number-1)*PAGE_SIZE)).fetchall()
        request_selected=query.get('selected',[''])[0]
        selected=None
        if request_selected.isdecimal():
            # A forged selected=<id> must not leak an archived ticket into active views.
            selected=db.execute('SELECT *' + sql + ' AND id=?', (*args,int(request_selected))).fetchone()
        if selected is None and rows: selected=rows[0]
    def link(**updates): return esc(view_params(query,**updates))
    out=f'''<section class="hero"><div class="hero-copy"><div class="eyebrow green">THE REALM NEVER SLEEPS</div>
      <h1>Welcome to <span>{esc(BRAND_NAME)}</span></h1><p>Review bugs, organize ideas, and keep Azeroth running.</p></div>
      <div class="hero-sign">⚔ <span>BATTLE FOR AZEROTH</span> ⚔<small>YOUR REALM. YOUR LEGACY.</small></div></section>'''
    out += (f'<section class="stat-grid" aria-label="Ticket summary">'
        f'<a class="stat-card" href="/?kind=Bug"><div class="stat-icon bug-icon">✳</div><div><strong>{bug_count}</strong><small>Active Bugs</small></div></a>'
        f'<a class="stat-card" href="/?kind=Idea"><div class="stat-icon idea-icon">♧</div><div><strong>{idea_count}</strong><small>Active Ideas</small></div></a>'
        f'<a class="stat-card" href="/?kind=Closed"><div class="stat-icon fixed-icon">✓</div><div><strong>{closed_count}</strong><small>Closed Tickets</small></div></a>'
        f'<a class="stat-card" href="/?kind=All"><div class="stat-icon total-icon">▤</div><div><strong>{all_count}</strong><small>Active Tickets</small></div></a></section>')
    heading = 'Closed Tickets' if kind == 'Closed' else 'Tickets'
    out+=f'<section class="desk"><div class="desk-main"><div class="desk-heading"><div class="section-heading"><div class="eyebrow">REPORT MANAGEMENT</div><h2>{heading}</h2></div><a class="btn primary" href="/new">＋ New Bug</a></div>'
    out+='<nav class="category-tabs" aria-label="Ticket categories">'
    for cat,label,icon in [('Bug','Bugs','✳'),('Idea','Ideas','♧'),('All','All Tickets','▤'),('Closed','Closed','✓')]:
        out+=f'<a class="{("active" if kind==cat else "")}" href="{link(kind=cat,page=1,selected="")}"><span>{icon}</span> {label}</a>'
    out+='</nav>'
    if query.get('notice',[''])[0]=='deleted': out+='<p class="notice" role="status">Selected reports deleted. Their original import IDs are protected from re-import.</p>'
    if query.get('notice',[''])[0]=='moved': out+='<p class="notice" role="status">Category updated. Closed reports stay in Closed until reopened.</p>'
    if query.get('notice',[''])[0]=='reopened': out+='<p class="notice" role="status">Selected tickets reopened and returned to their Bugs or Ideas tab.</p>'
    out+='<form method="get" action="/" class="filters"><input type="hidden" name="kind" value="'+esc(kind)+'"><input type="hidden" name="sort" value="'+esc(sort_key)+'"><input type="hidden" name="dir" value="'+esc(direction)+'">'
    out+='<label class="search-field"><span>⌕</span><input name="q" aria-label="Search reports" placeholder="Search tickets, characters, zones..." value="'+esc(needle)+'"></label>'
    if kind == 'Closed':
        out+='<select aria-label="Status: Closed only" disabled><option>Closed only</option></select>'
    else:
        out+='<select aria-label="Filter by status" name="status">'
        for option in ('All', *(v for v in STATUSES if v != 'Closed')):
            out+=f'<option value="{esc(option)}" {("selected" if status==option else "")}>{esc(option)}</option>'
        out+='</select>'
    for key,options,chosen in [('priority',('All',*PRIORITIES),priority_filter)]:
        out+='<select aria-label="Filter by '+key+'" name="'+key+'">'
        for option in options: out+=f'<option value="{esc(option)}" {("selected" if chosen==option else "")}>{esc(option)}</option>'
        out+='</select>'
    out+='<button class="btn subtle" type="submit">Filter</button></form>'
    out+=f'<form id="bulk-form" method="post" action="/bulk"><input type="hidden" name="csrf" value="{esc(CSRF)}"><input type="hidden" name="confirm_delete" id="confirm-delete" value=""><input type="hidden" name="return_to" value="{link(selected="",page=page_number)}">'
    out+='''<div class="bulk-bar"><div class="bulk-caption"><span>▣</span> BULK ACTIONS <b id="selected-count">0 selected</b></div>
        <button class="btn danger-outline" type="submit" name="bulk_action" value="delete">⌫ Delete Selected</button>
        <button class="btn green-outline" type="submit" name="bulk_action" value="Idea">♧ Move to Ideas</button>
        <button class="btn green-outline" type="submit" name="bulk_action" value="Bug">✳ Move to Bugs</button>'''
    if kind == 'Closed':
        out+='<button class="btn green-outline" type="submit" name="bulk_action" value="reopen">↻ Reopen Selected</button>'
    out+='</div><div class="table-wrap"><table class="ticket-table"><thead><tr><th><input id="select-all" type="checkbox" aria-label="Select all visible reports" title="Select all on this page"></th>'
    for key,label in [('id','ID'),('quest','Title'),('priority','Priority'),('status','Status'),('char','Submitted By'),('created','Date')]:
        nxt='desc' if sort_key==key and direction=='asc' else 'asc' if sort_key==key else DEFAULT_SORT_DIRECTION.get(key,'asc')
        out+=f'<th><a href="{link(sort=key,dir=nxt,page=1,selected="")}">{label} {("↓" if direction=="desc" else "↑") if sort_key==key else ""}</a></th>'
    out+='</tr></thead><tbody>'
    if not rows: out+='<tr><td colspan="7" class="empty-state">No reports match these filters. Try a different search.</td></tr>'
    for row in rows:
        ident=row['id']
        is_selected=selected and selected['id']==ident
        selected_link=link(selected=ident,page=page_number)
        submitted=(f'<time data-utc="{esc(row["created"] or "")}">{esc(row["created"] or "Unknown")}</time>')
        priority=esc(row['priority'] or 'Medium')
        stat=esc(row['status'] or 'Open')
        category=esc(row['kind'] or 'Bug')
        out+=(f'<tr class="ticket-row {("focused-row" if is_selected else "")}" data-report="{ident}">'
              f'<td><input name="ids" value="{ident}" type="checkbox" class="row-check" aria-label="Select report #{ident}"></td>'
              f'<td><a class="ticket-id" href="{selected_link}">#{ident}</a></td>'
              f'<td class="ticket-title"><a href="{selected_link}">{esc(human_title(row))}</a> <small>• {esc(github_export.classify(row))}</small><small>{esc((row["notes"] or "")[:100] or (row["zone"] or ""))}</small></td>'
              f'<td><span class="pill priority-{priority.lower()}">◆ {priority}</span></td>'
              f'<td><span class="pill status-{stat.lower().replace(" ","-")}">● {stat}</span></td>'
              f'<td class="submitter"><span class="round-avatar">{esc((row["char"] or "?")[:1].upper())}</span>{esc(row["char"] or "Unknown")}</td>'
              f'<td class="datecol">{submitted}</td></tr>')
    out+='</tbody></table></div></form>'
    start=(page_number-1)*PAGE_SIZE + (1 if in_view else 0)
    end=min(page_number*PAGE_SIZE,in_view)
    out+=f'<div class="table-foot"><span>Showing <b>{start}–{end}</b> of <b>{in_view}</b> reports</span><div class="pagination">'
    if page_number>1:out+=f'<a href="{link(page=page_number-1,selected="")}" aria-label="Previous page">← Previous</a>'
    out+=f'<span>Page {page_number} of {page_count}</span>'
    if page_number<page_count:out+=f'<a href="{link(page=page_number+1,selected="")}" aria-label="Next page">Next →</a>'
    out += """</div></div><div class="export-bar"><button type="button" class="text-action" onclick="loadAndCopy('/export/selection'+location.search,this)">↗ Copy filtered reports for ChatGPT</button><span id="copy-feedback" role="status"></span></div><div id="export-target"></div></div>"""
    # Right-hand inspector is read-only to avoid accidental edits; full editor remains functional.
    out+='<aside class="detail-pane">'
    if selected:
        rid=selected['id']; skind=esc(selected['kind'] or 'Bug'); title=esc(human_title(selected));
        out+=f'<div class="detail-head"><div class="eyebrow green">SELECTED REPORT</div><strong class="detail-no">#{rid}</strong><h2>{title}</h2><span class="pill category-pill">{skind}</span> <span class="pill priority-{esc((selected["priority"] or "Medium").lower())}">◆ {esc(selected["priority"] or "Medium")}</span></div>'
        out+='<div class="detail-meta">'
        for label,value in [('Submitted By',selected['char'] or 'Unknown'),('Date Submitted',selected['created'] or 'Unknown'),('Zone / Area',selected['zone'] or 'Not recorded'),('Subzone',selected['subzone'] or 'Not recorded'),('Target ID',selected['entry'] or 'Not recorded'),('Quest',selected['quest'] or 'Not recorded'),('Issue category',github_export.classify(selected))]:
            out+=f'<div class="meta-item"><span>{label}</span><strong>{esc(value)}</strong></div>'
        out+='</div>'
        out+=f'''<div class="detail-workflow"><div><span>Status</span><strong class="pill status-{esc((selected['status'] or 'Open').lower())}">● {esc(selected['status'] or 'Open')}</strong></div>
                    <div><span>Priority</span><strong class="pill priority-{esc((selected['priority'] or 'Medium').lower())}">◆ {esc(selected['priority'] or 'Medium')}</strong></div></div>'''
        out+=f'<div class="detail-notes"><h3>≡ Description / Notes</h3><div class="notes-body">{esc(selected["notes"] or "No description provided.")}</div></div>'
        if selected['questlog']:
            out+=f'<div class="detail-notes"><h3>▤ Quest Context</h3><div class="notes-body">{esc(selected["questlog"])}</div></div>'
        out+=f"""<div class="detail-actions"><a class="btn green-outline" href="/report/{rid}">View &amp; Update</a><a class="btn subtle" href="/edit/{rid}">Edit</a><a class="btn green-outline" href="/github/{rid}">GitHub Issue</a><button class="btn subtle" type="button" onclick="loadAndCopy('/export/{rid}',this)">Copy</button></div>"""
        if selected['github_issue_url']:
            out+=f'<p class="help">GitHub: <a href="{esc(selected["github_issue_url"])}" target="_blank" rel="noopener noreferrer">View linked issue</a></p>'
    else:
        out+='<div class="empty-inspector"><div>☠</div><h2>No report selected</h2><p>Choose a report from the list to inspect its details.</p></div>'
    out+='</aside></section>'
    return out

class App(BaseHTTPRequestHandler):
    def respond(self, content, status=200):
        data = page(content)
        self.send_response(status)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(data)

    def respond_text(self, content):
        data = content.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.send_header('Content-Disposition', 'inline; filename="Bug_Tracker_Report.txt"')
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(data)

    def redirect(self, to):
        self.send_response(303)
        self.send_header('Location', to)
        self.end_headers()

    def do_GET(self):
        path = urllib.parse.urlsplit(self.path)
        if path.path in STATIC_ASSETS:
            name, mime = STATIC_ASSETS[path.path]
            file_path = ASSETS / name
            if not file_path.is_file():
                return self.respond('Asset not found', 404)
            data = file_path.read_bytes()
            self.send_response(200)
            self.send_header('Content-Type', mime)
            self.send_header('Content-Length', str(len(data)))
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Cache-Control', 'public, max-age=3600')
            self.end_headers()
            self.wfile.write(data)
            return
        q = urllib.parse.parse_qs(path.query)

        if path.path.startswith('/github/'):
            try:
                ident = int(path.path[len('/github/'):])
            except ValueError:
                return self.respond('Not found', 404)
            with connect() as db:
                db.row_factory = sqlite3.Row
                r = db.execute('SELECT * FROM reports WHERE id=?', (ident,)).fetchone()
            if not r:
                return self.respond('Not found', 404)
            repo = github_export.valid_repo(q.get('repo', [GITHUB_REPOSITORY])[0])
            include_reporter = q.get('reporter', [''])[0] == 'yes'
            issue_title = github_export.title(r)
            issue_body = github_export.body(r, BRAND_NAME, include_reporter)
            draft_url, prefilled = github_export.draft_link(repo, issue_title, issue_body)
            out = (f'<div class="card"><h2>GitHub issue review — ticket #{ident}</h2>'
                   '<p>No issue is sent automatically. Check the details, then finish creating it on GitHub.</p>'
                   f'<p><a href="/report/{ident}">← Return to ticket</a></p>'
                   '<form method="get" class="form-grid">'
                   f'<div class="field full"><label for="repo">Destination GitHub repo (owner/repo)</label>'
                   f'<input id="repo" name="repo" value="{esc(repo)}" placeholder="your-account/your-game-core" maxlength="140" required></div>'
                   f'<div class="field full"><label><input type="checkbox" name="reporter" value="yes" {"checked" if include_reporter else ""}> Include character name and realm (off by default)</label></div>'
                   '<div class="actions"><button type="submit">Update preview</button></div></form>'
                   f'<h3>Issue title</h3><p><strong>{esc(issue_title)}</strong></p>'
                   f'<p>Detected category: <strong>{esc(github_export.classify(r))}</strong> '
                   f'(<a href="/edit/{ident}">change category</a>)</p>'
                   f'<label for="github-body">Issue description (review before making public)</label>'
                   f'<textarea class="export-text" id="github-body" readonly>{esc(issue_body)}</textarea>'
                   '<p>Personal data is not included by default. Check the destination repository carefully.</p>')
            if not repo:
                out += '<p class="notice">Enter your GAME CORE project repository above, then click Update preview. Do not send gameplay bugs to the Bug Tracker software repository.</p>'
            else:
                if not prefilled:
                    out += '<p class="notice">This report is too long to fit safely in a GitHub URL. Copy the full description below and paste it into the GitHub draft.</p>'
                out += (f'<div class="actions"><a class="btn primary" href="{esc(draft_url)}" target="_blank" rel="noopener noreferrer">'
                        + ('Open pre-filled GitHub draft' if prefilled else 'Open GitHub draft (paste description)')
                        + '</a> <button type="button" class="btn subtle" onclick="copyGithubDescription(this)">Copy description</button></div>')
            linked = r['github_issue_url'] or ''
            if linked:
                out += f'<p>Already linked: <a href="{esc(linked)}" target="_blank" rel="noopener noreferrer">{esc(linked)}</a></p>'
            out += (f'<form method="post" action="/github/{ident}/link">'
                    f'<input type="hidden" name="csrf" value="{esc(CSRF)}">'
                    '<p><label for="github_issue_url">After submitting on GitHub, paste its issue URL here to link it to this ticket:</label></p>'
                    f'<input id="github_issue_url" name="github_issue_url" type="url" value="{esc(linked)}" placeholder="https://github.com/owner/repo/issues/123" style="width:100%;max-width:640px" maxlength="400">'
                    '<div class="actions"><button type="submit">Save GitHub issue link</button></div>'
                    '<p class="help">The linked issue can be opened later from the ticket. Leave blank to clear the existing link.</p></form></div>')
            return self.respond(out)

        if path.path == '/new':
            return self.respond(new_report_form())

        if path.path.startswith('/edit/'):
            try:
                ident = int(path.path[len('/edit/'):])
            except ValueError:
                return self.respond('Not found', 404)
            with connect() as db:
                db.row_factory = sqlite3.Row
                r = db.execute('SELECT * FROM reports WHERE id=?', (ident,)).fetchone()
            if not r:
                return self.respond('Not found', 404)
            return self.respond(edit_report_form(r))

        if path.path == '/export/selection':
            sql, args, _, _, _, _ = filter_sql(q)
            sort_key, direction = sort_options(q)
            with connect() as db:
                db.row_factory = sqlite3.Row
                reports = db.execute('SELECT *' + sql + order_by(sort_key, direction) + ' LIMIT 25', args).fetchall()
            if not reports:
                return self.respond_text('No reports match the current filters.\n')
            return self.respond_text('\n\n' + ('=' * 60 + '\n\n').join(report_export(r) for r in reports))

        if path.path.startswith('/export/'):
            try:
                ident = int(path.path[len('/export/'):])
            except ValueError:
                return self.respond('Not found', 404)
            with connect() as db:
                db.row_factory = sqlite3.Row
                r = db.execute('SELECT * FROM reports WHERE id=?', (ident,)).fetchone()
            if not r:
                return self.respond('Not found', 404)
            return self.respond_text(report_export(r))

        if path.path == '/':
            return self.respond(render_dashboard(q))

        if path.path.startswith('/report/'):
            try:
                ident = int(path.path[len('/report/'):])
            except ValueError:
                return self.respond('Not found', 404)
            with connect() as db:
                db.row_factory = sqlite3.Row
                r = db.execute('SELECT * FROM reports WHERE id=?', (ident,)).fetchone()
            if not r:
                return self.respond('Not found', 404)
            saved = q.get('saved', [''])[0] == '1'
            out = (f'<div class="card"><h2>{esc(r["kind"])} #{ident}: {esc(r["target"])}</h2>'
                   + ('<p class="success" role="status">Changes saved successfully.</p>' if saved else '')
                   + '<div class="actions">'
                   + f'<a class="button-link" href="/edit/{ident}">Edit report</a>'
                   + f'<a class="button-link" href="/github/{ident}">Review GitHub issue</a>'
                   + f'<button type="button" onclick="copyCurrentReport()">Copy for ChatGPT</button>'
                   f'<a href="/export/{ident}" target="_blank" rel="noopener">View plain-text report</a>'
                   '<span id="copy-feedback" class="feedback" role="status" aria-live="polite"></span></div>')
            if r['github_issue_url']:
                out += f'<p><b>GitHub issue:</b> <a href="{esc(r["github_issue_url"])}" target="_blank" rel="noopener noreferrer">{esc(r["github_issue_url"])}</a></p>'
            for k in ('kind', 'created', 'char', 'realm', 'priority', 'issue_category', 'guid', 'typ', 'entry', 'map', 'x', 'y', 'zone', 'subzone', 'quest', 'questlog'):
                out += f'<p><b>{esc(k)}:</b> {esc(r[k])}</p>'
            out += ('</div><div class="card"><h3>Ready-to-paste report</h3>'
                    '<p>This includes all saved details. If copy is blocked, select this text and press Ctrl+C.</p>'
                    '<textarea id="chatgpt-export" class="export-text" readonly>' + esc(report_export(r)) + '</textarea></div>'
                    f'<form class="card" method="post"><input type="hidden" name="csrf" value="{CSRF}">'
                    '<label>Notes</label><p><textarea name="notes">' + esc(r['notes']) + '</textarea></p>'
                    '<select name="status">')
            for s in STATUSES:
                out += f'<option value="{s}" {"selected" if s == r["status"] else ""}>{s}</option>'
            out += '</select> <label for="priority-detail">Priority</label> <select id="priority-detail" name="priority">'
            for value in PRIORITIES:
                out += f'<option value="{value}" {"selected" if r["priority"] == value else ""}>{value}</option>'
            out += ('</select> <button name="action" value="save">Save changes</button> '
                    '<button name="action" value="delete" class="danger" '
                    'onclick="return confirm(\'Permanently delete this bug report?\')">Delete report</button></form>'
                    '<small>Save note edits before copying so the exported report includes the latest text.</small>')
            return self.respond(out)
        return self.respond('Not found', 404)

    def do_POST(self):
        path = urllib.parse.urlsplit(self.path).path
        if not (path.startswith('/github/') and path.endswith('/link')) and path != '/new' and path != '/bulk' and not path.startswith('/report/') and not path.startswith('/priority/') and not path.startswith('/edit/'):
            return self.respond('Not found', 404)
        try:
            n = int(self.headers.get('Content-Length', '0'))
        except ValueError:
            return self.respond('Bad request', 400)
        if n < 0 or n > 65536:
            return self.respond('Too large', 413)
        fields = urllib.parse.parse_qs(self.rfile.read(n).decode('utf-8', errors='replace'), keep_blank_values=True)
        if fields.get('csrf', [''])[0] != CSRF:
            return self.respond('Invalid form token', 403)
        if path.startswith('/github/') and path.endswith('/link'):
            try:
                ident = int(path[len('/github/'):-len('/link')])
            except ValueError:
                return self.respond('Not found', 404)
            requested = fields.get('github_issue_url', [''])[0].strip()
            issue_url = github_export.valid_issue_url(requested) if requested else ''
            if requested and not issue_url:
                return self.respond('Enter a valid https://github.com/owner/repo/issues/123 URL.', 400)
            with connect() as db:
                changed = db.execute('UPDATE reports SET github_issue_url=? WHERE id=?', (issue_url, ident)).rowcount
            if not changed:
                return self.respond('Not found', 404)
            return self.redirect('/github/' + str(ident))

        if path == '/bulk':
            action = fields.get('bulk_action', [''])[0]
            if action not in ('delete', 'Bug', 'Idea', 'reopen'):
                return self.respond('Invalid bulk operation', 400)
            ids_raw = fields.get('ids', [])
            if not ids_raw or len(ids_raw) > 35 or any(not x.isdecimal() for x in ids_raw):
                return self.respond('Select up to 35 valid report IDs from this page.', 400)
            ids = list(dict.fromkeys(int(x) for x in ids_raw))
            if not ids or any(x <= 0 for x in ids):
                return self.respond('Invalid report IDs', 400)
            if action == 'delete' and fields.get('confirm_delete', [''])[0] != 'YES':
                return self.respond('Deletion not confirmed', 400)
            placeholders = ','.join('?' for _ in ids)
            with connect() as db:
                selected = db.execute('SELECT id,ext,status FROM reports WHERE id IN (' + placeholders + ')', ids).fetchall()
                if len(selected) != len(ids):
                    return self.respond('One or more selected reports no longer exist. Refresh and retry.', 409)
                if action == 'delete':
                    # Keep tombstones so imported reports are not recreated by log ingest.
                    db.executemany('INSERT OR IGNORE INTO deleted(ext) VALUES(?)', [(ext,) for _, ext, _ in selected if ext])
                    db.execute('DELETE FROM reports WHERE id IN (' + placeholders + ')', ids)
                elif action == 'reopen':
                    if any(current_status != 'Closed' for _, _, current_status in selected):
                        return self.respond('Only closed tickets can be reopened.', 409)
                    db.execute('UPDATE reports SET status=? WHERE id IN (' + placeholders + ')', ('Open', *ids))
                else:
                    # Moving a closed ticket changes its category but not its archive status.
                    db.execute('UPDATE reports SET kind=? WHERE id IN (' + placeholders + ')', (action, *ids))
            back = fields.get('return_to', ['/'])[0]
            if back != '/' and not (back.startswith('/?') and len(back) < 1000):
                back = '/'
            # Do not pass untrusted redirect URLs. Add a simple status message.
            separator = '&' if '?' in back else '?'
            return self.redirect(back + separator + 'notice=' + ('deleted' if action == 'delete' else 'reopened' if action == 'reopen' else 'moved'))
        if path.startswith('/priority/'):
            try:
                ident = int(path[len('/priority/'):])
            except ValueError:
                return self.respond('Bad request', 400)
            priority = fields.get('priority', [''])[0]
            if priority not in PRIORITIES:
                return self.respond('Bad priority', 400)
            with connect() as db:
                found = db.execute('UPDATE reports SET priority=? WHERE id=?', (priority, ident)).rowcount
            if not found:
                return self.respond('Not found', 404)
            return_to = fields.get('return_to', ['/'])[0]
            # Never redirect to a different host or non-list page.
            if return_to != '/' and not (return_to.startswith('/?') and len(return_to) < 1000):
                return_to = '/'
            return self.redirect(return_to)
        if path.startswith('/edit/'):
            try:
                ident = int(path[len('/edit/'):])
            except ValueError:
                return self.respond('Bad request', 400)
            with connect() as db:
                db.row_factory = sqlite3.Row
                original = db.execute('SELECT * FROM reports WHERE id=?', (ident,)).fetchone()
                if original is None:
                    return self.respond('Not found', 404)
                # All user-facing fields must be present. Do not accidentally blank
                # existing records if a partial form is submitted.
                if any(k not in fields for k in MANUAL_FIELDS):
                    return self.respond('Incomplete report edit form', 400)
                values = {key: fields[key][0].strip() for key in MANUAL_FIELDS}
                for key, (description, limit) in MANUAL_FIELDS.items():
                    if len(values[key]) > limit:
                        return self.respond(edit_report_form(original, f'{description} is too long.', values), 400)
                if values['status'] not in STATUSES:
                    return self.respond(edit_report_form(original, 'Invalid status.', values), 400)
                if values['priority'] not in PRIORITIES:
                    return self.respond(edit_report_form(original, 'Invalid priority.', values), 400)
                if values['kind'] not in KINDS:
                    return self.respond(edit_report_form(original, 'Invalid category.', values), 400)
                if values['issue_category'] not in github_export.CATEGORIES:
                    return self.respond(edit_report_form(original, 'Invalid issue category.', values), 400)
                # Only whitelisted column names, drawn from MANUAL_FIELDS.
                cols = tuple(MANUAL_FIELDS)
                set_clause = ', '.join(f'"{key}"=?' for key in cols)
                db.execute('UPDATE reports SET ' + set_clause + ' WHERE id=?',
                           (*[values[key] for key in cols], ident))
            return self.redirect('/report/' + str(ident) + '?saved=1')
        if path == '/new':
            values = {key: fields.get(key, [''])[0].strip() for key in MANUAL_FIELDS if key not in ('status', 'priority', 'kind', 'issue_category')}
            values['status'] = 'Open'
            values['priority'] = fields.get('priority', ['Medium'])[0]
            values['kind'] = 'Bug'  # manual form submits bugs; category can be changed in Edit
            values['issue_category'] = fields.get('issue_category', ['Auto'])[0]
            if values['priority'] not in PRIORITIES:
                return self.respond('Bad priority', 400)
            if values['issue_category'] not in github_export.CATEGORIES:
                return self.respond('Bad issue category', 400)
            for key, (description, limit) in MANUAL_FIELDS.items():
                if len(values.get(key, '')) > limit:
                    return self.respond(new_report_form(values, f'{description} is too long.'), 400)
            if not values['notes']:
                return self.respond(new_report_form(values, 'Please enter what is broken in the description.'), 400)
            if not (values['target'] or values['quest']):
                return self.respond(new_report_form(values, 'Please enter a quest or NPC / object name.'), 400)
            reporter = values['char'] or 'Web dashboard'
            with connect() as db:
                cursor = db.execute('''INSERT INTO reports
                    (ext, char, realm, target, guid, typ, entry, map, x, y, zone, subzone, quest, notes, questlog, status, priority)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    ('manual-' + secrets.token_hex(16), reporter, values['realm'], values['target'],
                     values['guid'], values['typ'], values['entry'], values['map'], values['x'], values['y'],
                     values['zone'], values['subzone'], values['quest'], values['notes'], values['questlog'], 'Open', values['priority']))
                report_id = cursor.lastrowid
                db.execute('UPDATE reports SET issue_category=? WHERE id=?', (values['issue_category'], report_id))
            return self.redirect('/report/' + str(report_id))
        try:
            ident = int(path[len('/report/'):])
        except ValueError:
            return self.respond('Bad request', 400)
        with connect() as db:
            if fields.get('action', [''])[0] == 'delete':
                row = db.execute('SELECT ext FROM reports WHERE id=?', (ident,)).fetchone()
                if row:
                    db.execute('INSERT OR IGNORE INTO deleted(ext) VALUES(?)', (row[0],))
                    db.execute('DELETE FROM reports WHERE id=?', (ident,))
                return self.redirect('/')
            status = fields.get('status', ['Open'])[0]
            if status not in STATUSES:
                return self.respond('Bad status', 400)
            priority = fields.get('priority', ['Medium'])[0]
            if priority not in PRIORITIES:
                return self.respond('Bad priority', 400)
            db.execute('UPDATE reports SET notes=?,status=?,priority=? WHERE id=?',
                       (fields.get('notes', [''])[0][:10000], status, priority, ident))
        return self.redirect('/report/' + str(ident))


def loop():
    while True:
        try:
            ingest()
        except Exception as e:
            print('Import error:', e)
        time.sleep(2)


if __name__ == '__main__':
    init()
    ingest()
    threading.Thread(target=loop, daemon=True).start()
    print('Run this dashboard with Start_Dashboard.cmd or launch_dashboard.py')
