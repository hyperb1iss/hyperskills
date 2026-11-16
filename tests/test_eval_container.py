"""Docker transport contract tests without invoking Docker or a provider."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('eval_container', Path(__file__).parents[1] / 'scripts/eval_container.py')
container = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(container)
IMAGE = 'sha256:' + 'a' * 64


class ContainerTests(unittest.TestCase):
    def test_mutable_image_rejected_without_docker(self):
        with patch.object(container, 'docker') as docker:
            with self.assertRaises(ValueError):
                container.image_identity('claude:latest')
            docker.assert_not_called()

    def test_no_pull_and_cleanup_after_failure(self):
        calls = []
        def fake(args):
            calls.append(args)
            return subprocess.CompletedProcess(args, 0, '9' if args[0] == 'wait' else 'exited' if args[0] == 'inspect' else '', '')
        with patch.object(container, 'docker', side_effect=fake), patch.object(container.subprocess, 'run', return_value=subprocess.CompletedProcess([], 9, 'logs', 'error')):
            code, out, err = container.execute(IMAGE, [], ['python3', 'grade.py'], network=False)
        self.assertEqual(code, 9)
        self.assertEqual(out, 'logs')
        self.assertIn('never', calls[0])
        self.assertIn('none', calls[0])
        self.assertEqual(calls[-1][:2], ['rm', '--force'])
        self.assertNotIn('--privileged', calls[0])

    def test_cleanup_on_interruption(self):
        calls = []
        with patch.object(container, 'docker', side_effect=lambda args: calls.append(args) or subprocess.CompletedProcess(args, 0, '', '')), patch.object(container.subprocess, 'run', side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                container.execute(IMAGE, [], ['python3'])
        self.assertEqual(calls[-1][:2], ['rm', '--force'])

    def test_agent_mounts_and_request_exclude_host_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ('workspace', 'skills', 'home'):
                (root / name).mkdir()
            (root / 'prompt.txt').write_text('task')
            request = {'version': 1, 'id': '1', 'task': 'task', 'arm': 'baseline', 'turn': 0,
                       'workspace': str(root / 'workspace'), 'skills': str(root / 'skills'), 'home': str(root / 'home'),
                       'prompt': str(root / 'prompt.txt'), 'metrics': str(root / 'metrics.json'),
                       'interaction': '/private/hidden-answer.json', 'grader': '/private/grader.py',
                       'configuration': {'id': 'test', 'model': 'model', 'harness': 'docker', 'settings': {'container_image': IMAGE}}}
            path = root / 'request.json'
            path.write_text(json.dumps(request))
            with patch.object(container, 'image_identity', return_value=IMAGE), patch.object(container, 'execute', return_value=(0, '', '')) as execute:
                self.assertEqual(container.run(path), 0)
            staged = json.loads((root / 'container/outputs/request.json').read_text())
            self.assertNotIn('interaction', staged)
            self.assertNotIn('grader', staged)
            self.assertNotIn('task', staged)
            self.assertNotIn('id', staged)
            self.assertNotIn('repeat', staged)
            self.assertEqual(staged['workspace'], '/workspace')
            mounts = execute.call_args.args[1]
            sources = '\n'.join(str(x) for x in mounts)
            self.assertNotIn('/private/grader', sources)
            self.assertNotIn('docker.sock', sources)
            self.assertNotIn(f'src={root},', sources)
            self.assertIn(f'src={(root / "home").resolve()}', sources)
            self.assertEqual(json.loads((root / 'metrics.json').read_text())['container_image_id'], IMAGE)

    def test_grader_preserves_fixture_layout(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            (root / 'workspace').mkdir()
            (root / 'cases/case/fixture').mkdir(parents=True)
            (root / 'cases/grade.py').write_text('print("{}")')
            path = root / 'grade-request.json'
            path.write_text(json.dumps({'container_image': IMAGE, 'workspace': str(root / 'workspace'),
                'grader': ['python3', str(root / 'cases/grade.py')], 'grader_inputs': [str(root / 'cases/case/fixture')]}))
            with patch.object(container, 'image_identity', return_value=IMAGE), patch.object(container, 'execute', return_value=(0, '{}', '')) as execute:
                container.grade(path)
            mounts = str(execute.call_args.args[1])
            self.assertIn('dst=/grader/case/fixture,readonly', mounts)
            self.assertEqual(execute.call_args.args[2][1], '/grader/grade.py')

    def test_grader_has_no_credentials_or_network(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'workspace').mkdir()
            (root / 'grade.py').write_text('print("{}")')
            path = root / 'grade-request.json'
            path.write_text(json.dumps({'container_image': IMAGE, 'workspace': str(root / 'workspace'), 'grader': ['python3', str(root / 'grade.py')]}))
            with patch.object(container, 'image_identity', return_value=IMAGE), patch.object(container, 'execute', return_value=(0, '{}', '')) as execute:
                self.assertEqual(container.grade(path), 0)
            self.assertFalse(execute.call_args.kwargs['network'])
            self.assertNotIn('credentials', execute.call_args.kwargs)
            self.assertIn('readonly', execute.call_args.args[1][0][1])


if __name__ == '__main__':
    unittest.main()
