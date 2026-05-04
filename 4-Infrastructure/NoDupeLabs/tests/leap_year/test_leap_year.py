"""
Leap Year Tool Tests

Tests for the leap year calculation tool including:
- Leap year detection (Gregorian and Julian)
- Batch processing
- Date validation
- Cache statistics
- Edge cases
"""

import pytest
from unittest.mock import MagicMock, patch
from nodupe.tools.leap_year.leap_year import LeapYearTool, ToolMetadata


class TestLeapYearToolBasic:
    """Test basic LeapYearTool functionality."""

    def test_import(self):
        """LeapYearTool can be imported."""
        from nodupe.tools.leap_year.leap_year import LeapYearTool
        assert LeapYearTool is not None

    def test_instantiation_gregorian(self):
        """LeapYearTool can be instantiated with Gregorian calendar."""
        tool = LeapYearTool(calendar="gregorian")
        assert tool is not None
        assert tool.calendar == "gregorian"

    def test_instantiation_julian(self):
        """LeapYearTool can be instantiated with Julian calendar."""
        tool = LeapYearTool(calendar="julian")
        assert tool is not None
        assert tool.calendar == "julian"

    def test_instantiation_invalid_calendar(self):
        """LeapYearTool raises error for invalid calendar."""
        with pytest.raises(ValueError, match="Unsupported calendar"):
            LeapYearTool(calendar="invalid")

    def test_tool_name(self):
        """Tool has correct name."""
        tool = LeapYearTool()
        assert tool.name == "leap_year_algorithm"

    def test_tool_version(self):
        """Tool has correct version."""
        tool = LeapYearTool()
        assert tool.version == "1.0.0"

    def test_tool_dependencies(self):
        """Tool has no dependencies."""
        tool = LeapYearTool()
        assert tool.dependencies == []


class TestLeapYearGregorian:
    """Test Gregorian calendar leap year calculations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = LeapYearTool(calendar="gregorian")

    def test_leap_year_divisible_by_400(self):
        """Years divisible by 400 are leap years."""
        assert self.tool.is_leap_year(2000) == True
        assert self.tool.is_leap_year(1600) == True
        assert self.tool.is_leap_year(2400) == True

    def test_leap_year_divisible_by_4_not_100(self):
        """Years divisible by 4 but not 100 are leap years."""
        assert self.tool.is_leap_year(2024) == True
        assert self.tool.is_leap_year(2020) == True
        assert self.tool.is_leap_year(2016) == True
        assert self.tool.is_leap_year(1996) == True

    def test_not_leap_year_divisible_by_100_not_400(self):
        """Years divisible by 100 but not 400 are NOT leap years."""
        assert self.tool.is_leap_year(1900) == False
        assert self.tool.is_leap_year(1800) == False
        assert self.tool.is_leap_year(1700) == False
        assert self.tool.is_leap_year(2100) == False

    def test_not_leap_year_not_divisible_by_4(self):
        """Years not divisible by 4 are NOT leap years."""
        assert self.tool.is_leap_year(2023) == False
        assert self.tool.is_leap_year(2021) == False
        assert self.tool.is_leap_year(2019) == False
        assert self.tool.is_leap_year(2025) == False

    def test_known_leap_years(self):
        """Test known leap years."""
        leap_years = [1600, 1604, 1608, 1704, 1708, 1804, 1808, 1904,
                      1908, 1912, 1916, 1920, 1924, 1928, 1932, 1936,
                      1940, 1944, 1948, 1952, 1956, 1960, 1964, 1968,
                      1972, 1976, 1980, 1984, 1988, 1992, 1996, 2000,
                      2004, 2008, 2012, 2016, 2020, 2024, 2028, 2032]
        for year in leap_years:
            assert self.tool.is_leap_year(year) == True, f"{year} should be leap year"

    def test_known_non_leap_years(self):
        """Test known non-leap years."""
        non_leap_years = [1700, 1800, 1900, 2100, 2200, 2300,
                          2023, 2025, 2027, 2029, 2030, 2031]
        for year in non_leap_years:
            assert self.tool.is_leap_year(year) == False, f"{year} should NOT be leap year"


class TestLeapYearJulian:
    """Test Julian calendar leap year calculations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = LeapYearTool(calendar="julian")

    def test_julian_leap_year_divisible_by_4(self):
        """Julian calendar: years divisible by 4 are leap years."""
        assert self.tool.is_leap_year(2000) == True
        assert self.tool.is_leap_year(2004) == True
        assert self.tool.is_leap_year(1900) == True  # Different from Gregorian!
        assert self.tool.is_leap_year(1800) == True  # Different from Gregorian!

    def test_julian_not_leap_year(self):
        """Julian calendar: years not divisible by 4 are NOT leap years."""
        assert self.tool.is_leap_year(2023) == False
        assert self.tool.is_leap_year(2021) == False
        assert self.tool.is_leap_year(1901) == False


