"""Exercise malformed metadata and broken resources at the validator boundary."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate_skills.py"
spec = importlib.util.spec_from_file_location("validate_skills", SCRIPT)
assert spec is not None and spec.loader is not None
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


class ValidatorTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        manifests = self.root / ".claude-plugin"
        manifests.mkdir()
        (manifests / "plugin.json").write_text('{"name":"test","version":"1.0.0"}')
        (manifests / "marketplace.json").write_text('{"name":"test","plugins":[]}')

    def skill(
        self, name="example", frontmatter=None, body="# Example\nUseful guidance."
    ):
        directory = self.root / "skills" / name
        directory.mkdir(parents=True, exist_ok=True)
        fields = (
            frontmatter
            if frontmatter is not None
            else f"name: {name}\ndescription: Use for X"
        )
        (directory / "SKILL.md").write_text(f"---\n{fields}\n---\n{body}\n")
        return directory

    def test_valid_folded_description_and_reference(self):
        directory = self.skill(
            frontmatter="name: example\ndescription: >\n  Use for X\n  and Y"
        )
        (directory / "references").mkdir()
        (directory / "references" / "guide.md").write_text("# Guide")
        with (directory / "SKILL.md").open("a") as stream:
            stream.write("\nRead [the guide](references/guide.md).\n")
        self.assertEqual(validator.validate(self.root), (1, []))

    def test_failure_in_first_directory_survives_later_success(self):
        self.skill("a-invalid", "name: a-invalid")
        self.skill("z-valid")
        count, errors = validator.validate(self.root)
        self.assertEqual(count, 2)
        self.assertTrue(any("description" in error for error in errors))

    def test_missing_skill_file(self):
        directory = self.skill()
        (directory / "SKILL.md").unlink()
        self.assertTrue(validator.validate(self.root)[1])

    def test_metadata_errors(self):
        cases = (
            "name: example\ndescription: [unterminated",
            "name: example\nname: example\ndescription: X",
            "name: other\ndescription: X",
            "name: example\ndescription: false",
            "name: example\ndescription: " + "x" * 1025,
            "- example\n- X",
            "[name]: example\ndescription: X",
        )
        for fields in cases:
            with self.subTest(fields=fields):
                self.skill(frontmatter=fields)
                self.assertTrue(validator.validate(self.root)[1])

    def test_missing_delimiter(self):
        directory = self.skill()
        (directory / "SKILL.md").write_text("---\nname: example\ndescription: X\n")
        self.assertTrue(validator.validate(self.root)[1])

    def test_broken_resource(self):
        self.skill(body="Read `references/missing.md`.")
        self.assertTrue(
            any("missing bundled" in item for item in validator.validate(self.root)[1])
        )

    def test_resource_escape(self):
        self.skill(body="Read `references/../../outside.md`.")
        self.assertTrue(
            any("escapes" in item for item in validator.validate(self.root)[1])
        )

    def test_invalid_manifest(self):
        self.skill()
        (self.root / ".claude-plugin" / "plugin.json").write_text("{broken")
        self.assertTrue(validator.validate(self.root)[1])

    def test_empty_library(self):
        self.assertTrue(validator.validate(self.root)[1])

    def test_semantic_version_boundaries(self):
        self.skill()
        cases = {
            "1.0.0": True,
            "1.0.0+build.1": True,
            "1.0.0-rc.1+build.2": True,
            "0.0.0-0": True,
            "1.0.0-01alpha": True,
            "01.0.0": False,
            "1.0.0-01": False,
            "1.0.0-..": False,
            "1.0.0+": False,
            "1.0.0+build..2": False,
            "1.0.0-α": False,
            "1.0.١": False,
        }
        for version, valid in cases.items():
            with self.subTest(version=version):
                (self.root / ".claude-plugin" / "plugin.json").write_text(
                    json.dumps({"name": "test", "version": version})
                )
                self.assertEqual(not validator.validate(self.root)[1], valid)


if __name__ == "__main__":
    unittest.main()
