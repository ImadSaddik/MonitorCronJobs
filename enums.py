from enum import StrEnum


class JobFrequency(StrEnum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class JobStatus(StrEnum):
    STALE = "STALE"
    ERROR = "ERROR"
    FAILED = "FAILED"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    CRASHED = "CRASHED"
    MISSING = "MISSING"
    UNKNOWN = "UNKNOWN"
