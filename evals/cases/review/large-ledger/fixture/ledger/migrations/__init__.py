"""Schema migrations. Each module mNNNN_name.py defines apply(store); they run once, in number order."""
import importlib
import pkgutil
import re

PATTERN = re.compile(r"m(\d{4})_\w+$")


def available():
    found = []
    for module in pkgutil.iter_modules(__path__):
        match = PATTERN.match(module.name)
        if match:
            found.append((int(match.group(1)), module.name))
    return sorted(found)


def migrate(store, target=None):
    """Apply every migration above store.schema_version, up to target; returns the numbers applied."""
    applied = []
    for number, name in available():
        if number <= store.schema_version or (target is not None and number > target):
            continue
        importlib.import_module(f"{__name__}.{name}").apply(store)
        store.schema_version = number
        applied.append(number)
    return applied
