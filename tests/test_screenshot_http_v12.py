import contextlib
import json
import sqlite3
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'web'))
import dashboard
import screenshot_uploads as su
from test_screenshot_v12 import PNG

class HttpScreenshotTests(unittest.TestCase):
    def test_api(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)
            dashboard.BASE=p
            dashboard.DB=p/'bugs.sqlite3'
            dashboard.LOG=p/'inbox'/'received.log'
            dashboard.SCREENSHOT_KEY=su.private_key(p)
            dashboard.init()
            epoch=int(time.time())
            with dashboard.connect() as db:
                db.execute('INSERT INTO reports(ext,char,realm,notes,screenshot_epoch) VALUES(?,?,?,?,?)',
                          ('test','Mia','NecroRealm','notes',epoch))
            srv=ThreadingHTTPServer(('127.0.0.1',0),dashboard.App)
            th=threading.Thread(target=srv.serve_forever,daemon=True)
            th.start()
            url='http://127.0.0.1:'+str(srv.server_address[1])
            def req(path, key=None, method='GET', data=None, headers=None):
                h={'X-NecroScreenshot-Key':key} if key else {}
                h.update(headers or {})
                q=urllib.request.Request(url+path,data=data,method=method,headers=h)
                try:
                    with urllib.request.urlopen(q,timeout=4) as response:
                        return response.status, response.read()
                except urllib.error.HTTPError as e:
                    return e.code,e.read()
            try:
                status,_=req('/_screenshot/pending',key='incorrect')
                self.assertEqual(status,403)
                status,data=req('/_screenshot/pending',key=dashboard.SCREENSHOT_KEY)
                self.assertEqual(status,200)
                self.assertEqual(json.loads(data)['pending'][0]['character'],'Mia')
                h={'X-NecroScreenshot-Character':'Mia','X-NecroScreenshot-Epoch':str(epoch)}
                status,data=req('/_screenshot/upload/1',key=dashboard.SCREENSHOT_KEY,method='POST',data=PNG,headers=h)
                self.assertEqual(status,200,data)
                self.assertEqual(json.loads(data)['attached'],True)
                status,attached=req('/screenshot/1')
                self.assertEqual(status,200)
                self.assertEqual(attached,PNG)
                status,data=req('/_screenshot/pending',key=dashboard.SCREENSHOT_KEY)
                self.assertEqual(json.loads(data)['pending'],[])
                status,_=req('/_screenshot/upload/1',key=dashboard.SCREENSHOT_KEY,method='POST',data=PNG,headers=h)
                self.assertEqual(status,400)
            finally:
                srv.shutdown();srv.server_close();th.join(timeout=3)

if __name__=='__main__':unittest.main()
