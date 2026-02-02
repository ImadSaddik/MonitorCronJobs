from datetime import datetime

import core
from enums import JobFrequency


class TestFrequencyCheckFunctions:
    """Tests for individual frequency check functions."""

    def test_check_daily_same_day(self) -> None:
        """Test daily check with same day."""
        last_run = datetime(2026, 2, 1, 10, 0)
        current = datetime(2026, 2, 1, 23, 59)

        assert core._check_daily(last_run, current) is True

    def test_check_daily_different_day(self) -> None:
        """Test daily check with different day."""
        last_run = datetime(2026, 1, 31, 23, 0)
        current = datetime(2026, 2, 1, 0, 1)

        assert core._check_daily(last_run, current) is False

    def test_check_weekly_same_week(self) -> None:
        """Test weekly check within same week."""
        # Week 5 of 2026 (Jan 26 - Feb 1)
        last_run = datetime(2026, 1, 26, 10, 0)  # Monday
        current = datetime(2026, 2, 1, 15, 0)  # Sunday

        assert core._check_weekly(last_run, current) is True

    def test_check_weekly_different_week(self) -> None:
        """Test weekly check across different weeks."""
        # Week 4 vs Week 5
        last_run = datetime(2026, 1, 25, 23, 0)  # Sunday of week 4
        current = datetime(2026, 1, 26, 8, 0)  # Monday of week 5

        assert core._check_weekly(last_run, current) is False

    def test_check_weekly_same_day_different_week(self) -> None:
        """Test weekly check on same day of week but different weeks."""
        last_run = datetime(2026, 1, 19, 10, 0)  # Monday
        current = datetime(2026, 1, 26, 10, 0)  # Next Monday

        assert core._check_weekly(last_run, current) is False

    def test_check_monthly_same_month(self) -> None:
        """Test monthly check within same month."""
        last_run = datetime(2026, 2, 1, 10, 0)
        current = datetime(2026, 2, 28, 23, 59)

        assert core._check_monthly(last_run, current) is True

    def test_check_monthly_different_month_same_year(self) -> None:
        """Test monthly check across different months."""
        last_run = datetime(2026, 1, 31, 23, 0)
        current = datetime(2026, 2, 1, 0, 1)

        assert core._check_monthly(last_run, current) is False

    def test_check_monthly_same_month_different_year(self) -> None:
        """Test monthly check with same month but different year."""
        last_run = datetime(2025, 2, 15, 10, 0)
        current = datetime(2026, 2, 15, 10, 0)

        assert core._check_monthly(last_run, current) is False

    def test_check_monthly_december_to_january(self) -> None:
        """Test monthly check from December to January."""
        last_run = datetime(2025, 12, 31, 23, 0)
        current = datetime(2026, 1, 1, 0, 1)

        assert core._check_monthly(last_run, current) is False


class TestFrequencyStrategies:
    """Tests for the FREQUENCY_STRATEGIES mapping."""

    def test_all_frequencies_have_strategy(self) -> None:
        """Test that all job frequencies have a corresponding strategy."""
        for frequency in JobFrequency:
            assert frequency in core.FREQUENCY_STRATEGIES

    def test_strategies_are_callable(self) -> None:
        """Test that all strategies are callable functions."""
        for strategy in core.FREQUENCY_STRATEGIES.values():
            assert callable(strategy)

    def test_strategy_daily_function(self) -> None:
        """Test that daily frequency uses correct function."""
        assert core.FREQUENCY_STRATEGIES[JobFrequency.DAILY] == core._check_daily

    def test_strategy_weekly_function(self) -> None:
        """Test that weekly frequency uses correct function."""
        assert core.FREQUENCY_STRATEGIES[JobFrequency.WEEKLY] == core._check_weekly

    def test_strategy_monthly_function(self) -> None:
        """Test that monthly frequency uses correct function."""
        assert core.FREQUENCY_STRATEGIES[JobFrequency.MONTHLY] == core._check_monthly


class TestIsExecutionWithinCurrentInterval:
    """Tests for is_execution_within_current_interval with edge cases."""

    def test_invalid_frequency_returns_false(self) -> None:
        """Test that invalid frequency returns False."""
        last_run = datetime(2026, 2, 1, 10, 0)
        current = datetime(2026, 2, 1, 15, 0)

        result = core.is_execution_within_current_interval(
            last_run=last_run,
            frequency="invalid_frequency",  # type: ignore
            current_time=current,
        )

        assert result is False

    def test_uses_current_time_when_not_provided(self) -> None:
        """Test that function uses datetime.now() when current_time is None."""
        last_run = datetime.now().replace(hour=10, minute=0)

        result = core.is_execution_within_current_interval(
            last_run=last_run,
            frequency=JobFrequency.DAILY,
            current_time=None,
        )

        assert result is True

    def test_leap_year_february_monthly(self) -> None:
        """Test monthly check in leap year February."""
        # 2024 is a leap year
        last_run = datetime(2024, 2, 1, 10, 0)
        current = datetime(2024, 2, 29, 23, 59)  # Last day of leap year February

        result = core.is_execution_within_current_interval(
            last_run=last_run,
            frequency=JobFrequency.MONTHLY,
            current_time=current,
        )

        assert result is True
