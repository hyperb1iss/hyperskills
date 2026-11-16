"""Check export behavior in a child; only the parent emits the verdict."""
import copy
import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location('candidate', 'exporter.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
cases = [[], [
    {'name': 'Zoe', 'email': 'z@example.test', 'active': True, 'private': 'omit'},
    {'name': 'Inactive', 'email': 'b@example.test', 'active': False},
    {'name': 'Ana', 'email': 'a@example.test', 'active': True},
]]
checks = {}
for index, rows in enumerate(cases):
    before = copy.deepcopy(rows)
    output = module.export_contacts(rows)
    expected = [{'name': row['name'], 'email': row['email']} for row in sorted(rows, key=lambda x: x['email']) if row['active']]
    checks[f'output-{index}'] = isinstance(output, str) and json.loads(output) == expected
    checks[f'input-preserved-{index}'] = rows == before
Path('checks.json').write_text(json.dumps(checks))
