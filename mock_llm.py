"""A deterministic mock of an LLM Messages API, for the Applied AI problems.

    POST /mock/llm/v1/messages      same request/response shape as Anthropic's Messages API
    GET  /mock/llm/stats?key=...    how many requests a given API key made (used by the tests)

It validates requests the way the real API does (headers, roles, tool_use/tool_result
pairing) so code that works here is shaped right for the real thing. Its "model" is
scripted: what it says depends on markers in the conversation, as each problem documents.
"""
import json
import re
import threading
import time
from collections import defaultdict
from itertools import count

from flask import Blueprint, jsonify, request

bp = Blueprint("mock_llm", __name__, url_prefix="/mock/llm")

_lock = threading.Lock()
_ids = count(1)
_stats = defaultdict(lambda: {"attempts": 0, "in_flight": 0, "max_in_flight": 0})
_failures = defaultdict(int)  # (api key, prompt) -> failures served so far

INVOICES = {
    "INV-1001": {"vendor": "Acme Steel", "total": 1250.0, "due_date": "2026-11-01"},
    "INV-1002": {"vendor": "Desert Logistics", "total": 980.5, "due_date": "2026-10-15"},
    "INV-1003": {"vendor": "Gulf Cement Co", "total": 15000.0, "due_date": "2026-12-31"},
    "INV-1004": {"vendor": "Northwind Power", "total": 432.1, "due_date": "2027-01-20"},
    "INV-1005": {"vendor": "Broken Corp", "total": 1.0, "due_date": "2026-01-01"},
}

PERMITS = {"P-17": {"status": "approved", "inspector": "Layla Haddad"}}
INSPECTORS = {"Layla Haddad": {"phone": "+971-4-555-0117"}}


def _error(status, kind, message, headers=None):
    resp = jsonify({"type": "error", "error": {"type": kind, "message": message}})
    resp.status_code = status
    for k, v in (headers or {}).items():
        resp.headers[k] = v
    return resp


def _text_of(content):
    """All text in a message's content (a string, or a list of blocks)."""
    if isinstance(content, str):
        return content
    parts = []
    for block in content:
        if block.get("type") == "text":
            parts.append(block.get("text", ""))
        elif block.get("type") == "tool_result":
            parts.append(_result_text(block))
    return "".join(parts)


def _result_text(block):
    content = block.get("content", "")
    if isinstance(content, str):
        return content
    return "".join(b.get("text", "") for b in content if b.get("type") == "text")


def _validate(body):
    """Return an error response for malformed requests, like the real API, or None."""
    if not isinstance(body, dict):
        return _error(400, "invalid_request_error", "request body must be a JSON object")
    for field in ("model", "max_tokens", "messages"):
        if field not in body:
            return _error(400, "invalid_request_error", f"{field}: Field required")
    if not isinstance(body["max_tokens"], int) or body["max_tokens"] < 1:
        return _error(400, "invalid_request_error", "max_tokens: must be a positive integer")
    messages = body["messages"]
    if not isinstance(messages, list) or not messages:
        return _error(400, "invalid_request_error", "messages: at least one message is required")
    if messages[0].get("role") == "system":
        return _error(400, "invalid_request_error",
                      "messages: a system prompt goes in the top-level `system` parameter, not messages[0]")
    if messages[0].get("role") != "user":
        return _error(400, "invalid_request_error", "messages: the first message must use the user role")
    for i, msg in enumerate(messages):
        if msg.get("role") not in ("user", "assistant"):
            return _error(400, "invalid_request_error", f"messages.{i}.role: must be user or assistant")
        if i and msg["role"] == messages[i - 1]["role"]:
            return _error(400, "invalid_request_error", "messages: roles must alternate between user and assistant")
        content = msg.get("content")
        if not isinstance(content, (str, list)):
            return _error(400, "invalid_request_error", f"messages.{i}.content: must be a string or a list of blocks")
        blocks = content if isinstance(content, list) else []
        results = [b for b in blocks if b.get("type") == "tool_result"]
        prev = messages[i - 1]["content"] if i else []
        uses = [b for b in prev if isinstance(prev, list) and b.get("type") == "tool_use"]
        if uses and msg["role"] == "user":
            missing = {u["id"] for u in uses} - {r.get("tool_use_id") for r in results}
            if missing:
                return _error(400, "invalid_request_error",
                              f"messages.{i}: tool_use ids {sorted(missing)} have no tool_result in the next message")
        for r in results:
            if r.get("tool_use_id") not in {u["id"] for u in uses}:
                return _error(400, "invalid_request_error",
                              f"messages.{i}: tool_result for unknown tool_use_id {r.get('tool_use_id')!r}")
            if not isinstance(r.get("content", ""), (str, list)):
                return _error(400, "invalid_request_error",
                              f"messages.{i}: tool_result content must be a string or a list of blocks")
    return None


