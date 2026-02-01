import glob
import json
import os
import subprocess
from datetime import datetime
from typing import Callable

from enums import JobFrequency, JobStatus
from models import Job, JobState

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JOBS_FILE = os.path.join(BASE_DIR, "jobs.json")

MARKER_FAILED = "[JOB FAILED]"
MARKER_SUCCESS = "[JOB SUCCEEDED]"
MARKER_STARTED = "[JOB STARTED]"


def load_jobs() -> list[Job]:
    """Loads jobs from jobs.json."""
    try:
        with open(JOBS_FILE, "r") as f:
            data = json.load(f)
            return [Job(**job) for job in data.get("jobs", [])]
    except Exception as e:
        print(f"Error loading jobs: {e}")
        return []


def get_job_state(job: Job) -> JobState:
    """Returns a JobState object representing the current state of the job."""

    if is_job_running(job.process_pattern):
        return JobState(
            status=JobStatus.RUNNING,
            message="Process active",
            file=get_latest_log_file(job),
        )

    latest_file = get_latest_log_file(job)

    if not latest_file:
        return JobState(status=JobStatus.MISSING, message="No logs found", file=None)

    last_log_modification_time = datetime.fromtimestamp(os.path.getmtime(latest_file))

    if not is_execution_within_current_interval(
        last_log_modification_time,
        job.frequency,
    ):
        return JobState(
            status=JobStatus.STALE,
            message="Pending",
            file=latest_file,
            last_modification_time=last_log_modification_time,
        )

    return _analyze_log_file(latest_file, last_log_modification_time)


def get_latest_log_file(job: Job) -> str | None:
    """Returns the most recent log file matching the job's log pattern."""
    log_pattern = os.path.expanduser(job.log_pattern)
    files = glob.glob(log_pattern)
    return max(files, key=os.path.getmtime) if files else None


def is_job_running(pattern: str | None) -> bool:
    """Checks if a job is currently running based on its process pattern."""
    if not pattern:
        return False

    try:
        return (
            subprocess.call(
                args=["pgrep", "-f", pattern],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            == 0
        )
    except Exception:
        return False


def is_execution_within_current_interval(
    last_run: datetime,
    frequency: JobFrequency,
    current_time: datetime | None = None,
) -> bool:
    """
    Determines if the last run time is fresh based on the job frequency.
    """
    if current_time is None:
        current_time = datetime.now()

    check_strategy = FREQUENCY_STRATEGIES.get(frequency)

    if not check_strategy:
        return False

    return check_strategy(last_run, current_time)


def _analyze_log_file(filepath: str, modification_time: datetime) -> JobState:
    """Reads the log file and determines status based on content markers."""
    try:
        with open(filepath, "r", errors="replace") as f:
            content = f.read()

        if MARKER_FAILED in content:
            return JobState(
                status=JobStatus.FAILED,
                message="Failed",
                file=filepath,
                last_modification_time=modification_time,
            )

        if MARKER_SUCCESS in content:
            return JobState(
                status=JobStatus.SUCCESS,
                message="Finished",
                file=filepath,
                last_modification_time=modification_time,
            )

        if MARKER_STARTED in content:
            return JobState(
                status=JobStatus.CRASHED,
                message="Crashed",
                file=filepath,
                last_modification_time=modification_time,
            )

        return JobState(
            status=JobStatus.UNKNOWN,
            message="Unknown log format",
            file=filepath,
            last_modification_time=modification_time,
        )

    except Exception as e:
        return JobState(
            status=JobStatus.ERROR,
            message=str(e),
            file=filepath,
        )


def _check_daily(last_run: datetime, current_time: datetime) -> bool:
    return last_run.date() == current_time.date()


def _check_weekly(last_run: datetime, current_time: datetime) -> bool:
    return last_run.isocalendar()[:2] == current_time.isocalendar()[:2]


def _check_monthly(last_run: datetime, current_time: datetime) -> bool:
    return (last_run.month == current_time.month) and (
        last_run.year == current_time.year
    )


FREQUENCY_STRATEGIES: dict[JobFrequency, Callable[[datetime, datetime], bool]] = {
    JobFrequency.DAILY: _check_daily,
    JobFrequency.WEEKLY: _check_weekly,
    JobFrequency.MONTHLY: _check_monthly,
}
