# PLAN.md — Folder Monitor

## Overview
A simple Python script that watches a directory for new files and logs their names with timestamps.

**Developer:** Eric Brown (solo)
**Runtime:** Python 3
**Database:** None

---

## 1. Approach: watchdog Library

| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| **watchdog** | Cross-platform, event-driven, mature | External dep | ✅ **Winner** |
| `os.listdir` polling | Zero deps | CPU waste, misses fast changes | ❌ |
| `inotify` (Linux) | Kernel-level, fast | Linux only | ❌ |
| `fsevents` (macOS) | Native, fast | macOS only | ❌ |

**Why watchdog:**
- Uses native OS events under the hood (FSEvents on macOS, inotify on Linux, ReadDirectoryChanges on Windows)
- Simple Observer/Handler API — ~50 lines of code
- Well-maintained, 6k+ GitHub stars
- One dependency covers all platforms

---

## 2. File Structure

```
folder-monitor/
├── PLAN.md              # This file
├── monitor.py           # Main script (~50 lines)
├── requirements.txt     # watchdog
└── README.md            # Usage instructions
```

---

## 3. Dependencies

```txt
watchdog>=4.0
```

**Total deps: 1.** That's it.

---

## 4. Features

- Watch any directory (passed as CLI arg, defaults to current dir)
- Detect new files created in the folder
- Log to both console and a log file (`monitor.log`)
- Timestamps in ISO 8601 format
- Optional: detect modifications and deletions (flag-controlled)
- Graceful shutdown on Ctrl+C

---

## 5. Output Format

### Console
```
[2026-03-08T13:05:22] NEW  → report.pdf
[2026-03-08T13:05:45] NEW  → data.csv
[2026-03-08T13:06:01] NEW  → screenshot.png
```

### Log file (`monitor.log`)
Same format, appended. Rotates aren't needed for a simple script — just tail it.

---

## 6. Logic Flow

```
1. Parse args: target directory, optional flags
2. Set up Python logging (console + file handler)
3. Create watchdog Observer + FileSystemEventHandler subclass
4. Override on_created() to log new file name + timestamp
5. Start observer, loop until KeyboardInterrupt
6. Clean shutdown: observer.stop(), observer.join()
```

---

## 7. Error Handling

| Scenario | Behavior |
|----------|----------|
| Directory doesn't exist | Print error, exit code 1 |
| Permission denied | Print error, exit code 1 |
| File created then immediately deleted | Log creation, ignore missing file gracefully |
| Ctrl+C | Clean shutdown message, exit code 0 |
| Log file write fails | Fall back to console-only, warn user |

---

## 8. Implementation Steps

### Step 1: Scaffold
- Create `requirements.txt` with `watchdog`
- `pip install -r requirements.txt`

### Step 2: Argument Parsing
- `argparse` for:
  - `path` (positional, default `.`)
  - `--log` (log file path, default `monitor.log`)
  - `--all` (also log modifications and deletions)
  - `--recursive` (watch subdirectories too)

### Step 3: Event Handler
- Subclass `FileSystemEventHandler`
- `on_created()` → log new file
- Optionally `on_modified()`, `on_deleted()` behind `--all` flag
- Filter out directories (only log files, not folder creation)

### Step 4: Observer Loop
- Create `Observer()`, schedule handler on target path
- `observer.start()`
- `while True: time.sleep(1)` with KeyboardInterrupt catch
- Clean stop

### Step 5: Polish
- Startup banner: "Monitoring /path/to/dir — press Ctrl+C to stop"
- Write README.md

---

## 9. Usage (Target)

```bash
# Watch current directory
python monitor.py

# Watch specific folder
python monitor.py /Users/eric/Downloads

# Watch recursively, log all events
python monitor.py /Users/eric/Downloads --recursive --all

# Custom log file
python monitor.py . --log /tmp/file-events.log
```

---

## 10. Future Enhancements (Out of Scope)
- Filter by file extension (e.g., only `.csv` files)
- Send notifications (email/Slack) on new files
- Move/rename detected files automatically
- Systemd/launchd service wrapper

---

*Plan created: 2026-03-08*
