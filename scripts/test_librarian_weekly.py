#!/usr/bin/env python3
"""Unit tests for librarian_weekly.py — stdlib only."""
from __future__ import annotations

import datetime as _dt
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent))
import librarian_weekly as lw  # noqa: E402


class TestParseTs(unittest.TestCase):
    def test_iso_with_z(self):
        r = lw.parse_ts("2026-04-11T23:00:00Z")
        self.assertEqual(r.year, 2026)
        self.assertEqual(r.hour, 23)

    def test_iso_with_offset(self):
        r = lw.parse_ts("2026-04-10T02:25:22.055533+00:00")
        self.assertEqual(r.year, 2026)
        self.assertEqual(r.month, 4)

    def test_epoch_int(self):
        ts = int(_dt.datetime(2026, 4, 11, tzinfo=_dt.timezone.utc).timestamp())
        r = lw.parse_ts(ts)
        self.assertEqual(r.year, 2026)

    def test_none_tolerated(self):
        self.assertIsNone(lw.parse_ts(None))

    def test_malformed(self):
        self.assertIsNone(lw.parse_ts("not a date"))


class TestFilterWindow(unittest.TestCase):
    def test_filters_old_and_new(self):
        now = _dt.datetime(2026, 4, 11)
        incidents = [
            {"timestamp": "2026-04-10T00:00:00Z", "error_category": "auth"},  # 1 day ago
            {"timestamp": "2026-04-03T00:00:00Z", "error_category": "cron"},  # 8 days ago (OUT)
            {"timestamp": "2026-04-05T00:00:00Z", "error_category": "git"},   # 6 days ago
        ]
        r = lw.filter_window(incidents, window_days=7, now=now)
        cats = [i["error_category"] for i in r]
        self.assertIn("auth", cats)
        self.assertIn("git", cats)
        self.assertNotIn("cron", cats)


class TestGroupPatterns(unittest.TestCase):
    def test_groups_and_filters_by_min_count(self):
        incidents = [
            {"timestamp": "2026-04-10T00:00:00Z", "error_category": "auth", "error_summary": "gog expired"},
            {"timestamp": "2026-04-11T00:00:00Z", "error_category": "auth", "error_summary": "gog expired again"},
            {"timestamp": "2026-04-11T00:00:00Z", "error_category": "auth", "error_summary": "gog expired"},  # dup summary
            {"timestamp": "2026-04-10T00:00:00Z", "error_category": "cron", "error_summary": "cron storm"},
        ]
        patterns = lw.group_patterns(incidents, min_count=2)
        self.assertEqual(len(patterns), 1)  # cron only had 1
        p = patterns[0]
        self.assertEqual(p["category"], "auth")
        self.assertEqual(p["count"], 3)
        self.assertEqual(len(p["summaries"]), 2)  # de-duped

    def test_empty_when_no_repeats(self):
        incidents = [
            {"timestamp": "2026-04-10T00:00:00Z", "error_category": "auth"},
            {"timestamp": "2026-04-11T00:00:00Z", "error_category": "cron"},
        ]
        self.assertEqual(lw.group_patterns(incidents, min_count=2), [])

    def test_sorted_by_count_desc(self):
        incidents = [
            {"timestamp": "2026-04-10T00:00:00Z", "error_category": "a"},
            {"timestamp": "2026-04-10T00:00:00Z", "error_category": "a"},
            {"timestamp": "2026-04-10T00:00:00Z", "error_category": "b"},
            {"timestamp": "2026-04-10T00:00:00Z", "error_category": "b"},
            {"timestamp": "2026-04-10T00:00:00Z", "error_category": "b"},
        ]
        patterns = lw.group_patterns(incidents, min_count=2)
        self.assertEqual([p["category"] for p in patterns], ["b", "a"])


class TestRenderReport(unittest.TestCase):
    def test_empty_report_has_green_message(self):
        out = lw.render_report([], 7, 5, 3)
        self.assertIn("No recurring patterns", out)
        self.assertIn("type: feedback", out)  # correct frontmatter

    def test_populated_report_contains_pattern(self):
        patterns = [{
            "category": "auth",
            "count": 3,
            "earliest": "2026-04-09T00:00:00Z",
            "latest": "2026-04-11T00:00:00Z",
            "summaries": ["gog expired", "token revoked"],
            "most_recent": {"root_cause": "scope undeclared", "prevention": "declare scopes"},
        }]
        out = lw.render_report(patterns, 7, 10, 3)
        self.assertIn("`auth`", out)
        self.assertIn("3 incidents", out)
        self.assertIn("scope undeclared", out)
        self.assertIn("declare scopes", out)
        self.assertIn("type: feedback", out)


class TestAtomicWrite(unittest.TestCase):
    def test_write_and_read(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "sub" / "report.md"
            lw.atomic_write(p, "hello")
            self.assertEqual(p.read_text(), "hello")
            # No .tmp leaks
            names = sorted(x.name for x in Path(d).rglob("*"))
            self.assertIn("report.md", names)


class TestMain(unittest.TestCase):
    def test_end_to_end_on_real_schema(self):
        """Feed a realistic incidents.jsonl and assert the report is written."""
        with tempfile.TemporaryDirectory() as d:
            dp = Path(d)
            incidents = dp / "incidents.jsonl"
            report_dir = dp / "claude" / "memory"
            report = report_dir / "librarian_weekly_patterns.md"
            log_dir = dp / "logs"
            skills = dp / "memory" / "skill-suggestions.md"
            now = _dt.datetime.now(_dt.timezone.utc)
            recent = (now - _dt.timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
            old = (now - _dt.timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
            incidents.write_text(
                json.dumps({"timestamp": recent, "error_category": "auth", "error_summary": "gog", "root_cause": "scope", "prevention": "declare"}) + "\n" +
                json.dumps({"timestamp": recent, "error_category": "auth", "error_summary": "gog2"}) + "\n" +
                json.dumps({"timestamp": recent, "error_category": "cron", "error_summary": "storm"}) + "\n" +
                json.dumps({"timestamp": old, "error_category": "ignored", "error_summary": "stale"}) + "\n"
            )
            with mock.patch.multiple(
                lw,
                INCIDENTS_PATH=incidents,
                REPORT_DIR=report_dir,
                REPORT_PATH=report,
                LOG_DIR=log_dir,
                LOG_PATH=log_dir / "librarian.log",
                SKILL_SUGGESTIONS_PATH=skills,
            ):
                rc = lw.main([])
            self.assertEqual(rc, 0)
            self.assertTrue(report.exists())
            content = report.read_text()
            self.assertIn("type: feedback", content)
            self.assertIn("auth", content)  # auth has 2 incidents in window → pattern
            self.assertNotIn("ignored", content)  # outside window
            self.assertTrue(skills.exists())
            self.assertIn("auth×2", skills.read_text())


if __name__ == "__main__":
    unittest.main(verbosity=2)
