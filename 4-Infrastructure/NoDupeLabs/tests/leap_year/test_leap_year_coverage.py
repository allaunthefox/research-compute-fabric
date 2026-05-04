"""Test Leap Year Module - Coverage Completion.

Tests to achieve 100% coverage for leap_year.py
"""

import pytest

from nodupe.tools.leap_year.leap_year import LeapYearTool


class TestLeapYearToolInit:
    """Test LeapYearTool initialization."""

    def test_init_gregorian_default(self):
        """Test initialization with default gregorian calendar."""
        tool = LeapYearTool()
        assert tool.calendar == "gregorian"
        assert tool.enable_cache is True
        assert tool.cache_size == 10000
        assert tool.min_year == 1
        assert tool.max_year == 9999

    def test_init_julian(self):
        """Test initialization with julian calendar."""
        tool = LeapYearTool(calendar="julian")
        assert tool.calendar == "julian"

    def test_init_calendar_case_insensitive(self):
        """Test that calendar is case insensitive."""
        tool = LeapYearTool(calendar="GREGORIAN")
        assert tool.calendar == "gregorian"

    def test_init_invalid_calendar(self):
        """Test initialization with invalid calendar."""
        with pytest.raises(ValueError) as exc_info:
            LeapYearTool(calendar="invalid")
        assert "Unsupported calendar" in str(exc_info.value)

    def test_init_disable_cache(self):
        """Test initialization with cache disabled."""
        tool = LeapYearTool(enable_cache=False)
        assert tool.enable_cache is False

    def test_init_custom_cache_size(self):
        """Test initialization with custom cache size."""
        tool = LeapYearTool(cache_size=5000)
        assert tool.cache_size == 5000

    def test_init_custom_year_range(self):
        """Test initialization with custom year range."""
        tool = LeapYearTool(min_year=1900, max_year=2100)
        assert tool.min_year == 1900
        assert tool.max_year == 2100


class TestLeapYearToolProperties:
    """Test LeapYearTool properties."""

    def test_name_property(self):
        """Test name property."""
        tool = LeapYearTool()
        assert tool.name == "leap_year_algorithm"

    def test_version_property(self):
        """Test version property."""
        tool = LeapYearTool()
        assert tool.version == "1.0.0"

    def test_dependencies_property(self):
        """Test dependencies property."""
        tool = LeapYearTool()
        assert tool.dependencies == []


class TestLeapYearIsLeapYear:
    """Test is_leap_year method."""

    def test_is_leap_year_2000(self):
        """Test year 2000 is leap year (divisible by 400)."""
        tool = LeapYearTool()
        assert tool.is_leap_year(2000) is True

    def test_is_leap_year_1900(self):
        """Test year 1900 is not leap year (divisible by 100 but not 400)."""
        tool = LeapYearTool()
        assert tool.is_leap_year(1900) is False

    def test_is_leap_year_2004(self):
        """Test year 2004 is leap year (divisible by 4)."""
        tool = LeapYearTool()
        assert tool.is_leap_year(2004) is True

    def test_is_leap_year_2001(self):
        """Test year 2001 is not leap year."""
        tool = LeapYearTool()
        assert tool.is_leap_year(2001) is False

    def test_is_leap_year_cache_disabled(self):
        """Test is_leap_year with cache disabled."""
        tool = LeapYearTool(enable_cache=False)
        assert tool.is_leap_year(2000) is True
        assert tool.is_leap_year(1900) is False

    def test_is_leap_year_out_of_range(self):
        """Test is_leap_year with year out of range."""
        tool = LeapYearTool()
        with pytest.raises(ValueError) as exc_info:
            tool.is_leap_year(0)
        assert "out of range" in str(exc_info.value)

    def test_is_leap_year_type_error(self):
        """Test is_leap_year with non-integer year."""
        tool = LeapYearTool()
        with pytest.raises(TypeError) as exc_info:
            tool.is_leap_year("2000")
        assert "integer" in str(exc_info.value)


class TestLeapYearJulianCalendar:
    """Test Julian calendar leap year detection."""

    def test_julian_leap_year_1900(self):
        """Test Julian calendar: 1900 is leap year."""
        tool = LeapYearTool(calendar="julian")
        assert tool.is_leap_year(1900) is True

    def test_julian_leap_year_2001(self):
        """Test Julian calendar: 2001 is not leap year."""
        tool = LeapYearTool(calendar="julian")
        assert tool.is_leap_year(2001) is False

    def test_julian_leap_year_2004(self):
        """Test Julian calendar: 2004 is leap year."""
        tool = LeapYearTool(calendar="julian")
        assert tool.is_leap_year(2004) is True


