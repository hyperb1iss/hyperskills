from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import signal
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
RUNNER = SKILL_DIR / "scripts" / "run_claude_review.py"
STATUS_HELPER = SKILL_DIR / "scripts" / "review_status.py"


FAKE_CLAUDE = r"""#!/usr/bin/env python3
import json
import os
import sys
import time

prompt = sys.stdin.read()
capture = os.environ.get("FAKE_CLAUDE_CAPTURE")
if capture:
    with open(capture, "w", encoding="utf-8") as capture_file:
        json.dump(
            {
                "argv": sys.argv[1:],
                "prompt": prompt,
                "anthropic_api_key": os.environ.get("ANTHROPIC_API_KEY"),
                "anthropic_auth_token": os.environ.get("ANTHROPIC_AUTH_TOKEN"),
            },
            capture_file,
        )

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
if "REVIEW_FAIL" in prompt:
    events[-1]["result"] = "Verdict: FAIL\n\nFix the defect."
if "ERROR_RESULT" in prompt:
    events[-1] = {
        "type": "result",
        "subtype": "error",
        "is_error": True,
        "result": "Simulated error result, not a verdict.",
    }
if "SUCCESS_SUBTYPE_ERROR" in prompt:
    events[-1]["is_error"] = True
    events[-1]["result"] = "Spending limit reached."
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
"""


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
        self.fake_claude.write_text(textwrap.dedent(FAKE_CLAUDE), encoding="utf-8")
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
        extra: tuple[str, ...] = (),
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
            *extra,
        ]

    def _run(
        self,
        content: str = "Review the fixture.",
        environment: dict[str, str] | None = None,
        claude_bin: Path | str | None = None,
        extra: tuple[str, ...] = (),
    ) -> tuple[subprocess.CompletedProcess[str], Path]:
        review_dir = self.root / f"review-{time.monotonic_ns()}"
        completed = subprocess.run(
            self._command(self._prompt(content), review_dir, claude_bin, extra=extra),
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
            "SUCCESS_SUBTYPE_ERROR",
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
        completed, review_dir = self._run(claude_bin=self.root / "missing-claude")
        status = json.loads((review_dir / "status.json").read_text())

        self.assertEqual(completed.returncode, 127)
        self.assertEqual(status["state"], "failed")
        self.assertEqual(status["wrapper_exit_code"], 127)

    def test_launch_contract_restricts_tools_and_inherits_auth(self) -> None:
        capture = self.root / "launch.json"
        environment = os.environ.copy()
        environment.update(
            {
                "ANTHROPIC_API_KEY": "caller-auth-override",
                "ANTHROPIC_AUTH_TOKEN": "caller-auth-override",
                "FAKE_CLAUDE_CAPTURE": str(capture),
            }
        )
        completed, _ = self._run(environment=environment)
        launch = json.loads(capture.read_text())

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(launch["anthropic_api_key"], "caller-auth-override")
        self.assertEqual(launch["anthropic_auth_token"], "caller-auth-override")
        self.assertIn("--safe-mode", launch["argv"])
        self.assertEqual(
            launch["argv"][launch["argv"].index("--permission-mode") + 1], "dontAsk"
        )
        self.assertEqual(
            launch["argv"][launch["argv"].index("--tools") + 1],
            "Read,Glob,Grep",
        )
        self.assertIn("Write,Edit,MultiEdit,NotebookEdit,Bash,mcp__*", launch["argv"])

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
        status = self._wait_for_status(
            review_dir, lambda value: value.get("event_count") == 3
        )

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
        self.assertEqual(status["final_git"]["worktree_root"], str(self.repo.resolve()))

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
            self._command(self._prompt(), self.repo / "review-from-nested", cwd=nested),
            check=False,
            text=True,
            capture_output=True,
        )
        self.assertNotEqual(sibling_from_nested.returncode, 0)
        self.assertIn("outside the reviewed worktree", sibling_from_nested.stderr)

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

    def _gated_review(self, mutate, extra: tuple[str, ...] = ()) -> tuple[int, dict]:
        review_dir = self.root / f"review-gated-{time.monotonic_ns()}"
        gate = self.root / f"gate-{time.monotonic_ns()}"
        env = {**os.environ, "FAKE_CLAUDE_GATE": str(gate)}
        with subprocess.Popen(
            self._command(self._prompt(), review_dir, extra=extra),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        ) as process:
            try:
                self._wait_for_file(Path(f"{gate}.ready"))
                mutate()
            finally:
                Path(f"{gate}.release").touch()
            stdout, stderr = process.communicate(timeout=7)
            self.assertIn(process.returncode, (0, 90), f"{stdout}\n{stderr}")
        return process.returncode, json.loads((review_dir / "status.json").read_text())

    def test_subscription_mode_removes_only_child_key_and_token(self) -> None:
        capture = self.root / "subscription.json"
        environment = {
            **os.environ,
            "ANTHROPIC_API_KEY": "test-key",
            "ANTHROPIC_AUTH_TOKEN": "test-token",
            "FAKE_CLAUDE_CAPTURE": str(capture),
        }
        completed, review_dir = self._run(
            environment=environment,
            extra=("--auth-mode", "subscription"),
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        launch = json.loads(capture.read_text())
        self.assertIsNone(launch["anthropic_api_key"])
        self.assertIsNone(launch["anthropic_auth_token"])
        self.assertEqual(environment["ANTHROPIC_API_KEY"], "test-key")
        metadata = json.loads((review_dir / "meta.json").read_text())
        self.assertEqual(metadata["auth_mode"], "subscription")

    def test_index_only_change_with_identical_worktree_and_status_is_stale(
        self,
    ) -> None:
        for extra in ((), ("--scope", "source.txt")):
            with self.subTest(extra=extra):
                self.source.write_text("index B\n")
                self._git("add", "source.txt")
                self.source.write_text("worktree C\n")

                def mutate_index() -> None:
                    self.source.write_text("index D\n")
                    self._git("add", "source.txt")
                    self.source.write_text("worktree C\n")

                code, status = self._gated_review(mutate_index, extra)
                self.assertEqual(code, 90)
                self.assertTrue(status["target_stale"])

    def test_scope_detects_unstaged_untracked_and_committed_changes(self) -> None:
        selected = self.repo / "selected"
        selected.mkdir()
        tracked = selected / "tracked.txt"
        tracked.write_text("before")
        self._git("add", "selected")
        self._git("commit", "-m", "test: scoped fixture")
        for kind in ("unstaged", "untracked", "committed"):
            with self.subTest(kind=kind):

                def mutate(kind: str = kind) -> None:
                    if kind == "untracked":
                        (selected / "new.txt").write_text("new content")
                    else:
                        tracked.write_text(kind)
                        if kind == "committed":
                            self._git("add", "selected")
                            self._git("commit", "-m", "test: scoped change")

                code, status = self._gated_review(mutate, ("--scope", "selected"))
                self.assertEqual(code, 90)
                self.assertEqual(status["scope"], ["selected"])

    def test_scoped_review_survives_unrelated_index_worktree_untracked_and_commit(
        self,
    ) -> None:
        unrelated = self.repo / "unrelated.txt"
        unrelated.write_text("before")
        self._git("add", "unrelated.txt")
        self._git("commit", "-m", "test: unrelated fixture")

        def mutate() -> None:
            unrelated.write_text("committed")
            self._git("add", "unrelated.txt")
            self._git("commit", "-m", "test: unrelated change")
            unrelated.write_text("staged")
            self._git("add", "unrelated.txt")
            unrelated.write_text("unstaged")
            (self.repo / "new-unrelated.txt").write_text("untracked")

        code, status = self._gated_review(mutate, ("--scope", "source.txt"))
        self.assertEqual(code, 0)
        self.assertFalse(status["target_stale"])

    def test_repeatable_scope_is_literal_repo_relative_and_rejects_escape(self) -> None:
        literal = self.repo / "[literal].txt"
        literal.write_text("before")
        nested = self.repo / "nested"
        nested.mkdir()
        review_dir = self.root / "review-literal"
        done = subprocess.run(
            self._command(
                self._prompt(),
                review_dir,
                cwd=nested,
                extra=("--scope", "source.txt", "--scope", "[literal].txt"),
            ),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(done.returncode, 0, done.stderr)
        metadata = json.loads((review_dir / "meta.json").read_text())
        self.assertEqual(metadata["scope"], ["[literal].txt", "source.txt"])
        code, _ = self._gated_review(
            lambda: literal.write_text("after"),
            ("--scope", "[literal].txt"),
        )
        self.assertEqual(code, 90)
        (self.repo / "escape").symlink_to(self.root, target_is_directory=True)
        for value in ("../prompt.md", str(self.source), "escape", ".git/index"):
            with self.subTest(scope=value):
                done, directory = self._run(extra=("--scope", value))
                self.assertNotEqual(done.returncode, 0)
                self.assertFalse(directory.exists())

    def test_completed_report_does_not_mean_reviewer_approval(self) -> None:
        done, review_dir = self._run("REVIEW_FAIL")
        self.assertEqual(done.returncode, 0, done.stderr)
        status = json.loads((review_dir / "status.json").read_text())
        self.assertEqual(status["state"], "complete")
        self.assertIn("Verdict: FAIL", (review_dir / "final.md").read_text())
        self.assertNotIn("verdict", status)

    def _snapshot_hook_command(
        self, prompt: Path, review_dir: Path, hook: str
    ) -> list[str]:
        script = self.root / f"snapshot-hook-{time.monotonic_ns()}.py"
        script.write_text(
            "import runpy, sys, time\nfrom pathlib import Path\n"
            f"module = runpy.run_path({str(RUNNER)!r})\n"
            "main = module['main']\noriginal = main.__globals__['git_snapshot']\n"
            "calls = 0\ndef snapshot(cwd, scope):\n"
            "    global calls\n    calls += 1\n"
            + textwrap.indent(hook, "    ")
            + "\n    return original(cwd, scope)\n"
            "main.__globals__['git_snapshot'] = snapshot\nsys.exit(main())\n"
        )
        command = self._command(prompt, review_dir)
        command[1] = str(script)
        return command

    def test_prompt_copy_and_digest_survive_source_rewrite_before_launch(self) -> None:
        prompt = self._prompt("Original review brief.")
        review_dir = self.root / "review-prompt-copy"
        capture = self.root / "prompt-capture.json"
        command = self._snapshot_hook_command(
            prompt,
            review_dir,
            f"Path({str(prompt)!r}).write_text('REVIEW_FAIL')",
        )
        done = subprocess.run(
            command,
            text=True,
            capture_output=True,
            check=False,
            env={**os.environ, "FAKE_CLAUDE_CAPTURE": str(capture)},
        )
        self.assertEqual(done.returncode, 0, done.stderr)
        copied = review_dir / "prompt.md"
        self.assertEqual(copied.read_text(), "Original review brief.")
        self.assertEqual(copied.stat().st_mode & 0o777, 0o400)
        self.assertEqual(json.loads(capture.read_text())["prompt"], copied.read_text())
        metadata = json.loads((review_dir / "meta.json").read_text())
        self.assertEqual(metadata["prompt_file"], str(copied))
        self.assertEqual(
            metadata["prompt_sha256"], hashlib.sha256(copied.read_bytes()).hexdigest()
        )

    @unittest.skipUnless(os.name == "posix", "requires POSIX signals")
    def test_cancellation_during_initial_and_final_snapshots_records_failure(
        self,
    ) -> None:
        for call in (1, 2):
            with self.subTest(snapshot=call):
                review_dir = self.root / f"review-snapshot-{call}"
                ready = self.root / f"snapshot-{call}.ready"
                command = self._snapshot_hook_command(
                    self._prompt(),
                    review_dir,
                    f"if calls == {call}:\n    Path({str(ready)!r}).touch()\n    time.sleep(30)",
                )
                with subprocess.Popen(
                    command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                ) as process:
                    self._wait_for_file(ready)
                    process.send_signal(signal.SIGTERM)
                    stdout, stderr = process.communicate(timeout=7)
                self.assertEqual(process.returncode, 143, f"{stdout}\n{stderr}")
                status = json.loads((review_dir / "status.json").read_text())
                self.assertEqual(status["state"], "failed")
                self.assertEqual(status["wrapper_exit_code"], 143)
                self.assertIsNone(status["final_file"])

    @unittest.skipUnless(os.name == "posix", "requires POSIX process groups")
    def test_cleanup_kills_term_ignoring_descendants_after_leader_exit(self) -> None:
        spec = importlib.util.spec_from_file_location("review_runner", RUNNER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for leader_exited in (False, True):
            with self.subTest(leader_exited=leader_exited):
                heartbeat = self.root / f"heartbeat-{leader_exited}"
                child_code = (
                    "import signal,time\n"
                    "signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
                    f"with open({str(heartbeat)!r}, 'a', buffering=1) as f:\n"
                    "    while True:\n        f.write('x')\n        time.sleep(0.02)\n"
                )
                leader_code = (
                    "import subprocess,sys,time\n"
                    f"subprocess.Popen([sys.executable, '-c', {child_code!r}], "
                    "stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n"
                    + ("" if leader_exited else "time.sleep(30)\n")
                )
                leader = subprocess.Popen(
                    [sys.executable, "-c", leader_code], start_new_session=True
                )
                try:
                    self._wait_for_file(heartbeat)
                    if leader_exited:
                        leader.wait(timeout=3)
                    module.terminate_process_tree(leader, grace_seconds=0.1)
                    time.sleep(0.1)
                    size = heartbeat.stat().st_size
                    time.sleep(0.15)
                    self.assertEqual(
                        heartbeat.stat().st_size, size, "descendant survived cleanup"
                    )
                    self.assertIsNotNone(leader.returncode)
                finally:
                    try:
                        os.killpg(leader.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    leader.wait(timeout=3)


if __name__ == "__main__":
    unittest.main()
