"""Product engineering: build a small backend product end to end (multi-part).

Tests drive the candidate's Flask app through `app.test_client()`; the AI part calls the
mock LLM over HTTP, so `base_url` is passed in like the Applied AI problems.
"""
from problems.multipart import T

PRELUDE = """
            import os
            db_path = os.path.join(tmpdir, "permits.db")
            app = create_app(db_path)
            client = app.test_client()
            def new(**changes):
                body = {"applicant": "Layla Haddad", "address": "12 Palm St", "type": "solar", "description": "Rooftop panels"}
                body.update(changes)
                return client.post("/applications", json=body)
            def move(app_id, to, actor="reviewer-1", **extra):
                return client.post(f"/applications/{app_id}/transitions", json={"to": to, "actor": actor, **extra})
"""

AI_PRELUDE = """
            import os
            from practice_helpers import new_key, llm_stats
            key = new_key()
            db_path = os.path.join(tmpdir, "permits.db")
            app = create_app(db_path, llm_base_url=base_url, api_key=key)
            client = app.test_client()
            def new(**changes):
                body = {"applicant": "Layla Haddad", "address": "12 Palm St", "type": "solar", "description": "Rooftop panels"}
                body.update(changes)
                return client.post("/applications", json=body)
            def move(app_id, to, actor="reviewer-1", **extra):
                return client.post(f"/applications/{app_id}/transitions", json={"to": to, "actor": actor, **extra})
"""

SEED = """
            new(applicant="Layla Haddad", address="12 Palm St", type="solar")
            new(applicant="Omar Khan", address="7 Harbour Rd", type="commercial")
            new(applicant="Sara Ali", address="3 palm grove", type="residential")
            new(applicant="Ben Cole", address="99 Dune Ave", type="solar")
            new(applicant="Mia Park", address="1 Creek Ln", type="residential")
            move(2, "under_review"); move(4, "under_review"); move(4, "approved")
"""


def app_json(i, applicant="Layla Haddad", address="12 Palm St", type_="solar", description="Rooftop panels",
             status="submitted"):
    return {"id": i, "applicant": applicant, "address": address, "type": type_, "description": description,
            "status": status}


