import sqlite3
import os
from nodupe.tools.databases.query import DatabaseBackup


def test_create_and_restore_backup(tmp_path):
    db_path = tmp_path / "db.sqlite"
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, v TEXT);")
    conn.execute("INSERT INTO t (v) VALUES (?)", ("a",))
    conn.commit()
    conn.close()

    class Dummy:
        pass

    d = Dummy()
    d.path = str(db_path)

    backup = DatabaseBackup(d)
    backup_path = tmp_path / "backup.sqlite"
    backup.create_backup(str(backup_path))
    assert os.path.exists(str(backup_path))

    # restore to a new path
    restore_path = tmp_path / "restored.sqlite"
    backup.restore_backup(str(backup_path), str(restore_path))
    assert os.path.exists(str(restore_path))


def test_backup_errors_for_missing_path():
    class Dummy:
        pass

    d = Dummy()
    b = DatabaseBackup(d)
    try:
        b.create_backup('/tmp/x')
        raise AssertionError("Expected ValueError")
    except ValueError:
        pass
