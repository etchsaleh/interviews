"""Executes a user's solution in a separate Python process and grades the results."""
import json
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

from harness import MARKER

HARNESS = Path(__file__).with_name("harness.py")
HELPERS = Path(__file__).with_name("practice_helpers.py")
TIMEOUT_SECONDS = 10
RUN_ID = "<run-id>"  # test arg placeholder, replaced with a fresh uuid on every run


def _normalize(value, compare):
    if compare == "unordered":
        return sorted(value, key=json.dumps) if isinstance(value, list) else value
    if compare == "unordered_nested":
        if not isinstance(value, list):
            return value
        inner = [sorted(v, key=json.dumps) if isinstance(v, list) else v for v in value]
        return sorted(inner, key=json.dumps)
    return value


def is_correct(problem, args, actual, call_args=None):
    if "validator" in problem:
        try:
            return bool(problem["validator"](args, actual, call_args))
        except Exception:  # a malformed answer shouldn't crash grading
            return False
    compare = problem.get("compare", "exact")
    expected = args["expected"]
    if compare == "float":
        return isinstance(actual, (int, float)) and abs(actual - expected) < 1e-6
    return _normalize(actual, compare) == _normalize(expected, compare)


def run_solution(problem, code, base_url=None, upto=None):
    """Run `code` against the test cases of `problem` and return a JSON-able report.

    For multi-part problems, `upto` limits the run to parts 1..upto (tests are cumulative).
    """
    tests = [t for t in problem["tests"] if upto is None or t.get("part", 1) <= upto]
    timeout = problem.get("timeout", TIMEOUT_SECONDS)
    call_args = []
    for t in tests:
        args = [str(uuid.uuid4()) if a == RUN_ID else a for a in t["args"]]
        if problem.get("needs_base_url"):
            args = [base_url] + args
        call_args.append(args)

    spec = {"mode": problem.get("mode", "function"), "entry": problem["entry"], "tests": call_args}
    workdir = Path(tempfile.mkdtemp(prefix="practice_"))
    try:
        (workdir / "solution.py").write_text(code, encoding="utf-8")
        shutil.copy(HARNESS, workdir / "harness.py")
        shutil.copy(HELPERS, workdir / "practice_helpers.py")
        try:
            proc = subprocess.run(
                [sys.executable, "-I", "harness.py"],
                input=json.dumps(spec),
                capture_output=True,
                text=True,
                cwd=workdir,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": f"Time limit exceeded ({timeout}s). "
                                          "Look for an infinite loop or a very slow algorithm."}
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    payload = None
    stdout_lines = []
    for line in proc.stdout.splitlines():
        if line.startswith(MARKER):
            payload = json.loads(line[len(MARKER):])
        else:
            stdout_lines.append(line)
    if payload is None:
        return {"ok": False, "error": (proc.stderr or "The runner exited without results.").strip()}
    if "load_error" in payload:
        return {"ok": False, "error": payload["load_error"], "stdout": payload["stdout"]}

    cases = []
    for test, args, res in zip(tests, call_args, payload["results"]):
        passed = res["error"] is None and is_correct(problem, test, res["actual"], args)
        limit = test.get("time_limit_ms")
        if passed and limit and res["ms"] > limit:
            passed = False
            res["error"] = f"Too slow: took {res['ms']:.0f} ms, the limit for this test is {limit} ms."
        cases.append({
            "part": test.get("part", 1),
            "time_limit_ms": limit,
            "input": test["args"],
            "expected": test.get("expected"),
            "expected_label": test.get("expected_label"),
            "label": test.get("label"),
            "actual": res["actual"],
            "error": res["error"],
            "stdout": res["stdout"],
            "ms": res["ms"],
            "passed": passed,
        })
    return {
        "ok": True,
        "passed": sum(c["passed"] for c in cases),
        "total": len(cases),
        "cases": cases,
        "stdout": payload["stdout"],
        "stderr": proc.stderr.strip(),
    }