def _message(model, content, stop_reason, prompt_words):
    out_words = sum(len(_text_of([b]).split()) for b in content if b["type"] == "text") + 5 * sum(
        b["type"] == "tool_use" for b in content)
    return jsonify({
        "id": f"msg_mock_{next(_ids):05d}",
        "type": "message",
        "role": "assistant",
        "model": model,
        "content": content,
        "stop_reason": stop_reason,
        "stop_sequence": None,
        "usage": {"input_tokens": prompt_words, "output_tokens": out_words},
    })


def _tool_use(turn, i, name, tool_input):
    return {"type": "tool_use", "id": f"toolu_mock_{turn}_{i}", "name": name, "input": tool_input}


def _agent_reply(first, messages, tool_names):
    """Scripted agent behaviour. Returns (content blocks, stop_reason)."""
    turn = sum(m["role"] == "assistant" for m in messages)
    last = messages[-1]["content"]
    results = [b for b in last if isinstance(last, list) and b.get("type") == "tool_result"]
    by_id = {r["tool_use_id"]: r for r in results}

    def call(*uses, lead=None):
        blocks = [{"type": "text", "text": lead}] if lead else []
        return blocks + [_tool_use(turn, i, n, inp) for i, (n, inp) in enumerate(uses)], "tool_use"

    def say(text):
        return [{"type": "text", "text": text}], "end_turn"

    if "[weather]" in first:
        if turn == 0:
            return call(("get_weather", {"city": "Dubai"}), lead="Let me check the weather.")
        return say(f"The weather in Dubai is {_result_text(results[0])}.")
    if "[parallel]" in first:
        if turn == 0:
            return call(("get_weather", {"city": "Dubai"}), ("get_weather", {"city": "Toronto"}))
        dubai, toronto = by_id["toolu_mock_0_0"], by_id["toolu_mock_0_1"]
        return say(f"Dubai: {_result_text(dubai)}. Toronto: {_result_text(toronto)}.")
    if "[chain]" in first:
        if turn == 0:
            return call(("lookup_permit", {"permit_id": "P-17"}))
        if turn == 1:
            try:
                permit = json.loads(_result_text(results[0]))
            except ValueError:
                return say("I couldn't read the permit record (expected JSON).")
            return call(("get_inspector", {"name": permit.get("inspector")}))
        try:
            inspector = json.loads(_result_text(results[0]))
        except ValueError:
            return say("I couldn't read the inspector record (expected JSON).")
        return say(f"Permit P-17 is approved; the inspector can be reached at {inspector.get('phone')}.")
    if "[error]" in first:
        if turn == 0:
            return call(("get_weather", {"city": "Atlantis"}))
        r = results[0]
        if r.get("is_error") is True:
            return say(f"Sorry, I couldn't get the weather: {_result_text(r)}")
        return say(f"The weather in Atlantis is {_result_text(r)}.")
    if "[loop]" in first:
        return call(("get_weather", {"city": "Loopville"}))
    return None


