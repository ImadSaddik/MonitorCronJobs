import json
from pathlib import Path

from pytest import MonkeyPatch

import core
from enums import JobFrequency


class TestLoadJobs:
    """Tests for the load_jobs function."""

    def test_load_jobs_success(
        self,
        jobs_json_file: Path,
        monkeypatch: MonkeyPatch,
    ) -> None:
        """Test loading jobs from a valid JSON file."""
        monkeypatch.setattr(core, "JOBS_FILE", str(jobs_json_file))

        jobs = core.load_jobs()

        assert len(jobs) == 3
        assert jobs[0].name == "Daily Backup"
        assert jobs[0].frequency == JobFrequency.DAILY

        assert jobs[1].name == "Weekly Report"
        assert jobs[1].frequency == JobFrequency.WEEKLY

        assert jobs[2].name == "Monthly Cleanup"
        assert jobs[2].frequency == JobFrequency.MONTHLY

    def test_load_jobs_empty_file(
        self,
        temp_dir: Path,
        monkeypatch: MonkeyPatch,
    ):
        """Test loading from a file with no jobs."""
        empty_file = temp_dir / "empty.json"
        empty_file.write_text('{"jobs": []}')
        monkeypatch.setattr(core, "JOBS_FILE", str(empty_file))

        jobs = core.load_jobs()

        assert jobs == []

    def test_load_jobs_file_not_found(self, monkeypatch: MonkeyPatch) -> None:
        """Test handling of missing jobs file."""
        monkeypatch.setattr(core, "JOBS_FILE", "/nonexistent/path.json")

        jobs = core.load_jobs()

        assert jobs == []

    def test_load_jobs_invalid_json(
        self,
        temp_dir: Path,
        monkeypatch: MonkeyPatch,
    ) -> None:
        """Test handling of malformed JSON."""
        invalid_file = temp_dir / "invalid.json"
        invalid_file.write_text("not valid json{")
        monkeypatch.setattr(core, "JOBS_FILE", str(invalid_file))

        jobs = core.load_jobs()

        assert jobs == []

    def test_load_jobs_missing_required_fields(
        self,
        temp_dir: Path,
        monkeypatch: MonkeyPatch,
    ) -> None:
        """Test handling of jobs with missing required fields."""
        invalid_data = {
            "jobs": [
                {
                    "name": "Incomplete Job",
                    "frequency": "daily",
                    # Missing log_pattern and process_pattern
                }
            ]
        }

        invalid_file = temp_dir / "incomplete.json"
        with open(invalid_file, "w") as f:
            json.dump(invalid_data, f)

        monkeypatch.setattr(core, "JOBS_FILE", str(invalid_file))

        jobs = core.load_jobs()

        assert jobs == []
