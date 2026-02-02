from datetime import datetime

from pydantic import BaseModel

from .enums import JobFrequency, JobStatus


class Job(BaseModel):
    name: str
    frequency: JobFrequency
    log_pattern: str
    process_pattern: str


class JobState(BaseModel):
    status: JobStatus
    message: str
    file: str | None
    last_modification_time: datetime | None = None
