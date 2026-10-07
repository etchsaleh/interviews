"""Problems that make GET/POST calls with `requests` against the local mock API.

Every function receives `base_url` (e.g. "http://127.0.0.1:5000/mock") as its first argument.
"""
import mock_api

API_INTRO = """
> The mock API is served by this app. `base_url` is passed in for you — build URLs like
> `f"{base_url}/users"`. You can open any GET endpoint in your browser to see the data.
"""


def _todo_created(test, actual):
    title = test["args"][0]
    todo = mock_api.TODOS.get(actual) if isinstance(actual, int) else None
    return todo is not None and todo["title"] == title and todo["completed"] is False


PROBLEMS = [
    {
        "id": "api-active-users",
        "title": "GET: Active User Names",
        "difficulty": "Easy",
        "category": "APIs",
        "tags": ["GET", "JSON"],
        "entry": "active_user_names",
        "needs_base_url": True,
        "description": API_INTRO + """
`GET {base_url}/users` returns a JSON array of users:

```json
[{"id": 1, "name": "Ada", "email": "ada@example.com", "team": "platform", "active": true}, ...]
```

Return the **names of the active users**, sorted alphabetically.
""",
        "java_tip": """
- `requests.get(url)` replaces `HttpClient` + `HttpRequest.newBuilder()...` boilerplate.
- `resp.json()` parses the body straight into Python lists/dicts — no Jackson/POJOs. JSON `true` becomes `True`, `null` becomes `None`.
- Call `resp.raise_for_status()` to turn 4xx/5xx into an exception.
- Always pass a `timeout=` (seconds) in real code — requests has no default timeout.
""",
        "starter": """import requests


def active_user_names(base_url: str) -> list[str]:
    pass
""",
        "solution": """import requests


def active_user_names(base_url: str) -> list[str]:
    resp = requests.get(f"{base_url}/users", timeout=5)
    resp.raise_for_status()
    return sorted(user["name"] for user in resp.json() if user["active"])
""",
        "tests": [
            {"args": [], "expected": ["Ada", "Barbara", "Grace", "Guido"]},
        ],
    },
    {
        "id": "api-user-email",
        "title": "GET: Handle a 404",
        "difficulty": "Easy",
        "category": "APIs",
        "tags": ["GET", "status codes"],
        "entry": "get_user_email",
        "needs_base_url": True,
        "description": API_INTRO + """
`GET {base_url}/users/{user_id}` returns one user, or **404** with
`{"error": "user 42 not found"}` if it doesn't exist.

Return the user's email, or `None` if the user does not exist.
""",
        "java_tip": """
- `resp.status_code` is an `int` (`404`), and `resp.ok` is `True` for any status < 400.
- `None` is Python's `null`. Returning nothing at all from a function also returns `None`.
- f-strings interpolate: `f"{base_url}/users/{user_id}"`.
""",
        "starter": """import requests


def get_user_email(base_url: str, user_id: int) -> str | None:
    pass
""",
        "solution": """import requests


def get_user_email(base_url: str, user_id: int) -> str | None:
    resp = requests.get(f"{base_url}/users/{user_id}", timeout=5)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()["email"]
""",
        "tests": [
            {"args": [1], "expected": "ada@example.com"},
            {"args": [4], "expected": "guido@example.com"},
            {"args": [42], "expected": None},
        ],
    },
    {
        "id": "api-team-filter",
        "title": "GET: Query Parameters",
        "difficulty": "Easy",
        "category": "APIs",
        "tags": ["GET", "query params"],
        "entry": "team_member_ids",
        "needs_base_url": True,
        "description": API_INTRO + """
`GET {base_url}/users` supports query parameters:

- `team=<name>` — only users on that team
- `active=true|false` — only active / inactive users

Return the **ids** of the *active* members of `team`, in ascending order. Let the server
do the filtering — use query parameters rather than filtering in Python.
""",
        "java_tip": """
- Don't build query strings by hand. Pass a dict: `requests.get(url, params={"team": team, "active": "true"})` — requests URL-encodes it.
- `resp.url` shows the final URL that was requested — handy for debugging with `print`.
""",
        "starter": """import requests


def team_member_ids(base_url: str, team: str) -> list[int]:
    pass
""",
        "solution": """import requests


def team_member_ids(base_url: str, team: str) -> list[int]:
    resp = requests.get(f"{base_url}/users", params={"team": team, "active": "true"}, timeout=5)
    resp.raise_for_status()
    return sorted(user["id"] for user in resp.json())
""",
        "tests": [
            {"args": ["platform"], "expected": [1, 3, 6]},
            {"args": ["python"], "expected": [4]},
            {"args": ["java"], "expected": []},
            {"args": ["does-not-exist"], "expected": []},
        ],
    },
    {
        "id": "api-create-todo",
        "title": "POST: Create a Todo",
        "difficulty": "Easy",
        "category": "APIs",
        "tags": ["POST", "JSON body"],
        "entry": "create_todo",
        "needs_base_url": True,
        "validator": _todo_created,
        "description": API_INTRO + """
`POST {base_url}/todos` with a JSON body `{"title": "...", "completed": false}` creates a
todo and responds **201** with the created object:

```json
{"id": 7, "title": "Buy milk", "completed": false}
```

A missing/empty title gets a **400**.

Create a todo with the given `title` (not completed) and return the new todo's `id`.
The grader checks the todo really exists on the server.
""",
        "java_tip": """
- `requests.post(url, json={...})` serialises the dict *and* sets `Content-Type: application/json`.
- `data=` sends form-encoded data instead — a common mix-up.
- `resp.status_code == 201` for Created.
""",
        "starter": """import requests


def create_todo(base_url: str, title: str) -> int:
    pass
""",
        "solution": """import requests


def create_todo(base_url: str, title: str) -> int:
    resp = requests.post(f"{base_url}/todos", json={"title": title, "completed": False}, timeout=5)
    resp.raise_for_status()
    return resp.json()["id"]
""",
        "tests": [
            {"args": ["Learn Python"], "expected_label": "id of a todo titled 'Learn Python'"},
            {"args": ["Practice two_sum"], "expected_label": "id of a todo titled 'Practice two_sum'"},
        ],
    },
    {
        "id": "api-pagination",
        "title": "GET: Follow Pagination",
        "difficulty": "Medium",
        "category": "APIs",
        "tags": ["GET", "pagination", "loops"],
        "entry": "total_revenue",
        "needs_base_url": True,
        "compare": "float",
        "description": API_INTRO + """
`GET {base_url}/orders?page=N` returns one page of orders:

```json
{"data": [{"id": 100, "user_id": 1, "total": 25.5}, ...], "page": 1, "next_page": 2}
```

`next_page` is `null` on the last page. Return the **sum of `total`** across *all* orders,
rounded to 2 decimal places.
""",
        "java_tip": """
- Python has no `do { } while` — use `while True:` with `break`, or loop `while page is not None:`.
- Compare with `None` using `is` / `is not`, not `==`.
- `sum(o["total"] for o in orders)` and `round(x, 2)` are built-ins.
""",
        "starter": """import requests


def total_revenue(base_url: str) -> float:
    pass
""",
        "solution": """import requests


def total_revenue(base_url: str) -> float:
    total = 0.0
    page = 1
    while page is not None:
        resp = requests.get(f"{base_url}/orders", params={"page": page}, timeout=5)
        resp.raise_for_status()
        body = resp.json()
        total += sum(order["total"] for order in body["data"])
        page = body["next_page"]
    return round(total, 2)
""",
        "tests": [
            {"args": [], "expected": round(sum(o["total"] for o in mock_api.ORDERS), 2)},
        ],
    },
    {
        "id": "api-auth-profile",
        "title": "POST + GET: Bearer Token Auth",
        "difficulty": "Medium",
        "category": "APIs",
        "tags": ["POST", "headers", "auth"],
        "entry": "get_display_name",
        "needs_base_url": True,
        "description": API_INTRO + """
1. `POST {base_url}/login` with JSON `{"username": ..., "password": ...}` returns
   `{"token": "..."}` — or **401** for bad credentials.
2. `GET {base_url}/profile` with header `Authorization: Bearer <token>` returns
   `{"username": "ada", "display_name": "Ada", "plan": "pro"}`.

Log in and return the profile's `display_name`. Return `None` if login fails.
""",
        "java_tip": """
- Headers are just a dict: `requests.get(url, headers={"Authorization": f"Bearer {token}"})`.
- A `requests.Session()` keeps headers/cookies across calls: `s.headers.update({...})`. Use it in a `with` block (like try-with-resources).
""",
        "starter": """import requests


def get_display_name(base_url: str, username: str, password: str) -> str | None:
    pass
""",
        "solution": """import requests


def get_display_name(base_url: str, username: str, password: str) -> str | None:
    with requests.Session() as session:
        login = session.post(f"{base_url}/login", json={"username": username, "password": password}, timeout=5)
        if login.status_code == 401:
            return None
        login.raise_for_status()
        session.headers["Authorization"] = f"Bearer {login.json()['token']}"
        profile = session.get(f"{base_url}/profile", timeout=5)
        profile.raise_for_status()
        return profile.json()["display_name"]
""",
        "tests": [
            {"args": ["ada", "lovelace"], "expected": "Ada"},
            {"args": ["grace", "hopper"], "expected": "Grace"},
            {"args": ["ada", "wrong-password"], "expected": None},
        ],
    },
    {
        "id": "api-retry",
        "title": "GET: Retry on 503",
        "difficulty": "Medium",
        "category": "APIs",
        "tags": ["GET", "retries", "error handling"],
        "entry": "fetch_with_retry",
        "needs_base_url": True,
        "description": API_INTRO + """
`GET {base_url}/flaky?key=<key>` is unreliable: it answers **503** twice, then **200**
with `{"key": "...", "value": 21}`, then fails twice again, and so on.

Return the `value` from the first successful response. Retry on 503 up to **5 attempts**
in total (sleep a little between attempts — `time.sleep(0.05)` is plenty). If every
attempt fails, raise an exception.
""",
        "java_tip": """
- `for attempt in range(5):` + `return` on success is the idiomatic retry loop. A `for ... else:` block runs only if the loop *didn't* `break`/`return` early.
- Raise with `raise RuntimeError("...")` — no `throws` clause, all exceptions are unchecked.
- `try: ... except requests.RequestException as e:` catches network errors (connection refused, timeouts).
""",
        "starter": """import time

import requests


def fetch_with_retry(base_url: str, key: str) -> int:
    pass
""",
        "solution": """import time

import requests


def fetch_with_retry(base_url: str, key: str) -> int:
    for attempt in range(5):
        resp = requests.get(f"{base_url}/flaky", params={"key": key}, timeout=5)
        if resp.status_code == 503:
            time.sleep(0.05 * (attempt + 1))
            continue
        resp.raise_for_status()
        return resp.json()["value"]
    raise RuntimeError("flaky endpoint never succeeded")
""",
        "tests": [
            {"args": ["abc"], "expected": 21},
            {"args": ["python"], "expected": 42},
        ],
    },
    {
        "id": "api-spend-by-user",
        "title": "Combine Two Endpoints",
        "difficulty": "Medium",
        "category": "APIs",
        "tags": ["GET", "joins", "dict comprehension"],
        "entry": "spend_by_user",
        "needs_base_url": True,
        "description": API_INTRO + """
Using `GET {base_url}/users` and the paginated `GET {base_url}/orders?page=N`, return a
dict mapping each user's **name** to the total amount they have spent, rounded to 2
decimals. Users with no orders should map to `0`.

```python
{"Ada": 49.75, "Linus": 13.37, ...}
```
""",
        "java_tip": """
- Dict comprehension: `{u["id"]: u["name"] for u in users}`.
- `totals[key] = totals.get(key, 0) + amount` is the `merge(key, amount, Integer::sum)` equivalent. (Or use `defaultdict(float)`.)
- Small helper functions are cheap — split "fetch all orders" into its own function.
""",
        "starter": """import requests


def spend_by_user(base_url: str) -> dict[str, float]:
    pass
""",
        "solution": """import requests


def _all_orders(base_url: str) -> list[dict]:
    orders, page = [], 1
    while page is not None:
        body = requests.get(f"{base_url}/orders", params={"page": page}, timeout=5).json()
        orders.extend(body["data"])
        page = body["next_page"]
    return orders


def spend_by_user(base_url: str) -> dict[str, float]:
    users = requests.get(f"{base_url}/users", timeout=5).json()
    totals = {u["id"]: 0 for u in users}
    for order in _all_orders(base_url):
        totals[order["user_id"]] += order["total"]
    return {u["name"]: round(totals[u["id"]], 2) for u in users}
""",
        "tests": [
            {
                "args": [],
                "expected": {
                    u["name"]: round(sum(o["total"] for o in mock_api.ORDERS if o["user_id"] == u["id"]), 2)
                    for u in mock_api.USERS
                },
            },
        ],
    },
]
