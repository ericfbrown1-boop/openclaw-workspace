#!/usr/bin/env python3
"""Unit tests for jarvis_pipeline.py — stdlib unittest only, no pytest dep.

Run:
    python3 -m unittest scripts/test_jarvis_pipeline.py -v
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

# Import from sibling file
sys.path.insert(0, str(Path(__file__).parent))
import jarvis_pipeline as jp  # noqa: E402


class TestWalkForKey(unittest.TestCase):
    def test_finds_top_level(self):
        self.assertEqual(jp.walk_for_key({"finalAssistantVisibleText": "hi"}, "finalAssistantVisibleText"), "hi")

    def test_finds_nested(self):
        obj = {"a": {"b": {"finalAssistantVisibleText": "nested"}}}
        self.assertEqual(jp.walk_for_key(obj, "finalAssistantVisibleText"), "nested")

    def test_finds_in_list(self):
        obj = {"items": [{"x": 1}, {"finalAssistantVisibleText": "in-list"}]}
        self.assertEqual(jp.walk_for_key(obj, "finalAssistantVisibleText"), "in-list")

    def test_returns_none_when_absent(self):
        self.assertIsNone(jp.walk_for_key({"a": 1}, "finalAssistantVisibleText"))

    def test_real_openclaw_shape(self):
        # Shape discovered from live dispatches in session
        sample = {
            "result": {
                "session": {
                    "finalAssistantVisibleText": "pong",
                    "stopReason": "stop",
                    "model": "xai/grok-4.20",
                }
            }
        }
        self.assertEqual(jp.walk_for_key(sample, "finalAssistantVisibleText"), "pong")
        self.assertEqual(jp.walk_for_key(sample, "stopReason"), "stop")
        self.assertEqual(jp.walk_for_key(sample, "model"), "xai/grok-4.20")


class TestAtomicWriteJson(unittest.TestCase):
    def test_atomic_write_and_read(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "sub" / "state.json"
            jp.atomic_write_json(p, {"a": 1, "b": [1, 2, 3]})
            self.assertTrue(p.exists())
            with open(p) as f:
                self.assertEqual(json.load(f), {"a": 1, "b": [1, 2, 3]})

    def test_no_tmp_leaks_on_success(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "state.json"
            jp.atomic_write_json(p, {"ok": True})
            # Only the final file, no .tmp stragglers
            names = sorted(x.name for x in Path(d).iterdir())
            self.assertEqual(names, ["state.json"])


class TestStateLock(unittest.TestCase):
    def test_lock_blocks_second_acquirer(self):
        with tempfile.TemporaryDirectory() as d:
            lock = Path(d) / "pipeline.lock"
            with jp.StateLock(lock):
                with self.assertRaises(jp.PipelineError):
                    with jp.StateLock(lock):
                        pass
            # after release, it should work again
            with jp.StateLock(lock):
                pass


class TestLoadTask(unittest.TestCase):
    def test_missing_file_raises(self):
        with tempfile.TemporaryDirectory() as d:
            with mock.patch.object(jp, "TASKS_OPENCLAW", Path(d) / "nope.json"):
                with self.assertRaises(jp.TaskNotFound):
                    jp.load_task("any")

    def test_missing_task_raises(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "tasks.json"
            p.write_text(json.dumps({"tasks": {"other": {"id": "other", "title": "t", "verificationCmd": "x"}}}))
            with mock.patch.object(jp, "TASKS_OPENCLAW", p):
                with self.assertRaises(jp.TaskNotFound):
                    jp.load_task("missing")

    def test_missing_required_fields_raises(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "tasks.json"
            p.write_text(json.dumps({"tasks": {"t1": {"id": "t1", "title": "t"}}}))  # no verificationCmd
            with mock.patch.object(jp, "TASKS_OPENCLAW", p):
                with self.assertRaises(jp.PipelineError) as ctx:
                    jp.load_task("t1")
                self.assertIn("verificationCmd", str(ctx.exception))

    def test_happy_path(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "tasks.json"
            p.write_text(json.dumps({
                "tasks": {
                    "t1": {
                        "id": "t1",
                        "title": "Test task",
                        "verificationCmd": "true",
                        "repoPath": "/tmp/x",
                    }
                }
            }))
            with mock.patch.object(jp, "TASKS_OPENCLAW", p):
                task = jp.load_task("t1")
                self.assertEqual(task["id"], "t1")
                self.assertEqual(task["verificationCmd"], "true")


class TestDispatchAgent(unittest.TestCase):
    """dispatch_agent shells out to `openclaw agent`. Mock subprocess.run."""

    def _fake_run(self, stdout: str, returncode: int = 0, raise_timeout: bool = False):
        class FakeProc:
            def __init__(self):
                self.stdout = stdout
                self.stderr = ""
                self.returncode = returncode

        def _runner(*args, **kwargs):
            if raise_timeout:
                raise subprocess.TimeoutExpired(cmd=args[0], timeout=kwargs.get("timeout", 0))
            return FakeProc()

        return _runner

    def test_happy_path(self):
        fake_out = json.dumps({
            "result": {
                "finalAssistantVisibleText": "hello",
                "stopReason": "stop",
                "model": "xai/grok-4.20",
            }
        })
        with tempfile.TemporaryDirectory() as d:
            with mock.patch("jarvis_pipeline.subprocess.run", side_effect=self._fake_run(fake_out)):
                out = jp.dispatch_agent("researcher", "hi", 60, Path(d) / "log.txt")
                self.assertEqual(out.text, "hello")
                self.assertEqual(out.stop_reason, "stop")
                self.assertEqual(out.model, "xai/grok-4.20")
                self.assertGreaterEqual(out.duration_sec, 0)

    def test_non_zero_exit_raises(self):
        with tempfile.TemporaryDirectory() as d:
            with mock.patch(
                "jarvis_pipeline.subprocess.run",
                side_effect=self._fake_run("error output", returncode=1),
            ):
                with self.assertRaises(jp.DispatchError):
                    jp.dispatch_agent("researcher", "hi", 60, Path(d) / "log.txt")

    def test_invalid_json_raises(self):
        with tempfile.TemporaryDirectory() as d:
            with mock.patch(
                "jarvis_pipeline.subprocess.run",
                side_effect=self._fake_run("not json"),
            ):
                with self.assertRaises(jp.DispatchError):
                    jp.dispatch_agent("researcher", "hi", 60, Path(d) / "log.txt")

    def test_missing_final_text_raises(self):
        fake_out = json.dumps({"result": {"stopReason": "stop"}})
        with tempfile.TemporaryDirectory() as d:
            with mock.patch("jarvis_pipeline.subprocess.run", side_effect=self._fake_run(fake_out)):
                with self.assertRaises(jp.DispatchError):
                    jp.dispatch_agent("researcher", "hi", 60, Path(d) / "log.txt")

    def test_timeout_raises(self):
        with tempfile.TemporaryDirectory() as d:
            with mock.patch(
                "jarvis_pipeline.subprocess.run",
                side_effect=self._fake_run("", raise_timeout=True),
            ):
                with self.assertRaises(jp.DispatchError):
                    jp.dispatch_agent("researcher", "hi", 60, Path(d) / "log.txt")


class TestStageQuality(unittest.TestCase):
    """stage_quality has two gates — verify each."""

    def _make_task(self, cmd: str):
        return {
            "id": "t1",
            "title": "T",
            "verificationCmd": cmd,
            "repoPath": str(Path.home()),
        }

    def _make_pstate(self):
        state = jp.init_pipeline_record({"id": "t1", "title": "T", "verificationCmd": "x", "repoPath": "/tmp"})
        state["stages"]["coder"]["commitSha"] = "abc123"
        return state

    def test_cmd_failure_halts(self):
        task = self._make_task("false")
        pstate = self._make_pstate()
        with tempfile.TemporaryDirectory() as d:
            with mock.patch.multiple(
                jp,
                OUTPUTS_DIR=Path(d),
                PIPELINE_STATE_PATH=Path(d) / "pipeline-state.json",
                OPENCLAW_WORKSPACE=Path(d),
            ):
                with self.assertRaises(jp.QualityGateFailed):
                    jp.stage_quality(task, pstate)
                self.assertEqual(pstate["stages"]["quality"]["status"], "failed")

    def test_cmd_pass_then_llm_approve(self):
        task = self._make_task("true")
        pstate = self._make_pstate()
        fake_out = json.dumps({
            "result": {
                "finalAssistantVisibleText": "### Verdict — APPROVED\n### Reasons\n1. All good",
                "stopReason": "stop",
                "model": "xai/grok-4.20",
            }
        })

        def _runner(*args, **kwargs):
            class FP:
                stdout = fake_out
                stderr = ""
                returncode = 0
            return FP()

        with tempfile.TemporaryDirectory() as d:
            with mock.patch.multiple(
                jp,
                OUTPUTS_DIR=Path(d),
                OPENCLAW_WORKSPACE=Path(d),
                PIPELINE_STATE_PATH=Path(d) / "pipeline-state.json",
            ):
                # subprocess.run is called twice: once for verificationCmd (real),
                # once for openclaw dispatch (mocked). Patch only the 2nd.
                real_run = subprocess.run

                def selective_run(cmd, *a, **kw):
                    if isinstance(cmd, list) and len(cmd) > 0 and cmd[0] == "openclaw":
                        return _runner(cmd, *a, **kw)
                    return real_run(cmd, *a, **kw)

                with mock.patch("jarvis_pipeline.subprocess.run", side_effect=selective_run):
                    jp.stage_quality(task, pstate)
                self.assertEqual(pstate["stages"]["quality"]["status"], "completed")
                self.assertEqual(pstate["stages"]["quality"]["verdict"], "APPROVED")

    def test_cmd_pass_then_llm_reject(self):
        task = self._make_task("true")
        pstate = self._make_pstate()
        fake_out = json.dumps({
            "result": {
                "finalAssistantVisibleText": "### Verdict — REJECTED\n### Reasons\n1. Missing --version",
                "stopReason": "stop",
                "model": "xai/grok-4.20",
            }
        })

        def _runner(*args, **kwargs):
            class FP:
                stdout = fake_out
                stderr = ""
                returncode = 0
            return FP()

        with tempfile.TemporaryDirectory() as d:
            with mock.patch.multiple(
                jp,
                OUTPUTS_DIR=Path(d),
                OPENCLAW_WORKSPACE=Path(d),
                PIPELINE_STATE_PATH=Path(d) / "pipeline-state.json",
            ):
                real_run = subprocess.run

                def selective_run(cmd, *a, **kw):
                    if isinstance(cmd, list) and len(cmd) > 0 and cmd[0] == "openclaw":
                        return _runner(cmd, *a, **kw)
                    return real_run(cmd, *a, **kw)

                with mock.patch("jarvis_pipeline.subprocess.run", side_effect=selective_run):
                    with self.assertRaises(jp.QualityGateFailed):
                        jp.stage_quality(task, pstate)
                self.assertEqual(pstate["stages"]["quality"]["status"], "failed")


class TestUpdateTaskStores(unittest.TestCase):
    def test_dual_write_dict_and_array_forms(self):
        with tempfile.TemporaryDirectory() as d:
            oc = Path(d) / "oc.json"
            mirror = Path(d) / "mirror.json"
            mc = Path(d) / "mc.json"
            oc.write_text(json.dumps({"tasks": {"t1": {"id": "t1", "status": "running", "progress": 0}}}))
            mirror.write_text(json.dumps({"tasks": {"t1": {"id": "t1", "status": "running", "progress": 0}}}))
            mc.write_text(json.dumps([{"id": "t1", "status": "running", "progress": 0, "agentChain": []}]))

            task = {"id": "t1", "title": "T", "verificationCmd": "x", "repoPath": "/tmp"}
            pstate = jp.init_pipeline_record(task)
            for name in jp.STAGES:
                pstate["stages"][name]["status"] = "completed"
            pstate["stages"]["coder"]["commitSha"] = "deadbeef"

            with mock.patch.multiple(
                jp,
                TASKS_OPENCLAW=oc,
                TASKS_OPENCLAW_MIRROR=mirror,
                TASKS_MISSION_CONTROL=mc,
            ):
                jp._update_task_stores(task, pstate)

            oc_data = json.loads(oc.read_text())
            mc_data = json.loads(mc.read_text())
            self.assertEqual(oc_data["tasks"]["t1"]["status"], "completed")
            self.assertEqual(oc_data["tasks"]["t1"]["progress"], 100)
            self.assertEqual(oc_data["tasks"]["t1"]["completedCommit"], "deadbeef")
            self.assertEqual(mc_data[0]["status"], "completed")
            self.assertEqual(mc_data[0]["progress"], 100)
            self.assertEqual(mc_data[0]["completedCommit"], "deadbeef")
            self.assertEqual(mc_data[0]["updates"][-1]["text"], "jarvis-pipeline completed")


class TestResumability(unittest.TestCase):
    def test_completed_stages_are_skipped(self):
        # Seed a pipeline state where researcher+planner are already completed.
        with tempfile.TemporaryDirectory() as d:
            tasks_path = Path(d) / "tasks.json"
            state_path = Path(d) / "pipeline-state.json"
            lock_path = Path(d) / "pipeline-state.json.lock"
            outputs = Path(d) / "outputs"
            tasks_path.write_text(json.dumps({
                "tasks": {
                    "t1": {"id": "t1", "title": "T", "verificationCmd": "true", "repoPath": str(Path(d))}
                }
            }))
            with mock.patch.multiple(
                jp,
                TASKS_OPENCLAW=tasks_path,
                PIPELINE_STATE_PATH=state_path,
                PIPELINE_LOCK_PATH=lock_path,
                OUTPUTS_DIR=outputs,
                OPENCLAW_WORKSPACE=Path(d),
                INCIDENTS_PATH=Path(d) / "incidents.jsonl",
                TASKS_OPENCLAW_MIRROR=Path(d) / "mirror.json",
                TASKS_MISSION_CONTROL=Path(d) / "mc.json",
            ):
                task = jp.load_task("t1")
                pstate = jp.init_pipeline_record(task)
                pstate["stages"]["researcher"]["status"] = "completed"
                pstate["stages"]["planner"]["status"] = "completed"
                pstate["stages"]["auditor"]["status"] = "completed"
                pstate["stages"]["coder"]["status"] = "completed"
                # stage_quality would real-exec "true" — that's fine
                # But we need to also skip the LLM dispatch inside it. Just skip the stage.
                pstate["stages"]["quality"]["status"] = "completed"
                pstate["stages"]["monitor"]["status"] = "completed"
                pstate["stages"]["conductor"]["status"] = "completed"
                jp.save_pipeline_state({"version": 1, "pipelines": {"t1": pstate}})

                # Now run with --resume; every stage should short-circuit
                result = jp.run_pipeline("t1", resume=True, skip_stages=set())
                self.assertEqual(result["status"], "completed")
                for name in jp.STAGES:
                    self.assertEqual(result["stages"][name]["status"], "completed")


class TestMemoryInjection(unittest.TestCase):
    """Verify Planner, Auditor, and Coder stages inject Librarian memory into their prompts."""

    _SENTINEL = "SENTINEL_LIBRARIAN_CONTENT_XYZZY_12345"

    def _patch_and_capture(self, stage_fn, task, pstate):
        """Run a stage with mocked load_librarian_memory + dispatch_agent; return captured message."""
        captured = {}

        def fake_dispatch(agent_id, message, timeout_sec, log_path):
            captured["agent"] = agent_id
            captured["message"] = message
            return jp.AgentOutput(
                text="### Verdict — APPROVED\nok",
                raw={"result": {"finalAssistantVisibleText": "ok", "stopReason": "stop", "model": "test"}},
                duration_sec=0.1,
                stop_reason="stop",
                model="test-model",
            )

        with tempfile.TemporaryDirectory() as d:
            with mock.patch.multiple(
                jp,
                OUTPUTS_DIR=Path(d),
                OPENCLAW_WORKSPACE=Path(d),
                PIPELINE_STATE_PATH=Path(d) / "pipeline-state.json",
                load_librarian_memory=mock.Mock(return_value=f"MEMORY START\n{self._SENTINEL}\nMEMORY END"),
                dispatch_agent=fake_dispatch,
            ):
                stage_fn(task, pstate)
        return captured

    def _make_task(self):
        return {
            "id": "t1",
            "title": "Test task",
            "verificationCmd": "true",
            "repoPath": "/tmp/repo",
            "objective": "Do a thing",
        }

    def test_planner_injects_memory(self):
        task = self._make_task()
        pstate = jp.init_pipeline_record(task)
        captured = self._patch_and_capture(jp.stage_planner, task, pstate)
        self.assertEqual(captured["agent"], "planner")
        self.assertIn("LIBRARIAN MEMORY", captured["message"])
        self.assertIn(self._SENTINEL, captured["message"])
        self.assertIn("Past Lessons Applied", captured["message"])
        # Memory block must precede the TASK section
        self.assertLess(
            captured["message"].index("LIBRARIAN MEMORY"),
            captured["message"].index("TASK:"),
        )
        self.assertEqual(pstate["stages"]["planner"]["librarianBytes"], len(f"MEMORY START\n{self._SENTINEL}\nMEMORY END"))

    def test_auditor_injects_memory(self):
        task = self._make_task()
        pstate = jp.init_pipeline_record(task)
        # Seed a fake planner output
        planner_dir = Path(tempfile.mkdtemp())
        plan_path = planner_dir / "02-plan-draft.md"
        plan_path.write_text("# PLAN.md\nsome plan content")
        pstate["stages"]["planner"]["outputPath"] = "02-plan-draft.md"

        captured = {}

        def fake_dispatch(agent_id, message, timeout_sec, log_path):
            captured["agent"] = agent_id
            captured["message"] = message
            return jp.AgentOutput("APPROVED", {}, 0.1, "stop", "test")

        with mock.patch.multiple(
            jp,
            OUTPUTS_DIR=planner_dir,
            OPENCLAW_WORKSPACE=planner_dir,
            PIPELINE_STATE_PATH=planner_dir / "pipeline-state.json",
            load_librarian_memory=mock.Mock(return_value=f"MEMORY\n{self._SENTINEL}\nEND"),
            dispatch_agent=fake_dispatch,
        ):
            jp.stage_auditor(task, pstate)

        self.assertEqual(captured["agent"], "auditor")
        self.assertIn("LIBRARIAN MEMORY", captured["message"])
        self.assertIn(self._SENTINEL, captured["message"])
        self.assertIn("Applied Lessons", captured["message"])
        self.assertIn("Past-lesson enforcement", captured["message"])

    def test_coder_injects_memory(self):
        task = self._make_task()
        pstate = jp.init_pipeline_record(task)
        # Seed a fake auditor output
        auditor_dir = Path(tempfile.mkdtemp())
        merged = auditor_dir / "03-plan-merged.md"
        merged.write_text("# PLAN.md\nmerged plan content")
        pstate["stages"]["auditor"]["outputPath"] = "03-plan-merged.md"

        captured = {}

        def fake_dispatch(agent_id, message, timeout_sec, log_path):
            captured["agent"] = agent_id
            captured["message"] = message
            return jp.AgentOutput("commit sha abc", {}, 0.1, "stop", "test")

        # git subprocess call for sha — mock subprocess.run to return a fake sha
        real_run = subprocess.run
        def selective_run(cmd, *a, **kw):
            if isinstance(cmd, list) and len(cmd) > 0 and cmd[0] == "git":
                class FP:
                    stdout = "deadbeef\n"
                    returncode = 0
                return FP()
            return real_run(cmd, *a, **kw)

        with mock.patch.multiple(
            jp,
            OUTPUTS_DIR=auditor_dir,
            OPENCLAW_WORKSPACE=auditor_dir,
            PIPELINE_STATE_PATH=auditor_dir / "pipeline-state.json",
            load_librarian_memory=mock.Mock(return_value=f"MEM\n{self._SENTINEL}\nEND"),
            dispatch_agent=fake_dispatch,
        ):
            with mock.patch("jarvis_pipeline.subprocess.run", side_effect=selective_run):
                jp.stage_coder(task, pstate)

        self.assertEqual(captured["agent"], "coder")
        self.assertIn("LIBRARIAN MEMORY", captured["message"])
        self.assertIn(self._SENTINEL, captured["message"])
        self.assertIn("Past Lessons Applied", captured["message"])
        # Memory must precede the merged PLAN.md content block
        self.assertLess(
            captured["message"].index("LIBRARIAN MEMORY"),
            captured["message"].index("=== PLAN.md (merged with Auditor patches) ==="),
        )


class TestPostReviewFixes(unittest.TestCase):
    """New tests covering the post-Grok-review fixes (C1, H1, H4, M1, M2, M4)."""

    def setUp(self):
        self._sleep_patch = mock.patch("time.sleep", return_value=None)
        self._sleep_patch.start()

    def tearDown(self):
        self._sleep_patch.stop()

    # ─── H1: verificationCmd list form prevents shell injection ───

    def test_verification_cmd_list_form_prevents_injection(self):
        """A list-form verificationCmd runs without a shell → injection impossible."""
        task = {
            "id": "t1",
            "title": "T",
            "verificationCmd": [sys.executable, "-c", "pass"],  # list form
            "repoPath": str(Path.home()),
        }
        pstate = jp.init_pipeline_record(task)
        pstate["stages"]["coder"]["commitSha"] = "abc"

        fake_quality = json.dumps({"result": {"finalAssistantVisibleText": "### Verdict — APPROVED"}})
        real_run = subprocess.run

        def selective_run(cmd, *a, **kw):
            if isinstance(cmd, list) and len(cmd) > 0 and cmd[0] == "openclaw":
                class FP: stdout = fake_quality; stderr = ""; returncode = 0
                return FP()
            return real_run(cmd, *a, **kw)

        with tempfile.TemporaryDirectory() as d:
            with mock.patch.multiple(
                jp,
                OUTPUTS_DIR=Path(d),
                OPENCLAW_WORKSPACE=Path(d),
                PIPELINE_STATE_PATH=Path(d) / "pipeline-state.json",
                load_librarian_memory=mock.Mock(return_value=""),
            ):
                with mock.patch("jarvis_pipeline.subprocess.run", side_effect=selective_run):
                    jp.stage_quality(task, pstate)

        self.assertEqual(pstate["stages"]["quality"]["status"], "completed")
        self.assertEqual(pstate["stages"]["quality"]["shellMode"], "argv")

    def test_verification_cmd_string_form_still_works_and_marks_shell_mode(self):
        """String form still supported for backwards-compat but marked as shell-string."""
        task = {
            "id": "t1", "title": "T",
            "verificationCmd": "exit 0",  # shell string form
            "repoPath": str(Path.home()),
        }
        pstate = jp.init_pipeline_record(task)
        pstate["stages"]["coder"]["commitSha"] = "abc"

        fake_quality = json.dumps({"result": {"finalAssistantVisibleText": "### Verdict — APPROVED"}})
        real_run = subprocess.run

        def selective_run(cmd, *a, **kw):
            if isinstance(cmd, list) and len(cmd) > 0 and cmd[0] == "openclaw":
                class FP: stdout = fake_quality; stderr = ""; returncode = 0
                return FP()
            return real_run(cmd, *a, **kw)

        with tempfile.TemporaryDirectory() as d:
            with mock.patch.multiple(
                jp,
                OUTPUTS_DIR=Path(d),
                OPENCLAW_WORKSPACE=Path(d),
                PIPELINE_STATE_PATH=Path(d) / "pipeline-state.json",
                load_librarian_memory=mock.Mock(return_value=""),
            ):
                with mock.patch("jarvis_pipeline.subprocess.run", side_effect=selective_run):
                    jp.stage_quality(task, pstate)

        self.assertEqual(pstate["stages"]["quality"]["shellMode"], "shell-string")

    def test_verification_cmd_empty_rejects_loudly(self):
        """Empty verificationCmd must halt with QualityGateFailed, not silently pass."""
        task = {"id": "t1", "title": "T", "verificationCmd": "", "repoPath": str(Path.home())}
        pstate = jp.init_pipeline_record(task)
        with tempfile.TemporaryDirectory() as d:
            with mock.patch.multiple(
                jp, OUTPUTS_DIR=Path(d), OPENCLAW_WORKSPACE=Path(d),
                PIPELINE_STATE_PATH=Path(d) / "pipeline-state.json",
            ):
                with self.assertRaises(jp.QualityGateFailed):
                    jp.stage_quality(task, pstate)

    # ─── M4: StateLock TOCTOU protection ───

    def test_state_lock_refuses_symlink(self):
        """StateLock must refuse to open a symlinked lock file (O_NOFOLLOW)."""
        with tempfile.TemporaryDirectory() as d:
            real_target = Path(d) / "sensitive_file"
            real_target.write_text("secret")
            lock_path = Path(d) / "pipeline.lock"
            os.symlink(str(real_target), str(lock_path))
            with self.assertRaises(jp.PipelineError):
                with jp.StateLock(lock_path):
                    pass
            # Sensitive file must be untouched
            self.assertEqual(real_target.read_text(), "secret")

    def test_state_lock_creates_fresh_file_with_600(self):
        """Lock file is created mode 0600."""
        with tempfile.TemporaryDirectory() as d:
            lock_path = Path(d) / "pipeline.lock"
            with jp.StateLock(lock_path):
                mode = lock_path.stat().st_mode & 0o777
                self.assertEqual(mode, 0o600)

    # ─── M1: Auditor review is idempotent on re-run ───

    def test_auditor_review_replace_not_append_on_rerun(self):
        """Running stage_auditor twice replaces the review block, doesn't append."""
        with tempfile.TemporaryDirectory() as d:
            plan = Path(d) / "PLAN.md"
            plan.write_text("# PLAN.md\nsome plan content")
            # First insert
            jp._replace_or_append_auditor_review(plan, "### Gaps\nfirst review\n### Approval\nAPPROVED")
            first = plan.read_text()
            self.assertIn("first review", first)
            self.assertEqual(first.count(jp.AUDITOR_REVIEW_START), 1)
            # Second insert should REPLACE, not append
            jp._replace_or_append_auditor_review(plan, "### Gaps\nsecond review\n### Approval\nAPPROVED")
            second = plan.read_text()
            self.assertIn("second review", second)
            self.assertNotIn("first review", second)
            self.assertEqual(second.count(jp.AUDITOR_REVIEW_START), 1)

    def test_auditor_review_preserves_original_plan_content(self):
        with tempfile.TemporaryDirectory() as d:
            plan = Path(d) / "PLAN.md"
            plan.write_text("# PLAN.md\n## Task 1: do a thing\ncontent before review")
            jp._replace_or_append_auditor_review(plan, "review v1")
            jp._replace_or_append_auditor_review(plan, "review v2")
            final = plan.read_text()
            self.assertIn("# PLAN.md", final)
            self.assertIn("## Task 1: do a thing", final)
            self.assertIn("content before review", final)
            self.assertIn("review v2", final)

    # ─── M2: Librarian memory mtime cache ───

    def test_load_librarian_memory_mtime_cache_hit(self):
        """Second call with unchanged mtimes returns cached result without re-reading files."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "proj" / "memory").mkdir(parents=True)
            (root / "proj" / "memory" / "feedback.md").write_text("content v1")
            jp._invalidate_librarian_cache()

            # First call: populate cache
            out1 = jp.load_librarian_memory([root])
            self.assertIn("content v1", out1)

            # Mutate the file AT THE OS LEVEL but keep mtime the same
            # (to prove cache is used). We do this by reading and rewriting
            # with os.utime restoring mtime.
            target = root / "proj" / "memory" / "feedback.md"
            original_stat = target.stat()
            target.write_text("content v2")  # this changes mtime
            # Restore the mtime
            os.utime(target, (original_stat.st_atime, original_stat.st_mtime))

            out2 = jp.load_librarian_memory([root])
            # Cache hit — still shows v1 because mtime didn't change
            self.assertIn("content v1", out2)
            self.assertNotIn("content v2", out2)

    def test_load_librarian_memory_mtime_invalidates_cache(self):
        """When a memory file's mtime advances, the cache is invalidated."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "proj" / "memory").mkdir(parents=True)
            target = root / "proj" / "memory" / "feedback.md"
            target.write_text("content v1")
            jp._invalidate_librarian_cache()

            out1 = jp.load_librarian_memory([root])
            self.assertIn("content v1", out1)

            # Advance mtime and change content
            import time as _time
            _time.sleep(0.01)  # ensure mtime resolution advances
            target.write_text("content v2")

            out2 = jp.load_librarian_memory([root])
            self.assertIn("content v2", out2)
            self.assertNotIn("content v1", out2)

    def test_load_librarian_memory_cache_cleared_between_tests(self):
        """_invalidate_librarian_cache() actually clears the cache."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "proj" / "memory").mkdir(parents=True)
            (root / "proj" / "memory" / "feedback.md").write_text("original")
            jp._invalidate_librarian_cache()
            jp.load_librarian_memory([root])  # populate
            self.assertTrue(len(jp._LIBRARIAN_MEMORY_CACHE) > 0)
            jp._invalidate_librarian_cache()
            self.assertEqual(len(jp._LIBRARIAN_MEMORY_CACHE), 0)

    # ─── H4: Resume after Auditor REJECTED preserves state correctly ───

    def test_resume_after_auditor_reject_preserves_state(self):
        """After a revision loop fires, state contains correct rev counts + feedback."""
        # This is already covered by test_auditor_reject_triggers_revision_and_succeeds
        # but let's add an explicit resume-after-partial-revision test.
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            tasks_path = d / "tasks.json"
            tasks_path.write_text(json.dumps({
                "tasks": {"t1": {"id": "t1", "title": "T", "verificationCmd": "true", "repoPath": str(d)}}
            }))

            # Seed state with a revision already in progress: planner is pending,
            # auditor is pending, revisionFeedback["planner"] is set.
            state = {"version": 1, "pipelines": {
                "t1": {
                    **jp.init_pipeline_record({"id": "t1", "title": "T", "verificationCmd": "true"}),
                    "revisions": {"planner": 1, "coder": 0},
                    "revisionFeedback": {"planner": "prior rejection text here", "coder": None},
                }
            }}
            state["pipelines"]["t1"]["stages"]["researcher"]["status"] = "completed"
            state_path = d / "pipeline-state.json"
            state_path.write_text(json.dumps(state))

            # Capture the planner message to verify feedback is injected
            planner_messages = []

            def fake(agent_id, message, timeout_sec, log_path):
                log_path.parent.mkdir(parents=True, exist_ok=True)
                log_path.write_text(json.dumps({"result": {"finalAssistantVisibleText": "ok"}}))
                if agent_id == "planner":
                    planner_messages.append(message)
                    return jp.AgentOutput("ok", {}, 0.1, "stop", "test")
                if agent_id == "auditor":
                    return jp.AgentOutput("### Approval\nAPPROVED", {}, 0.1, "stop", "test")
                if agent_id == "quality":
                    return jp.AgentOutput("### Verdict — APPROVED", {}, 0.1, "stop", "test")
                return jp.AgentOutput("ok", {}, 0.1, "stop", "test")

            with mock.patch.multiple(
                jp,
                TASKS_OPENCLAW=tasks_path,
                PIPELINE_STATE_PATH=state_path,
                PIPELINE_LOCK_PATH=d / "pipeline-state.json.lock",
                OUTPUTS_DIR=d / "outputs",
                OPENCLAW_WORKSPACE=d,
                INCIDENTS_PATH=d / "incidents.jsonl",
                TASKS_OPENCLAW_MIRROR=d / "mirror.json",
                TASKS_MISSION_CONTROL=d / "mc.json",
                dispatch_agent=fake,
                load_librarian_memory=mock.Mock(return_value=""),
                _mc_ensure_task=mock.Mock(),
                _mc_update_stage=mock.Mock(),
                _mc_finalize=mock.Mock(),
            ):
                result = jp.run_pipeline("t1", resume=True, skip_stages=set(), max_revisions=2)

            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["revisions"]["planner"], 1)  # preserved from state
            # The replayed Planner run should have seen the prior rejection text
            self.assertTrue(any("prior rejection text here" in m for m in planner_messages))
            # After successful completion, revisionFeedback should be cleared
            self.assertIsNone(result["revisionFeedback"]["planner"])


class TestMissionControlIntegration(unittest.TestCase):
    """Unit tests for the MC REST client + stage transition hooks."""

    def _fake_urlopen_factory(self, responses: list):
        """Return a factory producing a mock urlopen that serves responses in order."""
        calls = []

        class FakeResp:
            def __init__(self, status: int, body: str):
                self.status = status
                self._body = body.encode()
            def read(self):
                return self._body
            def __enter__(self):
                return self
            def __exit__(self, *a):
                return False

        def fake_urlopen(req, timeout=None):
            calls.append({
                "method": req.get_method(),
                "url": req.full_url,
                "body": req.data.decode() if req.data else None,
            })
            if not responses:
                raise AssertionError(f"unexpected MC call: {req.get_method()} {req.full_url}")
            r = responses.pop(0)
            if isinstance(r, Exception):
                raise r
            status, body = r
            return FakeResp(status, body)

        return fake_urlopen, calls

    def test_mc_http_success(self):
        urlopen, calls = self._fake_urlopen_factory([(200, '{"ok": true}')])
        with mock.patch("urllib.request.urlopen", side_effect=urlopen):
            status, body = jp._mc_http("GET", "/tasks/t1")
            self.assertEqual(status, 200)
            self.assertEqual(body, {"ok": True})
            self.assertEqual(calls[0]["method"], "GET")
            self.assertTrue(calls[0]["url"].endswith("/tasks/t1"))

    def test_mc_http_transport_error_returns_zero(self):
        urlopen, _ = self._fake_urlopen_factory([ConnectionRefusedError("boom")])
        with mock.patch("urllib.request.urlopen", side_effect=urlopen):
            status, body = jp._mc_http("GET", "/tasks/t1")
            self.assertEqual(status, 0)
            self.assertIsNone(body)

    def test_mc_http_http_error_returns_code(self):
        err = urllib.error.HTTPError("http://x/tasks/t1", 404, "Not Found", {}, None)
        err.read = lambda: b'{"error": "Task not found"}'
        urlopen, _ = self._fake_urlopen_factory([err])
        with mock.patch("urllib.request.urlopen", side_effect=urlopen):
            status, _ = jp._mc_http("GET", "/tasks/t1")
            self.assertEqual(status, 404)

    def test_mc_ensure_task_creates_when_missing(self):
        err = urllib.error.HTTPError("http://x/tasks/t1", 404, "Not Found", {}, None)
        err.read = lambda: b""
        urlopen, calls = self._fake_urlopen_factory([
            err,  # GET returns 404
            (201, '{"id":"t1"}'),  # POST creates
        ])
        with mock.patch("urllib.request.urlopen", side_effect=urlopen):
            jp._mc_ensure_task({"id": "t1", "title": "T", "verificationCmd": "x", "summary": "hello"})
        self.assertEqual(calls[0]["method"], "GET")
        self.assertEqual(calls[1]["method"], "POST")
        posted = json.loads(calls[1]["body"])
        self.assertEqual(posted["id"], "t1")
        self.assertEqual(posted["status"], "running")
        self.assertEqual(posted["progress"], 1)
        self.assertIn("agentChain", posted)
        self.assertEqual(posted["updates"][0]["text"], "Pipeline starting via jarvis_pipeline.py")

    def test_mc_ensure_task_puts_when_exists(self):
        urlopen, calls = self._fake_urlopen_factory([
            (200, '{"id":"t1","status":"queued"}'),  # GET returns 200
            (200, '{"ok":true}'),  # PUT updates
        ])
        with mock.patch("urllib.request.urlopen", side_effect=urlopen):
            jp._mc_ensure_task({"id": "t1", "title": "T"})
        self.assertEqual(calls[0]["method"], "GET")
        self.assertEqual(calls[1]["method"], "PUT")
        put_body = json.loads(calls[1]["body"])
        self.assertEqual(put_body["status"], "running")

    def test_mc_ensure_task_tolerates_mc_down(self):
        """If MC is unreachable, ensure_task must not raise."""
        urlopen, _ = self._fake_urlopen_factory([ConnectionRefusedError("boom")])
        with mock.patch("urllib.request.urlopen", side_effect=urlopen):
            jp._mc_ensure_task({"id": "t1"})  # should not raise

    def test_mc_update_stage_progress_mapping(self):
        """Each stage sends the correct progress percentage on start vs done."""
        urlopen, calls = self._fake_urlopen_factory([(200, '{}')] * 14)
        with mock.patch("urllib.request.urlopen", side_effect=urlopen):
            for stage, (start, done) in jp.STAGE_PROGRESS.items():
                jp._mc_update_stage({"id": "t1"}, stage, "start")
                jp._mc_update_stage({"id": "t1"}, stage, "done")

        self.assertEqual(len(calls), 14)
        for i, (stage, (start, done)) in enumerate(jp.STAGE_PROGRESS.items()):
            start_call = json.loads(calls[i * 2]["body"])
            done_call = json.loads(calls[i * 2 + 1]["body"])
            self.assertEqual(start_call["progress"], start, f"{stage} start")
            self.assertEqual(done_call["progress"], done, f"{stage} done")
            self.assertIn("▶ running", start_call["update"])
            self.assertIn("✓ completed", done_call["update"])
            # Start call includes agentChain append
            self.assertIn("agent", start_call)
            self.assertEqual(start_call["agent"]["agent"], stage)

    def test_mc_update_stage_failed_phase(self):
        urlopen, calls = self._fake_urlopen_factory([(200, '{}')])
        with mock.patch("urllib.request.urlopen", side_effect=urlopen):
            jp._mc_update_stage({"id": "t1"}, "quality", "failed")
        body = json.loads(calls[0]["body"])
        self.assertIn("✗ FAILED", body["update"])
        self.assertEqual(body["progress"], 90)  # done_pct, since quality failed AFTER start

    def test_mc_finalize_success(self):
        urlopen, calls = self._fake_urlopen_factory([(200, '{}')])
        task = {"id": "t1"}
        pstate = jp.init_pipeline_record(task)
        for s in jp.STAGES:
            pstate["stages"][s]["status"] = "completed"
        pstate["stages"]["coder"]["commitSha"] = "deadbeef"
        with mock.patch("urllib.request.urlopen", side_effect=urlopen):
            jp._mc_finalize(task, pstate)
        body = json.loads(calls[0]["body"])
        self.assertEqual(body["status"], "completed")
        self.assertEqual(body["progress"], 100)
        self.assertEqual(body["completedCommit"], "deadbeef")
        self.assertIn("completedAt", body)

    def test_mc_finalize_failure(self):
        urlopen, calls = self._fake_urlopen_factory([(200, '{}')])
        task = {"id": "t1"}
        pstate = jp.init_pipeline_record(task)
        pstate["stages"]["quality"]["status"] = "failed"
        with mock.patch("urllib.request.urlopen", side_effect=urlopen):
            jp._mc_finalize(task, pstate)
        body = json.loads(calls[0]["body"])
        self.assertEqual(body["status"], "failed")
        self.assertNotIn("completedAt", body)  # only set on success


# urllib import needed for HTTPError in TestMissionControlIntegration
import urllib.error  # noqa: E402


class TestExternalContextHook(unittest.TestCase):
    """Verify the external context hook's discovery, subprocess isolation, and fail-safety.

    Post-review C1 fix: the hook is ALWAYS run in a subprocess via `python3 <hook>`.
    The hook file must have an `__main__` block that reads JSON from stdin and
    writes context to stdout.
    """

    # All hook templates include the __main__ block that the real orchestrator expects.
    _RUNNER_BLOCK = '''
if __name__ == "__main__":
    import json, sys
    try:
        p = json.load(sys.stdin)
        r = fetch_context(p.get("task") or {}, p.get("stage") or "")
        sys.stdout.write(str(r or ""))
        sys.exit(0)
    except Exception as e:
        sys.stderr.write(f"hook error: {e!r}\\n")
        sys.exit(1)
'''

    HOOK_TEMPLATE_MODULE = '''
def fetch_context(task, stage):
    return f"HOOK_SENTINEL_{stage}_{task['id']}"
''' + _RUNNER_BLOCK

    HOOK_RAISES = '''
def fetch_context(task, stage):
    raise RuntimeError("boom")
''' + _RUNNER_BLOCK

    HOOK_NO_FUNC = '''
# intentionally missing fetch_context
import sys
sys.exit(1)
'''

    def _install_hook(self, d: Path, source: str) -> Path:
        hook = d / "external_context_hook.py"
        hook.write_text(source)
        return hook

    def test_no_hook_returns_empty(self):
        with tempfile.TemporaryDirectory() as d:
            with mock.patch.object(jp, "EXTERNAL_CONTEXT_HOOK_PATH", Path(d) / "external_context_hook.py"):
                with mock.patch.dict(os.environ, {}, clear=False):
                    os.environ.pop("JARVIS_EXTERNAL_CONTEXT_CMD", None)
                    self.assertEqual(jp.load_external_context({"id": "t1"}, "researcher"), "")

    def test_python_hook_returns_content(self):
        """The subprocess-isolated hook can still return content to the parent."""
        with tempfile.TemporaryDirectory() as d:
            hook = self._install_hook(Path(d), self.HOOK_TEMPLATE_MODULE)
            with mock.patch.object(jp, "EXTERNAL_CONTEXT_HOOK_PATH", hook):
                out = jp.load_external_context({"id": "t1"}, "planner")
                self.assertEqual(out, "HOOK_SENTINEL_planner_t1")

    def test_hook_subprocess_isolation(self):
        """A hook that mutates a global variable does NOT affect the parent process."""
        hook_src = '''
import sys
# This would mutate the parent if we were using exec_module.
# In subprocess isolation, it only affects this process.
_poisoned = True

def fetch_context(task, stage):
    return "clean"
''' + self._RUNNER_BLOCK
        with tempfile.TemporaryDirectory() as d:
            hook = self._install_hook(Path(d), hook_src)
            with mock.patch.object(jp, "EXTERNAL_CONTEXT_HOOK_PATH", hook):
                out = jp.load_external_context({"id": "t1"}, "researcher")
                self.assertEqual(out, "clean")
            # Verify no module named _jarvis_external_context_hook polluted sys.modules
            import sys as _sys
            self.assertNotIn("_jarvis_external_context_hook", _sys.modules)
            # Verify _poisoned is not in any orchestrator module namespace
            self.assertFalse(hasattr(jp, "_poisoned"))

    def test_python_hook_exception_returns_empty(self):
        with tempfile.TemporaryDirectory() as d:
            hook = self._install_hook(Path(d), self.HOOK_RAISES)
            with mock.patch.object(jp, "EXTERNAL_CONTEXT_HOOK_PATH", hook):
                self.assertEqual(jp.load_external_context({"id": "t1"}, "researcher"), "")

    def test_python_hook_missing_function_returns_empty(self):
        with tempfile.TemporaryDirectory() as d:
            hook = self._install_hook(Path(d), self.HOOK_NO_FUNC)
            with mock.patch.object(jp, "EXTERNAL_CONTEXT_HOOK_PATH", hook):
                self.assertEqual(jp.load_external_context({"id": "t1"}, "researcher"), "")

    def test_task_opt_out_skips_hook(self):
        with tempfile.TemporaryDirectory() as d:
            hook = self._install_hook(Path(d), self.HOOK_TEMPLATE_MODULE)
            with mock.patch.object(jp, "EXTERNAL_CONTEXT_HOOK_PATH", hook):
                task = {"id": "t1", "externalContext": {"enabled": False}}
                self.assertEqual(jp.load_external_context(task, "researcher"), "")

    def test_truncation(self):
        big_hook = 'def fetch_context(task, stage):\n    return "x" * 1_000_000\n' + self._RUNNER_BLOCK
        with tempfile.TemporaryDirectory() as d:
            hook = self._install_hook(Path(d), big_hook)
            with mock.patch.object(jp, "EXTERNAL_CONTEXT_HOOK_PATH", hook):
                out = jp.load_external_context({"id": "t1"}, "researcher")
                self.assertTrue(len(out) <= jp.EXTERNAL_CONTEXT_MAX_BYTES + 200)  # + truncation notice
                self.assertIn("truncated", out)

    def test_shell_command_hook(self):
        with tempfile.TemporaryDirectory() as d:
            with mock.patch.object(jp, "EXTERNAL_CONTEXT_HOOK_PATH", Path(d) / "nope.py"):
                with mock.patch.dict(os.environ, {"JARVIS_EXTERNAL_CONTEXT_CMD": "cat; echo SHELL_HOOK_OK"}):
                    out = jp.load_external_context({"id": "t1"}, "researcher")
                    self.assertIn("SHELL_HOOK_OK", out)
                    # The stdin payload was piped through `cat` so it appears too
                    self.assertIn("researcher", out)

    def test_shell_command_failure_returns_empty(self):
        with tempfile.TemporaryDirectory() as d:
            with mock.patch.object(jp, "EXTERNAL_CONTEXT_HOOK_PATH", Path(d) / "nope.py"):
                with mock.patch.dict(os.environ, {"JARVIS_EXTERNAL_CONTEXT_CMD": "false"}):
                    self.assertEqual(jp.load_external_context({"id": "t1"}, "researcher"), "")

    def test_researcher_stage_injects_external_context(self):
        """End-to-end: stage_researcher pulls from the hook and prepends to the agent prompt.

        Note: this uses a REAL hook subprocess, so the hook file must be a valid
        standalone Python script (with the __main__ block).
        """
        captured = {}

        def fake_dispatch(agent_id, message, timeout_sec, log_path):
            captured["message"] = message
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_path.write_text(json.dumps({"result": {"finalAssistantVisibleText": "ok"}}))
            return jp.AgentOutput("ok", {}, 0.1, "stop", "test")

        with tempfile.TemporaryDirectory() as d:
            dp = Path(d)
            hook = self._install_hook(dp, self.HOOK_TEMPLATE_MODULE)
            with mock.patch.multiple(
                jp,
                OUTPUTS_DIR=dp,
                OPENCLAW_WORKSPACE=dp,
                PIPELINE_STATE_PATH=dp / "pipeline-state.json",
                EXTERNAL_CONTEXT_HOOK_PATH=hook,
                dispatch_agent=fake_dispatch,
            ):
                task = {"id": "t1", "title": "Test", "verificationCmd": "true", "objective": "x"}
                pstate = jp.init_pipeline_record(task)
                jp.stage_researcher(task, pstate)

        self.assertIn("EXISTING KNOWLEDGE", captured["message"])
        self.assertIn("HOOK_SENTINEL_researcher_t1", captured["message"])
        self.assertGreater(pstate["stages"]["researcher"]["externalContextBytes"], 0)

    def test_planner_stage_injects_external_context(self):
        """End-to-end: stage_planner pulls from the hook and prepends to the agent prompt."""
        captured = {}

        def fake_dispatch(agent_id, message, timeout_sec, log_path):
            captured["message"] = message
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_path.write_text(json.dumps({"result": {"finalAssistantVisibleText": "ok"}}))
            return jp.AgentOutput("ok", {}, 0.1, "stop", "test")

        with tempfile.TemporaryDirectory() as d:
            dp = Path(d)
            hook = self._install_hook(dp, self.HOOK_TEMPLATE_MODULE)
            with mock.patch.multiple(
                jp,
                OUTPUTS_DIR=dp,
                OPENCLAW_WORKSPACE=dp,
                PIPELINE_STATE_PATH=dp / "pipeline-state.json",
                EXTERNAL_CONTEXT_HOOK_PATH=hook,
                dispatch_agent=fake_dispatch,
                load_librarian_memory=mock.Mock(return_value="mem"),
            ):
                task = {"id": "t1", "title": "Test", "verificationCmd": "true",
                        "objective": "x", "repoPath": str(dp)}
                pstate = jp.init_pipeline_record(task)
                jp.stage_planner(task, pstate)

        self.assertIn("EXTERNAL KNOWLEDGE BASE", captured["message"])
        self.assertIn("HOOK_SENTINEL_planner_t1", captured["message"])
        # Must appear BEFORE Librarian memory in the final prompt
        ext_idx = captured["message"].index("EXTERNAL KNOWLEDGE BASE")
        lib_idx = captured["message"].index("LIBRARIAN MEMORY")
        self.assertLess(ext_idx, lib_idx)


# os import needed for TestExternalContextHook env manipulation
import os  # noqa: E402


class TestRevisionLoop(unittest.TestCase):
    """run_pipeline auto-revision: Auditor REJECTED → Planner revise, Quality REJECTED → Coder revise.

    All tests patch `time.sleep` to skip the exponential backoff delay.
    """

    def setUp(self):
        self._sleep_patch = mock.patch("time.sleep", return_value=None)
        self._sleep_patch.start()

    def tearDown(self):
        self._sleep_patch.stop()

    def _seed_env(self, d: Path, verificationCmd: str = "true"):
        """Set up a temp environment with task + mocked openclaw paths."""
        (d / "pipeline-outputs").mkdir()
        tasks_path = d / "tasks.json"
        tasks_path.write_text(json.dumps({
            "tasks": {
                "t1": {
                    "id": "t1",
                    "title": "Test",
                    "verificationCmd": verificationCmd,
                    "repoPath": str(d),
                    "objective": "test objective",
                }
            }
        }))
        return {
            "TASKS_OPENCLAW": tasks_path,
            "TASKS_OPENCLAW_MIRROR": d / "mirror.json",
            "TASKS_MISSION_CONTROL": d / "mc.json",
            "PIPELINE_STATE_PATH": d / "pipeline-state.json",
            "PIPELINE_LOCK_PATH": d / "pipeline-state.json.lock",
            "OUTPUTS_DIR": d / "pipeline-outputs",
            "OPENCLAW_WORKSPACE": d,
            "INCIDENTS_PATH": d / "incidents.jsonl",
        }

    def _make_dispatch(self, responses: dict):
        """Return a fake dispatch_agent that produces canned AgentOutput per agent.

        `responses` maps agent_id → list of text responses (consumed per-call).
        If exhausted, raises.
        """
        call_counts = {k: 0 for k in responses}

        def fake(agent_id, message, timeout_sec, log_path):
            if agent_id not in responses:
                return jp.AgentOutput("", {}, 0.1, "stop", "test")
            i = call_counts[agent_id]
            if i >= len(responses[agent_id]):
                raise AssertionError(f"dispatch_agent called too many times for {agent_id}")
            text = responses[agent_id][i]
            call_counts[agent_id] += 1
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_path.write_text(json.dumps({"result": {"finalAssistantVisibleText": text}}))
            return jp.AgentOutput(text, {}, 0.1, "stop", "fake-model")

        return fake, call_counts

    def test_auditor_reject_triggers_revision_and_succeeds(self):
        """Auditor REJECTs first, APPROVEs second → pipeline completes with planner revision=1."""
        responses = {
            "researcher": ["brief"],
            "planner": ["# PLAN.md\nfirst draft", "# PLAN.md\nrevised draft"],
            "auditor": [
                "### Gaps\n1. missing edge case\n### Approval\nREJECTED — needs revision",
                "### Gaps\n(none)\n### Approval\nAPPROVED",
            ],
            "coder": ["commit"],
            "quality": ["### Verdict — APPROVED"],
        }
        fake_dispatch, counts = self._make_dispatch(responses)

        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            env = self._seed_env(d)
            with mock.patch("time.sleep", return_value=None), mock.patch.multiple(
                jp, dispatch_agent=fake_dispatch,
                load_librarian_memory=mock.Mock(return_value="mem"),
                **env,
            ):
                result = jp.run_pipeline("t1", resume=False, skip_stages=set(), max_revisions=2)

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["revisions"]["planner"], 1)
        self.assertEqual(result["revisions"]["coder"], 0)
        self.assertEqual(counts["planner"], 2)  # drafted twice
        self.assertEqual(counts["auditor"], 2)  # reviewed twice
        self.assertEqual(counts["coder"], 1)    # coded once (after 2nd approval)
        # Post-review H4: revisionFeedback should be cleared after successful consumption
        self.assertIsNone(result["revisionFeedback"].get("planner"))

    def test_auditor_reject_exhausts_revisions(self):
        """Auditor keeps rejecting → pipeline fails with revisions at max."""
        responses = {
            "researcher": ["brief"],
            "planner": ["v0", "v1", "v2"],  # 1 original + 2 revisions
            "auditor": ["REJECTED 1", "REJECTED 2", "REJECTED 3"],
            "coder": [],
            "quality": [],
        }
        fake_dispatch, counts = self._make_dispatch(responses)

        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            env = self._seed_env(d)
            with mock.patch("time.sleep", return_value=None), mock.patch.multiple(
                jp, dispatch_agent=fake_dispatch,
                load_librarian_memory=mock.Mock(return_value="mem"),
                **env,
            ):
                result = jp.run_pipeline("t1", resume=False, skip_stages=set(), max_revisions=2)

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["revisions"]["planner"], 2)  # capped
        self.assertEqual(counts["planner"], 3)  # original + 2 revisions
        self.assertEqual(counts["auditor"], 3)
        self.assertEqual(counts["coder"], 0)  # never got here
        # Monitor should have logged the incident
        self.assertTrue(any("auditor" in e["stage"] for e in result["errors"]))

    def test_quality_llm_reject_triggers_coder_revision(self):
        """Quality cmd passes but LLM REJECTs → Coder re-runs with feedback, then passes."""
        responses = {
            "researcher": ["brief"],
            "planner": ["plan"],
            "auditor": ["APPROVED"],
            "coder": ["commit v1", "commit v2"],
            "quality": [
                "### Verdict — REJECTED\nmissing --version flag",
                "### Verdict — APPROVED",
            ],
        }
        fake_dispatch, counts = self._make_dispatch(responses)

        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            env = self._seed_env(d, verificationCmd="true")
            with mock.patch.multiple(jp, dispatch_agent=fake_dispatch,
                                     load_librarian_memory=mock.Mock(return_value="mem"),
                                     **env):
                result = jp.run_pipeline("t1", resume=False, skip_stages=set(), max_revisions=2)

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["revisions"]["coder"], 1)
        self.assertEqual(counts["coder"], 2)
        self.assertEqual(counts["quality"], 2)

    def test_quality_cmd_failure_does_not_retry(self):
        """verificationCmd exit 1 → halt immediately, NO Coder revision."""
        responses = {
            "researcher": ["brief"],
            "planner": ["plan"],
            "auditor": ["APPROVED"],
            "coder": ["commit"],
            "quality": [],  # LLM should NEVER be called when cmd fails
        }
        fake_dispatch, counts = self._make_dispatch(responses)

        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            env = self._seed_env(d, verificationCmd="false")
            with mock.patch.multiple(jp, dispatch_agent=fake_dispatch,
                                     load_librarian_memory=mock.Mock(return_value="mem"),
                                     **env):
                result = jp.run_pipeline("t1", resume=False, skip_stages=set(), max_revisions=2)

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["revisions"]["coder"], 0)  # no retry
        self.assertEqual(counts["coder"], 1)  # only initial run
        self.assertEqual(counts["quality"], 0)  # LLM never dispatched — gate failed first

    def test_revision_feedback_injected_into_next_planner_prompt(self):
        """The rejection text from Auditor must appear in the next Planner dispatch."""
        planner_messages = []
        auditor_responses = iter([
            "### Gaps\n1. atomic-write missing\n### Approval\nREJECTED — needs revision",
            "### Gaps\n(none)\n### Approval\nAPPROVED",
        ])

        def fake(agent_id, message, timeout_sec, log_path):
            log_path.parent.mkdir(parents=True, exist_ok=True)
            if agent_id == "planner":
                planner_messages.append(message)
                log_path.write_text(json.dumps({"result": {"finalAssistantVisibleText": "plan"}}))
                return jp.AgentOutput("plan", {}, 0.1, "stop", "test")
            if agent_id == "auditor":
                text = next(auditor_responses)
                log_path.write_text(json.dumps({"result": {"finalAssistantVisibleText": text}}))
                return jp.AgentOutput(text, {}, 0.1, "stop", "test")
            log_path.write_text(json.dumps({"result": {"finalAssistantVisibleText": "ok"}}))
            return jp.AgentOutput("ok" if agent_id != "quality" else "### Verdict — APPROVED",
                                  {}, 0.1, "stop", "test")

        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            env = self._seed_env(d)
            with mock.patch.multiple(jp, dispatch_agent=fake,
                                     load_librarian_memory=mock.Mock(return_value="mem"),
                                     **env):
                result = jp.run_pipeline("t1", resume=False, skip_stages=set(), max_revisions=2)

        self.assertEqual(result["status"], "completed")
        self.assertEqual(len(planner_messages), 2)
        # First planner call: no revision block
        self.assertNotIn("REVISION ATTEMPT", planner_messages[0])
        # Second planner call: revision block WITH the auditor's feedback
        self.assertIn("REVISION ATTEMPT 1/2", planner_messages[1])
        self.assertIn("atomic-write missing", planner_messages[1])


class TestPowerSpecDispatch(unittest.TestCase):
    """Tests for Option C — coder dispatch to PowerSpec node via openclaw exec."""

    def setUp(self):
        self._sleep_patch = mock.patch("time.sleep", return_value=None)
        self._sleep_patch.start()

    def tearDown(self):
        self._sleep_patch.stop()

    def _make_task(self, coderHost="powerspec", **overrides):
        task = {
            "id": "ps-test",
            "title": "Test",
            "verificationCmd": "true",
            "repoPath": "/tmp/repo",
            "objective": "test",
            "execution": {"coderHost": coderHost},
        }
        task.update(overrides)
        return task

    def test_coder_host_default_is_local(self):
        """Tasks without execution.coderHost field default to local."""
        task = {"id": "t1", "verificationCmd": "true"}
        self.assertEqual(jp._coder_host(task), "local")

    def test_coder_host_explicit_local(self):
        task = self._make_task(coderHost="local")
        self.assertEqual(jp._coder_host(task), "local")

    def test_coder_host_powerspec(self):
        task = self._make_task(coderHost="powerspec")
        self.assertEqual(jp._coder_host(task), "powerspec")

    def test_coder_host_invalid_raises(self):
        task = self._make_task(coderHost="elsewhere")
        with self.assertRaises(jp.PipelineError):
            jp._coder_host(task)

    def test_stage_coder_routes_to_powerspec_dispatcher(self):
        """When coderHost=powerspec, stage_coder calls _dispatch_coder_powerspec."""
        task = self._make_task(coderHost="powerspec")
        pstate = jp.init_pipeline_record(task)
        pstate["stages"]["auditor"]["outputPath"] = "02-plan.md"

        with mock.patch.object(jp, "_dispatch_coder_powerspec") as remote_mock, \
             mock.patch.object(jp, "_dispatch_coder_local") as local_mock:
            jp.stage_coder(task, pstate)
            remote_mock.assert_called_once_with(task, pstate)
            local_mock.assert_not_called()

    def test_stage_coder_routes_to_local_dispatcher(self):
        """When coderHost=local (default), stage_coder calls _dispatch_coder_local."""
        task = {"id": "t1", "verificationCmd": "true", "repoPath": "/tmp"}
        pstate = jp.init_pipeline_record(task)

        with mock.patch.object(jp, "_dispatch_coder_powerspec") as remote_mock, \
             mock.patch.object(jp, "_dispatch_coder_local") as local_mock:
            jp.stage_coder(task, pstate)
            local_mock.assert_called_once_with(task, pstate)
            remote_mock.assert_not_called()

    def test_powerspec_remote_work_dir_default(self):
        task = self._make_task()
        work_dir = jp._powerspec_remote_work_dir(task)
        self.assertEqual(work_dir, r"C:\Users\Eric Brown\repos\ps-test")

    def test_powerspec_remote_work_dir_explicit(self):
        task = self._make_task(execution={"coderHost": "powerspec", "remoteWorkDir": r"D:\custom\path"})
        self.assertEqual(jp._powerspec_remote_work_dir(task), r"D:\custom\path")

    def test_mc_update_stage_records_powerspec_host_for_coder(self):
        """When task.execution.coderHost=powerspec, MC agentChain entry has host=powerspec."""
        captured = {}

        class FakeResp:
            status = 200
            def read(self): return b'{}'
            def __enter__(self): return self
            def __exit__(self, *a): return False

        def fake_urlopen(req, timeout=None):
            captured["method"] = req.get_method()
            captured["url"] = req.full_url
            captured["body"] = req.data.decode() if req.data else None
            return FakeResp()

        task = self._make_task(coderHost="powerspec")
        with mock.patch("urllib.request.urlopen", side_effect=fake_urlopen):
            jp._mc_update_stage(task, "coder", "start")

        body = json.loads(captured["body"])
        self.assertIn("agent", body)
        self.assertEqual(body["agent"]["host"], "powerspec")
        self.assertIn("on powerspec", body["update"])

    def test_mc_update_stage_records_local_host_for_non_coder(self):
        """Stages other than Coder always report host=local."""
        captured = {}
        class FakeResp:
            status = 200
            def read(self): return b'{}'
            def __enter__(self): return self
            def __exit__(self, *a): return False
        def fake_urlopen(req, timeout=None):
            captured["body"] = req.data.decode() if req.data else None
            return FakeResp()

        task = self._make_task(coderHost="powerspec")
        with mock.patch("urllib.request.urlopen", side_effect=fake_urlopen):
            jp._mc_update_stage(task, "planner", "start")

        body = json.loads(captured["body"])
        self.assertEqual(body["agent"]["host"], "local")
        self.assertIn("on local", body["update"])

    def test_dispatch_coder_powerspec_captures_commit_sha(self):
        """_dispatch_coder_powerspec runs: SSH plumbing + main agent exec + SSH sha capture.

        Mocks the _powerspec_ssh helper for the plumbing steps and dispatch_agent
        for the workload step.
        """
        task = self._make_task()
        pstate = jp.init_pipeline_record(task)
        pstate["stages"]["auditor"]["outputPath"] = "02-plan.md"

        fake_sha = "deadbeefcafef00dfeed1234567890abcdef1234"
        dispatch_calls = []

        def fake_dispatch(agent_id, message, timeout_sec, log_path):
            dispatch_calls.append({"agent": agent_id, "message": message})
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_path.write_text(json.dumps({"result": {"finalAssistantVisibleText": "CODER_RUN_COMPLETE"}}))
            return jp.AgentOutput("CODER_RUN_COMPLETE", {}, 0.1, "stop", "test")

        ssh_calls = []
        def fake_ssh(remote_cmd, timeout=60):
            ssh_calls.append(remote_cmd)
            class Proc:
                returncode = 0
                stderr = ""
                stdout = ""
            p = Proc()
            # Return fake sha when asked for git log
            if "git log" in remote_cmd:
                p.stdout = fake_sha + "\n"
            elif "_output.txt" in remote_cmd:
                p.stdout = "Coder summary: wrote foo.py, committed\n"
            return p

        fake_scp = mock.Mock(return_value=mock.Mock(returncode=0, stderr="", stdout=""))

        with tempfile.TemporaryDirectory() as d:
            plan_path = Path(d) / "02-plan.md"
            plan_path.write_text("# PLAN\ntrivial")
            with mock.patch.multiple(
                jp,
                OPENCLAW_WORKSPACE=Path(d),
                OUTPUTS_DIR=Path(d) / "outputs",
                PIPELINE_STATE_PATH=Path(d) / "pipeline-state.json",
                dispatch_agent=fake_dispatch,
                load_librarian_memory=mock.Mock(return_value=""),
                _powerspec_ssh=fake_ssh,
            ):
                with mock.patch("jarvis_pipeline.subprocess.run", side_effect=lambda *a, **k: mock.Mock(returncode=0, stderr="", stdout="")):
                    jp._dispatch_coder_powerspec(task, pstate)

        # Exactly 1 dispatch: the workload call
        self.assertEqual(len(dispatch_calls), 1)
        # SSH should have been called: ensure_work_dir, read_output, capture_sha (at least)
        self.assertGreaterEqual(len(ssh_calls), 3)
        self.assertEqual(pstate["stages"]["coder"]["commitSha"], fake_sha)
        self.assertEqual(pstate["stages"]["coder"]["host"], "powerspec")
        self.assertEqual(pstate["stages"]["coder"]["status"], "completed")


class TestKnownFailuresPrevention(unittest.TestCase):
    """Regression tests for the 6 KNOWN_FAILURES entries from Option C rollout.

    (a) Planner scope violation → fixed in openclaw.json (write removed from allow)
    (b) Node idle disconnect → _powerspec_ensure_node_alive() added (tested separately)
    (c) PS path quoting → all PS commands must use single quotes for paths
    (d) Exec pipe hang → optimistic-timeout recovery pattern added (tested separately)
    (e) stage_quality cwd → for remote host, uses Path.home() not Windows path
    (f) claude.cmd argv → stdin pipe pattern, not positional arg
    """

    def test_c_powerspec_ps_helpers_use_single_quotes_for_paths(self):
        """All PowerShell command builders must use single quotes around paths
        containing spaces (e.g., 'C:\\Users\\Eric Brown\\repos'). Double quotes
        inside a bash-SSH-PS nesting get split on spaces."""
        import inspect
        source = inspect.getsource(jp)
        # Find all _powerspec_* function bodies and assert single-quote usage
        for fn_name in ("_powerspec_ensure_work_dir", "_powerspec_read_output",
                        "_powerspec_capture_commit_sha"):
            fn = getattr(jp, fn_name)
            fn_src = inspect.getsource(fn)
            # Check for paths with POWERSPEC_REMOTE_BASE_DIR or Eric Brown
            if "POWERSPEC_REMOTE_BASE_DIR" in fn_src or "work_dir" in fn_src:
                # Should NOT have f'"{ ... }"' (double-quoted path interpolation)
                # inside PowerShell command strings
                self.assertNotIn("Set-Location \"{", fn_src,
                    f"{fn_name} uses double-quoted path in PowerShell — use single quotes")
                self.assertNotIn("Test-Path \"{", fn_src,
                    f"{fn_name} uses double-quoted Test-Path — use single quotes")
                self.assertNotIn('-Path "{', fn_src,
                    f"{fn_name} uses double-quoted -Path — use single quotes")

    def test_e_stage_quality_uses_local_cwd_for_powerspec_tasks(self):
        """stage_quality must NOT use the Windows repoPath as cwd for Mac subprocess."""
        import inspect
        src = inspect.getsource(jp.stage_quality)
        # The fix: checks coderHost == "powerspec" and uses Path.home()
        self.assertIn("coderHost", src, "stage_quality must check coderHost")
        self.assertIn("Path.home()", src, "stage_quality must fall back to Path.home() for remote tasks")

    def test_f_powerspec_dispatch_uses_stdin_pipe_not_positional_prompt(self):
        """The dispatch message must use the `echo|claude.cmd --print` pattern,
        not positional prompt argv (which claude.cmd drops on Windows)."""
        import inspect
        src = inspect.getsource(jp._build_powerspec_dispatch_message)
        # Must contain the pipe pattern
        self.assertIn("type _prompt.txt", src,
            "_build_powerspec_dispatch_message must pipe _prompt.txt to claude.cmd")
        self.assertIn("--print", src)
        # Must NOT put the prompt as a trailing positional argv element
        self.assertNotIn("'--print', prompt", src,
            "must NOT use positional prompt — use stdin pipe")


class TestLoadLibrarianMemory(unittest.TestCase):
    def _seed(self, root: Path, files: dict[str, str]) -> None:
        """Seed `root/<project>/memory/<file>` from {project/file: content}."""
        for path, content in files.items():
            project, name = path.split("/", 1)
            d = root / project / "memory"
            d.mkdir(parents=True, exist_ok=True)
            (d / name).write_text(content)

    def test_empty_when_no_roots(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(jp.load_librarian_memory([Path(d)]), "")

    def test_reads_files_across_multiple_projects(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._seed(root, {
                "proj-a/feedback_rule.md": "---\ntype: feedback\n---\nnever mock DB",
                "proj-b/project_deploy.md": "---\ntype: project\n---\nrailway deploys via git push",
                "proj-a/MEMORY.md": "INDEX — should be skipped",
                "proj-b/reference_api.md": "---\ntype: reference\n---\nAPI pattern X",
            })
            out = jp.load_librarian_memory([root])
            self.assertIn("never mock DB", out)
            self.assertIn("railway deploys via git push", out)
            self.assertIn("API pattern X", out)
            self.assertNotIn("INDEX — should be skipped", out)  # MEMORY.md excluded
            self.assertIn("proj-a/feedback_rule.md", out)  # header present
            self.assertIn("proj-b/project_deploy.md", out)

    def test_respects_max_bytes_cap(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            big = "x" * 5000
            self._seed(root, {
                "p/feedback_a.md": big,
                "p/feedback_b.md": big,
                "p/feedback_c.md": big,
            })
            out = jp.load_librarian_memory([root], max_bytes=8000)
            self.assertIn("truncated", out)
            # Should fit 1 file (5000 + header) but not 2
            self.assertEqual(out.count("--- FILE:"), 1)

    def test_ignores_non_md_and_non_memory_dirs(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._seed(root, {"p/feedback.md": "good"})
            # Add noise: a non-md file, and a sibling dir that isn't "memory"
            (root / "p" / "memory" / "readme.txt").write_text("ignore me")
            (root / "p" / "other").mkdir()
            (root / "p" / "other" / "file.md").write_text("also ignore")
            out = jp.load_librarian_memory([root])
            self.assertIn("good", out)
            self.assertNotIn("ignore me", out)
            self.assertNotIn("also ignore", out)

    def test_missing_root_is_tolerated(self):
        self.assertEqual(jp.load_librarian_memory([Path("/nonexistent/path/xyz")]), "")

    def test_real_memory_is_readable(self):
        """Sanity: on this machine, the real memory dir should have content we can read."""
        out = jp.load_librarian_memory()
        # Don't assert specific content — just that it returns a string
        # and doesn't crash. If memory files exist they should be read.
        self.assertIsInstance(out, str)


class TestInitPipelineRecord(unittest.TestCase):
    def test_has_all_stages_pending(self):
        task = {"id": "t1", "title": "T", "verificationCmd": "x"}
        rec = jp.init_pipeline_record(task)
        self.assertEqual(rec["status"], "running")
        self.assertEqual(rec["currentStage"], "researcher")
        for s in jp.STAGES:
            self.assertIn(s, rec["stages"])
            self.assertEqual(rec["stages"][s]["status"], "pending")


if __name__ == "__main__":
    unittest.main(verbosity=2)
