import pytest
import requests

import re
from pathlib import Path

from problems import ALL_PROBLEMS, BY_ID
from runner import run_solution


@pytest.mark.parametrize("problem", ALL_PROBLEMS, ids=lambda p: p["id"])
def test_reference_solution_passes(problem, live_server):
    report = run_solution(problem, problem["solution"], base_url=f"{live_server}/mock")
    assert report["ok"], report.get("error")
    failed = [c for c in report["cases"] if not c["passed"]]
    assert not failed, failed


@pytest.mark.parametrize("problem", ALL_PROBLEMS, ids=lambda p: p["id"])
def test_starter_code_does_not_pass(problem, live_server):
    report = run_solution(problem, problem["starter"], base_url=f"{live_server}/mock")
    assert report["ok"], report.get("error")
    assert report["passed"] < report["total"]


def test_syntax_error_is_reported():
    problem = BY_ID["two-sum"]
    report = run_solution(problem, "def two_sum(nums, target)\n    return []\n")
    assert not report["ok"]
    assert "SyntaxError" in report["error"]


def test_runtime_error_shows_user_traceback():
    problem = BY_ID["two-sum"]
    report = run_solution(problem, "def two_sum(nums, target):\n    return nums[99]\n")
    assert report["ok"]
    assert report["passed"] == 0
    assert "IndexError" in report["cases"][0]["error"]
    assert "harness.py" not in report["cases"][0]["error"]


def test_print_output_is_captured():
    problem = BY_ID["two-sum"]
    code = "def two_sum(nums, target):\n    print('debug', target)\n    return [0, 1]\n"
    report = run_solution(problem, code)
    assert report["cases"][0]["stdout"] == "debug 9\n"
    assert report["cases"][0]["passed"]


def test_infinite_loop_times_out(monkeypatch):
    import runner
    monkeypatch.setattr(runner, "TIMEOUT_SECONDS", 1)
    report = runner.run_solution(BY_ID["two-sum"], "def two_sum(nums, target):\n    while True: pass\n")
    assert not report["ok"]
    assert "Time limit" in report["error"]


def test_pages_render(client):
    for path in ["/", "/guide", "/plan", "/system-design", "/playground", "/problem/two-sum", "/problem/api-retry",
                 "/problem/ttl-cache"]:
        resp = client.get(path)
        assert resp.status_code == 200, path
    assert client.get("/problem/nope").status_code == 404
    # The reference solution must never leak into the page itself.
    page = client.get("/problem/two-sum").get_data(as_text=True)
    assert "seen[num] = i" not in page


def test_run_endpoint(live_server):
    resp = requests.post(f"{live_server}/api/run", json={"id": "api-user-email",
                         "code": "import requests\ndef get_user_email(base_url, user_id):\n"
                                 "    r = requests.get(f'{base_url}/users/{user_id}')\n"
                                 "    return r.json()['email'] if r.ok else None\n"})
    body = resp.json()
    assert body["passed"] == body["total"] == 3


def test_playground(live_server):
    resp = requests.post(f"{live_server}/api/run", json={"id": "playground", "code": "print(7 // 2)"})
    assert resp.json()["stdout"] == "3\n"


def test_study_plan_links_point_to_real_problems():
    plan = (Path(__file__).resolve().parent.parent / "STUDY_PLAN.md").read_text()
    linked = set(re.findall(r"\(/problem/([\w-]+)\)", plan))
    assert linked, "plan should link to problems"
    assert linked <= set(BY_ID), linked - set(BY_ID)


def test_uncached_price_lookups_fail(live_server):
    naive = (
        "import requests\n"
        "def get_prices(base_url, skus, client_id):\n"
        "    return [requests.get(f'{base_url}/price/{s}', params={'client': client_id}).json()['price'] for s in skus]\n"
    )
    report = run_solution(BY_ID["cached-prices"], naive, base_url=f"{live_server}/mock")
    passed = [c["passed"] for c in report["cases"]]
    assert passed == [False, False, True]  # right prices but too many calls; empty list is trivially fine


def test_mock_index_lists_endpoints(client):
    for path in ["/mock", "/mock/"]:
        body = client.get(path).get_json()
        assert any(e["path"] == "/users" for e in body["endpoints"]), path
