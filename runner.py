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


def run_solution(problem, code, base_url=None):
    """Run `code` against every test case of `problem` and return a JSON-able report."""
    tests = problem["tests"]
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
        try:
            proc = subprocess.run(
                [sys.executable, "-I", "harness.py"],
                input=json.dumps(spec),
                capture_output=True,
                text=True,
                cwd=workdir,
                timeout=TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": f"Time limit exceeded ({TIMEOUT_SECONDS}s). "
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
        cases.append({
            "input": test["args"],
            "expected": test.get("expected"),
            "expected_label": test.get("expected_label"),
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
