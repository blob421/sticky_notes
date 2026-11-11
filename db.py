import sqlite3
import os 
from contextlib import closing
import traceback
CUR_DIR = os.path.dirname(__file__)


def with_sqlite3(fn):
    def wrapper(*args, **kwargs):
        try:
            with sqlite3.connect(os.path.join(CUR_DIR, 'db.sqlite')) as db:
                with closing(db.cursor()) as cur:
                    return fn(cur, *args, **kwargs)
        
                
        except Exception as e:
              traceback.print_exc()
              print(e)

    return wrapper


@with_sqlite3
def init_db(cur):
            
    cur.execute("""CREATE TABLE IF NOT EXISTS notes (
                                                    id INTEGER PRIMARY KEY,
                                                    title TEXT,
                                                    content TEXT
                                                    )""")
    
    cur.execute("""CREATE TABLE IF NOT EXISTS metadata(last_idx INTEGER)""")
   
   
    
@with_sqlite3
def get_notes(cur):
    cur.execute("""SELECT * FROM notes ORDER BY id ASC""")
    data:list = list(cur.fetchall())

    if not data: 
       
        return {1: {'title': " ", 'content': " "}}, None
    

    parsed = {}

    for n in data:
        parsed[n[0]] = {'title': n[1], 'content': n[2]}

    
    highest_id = data[-1][0]

    return parsed, highest_id

@with_sqlite3
def delete_note(cur, id):
    cur.execute("""DELETE FROM notes WHERE id=?""", (id,))
    
@with_sqlite3
def save_note(cur, content, title, create=False, id=None):
    if id and not create:
       cur.execute("""UPDATE notes SET title=?,content=? WHERE id=?""", (title, content, id))
       cur.execute("""UPDATE metadata SET last_idx=? WHERE rowid=?""", (id, 1))

    elif id and create:
       cur.execute("""INSERT OR IGNORE INTO notes(id, title, content) VALUES(?,?,?)""",(id, title, content))  

    elif not id:
        cur.execute("""INSERT OR IGNORE INTO notes(id, title, content) VALUES(?,?,?)""",(1, title, content))   

@with_sqlite3
def get_metadata(cur):
    cur.execute("""SELECT * FROM metadata""")
    data = cur.fetchone()
    if not data:
         cur.execute("""INSERT INTO metadata(last_idx) VALUES(?)""",(1,))
         return 1
   
    return data[0]