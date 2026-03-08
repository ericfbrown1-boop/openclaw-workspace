# Folder Monitor

Watch a directory for new files and log their names with timestamps.

## Setup

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Watch current directory
python monitor.py

# Watch a specific folder
python monitor.py /Users/eric/Downloads

# Watch recursively, log all events (new, modified, deleted)
python monitor.py /Users/eric/Downloads --recursive --all

# Custom log file
python monitor.py . --log /tmp/file-events.log

# Console only (no log file)
python monitor.py . --no-log-file
```

## Output

```
[2026-03-08T13:05:22] Monitoring /Users/eric/Downloads for new files — press Ctrl+C to stop
[2026-03-08T13:05:30] NEW  → report.pdf
[2026-03-08T13:05:45] NEW  → data.csv
```

With `--all`:
```
[2026-03-08T13:05:30] NEW  → report.pdf
[2026-03-08T13:06:01] MOD  → report.pdf
[2026-03-08T13:06:15] DEL  → old-file.txt
```

Events are logged to both the console and `monitor.log` (default).

## Options

| Flag | Description |
|------|-------------|
| `path` | Directory to watch (default: `.`) |
| `--log FILE` | Log file path (default: `monitor.log`) |
| `--no-log-file` | Console output only |
| `--all` | Also log modifications and deletions |
| `--recursive` | Watch subdirectories |
