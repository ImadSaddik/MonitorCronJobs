import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Generator

import pytest

from enums import JobFrequency, JobStatus
from models import Job, JobState


@pytest.fixture
def temp_dir() -> Generator[Path, Any, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as directory:
        yield Path(directory)


@pytest.fixture
def sample_jobs() -> list[Job]:
    """Return a list of sample Job objects for testing."""
    return [
        Job(
            name="Daily Backup",
            frequency=JobFrequency.DAILY,
            log_pattern="/var/log/backup-*.log",
            process_pattern="backup_script.py",
        ),
        Job(
            name="Weekly Report",
            frequency=JobFrequency.WEEKLY,
            log_pattern="/var/log/report-*.log",
            process_pattern="generate_report",
        ),
        Job(
            name="Monthly Cleanup",
            frequency=JobFrequency.MONTHLY,
            log_pattern="/var/log/cleanup-*.log",
            process_pattern="cleanup.sh",
        ),
    ]


@pytest.fixture
def jobs_json_file(temp_dir: Path, sample_jobs: list[Job]) -> Path:
    """Create a temporary jobs.json file."""
    jobs_file = temp_dir / "jobs.json"
    jobs_data = {"jobs": [job.model_dump() for job in sample_jobs]}

    with open(jobs_file, "w") as f:
        json.dump(jobs_data, f)

    return jobs_file


@pytest.fixture
def log_file_with_success(temp_dir: Path) -> Path:
    """Create a log file with success marker."""
    log_file = temp_dir / "test-success.log"
    log_file.write_text("[JOB STARTED]\nProcessing...\n[JOB SUCCEEDED]\n")
    return log_file


@pytest.fixture
def log_file_with_failure(temp_dir: Path) -> Path:
    """Create a log file with failure marker."""
    log_file = temp_dir / "test-failure.log"
    log_file.write_text("[JOB STARTED]\nError occurred\n[JOB FAILED]\n")
    return log_file


@pytest.fixture
def log_file_with_crash(temp_dir: Path) -> Path:
    """Create a log file indicating a crash (started but no completion marker)."""
    log_file = temp_dir / "test-crash.log"
    log_file.write_text("[JOB STARTED]\nProcessing...\n")
    return log_file


@pytest.fixture
def log_file_unknown_format(temp_dir: Path) -> Path:
    """Create a log file without any markers."""
    log_file = temp_dir / "test-unknown.log"
    log_file.write_text("Some log content without markers\n")
    return log_file


@pytest.fixture
def multiple_log_files(temp_dir: Path) -> list[Path]:
    """Create multiple log files with different timestamps."""
    files = []

    for i in range(3):
        log_file = temp_dir / f"backup-2026-02-0{i + 1}.log"
        log_file.write_text(f"Log content {i + 1}\n[JOB SUCCEEDED]\n")

        timestamp = datetime(2026, 2, i + 1, 12, 0).timestamp()
        access_time, modification_time = timestamp, timestamp
        os.utime(log_file, (access_time, modification_time))

        files.append(log_file)

    return files


@pytest.fixture
def sample_job_state() -> JobState:
    """Return a sample JobState for testing."""
    return JobState(
        status=JobStatus.SUCCESS,
        message="Job completed successfully",
        file="/var/log/test.log",
        last_modification_time=datetime(2026, 2, 1, 12, 0),
    )