class TestLeapYearBatch:
    """Test batch processing functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = LeapYearTool(calendar="gregorian")

    def test_find_leap_years_range(self):
        """find_leap_years finds all leap years in range."""
        result = self.tool.find_leap_years(2020, 2030)
        expected = [2020, 2024, 2028]
        assert result == expected

    def test_find_leap_years_single_year(self):
        """find_leap_years with single year range."""
        result = self.tool.find_leap_years(2024, 2024)
        assert result == [2024]

    def test_find_leap_years_no_leap_years(self):
        """find_leap_years with no leap years in range."""
        result = self.tool.find_leap_years(2021, 2023)
        assert result == []

    def test_count_leap_years_range(self):
        """count_leap_years counts leap years in range."""
        count = self.tool.count_leap_years(2020, 2030)
        assert count == 3  # 2020, 2024, 2028

    def test_count_leap_years_single_leap_year(self):
        """count_leap_years with single leap year."""
        count = self.tool.count_leap_years(2024, 2024)
        assert count == 1

    def test_count_leap_years_no_leap_years(self):
        """count_leap_years with no leap years."""
        count = self.tool.count_leap_years(2021, 2023)
        assert count == 0


class TestLeapYearDateValidation:
    """Test date validation functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = LeapYearTool(calendar="gregorian")

    def test_is_valid_date_valid(self):
        """is_valid_date returns True for valid dates."""
        assert self.tool.is_valid_date(2024, 2, 29) == True  # Leap year Feb 29
        assert self.tool.is_valid_date(2023, 2, 28) == True  # Normal Feb 28
        assert self.tool.is_valid_date(2023, 12, 31) == True
        assert self.tool.is_valid_date(2023, 1, 1) == True

    def test_is_valid_date_invalid_month(self):
        """is_valid_date returns False for invalid months."""
        assert self.tool.is_valid_date(2023, 13, 1) == False
        assert self.tool.is_valid_date(2023, 0, 1) == False

    def test_is_valid_date_invalid_day(self):
        """is_valid_date returns False for invalid days."""
        assert self.tool.is_valid_date(2023, 2, 30) == False
        assert self.tool.is_valid_date(2023, 4, 31) == False
        assert self.tool.is_valid_date(2023, 6, 31) == False

    def test_is_valid_date_feb_29_non_leap_year(self):
        """is_valid_date returns False for Feb 29 in non-leap year."""
        assert self.tool.is_valid_date(2023, 2, 29) == False
        assert self.tool.is_valid_date(2021, 2, 29) == False
        assert self.tool.is_valid_date(1900, 2, 29) == False

    def test_get_days_in_month_common_year(self):
        """get_days_in_month returns correct days for common year."""
        assert self.tool.get_days_in_month(2023, 1) == 31
        assert self.tool.get_days_in_month(2023, 2) == 28
        assert self.tool.get_days_in_month(2023, 4) == 30
        assert self.tool.get_days_in_month(2023, 12) == 31

    def test_get_days_in_month_leap_year(self):
        """get_days_in_month returns correct days for leap year."""
        assert self.tool.get_days_in_month(2024, 1) == 31
        assert self.tool.get_days_in_month(2024, 2) == 29  # Leap year!
        assert self.tool.get_days_in_month(2024, 4) == 30
        assert self.tool.get_days_in_month(2024, 12) == 31


