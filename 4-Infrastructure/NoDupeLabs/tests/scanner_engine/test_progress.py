"""Tests for progress tracker module."""

import time
from unittest.mock import MagicMock

import pytest


class TestProgressTracker:
    """Test ProgressTracker class."""

    def test_initialization(self):
        """Test tracker initialization."""
        from nodupe.tools.scanner_engine.progress import ProgressTracker
        
        tracker = ProgressTracker()
        
        assert tracker._total_items == 0
        assert tracker._completed_items == 0
        assert tracker._total_bytes == 0
        assert tracker._processed_bytes == 0
        assert tracker._status == "not_started"

    def test_start(self):
        """Test starting progress tracking."""
        from nodupe.tools.scanner_engine.progress import ProgressTracker
        
        tracker = ProgressTracker()
        
        tracker.start(total_items=100, total_bytes=1000)
        
        assert tracker._total_items == 100
        assert tracker._total_bytes == 1000
        assert tracker._completed_items == 0
        assert tracker._status == "in_progress"

    def test_update(self):
        """Test updating progress."""
        from nodupe.tools.scanner_engine.progress import ProgressTracker
        
        tracker = ProgressTracker()
        
        tracker.start(total_items=100)
        tracker.update(items_completed=10, bytes_processed=100)
        
        assert tracker._completed_items == 10
        assert tracker._processed_bytes == 100

    def test_complete(self):
        """Test marking as complete."""
        from nodupe.tools.scanner_engine.progress import ProgressTracker
        
        tracker = ProgressTracker()
        
        tracker.start(total_items=100)
        tracker.complete()
        
        assert tracker._status == "completed"

    def test_error(self):
        """Test recording an error."""
        from nodupe.tools.scanner_engine.progress import ProgressTracker
        
        tracker = ProgressTracker()
        
        tracker.start()
        tracker.error()
        
        assert tracker._error_count == 1

    def test_get_progress(self):
        """Test getting progress information."""
        from nodupe.tools.scanner_engine.progress import ProgressTracker
        
        tracker = ProgressTracker()
        
        tracker.start(total_items=100, total_bytes=1000)
        tracker.update(items_completed=50, bytes_processed=500)
        
        progress = tracker.get_progress()
        
        assert progress['status'] == 'in_progress'
        assert progress['total_items'] == 100
        assert progress['completed_items'] == 50
        assert progress['remaining_items'] == 50
        assert progress['total_bytes'] == 1000
        assert progress['processed_bytes'] == 500

    def test_get_progress_before_start(self):
        """Test getting progress before starting."""
        from nodupe.tools.scanner_engine.progress import ProgressTracker
        
        tracker = ProgressTracker()
        
        progress = tracker.get_progress()
        
        assert progress['status'] == 'not_started'
        assert progress['elapsed_time'] == 0

    def test_get_progress_percent_complete(self):
        """Test percent complete calculation."""
        from nodupe.tools.scanner_engine.progress import ProgressTracker
        
        tracker = ProgressTracker()
        
        tracker.start(total_items=100)
        tracker.update(items_completed=25)
        
        progress = tracker.get_progress()
        
        assert progress['percent_complete'] == 25.0

    def test_get_progress_time_remaining(self):
        """Test time remaining calculation."""
        from nodupe.tools.scanner_engine.progress import ProgressTracker
        
        tracker = ProgressTracker()
        
        tracker.start(total_items=100)
        
        # Add some items processed
        time.sleep(0.01)
        tracker.update(items_completed=10)
        
        progress = tracker.get_progress()
        
        # Should have a time remaining estimate
        assert 'time_remaining' in progress
        assert progress['time_remaining'] >= 0

    def test_get_progress_rates(self):
        """Test rate calculation."""
        from nodupe.tools.scanner_engine.progress import ProgressTracker
        
        tracker = ProgressTracker()
        
        tracker.start(total_items=100, total_bytes=1000)
        
        time.sleep(0.01)
        tracker.update(items_completed=10, bytes_processed=100)
        
        progress = tracker.get_progress()
        
        assert progress['items_per_second'] >= 0
        assert progress['bytes_per_second'] >= 0

    def test_report_progress(self):
        """Test reporting progress via callback."""
        from nodupe.tools.scanner_engine.progress import ProgressTracker
        
        tracker = ProgressTracker()
        
        tracker.start(total_items=100)
        tracker.update(items_completed=50)
        
        callback_called = []
        
        def on_progress(progress):
            """Callback function for progress updates."""
            callback_called.append(progress)
        
        tracker.report_progress(on_progress)
        
        assert len(callback_called) == 1
        assert callback_called[0]['completed_items'] == 50

    def test_report_progress_no_callback(self):
        """Test reporting progress without callback."""
        from nodupe.tools.scanner_engine.progress import ProgressTracker
        
        tracker = ProgressTracker()
        
        tracker.start()
        
        # Should not raise
        tracker.report_progress(None)

    def test_reset(self):
        """Test resetting progress tracker."""
        from nodupe.tools.scanner_engine.progress import ProgressTracker
        
        tracker = ProgressTracker()
        
        tracker.start(total_items=100, total_bytes=1000)
        tracker.update(items_completed=50)
        tracker.error()
        
        tracker.reset()
        
        assert tracker._total_items == 0
        assert tracker._completed_items == 0
        assert tracker._total_bytes == 0
        assert tracker._processed_bytes == 0
        assert tracker._status == "not_started"
        assert tracker._error_count == 0

    def test_get_elapsed_time(self):
        """Test getting elapsed time."""
        from nodupe.tools.scanner_engine.progress import ProgressTracker
        
        tracker = ProgressTracker()
        
        tracker.start()
        
        time.sleep(0.01)
        
        elapsed = tracker.get_elapsed_time()
        
        assert elapsed > 0

    def test_get_elapsed_time_not_started(self):
        """Test getting elapsed time when not started."""
        from nodupe.tools.scanner_engine.progress import ProgressTracker
        
        tracker = ProgressTracker()
        
        elapsed = tracker.get_elapsed_time()
        
        assert elapsed == 0

    def test_get_status(self):
        """Test getting status."""
        from nodupe.tools.scanner_engine.progress import ProgressTracker
        
        tracker = ProgressTracker()
        
        assert tracker.get_status() == "not_started"
        
        tracker.start()
        
        assert tracker.get_status() == "in_progress"
        
        tracker.complete()
        
        assert tracker.get_status() == "completed"

    def test_is_complete(self):
        """Test is_complete method."""
        from nodupe.tools.scanner_engine.progress import ProgressTracker
        
        tracker = ProgressTracker()
        
        assert tracker.is_complete() is False
        
        tracker.start()
        
        assert tracker.is_complete() is False
        
        tracker.complete()
        
        assert tracker.is_complete() is True

    def test_get_error_count(self):
        """Test getting error count."""
        from nodupe.tools.scanner_engine.progress import ProgressTracker
        
        tracker = ProgressTracker()
        
        tracker.start()
        tracker.error()
        tracker.error()
        
        assert tracker.get_error_count() == 2

    def test_format_progress(self):
        """Test formatting progress as string."""
        from nodupe.tools.scanner_engine.progress import ProgressTracker
        
        tracker = ProgressTracker()
        
        tracker.start(total_items=100)
        tracker.update(items_completed=50)
        
        formatted = tracker.format_progress()
        
        assert "Status:" in formatted
        assert "Progress:" in formatted
        assert "Items:" in formatted
        assert "50/100" in formatted

    def test_format_progress_with_dict(self):
        """Test formatting progress with custom dict."""
        from nodupe.tools.scanner_engine.progress import ProgressTracker
        
        tracker = ProgressTracker()
        
        progress_dict = {
            'status': 'completed',
            'percent_complete': 100.0,
            'elapsed_time': 10.0,
            'time_remaining': 0.0,
            'completed_items': 100,
            'total_items': 100,
            'error_count': 0
        }
        
        formatted = tracker.format_progress(progress_dict)
        
        assert "completed" in formatted.lower()
        assert "100.0%" in formatted

    def test_thread_safety(self):
        """Test thread safety of progress tracker."""
        import threading

        from nodupe.tools.scanner_engine.progress import ProgressTracker
        
        tracker = ProgressTracker()
        
        tracker.start(total_items=1000)
        
        def update_progress():
            """Update progress in a thread."""
            for _ in range(100):
                tracker.update(items_completed=1)
        
        threads = [threading.Thread(target=update_progress) for _ in range(10)]
        
        for t in threads:
            t.start()
        
        for t in threads:
            t.join()
        
        progress = tracker.get_progress()
        
        assert progress['completed_items'] == 1000


class TestCreateProgressTracker:
    """Test create_progress_tracker factory function."""

    def test_create_progress_tracker(self):
        """Test creating progress tracker."""
        from nodupe.tools.scanner_engine.progress import create_progress_tracker
        
        tracker = create_progress_tracker()
        
        assert tracker is not None
        assert tracker._status == "not_started"
