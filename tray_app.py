import os
import signal
import sys
from typing import Any, Callable

import gi

import core
from enums import JobStatus
from models import Job, JobState

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import GLib, Gtk  # noqa: E402


def main() -> None:
    # Handle Ctrl+C gracefully
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = CronMonitorApp()
    exit_status = app.run(sys.argv)
    sys.exit(exit_status)


class CronMonitorApp(Gtk.Application):
    def __init__(self) -> None:
        super().__init__(application_id="com.imadsaddik.cronmonitor")
        self.tray: TrayController | None = None
        self.menu: Any | None = None
        self.jobs: list[Job] = []
        self.job_rows: list[JobRow] = []

    def do_activate(self) -> None:
        # This is a tray-only app. No main window required.
        pass

    def do_startup(self) -> None:
        Gtk.Application.do_startup(self)
        self.hold()  # Keep app alive

        self.menu = GMenu()
        self.jobs = core.load_jobs()

        self._build_menu()
        self.tray = TrayController("cron_monitor_id", self.menu)

        # Start the loop
        self.refresh_jobs()
        GLib.timeout_add_seconds(60, self._on_timer_tick)

    def _build_menu(self) -> None:
        """Constructs the tray menu sections grouped by frequency."""
        if not self.menu:
            return

        jobs_by_frequency = _group_jobs_by_frequency(self.jobs)

        for i, (frequency, jobs) in enumerate(jobs_by_frequency.items()):
            if i > 0:
                self.menu.append(GSeparatorMenuItem())

            self._add_header(f"{frequency} jobs")

            for job in jobs:
                row = JobRow(job, self.open_log)
                self.job_rows.append(row)
                self.menu.append(row.root_item)

        self._add_footer()
        self.menu.show_all()

    def _add_header(self, label: str) -> None:
        if self.menu is None:
            return

        header = GMenuItem(label=label.capitalize())
        header.set_sensitive(False)
        self.menu.append(header)

    def _add_footer(self) -> None:
        if self.menu is None:
            return

        self.menu.append(GSeparatorMenuItem())
        quit_item = GMenuItem(label="Quit monitor")
        quit_item.connect("activate", lambda _: self.quit())
        self.menu.append(quit_item)

    def _on_timer_tick(self) -> bool:
        self.refresh_jobs()
        return True

    def refresh_jobs(self) -> None:
        if not self.tray:
            return

        current_statuses = [
            row.update(core.get_job_state(row.job)) for row in self.job_rows
        ]

        global_icon, global_description = _get_global_app_status(current_statuses)
        self.tray.set_status(global_icon, global_description)

    def open_log(self, job: Job) -> None:
        result = core.get_job_state(job)
        if result.file:
            try:
                GShowUri(
                    None, f"file://{os.path.abspath(result.file)}", GGetCurrentTime()
                )
            except Exception as e:
                print(f"Failed to open file: {e}")


class TrayController:
    """Manages the system tray icon."""

    def __init__(self, app_id: str, menu: Any) -> None:
        self.indicator = _get_app_indicator().Indicator.new(
            app_id,
            TRAY_ICON_SUCCESS,
            _get_app_indicator().IndicatorCategory.APPLICATION_STATUS,  # type: ignore
        )
        self.indicator.set_status(_get_app_indicator().IndicatorStatus.ACTIVE)  # type: ignore
        self.indicator.set_menu(menu)

    def set_status(self, icon_name: str, description: str) -> None:
        self.indicator.set_icon_full(icon_name, description)


class JobRow:
    """Manages the UI elements (menu items) for a single job."""

    def __init__(self, job: Job, open_log_callback: Callable[[Job], None]) -> None:
        self.job = job
        self.open_log_callback = open_log_callback

        # UI components
        self.root_item = GMenuItem(label=f"Initializing {job.name}")
        self.submenu = GMenu()
        self.root_item.set_submenu(self.submenu)

        self.message_item = self._add_item("Checking", sensitive=False)
        self.time_item = self._add_item("Time: --", sensitive=False)
        self.log_item = self._add_item("Open log file", sensitive=True)

        self.log_item.connect("activate", lambda _: self.open_log_callback(self.job))
        self.log_item.hide()

    def update(self, state: JobState) -> str:
        """Updates the UI and returns the current status string."""

        # Update main label
        icon = JOB_STATUS_ICONS.get(state.status, JOB_STATUS_ICONS[JobStatus.UNKNOWN])
        self.root_item.set_label(f"{icon} {self.job.name}")

        # Update details
        self.message_item.set_label(f"Status: {state.message}")

        if state.last_modification_time:
            self.time_item.set_label(
                f"Last run: {state.last_modification_time.strftime('%d-%m-%Y %H:%M')}"
            )
            self.time_item.show()
        else:
            self.time_item.hide()

        # Update actions
        if state.file:
            self.log_item.show()
        else:
            self.log_item.hide()

        return state.status

    def _add_item(self, label: str, sensitive: bool = True) -> Any:
        item = GMenuItem(label=label)
        item.set_sensitive(sensitive)
        self.submenu.append(item)
        return item


def _group_jobs_by_frequency(jobs: list[Job]) -> dict[str, list[Job]]:
    groups: dict[str, list[Job]] = {}
    for job in jobs:
        groups.setdefault(job.frequency, []).append(job)
    return groups


def _get_global_app_status(statuses: list[str]) -> tuple[str, str]:
    """Determines the tray icon based on the worst status in the list."""
    if any(status in FAIL_STATUSES for status in statuses):
        return TRAY_ICON_FAIL, "Job failure detected"

    if any(status in WARN_STATUSES for status in statuses):
        return TRAY_ICON_WARN, "Warnings present"

    return TRAY_ICON_SUCCESS, "All systems operational"


def _get_app_indicator() -> Any:
    """Lazy loads AppIndicator to keep the top-level import clean."""
    try:
        gi.require_version("AyatanaAppIndicator3", "0.1")
        from gi.repository import AyatanaAppIndicator3 as AppIndicator

        return AppIndicator
    except (ValueError, ImportError, OSError):
        try:
            gi.require_version("AppIndicator3", "0.1")
            from gi.repository import AppIndicator3 as AppIndicator

            return AppIndicator
        except (ValueError, ImportError):
            print("Error: System tray support not found.")
            sys.exit(1)


TRAY_ICON_SUCCESS = "emblem-default"
TRAY_ICON_WARN = "emblem-synchronizing"
TRAY_ICON_FAIL = "emblem-important"

JOB_STATUS_ICONS = {
    JobStatus.SUCCESS: "🟢",
    JobStatus.RUNNING: "⏳",
    JobStatus.STALE: "🟡",
    JobStatus.FAILED: "🔴",
    JobStatus.CRASHED: "🔴",
    JobStatus.MISSING: "⚪",
    JobStatus.UNKNOWN: "⚪",
    JobStatus.ERROR: "⚪",
}

FAIL_STATUSES = {JobStatus.FAILED, JobStatus.CRASHED, JobStatus.ERROR}
WARN_STATUSES = {JobStatus.STALE, JobStatus.MISSING, JobStatus.UNKNOWN}

# Type-checker workaround for dynamic Gtk 3 bindings
GMenu: Any = Gtk.Menu  # type: ignore
GMenuItem: Any = Gtk.MenuItem  # type: ignore
GSeparatorMenuItem: Any = Gtk.SeparatorMenuItem  # type: ignore
GShowUri: Any = Gtk.show_uri_on_window  # type: ignore
GGetCurrentTime: Any = Gtk.get_current_event_time  # type: ignore


if __name__ == "__main__":
    main()
