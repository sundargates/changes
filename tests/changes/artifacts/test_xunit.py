import uuid

from cStringIO import StringIO

from changes.artifacts.xunit import XunitHandler, _truncate_message, _TRUNCATION_HEADER
from changes.constants import Result
from changes.models import JobStep, TestResult
from changes.testutils import SAMPLE_XUNIT, SAMPLE_XUNIT_DOUBLE_CASES


def test_result_generation():
    jobstep = JobStep(
        id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        job_id=uuid.uuid4(),
    )

    fp = StringIO(SAMPLE_XUNIT)

    handler = XunitHandler(jobstep)
    results = handler.get_tests(fp)

    assert len(results) == 2

    r1 = results[0]
    assert type(r1) == TestResult
    assert r1.step == jobstep
    assert r1.package is None
    assert r1.name == 'tests.test_report'
    assert r1.duration == 0.0
    assert r1.result == Result.failed
    assert r1.message == """tests/test_report.py:1: in <module>
>   import mock
E   ImportError: No module named mock"""
    r2 = results[1]
    assert type(r2) == TestResult
    assert r2.step == jobstep
    assert r2.package is None
    assert r2.name == 'tests.test_report.ParseTestResultsTest.test_simple'
    assert r2.duration == 1.65796279907
    assert r2.result == Result.passed
    assert r2.message == ''
    assert r2.reruns == 1


def test_result_generation_when_one_test_has_two_cases():
    jobstep = JobStep(
        id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        job_id=uuid.uuid4(),
    )

    fp = StringIO(SAMPLE_XUNIT_DOUBLE_CASES)

    handler = XunitHandler(jobstep)
    results = handler.get_tests(fp)

    assert len(results) == 2

    r1 = results[0]
    assert type(r1) is TestResult
    assert r1.step == jobstep
    assert r1.package is None
    assert r1.name == 'test_simple.SampleTest.test_falsehood'
    assert r1.duration == 750.0
    assert r1.result == Result.failed
    assert r1.message == """\
test_simple.py:8: in test_falsehood
    assert False
E   AssertionError: assert False

test_simple.py:4: in tearDown
    1/0
E   ZeroDivisionError: integer division or modulo by zero"""
    assert r1.reruns == 3

    r2 = results[1]
    assert type(r2) is TestResult
    assert r2.step == jobstep
    assert r2.package is None
    assert r2.name == 'test_simple.SampleTest.test_truth'
    assert r2.duration == 1250.0
    assert r2.result == Result.failed
    assert r2.message == """\
test_simple.py:4: in tearDown
    1/0
E   ZeroDivisionError: integer division or modulo by zero"""
    assert r2.reruns == 0


def test_result_generation_when_a_quarantined_test_has_two_cases():
    jobstep = JobStep(
        id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        job_id=uuid.uuid4(),
    )

    fp = StringIO(SAMPLE_XUNIT_DOUBLE_CASES
                  .replace('<testcase c', '<testcase quarantined="1" c', 1)
                  .replace('<testcase c', '<testcase quarantined="1" c', 1))

    handler = XunitHandler(jobstep)
    results = handler.get_tests(fp)

    assert len(results) == 2

    r1 = results[0]
    assert type(r1) is TestResult
    assert r1.step == jobstep
    assert r1.package is None
    assert r1.name == 'test_simple.SampleTest.test_falsehood'
    assert r1.duration == 750.0
    assert r1.result == Result.quarantined_failed
    assert r1.message == """\
test_simple.py:8: in test_falsehood
    assert False
E   AssertionError: assert False

test_simple.py:4: in tearDown
    1/0
E   ZeroDivisionError: integer division or modulo by zero"""
    assert r1.reruns == 3

    r2 = results[1]
    assert type(r2) is TestResult
    assert r2.step == jobstep
    assert r2.package is None
    assert r2.name == 'test_simple.SampleTest.test_truth'
    assert r2.duration == 1250.0
    assert r2.result == Result.failed
    assert r2.message == """\
test_simple.py:4: in tearDown
    1/0
E   ZeroDivisionError: integer division or modulo by zero"""
    assert r2.reruns == 0


def test_truncate_message():
    suffix = "But it'll be truncated anyway."
    original = ("This isn't really that big.\n" * 1024) + suffix
    limit = len(suffix) + 3
    newmsg = _truncate_message(original, limit=len(suffix) + 3)
    assert len(newmsg) < limit + len(_TRUNCATION_HEADER)

    short = "Hello"
    assert short == _truncate_message(short, limit=1024)

    single_long_line = "Text " * 1024
    assert _truncate_message(single_long_line, limit=1024) == _TRUNCATION_HEADER
