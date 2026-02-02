from monitor_cron.enums import JobFrequency, JobStatus


class TestJobFrequency:
    """Tests for JobFrequency enum."""

    def test_all_frequencies_exist(self) -> None:
        """Test that all expected frequencies are defined."""
        assert hasattr(JobFrequency, "DAILY")
        assert hasattr(JobFrequency, "WEEKLY")
        assert hasattr(JobFrequency, "MONTHLY")

    def test_frequency_values(self) -> None:
        """Test that frequency values are correct."""
        assert JobFrequency.DAILY == "daily"
        assert JobFrequency.WEEKLY == "weekly"
        assert JobFrequency.MONTHLY == "monthly"

    def test_frequency_count(self) -> None:
        """Test that there are exactly 3 frequencies."""
        assert len(list(JobFrequency)) == 3

    def test_frequency_iteration(self) -> None:
        """Test iterating over all frequencies."""
        frequencies = list(JobFrequency)
        assert JobFrequency.DAILY in frequencies
        assert JobFrequency.WEEKLY in frequencies
        assert JobFrequency.MONTHLY in frequencies


class TestJobStatus:
    """Tests for JobStatus enum."""

    def test_all_statuses_exist(self) -> None:
        """Test that all expected statuses are defined."""
        expected_statuses = [
            "STALE",
            "ERROR",
            "FAILED",
            "RUNNING",
            "SUCCESS",
            "CRASHED",
            "MISSING",
            "UNKNOWN",
        ]
        for status in expected_statuses:
            assert hasattr(JobStatus, status)

    def test_status_values(self) -> None:
        """Test that status values match their names."""
        assert JobStatus.STALE == "STALE"
        assert JobStatus.ERROR == "ERROR"
        assert JobStatus.FAILED == "FAILED"
        assert JobStatus.RUNNING == "RUNNING"
        assert JobStatus.SUCCESS == "SUCCESS"
        assert JobStatus.CRASHED == "CRASHED"
        assert JobStatus.MISSING == "MISSING"
        assert JobStatus.UNKNOWN == "UNKNOWN"

    def test_status_count(self) -> None:
        """Test that there are exactly 8 statuses."""
        assert len(list(JobStatus)) == 8
