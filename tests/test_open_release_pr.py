"""Exercise PR preparation with real local Git remotes and a fake GitHub CLI."""

import contextlib
import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "open_release_pr.py"
spec = importlib.util.spec_from_file_location("open_release_pr", SCRIPT)
opener = importlib.util.module_from_spec(spec)
spec.loader.exec_module(opener)


class ReleasePRTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.remote = self.root / "remote.git"
        self.git("init", "--bare", str(self.remote), cwd=self.root)
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Release test")
        self.git("config", "user.email", "test@example.invalid")
        (self.repo / ".claude-plugin").mkdir()
        (self.repo / ".claude-plugin/plugin.json").write_text('{"version":"1.0.0"}')
        (self.repo / "CHANGELOG.md").write_text("# Changelog\n")
        (self.repo / "release.json").write_text("null\n")
        self.git("add", ".")
        self.git("commit", "-m", "initial")
        self.source = self.git("rev-parse", "HEAD")
        self.git("remote", "add", "origin", str(self.remote))
        self.git("push", "origin", "main")
        notes = self.root / "notes.md"
        notes.write_text("Keep `literal` and $(not-a-command) intact.\n")
        self.notes = notes
        self.calls = []
        self.prs = []
        self.fail_create = False
        self.real_run = opener.run

    def git(self, *args, cwd=None):
        return subprocess.check_output(
            ["git", *args], cwd=cwd or self.repo, text=True, stderr=subprocess.DEVNULL
        ).strip()

    def prepare(self):
        subprocess.run(
            [
                os.sys.executable,
                str(SCRIPT.with_name("release.py")),
                "prepare",
                "--bump",
                "patch",
                "--notes-file",
                str(self.notes),
            ],
            cwd=self.repo,
            check=True,
            capture_output=True,
            text=True,
        )

    def fake_run(self, *args, input=None):
        if args[0] != "gh":
            return self.real_run(*args, input=input)
        self.calls.append((args, input))
        if args[1:3] == ("pr", "list"):
            return json.dumps(self.prs)
        if args[1:3] == ("pr", "create"):
            if self.fail_create:
                raise subprocess.CalledProcessError(
                    1, args, stderr="provider unavailable"
                )
            self.prs = [{"url": "https://example.invalid/pr/1", "state": "OPEN"}]
            return self.prs[0]["url"]
        self.assertEqual(args[1], "api")
        self.assertEqual(json.loads(input)["ref"], self.branch)
        return ""

    @property
    def branch(self):
        return f"release/v1.0.1-{self.source[:12]}"

    def open(self):
        with contextlib.chdir(self.repo), patch.object(opener, "run", self.fake_run):
            return opener.open_pr("owner/repo")

    def fresh_source(self):
        # The workflow starts again from the immutable source in its own checkout.
        self.git("reset", "--hard", self.source)
        self.prepare()

    def test_create_then_retry_reuses_branch_and_pr(self):
        self.prepare()
        self.open()
        head = self.git("rev-parse", "HEAD")
        self.assertEqual(self.git("ls-remote", "origin", self.branch).split()[0], head)
        self.assertIn("$(not-a-command)", self.calls[1][1])
        self.fresh_source()
        self.open()
        self.assertEqual(sum(c[0][1:3] == ("pr", "create") for c in self.calls), 1)
        self.assertEqual(self.git("ls-remote", "origin", self.branch).split()[0], head)

    def test_resume_after_branch_push_and_failed_pr_creation(self):
        self.prepare()
        self.fail_create = True
        with self.assertRaises(subprocess.CalledProcessError):
            self.open()
        head = self.git("rev-parse", "HEAD")
        self.fresh_source()
        self.fail_create = False
        self.open()
        self.assertEqual(self.git("ls-remote", "origin", self.branch).split()[0], head)

    def test_conflicting_remote_branch_is_preserved(self):
        self.prepare()
        self.open()
        original = self.git("rev-parse", "HEAD")
        self.fresh_source()
        self.notes.write_text("Different release notes.\n")
        self.git("reset", "--hard", self.source)
        self.prepare()
        with self.assertRaisesRegex(ValueError, "refusing to overwrite"):
            self.open()
        self.assertEqual(
            self.git("ls-remote", "origin", self.branch).split()[0], original
        )

    def test_unrelated_edits_are_not_staged_or_pushed(self):
        self.prepare()
        (self.repo / "unrelated.txt").write_text("human work")
        with self.assertRaisesRegex(ValueError, "unrelated edits"):
            self.open()
        self.assertEqual(self.git("diff", "--cached", "--name-only"), "")
        self.assertEqual(self.git("ls-remote", "origin", self.branch), "")

    def test_closed_pr_is_not_reopened(self):
        self.prepare()
        self.prs = [{"url": "https://example.invalid/pr/1", "state": "CLOSED"}]
        with self.assertRaisesRegex(ValueError, "closed"):
            self.open()
        self.assertFalse(any(c[0][1:3] == ("pr", "create") for c in self.calls))

    def test_staged_release_draft_survives_generated_worktree(self):
        self.prepare()
        changelog = self.repo / "CHANGELOG.md"
        generated = changelog.read_text()
        changelog.write_text("human staged draft\n")
        self.git("add", "CHANGELOG.md")
        staged = self.git("rev-parse", ":CHANGELOG.md")
        changelog.write_text(generated)
        with self.assertRaisesRegex(ValueError, "conflicting staged"):
            self.open()
        self.assertEqual(self.git("rev-parse", ":CHANGELOG.md"), staged)
        self.assertEqual(changelog.read_text(), generated)
        self.assertEqual(self.git("ls-remote", "origin", self.branch), "")

    def test_whitespace_filename_is_not_confused_with_release_file(self):
        self.prepare()
        for name in (" CHANGELOG.md", "CHANGELOG.md "):
            with self.subTest(name=name):
                (self.repo / name).write_text("private human work\n")
                self.git("add", "--", name)
                staged = self.git("write-tree")
                with self.assertRaisesRegex(ValueError, "unrelated edits"):
                    self.open()
                self.assertEqual(self.git("write-tree"), staged)
                self.assertEqual(self.git("ls-remote", "origin", self.branch), "")
                self.git("rm", "--cached", "--", name)
                (self.repo / name).unlink()

    def test_staged_release_deletion_is_preserved(self):
        self.prepare()
        self.git("rm", "--cached", "CHANGELOG.md")
        staged = self.git("write-tree")
        with self.assertRaisesRegex(ValueError, "staged release deletion"):
            self.open()
        self.assertEqual(self.git("write-tree"), staged)
        self.assertTrue((self.repo / "CHANGELOG.md").is_file())
        self.assertEqual(self.git("ls-remote", "origin", self.branch), "")


if __name__ == "__main__":
    unittest.main()
