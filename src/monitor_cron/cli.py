import argparse
import subprocess

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from . import core
from .enums import JobStatus
from .models import Job

console = Console()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "id",
        nargs="?",
        type=int,
        help="The job number to view logs for (as shown in the status table)",
    )

    args = parser.parse_args()
    jobs = core.load_jobs()

    if args.id:
        view_log(job=jobs[args.id - 1])
    else:
        table = Table(title="Cron job status", box=box.ROUNDED)
        table.add_column("#", style="dim")
        table.add_column("Status")
        table.add_column("Job name", style="bold white")
        table.add_column("Details", style="dim")

        for i, job in enumerate(jobs, 1):
            status_display, details = check_job(job)
            table.add_row(str(i), status_display, job.name, details)

        console.print(table)


def view_log(job: Job) -> None:
    """Opens the log file for a given job in less."""
    state = core.get_job_state(job)
    if not state.file:
        console.print(f"[red]No log file found for [bold]{job.name}[/bold][/red]")
        return

    console.print(
        Panel(
            f"[bold cyan]{job.name}[/bold cyan]\n[dim]{state.file}[/dim]",
            title="Viewing log",
            border_style="cyan",
        )
    )

    # +G is used to go to the end of the file in less
    subprocess.call(["less", "+G", state.file])


def check_job(job: Job) -> tuple[Text, str]:
    """Checks the status of a job and returns its display text and details."""
    state = core.get_job_state(job)

    if not state:
        return _get_status_display(JobStatus.UNKNOWN), "Could not determine job state"

    return _get_status_display(state.status), state.message


def _get_status_display(status: JobStatus) -> Text:
    """Retrieves the UI configuration for a given status."""
    icon, style = JOB_STATUS_STYLES.get(status, JOB_STATUS_STYLES[JobStatus.UNKNOWN])
    return Text(f"{icon} {status.value}", style=style)


JOB_STATUS_STYLES = {
    JobStatus.RUNNING: ("⏳", "cyan bold"),
    JobStatus.MISSING: ("⚪", "red"),
    JobStatus.STALE: ("🟡", "yellow bold"),
    JobStatus.FAILED: ("🔴", "red bold"),
    JobStatus.SUCCESS: ("🟢", "green bold"),
    JobStatus.CRASHED: ("🔴", "red bold"),
    JobStatus.UNKNOWN: ("❓", "red"),
}


if __name__ == "__main__":
    main()
