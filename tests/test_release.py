"""Release behavior against real Git repositories and a stateful fake GitHub API."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "release.py"
FAKE_GH = r"""#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
p = Path(os.environ['FAKE_GH_STATE'])
s = json.loads(p.read_text())
args = sys.argv[1:]
endpoint = args[args.index('--include') + 1].split('/', 3)[3]
data = json.load(sys.stdin) if '--input' in args else None
s.setdefault('calls', []).append([endpoint, data])
code = 200
body = {}
if s.get('error'):
    code = s['error']
elif endpoint.startswith('git/ref/tags/'):
    if s.get('tag'):
        body = {'object': s['tag']}
    else:
        code = 404
elif endpoint == 'git/refs':
    s['tag'] = {'type': 'commit', 'sha': data['sha']}
    body = {'object': s['tag']}
    code = 201
elif endpoint.startswith('releases/tags/'):
    if s.get('release'):
        body = s['release']
    else:
        code = 404
elif endpoint == 'releases':
    if s.get('fail_release_once'):
        del s['fail_release_once']
        code = 500
    else:
        s['release'] = data
        body = data
        code = 201
else:
    code = 500
p.write_text(json.dumps(s))
print(f'HTTP/2.0 {code} response\nContent-Type: application/json\n\n{json.dumps(body)}')
sys.exit(0 if code < 400 else 1)
"""


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.repo = self.base / "repo"
        self.repo.mkdir()
        self.env = os.environ.copy()
        self.env.update({"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull})
        self.git("init", "-q")
        self.git("config", "user.email", "test@example.com")
        self.git("config", "user.name", "Release Test")
        (self.repo / ".claude-plugin").mkdir()
        (self.repo / ".claude-plugin/plugin.json").write_text(
            json.dumps({"name": "hyperskills", "version": "3.12.0"}, indent=2) + "\n"
        )
        self.commit("initial source")
        self.source = self.git("rev-parse", "HEAD")
        self.notes = self.base / "notes.md"
        self.notes.write_text("Correct the review output.\n")
        bindir = self.base / "bin"
        bindir.mkdir()
        fake = bindir / "gh"
        fake.write_text(FAKE_GH)
        fake.chmod(0o755)
        self.state = self.base / "state.json"
        self.state.write_text("{}")
        self.env["PATH"] = str(bindir) + os.pathsep + self.env["PATH"]
        self.env["FAKE_GH_STATE"] = str(self.state)

    def git(self, *args):
        return subprocess.check_output(
            ["git", *args], cwd=self.repo, env=self.env, text=True
        ).strip()

    def commit(self, message):
        self.git("add", ".")
        self.git("commit", "-qm", message)

    def run_cli(self, *args, success=True):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=self.repo,
            env=self.env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(
            result.returncode, 0 if success else 1, result.stdout + result.stderr
        )
        return result

    def prepare(self, bump="patch", success=True):
        return self.run_cli(
            "prepare", "--bump", bump, "--notes-file", str(self.notes), success=success
        )

    def release_commit(self):
        self.prepare()
        self.commit("release")
        return self.git("rev-parse", "HEAD")

    def publish(self, success=True):
        return self.run_cli("publish", "--repo", "owner/repo", success=success)

    def state_data(self):
        return json.loads(self.state.read_text())

    def test_bootstrap_has_no_candidate(self):
        self.run_cli("check")
        self.assertEqual(self.run_cli("candidate").stdout.strip(), "false")
        self.publish(success=False)
        self.assertEqual(self.state_data(), {})

    def test_prepare_repeats_without_duplicate_bump(self):
        self.assertEqual(self.prepare().stdout.strip(), "3.12.1")
        before = {
            p: (self.repo / p).read_bytes()
            for p in ["release.json", "CHANGELOG.md", ".claude-plugin/plugin.json"]
        }
        self.prepare()
        self.assertEqual(before, {p: (self.repo / p).read_bytes() for p in before})
        self.assertEqual(self.git("rev-parse", "HEAD"), self.source)
        self.run_cli("check")

    def test_null_bootstrap(self):
        (self.repo / "release.json").write_text("null\n")
        (self.repo / "CHANGELOG.md").write_text(
            "# Changelog\n\nReleases are recorded here.\n"
        )
        self.commit("bootstrap")
        self.run_cli("check")
        self.assertEqual(self.run_cli("candidate").stdout.strip(), "false")
        self.prepare()
        self.commit("release")
        self.run_cli("check")
        self.publish()

    def test_cleared_record_is_rejected(self):
        self.release_commit()
        (self.repo / "release.json").write_text("null\n")
        self.run_cli("check", success=False)
        self.commit("clear record")
        self.run_cli("check", success=False)
        self.assertEqual(self.run_cli("candidate").stdout.strip(), "true")

    def test_bumps(self):
        self.assertEqual(self.prepare("minor").stdout.strip(), "3.13.0")
        self.commit("minor release")
        self.assertEqual(self.prepare("major").stdout.strip(), "4.0.0")
        self.assertEqual((self.repo / "CHANGELOG.md").read_text().count("## 3.13.0"), 1)

    def test_rejects_dirty_unrelated_file(self):
        (self.repo / "work.txt").write_text("someone else")
        self.prepare(success=False)
        self.assertFalse((self.repo / "release.json").exists())

    def test_rejects_hidden_index_change(self):
        p = self.repo / ".claude-plugin/plugin.json"
        original = p.read_text()
        p.write_text(original + "\n")
        self.git("add", str(p))
        p.write_text(original)
        self.prepare(success=False)

    def test_conflicting_repeat_preserves_files(self):
        self.prepare()
        before = (self.repo / "release.json").read_bytes()
        self.notes.write_text("different notes")
        self.prepare(success=False)
        self.assertEqual((self.repo / "release.json").read_bytes(), before)

    def test_tampered_pending_file_rejected(self):
        self.prepare()
        (self.repo / "CHANGELOG.md").write_text("user edits")
        self.prepare(success=False)
        self.run_cli("check", success=False)

    def test_release_is_candidate_but_later_content_is_not(self):
        self.release_commit()
        self.run_cli("check")
        self.assertEqual(self.run_cli("candidate").stdout.strip(), "true")
        (self.repo / "skill.md").write_text("new guidance")
        self.commit("content")
        self.run_cli("check")
        self.assertEqual(self.run_cli("candidate").stdout.strip(), "false")
        self.publish(success=False)

    def test_stale_source_is_rejected(self):
        self.prepare()
        (self.repo / "other").write_text("advanced main")
        self.git("add", "other")
        self.git("commit", "-qm", "main advances")
        self.commit("stale release")
        self.run_cli("check", success=False)
        self.publish(success=False)
        self.assertEqual(self.state_data(), {})

    def test_release_commit_cannot_bundle_content(self):
        self.prepare()
        (self.repo / "extra").write_text("unreviewed content")
        self.commit("release plus extra")
        self.run_cli("check", success=False)

    def test_release_merge_commit_is_supported(self):
        self.git("checkout", "-qb", "release-branch")
        self.release_commit()
        self.git("checkout", "-q", "-")
        self.git("merge", "--no-ff", "-qm", "merge release", "release-branch")
        self.run_cli("check")
        self.publish()
        self.assertEqual(self.state_data()["tag"]["sha"], self.git("rev-parse", "HEAD"))

    def test_record_deletion_is_rejected(self):
        self.release_commit()
        (self.repo / "release.json").unlink()
        self.run_cli("check", success=False)
        self.commit("remove record")
        self.run_cli("check", success=False)
        self.assertEqual(self.run_cli("candidate").stdout.strip(), "true")

    def test_corrupt_version_is_rejected(self):
        self.release_commit()
        p = self.repo / ".claude-plugin/plugin.json"
        p.write_text(p.read_text().replace("3.12.1", "3.12.9"))
        self.run_cli("check", success=False)

    def test_publish_exact_commit_and_repeat(self):
        sha = self.release_commit()
        self.publish()
        first = self.state_data()
        self.assertEqual(first["tag"], {"type": "commit", "sha": sha})
        self.assertEqual(first["release"]["target_commitish"], sha)
        self.assertEqual(first["release"]["body"], self.notes.read_text())
        self.publish()
        mutations = [call for call in self.state_data()["calls"] if call[1] is not None]
        self.assertEqual(len(mutations), 2)

    def test_tag_mismatch_never_overwrites(self):
        self.release_commit()
        self.state.write_text(
            json.dumps({"tag": {"type": "commit", "sha": self.source}})
        )
        self.publish(success=False)
        self.assertFalse(any(call[1] for call in self.state_data()["calls"]))

    def test_annotated_tag_is_not_silently_replaced(self):
        sha = self.release_commit()
        self.state.write_text(json.dumps({"tag": {"type": "tag", "sha": sha}}))
        self.publish(success=False)
        self.assertFalse(any(call[1] for call in self.state_data()["calls"]))

    def test_partial_publication_resumes(self):
        self.release_commit()
        self.state.write_text(json.dumps({"fail_release_once": True}))
        self.publish(success=False)
        self.assertIn("tag", self.state_data())
        self.assertNotIn("release", self.state_data())
        self.publish()
        self.assertEqual(
            sum(call[0] == "git/refs" for call in self.state_data()["calls"]), 1
        )
        self.assertIn("release", self.state_data())

    def test_non_404_failure_is_not_absence(self):
        self.release_commit()
        for code in (401, 403, 429, 500):
            with self.subTest(code=code):
                self.state.write_text(json.dumps({"error": code}))
                self.publish(success=False)
                self.assertEqual(len(self.state_data()["calls"]), 1)
                self.assertIsNone(self.state_data()["calls"][0][1])

    def test_modified_existing_release_refused(self):
        self.release_commit()
        self.publish()
        state = self.state_data()
        state["release"]["body"] = "human edit"
        state["calls"] = []
        self.state.write_text(json.dumps(state))
        self.publish(success=False)
        self.assertFalse(any(call[1] for call in self.state_data()["calls"]))

    def test_dirty_publish_has_no_remote_effect(self):
        self.release_commit()
        (self.repo / "dirty").write_text("pending")
        self.publish(success=False)
        self.assertEqual(self.state_data(), {})


if __name__ == "__main__":
    unittest.main()
