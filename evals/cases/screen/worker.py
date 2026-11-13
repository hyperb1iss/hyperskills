"""Exercise one screen case in a child process. Only the parent grader emits a verdict."""
import copy, importlib, json, logging, os, subprocess, sys, warnings
from pathlib import Path

case = sys.argv[1]
sys.path.insert(0, os.getcwd())
checks = {}


def attempt(name, fn):
    try:
        checks[name] = bool(fn())
    except Exception:
        checks[name] = False


if case == 'batch-isolation':
    from jobs.invoices import sync_invoices

    class Client:
        def __init__(self, bad=()):
            self.bad, self.seen = set(bad), []

        def upsert_invoice(self, invoice):
            self.seen.append(invoice['id'])
            if invoice['id'] in self.bad:
                raise RuntimeError('billing rejected the invoice')

    rows = [{'id': 1}, {'id': 2}, {'id': 3}]
    good, flaky = Client(), Client(bad=[2])
    attempt('feature_counts_synced', lambda: sync_invoices(copy.deepcopy(rows), good) == 3 and good.seen == [1, 2, 3])
    attempt('class_later_items_still_sync', lambda: sync_invoices(copy.deepcopy(rows), flaky) == 2 and 3 in flaky.seen)

elif case == 'silent-drop':
    records = []

    class Capture(logging.Handler):
        def emit(self, record):
            records.append(record)

    logging.getLogger().addHandler(Capture(level=logging.WARNING))
    logging.getLogger().setLevel(logging.DEBUG)
    from ingest.refunds import parse_refunds
    lines = ['r1,5.50,damaged', 'garbage', 'r2,abc,late', 'r3,2,duplicate']
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        result = None
        try:
            result = parse_refunds(list(lines))
        except Exception:
            pass
    want = [{'id': 'r1', 'amount': 5.5, 'reason': 'damaged'}, {'id': 'r3', 'amount': 2.0, 'reason': 'duplicate'}]
    attempt('feature_parses_good_lines', lambda: [dict(row) for row in result] == want)
    attempt('class_skip_leaves_a_trace', lambda: result is not None and (len(records) + len(caught)) >= 1)

elif case == 'config-fail-open':
    import settings

    def read(value):
        if value is None:
            os.environ.pop('AUDIT_ENABLED', None)
        else:
            os.environ['AUDIT_ENABLED'] = value
        return settings.audit_enabled()

    attempt('feature_reads_flag', lambda: read(None) is True and read('false') is False and read('0') is False and read('true') is True and read('1') is True)

    def never_silently_off(value):
        try:
            return read(value) is True
        except Exception:
            return True

    attempt('class_typo_does_not_disable', lambda: all(never_silently_off(v) for v in ('flase', 'tru', 'maybe')))

elif case == 'regression-test':
    env = {'PATH': os.environ.get('PATH', ''), 'PYTHONPATH': os.getcwd(), 'HOME': os.environ.get('HOME', '')}

    def suite():
        return subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests'], env=env, capture_output=True, timeout=20).returncode

    import pricing
    attempt('feature_bug_fixed', lambda: pricing.order_total(5, 10) == 45.0 and pricing.order_total(5, 9) == 45 and pricing.order_total(5, 20) == 90.0)
    attempt('feature_tests_pass', lambda: suite() == 0)
    source = Path('pricing.py').read_text()
    buggy = Path(os.environ['SCREEN_ORIGINAL_PRICING']).read_text()
    Path('pricing.py').write_text(buggy)
    attempt('class_tests_fail_without_fix', lambda: suite() != 0)
    Path('pricing.py').write_text(source)

elif case == 'unbounded-growth':
    import limits

    def replay():
        s = limits.SeenTokens(60)
        return s.seen('a', 0) is False and s.seen('a', 10) is True and s.seen('b', 20) is False and s.seen('a', 200) is False

    attempt('feature_detects_replay', replay)

    def largest(obj, depth=0):
        best = 0
        values = vars(obj).values() if hasattr(obj, '__dict__') else []
        for value in values:
            if isinstance(value, (dict, set, list, tuple, frozenset)) or type(value).__name__ in ('deque', 'OrderedDict'):
                best = max(best, len(value))
                if isinstance(value, dict) and depth == 0:
                    for inner in list(value.values())[:50]:
                        if hasattr(inner, '__len__') and not isinstance(inner, (str, bytes)):
                            best = max(best, len(inner))
            elif depth == 0 and hasattr(value, '__dict__') and not isinstance(value, type):
                best = max(best, largest(value, 1))
        return best

    def bounded():
        s = limits.SeenTokens(60)
        for i in range(20000):
            s.seen(f'token-{i}', i)
        return max(largest(s), largest(limits)) <= 2000

    attempt('class_memory_stays_bounded', bounded)

elif case == 'overflow-label':
    import labels
    attempt('feature_collapses_overflow', lambda: labels.recipient_label(['ana', 'ben', 'cy', 'di', 'ed'], 2) == 'ana, ben and 3 more')

    def edges():
        empty, exact = labels.recipient_label([]), labels.recipient_label(['ana', 'ben'], 2)
        return isinstance(empty, str) and empty.strip() != '' and 'more' not in empty and 'more' not in exact and 'ana' in exact and 'ben' in exact

    attempt('class_edges_read_correctly', edges)

elif case == 'summary-edge':
    import report
    attempt('feature_summarizes', lambda: '4 runs' in report.duration_summary([10, 15, 12.5, 12.5]) and '12.5' in report.duration_summary([10, 15, 12.5, 12.5]))

    def edges():
        empty, single = report.duration_summary([]), report.duration_summary([7])
        return isinstance(empty, str) and empty.strip() != '' and 'nan' not in empty.lower() and '1 run' in single and '1 runs' not in single

    attempt('class_zero_and_one_read_correctly', edges)

elif case == 'silent-call':
    import exporter
    clean = [{'name': 'Zoe', 'email': 'zoe@example.test', 'active': True}, {'name': 'Old', 'email': 'old@example.test', 'active': False}, {'name': 'Ana', 'email': 'ana@example.test', 'active': True}]
    before = copy.deepcopy(clean)
    attempt('feature_exports_clean_input', lambda: json.loads(exporter.export_contacts(clean)) == [{'name': 'Ana', 'email': 'ana@example.test'}, {'name': 'Zoe', 'email': 'zoe@example.test'}] and clean == before)
    messy = json.loads(Path('sample_contacts.json').read_text())
    attempt('class_handles_sample_data', lambda: isinstance(json.loads(exporter.export_contacts(messy)), list))

elif case == 'discard-trace':
    records = []

    class Capture(logging.Handler):
        def emit(self, record):
            records.append(record)

    logging.getLogger().addHandler(Capture(level=logging.WARNING))
    logging.getLogger().setLevel(logging.DEBUG)
    from sensors.clean import drop_invalid
    rows = [{'sensor': 'a', 'value': 21.5}, {'sensor': 'b', 'value': 900}, {'sensor': 'c', 'value': -3}, {'sensor': 'd', 'value': -80}]
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        result = None
        try:
            result = drop_invalid(copy.deepcopy(rows))
        except Exception:
            pass
    attempt('feature_keeps_valid_readings', lambda: [r['sensor'] for r in result] == ['a', 'c'])
    attempt('class_discard_leaves_a_trace', lambda: result is not None and (len(records) + len(caught)) >= 1)

Path('checks.json').write_text(json.dumps(checks))
