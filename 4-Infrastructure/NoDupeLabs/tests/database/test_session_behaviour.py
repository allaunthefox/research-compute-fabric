import sqlite3
from nodupe.tools.databases.session import DatabaseSession


def test_session_begin_commit_and_rollback(tmp_path):
    dbfile = str(tmp_path / 's.db')
    # use file path to exercise opened_conn path
    session = DatabaseSession(dbfile)

    # successful commit
    with session.begin() as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS x (id INTEGER PRIMARY KEY, v TEXT)')
        conn.execute('INSERT INTO x (v) VALUES (?)', ('a',))

    # reopened connection to check data persisted
    conn2 = sqlite3.connect(dbfile)
    cur = conn2.execute('SELECT v FROM x')
    rows = cur.fetchall()
    conn2.close()
    assert rows and rows[0][0] == 'a'

    # exception path should rollback and not raise
    try:
        with session.begin() as conn:
            conn.execute('INSERT INTO x (v) VALUES (?)', ('b',))
            raise RuntimeError('fail')
    except RuntimeError:
        pass

    # ensure last insert did not persist
    conn3 = sqlite3.connect(dbfile)
    cur = conn3.execute('SELECT COUNT(*) FROM x')
    count = cur.fetchone()[0]
    conn3.close()
    assert count == 1