class TestLeapYearEdgeCases:
    """Test edge cases and boundary conditions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = LeapYearTool(calendar="gregorian")

    def test_year_validation_min(self):
        """Year validation at minimum boundary."""
        assert self.tool.is_leap_year(1) == False
        assert self.tool.is_leap_year(4) == True

    def test_year_validation_max(self):
        """Year validation at maximum boundary."""
        assert self.tool.is_leap_year(9999) == False
        assert self.tool.is_leap_year(9996) == True

    def test_year_validation_out_of_range(self):
        """Year validation rejects out-of-range years."""
        with pytest.raises(ValueError):
            self.tool.is_leap_year(0)
        with pytest.raises(ValueError):
            self.tool.is_leap_year(10000)
        with pytest.raises(ValueError):
            self.tool.is_leap_year(-1)


class TestLeapYearCache:
    """Test caching functionality."""

    def test_cache_enabled(self):
        """Cache can be enabled."""
        tool = LeapYearTool(enable_cache=True, cache_size=100)
        assert tool.enable_cache == True
        assert tool.cache_size == 100

    def test_cache_disabled(self):
        """Cache can be disabled."""
        tool = LeapYearTool(enable_cache=False)
        assert tool.enable_cache == False

    def test_cache_stats(self):
        """Cache statistics are tracked."""
        tool = LeapYearTool(enable_cache=True, cache_size=100)
        stats = tool.get_cache_stats()
        assert 'hits' in stats
        assert 'misses' in stats


class TestLeapYearToolMethods:
    """Test tool interface methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = LeapYearTool(calendar="gregorian")

    def test_api_methods(self):
        """api_methods returns expected methods."""
        api_methods = self.tool.api_methods
        assert 'is_leap_year' in api_methods
        assert 'find_leap_years' in api_methods
        assert 'count_leap_years' in api_methods
        assert 'is_valid_date' in api_methods
        assert 'get_days_in_month' in api_methods
        assert 'get_calendar_info' in api_methods

    def test_get_capabilities(self):
        """get_capabilities returns expected capabilities."""
        capabilities = self.tool.get_capabilities()
        assert capabilities['leap_year_detection'] == True
        assert 'gregorian' in capabilities['calendar_systems']
        assert 'julian' in capabilities['calendar_systems']
        assert capabilities['batch_processing'] == True
        assert capabilities['date_validation'] == True
        assert capabilities['caching'] == True
        assert capabilities['thread_safe'] == True

    def test_get_calendar_info(self):
        """get_calendar_info returns calendar information."""
        tool = LeapYearTool()
        info = tool.get_calendar_info(2024)
        assert 'calendar' in info
        assert info['calendar'] == 'gregorian'
        # Additional keys may be present
        assert len(info) > 0

    def test_metadata(self):
        """metadata returns ToolMetadata."""
        metadata = self.tool.metadata
        assert isinstance(metadata, ToolMetadata)
        assert metadata.name == "leap_year_algorithm"
        assert metadata.version == "1.0.0"

    def test_initialize(self):
        """initialize() works without error."""
        container = MagicMock()
        tool = LeapYearTool()
        tool.initialize(container)
        # Should not raise

    def test_shutdown(self):
        """shutdown() works without error."""
        container = MagicMock()
        tool = LeapYearTool()
        tool.shutdown(container)
        # Should not raise


class TestLeapYearRunStandalone:
    """Test run_standalone functionality."""

    def test_run_standalone_no_args(self, capsys):
        """run_standalone() with no args shows help."""
        tool = LeapYearTool()
        result = tool.run_standalone([])
        assert result == 0
        captured = capsys.readouterr()
        assert "help" in captured.out.lower() or "year" in captured.out.lower()

    def test_run_standalone_with_year(self, capsys):
        """run_standalone() with year argument."""
        tool = LeapYearTool()
        result = tool.run_standalone(['2024'])
        assert result == 0
        captured = capsys.readouterr()
        assert "2024" in captured.out
        assert "leap year" in captured.out.lower()

    def test_run_standalone_non_leap_year(self, capsys):
        """run_standalone() with non-leap year."""
        tool = LeapYearTool()
        result = tool.run_standalone(['2023'])
        assert result == 0
        captured = capsys.readouterr()
        assert "2023" in captured.out
        assert "False" in captured.out or "not" in captured.out.lower()

    def test_run_standalone_invalid_year(self, capsys):
        """run_standalone() with invalid year."""
        tool = LeapYearTool()
        result = tool.run_standalone(['0'])
        assert result == 1
        captured = capsys.readouterr()
        assert "Error" in captured.out


class TestLeapYearDescribeUsage:
    """Test describe_usage method."""

    def test_describe_usage_returns_string(self):
        """describe_usage() returns a string."""
        tool = LeapYearTool()
        usage = tool.describe_usage()
        assert isinstance(usage, str)
        assert len(usage) > 0

    def test_describe_usage_content(self):
        """describe_usage() contains meaningful content."""
        tool = LeapYearTool()
        usage = tool.describe_usage()
        assert "leap" in usage.lower() or "year" in usage.lower()
        assert "day" in usage.lower() or "calendar" in usage.lower()
