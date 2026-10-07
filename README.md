# pypractice — Python interview practice

A small local web app for interview prep in Python, built for a Java engineer making the
switch. It focuses on **graphs, queues and caching** (easy/medium, each with a twist),
basic Python OOP, a light API refresher, and **system design** practice. It also has a
3-week [study plan](STUDY_PLAN.md) and a [Java → Python guide](GUIDE.md).

## Run it

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000.

## What's inside

| Page | What it does |
|---|---|
| **Problems** (`/`) | 35 problems: Graphs (5), Queues (4), Caching (4), Python OOP (2), Fundamentals (12), APIs (8). Shows solved ticks and best times |
| **Problem** (`/problem/<id>`) | Description, *Twists to try*, Java tips, test list, editor, *Run tests* (Ctrl/⌘+Enter), *Show solution*, and a **timer** with target times (Easy 10 min, Medium 20 min) |
| **Study Plan** (`/plan`) | 3-week schedule in priority order, coding-round playbook, behavioural/mindset prep, progress per category |
| **System Design** (`/system-design`) | End-to-end interview framework, clarifying-question checklist, building blocks (LB, API gateway, queues, caches…), trade-offs, and 9 deliberately vague prompts with a 45-min mock timer, notes, and reveal-after sections |
| **Playground** (`/playground`) | Run any snippet and see its `print` output |
| **Guide** (`/guide`) | Java → Python cheat sheet: syntax, collections, comprehensions, classes, sorting, exceptions, `requests`, interview patterns, gotchas |
| **Mock API** (`/mock/...`) | In-memory REST API the API problems call: users, paginated orders, todos (POST), login + bearer token, a flaky 503 endpoint, and `/echo` |

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
    "category": "Algorithms", "tags": ["list"],
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

Then run the tests — they check every reference solution passes and every starter fails:

```bash
python -m pytest -q
```