SOLUTION = '''import sqlite3

import requests
from flask import Flask, g, jsonify, request

TYPES = {"residential", "commercial", "solar"}
TRANSITIONS = {
    "submitted": {"under_review"},
    "under_review": {"approved", "rejected", "needs_info"},
    "needs_info": {"under_review"},
    "approved": set(),
    "rejected": set(),
}
FIELDS = "id, applicant, address, type, description, status"
SCHEMA = """
CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    applicant TEXT NOT NULL,
    address TEXT NOT NULL,
    type TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER NOT NULL REFERENCES applications(id),
    from_status TEXT,
    to_status TEXT NOT NULL,
    actor TEXT NOT NULL,
    note TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS summaries (
    application_id INTEGER NOT NULL,
    status TEXT NOT NULL,
    summary TEXT NOT NULL,
    PRIMARY KEY (application_id, status)
);
"""


def create_app(db_path: str, llm_base_url: str | None = None, api_key: str | None = None) -> Flask:
    app = Flask(__name__)
    with sqlite3.connect(db_path) as conn:
        conn.executescript(SCHEMA)

    def db() -> sqlite3.Connection:
        if "db" not in g:
            g.db = sqlite3.connect(db_path)
            g.db.row_factory = sqlite3.Row
        return g.db

    @app.teardown_appcontext
    def close_db(_exc):
        conn = g.pop("db", None)
        if conn is not None:
            conn.close()

    def error(status: int, message: str, **extra):
        return jsonify({"error": message, **extra}), status

    def load(app_id: int) -> dict | None:
        row = db().execute(f"SELECT {FIELDS} FROM applications WHERE id = ?", (app_id,)).fetchone()
        return dict(row) if row else None

    @app.post("/applications")
    def create_application():
        body = request.get_json(silent=True)
        if not isinstance(body, dict):
            return error(400, "body must be a JSON object", fields=[])
        bad = [f for f in ("applicant", "address") if not isinstance(body.get(f), str) or not body[f].strip()]
        if not isinstance(body.get("type"), str) or body["type"] not in TYPES:
            bad.append("type")
        if not isinstance(body.get("description", ""), str):
            bad.append("description")
        if bad:
            return error(400, "invalid fields", fields=sorted(bad))
        conn = db()
        cur = conn.execute(
            "INSERT INTO applications (applicant, address, type, description, status) VALUES (?, ?, ?, ?, 'submitted')",
            (body["applicant"], body["address"], body["type"], body.get("description", "")),
        )
        conn.execute(
            "INSERT INTO history (application_id, from_status, to_status, actor) VALUES (?, NULL, 'submitted', ?)",
            (cur.lastrowid, body["applicant"]),
        )
        conn.commit()
        return jsonify(load(cur.lastrowid)), 201

    @app.get("/applications/<int:app_id>")
    def get_application(app_id):
        application = load(app_id)
        return jsonify(application) if application else error(404, "application not found")

    @app.post("/applications/<int:app_id>/transitions")
    def transition(app_id):
        application = load(app_id)
        if not application:
            return error(404, "application not found")
        body = request.get_json(silent=True) or {}
        target, actor, note = body.get("to"), body.get("actor"), body.get("note", "")
        if target not in TRANSITIONS or not isinstance(actor, str) or not actor or not isinstance(note, str):
            return error(400, "need a known status in 'to' and a non-empty 'actor'")
        if target not in TRANSITIONS[application["status"]]:
            return error(409, f"can't move from {application['status']} to {target}")
        conn = db()
        conn.execute("UPDATE applications SET status = ? WHERE id = ?", (target, app_id))
        conn.execute(
            "INSERT INTO history (application_id, from_status, to_status, actor, note) VALUES (?, ?, ?, ?, ?)",
            (app_id, application["status"], target, actor, note),
        )
        conn.commit()
        return jsonify(load(app_id))

    @app.get("/applications/<int:app_id>/history")
    def history(app_id):
        if not load(app_id):
            return error(404, "application not found")
        rows = db().execute(
            'SELECT from_status AS "from", to_status AS "to", actor, note FROM history '
            "WHERE application_id = ? ORDER BY id",
            (app_id,),
        ).fetchall()
        return jsonify([dict(r) for r in rows])

    @app.get("/applications")
    def list_applications():
        try:
            limit = int(request.args.get("limit", 20))
            offset = int(request.args.get("offset", 0))
        except ValueError:
            return error(400, "limit and offset must be integers")
        if not 1 <= limit <= 100 or offset < 0:
            return error(400, "limit must be 1-100 and offset >= 0")
        where, params = [], []
        for field in ("status", "type"):
            if request.args.get(field):
                where.append(f"{field} = ?")
                params.append(request.args[field])
        if request.args.get("q"):
            where.append("(LOWER(applicant) LIKE ? OR LOWER(address) LIKE ?)")
            params += [f"%{request.args['q'].lower()}%"] * 2
        clause = f"WHERE {' AND '.join(where)}" if where else ""
        total = db().execute(f"SELECT COUNT(*) FROM applications {clause}", params).fetchone()[0]
        rows = db().execute(
            f"SELECT {FIELDS} FROM applications {clause} ORDER BY id LIMIT ? OFFSET ?", params + [limit, offset]
        ).fetchall()
        return jsonify({"items": [dict(r) for r in rows], "total": total})

    @app.get("/applications/<int:app_id>/summary")
    def summary(app_id):
        application = load(app_id)
        if not application:
            return error(404, "application not found")
        cached = db().execute(
            "SELECT summary FROM summaries WHERE application_id = ? AND status = ?", (app_id, application["status"])
        ).fetchone()
        if cached:
            return jsonify({"summary": cached["summary"]})
        prompt = (
            "Summarise this building-permit application for a reviewer in two sentences.\\n"
            f"Applicant: {application['applicant']}\\nAddress: {application['address']}\\n"
            f"Type: {application['type']}\\nStatus: {application['status']}\\n"
            f"Description: {application['description']}"
        )
        try:
            resp = requests.post(
                f"{llm_base_url}/llm/v1/messages",
                headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"},
                json={"model": "claude-opus-5-5", "max_tokens": 1024,
                      "messages": [{"role": "user", "content": prompt}]},
                timeout=30,
            )
        except requests.RequestException:
            return error(503, "summary service unavailable")
        if resp.status_code != 200:
            return error(503, "summary service unavailable")
        text = "".join(b["text"] for b in resp.json()["content"] if b["type"] == "text")
        conn = db()
        conn.execute("INSERT INTO summaries (application_id, status, summary) VALUES (?, ?, ?)",
                     (app_id, application["status"], text))
        conn.commit()
        return jsonify({"summary": text})

    return app
'''