class TestLeapYearBatchOperations:
    """Test batch operations."""

    def test_find_leap_years(self):
        """Test finding leap years in range."""
        tool = LeapYearTool()
        leap_years = tool.find_leap_years(2000, 2010)
        assert leap_years == [2000, 2004, 2008]

    def test_find_leap_years_single_year(self):
        """Test finding leap years in single year range."""
        tool = LeapYearTool()
        leap_years = tool.find_leap_years(2000, 2000)
        assert leap_years == [2000]

    def test_find_leap_years_invalid_range(self):
        """Test finding leap years with invalid range."""
        tool = LeapYearTool()
        with pytest.raises(ValueError) as exc_info:
            tool.find_leap_years(2010, 2000)
        assert "start_year" in str(exc_info.value)

    def test_count_leap_years(self):
        """Test counting leap years in range."""
        tool = LeapYearTool()
        count = tool.count_leap_years(2000, 2010)
        assert count == 3

    def test_count_leap_years_none(self):
        """Test counting leap years with none in range."""
        tool = LeapYearTool()
        count = tool.count_leap_years(2001, 2003)
        assert count == 0

    def test_is_leap_year_batch(self):
        """Test batch leap year checking."""
        tool = LeapYearTool()
        results = tool.is_leap_year_batch([2000, 2001, 2004, 2005])
        assert results == [True, False, True, False]


class TestLeapYearDateValidation:
    """Test date validation methods."""

    def test_is_valid_date_valid(self):
        """Test validating valid date."""
        tool = LeapYearTool()
        assert tool.is_valid_date(2000, 2, 29) is True

    def test_is_valid_date_invalid_feb_29(self):
        """Test validating Feb 29 in non-leap year."""
        tool = LeapYearTool()
        assert tool.is_valid_date(2001, 2, 29) is False

    def test_is_valid_date_invalid_month(self):
        """Test validating invalid month."""
        tool = LeapYearTool()
        assert tool.is_valid_date(2000, 13, 1) is False

    def test_is_valid_date_invalid_day(self):
        """Test validating invalid day."""
        tool = LeapYearTool()
        assert tool.is_valid_date(2000, 1, 32) is False

    def test_is_valid_date_type_error_year(self):
        """Test validating date with non-integer year."""
        tool = LeapYearTool()
        assert tool.is_valid_date("2000", 1, 1) is False

    def test_is_valid_date_type_error_month(self):
        """Test validating date with non-integer month."""
        tool = LeapYearTool()
        assert tool.is_valid_date(2000, "1", 1) is False

    def test_is_valid_date_type_error_day(self):
        """Test validating date with non-integer day."""
        tool = LeapYearTool()
        assert tool.is_valid_date(2000, 1, "1") is False


class TestLeapYearGetDaysInMonth:
    """Test get_days_in_month method."""

    def test_get_days_in_month_jan(self):
        """Test getting days in January."""
        tool = LeapYearTool()
        assert tool.get_days_in_month(2000, 1) == 31

    def test_get_days_in_month_feb_leap(self):
        """Test getting days in February (leap year)."""
        tool = LeapYearTool()
        assert tool.get_days_in_month(2000, 2) == 29

    def test_get_days_in_month_feb_non_leap(self):
        """Test getting days in February (non-leap year)."""
        tool = LeapYearTool()
        assert tool.get_days_in_month(2001, 2) == 28

    def test_get_days_in_month_invalid_month(self):
        """Test getting days for invalid month."""
        tool = LeapYearTool()
        with pytest.raises(ValueError) as exc_info:
            tool.get_days_in_month(2000, 13)
        assert "out of range" in str(exc_info.value)

    def test_get_days_in_month_type_error_month(self):
        """Test getting days with non-integer month."""
        tool = LeapYearTool()
        with pytest.raises(TypeError) as exc_info:
            tool.get_days_in_month(2000, "1")
        assert "integer" in str(exc_info.value)


class TestLeapYearGetDaysInYear:
    """Test get_days_in_year method."""

    def test_get_days_in_year_leap(self):
        """Test getting days in leap year."""
        tool = LeapYearTool()
        assert tool.get_days_in_year(2000) == 366

    def test_get_days_in_year_non_leap(self):
        """Test getting days in non-leap year."""
        tool = LeapYearTool()
        assert tool.get_days_in_year(2001) == 365


