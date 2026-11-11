"""Visible action traces exclude hidden reasoning and require successful reads."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / 'scripts'))
from eval_trace import normalize


class TraceTests(unittest.TestCase):
    def test_visible_trace_preserves_tools_but_not_thinking(self):
        events = [
            {'type': 'assistant', 'message': {'content': [
                {'type': 'thinking', 'thinking': 'PRIVATE'},
                {'type': 'text', 'text': 'I will inspect the file.'},
                {'type': 'tool_use', 'id': 'a', 'name': 'Read', 'input': {'file_path': '/skills/implement/SKILL.md'}},
                {'type': 'tool_use', 'id': 'b', 'name': 'Read', 'input': {'file_path': '/skills/research/SKILL.md'}},
                {'type': 'tool_use', 'id': 'c', 'name': 'Bash', 'input': {'command': 'python -m unittest'}}]}},
            {'type': 'user', 'message': {'content': [
                {'type': 'tool_result', 'tool_use_id': 'a', 'content': [{'type': 'text', 'text': 'skill body'}, {'type': 'thinking', 'thinking': 'PRIVATE'}]},
                {'type': 'tool_result', 'tool_use_id': 'b', 'is_error': True, 'content': 'Denied'}]}}
        ]
        trace = normalize(events, '/skills')
        self.assertNotIn('PRIVATE', str(trace))
        self.assertEqual(trace['skill_read_attempts'], ['implement', 'research'])
        self.assertEqual(trace['skills_read_successfully'], ['implement'])
        self.assertEqual(trace['actions'][3]['name'], 'Bash')

    def test_unreturned_read_is_not_loaded(self):
        events = [{'type': 'assistant', 'message': {'content': [{'type': 'tool_use', 'id': 'a', 'name': 'Read', 'input': {'file_path': '/skills/a/SKILL.md'}}]}}]
        self.assertEqual(normalize(events, '/skills')['skills_read_successfully'], [])

    def test_outside_skill_path_is_not_attributed(self):
        events = [{'type': 'assistant', 'message': {'content': [{'type': 'tool_use', 'id': 'a', 'name': 'Read', 'input': {'file_path': '/skills/../answer.md'}}]}}]
        self.assertEqual(normalize(events, '/skills')['skill_read_attempts'], [])


if __name__ == '__main__':
    unittest.main()
