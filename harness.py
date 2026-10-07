"""Runs inside a child process: loads the user's solution and executes test cases.

Reads a JSON spec on stdin and prints a single JSON line with the results.
Kept dependency-free on purpose so it runs with `python -I`.
"""
import contextlib
import copy
import io
import json
import sys
import time
import traceback

MARKER = "__PRACTICE_RESULTS__"


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
    frames = [f for f in traceback.extract_tb(exc.__traceback__) if f.filename == "solution.py"]
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


def main():
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

    runner = run_class if spec["mode"] == "class" else run_function
    for args in spec["tests"]:
        out = io.StringIO()
        start = time.perf_counter()
        try:
            with contextlib.redirect_stdout(out):
                actual = runner(namespace, spec["entry"], copy.deepcopy(args))
            results.append({"actual": to_jsonable(actual), "error": None})
        except BaseException as exc:  # noqa: BLE001
            results.append({"actual": None, "error": short_traceback(exc)})
        results[-1]["stdout"] = out.getvalue()
        results[-1]["ms"] = round((time.perf_counter() - start) * 1000, 2)

    print(MARKER + json.dumps({"results": results, "stdout": load_out.getvalue()}))


if __name__ == "__main__":
    main()