class TestLeapYearGetCalendarInfo:
    """Test get_calendar_info method."""

    def test_get_calendar_info_leap(self):
        """Test getting calendar info for leap year."""
        tool = LeapYearTool()
        info = tool.get_calendar_info(2000)
        assert info["year"] == 2000
        assert info["is_leap_year"] is True
        assert info["days_in_year"] == 366
        assert info["days_in_february"] == 29
        assert len(info["monthly_days"]) == 12

    def test_get_calendar_info_non_leap(self):
        """Test getting calendar info for non-leap year."""
        tool = LeapYearTool()
        info = tool.get_calendar_info(2001)
        assert info["year"] == 2001
        assert info["is_leap_year"] is False
        assert info["days_in_year"] == 365
        assert info["days_in_february"] == 28


class TestLeapYearEasterDate:
    """Test Easter date calculation."""

    def test_get_easter_date_gregorian(self):
        """Test getting Easter date (Gregorian)."""
        tool = LeapYearTool()
        month, day = tool.get_easter_date(2000)
        assert 3 <= month <= 4  # Easter is in March or April
        assert 1 <= day <= 31

    def test_get_easter_date_julian(self):
        """Test getting Easter date (Julian)."""
        tool = LeapYearTool(calendar="julian")
        month, day = tool.get_easter_date(2000)
        assert 3 <= month <= 4
        assert 1 <= day <= 31


class TestLeapYearPerformance:
    """Test performance and statistics methods."""

    def test_get_cache_stats_enabled(self):
        """Test getting cache stats when enabled."""
        tool = LeapYearTool(enable_cache=True)
        tool.is_leap_year(2000)
        tool.is_leap_year(2000)  # Cache hit
        stats = tool.get_cache_stats()
        assert stats["enabled"] is True
        assert stats["hits"] >= 1

    def test_get_cache_stats_disabled(self):
        """Test getting cache stats when disabled."""
        tool = LeapYearTool(enable_cache=False)
        stats = tool.get_cache_stats()
        assert stats["enabled"] is False

    def test_reset_cache_stats(self):
        """Test resetting cache stats."""
        tool = LeapYearTool(enable_cache=True)
        tool.is_leap_year(2000)
        tool.reset_cache_stats()
        stats = tool.get_cache_stats()
        assert stats["hits"] == 0

    def test_benchmark_algorithm(self):
        """Test benchmarking algorithm."""
        tool = LeapYearTool()
        results = tool.benchmark_algorithm([2000, 2001, 2004], iterations=10)
        assert "total_time" in results
        assert "iterations" in results
        assert results["iterations"] == 10


class TestLeapYearIterator:
    """Test iterator support."""

    def test_leap_year_range(self):
        """Test iterating over leap years."""
        tool = LeapYearTool()
        leap_years = list(tool.leap_year_range(2000, 2010))
        assert leap_years == [2000, 2004, 2008]

    def test_leap_year_range_invalid(self):
        """Test iterating with invalid range."""
        tool = LeapYearTool()
        with pytest.raises(ValueError):
            list(tool.leap_year_range(2010, 2000))


class TestLeapYearConfiguration:
    """Test configuration methods."""

    def test_set_calendar(self):
        """Test setting calendar."""
        tool = LeapYearTool()
        tool.set_calendar("julian")
        assert tool.calendar == "julian"

    def test_set_calendar_invalid(self):
        """Test setting invalid calendar."""
        tool = LeapYearTool()
        with pytest.raises(ValueError):
            tool.set_calendar("invalid")

    def test_enable_caching(self):
        """Test enabling caching."""
        tool = LeapYearTool(enable_cache=False)
        tool.enable_caching()
        assert tool.enable_cache is True

    def test_enable_caching_with_size(self):
        """Test enabling caching with custom size."""
        tool = LeapYearTool(enable_cache=False)
        tool.enable_caching(cache_size=5000)
        assert tool.cache_size == 5000

    def test_disable_caching(self):
        """Test disabling caching."""
        tool = LeapYearTool(enable_cache=True)
        tool.disable_caching()
        assert tool.enable_cache is False


