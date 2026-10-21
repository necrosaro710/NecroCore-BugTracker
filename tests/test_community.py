"""Offline smoke tests; use a temp copy and never touch a live installation."""
import base64
import hashlib
import http.cookiejar
import json
import os
import re
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent


def get_port():
    with socket.socket() as s:
        s.bind(('127.0.0.1',0))
        return s.getsockname()[1]


def go(auth, linked=False):
    tmp=tempfile.TemporaryDirectory(prefix='necrob_community_')
    parent=Path(tmp.name)
    web=parent/'web'
    shutil.copytree(ROOT/'web', web)
    port=get_port()
    cfg=dict(server_name='Obsidian & Ash <Realm>',bind_address='127.0.0.1',port=port,data_directory='.',inbox_path='inbox/received.log',
             admin_login=auth,admin_username='tester',password_hash='',
             attribution_repo_url=('https://github.com/example/repo' if linked else ''))
    if auth:
        salt=b'0123456789012345'
        digest=hashlib.pbkdf2_hmac('sha256',b'test secret password',salt,300000)
        cfg['password_hash']=f'pbkdf2_sha256$300000${salt.hex()}${digest.hex()}'
    (web/'config.json').write_text(json.dumps(cfg))
    proc=subprocess.Popen([sys.executable,'-u',str(web/'launch_dashboard.py')],stdout=subprocess.PIPE,stderr=subprocess.STDOUT, text=True)
    url=f'http://127.0.0.1:{port}'
    opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    try:
        for i in range(120):
            try:
                with opener.open(url+'/assets/necrocore.css', timeout=.3) as r:
                    assert r.status==200
                    break
            except (OSError,urllib.error.URLError):
                if proc.poll() is not None:
                    raise RuntimeError('Dashboard failed to start')
                time.sleep(.1)
        else:
            raise RuntimeError('Dashboard startup timeout')

        global current_opener,current_url
        current_opener, current_url=opener,url
        def get(p):
            with opener.open(url+p,timeout=10) as r:
                return r.read().decode(),r.url
        def post(p,data):
            content=urllib.parse.urlencode(data,doseq=True).encode()
            return opener.open(urllib.request.Request(url+p,content,method='POST'),timeout=10)
        if auth:
            page,actual=get('/')
            assert actual.endswith('/login') and 'Administrator' in page
            assert 'Obsidian &amp; Ash &lt;Realm&gt;' in page and 'Powered by NecroCore Bug Tracker' in page
            try:
                post('/bulk',dict(ids='1',bulk_action='delete'))
                raise AssertionError('Unauthenticated POST allowed')
            except urllib.error.HTTPError as e:
                assert e.code==403
            r=post('/login',dict(username='tester',password='test secret password'))
            assert r.status==200 and r.url.endswith('/')
            page,actual=get('/')
        else:
            page,actual=get('/')
            assert actual.endswith('/') and 'Closed' in page
        assert '<title>Obsidian &amp; Ash &lt;Realm&gt; · Bug Tracker</title>' in page
        assert 'Powered by NecroCore Bug Tracker' in page
        if not linked:
            assert 'href="https://github.com/necrosaro710/NecroCore-BugTracker"' in page, 'Missing official footer link'
        if linked:
            assert 'href=\"https://github.com/example/repo\"' in page
        else:
            assert 'href=\"https://github.com/example/repo\"' not in page
        assert '<Realm>' not in page
        assert 'Welcome to <span>Obsidian &amp; Ash &lt;Realm&gt;</span>' in page
        with sqlite3.connect(web/'bugs.sqlite3') as db:
            for ext,kind,status in [('a','Bug','Open'),('b','Idea','Open'),('c','Bug','Closed'),('d','Idea','Closed')]:
                db.execute('INSERT INTO reports(ext,char,quest,notes,kind,status) VALUES(?,?,?,?,?,?)',(ext,'Example',ext+' Quest','Synthetic ticket',kind,status))
            ids=dict((ext,id) for id,ext in db.execute('SELECT id,ext FROM reports'))
        for key, expected in [('Bug',['a']),('Idea',['b']),('All',['a','b']),('Closed',['c','d'])]:
            page,_=get('/?kind='+key)
            names=re.findall(r'<td class="ticket-title"><a[^>]*>([^<]+)',page)
            assert set(names)==set(x+' Quest' for x in expected),(key,names)
        # bulk action updates kind but not closed archive; reopening restores active category
        r=post('/bulk',dict(ids=str(ids['b']),bulk_action='Bug',csrf=find_csrf(web)))
        with sqlite3.connect(web/'bugs.sqlite3') as db:
            assert db.execute('SELECT kind FROM reports WHERE id=?',(ids['b'],)).fetchone()[0]=='Bug'
        page,_=get('/?kind=Bug')
        assert 'b Quest' in page
        r=post('/bulk',dict(ids=str(ids['c']),bulk_action='reopen',csrf=find_csrf(web)))
        page,_=get('/?kind=Closed')
        assert 'c Quest' not in page
        r=post('/bulk',dict(ids=str(ids['d']),bulk_action='delete',confirm_delete='YES',csrf=find_csrf(web)))
        with sqlite3.connect(web/'bugs.sqlite3') as db:
            assert not db.execute('SELECT 1 FROM reports WHERE id=?',(ids['d'],)).fetchone()
            assert db.execute('SELECT 1 FROM deleted WHERE ext="d"').fetchone()
        print('PASS HTTP dashboard', 'with login' if auth else 'trusted LAN mode')
    finally:
        proc.terminate()
        try: proc.wait(timeout=5)
        except subprocess.TimeoutExpired: proc.kill()
        proc.stdout.close()
        tmp.cleanup()


def find_csrf(web):
    # Test code reads the CSRF from the web process only through a valid form.
    # The module-level token is randomized in the child, so extract it from HTML.
    import urllib.request
    global current_opener,current_url
    with current_opener.open(current_url+'/?kind=Bug') as r:
        body=r.read().decode()
    match=re.search(r'<input[^>]*name="csrf"[^>]*value="([^"]+)"',body)
    assert match
    return match.group(1)


if __name__=='__main__':
    go(False)
    go(True)
    go(False, linked=True)
    print('COMMUNITY WEB TESTS PASSED')
