import sqlite3
from nodupe.tools.databases.schema import DatabaseSchema


def test_schema_create_and_get_info(tmp_path):
    db = sqlite3.connect(str(tmp_path / "s.db"))
    schema = DatabaseSchema(db)

    # create schema and validate version
    schema.create_schema()
    v = schema.get_schema_version()
    assert v is not None

    # validate schema reports valid
    is_valid, errors = schema.validate_schema()
    assert is_valid is True
    assert errors == []

    # get table info for files
    cols = schema.get_table_info('files')
    assert any(c['name'] == 'path' for c in cols)

    # get indexes for files (should return list)
    idxs = schema.get_indexes('files')
    assert isinstance(idxs, list)

    # optimize database (no exception)
    schema.optimize_database()
