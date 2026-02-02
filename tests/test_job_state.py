import os
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from monitor_cron import core
from monitor_cron.enums import JobStatus
from monitor_cron.models import Job


class TestGetJobState:
    """Tests for the get_job_state function."""

    def test_get_job_state_running(self, sample_jobs: list[Job]) -> None:
        """Test job state when process is running."""
        job = sample_jobs[0]

        with patch.object(core, "is_job_running", return_value=True):
            with patch.object(
                core, "get_latest_log_file", return_value="/var/log/test.log"
            ):
                state = core.get_job_state(job)

        assert state.status == JobStatus.RUNNING
        assert state.message == "Process active"
        assert state.file == "/var/log/test.log"

    def test_get_job_state_missing_logs(self, sample_jobs: list[Job]) -> None:
        """Test job state when no log files exist."""
        job = sample_jobs[0]

        with patch.object(core, "is_job_running", return_value=False):
            with patch.object(core, "get_latest_log_file", return_value=None):
                state = core.get_job_state(job)

        assert state.status == JobStatus.MISSING
        assert state.message == "No logs found"
        assert state.file is None

    def test_get_job_state_stale(
        self,
        sample_jobs: list[Job],
        log_file_with_success: Path,
    ) -> None:
        """Test job state when log is stale (old execution)."""
        job = sample_jobs[0]  # Daily job

        # Set log file modification time to yesterday
        old_time = datetime(2026, 1, 31, 12, 0).timestamp()
        os.utime(log_file_with_success, (old_time, old_time))

        with patch.object(core, "is_job_running", return_value=False):
            with patch.object(
                core, "get_latest_log_file", return_value=str(log_file_with_success)
            ):
                with patch.object(core, "datetime") as mock_datetime:
                    mock_datetime.now.return_value = datetime(2026, 2, 1, 12, 0)
                    mock_datetime.fromtimestamp.return_value = datetime.fromtimestamp(
                        old_time
                    )

                    state = core.get_job_state(job)

        assert state.status == JobStatus.STALE
        assert state.message == "Pending"
        assert state.file == str(log_file_with_success)
        assert state.last_modification_time == datetime.fromtimestamp(old_time)

    def test_get_job_state_success(
        self,
        sample_jobs: list[Job],
        log_file_with_success: Path,
    ) -> None:
        """Test job state with successful completion."""
        job = sample_jobs[0]  # Daily job

        # Set today's modification time
        today_time = datetime(2026, 2, 1, 12, 0).timestamp()
        os.utime(log_file_with_success, (today_time, today_time))

        with patch.object(core, "is_job_running", return_value=False):
            with patch.object(
                core, "get_latest_log_file", return_value=str(log_file_with_success)
            ):
                with patch.object(core, "datetime") as mock_datetime:
                    mock_datetime.now.return_value = datetime(2026, 2, 1, 15, 0)
                    mock_datetime.fromtimestamp.return_value = datetime.fromtimestamp(
                        today_time
                    )

                    state = core.get_job_state(job)

        assert state.status == JobStatus.SUCCESS
        assert state.message == "Finished"
        assert state.file == str(log_file_with_success)
        assert state.last_modification_time == datetime.fromtimestamp(today_time)

    def test_get_job_state_failed(
        self,
        sample_jobs: list[Job],
        log_file_with_failure: Path,
    ) -> None:
        """Test job state with failed execution."""
        job = sample_jobs[0]

        today_time = datetime(2026, 2, 1, 12, 0).timestamp()
        os.utime(log_file_with_failure, (today_time, today_time))

        with patch.object(core, "is_job_running", return_value=False):
            with patch.object(
                core, "get_latest_log_file", return_value=str(log_file_with_failure)
            ):
                with patch.object(core, "datetime") as mock_datetime:
                    mock_datetime.now.return_value = datetime(2026, 2, 1, 15, 0)
                    mock_datetime.fromtimestamp.return_value = datetime.fromtimestamp(
                        today_time
                    )

                    state = core.get_job_state(job)

        assert state.status == JobStatus.FAILED
        assert state.message == "Failed"
        assert state.file == str(log_file_with_failure)
        assert state.last_modification_time == datetime.fromtimestamp(today_time)

    def test_get_job_state_crashed(
        self,
        sample_jobs: list[Job],
        log_file_with_crash: Path,
    ) -> None:
        """Test job state when job crashed."""
        job = sample_jobs[0]

        today_time = datetime(2026, 2, 1, 12, 0).timestamp()
        os.utime(log_file_with_crash, (today_time, today_time))

        with patch.object(core, "is_job_running", return_value=False):
            with patch.object(
                core, "get_latest_log_file", return_value=str(log_file_with_crash)
            ):
                with patch.object(core, "datetime") as mock_datetime:
                    mock_datetime.now.return_value = datetime(2026, 2, 1, 15, 0)
                    mock_datetime.fromtimestamp.return_value = datetime.fromtimestamp(
                        today_time
                    )

                    state = core.get_job_state(job)

        assert state.status == JobStatus.CRASHED
        assert state.message == "Crashed"
        assert state.file == str(log_file_with_crash)
        assert state.last_modification_time == datetime.fromtimestamp(today_time)
