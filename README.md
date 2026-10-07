# pypractice — Python interview practice

A small local web app for practising LeetCode-style problems **and** HTTP/API problems
(GET/POST with `requests`) in Python. Built for a Java engineer switching to Python, so
every problem has a **"Coming from Java"** tab, and there's a full
[Java → Python guide](GUIDE.md) (also served at `/guide`).

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
| **Problems** (`/`) | 14 algorithm problems + 8 API problems, with solved ticks saved in your browser |
| **Problem** (`/problem/<id>`) | Description, Java tips, test list, editor, *Run tests* (Ctrl/⌘+Enter), *Show solution* |
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

Append a dict to `problems/algorithms.py` or `problems/api.py`:

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
}
```

Then run the tests — they check every reference solution passes and every starter fails:

```bash
python -m pytest -q
```
