from datetime import datetime

import pytest
from pydantic import ValidationError

from enums import JobFrequency, JobStatus
from models import Job, JobState


class TestJob:
    """Tests for the Job model."""

    def test_job_creation_with_valid_data(self) -> None:
        """Test creating a Job with valid data."""
        job = Job(
            name="Test Job",
            frequency=JobFrequency.DAILY,
            log_pattern="/var/log/test-*.log",
            process_pattern="test_process",
        )

        assert job.name == "Test Job"
        assert job.frequency == JobFrequency.DAILY
        assert job.log_pattern == "/var/log/test-*.log"
        assert job.process_pattern == "test_process"

    def test_job_with_all_frequencies(self) -> None:
        """Test Job creation with different frequencies."""
        for frequency in JobFrequency:
            job = Job(
                name="Test",
                frequency=frequency,
                log_pattern="/test.log",
                process_pattern="test",
            )
            assert job.frequency == frequency

    def test_job_missing_required_field(self) -> None:
        """Test that Job raises validation error when required fields are missing."""
        with pytest.raises(ValidationError):
            Job(
                name="Test",
                frequency=JobFrequency.DAILY,
                log_pattern="/test.log",
            )  # type: ignore

    def test_job_invalid_frequency(self) -> None:
        """Test that Job raises validation error for invalid frequency."""
        with pytest.raises(ValidationError):
            Job(
                name="Test",
                frequency="invalid_frequency",  # type: ignore
                log_pattern="/test.log",
                process_pattern="test",
            )  # type: ignore


class TestJobState:
    """Tests for the JobState model."""

    def test_job_state_creation(self) -> None:
        """Test creating a JobState with all fields."""
        state = JobState(
            status=JobStatus.SUCCESS,
            message="Job completed",
            file="/var/log/test.log",
            last_modification_time=datetime(2026, 2, 1, 12, 0),
        )

        assert state.status == JobStatus.SUCCESS
        assert state.message == "Job completed"
        assert state.file == "/var/log/test.log"
        assert state.last_modification_time == datetime(2026, 2, 1, 12, 0)

    def test_job_state_with_none_values(self) -> None:
        """Test JobState with optional None values."""
        state = JobState(
            status=JobStatus.MISSING,
            message="No logs found",
            file=None,
            last_modification_time=None,
        )

        assert state.status == JobStatus.MISSING
        assert state.message == "No logs found"
        assert state.file is None
        assert state.last_modification_time is None

    def test_job_state_default_last_modification_time(self) -> None:
        """Test that last_modification_time defaults to None."""
        state = JobState(
            status=JobStatus.SUCCESS,
            message="Done",
            file="/test.log",
        )

        assert state.last_modification_time is None

    def test_job_state_all_statuses(self) -> None:
        """Test JobState with all possible statuses."""
        for status in JobStatus:
            state = JobState(
                status=status,
                message="Test message",
                file=None,
            )
            assert state.status == status

    def test_job_state_invalid_status(self) -> None:
        """Test that JobState raises validation error for invalid status."""
        with pytest.raises(ValidationError):
            JobState(
                status="INVALID_STATUS",  # type: ignore
                message="Test",
                file=None,
            )
