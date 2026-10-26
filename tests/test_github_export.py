"""v1.1 offline GitHub integration tests (never sends requests to github.com)."""
import json
import re
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit, urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT/'web'))
import github_export


def free_port():
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


class GithubExportTests(unittest.TestCase):
    def test_helpers(self):
        r = {'id': 42, 'kind': 'Bug', 'issue_category': 'Auto', 'quest': 'Treasure Hunting', 'target': 'Treasure',
             'zone': 'Westfall', 'notes': 'Questgiver ignores me', 'typ': 'Creature', 'priority': 'High',
             'char': 'PrivateCharacter', 'realm': 'My Private Realm', 'subzone':'', 'entry':'123', 'map':'1',
             'x':'10', 'y':'20', 'questlog':''}
        self.assertEqual(github_export.title(r), '[Quest] Westfall: Treasure Hunting')
        text=github_export.body(r)
        self.assertNotIn('PrivateCharacter', text)
        self.assertIn('Target entry ID: 123', text)
        self.assertIn('PrivateCharacter', github_export.body(r, include_reporter=True))
        r['issue_category']='Spell'
        self.assertEqual(github_export.title(r), '[Spell] Westfall: Treasure Hunting')
        r['issue_category']='Auto'; r['quest']=''
        self.assertEqual(github_export.classify(r),'NPC')
        self.assertEqual(github_export.valid_repo('MyOrg/GameCore'), 'MyOrg/GameCore')
        for value in ('https://github.com/MyOrg/GameCore', '//evil.com', 'good/../evil', 'x/y?hack=1', ''):
            self.assertEqual(github_export.valid_repo(value),'')
        self.assertEqual(github_export.valid_issue_url('https://github.com/org/core/issues/42'), 'https://github.com/org/core/issues/42')
        for value in ('https://github.com/evil/core/pulls/42','https://github.com.evil.com/org/core/issues/3',
                      'javascript:alert(1)', 'https://github.com/org/core/issues/12?x=1', 'http://github.com/o/r/issues/3'):
            self.assertEqual(github_export.valid_issue_url(value), '')
        u, prefilled=github_export.draft_link('org/core', 'Some title', 'A body')
        self.assertTrue(prefilled)
        self.assertEqual(parse_qs(urlsplit(u).query), {'title':['Some title'],'body':['A body']})
        long, prefilled=github_export.draft_link('org/core', 'Some title', 'long'*5000)
        self.assertFalse(prefilled)
        self.assertNotIn('body=',long)

    def test_dashboard(self):
        with tempfile.TemporaryDirectory(prefix='necrob_v11_') as temp:
            web=Path(temp)/'web';shutil.copytree(ROOT/'web',web)
            port=free_port()
            (web/'config.json').write_text(json.dumps(dict(server_name='Test Realm', bind_address='127.0.0.1',
                port=port, data_directory='.', inbox_path='inbox/received.log', admin_login=False,
                github_issue_repo='team/bfa-core')))
            # Pre-v1.1 schema & existing ticket are kept and upgraded in place.
            with sqlite3.connect(web/'bugs.sqlite3') as db:
                db.execute('''CREATE TABLE reports (id INTEGER PRIMARY KEY, ext TEXT UNIQUE, char TEXT,
                    realm TEXT, target TEXT, guid TEXT, typ TEXT, entry TEXT, map TEXT, x TEXT, y TEXT,
                    zone TEXT, subzone TEXT, quest TEXT, notes TEXT, questlog TEXT, status TEXT DEFAULT "Open",
                    created DATETIME DEFAULT CURRENT_TIMESTAMP, priority TEXT DEFAULT 'Medium', kind TEXT DEFAULT 'Bug')''')
                db.execute("INSERT INTO reports(ext,char,realm,quest,zone,target,typ,entry,notes,kind,priority) VALUES ('test','PrivateCharacter','Private Realm','Treasure Hunting','Westfall','Chest','GameObject','123','The chest does not open','Bug','High')")
            proc=subprocess.Popen([sys.executable,'-u',str(web/'launch_dashboard.py')],cwd=str(web),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
            base=f'http://127.0.0.1:{port}'
            def get(path):
                with urlopen(base+path,timeout=3) as r:
                    return r.read().decode(),r.url
            def post(path,data):
                request=Request(base+path,data=urlencode(data).encode(),method='POST')
                return urlopen(request,timeout=4)
            try:
                for _ in range(80):
                    try:
                        get('/assets/necrocore.css');break
                    except (URLError, ConnectionError):time.sleep(.1)
                else:self.fail('Dashboard never started')
                with sqlite3.connect(web/'bugs.sqlite3') as db:
                    cols={r[1] for r in db.execute('PRAGMA table_info(reports)')}
                    self.assertIn('github_issue_url',cols)
                    self.assertIn('issue_category',cols)
                    self.assertEqual(db.execute('SELECT notes FROM reports WHERE id=1').fetchone()[0],'The chest does not open')
                body,_=get('/?kind=Bug')
                self.assertIn('href="/github/1"',body)
                preview,_=get('/github/1')
                self.assertIn('[Quest] Westfall: Treasure Hunting',preview)
                self.assertIn('Open pre-filled GitHub draft',preview)
                self.assertNotIn('PrivateCharacter',preview)  # Reporter omitted from generated issue, not necessarily page metadata.
                self.assertIn('team/bfa-core/issues/new?',preview)
                self.assertIn('name="issue_category"',get('/edit/1')[0])
                # Preserve category override in the edit form.
                edit,_=get('/edit/1')
                csrf=re.search(r'name="csrf" value="([^"]+)',edit).group(1)
                with sqlite3.connect(web/'bugs.sqlite3') as db:
                    db.row_factory=sqlite3.Row
                    row=db.execute('SELECT * FROM reports WHERE id=1').fetchone()
                    fields={x:str(row[x] or '') for x in ('char','realm','target','typ','entry','guid','quest','zone','subzone','map','x','y','questlog','notes','status','priority','kind','issue_category')}
                fields['issue_category']='GameObject';fields['csrf']=csrf
                with post('/edit/1',fields) as resp: self.assertEqual(resp.status,200)
                self.assertIn('[GameObject] Westfall: Treasure Hunting',get('/github/1')[0])
                with self.assertRaises(HTTPError) as error:
                    post('/github/1/link', {'csrf':'bad','github_issue_url':'https://github.com/team/core/issues/99'})
                self.assertEqual(error.exception.code,403)
                with self.assertRaises(HTTPError) as error:
                    post('/github/1/link', {'csrf':csrf,'github_issue_url':'https://evil.example/evil'})
                self.assertEqual(error.exception.code,400)
                with post('/github/1/link', {'csrf':csrf,'github_issue_url':'https://github.com/team/bfa-core/issues/99'}) as resp:
                    self.assertEqual(resp.status,200)
                linked,_=get('/report/1')
                self.assertIn('https://github.com/team/bfa-core/issues/99',linked)
                with sqlite3.connect(web/'bugs.sqlite3') as db:
                    self.assertEqual(db.execute('SELECT github_issue_url FROM reports WHERE id=1').fetchone()[0],'https://github.com/team/bfa-core/issues/99')
                with post('/github/1/link', {'csrf':csrf,'github_issue_url':''}) as resp:
                    self.assertEqual(resp.status,200)
                self.assertNotIn('Already linked:',get('/github/1')[0])
                print('PASS GitHub issue preview, edit, link, CSRF, migration, offline')
            finally:
                proc.terminate()
                try:proc.wait(timeout=6)
                except subprocess.TimeoutExpired:proc.kill()
                proc.stdout.close()

if __name__=='__main__':
    unittest.main(verbosity=2)
