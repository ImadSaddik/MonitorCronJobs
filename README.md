# Monitor cron jobs

[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](./LICENSE)

This project is a monitoring suite for Ubuntu that automates the tracking of cron jobs, replacing the tedious process of manually navigating to log folders and opening files to check execution status. It provides a **system tray app** for instant visual feedback and a **CLI tool** for rapid status checks and log inspection.

This project uses a **calendar-based state machine** to verify that jobs ran within their designated schedule (e.g., *today* or *this week*). This prevents "silent failures" where a task stops running entirely, but the old successful log remains in place.

![System tray application interface showing job list and detailed view](./images/system_tray_app_states.svg)

The system tray menu showing the daily job list (left) and the detailed status view for a specific task (right).

[https://github.com/user-attachments/assets/79dc0905-51a4-4a0b-aec1-95f51dd36ce3](https://github.com/user-attachments/assets/79dc0905-51a4-4a0b-aec1-95f51dd36ce3)

The CLI interface allows for rapid status checks and instant log inspection by job ID.

## Environment setup

### System dependencies

Since this project uses [GTK](https://www.gtk.org/) and `AppIndicators` for the system tray, the following system libraries are required:

```bash
# Ubuntu 24.04+
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-ayatanaappindicator3-0.1 libgirepository1.0-dev libcairo2-dev
```

Explanation of packages:

- `python3-gi`: Python bindings for GObject-based libraries (GTK).
- `gir1.2-gtk-3.0`: The GTK+ 3.0 graphics library.
- `gir1.2-ayatanaappindicator3-0.1`: A library and indicator to take menus from applications and place them in the panel.
- `libgirepository1.0-dev & libcairo2-dev`: Development headers required when building Python wrappers.

### Python environment

This project uses [uv](https://docs.astral.sh/uv/) for dependency management.

1. Install uv (if not already installed):

    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

2. Install the project dependencies:

    ```bash
    uv sync
    ```

## Configuration

### The wrapper script

> [!IMPORTANT]
> For the monitor to work, cron jobs **must** use a wrapper script. Do not run worker scripts directly from cron.

The wrapper handles permissions and writes the standardized state tags (`[JOB STARTED]`, `[JOB FAILED]`, `[JOB SUCCEEDED]`) that the monitor requires.

Save this template as `/etc/cron.daily/job-name` (must be executable and root-owned):

```bash
#!/bin/bash
set -e

TARGET_USER="your_username"
LOG_DIR="/home/$TARGET_USER/Projects/MyProject/logs"
LOG_FILE="$LOG_DIR/job_name_$(date +%Y-%m-%d).log"

# The command you want to run.
# This can be a script path OR a chain of commands (Conda, cd, python, etc.)
WORKER_CMD="/home/$TARGET_USER/Projects/MyProject/worker.sh"

mkdir -p "$LOG_DIR"
touch "$LOG_FILE"
chown -R $TARGET_USER:$TARGET_USER "$LOG_DIR"

# Redirect all output (stdout and stderr) to log
exec >> "$LOG_FILE" 2>&1

echo "[JOB STARTED] $(date)"

# Error Trap (Catches crashes & non-zero exits)
handle_error() {
    echo "[JOB FAILED] $(date)"
    exit 1
}
trap 'handle_error' ERR

# Run the command as the target user
su - $TARGET_USER -c "$WORKER_CMD"

echo "[JOB SUCCEEDED] $(date)"
exit 0
```

### Registering jobs

The monitor looks for the configuration file in two places (in this order):

1. `~/.config/monitor_cron/jobs.json` (Recommended)
2. `jobs.json` (Project root fallback)

Create the config directory and file:

```bash
mkdir -p ~/.config/monitor_cron
nano ~/.config/monitor_cron/jobs.json
```

Then add your jobs configuration:

```json
{
    "jobs": [
        {
            "name": "Backup music",
            "frequency": "weekly",
            "log_pattern": "/home/your_username/logs/backup_*.log",
            "process_pattern": "backup_music"
        }
    ]
}
```

Configuration breakdown:

- **`frequency`**: How often the job should run. Accepted values are: `daily`, `weekly`, `monthly`.
- **`log_pattern`**: A glob pattern to find the log files. The monitor always reads the newest file matching this pattern.
- **`process_pattern`**: The name of the script or command (used by `pgrep -f`). If found, the status becomes **⏳ RUNNING** immediately.

> [!TIP]
>
> Use the name of your wrapper script (e.g., if your wrapper is `/etc/cron.daily/backup_music`, use `"process_pattern": "backup_music"`).

## Usage

### CLI tool

The CLI tool checks job status from the terminal.

```bash
# Quick status check
uv run cron-status

# View the latest log for a specific job (by ID)
uv run cron-status 1
```

> [!NOTE]
>
> `cron-status` is the command defined in the project. It is equivalent to running `uv run python -m monitor_cron.cli`.

To run this command globally (from any terminal without manually activating the environment):

1. Create a new file in `/usr/local/bin/`:

    ```bash
    sudo nano /usr/local/bin/cron-status
    ```

2. Paste the following content (update `PROJECT_DIR` to match your system):

    ```bash
    #!/bin/bash
    PROJECT_DIR="$HOME/Projects/MonitorCronJobs"

    uv run --directory "$PROJECT_DIR" cron-status "$@"
    ```

3. Make the file executable:

    ```bash
    sudo chmod +x /usr/local/bin/cron-status
    ```

Now you can run `cron-status` from any terminal!

```bash
cron-status
cron-status 1
```

### System tray app

You can run the system tray app manually:

```bash
uv run cron-tray
```

> [!NOTE]
>
> `cron-tray` is the command defined in the project. It is equivalent to running `uv run python -m monitor_cron.tray`.

Or you can set it to start automatically on login.

1. Create a `.desktop` file:

    ```bash
    nano ~/.config/autostart/cron-monitor.desktop
    ```

2. Paste the following content (update the paths to match your system):

    ```ini
    [Desktop Entry]
    Type=Application
    Name=Cron monitor
    Comment=Monitors the status of cron jobs
    # Update the path to point to your project folder
    Exec=/usr/bin/env uv run --directory /home/your_username/Projects/MonitorCronJobs cron-tray
    Path=/home/your_username/Projects/MonitorCronJobs
    Icon=utilities-system-monitor
    Terminal=false
    Hidden=false
    NoDisplay=false
    X-GNOME-Autostart-enabled=true
    ```

> [!WARNING]
> Use absolute paths in the `.desktop` file (not `~`), as tilde expansion may not work reliably.

## License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.

## Contact

- **Email** – [simad3647@gmail.com](mailto:simad3647@gmail.com)
- **LinkedIn** – [Connect with me](https://www.linkedin.com/in/imadsaddik/)
