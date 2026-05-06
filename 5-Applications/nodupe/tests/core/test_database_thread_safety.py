# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun

"""Thread safety tests for DatabaseConnection singleton.

This module contains comprehensive tests for verifying thread-safe behavior
of the DatabaseConnection singleton pattern under concurrent load.

Tests cover:
- Multiple threads calling get_instance() simultaneously
- Verification that only ONE connection per db_path is created
- WAL file integrity under concurrent load
- Race condition stress tests
- Connection pool thread isolation
"""

import os
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Set

from nodupe.tools.databases.connection import DatabaseConnection, get_connection
from nodupe.tools.databases.schema import DatabaseSchema


def _init_full_schema(db: DatabaseConnection) -> None:
    """Helper to initialize the full schema for tests."""
    schema = DatabaseSchema(db.get_connection())
    schema.create_schema()


class TestSingletonThreadSafety:
    """Test thread safety of DatabaseConnection singleton pattern."""

    def test_singleton_same_instance_concurrent_access(self):
        """Test that concurrent access returns the same singleton instance."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name

        try:
            instances: List[DatabaseConnection] = []
            errors: List[Exception] = []
            lock = threading.Lock()

            def get_instance_thread():
                """Get database instance in thread."""
                try:
                    instance = DatabaseConnection.get_instance(db_path)
                    with lock:
                        instances.append(instance)
                except Exception as e:
                    with lock:
                        errors.append(e)

            # Create 50 threads all trying to get the same instance
            threads = [threading.Thread(target=get_instance_thread) for _ in range(50)]

            # Start all threads nearly simultaneously
            for thread in threads:
                thread.start()

            # Wait for all threads to complete
            for thread in threads:
                thread.join()

            # Verify no errors occurred
            assert len(errors) == 0, f"Errors occurred: {errors}"

            # Verify all threads got the same instance
            assert len(instances) == 50
            first_instance = instances[0]
            for instance in instances[1:]:
                assert instance is first_instance, "Different instances returned!"

            # Verify only one instance was created (singleton)
            unique_instances = set(id(inst) for inst in instances)
            assert len(unique_instances) == 1, f"Expected 1 unique instance, got {len(unique_instances)}"

            # Cleanup
            first_instance.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_singleton_different_db_paths(self):
        """Test that different db paths return different instances."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp1, \
             tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp2:
            db_path1 = tmp1.name
            db_path2 = tmp2.name

        try:
            instances: Dict[str, List[DatabaseConnection]] = {db_path1: [], db_path2: []}
            lock = threading.Lock()

            def get_instance_thread(db_path: str):
                """Get database instance for specific path."""
                instance = DatabaseConnection.get_instance(db_path)
                with lock:
                    instances[db_path].append(instance)

            # Create threads for both database paths
            threads = []
            for _ in range(25):
                threads.append(threading.Thread(target=get_instance_thread, args=(db_path1,)))
                threads.append(threading.Thread(target=get_instance_thread, args=(db_path2,)))

            # Start all threads
            for thread in threads:
                thread.start()

            # Wait for all threads to complete
            for thread in threads:
                thread.join()

            # Verify all instances for db_path1 are the same
            path1_instances = instances[db_path1]
            path1_first = path1_instances[0]
            for inst in path1_instances[1:]:
                assert inst is path1_first

            # Verify all instances for db_path2 are the same
            path2_instances = instances[db_path2]
            path2_first = path2_instances[0]
            for inst in path2_instances[1:]:
                assert inst is path2_first

            # Verify instances for different paths are different
            assert path1_first is not path2_first

            # Cleanup
            path1_first.close()
            path2_first.close()
        finally:
            for path in [db_path1, db_path2]:
                if os.path.exists(path):
                    os.unlink(path)

    def test_singleton_concurrent_with_executor(self):
        """Test singleton behavior using ThreadPoolExecutor."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name

        try:
            def get_instance_task():
                """Task to get database instance."""
                return DatabaseConnection.get_instance(db_path)

            # Use ThreadPoolExecutor for concurrent access
            with ThreadPoolExecutor(max_workers=20) as executor:
                futures = [executor.submit(get_instance_task) for _ in range(100)]
                results = [f.result() for f in as_completed(futures)]

            # Verify all results are the same instance
            first = results[0]
            for result in results[1:]:
                assert result is first, "Different instances returned from executor!"

            # Verify singleton count
            unique_ids = set(id(r) for r in results)
            assert len(unique_ids) == 1

            # Cleanup
            first.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_singleton_rapid_creation_destruction(self):
        """Test singleton under rapid creation/destruction cycles."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name

        try:
            instances_created: List[int] = []
            lock = threading.Lock()

            def create_destroy_cycle(thread_id: int):
                """Create and destroy database instance cycles."""
                for _ in range(10):
                    instance = DatabaseConnection.get_instance(db_path)
                    with lock:
                        instances_created.append(id(instance))
                    # Don't close - let singleton manage lifecycle
                    time.sleep(0.001)  # Small delay

            threads = [threading.Thread(target=create_destroy_cycle, args=(i,)) for i in range(20)]

            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()

            # All instances should be the same (singleton)
            unique_ids = set(instances_created)
            assert len(unique_ids) == 1, f"Expected 1 unique instance, got {len(unique_ids)}"

            # Cleanup
            DatabaseConnection.get_instance(db_path).close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)


