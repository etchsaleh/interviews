"""Runs inside a child process: loads the user's solution and executes test cases.

Reads a JSON spec on stdin and prints a single JSON line with the results.
Kept dependency-free on purpose so it runs with `python -I`.
"""
import contextlib
import copy
import io
import json
import os
import signal
import sys
import tempfile
import time
import traceback

MARKER = "__PRACTICE_RESULTS__"
DEFAULT_TEST_LIMIT_MS = 2000   # per test, unless the test sets its own limit
AFTER_TIMEOUT_LIMIT_MS = 500   # once something timed out, don't wait long on every remaining test


class TestTimeout(BaseException):
    """Raised by the per-test alarm. A BaseException, so `except Exception` in solutions can't swallow it."""


def _on_alarm(_signum, _frame):
    raise TestTimeout()


def generate(code):
    """Run a test's input generator (a snippet that sets `args`, and optionally `expected`)."""
    scope = {"__name__": "generator"}
    exec(compile(code, "<generator>", "exec"), scope)
    return scope["args"], scope.get("expected", _MISSING)


_MISSING = object()


def to_jsonable(value):
    """Convert common Python values (tuples, sets, objects) into JSON-friendly ones."""
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(v) for v in value]
    if isinstance(value, (set, frozenset)):
        items = [to_jsonable(v) for v in value]
        try:
            return sorted(items)
        except TypeError:
            return items
    return repr(value)


def short_traceback(exc):
    """Hide harness frames so the user only sees lines from their own code."""
    frames = [f for f in traceback.extract_tb(exc.__traceback__) if f.filename in ("solution.py", "<test>")]
    lines = ["Traceback (most recent call last):\n"]
    lines += traceback.format_list(frames)
    lines += traceback.format_exception_only(type(exc), exc)
    return "".join(lines)


def run_function(namespace, entry, args):
    fn = namespace.get(entry)
    if not callable(fn):
        raise NameError(f"Could not find a function named '{entry}' in your code.")
    return fn(*args)


def run_class(namespace, entry, args):
    """LeetCode-style design problems: args = [operations, arguments]."""
    cls = namespace.get(entry)
    if not isinstance(cls, type):
        raise NameError(f"Could not find a class named '{entry}' in your code.")
    operations, arguments = args
    obj = cls(*arguments[0])
    outputs = [None]
    for op, op_args in zip(operations[1:], arguments[1:]):
        outputs.append(getattr(obj, op)(*op_args))
    return outputs


def run_script(namespace, entry, args):
    """Multi-part problems: args = [python_snippet] (or [base_url, snippet]). The snippet sees
    the user's code plus a fresh `tmpdir` (and `base_url`), and stores its answer in `result`."""
    scope = dict(namespace)
    scope["tmpdir"] = tempfile.mkdtemp(prefix="t", dir=os.getcwd())
    if len(args) > 1:  # problems that talk to the mock server get its URL first
        scope["base_url"] = args[0]
    exec(compile(args[-1], "<test>", "exec"), scope)
    return scope.get("result")


def main():
    sys.path.insert(0, os.getcwd())  # lets tests import practice_helpers (we run with -I)
    spec = json.loads(sys.stdin.read())
    with open("solution.py", encoding="utf-8") as f:
        source = f.read()

    results = []
    namespace = {"__name__": "solution"}
    load_out = io.StringIO()
    try:
        code = compile(source, "solution.py", "exec")
        with contextlib.redirect_stdout(load_out):
            exec(code, namespace)
    except BaseException as exc:  # noqa: BLE001 - report anything, including SyntaxError
        detail = short_traceback(exc) if not isinstance(exc, SyntaxError) else "".join(
            traceback.format_exception_only(type(exc), exc)
        )
        print(MARKER + json.dumps({"load_error": detail, "stdout": load_out.getvalue()}))
        return

    runner = {"class": run_class, "script": run_script}.get(spec["mode"], run_function)
    can_alarm = hasattr(signal, "setitimer")
    if can_alarm:
        signal.signal(signal.SIGALRM, _on_alarm)
    limits = spec.get("limits") or [None] * len(spec["tests"])
    budget = spec.get("budget_s", 60)
    run_started = time.perf_counter()
    timed_out = False
    for args, limit_ms in zip(spec["tests"], limits):
        if time.perf_counter() - run_started > budget:
            results.append({"actual": None, "stdout": "", "ms": 0,
                            "error": "Not run: the run's time budget was used up by earlier slow tests."})
            continue
        out = io.StringIO()
        expected = _MISSING
        try:
            if isinstance(args, dict) and "__gen__" in args:
                args, expected = generate(args["__gen__"])
            else:
                args = copy.deepcopy(args)
        except BaseException as exc:  # noqa: BLE001 - a broken generator is the app's bug, but report it
            results.append({"actual": None, "stdout": "", "ms": 0, "error": "Test generator failed: " + repr(exc)})
            continue
        limit_ms = limit_ms or (AFTER_TIMEOUT_LIMIT_MS if timed_out else DEFAULT_TEST_LIMIT_MS)
        start = time.perf_counter()
        try:
            if can_alarm:
                signal.setitimer(signal.ITIMER_REAL, limit_ms / 1000)
            with contextlib.redirect_stdout(out):
                actual = runner(namespace, spec["entry"], args)
            if can_alarm:
                signal.setitimer(signal.ITIMER_REAL, 0)
            results.append({"actual": to_jsonable(actual), "error": None})
        except TestTimeout:
            timed_out = True
            results.append({"actual": None, "error": (
                f"Time limit exceeded: stopped after {limit_ms} ms. "
                "Look for an infinite loop, or an algorithm that's too slow for this input size (e.g. O(n²) where O(n) is needed).")})
        except BaseException as exc:  # noqa: BLE001
            if can_alarm:
                signal.setitimer(signal.ITIMER_REAL, 0)
            results.append({"actual": None, "error": short_traceback(exc)})
        results[-1]["stdout"] = out.getvalue()
        results[-1]["ms"] = round((time.perf_counter() - start) * 1000, 2)
        if expected is not _MISSING:
            results[-1]["expected"] = to_jsonable(expected)

    print(MARKER + json.dumps({"results": results, "stdout": load_out.getvalue()}))


if __name__ == "__main__":
    main()
