#!/usr/bin/env python3
"""Watch a directory for new files and log their names."""

import argparse
import logging
import sys
import time
from pathlib import Path

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class FileMonitor(FileSystemEventHandler):
    def __init__(self, log_all=False):
        self.log_all = log_all
        self.logger = logging.getLogger("folder-monitor")

    def on_created(self, event):
        if not event.is_directory:
            self.logger.info("NEW  → %s", Path(event.src_path).name)

    def on_modified(self, event):
        if self.log_all and not event.is_directory:
            self.logger.info("MOD  → %s", Path(event.src_path).name)

    def on_deleted(self, event):
        if self.log_all and not event.is_directory:
            self.logger.info("DEL  → %s", Path(event.src_path).name)


def setup_logging(log_file):
    logger = logging.getLogger("folder-monitor")
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("[%(asctime)s] %(message)s", datefmt="%Y-%m-%dT%H:%M:%S")

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(fmt)
    logger.addHandler(console)

    if log_file:
        try:
            fh = logging.FileHandler(log_file, mode="a")
            fh.setFormatter(fmt)
            logger.addHandler(fh)
        except OSError as e:
            logger.warning("Could not open log file %s: %s (logging to console only)", log_file, e)

    return logger


def main():
    parser = argparse.ArgumentParser(description="Monitor a folder for new files and log their names.")
    parser.add_argument("path", nargs="?", default=".", help="Directory to watch (default: current dir)")
    parser.add_argument("--log", default="monitor.log", help="Log file path (default: monitor.log)")
    parser.add_argument("--no-log-file", action="store_true", help="Disable file logging, console only")
    parser.add_argument("--all", action="store_true", help="Also log modifications and deletions")
    parser.add_argument("--recursive", action="store_true", help="Watch subdirectories too")
    args = parser.parse_args()

    watch_path = Path(args.path).resolve()
    if not watch_path.is_dir():
        print(f"Error: '{watch_path}' is not a directory or does not exist.", file=sys.stderr)
        sys.exit(1)

    log_file = None if args.no_log_file else args.log
    logger = setup_logging(log_file)

    handler = FileMonitor(log_all=args.all)
    observer = Observer()
    observer.schedule(handler, str(watch_path), recursive=args.recursive)
    observer.start()

    mode = "all events" if args.all else "new files"
    recursive_label = " (recursive)" if args.recursive else ""
    logger.info("Monitoring %s for %s%s — press Ctrl+C to stop", watch_path, mode, recursive_label)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down.")
        observer.stop()

    observer.join()


if __name__ == "__main__":
    main()
