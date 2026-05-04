def test_database_module_exports():
    # Ensure the backward-compat module exports the expected symbols
    import importlib
    m = importlib.import_module('nodupe.tools.databases.database')
    assert 'Database' in getattr(m, '__all__', [])
    assert 'DatabaseError' in getattr(m, '__all__', [])
