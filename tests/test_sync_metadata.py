"""Exercise generation against disposable repositories and malformed inputs."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from sync_metadata import replace_region, synchronize


def marker(name):
    return f"<!-- BEGIN GENERATED: {name} -->\nold\n<!-- END GENERATED: {name} -->"


class MetadataTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        self.write(
            ".claude-plugin/plugin.json",
            json.dumps(
                {
                    "name": "test",
                    "version": "1.0.0",
                    "description": "Canonical description",
                }
            ),
        )
        self.write(
            ".claude-plugin/marketplace.json",
            json.dumps(
                {
                    "name": "test",
                    "plugins": [
                        {"name": "test", "description": "Canonical description"}
                    ],
                }
            ),
        )
        self.write(
            "AGENTS.md",
            "authored preface\n"
            + marker("repository-map")
            + "\n"
            + marker("skill-inventory")
            + "\nauthored ending\n",
        )
        self.write("README.md", "authored readme\n" + marker("skill-badge") + "\n")
        self.skill("zeta")
        self.skill("alpha")

    def write(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    def skill(self, name):
        self.write(
            f"skills/{name}/SKILL.md",
            f"---\nname: {name}\ndescription: A valid skill description.\n---\nUseful guidance.\n",
        )

    def snapshot(self):
        return {
            name: (self.root / name).read_bytes()
            for name in ("README.md", "AGENTS.md", ".claude-plugin/marketplace.json")
        }

    def test_check_reports_drift_without_writing(self):
        before = self.snapshot()
        self.assertEqual(
            set(synchronize(self.root, check=True)), {"README.md", "AGENTS.md"}
        )
        self.assertEqual(self.snapshot(), before)

    def test_idempotent_sorted_generation_preserves_prose(self):
        self.write("skills/alpha/references/guide.md", "reference")
        self.write("skills/alpha/references/fixtures/example.txt", "fixture")
        synchronize(self.root)
        first = self.snapshot()
        self.assertEqual(synchronize(self.root), [])
        self.assertEqual(first, self.snapshot())
        agents = first["AGENTS.md"].decode()
        self.assertTrue(agents.startswith("authored preface\n"))
        self.assertTrue(agents.endswith("\nauthored ending\n"))
        self.assertLess(agents.index("alpha/"), agents.index("zeta/"))
        self.assertRegex(agents, r"\[alpha\].*\| 2\s*\|")
        self.assertIn("Skills-2-", first["README.md"].decode())

    def test_add_remove_and_rename_skill(self):
        synchronize(self.root)
        self.skill("beta")
        (self.root / "skills/zeta").rename(self.root / "skills/gamma")
        self.skill("gamma")
        (self.root / "skills/alpha/SKILL.md").unlink()
        (self.root / "skills/alpha").rmdir()
        synchronize(self.root)
        agents = (self.root / "AGENTS.md").read_text()
        self.assertIn("[beta]", agents)
        self.assertIn("[gamma]", agents)
        self.assertNotIn("[zeta]", agents)
        self.assertNotIn("[alpha]", agents)
        self.assertIn("Skills-2-", (self.root / "README.md").read_text())

    def test_missing_or_duplicate_markers_prevent_all_writes(self):
        for content in ("no markers", marker("skill-badge") * 2):
            with self.subTest(content=content):
                self.write("README.md", content)
                before = self.snapshot()
                with self.assertRaisesRegex(ValueError, "exactly one marker pair"):
                    synchronize(self.root)
                self.assertEqual(before, self.snapshot())

    def test_reversed_and_nested_markers_fail(self):
        for content in (
            "<!-- END GENERATED: a --><!-- BEGIN GENERATED: a -->",
            "<!-- BEGIN GENERATED: a --><!-- BEGIN GENERATED: b --><!-- END GENERATED: a -->",
        ):
            with self.assertRaisesRegex(ValueError, "reversed or nested"):
                replace_region(content, "a", "generated")

    def test_invalid_skill_prevents_all_writes(self):
        self.write("skills/zeta/SKILL.md", "invalid")
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "frontmatter"):
            synchronize(self.root)
        self.assertEqual(before, self.snapshot())

    def test_empty_skill_library_fails(self):
        for name in ("alpha", "zeta"):
            (self.root / f"skills/{name}/SKILL.md").unlink()
            (self.root / f"skills/{name}").rmdir()
        with self.assertRaisesRegex(ValueError, "no skills found"):
            synchronize(self.root)

    def test_ignored_build_files_do_not_change_tree(self):
        self.write(".gitignore", "cache/\n")
        synchronize(self.root)
        self.write("cache/noise", "not source")
        self.assertEqual(synchronize(self.root, check=True), [])

    def test_reference_counts_ignore_cache_but_include_new_source(self):
        self.write(".gitignore", "cache/\n")
        synchronize(self.root)
        before = self.snapshot()
        self.write("skills/alpha/references/cache/noise", "ignored artifact")
        self.assertEqual(synchronize(self.root, check=True), [])
        self.assertEqual(before, self.snapshot())
        self.write("skills/alpha/references/new-guide.md", "new reference")
        self.assertIn("AGENTS.md", synchronize(self.root, check=True))
        synchronize(self.root)
        agents = (self.root / "AGENTS.md").read_text()
        self.assertRegex(agents, r"\[alpha\].*\| 1\s*\|")
        self.assertIn("new-guide.md", agents)
        self.assertNotIn("noise", agents)

    def test_ignored_skill_is_rejected(self):
        self.write(".gitignore", "skills/zeta/\n")
        with self.assertRaisesRegex(ValueError, "ignored by Git: zeta"):
            synchronize(self.root)

    def test_marketplace_description_preserves_other_values(self):
        original = {
            "name": "catalog",
            "owner": {"name": "Someone"},
            "plugins": [
                {"name": "unrelated", "description": "Keep me", "source": "elsewhere"},
                {
                    "name": "test",
                    "description": "stale",
                    "source": "./",
                    "custom": [1, "é"],
                },
            ],
        }
        self.write(".claude-plugin/marketplace.json", json.dumps(original))
        before = self.snapshot()
        self.assertIn(
            ".claude-plugin/marketplace.json", synchronize(self.root, check=True)
        )
        self.assertEqual(before, self.snapshot())
        synchronize(self.root)
        original["plugins"][1]["description"] = "Canonical description"
        self.assertEqual(
            json.loads((self.root / ".claude-plugin/marketplace.json").read_text()),
            original,
        )
        self.assertEqual(synchronize(self.root, check=True), [])

    def test_missing_or_duplicate_marketplace_matches_prevent_writes(self):
        for entries in ([], [{"name": "test"}, {"name": "test"}], [{"name": "other"}]):
            with self.subTest(entries=entries):
                self.write(
                    ".claude-plugin/marketplace.json",
                    json.dumps({"name": "test", "plugins": entries}),
                )
                before = self.snapshot()
                with self.assertRaisesRegex(ValueError, "exactly one matching"):
                    synchronize(self.root)
                self.assertEqual(before, self.snapshot())

    def test_empty_canonical_description_prevents_writes(self):
        for description in (None, "", "   ", 42):
            with self.subTest(description=description):
                self.write(
                    ".claude-plugin/plugin.json",
                    json.dumps(
                        {"name": "test", "version": "1.0.0", "description": description}
                    ),
                )
                before = self.snapshot()
                with self.assertRaisesRegex(
                    ValueError, "description must be a nonempty"
                ):
                    synchronize(self.root)
                self.assertEqual(before, self.snapshot())

    def test_symlink_output_does_not_modify_target(self):
        target = self.root / "external.md"
        target.write_text(marker("skill-badge"))
        (self.root / "README.md").unlink()
        (self.root / "README.md").symlink_to(target)
        before = target.read_bytes()
        with self.assertRaisesRegex(ValueError, "must not be a symlink"):
            synchronize(self.root)
        self.assertEqual(target.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
