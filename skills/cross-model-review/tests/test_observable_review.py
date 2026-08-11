from __future__ import annotations

import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest


SKILL_DIR = Path(__file__).resolve().parents[1]
RUNNER = SKILL_DIR / "scripts" / "run_claude_review.py"
STATUS_HELPER = SKILL_DIR / "scripts" / "review_status.py"


FAKE_CLAUDE = r'''#!/usr/bin/env python3
import json
import os
import sys
import time

capture = os.environ.get("FAKE_CLAUDE_CAPTURE")
if capture:
    with open(capture, "w", encoding="utf-8") as capture_file:
        json.dump(
            {
                "argv": sys.argv[1:],
                "anthropic_api_key": os.environ.get("ANTHROPIC_API_KEY"),
                "anthropic_auth_token": os.environ.get("ANTHROPIC_AUTH_TOKEN"),
            },
            capture_file,
        )

prompt = sys.stdin.read()
if "FAIL_LAUNCH" in prompt:
    print("simulated failure", file=sys.stderr)
    raise SystemExit(7)

events = [
    {"type": "system", "subtype": "init"},
    {
        "type": "assistant",
        "message": {
            "content": [
                {
                    "type": "tool_use",
                    "name": "Read",
                    "input": {"file_path": os.path.join(os.getcwd(), "source.txt")},
                }
            ]
        },
    },
    {"type": "system", "subtype": "thinking_tokens"},
    {
        "type": "assistant",
        "message": {"content": [{"type": "text", "text": "Review ready"}]},
    },
    {
        "type": "result",
        "subtype": "success",
        "is_error": False,
        "result": "Verdict: PASS\n\nNo findings.",
    },
]
if "ERROR_RESULT" in prompt:
    events[-1] = {
        "type": "result",
        "subtype": "error",
        "is_error": True,
        "result": "Simulated error result, not a verdict.",
    }
if "MISSING_RESULT" in prompt:
    events[-1] = {
        "type": "result",
        "subtype": "success",
        "is_error": False,
    }
if "EMPTY_RESULT" in prompt:
    events[-1]["result"] = "\n"
if "NON_SUCCESS_RESULT" in prompt:
    events[-1]["subtype"] = "partial"

delay = float(os.environ.get("FAKE_CLAUDE_DELAY", "0"))
gate = os.environ.get("FAKE_CLAUDE_GATE")
for index, event in enumerate(events):
    print(json.dumps(event), flush=True)
    if gate and index == 2:
        open(gate + ".ready", "w", encoding="utf-8").close()
        while not os.path.exists(gate + ".release"):
            time.sleep(0.01)
    time.sleep(delay)
if "FAIL_AFTER_STREAM" in prompt:
    raise SystemExit(7)
'''


class ObservableReviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.source = self.repo / "source.txt"
        self.source.write_text("before\n", encoding="utf-8")
        self._git("init")
        self._git("config", "user.name", "Observable Review Test")
        self._git("config", "user.email", "test@example.invalid")
        self._git("config", "commit.gpgsign", "false")
        self._git("add", "source.txt")
        self._git("commit", "-m", "test: initialize fixture")

        self.fake_claude = self.root / "fake_claude.py"
        self.fake_claude.write_text(
            textwrap.dedent(FAKE_CLAUDE), encoding="utf-8"
        )
        self.fake_claude.chmod(0o755)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _git(self, *arguments: str) -> None:
        subprocess.run(
            ["git", *arguments],
            cwd=self.repo,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def _prompt(self, content: str = "Review the fixture.") -> Path:
        prompt = self.root / f"prompt-{time.monotonic_ns()}.md"
        prompt.write_text(content, encoding="utf-8")
        return prompt

    def _command(
        self,
        prompt: Path,
        review_dir: Path,
        claude_bin: Path | str | None = None,
        cwd: Path | None = None,
    ) -> list[str]:
        return [
            sys.executable,
            str(RUNNER),
            "--prompt-file",
            str(prompt),
            "--cwd",
            str(cwd or self.repo),
            "--label",
            "fixture/test",
            "--review-dir",
            str(review_dir),
            "--claude-bin",
            str(claude_bin or self.fake_claude),
        ]

    def _run(
        self,
        content: str = "Review the fixture.",
        environment: dict[str, str] | None = None,
        claude_bin: Path | str | None = None,
    ) -> tuple[subprocess.CompletedProcess[str], Path]:
        review_dir = self.root / f"review-{time.monotonic_ns()}"
        completed = subprocess.run(
            self._command(self._prompt(content), review_dir, claude_bin),
            check=False,
            text=True,
            capture_output=True,
            env=environment,
        )
        return completed, review_dir

    def _wait_for_file(self, path: Path, timeout: float = 5) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if path.exists():
                return
            time.sleep(0.02)
        self.fail(f"file did not appear: {path}")

    def _wait_for_status(
        self, review_dir: Path, predicate, timeout: float = 5
    ) -> dict[str, object]:
        status_path = review_dir / "status.json"
        deadline = time.monotonic() + timeout
        status: dict[str, object] = {}
        while time.monotonic() < deadline:
            try:
                status = json.loads(status_path.read_text(encoding="utf-8"))
            except (FileNotFoundError, json.JSONDecodeError):
                time.sleep(0.02)
                continue
            if predicate(status):
                return status
            time.sleep(0.02)
        self.fail(f"status predicate was not met: {status_path}; last={status}")

    def test_success_writes_final_result(self) -> None:
        completed, review_dir = self._run()

        self.assertEqual(completed.returncode, 0, completed.stderr)
        status = json.loads((review_dir / "status.json").read_text())
        self.assertEqual(status["state"], "complete")
        self.assertFalse(status["target_stale"])
        self.assertEqual(status["wrapper_exit_code"], 0)
        self.assertEqual(
            (review_dir / "final.md").read_text(),
            "Verdict: PASS\n\nNo findings.\n",
        )

    def test_unusable_result_fails_closed(self) -> None:
        for content in (
            "ERROR_RESULT",
            "MISSING_RESULT",
            "EMPTY_RESULT",
            "NON_SUCCESS_RESULT",
        ):
            with self.subTest(content=content):
                completed, review_dir = self._run(content)
                status = json.loads((review_dir / "status.json").read_text())

                self.assertEqual(completed.returncode, 91)
                self.assertEqual(status["state"], "failed")
                self.assertEqual(status["wrapper_exit_code"], 91)
                self.assertFalse((review_dir / "final.md").exists())

    def test_nonzero_child_exit_never_preserves_a_verdict(self) -> None:
        for content in ("FAIL_LAUNCH", "FAIL_AFTER_STREAM"):
            with self.subTest(content=content):
                completed, review_dir = self._run(content)
                status = json.loads((review_dir / "status.json").read_text())

                self.assertEqual(completed.returncode, 91)
                self.assertEqual(status["exit_code"], 7)
                self.assertEqual(status["state"], "failed")
                self.assertFalse((review_dir / "final.md").exists())

    def test_missing_binary_exits_127(self) -> None:
        completed, review_dir = self._run(
            claude_bin=self.root / "missing-claude"
        )
        status = json.loads((review_dir / "status.json").read_text())

        self.assertEqual(completed.returncode, 127)
        self.assertEqual(status["state"], "failed")
        self.assertEqual(status["wrapper_exit_code"], 127)

    def test_launch_contract_restricts_tools_and_strips_auth(self) -> None:
        capture = self.root / "launch.json"
        environment = os.environ.copy()
        environment.update(
            {
                "ANTHROPIC_API_KEY": "must-not-reach-child",
                "ANTHROPIC_AUTH_TOKEN": "must-not-reach-child",
                "FAKE_CLAUDE_CAPTURE": str(capture),
            }
        )
        completed, _ = self._run(environment=environment)
        launch = json.loads(capture.read_text())

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIsNone(launch["anthropic_api_key"])
        self.assertIsNone(launch["anthropic_auth_token"])
        self.assertIn("--safe-mode", launch["argv"])
        self.assertEqual(
            launch["argv"][launch["argv"].index("--tools") + 1],
            "Read,Glob,Grep",
        )
        self.assertIn(
            "Write,Edit,MultiEdit,NotebookEdit,Bash", launch["argv"]
        )

    def test_progress_phase_survives_thinking_events(self) -> None:
        review_dir = self.root / "review-progress"
        environment = os.environ.copy()
        gate = self.root / "progress-gate"
        environment["FAKE_CLAUDE_GATE"] = str(gate)
        process = subprocess.Popen(
            self._command(self._prompt(), review_dir),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=environment,
        )
        self._wait_for_file(Path(f"{gate}.ready"))
        status = self._wait_for_status(review_dir, lambda value: value.get("event_count") == 3)

        self.assertEqual(status["state"], "running")
        self.assertEqual(status["phase"], "inspecting")
        Path(f"{gate}.release").touch()
        stdout, stderr = process.communicate(timeout=5)
        self.assertEqual(process.returncode, 0, f"{stdout}\n{stderr}")

    def test_tracked_and_untracked_changes_mark_review_stale(self) -> None:
        for change_untracked in (False, True):
            with self.subTest(change_untracked=change_untracked):
                if change_untracked:
                    target = self.repo / "untracked.txt"
                    target.write_text("first\n", encoding="utf-8")
                else:
                    target = self.source

                review_dir = self.root / f"review-stale-{change_untracked}"
                environment = os.environ.copy()
                gate = self.root / f"stale-gate-{change_untracked}"
                environment["FAKE_CLAUDE_GATE"] = str(gate)
                process = subprocess.Popen(
                    self._command(self._prompt(), review_dir),
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=environment,
                )
                self._wait_for_file(Path(f"{gate}.ready"))
                target.write_text("changed\n", encoding="utf-8")
                Path(f"{gate}.release").touch()
                stdout, stderr = process.communicate(timeout=5)
                status = json.loads((review_dir / "status.json").read_text())

                self.assertEqual(process.returncode, 90, f"{stdout}\n{stderr}")
                self.assertEqual(status["state"], "stale")
                self.assertTrue(status["target_stale"])

    def test_lost_final_freshness_check_fails_closed(self) -> None:
        review_dir = self.root / "review-lost-freshness"
        environment = os.environ.copy()
        gate = self.root / "freshness-gate"
        environment["FAKE_CLAUDE_GATE"] = str(gate)
        process = subprocess.Popen(
            self._command(self._prompt(), review_dir),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=environment,
        )
        self._wait_for_file(Path(f"{gate}.ready"))
        hidden_git = self.repo / ".git-hidden"
        (self.repo / ".git").rename(hidden_git)
        try:
            Path(f"{gate}.release").touch()
            stdout, stderr = process.communicate(timeout=5)
        finally:
            hidden_git.rename(self.repo / ".git")
        status = json.loads((review_dir / "status.json").read_text())

        self.assertEqual(process.returncode, 90, f"{stdout}\n{stderr}")
        self.assertEqual(status["state"], "stale")
        self.assertTrue(status["target_stale"])
        self.assertEqual(status["freshness_error"], "git-unavailable")

    def test_subdirectory_cwd_still_covers_the_whole_worktree(self) -> None:
        nested = self.repo / "nested"
        nested.mkdir()
        outside = self.repo / "outside-untracked.txt"
        outside.write_text("before\n", encoding="utf-8")
        review_dir = self.root / "review-subdirectory"
        environment = os.environ.copy()
        gate = self.root / "subdirectory-gate"
        environment["FAKE_CLAUDE_GATE"] = str(gate)
        process = subprocess.Popen(
            self._command(self._prompt(), review_dir, cwd=nested),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=environment,
        )
        self._wait_for_file(Path(f"{gate}.ready"))
        outside.write_text("changed\n", encoding="utf-8")
        Path(f"{gate}.release").touch()
        stdout, stderr = process.communicate(timeout=5)
        status = json.loads((review_dir / "status.json").read_text())

        self.assertEqual(process.returncode, 90, f"{stdout}\n{stderr}")
        self.assertEqual(status["state"], "stale")
        self.assertEqual(
            status["final_git"]["worktree_root"], str(self.repo.resolve())
        )

    @unittest.skipUnless(hasattr(signal, "SIGINT"), "requires POSIX signals")
    def test_interrupt_terminates_child_and_records_failure(self) -> None:
        for sent_signal, expected in ((signal.SIGINT, 130), (signal.SIGTERM, 143)):
            with self.subTest(sent_signal=sent_signal):
                review_dir = self.root / f"review-interrupt-{expected}"
                environment = os.environ.copy()
                environment["FAKE_CLAUDE_DELAY"] = "1"
                process = subprocess.Popen(
                    self._command(self._prompt(), review_dir),
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=environment,
                )
                self._wait_for_status(
                    review_dir, lambda value: value.get("state") == "running"
                )
                metadata = json.loads((review_dir / "meta.json").read_text())

                interrupted_at = time.monotonic()
                process.send_signal(sent_signal)
                stdout, stderr = process.communicate(timeout=7)
                interrupted_for = time.monotonic() - interrupted_at
                status = json.loads((review_dir / "status.json").read_text())

                self.assertEqual(process.returncode, expected, f"{stdout}\n{stderr}")
                self.assertEqual(status["state"], "failed")
                self.assertEqual(status["wrapper_exit_code"], expected)
                self.assertLess(interrupted_for, 4)
                with self.assertRaises(ProcessLookupError):
                    os.kill(metadata["pid"], 0)

    def test_empty_prompt_and_reused_directory_are_rejected(self) -> None:
        empty_prompt = self._prompt("")
        empty_review = self.root / "review-empty"
        empty = subprocess.run(
            self._command(empty_prompt, empty_review),
            check=False,
            text=True,
            capture_output=True,
        )
        self.assertNotEqual(empty.returncode, 0)
        self.assertIn("prompt file is empty", empty.stderr)
        self.assertFalse(empty_review.exists())

        completed, review_dir = self._run()
        self.assertEqual(completed.returncode, 0)
        reused = subprocess.run(
            self._command(self._prompt(), review_dir),
            check=False,
            text=True,
            capture_output=True,
        )
        self.assertNotEqual(reused.returncode, 0)
        self.assertIn("review directory is not empty", reused.stderr)

        inside_repo = subprocess.run(
            self._command(self._prompt(), self.repo / "review"),
            check=False,
            text=True,
            capture_output=True,
        )
        self.assertNotEqual(inside_repo.returncode, 0)
        self.assertIn("outside the reviewed worktree", inside_repo.stderr)

        nested = self.repo / "nested"
        nested.mkdir(exist_ok=True)
        sibling_from_nested = subprocess.run(
            self._command(
                self._prompt(), self.repo / "review-from-nested", cwd=nested
            ),
            check=False,
            text=True,
            capture_output=True,
        )
        self.assertNotEqual(sibling_from_nested.returncode, 0)
        self.assertIn(
            "outside the reviewed worktree", sibling_from_nested.stderr
        )

        review_file = self.root / "review-file"
        review_file.write_text("not a directory", encoding="utf-8")
        existing_file = subprocess.run(
            self._command(self._prompt(), review_file),
            check=False,
            text=True,
            capture_output=True,
        )
        self.assertNotEqual(existing_file.returncode, 0)
        self.assertIn("is not a directory", existing_file.stderr)

        private_review = self.root / "review-private"
        private_review.mkdir(mode=0o755)
        private = subprocess.run(
            self._command(self._prompt(), private_review),
            check=False,
            text=True,
            capture_output=True,
        )
        self.assertEqual(private.returncode, 0, private.stderr)
        self.assertEqual(private_review.stat().st_mode & 0o777, 0o700)

    def test_status_helper_text_json_and_missing_file(self) -> None:
        completed, review_dir = self._run()
        self.assertEqual(completed.returncode, 0)

        text_status = subprocess.run(
            [sys.executable, str(STATUS_HELPER), str(review_dir)],
            check=False,
            text=True,
            capture_output=True,
        )
        self.assertEqual(text_status.returncode, 0)
        self.assertIn("state=complete", text_status.stdout)
        self.assertIn("target_stale=false", text_status.stdout)

        json_status = subprocess.run(
            [sys.executable, str(STATUS_HELPER), str(review_dir), "--json"],
            check=False,
            text=True,
            capture_output=True,
        )
        self.assertEqual(json_status.returncode, 0)
        self.assertEqual(json.loads(json_status.stdout)["state"], "complete")

        missing = subprocess.run(
            [sys.executable, str(STATUS_HELPER), str(self.root / "missing")],
            check=False,
            text=True,
            capture_output=True,
        )
        self.assertEqual(missing.returncode, 2)
        self.assertIn("status file not found", missing.stderr)


if __name__ == "__main__":
    unittest.main()
