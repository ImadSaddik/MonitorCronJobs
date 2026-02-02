import subprocess
from unittest.mock import patch

import core


class TestIsJobRunning:
    """Tests for the is_job_running function."""

    def test_is_job_running_process_found(self) -> None:
        """Test when process is found."""
        with patch.object(subprocess, "call", return_value=0):
            result = core.is_job_running("test_process")

        assert result is True

    def test_is_job_running_process_not_found(self) -> None:
        """Test when process is not found."""
        with patch.object(subprocess, "call", return_value=1):
            result = core.is_job_running("nonexistent_process")

        assert result is False

    def test_is_job_running_none_pattern(self) -> None:
        """Test with None pattern."""
        result = core.is_job_running(None)

        assert result is False

    def test_is_job_running_empty_pattern(self) -> None:
        """Test with empty string pattern."""
        result = core.is_job_running("")

        assert result is False

    def test_is_job_running_exception_handling(self) -> None:
        """Test exception handling in is_job_running."""
        with patch.object(subprocess, "call", side_effect=Exception("Test error")):
            result = core.is_job_running("test_process")

        assert result is False

    def test_is_job_running_calls_pgrep_correctly(self) -> None:
        """Test that pgrep is called with correct arguments."""
        with patch.object(subprocess, "call", return_value=0) as mock_call:
            core.is_job_running("my_process")

            mock_call.assert_called_once()
            args = mock_call.call_args[1]["args"]

            assert args[0] == "pgrep"
            assert args[1] == "-f"
            assert args[2] == "my_process"
            assert mock_call.call_args[1]["stdout"] == subprocess.DEVNULL
            assert mock_call.call_args[1]["stderr"] == subprocess.DEVNULL
