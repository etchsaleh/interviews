"""A small in-memory REST API that the HTTP practice problems talk to.

Everything lives under /mock so you can also poke at it with curl or a browser,
e.g. http://127.0.0.1:5000/mock/users
"""
import itertools
import threading
import time
from collections import defaultdict

from flask import Blueprint, jsonify, request

bp = Blueprint("mock", __name__, url_prefix="/mock")
_lock = threading.Lock()

USERS = [
    {"id": 1, "name": "Ada", "email": "ada@example.com", "team": "platform", "active": True},
    {"id": 2, "name": "Linus", "email": "linus@example.com", "team": "kernel", "active": False},
    {"id": 3, "name": "Grace", "email": "grace@example.com", "team": "platform", "active": True},
    {"id": 4, "name": "Guido", "email": "guido@example.com", "team": "python", "active": True},
    {"id": 5, "name": "James", "email": "james@example.com", "team": "java", "active": False},
    {"id": 6, "name": "Barbara", "email": "barbara@example.com", "team": "platform", "active": True},
]

ORDERS = [
    {"id": 100 + i, "user_id": uid, "total": total}
    for i, (uid, total) in enumerate([
        (1, 25.5), (3, 10.0), (4, 99.99), (1, 5.25), (6, 42.0), (2, 13.37),
        (3, 7.5), (4, 0.51), (5, 60.0), (1, 19.0), (6, 3.0), (3, 1.0),
    ])
]
PAGE_SIZE = 5

ACCOUNTS = {"ada": "lovelace", "grace": "hopper"}
TOKENS = {}  # token -> username

TODOS = {}
_todo_ids = itertools.count(1)
_flaky_attempts = defaultdict(int)
PRICE_CALLS = defaultdict(lambda: defaultdict(int))  # client -> sku -> number of calls


def price_for(sku):
    return round(sum(ord(c) for c in sku) % 90 + 9.99, 2)


def _error(message, status):
    return jsonify({"error": message}), status


ENDPOINTS = [
    ("GET", "/users", "All users. Query params: team=<name>, active=true|false"),
    ("GET", "/users/<id>", "One user, or 404"),
    ("GET", "/orders?page=N", "Paginated orders; next_page is null on the last page"),
    ("POST", "/todos", 'Create a todo from JSON {"title": "..."} -> 201'),
    ("GET", "/todos/<id>", "One todo, or 404"),
    ("POST", "/login", 'JSON {"username": "ada", "password": "lovelace"} -> {"token": ...}'),
    ("GET", "/profile", "Needs header Authorization: Bearer <token>"),
    ("GET", "/flaky?key=<k>", "503, 503, 200, repeat (per key)"),
    ("GET", "/price/<sku>?client=<id>", "Slow price lookup (counts calls per client)"),
    ("ANY", "/echo", "Echoes your method, query params, JSON body and headers"),
    ("POST", "/llm/v1/messages", "Mock LLM with the Messages API shape (needs x-api-key + anthropic-version headers)"),
    ("GET", "/llm/stats?key=<api key>", "How many requests an API key made to the mock LLM"),
]


@bp.get("", strict_slashes=False)
def index():
    """GET /mock - lists the available endpoints."""
    base = request.base_url.rstrip("/")
    return jsonify({
        "base_url": base,
        "endpoints": [
            {"method": m, "path": path, "url": base + path, "description": d} for m, path, d in ENDPOINTS
        ],
    })


@bp.get("/users")
def list_users():
    team = request.args.get("team")
    active = request.args.get("active")
    users = USERS
    if team:
        users = [u for u in users if u["team"] == team]
    if active is not None:
        want = active.lower() == "true"
        users = [u for u in users if u["active"] == want]
    return jsonify(users)


@bp.get("/users/<int:user_id>")
def get_user(user_id):
    for u in USERS:
        if u["id"] == user_id:
            return jsonify(u)
    return _error(f"user {user_id} not found", 404)


@bp.get("/orders")
def list_orders():
    page = request.args.get("page", default=1, type=int)
    start = (page - 1) * PAGE_SIZE
    chunk = ORDERS[start:start + PAGE_SIZE] if page >= 1 else []
    has_more = start + PAGE_SIZE < len(ORDERS)
    return jsonify({"data": chunk, "page": page, "next_page": page + 1 if has_more else None})


@bp.post("/todos")
def create_todo():
    body = request.get_json(silent=True)
    if not isinstance(body, dict) or not isinstance(body.get("title"), str) or not body["title"]:
        return _error("JSON body with a non-empty 'title' is required", 400)
    with _lock:
        todo = {"id": next(_todo_ids), "title": body["title"], "completed": bool(body.get("completed", False))}
        TODOS[todo["id"]] = todo
    return jsonify(todo), 201


@bp.get("/todos/<int:todo_id>")
def get_todo(todo_id):
    todo = TODOS.get(todo_id)
    return jsonify(todo) if todo else _error("todo not found", 404)


@bp.post("/login")
def login():
    body = request.get_json(silent=True) or {}
    username, password = body.get("username"), body.get("password")
    if ACCOUNTS.get(username) != password:
        return _error("invalid credentials", 401)
    token = f"tok-{username}-{len(TOKENS) + 1}"
    with _lock:
        TOKENS[token] = username
    return jsonify({"token": token})


@bp.get("/profile")
def profile():
    header = request.headers.get("Authorization", "")
    token = header.removeprefix("Bearer ").strip()
    username = TOKENS.get(token) if header.startswith("Bearer ") else None
    if not username:
        return _error("missing or invalid bearer token", 401)
    return jsonify({"username": username, "display_name": username.capitalize(), "plan": "pro"})


@bp.get("/flaky")
def flaky():
    """Fails with 503 twice, then succeeds, then repeats - per `key`."""
    key = request.args.get("key", "default")
    with _lock:
        _flaky_attempts[key] += 1
        attempt = _flaky_attempts[key]
    if attempt % 3 != 0:
        return _error("service temporarily unavailable, try again", 503)
    return jsonify({"key": key, "value": len(key) * 7})


@bp.get("/price/<sku>")
def price(sku):
    """A deliberately slow lookup - callers are expected to cache results."""
    client = request.args.get("client", "anonymous")
    with _lock:
        PRICE_CALLS[client][sku] += 1
    time.sleep(0.05)
    return jsonify({"sku": sku, "price": price_for(sku)})


@bp.route("/echo", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
def echo():
    """Returns what you sent - handy for experimenting with requests."""
    return jsonify({
        "method": request.method,
        "args": request.args.to_dict(),
        "json": request.get_json(silent=True),
        "headers": {k: v for k, v in request.headers.items() if k.lower().startswith(("x-", "authorization", "content-type"))},
    })
