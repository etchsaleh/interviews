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
    for path in ["/", "/guide", "/plan", "/system-design", "/fde", "/playground", "/problem/two-sum",
                 "/problem/api-retry", "/problem/ttl-cache", "/problem/ai-agent-loop"]:
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


# ----------------------------------------------------------------- multi-part
MULTIPART = [p for p in ALL_PROBLEMS if p.get("parts")]


@pytest.mark.parametrize("problem", MULTIPART, ids=lambda p: p["id"])
def test_multipart_tests_are_numbered_by_part(problem):
    parts = {t["part"] for t in problem["tests"]}
    assert parts == set(range(1, len(problem["parts"]) + 1)), "every part needs tests"


def test_upto_runs_only_unlocked_parts():
    problem = BY_ID["mp-ip-iterator"]
    report = run_solution(problem, problem["solution"], upto=2)
    assert {c["part"] for c in report["cases"]} == {1, 2}
    assert report["passed"] == report["total"]


def test_counting_replies_by_number_fails_only_part_3():
    counting = """
class Node:
    def __init__(self, node_id, children, parent):
        self.node_id, self.children, self.parent = node_id, children, parent
        self.total = self.waiting = 0

    def sendAsyncMessage(self, node_id, message):
        pass

    def receiveMessage(self, fromNodeId, message):
        if message in ("count", "COUNT"):
            if not self.children:
                return self._done("1")
            self.total, self.waiting = 1, len(self.children)
            for c in self.children:
                self.sendAsyncMessage(c, "COUNT")
        else:
            self.total += int(message)
            self.waiting -= 1
            if self.waiting == 0:
                self._done(str(self.total))

    def _done(self, answer):
        if self.parent is None:
            print(answer)
        else:
            self.sendAsyncMessage(self.parent, answer)
"""
    report = run_solution(BY_ID["mp-cluster-messages"], counting)
    failed_parts = {c["part"] for c in report["cases"] if not c["passed"]}
    assert all(c["passed"] for c in report["cases"] if c["part"] == 1)
    assert 3 in failed_parts


def test_gpu_reference_matches_brute_force():
    import random

    ns = {}
    exec(BY_ID["mp-gpu-credits"]["solution"], ns)

    class Naive:
        def __init__(self):
            self.events = []

        def add_credit(self, cid, amount, t, exp):
            self.events.append((t, "add", amount, t + exp))

        def subtract(self, amount, t):
            self.events.append((t, "sub", amount, None))

        def get_balance(self, t):
            grants, debt = [], 0
            for ts, kind, amount, end in sorted(e for e in self.events if e[0] <= t):
                if kind == "add":
                    paid = min(debt, amount)
                    debt -= paid
                    grants.append([ts, end, amount - paid])
                else:
                    for g in sorted((g for g in grants if g[0] <= ts <= g[1]), key=lambda g: g[1]):
                        used = min(g[2], amount)
                        g[2] -= used
                        amount -= used
                    debt += amount
            active = [g for g in grants if g[0] <= t <= g[1]]
            balance = sum(g[2] for g in active) - debt
            return None if not active or balance < 0 else balance

    rng = random.Random(7)
    for _ in range(500):
        ref, naive = ns["GPUCredit"](), Naive()
        for t in rng.sample(range(60), rng.randint(1, 10)):
            if rng.random() < 0.5:
                args = (f"g{t}", rng.randint(0, 10), t, rng.randint(0, 25))
                ref.add_credit(*args)
                naive.add_credit(*args)
            else:
                args = (rng.randint(0, 12), t)
                ref.subtract(*args)
                naive.subtract(*args)
            q = rng.randint(0, 70)
            assert ref.get_balance(q) == naive.get_balance(q)
        for q in range(75):
            assert ref.get_balance(q) == naive.get_balance(q)


# ------------------------------------------------------------------ mock LLM
def _llm(live_server, body, headers=None):
    h = {"x-api-key": "sk-test", "anthropic-version": "2023-06-01"}
    h.update(headers or {})
    return requests.post(f"{live_server}/mock/llm/v1/messages", json=body, headers=h)


def test_mock_llm_validates_like_the_real_api(live_server):
    ok = {"model": "m", "max_tokens": 10, "messages": [{"role": "user", "content": "hi"}]}
    assert _llm(live_server, ok).status_code == 200
    assert _llm(live_server, ok, {"x-api-key": ""}).status_code == 401
    bad_role = dict(ok, messages=[{"role": "system", "content": "x"}, {"role": "user", "content": "hi"}])
    assert "top-level" in _llm(live_server, bad_role).json()["error"]["message"]
    no_alternation = dict(ok, messages=[{"role": "user", "content": "a"}, {"role": "user", "content": "b"}])
    assert _llm(live_server, no_alternation).status_code == 400
    orphan_result = dict(ok, messages=[{"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": "toolu_x", "content": "r"}]}])
    assert _llm(live_server, orphan_result).status_code == 400


def test_mock_llm_response_shape(live_server):
    body = _llm(live_server, {"model": "m", "max_tokens": 10, "system": "S",
                              "messages": [{"role": "user", "content": "hi"}]}).json()
    assert body["type"] == "message" and body["stop_reason"] == "end_turn"
    assert "".join(b["text"] for b in body["content"] if b["type"] == "text") == "(S) Echo: hi"
    assert set(body["usage"]) == {"input_tokens", "output_tokens"}


def test_study_plan_and_fde_links_resolve(client):
    import re
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent
    for doc in ("STUDY_PLAN.md", "FDE.md"):
        for pid in re.findall(r"\(/problem/([\w-]+)\)", (root / doc).read_text()):
            assert pid in BY_ID, (doc, pid)
