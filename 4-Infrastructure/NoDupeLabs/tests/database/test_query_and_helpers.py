import sqlite3
import pytest

from nodupe.tools.databases.query import (
    DatabaseQuery,
    DatabaseBatch,
    DatabasePerformance,
    DatabaseRecovery,
    DatabaseOptimization,
)


class ConnWrapper:
    def __init__(self, conn):
        self._conn = conn

    def get_connection(self):
        return self._conn


def test_database_query_execute_and_batch_commit(tmp_path):
    conn = sqlite3.connect(':memory:')
    conn.execute('CREATE TABLE t (id INTEGER PRIMARY KEY, v TEXT)')
    conn.commit()

    wrapper = ConnWrapper(conn)
    dq = DatabaseQuery(wrapper)
    # insert via batch
    dbatch = DatabaseBatch(wrapper)
    dbatch.execute_batch([('INSERT INTO t (v) VALUES (?)', ('a',))])

    res = dq.execute('SELECT v FROM t')
    assert res and res[0]['v'] == 'a'


def test_execute_transaction_batch_rollback_on_error():
    conn = sqlite3.connect(':memory:')
    conn.execute('CREATE TABLE t (id INTEGER PRIMARY KEY, v TEXT)')
    conn.commit()
    wrapper = ConnWrapper(conn)
    dbatch = DatabaseBatch(wrapper)

    # first op valid, second invalid should trigger rollback and raise
    ops = [
        ('INSERT INTO t (v) VALUES (?)', ('x',)),
        ('INSERT INTO nonexist (a) VALUES (?)', ('y',)),
    ]
    with pytest.raises(Exception):
        dbatch.execute_transaction_batch(ops)

    # ensure first insert not committed
    cur = conn.execute('SELECT COUNT(*) FROM t')
    assert cur.fetchone()[0] == 0


def test_performance_and_optimization_and_recovery():
    # DatabasePerformance record/query
    class Dummy:
        def __init__(self):
            self.monitoring = self

        def get_metrics(self):
            return {'metrics': {'queries': 1}}

    dummy = Dummy()
    perf = DatabasePerformance(dummy)
    perf.record_query(0.1)
    metrics = perf.get_metrics()
    assert 'metrics' in metrics

    # Optimization
    opt = DatabaseOptimization(None)
    assert opt.optimize_query('SELECT 1;') == 'SELECT 1'

    # Recovery - valid
    class WithIntegrity:
        def __init__(self, valid=True):
            self.integrity = self
            self._valid = valid

        def check_integrity(self):
            return {'valid': self._valid}

    rec = DatabaseRecovery(WithIntegrity(True))
    assert rec.handle_errors() is True

    rec2 = DatabaseRecovery(WithIntegrity(False))
    assert rec2.handle_errors(raise_on_error=False) is False