@bp.post("/v1/messages")
def messages_endpoint():
    key = request.headers.get("x-api-key")
    if not key:
        return _error(401, "authentication_error", "x-api-key header is required")
    if not request.headers.get("anthropic-version"):
        return _error(400, "invalid_request_error", "anthropic-version header is required")

    stats = _stats[key]
    with _lock:
        stats["attempts"] += 1
    body = request.get_json(silent=True)
    invalid = _validate(body)
    if invalid:
        return invalid

    messages = body["messages"]
    first = _text_of(messages[0]["content"])
    last = _text_of(messages[-1]["content"])
    prompt_words = len(" ".join(_text_of(m["content"]) for m in messages).split())
    model = body["model"]

    # Scripted failures, counted per (key, prompt) so retries eventually succeed.
    m = re.search(r"\[(overloaded|ratelimit|servererror):(\d+)\]", first)
    if m:
        kind, n = m.group(1), int(m.group(2))
        with _lock:
            served = _failures[(key, first)]
            if served < n:
                _failures[(key, first)] += 1
        if served < n:
            if kind == "overloaded":
                return _error(529, "overloaded_error", "Overloaded")
            if kind == "ratelimit":
                return _error(429, "rate_limit_error", "Rate limited", {"retry-after": "0"})
            return _error(500, "api_error", "Internal server error")
    if "[bad]" in first:
        return _error(400, "invalid_request_error", "this request is malformed (scripted)")

    with _lock:
        stats["in_flight"] += 1
        stats["max_in_flight"] = max(stats["max_in_flight"], stats["in_flight"])
    try:
        if "[slow]" in first:
            time.sleep(0.25)

        tool_names = {t.get("name") for t in body.get("tools", [])}
        if tool_names:
            scripted = _agent_reply(first, messages, tool_names)
            if scripted:
                content, stop = scripted
                missing = {b["name"] for b in content if b["type"] == "tool_use"} - tool_names
                if missing:
                    content, stop = [{"type": "text", "text": f"I don't have a tool called {sorted(missing)[0]}."}], "end_turn"
                return _message(model, content, stop, prompt_words)

        invoice = re.search(r"INV-\d{4}", first)
        if invoice and invoice.group() in INVOICES:
            return _message(model, [{"type": "text", "text": _invoice_reply(invoice.group(), messages)}],
                            "end_turn", prompt_words)

        reply = f"Echo: {last}"
        if body.get("system"):
            reply = f"({body['system']}) {reply}"
        # Real responses often start with a thinking block and can split text across blocks.
        half = len(reply) // 2
        content = [
            {"type": "thinking", "thinking": "", "signature": "mock-signature"},
            {"type": "text", "text": reply[:half]},
            {"type": "text", "text": reply[half:]},
        ]
        return _message(model, content, "end_turn", prompt_words)
    finally:
        with _lock:
            stats["in_flight"] -= 1


def _invoice_reply(invoice_id, messages):
    data = INVOICES[invoice_id]
    user_turns = sum(m["role"] == "user" for m in messages)
    if invoice_id == "INV-1001":
        return json.dumps(data)
    if invoice_id == "INV-1002":
        return "```json\n" + json.dumps(data, indent=2) + "\n```"
    if invoice_id == "INV-1003":
        return f"Here is the extracted data:\n{json.dumps(data)}\nLet me know if you need anything else."
    if invoice_id == "INV-1004":
        if user_turns == 1:
            return json.dumps({"vendor": data["vendor"], "due_date": data["due_date"]})
        return json.dumps(data)
    return '{"vendor": "Broken Corp", "total": "a lot", "due_date": "soon"'


@bp.get("/stats")
def stats_endpoint():
    key = request.args.get("key", "")
    s = _stats.get(key, {"attempts": 0, "max_in_flight": 0})
    return jsonify({"attempts": s["attempts"], "max_in_flight": s["max_in_flight"]})
