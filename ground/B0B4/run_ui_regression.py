"""Run native offline tests with original fixtures and temporary output only.

    python -B ground/B0B4/run_ui_regression.py

No fixture adaptation or protocol changes. Real serial/device enumeration is
blocked; the existing transport tests can install their own in-memory mocks.
All test data, including legacy test_output, is cleaned on exit. A JSON report
is retained separately in the OS temporary directory.
"""
from contextlib import ExitStack
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ground_server as gs


def run():
    log, counts, redirects = io.StringIO(), {}, []
    started = time.monotonic()
    original_divide = Path.__truediv__
    with tempfile.TemporaryDirectory(prefix='gmfly-ui-regression-work-') as work:
        work_path = Path(work)
        output = work_path/'test_output'

        def divide(path, part):
            caller = sys._getframe(1).f_globals.get('__name__')
            if path == HERE and part == 'test_output' and caller in ('test_system', 'test_mtf'):
                redirects.append(caller)
                return output
            return original_divide(path, part)

        with ExitStack() as stack:
            # Only the two legacy output-directory expressions are redirected.
            # Every original fixture and production-file read is unchanged.
            stack.enter_context(patch.object(Path, '__truediv__', divide))
            stack.enter_context(patch.object(tempfile, 'tempdir', str(work_path)))
            stack.enter_context(patch.object(gs.serial, 'Serial', side_effect=AssertionError('Real serial forbidden')))
            stack.enter_context(patch.object(gs.serial.tools.list_ports, 'comports', side_effect=AssertionError('Real enumeration forbidden')))
            stack.enter_context(patch.object(gs, 'ports', side_effect=AssertionError('Real enumeration forbidden')))
            suite = unittest.TestSuite()
            for path in sorted(HERE.glob('test_*.py')):
                tests = unittest.defaultTestLoader.loadTestsFromName(path.stem)
                counts[path.stem] = tests.countTestCases()
                suite.addTests(tests)
            result = unittest.TextTestRunner(stream=log, verbosity=1).run(suite)

    report = dict(mode='native_full_offline_regression', passed=result.wasSuccessful(),
                  tests=result.testsRun, failures=len(result.failures), errors=len(result.errors),
                  skipped=len(result.skipped), modules=counts,
                  elapsed_s=round(time.monotonic()-started, 3), fixture_adaptation=False,
                  no_real_serial=True, no_real_device_enumeration=True,
                  redirected_test_output_modules=redirects,
                  test_data_directory=str(work_path), test_data_cleaned=not work_path.exists(),
                  output=log.getvalue())
    fd, report_path = tempfile.mkstemp(prefix='gmfly-ui-regression-report-', suffix='.json')
    with os.fdopen(fd, 'w', encoding='utf8') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({key: report[key] for key in ('mode', 'passed', 'tests', 'failures', 'errors',
                                                 'fixture_adaptation', 'test_data_cleaned')} |
                     dict(report=report_path), ensure_ascii=False))
    if not result.wasSuccessful():
        print(log.getvalue(), file=sys.stderr)
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run())
