"""Synthetic protocol oracle, never evidence about model behavior."""
import json
from pathlib import Path
import sys

request = json.loads(Path(sys.argv[-1]).read_text())
workspace = Path(request['workspace'])
if request['task'] == 'clarification-missing' and request.get('turn', 0) == 0:
    (workspace / 'clarification.json').write_text(json.dumps({'question': 'Which export format does the team prefer?'}))
    print('Synthetic oracle requested clarification.')
    sys.exit(0)
(workspace / 'exporter.py').write_text('''import json

def export_contacts(contacts):
    return json.dumps([
        {"name": contact["name"], "email": contact["email"]}
        for contact in sorted(contacts, key=lambda item: item["email"])
        if contact["active"]
    ])
''')
print('Synthetic clarification oracle; not a model trial.')
