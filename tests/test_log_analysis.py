import os
from datetime import datetime
from pathlib import Path

from pytest import MonkeyPatch

from monitor_cron import core
from monitor_cron.enums import JobStatus
from monitor_cron.models import Job


class TestAnalyzeLogFile:
    """Tests for the _analyze_log_file function."""

    def test_analyze_log_with_success_marker(self, log_file_with_success: Path) -> None:
        """Test analyzing a log file with success marker."""
        modification_time = datetime.fromtimestamp(
            os.path.getmtime(log_file_with_success)
        )

        result = core._analyze_log_file(str(log_file_with_success), modification_time)

        assert result.status == JobStatus.SUCCESS
        assert result.message == "Finished"
        assert result.file == str(log_file_with_success)
        assert result.last_modification_time == modification_time

    def test_analyze_log_with_failure_marker(self, log_file_with_failure: Path) -> None:
        """Test analyzing a log file with failure marker."""
        modification_time = datetime.fromtimestamp(
            os.path.getmtime(log_file_with_failure)
        )

        result = core._analyze_log_file(str(log_file_with_failure), modification_time)

        assert result.status == JobStatus.FAILED
        assert result.message == "Failed"
        assert result.file == str(log_file_with_failure)
        assert result.last_modification_time == modification_time

    def test_analyze_log_with_crash(self, log_file_with_crash: Path) -> None:
        """Test analyzing a log file indicating a crash."""
        modification_time = datetime.fromtimestamp(
            os.path.getmtime(log_file_with_crash)
        )

        result = core._analyze_log_file(str(log_file_with_crash), modification_time)

        assert result.status == JobStatus.CRASHED
        assert result.message == "Crashed"
        assert result.file == str(log_file_with_crash)
        assert result.last_modification_time == modification_time

    def test_analyze_log_with_unknown_format(
        self, log_file_unknown_format: Path
    ) -> None:
        """Test analyzing a log file without recognized markers."""
        modification_time = datetime.fromtimestamp(
            os.path.getmtime(log_file_unknown_format)
        )

        result = core._analyze_log_file(str(log_file_unknown_format), modification_time)

        assert result.status == JobStatus.UNKNOWN
        assert result.message == "Unknown log format"
        assert result.file == str(log_file_unknown_format)
        assert result.last_modification_time == modification_time

    def test_analyze_log_file_not_found(self) -> None:
        """Test analyzing a non-existent log file."""
        result = core._analyze_log_file("/nonexistent/file.log", datetime.now())

        assert result.status == JobStatus.ERROR
        assert (
            "No such file" in result.message
            or "does not exist" in result.message.lower()
        )

    def test_analyze_log_priority_failed_over_success(self, temp_dir: Path) -> None:
        """Test that failed marker takes priority over success marker."""
        log_file = temp_dir / "both-markers.log"
        log_file.write_text("[JOB STARTED]\n[JOB SUCCEEDED]\n[JOB FAILED]\n")

        modification_time = datetime.fromtimestamp(os.path.getmtime(log_file))
        result = core._analyze_log_file(str(log_file), modification_time)

        assert result.status == JobStatus.FAILED
        assert result.message == "Failed"
        assert result.file == str(log_file)
        assert result.last_modification_time == modification_time


class TestGetLatestLogFile:
    """Tests for the get_latest_log_file function."""

    def test_get_latest_log_file(
        self,
        multiple_log_files: list[Path],
        sample_jobs: list[Job],
    ) -> None:
        """Test getting the most recent log file."""
        # Update the job pattern to match our test files
        job = sample_jobs[0]
        job.log_pattern = str(multiple_log_files[0].parent / "backup-*.log")

        latest = core.get_latest_log_file(job)

        # Should return the file with the latest modification time (2026-02-03)
        assert latest == str(multiple_log_files[2])

    def test_get_latest_log_file_no_matches(self, sample_jobs: list[Job]) -> None:
        """Test when no files match the pattern."""
        job = sample_jobs[0]
        job.log_pattern = "/nonexistent/path/*.log"

        latest = core.get_latest_log_file(job)

        assert latest is None

    def test_get_latest_log_file_with_tilde_expansion(
        self,
        temp_dir: Path,
        sample_jobs: list[Job],
        monkeypatch: MonkeyPatch,
    ) -> None:
        """Test that tilde in path is properly expanded."""
        # Create a log file in temp dir
        log_file = temp_dir / "test.log"
        log_file.write_text("test")

        original_expanduser = os.path.expanduser

        def mock_expanduser(path: str) -> str:
            if path.startswith("~"):
                start_index = len("~") + 1
                return str(temp_dir / path[start_index:])
            return original_expanduser(path)

        monkeypatch.setattr(os.path, "expanduser", mock_expanduser)

        job = sample_jobs[0]
        job.log_pattern = "~/test.log"

        latest = core.get_latest_log_file(job)

        assert latest == str(log_file)
