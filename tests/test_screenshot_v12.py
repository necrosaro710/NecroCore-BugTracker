import io
import json
import os
import sqlite3
import struct
import sys
import tempfile
import time
import unittest
import urllib.parse
from pathlib import Path
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'web'))
sys.path.insert(0,str(ROOT/'client_helper'))
import dashboard
import screenshot_uploads as su
from necro_screenshot_companion import choose_match

# Minimal real-looking 1x1 PNG with valid IEND (payload isn't decoded by server).
PNG=(b'\x89PNG\r\n\x1a\n'+ struct.pack('>I',13)+b'IHDR'+struct.pack('>II',1,1)
     +b'\x08\x02\x00\x00\x00'+ b'\x00'*4 + struct.pack('>I',0)+b'IEND'+b'\x00'*4)

class ScreenshotTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)
        dashboard.BASE=self.path
        dashboard.DB=self.path/'bugs.sqlite3'
        dashboard.LOG=self.path/'inbox'/'received.log'
        dashboard.init()
        self.t=int(time.time())
        with dashboard.connect() as db:
            db.execute('INSERT INTO reports(ext,char,realm,target,notes,screenshot_epoch) VALUES(?,?,?,?,?,?)',
                       ('test-1','Miasmus','NecroRealm','Test Quest','Test note',self.t))
            self.ident=db.execute('SELECT last_insert_rowid()').fetchone()[0]

    def tearDown(self): self.tmp.cleanup()

    def test_pair_and_store_image(self):
        with dashboard.connect() as db:
            todo=su.pending(db)
            self.assertEqual(todo[0]['id'],self.ident)
            self.assertEqual(su.store(db,self.path,self.ident,'Miasmus',self.t,PNG),'image/png')
            self.assertEqual(su.attachment(db,self.path,self.ident).read_bytes(),PNG)
            self.assertEqual(su.pending(db),[])
            with self.assertRaises(ValueError):
                su.store(db,self.path,self.ident,'Miasmus',self.t,PNG)

    def test_never_match_wrong_character_or_epoch(self):
        with dashboard.connect() as db:
            with self.assertRaises(ValueError):su.store(db,self.path,self.ident,'Other',self.t,PNG)
            with self.assertRaises(ValueError):su.store(db,self.path,self.ident,'Miasmus',self.t+1,PNG)
            with self.assertRaises(ValueError):su.store(db,self.path,self.ident,'Miasmus',self.t,b'<script>')
            with self.assertRaises(ValueError):su.store(db,self.path,self.ident,'Miasmus',self.t,b'x'*(su.MAX_IMAGE+1))

    def test_companion_pairing_ambiguity(self):
        f=self.path/'screen.png';f.write_bytes(PNG)
        os.utime(f,(self.t,self.t))
        files=[(f,f.stat())]
        item=dict(id=self.ident,character='Miasmus',realm='NecroRealm',captured_at=self.t)
        self.assertEqual(len(choose_match([item],files,'Miasmus','NecroRealm')),1)
        self.assertEqual(choose_match([item],files,'Other','NecroRealm'),[])
        self.assertEqual(choose_match([item,{**item,'id':2}],files,'Miasmus','NecroRealm'),[])
        f2=self.path/'other.png';f2.write_bytes(PNG);os.utime(f2,(self.t+10,self.t+10))
        self.assertEqual(choose_match([item],[(f,f.stat()),(f2,f2.stat())],'Miasmus','NecroRealm'),[])

    def test_ingest_17_fields_and_old_16_fields(self):
        # Ingest server-verified character; 17th payload field is screenshot epoch.
        rows=[]
        for i,shot in enumerate((str(self.t),'') ,start=10):
            data=['fake-name','NecroRealm','Target','','','','1','40','40','Westfall','','1:Quest','Notes','','Medium','Bug']
            if shot:data.append(shot)
            rows.append('NB2|rid'+str(i)+'|ServerVerified|'+ '|'.join(urllib.parse.quote(x,safe='') for x in data)+'\n')
        dashboard.LOG.write_text(''.join(rows), encoding='utf-8')
        dashboard.ingest()
        with dashboard.connect() as db:
            results=db.execute("SELECT char,screenshot_epoch FROM reports WHERE ext LIKE 'server-%' ORDER BY id").fetchall()
            self.assertEqual(results,[('ServerVerified',self.t),('ServerVerified',0)])

    def test_private_key_persistent(self):
        k1=su.private_key(self.path)
        k2=su.private_key(self.path)
        self.assertEqual(k1,k2)
        self.assertTrue(su.authorize(k1,k2))
        self.assertFalse(su.authorize('bad',k2))

if __name__=='__main__': unittest.main()
