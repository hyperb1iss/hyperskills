"""Subtraction preserves source and changes only the selected exact section."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('eval_subtract', ROOT / 'scripts/eval_subtract.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class SubtractionTests(unittest.TestCase):
    def test_only_named_section_changes(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source = base / 'source'
            (source / 'implement').mkdir(parents=True)
            original = '# Title\n\n## Keep\nKeep.\n\n## Remove\nRemove.\n### Nested\nAlso remove.\n\n## Tail\nTail.\n'
            (source / 'implement/SKILL.md').write_text(original)
            (source / 'implement/other.txt').write_text('unchanged')
            experiment = base / 'experiment.json'
            experiment.write_text(json.dumps({'skill': 'implement', 'section': 'Remove', 'hypothesis': 'Reduce process.'}))
            receipt = module.prepare(source, base / 'candidate', experiment)
            self.assertEqual((source / 'implement/SKILL.md').read_text(), original)
            self.assertEqual(receipt['changed_paths'], ['implement/SKILL.md'])
            self.assertEqual((base / 'candidate/skills/implement/other.txt').read_text(), 'unchanged')
            self.assertEqual((base / 'candidate/skills/implement/SKILL.md').read_text(), '# Title\n\n## Keep\nKeep.\n\n## Tail\nTail.\n')
            self.assertEqual(receipt['status'], 'prepared-not-evaluated')
            with self.assertRaisesRegex(ValueError, 'already exists'):
                module.prepare(source, base / 'candidate', experiment)
            with self.assertRaisesRegex(ValueError, 'separate'):
                module.prepare(source, source / 'candidate', experiment)

    def test_missing_or_duplicate_section_fails(self):
        for text in ('## Other\n', '## Remove\nA\n## Remove\nB\n'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                module.subtract(text, 'Remove')

    def test_exact_heading_not_substring(self):
        text = '## Remove later\nKeep\n\n## Remove\nCut\n'
        self.assertEqual(module.subtract(text, 'Remove')[0], '## Remove later\nKeep\n\n')

if __name__ == '__main__':
    unittest.main()
