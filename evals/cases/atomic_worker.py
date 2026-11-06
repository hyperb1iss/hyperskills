"""Execute candidate checks in a child process; parent alone emits the verdict.

This process boundary is not an OS security sandbox.
"""
import importlib.util
import json
from pathlib import Path
import tempfile

checks = {}
spec = importlib.util.spec_from_file_location('candidate', Path('exporter.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
class Cancelled(BaseException):
    pass
for failure in (RuntimeError, Cancelled):
    for existing in (False, True):
        for after in (0, 1, 3):
            with tempfile.TemporaryDirectory() as temp:
                dest = Path(temp) / 'result.txt'
                if existing:
                    dest.write_bytes(b'original\x00')
                error = failure('interrupted')
                def lines():
                    for _ in range(after):
                        yield 'part'
                    raise error
                propagated = False
                try:
                    module.export_lines(lines(), dest)
                except BaseException as caught:
                    propagated = caught is error
                key = f'{failure.__name__}-{existing}-{after}'
                checks[key] = propagated and (dest.read_bytes() == b'original\x00' if existing and dest.exists() else not existing and not dest.exists()) and set(Path(temp).iterdir()) == ({dest} if existing else set())
for lines in ([], ['hello', 'caf\u00e9', '']):
    with tempfile.TemporaryDirectory() as temp:
        dest = Path(temp) / 'result.txt'
        module.export_lines(iter(lines), dest)
        checks[f'success-{len(lines)}'] = dest.read_text() == ''.join(line + '\n' for line in lines) and set(Path(temp).iterdir()) == {dest}
for existing in (False, True):
    with tempfile.TemporaryDirectory() as temp:
        dest = Path(temp) / 'result.txt'
        if existing:
            dest.write_bytes(b'original')
        failed = False
        try:
            module.export_lines(iter(['ok', '\ud800']), dest)
        except UnicodeEncodeError:
            failed = True
        preserved = dest.read_bytes() == b'original' if existing and dest.exists() else not existing and not dest.exists()
        checks[f'encoding-{existing}'] = failed and preserved and set(Path(temp).iterdir()) == ({dest} if existing else set())
Path('checks.json').write_text(json.dumps(checks))