class TestWALIntegrityUnderConcurrentLoad:
    """Test WAL file integrity under concurrent database operations."""

    def test_wal_concurrent_writes(self):
        """Test WAL integrity with concurrent write operations."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name

        try:
            db = DatabaseConnection.get_instance(db_path)
            _init_full_schema(db)

            errors: List[Exception] = []
            success_count = [0]
            lock = threading.Lock()

            def write_data(thread_id: int):
                """Write data to database in thread."""
                try:
                    for i in range(50):
                        db.execute(
                            "INSERT INTO files (path, size, modified_time, created_time, scanned_at, updated_at) "
                            "VALUES (?, ?, ?, ?, ?, ?)",
                            (f"file_{thread_id}_{i}.txt", 100 + i, int(time.time()),
                             int(time.time()), int(time.time()), int(time.time()))
                        )
                    db.commit()
                    with lock:
                        success_count[0] += 1
                except Exception as e:
                    with lock:
                        errors.append(e)

            threads = [threading.Thread(target=write_data, args=(i,)) for i in range(10)]

            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()

            # Verify no errors
            assert len(errors) == 0, f"Errors during concurrent writes: {errors}"

            # Verify data integrity - count total records
            cursor = db.execute("SELECT COUNT(*) FROM files")
            count = cursor.fetchone()[0]
            assert count == 500, f"Expected 500 records, got {count}"

            # Verify WAL mode is enabled
            cursor = db.execute("PRAGMA journal_mode")
            journal_mode = cursor.fetchone()[0]
            assert journal_mode == "wal", f"Expected WAL mode, got {journal_mode}"

            db.close()
        finally:
            # Clean up WAL and SHM files
            for ext in ['', '-wal', '-shm']:
                path = db_path + ext
                if os.path.exists(path):
                    os.unlink(path)

    def test_wal_concurrent_reads_writes(self):
        """Test WAL integrity with mixed read/write operations."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name

        try:
            db = DatabaseConnection.get_instance(db_path)
            _init_full_schema(db)

            # Pre-populate some data
            for i in range(100):
                db.execute(
                    "INSERT INTO files (path, size, modified_time, created_time, scanned_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (f"initial_{i}.txt", 100, int(time.time()), int(time.time()),
                     int(time.time()), int(time.time()))
                )
            db.commit()

            errors: List[Exception] = []
            read_counts: List[int] = []
            write_counts: List[int] = []
            lock = threading.Lock()

            def reader(thread_id: int):
                """Read data from database in thread."""
                try:
                    for _ in range(20):
                        cursor = db.execute("SELECT COUNT(*) FROM files")
                        count = cursor.fetchone()[0]
                        with lock:
                            read_counts.append(count)
                        time.sleep(0.001)
                except Exception as e:
                    with lock:
                        errors.append(("reader", thread_id, e))

            def writer(thread_id: int):
                """Write data to database in thread."""
                try:
                    for i in range(20):
                        db.execute(
                            "INSERT INTO files (path, size, modified_time, created_time, scanned_at, updated_at) "
                            "VALUES (?, ?, ?, ?, ?, ?)",
                            (f"writer_{thread_id}_{i}.txt", 200, int(time.time()),
                             int(time.time()), int(time.time()), int(time.time()))
                        )
                        if i % 5 == 0:
                            db.commit()
                        time.sleep(0.001)
                    db.commit()
                    with lock:
                        write_counts.append(20)
                except Exception as e:
                    with lock:
                        errors.append(("writer", thread_id, e))

            threads = []
            for i in range(5):
                threads.append(threading.Thread(target=reader, args=(i,)))
                threads.append(threading.Thread(target=writer, args=(i,)))

            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()

            # Verify no errors
            assert len(errors) == 0, f"Errors during concurrent read/write: {errors}"

            # Verify final count
            cursor = db.execute("SELECT COUNT(*) FROM files")
            final_count = cursor.fetchone()[0]
            expected = 100 + (5 * 20)  # initial + writers
            assert final_count == expected, f"Expected {expected} records, got {final_count}"

            db.close()
        finally:
            for ext in ['', '-wal', '-shm']:
                path = db_path + ext
                if os.path.exists(path):
                    os.unlink(path)

    def test_wal_transaction_isolation(self):
        """Test transaction isolation under concurrent load."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name

        try:
            db = DatabaseConnection.get_instance(db_path)
            _init_full_schema(db)

            errors: List[Exception] = []
            transactions_committed: List[int] = []
            lock = threading.Lock()

            def transaction_worker(thread_id: int):
                """Execute transactions in thread."""
                try:
                    for i in range(10):
                        # Start transaction
                        db.execute(
                            "INSERT INTO files (path, size, modified_time, created_time, scanned_at, updated_at) "
                            "VALUES (?, ?, ?, ?, ?, ?)",
                            (f"txn_{thread_id}_{i}.txt", 300, int(time.time()),
                             int(time.time()), int(time.time()), int(time.time()))
                        )
                        # Small delay to increase chance of interleaving
                        time.sleep(0.001)
                        db.commit()
                        with lock:
                            transactions_committed.append(thread_id)
                except Exception as e:
                    with lock:
                        errors.append(e)

            threads = [threading.Thread(target=transaction_worker, args=(i,)) for i in range(8)]

            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()

            # Verify no errors
            assert len(errors) == 0, f"Transaction errors: {errors}"

            # Verify all transactions committed
            assert len(transactions_committed) == 80  # 8 threads * 10 transactions

            # Verify data integrity
            cursor = db.execute("SELECT COUNT(*) FROM files")
            count = cursor.fetchone()[0]
            assert count == 80, f"Expected 80 records, got {count}"

            db.close()
        finally:
            for ext in ['', '-wal', '-shm']:
                path = db_path + ext
                if os.path.exists(path):
                    os.unlink(path)


class TestRaceConditionStress:
    """Stress tests for race conditions."""

    def test_stress_concurrent_singleton_access(self):
        """Stress test with high concurrency singleton access."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name

        try:
            instance_ids: Set[int] = set()
            lock = threading.Lock()

            def get_and_verify():
                """Get instance and verify singleton."""
                instance = DatabaseConnection.get_instance(db_path)
                with lock:
                    instance_ids.add(id(instance))
                time.sleep(0.0001)  # Tiny delay to increase contention

            # Use ThreadPoolExecutor for maximum concurrency
            with ThreadPoolExecutor(max_workers=50) as executor:
                futures = [executor.submit(get_and_verify) for _ in range(500)]
                for f in as_completed(futures):
                    f.result()  # Raise any exceptions

            # Verify only ONE instance was ever created
            assert len(instance_ids) == 1, f"Race condition detected! {len(instance_ids)} instances created"

            # Cleanup
            DatabaseConnection.get_instance(db_path).close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_stress_multiple_databases_concurrent(self):
        """Stress test with multiple databases accessed concurrently."""
        db_paths: List[str] = []
        try:
            # Create 5 temporary databases
            for _ in range(5):
                tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
                db_paths.append(tmp.name)
                tmp.close()

            results: Dict[str, Set[int]] = {path: set() for path in db_paths}
            lock = threading.Lock()

            def access_database(db_path: str, thread_id: int):
                """Access database from thread."""
                instance = DatabaseConnection.get_instance(db_path)
                with lock:
                    results[db_path].add(id(instance))
                time.sleep(0.001)

            # Create threads accessing all databases
            threads = []
            for db_path in db_paths:
                for i in range(20):
                    threads.append(threading.Thread(target=access_database, args=(db_path, i)))

            # Start all threads
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()

            # Verify each database has exactly one instance
            for db_path, instance_ids in results.items():
                assert len(instance_ids) == 1, \
                    f"Race condition for {db_path}! {len(instance_ids)} instances created"

            # Cleanup
            for db_path in db_paths:
                DatabaseConnection.get_instance(db_path).close()
        finally:
            for db_path in db_paths:
                if os.path.exists(db_path):
                    os.unlink(db_path)

    def test_stress_interleaved_get_instance_calls(self):
        """Stress test with interleaved get_instance calls."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name

        try:
            call_order: List[int] = []
            instances: List[DatabaseConnection] = []
            lock = threading.Lock()
            barrier = threading.Barrier(30)  # Synchronize thread start

            def synchronized_get(thread_id: int):
                """Get instance with barrier synchronization."""
                barrier.wait()  # All threads wait here
                instance = DatabaseConnection.get_instance(db_path)
                with lock:
                    call_order.append(thread_id)
                    instances.append(instance)

            threads = [threading.Thread(target=synchronized_get, args=(i,)) for i in range(30)]

            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()

            # Verify all got the same instance
            first_instance = instances[0]
            for instance in instances[1:]:
                assert instance is first_instance, "Different instances after barrier synchronization!"

            # Verify singleton
            unique_ids = set(id(inst) for inst in instances)
            assert len(unique_ids) == 1

            # Cleanup
            first_instance.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)


class TestConnectionThreadIsolation:
    """Test that connections are properly isolated per thread."""

    def test_thread_local_connections(self):
        """Test that each thread gets its own connection."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name

        try:
            db = DatabaseConnection.get_instance(db_path)
            _init_full_schema(db)

            connection_ids: Dict[int, int] = {}
            lock = threading.Lock()

            def get_connection_id(thread_id: int):
                """Get connection ID in thread."""
                conn = db.get_connection()
                conn_id = id(conn)
                with lock:
                    connection_ids[thread_id] = conn_id

            # Get connections from multiple threads
            threads = [threading.Thread(target=get_connection_id, args=(i,)) for i in range(10)]

            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()

            # Each thread should have its own connection
            unique_conn_ids = set(connection_ids.values())
            assert len(unique_conn_ids) == 10, \
                f"Expected 10 unique connections, got {len(unique_conn_ids)}"

            # Same thread should get same connection (verify in main thread)
            conn1 = db.get_connection()
            conn2 = db.get_connection()
            assert conn1 is conn2, "Same thread should get same connection"

            db.close()
        finally:
            for ext in ['', '-wal', '-shm']:
                path = db_path + ext
                if os.path.exists(path):
                    os.unlink(path)

    def test_concurrent_operations_thread_isolation(self):
        """Test concurrent operations maintain thread isolation."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name

        try:
            db = DatabaseConnection.get_instance(db_path)
            _init_full_schema(db)

            errors: List[Exception] = []
            results: Dict[int, int] = {}
            lock = threading.Lock()

            def thread_operation(thread_id: int):
                """Execute database operation in thread."""
                try:
                    # Each thread inserts its own data
                    db.execute(
                        "INSERT INTO files (path, size, modified_time, created_time, scanned_at, updated_at) "
                        "VALUES (?, ?, ?, ?, ?, ?)",
                        (f"thread_{thread_id}.txt", thread_id * 100, int(time.time()),
                         int(time.time()), int(time.time()), int(time.time()))
                    )
                    db.commit()

                    # Each thread reads its own data
                    cursor = db.execute(
                        "SELECT size FROM files WHERE path = ?",
                        (f"thread_{thread_id}.txt",)
                    )
                    result = cursor.fetchone()
                    with lock:
                        results[thread_id] = result[0] if result else -1
                except Exception as e:
                    with lock:
                        errors.append(e)

            threads = [threading.Thread(target=thread_operation, args=(i,)) for i in range(20)]

            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()

            # Verify no errors
            assert len(errors) == 0, f"Errors: {errors}"

            # Verify each thread got its correct data
            for thread_id, size in results.items():
                assert size == thread_id * 100, \
                    f"Thread {thread_id} got wrong size: {size}"

            db.close()
        finally:
            for ext in ['', '-wal', '-shm']:
                path = db_path + ext
                if os.path.exists(path):
                    os.unlink(path)


class TestGetConnectionFunction:
    """Test the get_connection convenience function."""

    def test_get_connection_thread_safe(self):
        """Test that get_connection function is thread-safe."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name

        try:
            instances: List[DatabaseConnection] = []
            lock = threading.Lock()

            def get_conn():
                """Get database connection."""
                conn = get_connection(db_path)
                with lock:
                    instances.append(conn)

            threads = [threading.Thread(target=get_conn) for _ in range(25)]

            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()

            # All should be the same instance
            first = instances[0]
            for inst in instances[1:]:
                assert inst is first

            # Cleanup
            first.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)


class TestMemoryDatabaseThreadSafety:
    """Test thread safety with in-memory databases."""

    def test_memory_database_singleton(self):
        """Test singleton behavior with :memory: database."""
        # Note: Each :memory: connection creates a new database
        # This test verifies the singleton still works correctly

        db1 = DatabaseConnection.get_instance(":memory:")
        db2 = DatabaseConnection.get_instance(":memory:")

        # For :memory:, same path should return same instance
        assert db1 is db2

        db1.close()

    def test_memory_database_concurrent_access(self):
        """Test concurrent access to in-memory database."""
        instances: List[DatabaseConnection] = []
        lock = threading.Lock()

        def get_memory_db():
            """Get in-memory database instance."""
            instance = DatabaseConnection.get_instance(":memory:")
            with lock:
                instances.append(instance)

        threads = [threading.Thread(target=get_memory_db) for _ in range(10)]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # All should be the same instance
        first = instances[0]
        for inst in instances[1:]:
            assert inst is first

        first.close()