PERMITS_API = {
    "id": "product-permit-tracker",
    "title": "Build a Permit Tracker (API + AI feature)",
    "difficulty": "Medium",
    "category": "Product Engineering",
    "tags": ["REST API", "Flask", "SQLite", "workflow", "LLM feature"],
    "entry": "create_app",
    "mode": "script",
    "needs_base_url": True,
    "target_minutes": 60,
    "timeout": 25,
    "description": """
A municipality wants to replace its spreadsheet of building-permit applications. You
agreed the spec with their permit office last week. Now build the backend, in stages,
the way you'd ship it to them.

```python
def create_app(db_path: str) -> Flask: ...
```

Return a Flask app. `db_path` is a file path the app may use for storage. The tests create
a **fresh app for every test**, so keep state inside the app you create, not in
module-level globals. All request and response bodies are JSON. Errors return a JSON
object with an `"error"` message.
""",
    "parts": [
        {
            "title": "Create and fetch",
            "description": """
| Endpoint | Behaviour |
|---|---|
| `POST /applications` | Body: `applicant`, `address` (non-empty strings), `type` (`residential`, `commercial` or `solar`), optional `description` (string, default `""`). **201** with the new application. |
| `GET /applications/<id>` | **200** with the application, or **404**. |

An application is exactly
`{"id", "applicant", "address", "type", "description", "status"}`. Ids start at 1 and
increase; new applications have status `"submitted"`.

Invalid input returns **400** with `"fields"`: the sorted list of invalid field names
(`[]` if the body isn't a JSON object).
""",
        },
        {
            "title": "Review workflow",
            "description": """
Reviewers move applications through a workflow, and the office needs an audit trail.

| Endpoint | Behaviour |
|---|---|
| `POST /applications/<id>/transitions` | Body: `to` (new status), `actor` (non-empty string), optional `note` (string). **200** with the updated application. |
| `GET /applications/<id>/history` | **200** with every status change, oldest first: `{"from", "to", "actor", "note"}`. |

```
submitted → under_review → approved | rejected | needs_info
needs_info → under_review
```

- Creating an application is the first history entry: `from` is `null`, `to` is
  `"submitted"`, the `actor` is the applicant, and `note` is `""`.
- Unknown status or missing actor → **400**. A move the workflow doesn't allow → **409**.
  Unknown application → **404**.
""",
        },
        {
            "title": "Search and pagination",
            "description": """
The office has thousands of applications.

`GET /applications` returns `{"items": [...], "total": N}`, ordered by id.

| Query param | Meaning |
|---|---|
| `status`, `type` | exact match filters |
| `q` | case-insensitive text that must appear in the applicant **or** the address |
| `limit` | page size, default 20, must be 1–100 |
| `offset` | items to skip, default 0, must be ≥ 0 |

`total` counts every match, ignoring `limit` and `offset`. Invalid `limit` or `offset`
→ **400**.
""",
        },
        {
            "title": "Persistence",
            "description": """
The app gets restarted during deployments, and runs as several processes.

- Everything (applications, statuses, history) must survive restarts: a **new app created
  with the same `db_path`** sees all of it, and new ids continue from where they left off.
- Two apps open on the same `db_path` at the same time see each other's changes.

Use SQLite (`import sqlite3`, built into Python).
""",
        },
        {
            "title": "AI summary",
            "description": """
Reviewers want a short AI summary of each application.

```python
def create_app(db_path: str, llm_base_url: str | None = None, api_key: str | None = None) -> Flask: ...
```

`GET /applications/<id>/summary` → **200** `{"summary": "..."}`. Get it from the LLM at
`POST {llm_base_url}/llm/v1/messages`. That's the same mock Messages API as the
*LLM API Client* problem: headers `x-api-key` and `anthropic-version: 2023-06-01`, and the
reply text is in the `text` blocks of `content`.

- The prompt must include the application's applicant, address, type, status and
  description. (The mock model echoes your prompt back, so the tests can check.)
- LLM calls are slow and cost money. Call the LLM **at most once per application per
  status**; serve repeats from a cache that survives restarts. A status change means a
  fresh summary.
- If the LLM call fails, return **503** and cache nothing. Unknown application → **404**,
  without calling the LLM.
""",
        },
    ],
    "discussion": [
        "The permit office wants applicants to upload PDFs and drawings. How does the API and storage change?",
        "Two reviewers transition the same application at the same moment. What happens, and how would you prevent a bad state?",
        "How would you version this API once a mobile app depends on it?",
        "The summary sometimes misstates the address. How do you detect that, and what do you show reviewers?",
        "SQLite vs Postgres for this client: when would you switch, and what changes?",
        "Who can see which applications? Sketch authentication and per-municipality access.",
    ],
    "java_tip": """
*This tab names Python tools, which can hint at an approach.*

**Flask** (a micro framework, like a tiny Spring MVC):

```python
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.post("/items")                      # also @app.get, @app.route(..., methods=[...])
def create_item():
    body = request.get_json(silent=True)  # None if the body isn't JSON
    return jsonify({"id": 1}), 201       # (body, status code)

@app.get("/items/<int:item_id>")         # path variable, converted to int
def get_item(item_id):
    page = request.args.get("page", "1") # query string, always str
    return jsonify({"id": item_id})
```

- Testing without a server: `client = app.test_client(); resp = client.post("/items", json={...}); resp.status_code, resp.get_json()`.
- Routes defined **inside** `create_app` close over its local variables, so you get per-app state for free.

**sqlite3** (JDBC-like, built in):

```python
conn = sqlite3.connect(path)
conn.row_factory = sqlite3.Row           # rows behave like dicts: dict(row)
cur = conn.execute("INSERT INTO t (a) VALUES (?)", (value,))   # always ? placeholders
cur.lastrowid; conn.commit()
conn.execute("SELECT * FROM t WHERE id = ?", (1,)).fetchone()
```

- `INTEGER PRIMARY KEY AUTOINCREMENT` gives increasing ids. `executescript(...)` runs multiple statements.
- Open a connection per request (Flask's `g` object) rather than sharing one across threads.
""",
    "starter": '''from flask import Flask, jsonify, request


def create_app(db_path: str) -> Flask:
    app = Flask(__name__)

    @app.post("/applications")
    def create_application():
        pass

    return app
''',
    "solution": SOLUTION,
    "tests": [
        T(1, PRELUDE + """
            first = new()
            second = new(applicant="Omar Khan", address="7 Harbour Rd", type="commercial", description="Office fit-out")
            result = [first.status_code, first.get_json(), second.status_code, second.get_json()["id"]]
        """, [201, app_json(1), 201, 2], label="create"),
        T(1, PRELUDE + """
            new(); new(applicant="Omar Khan")
            r = client.get("/applications/2")
            result = [r.status_code, r.get_json()]
        """, [200, app_json(2, applicant="Omar Khan")], label="fetch"),
        T(1, PRELUDE + """
            r = client.post("/applications", json={"applicant": "Sara Ali", "address": "3 Palm Grove", "type": "residential"})
            result = [r.status_code, r.get_json()["description"], r.get_json()["status"]]
        """, [201, "", "submitted"], label="description is optional"),
        T(1, PRELUDE + """
            cases = [
                {"address": "1 St", "type": "boat"},
                {"applicant": "A", "address": "   ", "type": "solar"},
                {"applicant": "A", "address": "1 St", "type": "solar", "description": 42},
                {"applicant": "A", "address": "1 St", "type": ["solar"]},
                {"applicant": 7, "address": None, "type": "solar"},
            ]
            out = []
            for body in cases:
                r = client.post("/applications", json=body)
                out.append([r.status_code, r.get_json()["fields"]])
            r = client.post("/applications", data="not json", content_type="text/plain")
            out.append([r.status_code, r.get_json()["fields"], "error" in r.get_json()])
            result = out
        """, [[400, ["applicant", "type"]], [400, ["address"]], [400, ["description"]], [400, ["type"]],
              [400, ["address", "applicant"]], [400, [], True]], label="validation"),
        T(1, PRELUDE + """
            new()
            r = client.get("/applications/99")
            result = [r.status_code, "error" in r.get_json(), client.get("/applications/1").status_code]
        """, [404, True, 200], label="404"),
        T(2, PRELUDE + """
            new()
            steps = [move(1, "under_review"), move(1, "needs_info", note="Missing roof survey"),
                     move(1, "under_review", actor="reviewer-2"), move(1, "approved", actor="reviewer-2")]
            result = [[s.status_code for s in steps], steps[-1].get_json()["status"], client.get("/applications/1").get_json()["status"]]
        """, [[200, 200, 200, 200], "approved", "approved"], label="happy path"),
        T(2, PRELUDE + """
            new()
            move(1, "under_review"); move(1, "needs_info", note="Missing roof survey")
            r = client.get("/applications/1/history")
            result = [r.status_code, r.get_json()]
        """, [200, [
            {"from": None, "to": "submitted", "actor": "Layla Haddad", "note": ""},
            {"from": "submitted", "to": "under_review", "actor": "reviewer-1", "note": ""},
            {"from": "under_review", "to": "needs_info", "actor": "reviewer-1", "note": "Missing roof survey"},
        ]], label="audit history"),
        T(2, PRELUDE + """
            new(); new()
            move(2, "under_review"); move(2, "rejected")
            result = [
                move(1, "approved").status_code,
                move(2, "under_review").status_code,
                move(1, "lost").status_code,
                client.post("/applications/1/transitions", json={"to": "under_review"}).status_code,
                move(1, "under_review", actor="").status_code,
                move(99, "under_review").status_code,
                client.get("/applications/99/history").status_code,
                client.get("/applications/1").get_json()["status"],
                len(client.get("/applications/1/history").get_json()),
            ]
        """, [409, 409, 400, 400, 400, 404, 404, "submitted", 1], label="rejected moves change nothing"),
        T(3, PRELUDE + SEED + """
            r = client.get("/applications")
            body = r.get_json()
            result = [r.status_code, body["total"], [a["id"] for a in body["items"]]]
        """, [200, 5, [1, 2, 3, 4, 5]], label="list all"),
        T(3, PRELUDE + SEED + """
            def ids(query):
                body = client.get("/applications" + query).get_json()
                return [[a["id"] for a in body["items"]], body["total"]]
            result = [ids("?type=solar"), ids("?status=submitted"), ids("?status=approved&type=solar"),
                      ids("?q=PALM"), ids("?q=khan"), ids("?q=palm&type=residential"), ids("?q=nowhere")]
        """, [[[1, 4], 2], [[1, 3, 5], 3], [[4], 1], [[1, 3], 2], [[2], 1], [[3], 1], [[], 0]], label="filters and search"),
        T(3, PRELUDE + SEED + """
            def page(query):
                body = client.get("/applications" + query).get_json()
                return [[a["id"] for a in body["items"]], body["total"]]
            result = [page("?limit=2"), page("?limit=2&offset=2"), page("?limit=2&offset=4"), page("?offset=10"),
                      page("?type=solar&limit=1&offset=1")]
        """, [[[1, 2], 5], [[3, 4], 5], [[5], 5], [[], 5], [[4], 2]], label="pagination"),
        T(3, PRELUDE + SEED + """
            result = [client.get("/applications" + q).status_code
                      for q in ("?limit=0", "?limit=101", "?limit=abc", "?offset=-1", "?offset=x", "?limit=100")]
        """, [400, 400, 400, 400, 400, 200], label="invalid paging"),
        T(4, PRELUDE + """
            new(); new(applicant="Omar Khan")
            move(1, "under_review")
            restarted = create_app(db_path).test_client()
            third = restarted.post("/applications", json={"applicant": "Sara Ali", "address": "3 Palm Grove", "type": "residential"})
            result = [
                restarted.get("/applications/1").get_json()["status"],
                len(restarted.get("/applications/1/history").get_json()),
                restarted.get("/applications").get_json()["total"],
                third.get_json()["id"],
            ]
        """, ["under_review", 2, 3, 3], label="survives a restart"),
        T(4, PRELUDE + """
            other = create_app(db_path).test_client()
            new()
            seen_by_other = other.get("/applications/1").status_code
            other.post("/applications/1/transitions", json={"to": "under_review", "actor": "reviewer-9"})
            result = [seen_by_other, client.get("/applications/1").get_json()["status"],
                      client.get("/applications/1/history").get_json()[-1]["actor"]]
        """, [200, "under_review", "reviewer-9"], label="two processes, one database"),
        T(4, PRELUDE + """
            fresh = create_app(os.path.join(tmpdir, "other.db")).test_client()
            new()
            result = [fresh.get("/applications").get_json(), fresh.get("/applications/1").status_code]
        """, [{"items": [], "total": 0}, 404], label="different db_path, different data"),
        T(5, AI_PRELUDE + """
            new()
            r = client.get("/applications/1/summary")
            text = r.get_json()["summary"]
            again = client.get("/applications/1/summary").get_json()["summary"]
            result = [r.status_code, all(s in text for s in ("Layla Haddad", "12 Palm St", "solar", "submitted", "Rooftop panels")),
                      again == text, llm_stats(base_url, key)["attempts"]]
        """, [200, True, True, 1], label="summary is generated once"),
        T(5, AI_PRELUDE + """
            new()
            client.get("/applications/1/summary")
            move(1, "under_review")
            text = client.get("/applications/1/summary").get_json()["summary"]
            client.get("/applications/1/summary")
            result = ["under_review" in text, llm_stats(base_url, key)["attempts"]]
        """, [True, 2], label="status change means a new summary"),
        T(5, AI_PRELUDE + """
            new()
            first = client.get("/applications/1/summary").get_json()["summary"]
            restarted = create_app(db_path, llm_base_url=base_url, api_key=key).test_client()
            again = restarted.get("/applications/1/summary").get_json()["summary"]
            result = [again == first, llm_stats(base_url, key)["attempts"]]
        """, [True, 1], label="cache survives a restart"),
        T(5, AI_PRELUDE + """
            new(applicant="[overloaded:50] Omar Khan")
            first = client.get("/applications/1/summary")
            second = client.get("/applications/1/summary")
            result = [first.status_code, "error" in first.get_json(), second.status_code,
                      llm_stats(base_url, key)["attempts"] >= 2]
        """, [503, True, 503, True], label="LLM failure: 503, nothing cached"),
        T(5, AI_PRELUDE + """
            r = client.get("/applications/42/summary")
            result = [r.status_code, llm_stats(base_url, key)["attempts"]]
        """, [404, 0], label="unknown application: no LLM call"),
    ],
}

PROBLEMS = [PERMITS_API]
