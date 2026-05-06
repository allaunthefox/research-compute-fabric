import sqlite3
from nodupe.tools.databases.wrapper import Database


def test_wrapper_crud_operations(tmp_path):
    dbpath = str(tmp_path / 'w.db')
    db = Database(dbpath)

    # create a table
    db.create_table('items', 'id INTEGER PRIMARY KEY, name TEXT')

    # insert
    rowid = db.create('items', {'name': 'alice'})
    assert rowid is not None

    # read
    rows = db.read('SELECT * FROM items')
    assert any(r['name'] == 'alice' for r in rows)

    # update
    cnt = db.update("UPDATE items SET name = ? WHERE id = ?", ('bob', rowid))
    assert cnt == 1

    # delete
    cnt = db.delete("DELETE FROM items WHERE id = ?", (rowid,))
    assert cnt == 1

    db.close()