class TestLeapYearConvenience:
    """Test convenience methods."""

    def test_next_leap_year(self):
        """Test finding next leap year."""
        tool = LeapYearTool()
        assert tool.next_leap_year(2001) == 2004
        assert tool.next_leap_year(2000) == 2004

    def test_previous_leap_year(self):
        """Test finding previous leap year."""
        tool = LeapYearTool()
        assert tool.previous_leap_year(2005) == 2004
        assert tool.previous_leap_year(2004) == 2000

    def test_previous_leap_year_none(self):
        """Test finding previous leap year when none exists."""
        tool = LeapYearTool(min_year=2000)
        with pytest.raises(ValueError):
            tool.previous_leap_year(2000)

    def test_get_leap_year_cycle(self):
        """Test getting leap year cycle."""
        tool = LeapYearTool()
        cycle = tool.get_leap_year_cycle(2002)
        assert cycle == (2001, 2002, 2003, 2004)

    def test_is_gregorian_leap_year(self):
        """Test Gregorian leap year check."""
        tool = LeapYearTool()
        assert tool.is_gregorian_leap_year(2000) is True
        assert tool.is_gregorian_leap_year(1900) is False

    def test_is_julian_leap_year(self):
        """Test Julian leap year check."""
        tool = LeapYearTool()
        assert tool.is_julian_leap_year(1900) is True
        assert tool.is_julian_leap_year(2001) is False


class TestLeapYearToolLifecycle:
    """Test tool lifecycle methods."""

    def test_initialize(self):
        """Test tool initialization."""
        tool = LeapYearTool()
        tool.initialize(None)  # Should not raise

    def test_shutdown(self):
        """Test tool shutdown."""
        tool = LeapYearTool()
        tool.is_leap_year(2000)  # Generate some cache stats
        tool.shutdown(None)  # Should not raise

    def test_shutdown_with_cache_stats(self, caplog):
        """Test tool shutdown logs cache stats."""
        tool = LeapYearTool()
        tool.is_leap_year(2000)
        tool.is_leap_year(2000)
        tool.shutdown(None)


class TestLeapYearRunStandalone:
    """Test standalone execution."""

    def test_run_standalone_no_args(self, capsys):
        """Test running standalone with no args."""
        tool = LeapYearTool()
        result = tool.run_standalone([])
        assert result == 0
        captured = capsys.readouterr()
        assert "usage" in captured.out.lower()

    def test_run_standalone_with_year(self, capsys):
        """Test running standalone with year argument."""
        tool = LeapYearTool()
        result = tool.run_standalone(["2000"])
        assert result == 0
        captured = capsys.readouterr()
        assert "leap year" in captured.out.lower()

    def test_run_standalone_error(self):
        """Test running standalone with invalid year."""
        tool = LeapYearTool()
        with pytest.raises(SystemExit):
            tool.run_standalone(["invalid"])


class TestLeapYearDescribeUsage:
    """Test describe_usage method."""

    def test_describe_usage(self):
        """Test describing usage."""
        tool = LeapYearTool()
        description = tool.describe_usage()
        assert "leap year" in description.lower() or "day" in description.lower()


class TestLeapYearGetCapabilities:
    """Test get_capabilities method."""

    def test_get_capabilities(self):
        """Test getting capabilities."""
        tool = LeapYearTool()
        caps = tool.get_capabilities()
        assert caps["leap_year_detection"] is True
        assert "gregorian" in caps["calendar_systems"]
        assert "julian" in caps["calendar_systems"]
        assert caps["batch_processing"] is True
        assert caps["date_validation"] is True
        assert caps["caching"] is True
        assert caps["thread_safe"] is True


class TestLeapYearMetadata:
    """Test metadata property."""

    def test_metadata(self):
        """Test getting metadata."""
        tool = LeapYearTool()
        metadata = tool.metadata
        assert metadata.name == "leap_year_algorithm"
        assert metadata.version == "1.0.0"


class TestLeapYearAPIMethods:
    """Test api_methods property."""

    def test_api_methods(self):
        """Test getting API methods."""
        tool = LeapYearTool()
        api_methods = tool.api_methods
        assert "is_leap_year" in api_methods
        assert "find_leap_years" in api_methods
        assert "count_leap_years" in api_methods
        assert "is_valid_date" in api_methods
        assert "get_days_in_month" in api_methods
        assert "get_calendar_info" in api_methods


class TestRegisterTool:
    """Test register_tool function."""

    def test_register_tool(self):
        """Test registering tool."""
        from nodupe.tools.leap_year.leap_year import register_tool
        tool = register_tool()
        assert isinstance(tool, LeapYearTool)
