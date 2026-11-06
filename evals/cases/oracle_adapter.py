"""Synthetic fixture oracle for plumbing checks only, never skill efficacy."""
import json
from pathlib import Path
import sys
request = json.loads(Path(sys.argv[-1]).read_text())
workspace = Path(request['workspace'])
if (workspace / 'exporter.py').exists():
    (workspace / 'exporter.py').write_text('''from pathlib import Path
import os
import tempfile

def export_lines(lines, destination):
    destination = Path(destination)
    fd, name = tempfile.mkstemp(dir=destination.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as output:
            for line in lines:
                output.write(line + "\\n")
        os.replace(name, destination)
    finally:
        Path(name).unlink(missing_ok=True)
''')
elif (workspace / 'cache.py').exists():
    (workspace / 'review.json').write_text(json.dumps({'findings':[{'file':'cache.py','line':3,'trigger':'A stored zero is falsy.','impact':'The loader is invoked despite a cache hit.'}]}))
elif (workspace / 'draft.md').exists():
    (workspace / 'edited.md').write_text('The export pilot processed 240 files; 7 failed. Estimated recovery is 2-4 hours, not a guarantee. "Keep the original until verification finishes." This pilot is not a production rollout. Command: `exportctl retry --limit 7`.\n')
else:
    (workspace / 'answer.json').write_text(json.dumps({'version':'2.4.0','evidence_file':'releases.json','limitation':'The frozen packet cannot establish the current live release.'}))
print('Synthetic oracle completed; not a model trial.')
