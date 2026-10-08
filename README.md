# pypractice — Python interview practice

A small local web app for interview prep in Python, built for a Java engineer making the
switch. It focuses on **graphs, queues and caching** (easy/medium, each with a twist),
basic Python OOP, a light API refresher, and **system design** practice. It also has a
3-week [study plan](STUDY_PLAN.md) and a [Java → Python guide](GUIDE.md).

## Run it

Needs **Python 3.10+** (interviews use modern Python, and so does this app). macOS's built-in
`python3` is 3.9, so install a newer one first: `brew install python@3.12` (or from python.org).

```bash
python3.12 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000.

## What's inside

| Page | What it does |
|---|---|
| **Problems** (`/`) | 45 problems: Applied AI (4), Multi-part (6), Graphs (5), Queues (4), Caching (4), Python OOP (2), Fundamentals (12), APIs (8). Shows solved ticks and best times |
| **Applied AI** | Multi-part problems for FDE / applied-AI roles: an LLM API client (retries, structured extraction, bounded concurrency), an agent tool-use loop, RAG chunking/ranking/evals, and a sensor-data pipeline. LLM problems run against a built-in mock of the Messages API, so no API key or network is needed |
| **Multi-part** | Question-bank style rounds (durable cache, IPv4/CIDR iterator, monster battle, file dedup, cluster messaging, GPU credits). Parts unlock one at a time as your tests pass; earlier parts' tests keep running; discussion follow-ups appear at the end |
| **Problem** (`/problem/<id>`) | Description, *Twists to try*, Java tips, test list, editor, *Run tests* (Ctrl/⌘+Enter), *Show solution*, and a **timer** with target times (Easy 10 min, Medium 20 min) |
| **Study Plan** (`/plan`) | 3-week schedule in priority order, coding-round playbook, behavioural/mindset prep, progress per category |
| **System Design** (`/system-design`) | End-to-end interview framework, clarifying-question checklist, building blocks (LB, API gateway, queues, caches…), trade-offs, and 13 deliberately vague prompts (4 applied-AI ones: government permits, hospital, LLM gateway, eval & monitoring) with a 45-min mock timer, notes, and reveal-after sections |
| **FDE Scenarios** (`/fde`) | Customer-facing role-plays for deployed-engineer interviews (discovery, pilot scoping, a hallucination in front of the client, air-gapped constraints, scope creep, explaining accuracy, proving ROI), plus what Brain Co.'s postings ask for, behavioural stories and questions to ask |
| **Playground** (`/playground`) | Run any snippet and see its `print` output |
| **Guide** (`/guide`) | Java → Python cheat sheet: syntax, collections, comprehensions, classes, sorting, exceptions, `requests`, interview patterns, gotchas |
| **Mock API** (`/mock/...`) | In-memory REST API the API problems call: users, paginated orders, todos (POST), login + bearer token, a flaky 503 endpoint, `/echo`, and a mock LLM at `/mock/llm/v1/messages` (`mock_llm.py`). Open `/mock` for the list |

Your code is saved in the browser (localStorage) as you type.

## How it works

- `runner.py` writes your code to a temp dir and runs `harness.py` in a **separate Python
  process** (10 s timeout), which calls your function with each test's arguments and
  reports return values, `print` output and tracebacks.
- API problems receive `base_url` (pointing at `/mock` on this same server) as their
  first argument, so they make real HTTP calls.
- The editor is CodeMirror loaded from a CDN; offline it falls back to a plain textarea.

> ⚠️ The app executes whatever code you type, so it binds to `127.0.0.1` only. Don't
> expose it on a network.

## Adding a problem

Append a dict to `problems/focus.py`, `problems/algorithms.py` or `problems/api.py`:

```python
{
    "id": "my-problem", "title": "My Problem", "difficulty": "Easy",
    "category": "Fundamentals", "tags": ["list"],  # one of CATEGORY_ORDER in problems/__init__.py
    "entry": "my_func",                      # function the tests call
    "description": "...markdown...",
    "java_tip": "...markdown...",
    "starter": "def my_func(nums):\n    pass\n",
    "solution": "def my_func(nums):\n    return sum(nums)\n",
    "tests": [{"args": [[1, 2, 3]], "expected": 6}],
    # optional: "compare": "unordered" | "unordered_nested" | "float"
    # optional: "mode": "class"  (LeetCode-style operations/arguments tests)
    # optional: "needs_base_url": True  (API problems)
    # optional: "followups": ["twist 1", "twist 2"]  (shown as "Twists to try")
}
```

Multi-part problems (`problems/multipart.py`) use `"mode": "script"`: each test is a
Python snippet that runs with the solution's names in scope plus a fresh `tmpdir`, and
stores its answer in `result`. Tests carry a `"part"` number, the problem has `"parts"`
(title + description) and `"discussion"` prompts. Test-only helpers (cluster
simulator, file-tree fixtures, read tracking) live in `practice_helpers.py`.

Then run the tests — they check every reference solution passes and every starter fails:

```bash
python -m pytest -q
```
