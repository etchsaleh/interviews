"""Applied AI / forward-deployed engineering problems (multi-part, like problems/multipart.py).

The LLM problems talk to the mock Messages API in mock_llm.py, which mirrors the real
request/response shape and validation, so there's no API key or network needed. Each
test gets a fresh API key, so the mock's per-key request counts are the test's own.
"""
from problems.multipart import T

LLM_PRELUDE = """
            from practice_helpers import new_key, llm_stats
            key = new_key()
"""
AGENT_PRELUDE = """
            from practice_helpers import new_key, llm_stats, agent_tools
            key = new_key()
            specs, handlers, log = agent_tools()
"""

API_SHAPE = """
**The API** (a mock with the same shape as Anthropic's Messages API): `POST {base_url}/llm/v1/messages`

```
headers:  x-api-key: <api_key>
          anthropic-version: 2023-06-01
          content-type: application/json
body:     {"model": "claude-opus-5-5", "max_tokens": 1024,
           "system": "optional system prompt",
           "messages": [{"role": "user", "content": "Hello"}]}
response: {"id": "msg_...", "type": "message", "role": "assistant",
           "content": [{"type": "text", "text": "..."}, ...],
           "stop_reason": "end_turn", "usage": {"input_tokens": 9, "output_tokens": 3}}
errors:   {"type": "error", "error": {"type": "overloaded_error", "message": "..."}}
```

The mock "model" is scripted: it replies `Echo: <your last message>`, or
`(<system prompt>) Echo: <your last message>` when a system prompt is set.
"""

# ================================================================ LLM client
LLM_CLIENT_SOLUTION = '''import json
import re
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date

import requests

MODEL = "claude-opus-5-5"
RETRYABLE = {429, 500, 502, 503, 504, 529}
MAX_RETRIES = 4


def _post(base_url: str, api_key: str, body: dict) -> dict:
    headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
    for attempt in range(MAX_RETRIES + 1):
        resp = requests.post(f"{base_url}/llm/v1/messages", headers=headers, json=body, timeout=30)
        if resp.status_code not in RETRYABLE or attempt == MAX_RETRIES:
            break
        retry_after = resp.headers.get("retry-after")
        time.sleep(float(retry_after) if retry_after else 0.05 * 2 ** attempt)
    if resp.status_code != 200:
        error = resp.json().get("error", {})
        raise RuntimeError(f"LLM API error {resp.status_code} {error.get('type')}: {error.get('message')}")
    return resp.json()


def _text(message: dict) -> str:
    return "".join(b["text"] for b in message["content"] if b["type"] == "text")


def complete(base_url: str, api_key: str, prompt: str, system: str | None = None) -> str:
    body = {"model": MODEL, "max_tokens": 1024, "messages": [{"role": "user", "content": prompt}]}
    if system:
        body["system"] = system
    return _text(_post(base_url, api_key, body))


def _parse_invoice(reply: str) -> tuple[dict | None, str]:
    """Return (invoice, "") if the reply holds a valid invoice, else (None, what's wrong)."""
    match = re.search(r"\\{.*\\}", reply, re.DOTALL)
    if not match:
        return None, "no JSON object found"
    try:
        data = json.loads(match.group())
    except ValueError as exc:
        return None, f"invalid JSON: {exc}"
    problems = []
    if not isinstance(data.get("vendor"), str) or not data["vendor"]:
        problems.append("vendor must be a non-empty string")
    total = data.get("total")
    if isinstance(total, bool) or not isinstance(total, (int, float)) or total < 0:
        problems.append("total must be a non-negative number")
    try:
        date.fromisoformat(data.get("due_date"))
        if not re.fullmatch(r"\\d{4}-\\d{2}-\\d{2}", data["due_date"]):
            raise ValueError
    except (TypeError, ValueError):
        problems.append("due_date must be a YYYY-MM-DD date")
    if problems:
        return None, "; ".join(problems)
    return {"vendor": data["vendor"], "total": float(total), "due_date": data["due_date"]}, ""


def extract_invoice(base_url: str, api_key: str, document: str) -> dict:
    messages = [{"role": "user", "content": (
        "Extract the invoice fields from the document below. Reply with only a JSON object with keys "
        '"vendor" (string), "total" (number) and "due_date" (YYYY-MM-DD).\\n\\n' + document)}]
    for _attempt in range(3):
        reply = _text(_post(base_url, api_key, {"model": MODEL, "max_tokens": 1024, "messages": messages}))
        invoice, problem = _parse_invoice(reply)
        if invoice:
            return invoice
        messages += [{"role": "assistant", "content": reply},
                     {"role": "user", "content": f"That wasn't valid: {problem}. Reply with only the corrected JSON object."}]
    raise ValueError(f"model never produced a valid invoice: {problem}")


def complete_many(base_url: str, api_key: str, prompts: list[str], max_concurrency: int = 4) -> list[str]:
    with ThreadPoolExecutor(max_workers=max_concurrency) as pool:
        return list(pool.map(lambda p: complete(base_url, api_key, p), prompts))
'''

LLM_CLIENT = {
    "id": "ai-llm-client",
    "title": "LLM API Client",
    "difficulty": "Medium",
    "category": "Applied AI",
    "tags": ["LLM API", "requests", "retries", "structured output", "concurrency"],
    "entry": "complete",
    "mode": "script",
    "needs_base_url": True,
    "target_minutes": 40,
    "timeout": 25,
    "description": """
A customer's backend needs a small, reliable client for an LLM API. No SDK is allowed in
their environment, so you'll use `requests` directly. Every function takes the server's
`base_url` and an `api_key`.
""" + API_SHAPE,
    "parts": [
        {
            "title": "One call",
            "description": """
```python
def complete(base_url: str, api_key: str, prompt: str, system: str | None = None) -> str: ...
```

Send `prompt` as a single user message (with `system` as the system prompt if given) and
return the reply's text. A reply can contain several content blocks, including blocks
that aren't text.
""",
        },
        {
            "title": "Retries",
            "description": """
The API is sometimes overloaded. Make `complete` resilient:

- Retry on **429, 500 and 529**, up to **4 retries** (5 attempts in total). Honour a
  `retry-after` header if present; otherwise back off, starting from 0.05 s. The tests
  have a time budget, so keep the waits short.
- **Any other error is not retried.** Raise an exception straight away.
- If every attempt fails, raise an exception.
""",
        },
        {
            "title": "Structured extraction",
            "description": """
```python
def extract_invoice(base_url: str, api_key: str, document: str) -> dict: ...
# -> {"vendor": "Acme Steel", "total": 1250.0, "due_date": "2026-11-01"}
```

Ask the model to extract `vendor` (non-empty string), `total` (number, returned as a
float) and `due_date` (`YYYY-MM-DD`) from an invoice document. The mock model answers
like real ones sometimes do: plain JSON, JSON inside a code fence, JSON surrounded by
prose, or a reply with a field missing or invalid.

- Return the validated dict.
- If the reply isn't valid, **ask again in the same conversation**, saying what was
  wrong. Make at most **3 requests** in total, then raise `ValueError`.
""",
        },
        {
            "title": "Batch at scale",
            "description": """
```python
def complete_many(base_url: str, api_key: str, prompts: list[str], max_concurrency: int = 4) -> list[str]: ...
```

Run `complete` for every prompt and return the replies **in the same order as the
prompts**. Requests must run concurrently, but never more than `max_concurrency` at once.
Each mock request takes ~0.25 s here, so 12 prompts must finish in **under 1.5 s**.
""",
        },
    ],
    "discussion": [
        "Your client hits the provider's rate limit during a big batch. What do you change: client-side throttling, a queue, the Batch API?",
        "How would you make extraction more reliable *before* reaching for retries: schema-constrained outputs, tool use, better prompts?",
        "The customer can't send data outside their country. What are your options for hosting the model?",
        "How do you log and monitor these calls in production without storing sensitive document contents?",
        "Threads vs asyncio for this batch job: when would you pick each?",
    ],
    "java_tip": """
*This tab names Python tools, which can hint at an approach.*

- `requests.post(url, headers={...}, json=body, timeout=30)`; then `resp.status_code`, `resp.headers.get("retry-after")`, `resp.json()`.
- `time.sleep(0.05)` takes seconds as a float.
- `json.loads(s)` raises `ValueError` (`json.JSONDecodeError`) on bad JSON. `re.search(r"\\{.*\\}", s, re.DOTALL)` finds a `{...}` span.
- `date.fromisoformat("2026-11-01")` validates a date.
- `concurrent.futures.ThreadPoolExecutor(max_workers=n)` and its `.map(fn, items)` keep results in input order. It's the `ExecutorService` equivalent, and threads are fine for I/O-bound work.
- Real projects would use the official SDK: `anthropic.Anthropic().messages.create(model=..., max_tokens=..., messages=[...])`, which retries 429/5xx for you.
""",
    "starter": '''import requests


def complete(base_url: str, api_key: str, prompt: str, system: str | None = None) -> str:
    pass
''',
    "solution": LLM_CLIENT_SOLUTION,
    "tests": [
        T(1, LLM_PRELUDE + """
            result = complete(base_url, key, "Hello")
        """, "Echo: Hello"),
        T(1, LLM_PRELUDE + """
            result = complete(base_url, key, "Summarise the permit backlog", system="Be brief")
        """, "(Be brief) Echo: Summarise the permit backlog", label="system prompt"),
        T(1, LLM_PRELUDE + """
            result = [complete(base_url, key, "مرحبا — ok?"), llm_stats(base_url, key)["attempts"]]
        """, ["Echo: مرحبا — ok?", 1], label="unicode, one request"),
        T(2, LLM_PRELUDE + """
            text = complete(base_url, key, "[overloaded:2] status report")
            result = [text, llm_stats(base_url, key)["attempts"]]
        """, ["Echo: [overloaded:2] status report", 3], label="529 overloaded"),
        T(2, LLM_PRELUDE + """
            text = complete(base_url, key, "[ratelimit:1] hi")
            result = [text, llm_stats(base_url, key)["attempts"]]
        """, ["Echo: [ratelimit:1] hi", 2], label="429 with retry-after"),
        T(2, LLM_PRELUDE + """
            text = complete(base_url, key, "[servererror:1] hi")
            result = [text, llm_stats(base_url, key)["attempts"]]
        """, ["Echo: [servererror:1] hi", 2], label="500"),
        T(2, LLM_PRELUDE + """
            try:
                complete(base_url, key, "[bad] request")
                outcome = "returned"
            except Exception:
                outcome = "raised"
            result = [outcome, llm_stats(base_url, key)["attempts"]]
        """, ["raised", 1], label="400 is not retried"),
        T(2, LLM_PRELUDE + """
            try:
                complete(base_url, key, "[overloaded:10] doomed")
                outcome = "returned"
            except Exception:
                outcome = "raised"
            result = [outcome, llm_stats(base_url, key)["attempts"]]
        """, ["raised", 5], label="gives up after 4 retries"),
        T(3, LLM_PRELUDE + """
            result = extract_invoice(base_url, key, "Invoice INV-1001\\nFrom: Acme Steel\\nTotal due: $1,250.00 by Nov 1, 2026")
        """, {"vendor": "Acme Steel", "total": 1250.0, "due_date": "2026-11-01"}, label="plain JSON"),
        T(3, LLM_PRELUDE + """
            result = extract_invoice(base_url, key, "INV-1002 Desert Logistics, AED 980.50, due 15 Oct 2026")
        """, {"vendor": "Desert Logistics", "total": 980.5, "due_date": "2026-10-15"}, label="fenced JSON"),
        T(3, LLM_PRELUDE + """
            result = extract_invoice(base_url, key, "Gulf Cement Co - invoice INV-1003 - 15,000 - 2026-12-31")
        """, {"vendor": "Gulf Cement Co", "total": 15000.0, "due_date": "2026-12-31"}, label="JSON inside prose"),
        T(3, LLM_PRELUDE + """
            invoice = extract_invoice(base_url, key, "Northwind Power INV-1004 total 432.10 due 2027-01-20")
            result = [invoice, llm_stats(base_url, key)["attempts"]]
        """, [{"vendor": "Northwind Power", "total": 432.1, "due_date": "2027-01-20"}, 2],
          label="missing field: re-ask in the same conversation"),
        T(3, LLM_PRELUDE + """
            try:
                extract_invoice(base_url, key, "INV-1005 garbled scan")
                outcome = "returned"
            except ValueError:
                outcome = "ValueError"
            result = [outcome, llm_stats(base_url, key)["attempts"]]
        """, ["ValueError", 3], label="gives up after 3 requests"),
        T(4, LLM_PRELUDE + """
            import time
            prompts = [f"[slow] job {i}" for i in range(12)]
            start = time.perf_counter()
            replies = complete_many(base_url, key, prompts)
            elapsed = time.perf_counter() - start
            peak = llm_stats(base_url, key)["max_in_flight"]
            result = [replies == [f"Echo: {p}" for p in prompts], elapsed < 1.5, 2 <= peak <= 4]
        """, [True, True, True], label="12 prompts, in order, concurrent, capped at 4"),
        T(4, LLM_PRELUDE + """
            replies = complete_many(base_url, key, ["[slow] a", "[slow] b", "[slow] c"], max_concurrency=1)
            result = [replies, llm_stats(base_url, key)["max_in_flight"]]
        """, [["Echo: [slow] a", "Echo: [slow] b", "Echo: [slow] c"], 1], label="max_concurrency=1"),
        T(4, LLM_PRELUDE + """
            result = complete_many(base_url, key, ["[overloaded:1] x", "y"], max_concurrency=2)
        """, ["Echo: [overloaded:1] x", "Echo: y"], label="retries still apply"),
    ],
}


# ================================================================ agent loop
AGENT_SOLUTION = '''import json

import requests

MODEL = "claude-opus-5-5"


def _call(base_url, api_key, messages, tool_specs):
    resp = requests.post(
        f"{base_url}/llm/v1/messages",
        headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"},
        json={"model": MODEL, "max_tokens": 4096, "tools": tool_specs, "messages": messages},
        timeout=30,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"LLM API error {resp.status_code}: {resp.text}")
    return resp.json()


def _run_tool(handlers, block):
    try:
        output = handlers[block["name"]](**block["input"])
        content = output if isinstance(output, str) else json.dumps(output)
        return {"type": "tool_result", "tool_use_id": block["id"], "content": content}
    except Exception as exc:  # report the failure to the model instead of crashing the loop
        return {"type": "tool_result", "tool_use_id": block["id"], "content": str(exc), "is_error": True}


def run_agent(base_url: str, api_key: str, task: str, tool_specs: list[dict],
              handlers: dict, max_steps: int = 8) -> str:
    messages = [{"role": "user", "content": task}]
    for _step in range(max_steps):
        reply = _call(base_url, api_key, messages, tool_specs)
        tool_uses = [b for b in reply["content"] if b["type"] == "tool_use"]
        if reply["stop_reason"] != "tool_use" or not tool_uses:
            return "".join(b["text"] for b in reply["content"] if b["type"] == "text")
        messages.append({"role": "assistant", "content": reply["content"]})
        messages.append({"role": "user", "content": [_run_tool(handlers, b) for b in tool_uses]})
    raise RuntimeError(f"agent did not finish within {max_steps} steps")
'''

AGENT = {
    "id": "ai-agent-loop",
    "title": "Agent Tool-Use Loop",
    "difficulty": "Medium",
    "category": "Applied AI",
    "tags": ["agents", "tool use", "LLM API", "error handling"],
    "entry": "run_agent",
    "mode": "script",
    "needs_base_url": True,
    "target_minutes": 35,
    "timeout": 20,
    "description": """
Build the loop that lets an LLM use your tools, without an agent framework:

```python
def run_agent(base_url: str, api_key: str, task: str, tool_specs: list[dict],
              handlers: dict, max_steps: int = 8) -> str: ...
```

- `tool_specs`: tool definitions to send in the request's `tools` field, as-is:
  `{"name": ..., "description": ..., "input_schema": {JSON schema}}`
- `handlers`: `{tool name: python function}`. Call a handler with the tool's input as
  keyword arguments: `handlers[name](**input)`. Handlers return a string or a dict.
- Return the model's final text answer.
""" + API_SHAPE.replace("The mock \"model\" is scripted", "Without tool calls, the mock \"model\" is scripted") + """
**Tool calls.** When the model wants a tool, the reply has `"stop_reason": "tool_use"`
and content blocks like
`{"type": "tool_use", "id": "toolu_...", "name": "get_weather", "input": {"city": "Dubai"}}`.
Send each result back in the next **user** message as
`{"type": "tool_result", "tool_use_id": "toolu_...", "content": "<string>"}`. Like the
real API, the mock rejects conversations where the tool calls and results don't line up.
""",
    "parts": [
        {
            "title": "Single tool call",
            "description": "Make the loop work for tasks that need one tool call, and for tasks that need none.",
        },
        {
            "title": "Parallel and chained calls",
            "description": """
The model may ask for **several tools in one reply**, and may need **several rounds**
of tool calls, where later calls depend on earlier results. Some handlers return dicts,
and the model expects JSON for those.
""",
        },
        {
            "title": "Failures",
            "description": """
- When a handler raises, the agent must not crash. Report the failure to the model as
  that tool's result: `"is_error": true`, with the exception message (`str(exc)`) as content.
- The model can get stuck calling tools forever. Make at most `max_steps` model requests;
  if it still hasn't finished, raise `RuntimeError`.
""",
        },
    ],
    "discussion": [
        "A tool can take a destructive action (approve a permit, send an email). How do you add a human approval step?",
        "How would you trace and debug an agent that gave a wrong answer in production?",
        "Tool results can be huge (a 200-page document). What do you do about context length and cost?",
        "When should this be a fixed workflow instead of an open-ended agent?",
        "How would you test an agent's behaviour automatically before a release?",
    ],
    "java_tip": """
*This tab names Python tools, which can hint at an approach.*

- `fn(**kwargs)` calls a function with a dict as keyword arguments, so `handlers["get_weather"](**{"city": "Dubai"})` means `get_weather(city="Dubai")`.
- `json.dumps(obj)` turns a dict into a JSON string.
- `except Exception as exc:` catches anything a handler throws; `str(exc)` is its message.
- `isinstance(x, str)` checks a type at runtime.
""",
    "starter": '''import requests


def run_agent(base_url: str, api_key: str, task: str, tool_specs: list[dict],
              handlers: dict, max_steps: int = 8) -> str:
    pass
''',
    "solution": AGENT_SOLUTION,
    "tests": [
        T(1, AGENT_PRELUDE + """
            answer = run_agent(base_url, key, "[weather] What's the weather in Dubai?", specs, handlers)
            result = [answer, log]
        """, ["The weather in Dubai is 34°C and sunny.", [["get_weather", "Dubai"]]]),
        T(1, AGENT_PRELUDE + """
            answer = run_agent(base_url, key, "Say hi", specs, handlers)
            result = [answer, log, llm_stats(base_url, key)["attempts"]]
        """, ["Echo: Say hi", [], 1], label="no tool needed"),
        T(2, AGENT_PRELUDE + """
            answer = run_agent(base_url, key, "[parallel] Weather in Dubai and Toronto?", specs, handlers)
            result = [answer, sorted(c[1] for c in log)]
        """, ["Dubai: 34°C and sunny. Toronto: 8°C and cloudy.", ["Dubai", "Toronto"]], label="two tools in one reply"),
        T(2, AGENT_PRELUDE + """
            answer = run_agent(base_url, key, "[chain] Who inspects permit P-17 and how do I reach them?", specs, handlers)
            result = [answer, log, llm_stats(base_url, key)["attempts"]]
        """, ["Permit P-17 is approved; the inspector can be reached at +971-4-555-0117.",
              [["lookup_permit", "P-17"], ["get_inspector", "Layla Haddad"]], 3], label="chained calls, dict results"),
        T(3, AGENT_PRELUDE + """
            answer = run_agent(base_url, key, "[error] Weather in Atlantis?", specs, handlers)
            result = answer
        """, "Sorry, I couldn't get the weather: unknown city: Atlantis", label="tool raises"),
        T(3, AGENT_PRELUDE + """
            try:
                run_agent(base_url, key, "[loop] keep going", specs, handlers)
                outcome = "returned"
            except RuntimeError:
                outcome = "RuntimeError"
            result = [outcome, llm_stats(base_url, key)["attempts"]]
        """, ["RuntimeError", 8], label="stops at max_steps"),
        T(3, AGENT_PRELUDE + """
            try:
                run_agent(base_url, key, "[loop] keep going", specs, handlers, max_steps=3)
                outcome = "returned"
            except RuntimeError:
                outcome = "RuntimeError"
            result = [outcome, llm_stats(base_url, key)["attempts"]]
        """, ["RuntimeError", 3], label="custom max_steps"),
    ],
}


# ======================================================================= RAG
RAG_SOLUTION = '''import math
import re
from collections import Counter


def chunk_text(text: str, max_words: int, overlap: int) -> list[str]:
    if max_words <= 0 or overlap < 0 or overlap >= max_words:
        raise ValueError("need max_words > 0 and 0 <= overlap < max_words")
    words = text.split()
    chunks, start = [], 0
    while start < len(words):
        chunks.append(" ".join(words[start:start + max_words]))
        if start + max_words >= len(words):
            break
        start += max_words - overlap
    return chunks


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


class Retriever:
    """TF-IDF ranking: tf * log(N / df), so a term found in every document weighs nothing."""

    def __init__(self, docs: dict[str, str]):
        self.ids = list(docs)
        self.tf = {doc_id: Counter(_tokens(text)) for doc_id, text in docs.items()}
        df = Counter(term for counts in self.tf.values() for term in counts)
        self.idf = {term: math.log(len(docs) / n) for term, n in df.items()}

    def search(self, query: str, k: int = 3) -> list[str]:
        terms = set(_tokens(query))
        scored = []
        for order, doc_id in enumerate(self.ids):
            score = sum(self.tf[doc_id][t] * self.idf.get(t, 0.0) for t in terms)
            if score > 0:
                scored.append((-score, order, doc_id))
        return [doc_id for _, _, doc_id in sorted(scored)[:k]]


def evaluate(search, labeled: list, k: int) -> dict:
    recalls, reciprocal_ranks = [], []
    for query, relevant in labeled:
        results = search(query, k)[:k]
        hits = [r for r in results if r in relevant]
        recalls.append(len(set(hits)) / len(relevant))
        first = next((i for i, r in enumerate(results, start=1) if r in relevant), None)
        reciprocal_ranks.append(1 / first if first else 0.0)
    n = len(labeled)
    return {"recall_at_k": round(sum(recalls) / n, 3), "mrr": round(sum(reciprocal_ranks) / n, 3)}
'''

RAG_DOCS = '''
            docs = {
                "solar": "The solar panel installation on a residential roof needs a permit and a structural check.",
                "fees": "The permit fee schedule: permit fees depend on project value. Permit permit permit fee.",
                "fence": "The rules for a fence taller than two metres need a permit and a site plan.",
                "pool": "The swimming pool construction needs a permit, a safety barrier and a drainage plan.",
                "fence2": "The fence fence fence: fence permit for fence repairs.",
            }
'''

RAG = {
    "id": "ai-rag-retrieval",
    "title": "RAG: Chunk, Retrieve, Evaluate",
    "difficulty": "Medium",
    "category": "Applied AI",
    "tags": ["RAG", "search ranking", "evals"],
    "entry": "chunk_text",
    "mode": "script",
    "target_minutes": 40,
    "description": """
A government client wants an assistant that answers questions from its building-permit
regulations. Before any LLM is involved, the retrieval has to be good, and you have to be
able to **prove** it's good. Pure Python, no libraries.
""",
    "parts": [
        {
            "title": "Chunking",
            "description": """
```python
def chunk_text(text: str, max_words: int, overlap: int) -> list[str]: ...
```

Split `text` into chunks of at most `max_words` words, where each chunk starts with the
last `overlap` words of the previous one. Words are separated by any whitespace, and
chunks join words with single spaces. Stop once a chunk reaches the end of the text, so
no chunk is a tail of the previous one. Empty text gives `[]`. Raise `ValueError` unless
`max_words > 0` and `0 <= overlap < max_words`.

```python
chunk_text("a b c d e f g h i j", 4, 1)   # ["a b c d", "d e f g", "g h i j"]
```
""",
        },
        {
            "title": "Ranking",
            "description": """
```python
class Retriever:
    def __init__(self, docs: dict[str, str]): ...          # doc id -> text
    def search(self, query: str, k: int = 3) -> list[str]: ...   # best doc ids first
```

- Match words case-insensitively, ignoring punctuation (words are runs of letters and digits).
- A document ranks higher when it contains the query's words more often, and **rarer words
  matter more**. A word that appears in every document carries no weight at all.
- Documents with no weight are not returned. Return at most `k` ids; on a tie, keep the
  order the documents were given in.
""",
        },
        {
            "title": "Evaluation",
            "description": """
```python
def evaluate(search, labeled: list, k: int) -> dict: ...
# search(query, k) -> ranked doc ids; labeled = [(query, {relevant ids}), ...]
# -> {"recall_at_k": 0.75, "mrr": 0.583}
```

- **recall@k** for one query: the fraction of its relevant ids that appear in the top `k`
  results.
- **reciprocal rank** for one query: `1 / rank` of the first relevant result in the top `k`
  (rank starts at 1), or 0 if there is none.
- Return the mean of each over all queries, rounded to 3 decimals.
""",
        },
    ],
    "discussion": [
        "When would you switch from keyword ranking to embeddings, or combine both (hybrid search)? How would you decide with data?",
        "Where do labeled queries come from at a new client with no data? Who writes them?",
        "Retrieval looks good but answers are still wrong. How do you evaluate the generation step?",
        "Some regulations are confidential to certain departments. Where do access controls go in this pipeline?",
        "How should chunk size and overlap be chosen, and what goes wrong with tables and scanned PDFs?",
    ],
    "java_tip": """
*This tab names Python tools, which can hint at an approach.*

- `text.split()` with no argument splits on any run of whitespace and drops empty strings.
- `re.findall(r"[a-z0-9]+", text.lower())` returns all word tokens.
- `collections.Counter(tokens)` counts occurrences; a missing key gives 0.
- `math.log(x)` is the natural log.
- Sorting by several keys: `sorted(items, key=lambda x: (-score, order))`.
- `next((i for i, x in enumerate(xs, start=1) if cond), None)` finds the first match.
""",
    "starter": '''def chunk_text(text: str, max_words: int, overlap: int) -> list[str]:
    pass
''',
    "solution": RAG_SOLUTION,
    "tests": [
        T(1, 'result = chunk_text("a b c d e f g h i j", 4, 1)', ["a b c d", "d e f g", "g h i j"]),
        T(1, 'result = chunk_text("a b c d e f g h i j", 4, 0)', ["a b c d", "e f g h", "i j"]),
        T(1, 'result = [chunk_text("a b c d e", 3, 1), chunk_text("a b", 5, 2), chunk_text("", 5, 2)]',
          [["a b c", "c d e"], ["a b"], []], label="ends exactly / short / empty"),
        T(1, 'result = chunk_text("  one\\ntwo\\t three   four ", 2, 1)', ["one two", "two three", "three four"],
          label="any whitespace"),
        T(1, """
            outcomes = []
            for args in [(3, 3), (3, 5), (0, 0), (3, -1)]:
                try:
                    chunk_text("a b c d", *args)
                    outcomes.append("ok")
                except ValueError:
                    outcomes.append("ValueError")
            result = outcomes
        """, ["ValueError", "ValueError", "ValueError", "ValueError"], label="invalid sizes"),
        T(2, RAG_DOCS + """
            result = Retriever(docs).search("solar permit", 1)
        """, ["solar"], label="rare words beat repeated common words"),
        T(2, RAG_DOCS + """
            result = Retriever(docs).search("Swimming POOL barrier!!", 3)
        """, ["pool"], label="case and punctuation"),
        T(2, RAG_DOCS + """
            result = Retriever(docs).search("fence", 2)
        """, ["fence2", "fence"], label="more occurrences rank higher"),
        T(2, RAG_DOCS + """
            r = Retriever(docs)
            result = [r.search("the", 3), r.search("helicopter", 3)]
        """, [[], []], label="words in every doc / unknown words"),
        T(2, RAG_DOCS + """
            r = Retriever(docs)
            hits = r.search("permit fee drainage plan", 2)
            result = [len(hits), hits[0]]
        """, [2, "fees"], label="respects k"),
        T(3, """
            ranked = {"q1": ["a", "b", "c"], "q2": ["x", "y", "z"], "q3": ["m", "n", "o"]}
            search = lambda q, k: ranked[q][:k]
            labeled = [("q1", {"a"}), ("q2", {"y", "z"}), ("q3", {"p"})]
            result = evaluate(search, labeled, 3)
        """, {"recall_at_k": 0.667, "mrr": 0.5}),
        T(3, """
            ranked = {"q1": ["a", "b", "c"], "q2": ["x", "y", "z"]}
            search = lambda q, k: ranked[q]
            labeled = [("q1", {"c"}), ("q2", {"y", "q"})]
            result = [evaluate(search, labeled, 2), evaluate(search, labeled, 3)]
        """, [{"recall_at_k": 0.25, "mrr": 0.25}, {"recall_at_k": 0.75, "mrr": 0.417}],
          label="only the top k count"),
        T(3, RAG_DOCS + """
            labeled = [("solar roof", {"solar"}), ("drainage barrier", {"pool"}), ("site plan for a taller fence", {"fence"}),
                       ("project value", {"fees"})]
            result = evaluate(Retriever(docs).search, labeled, 1)
        """, {"recall_at_k": 1.0, "mrr": 1.0}, label="your retriever on a labeled set"),
    ],
}


# ============================================================ sensor pipeline
SENSOR_SOLUTION = '''import calendar
import math
import time
from collections import defaultdict

RANGES = {"temp_c": (-50, 60), "humidity": (0, 100), "pressure_kpa": (80, 110)}
HEADER = "timestamp,sensor_id,metric,value"


def _parse_line(line: str):
    """Return (reading, None) or (None, reason)."""
    fields = [f.strip() for f in line.split(",")]
    if len(fields) != 4 or not fields[1]:
        return None, "fields"
    stamp, sensor, metric, raw = fields
    try:
        ts = calendar.timegm(time.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ"))
    except ValueError:
        return None, "timestamp"
    if metric not in RANGES and metric != "temp_f":
        return None, "metric"
    try:
        value = float(raw)
    except ValueError:
        return None, "value"
    if not math.isfinite(value):
        return None, "value"
    if metric == "temp_f":
        metric, value = "temp_c", round((value - 32) * 5 / 9, 2)
    low, high = RANGES[metric]
    if not low <= value <= high:
        return None, "range"
    return {"ts": ts, "sensor": sensor, "metric": metric, "value": value}, None


def parse_readings(lines: list[str]) -> dict:
    latest, errors = {}, []
    for number, line in enumerate(lines, start=1):
        line = line.strip()
        if not line or line.startswith("#") or line == HEADER:
            continue
        reading, reason = _parse_line(line)
        if reason:
            errors.append([number, reason])
        else:
            latest[(reading["ts"], reading["sensor"], reading["metric"])] = reading  # last one wins
    readings = [latest[k] for k in sorted(latest)]
    return {"readings": readings, "errors": errors}


def summarize(readings: list[dict], window_s: int = 60) -> list[dict]:
    groups = defaultdict(list)
    for r in readings:
        groups[(r["sensor"], r["metric"], r["ts"] - r["ts"] % window_s)].append(r["value"])
    return [
        {"sensor": s, "metric": m, "window_start": w, "count": len(v),
         "min": min(v), "max": max(v), "avg": round(sum(v) / len(v), 2)}
        for (s, m, w), v in sorted(groups.items())
    ]


def find_gaps(readings: list[dict], max_gap_s: int) -> list[list]:
    times = defaultdict(set)
    for r in readings:
        times[r["sensor"]].add(r["ts"])
    gaps = []
    for sensor in sorted(times):
        ts = sorted(times[sensor])
        gaps += [[sensor, a, b] for a, b in zip(ts, ts[1:]) if b - a > max_gap_s]
    return gaps
'''

T0 = 1772359200  # 2026-03-01T10:00:00Z

SENSOR = {
    "id": "ai-sensor-pipeline",
    "title": "Sensor Data Pipeline",
    "difficulty": "Medium",
    "category": "Applied AI",
    "tags": ["data pipeline", "parsing", "validation", "time windows"],
    "entry": "parse_readings",
    "mode": "script",
    "target_minutes": 40,
    "description": """
A deployed system collects readings from field sensors (an energy site, a hospital
wing...) as CSV lines, and an AI forecasting model downstream needs clean data. Field
data is messy, and you're the one on site making it reliable. Pure Python.

```
timestamp,sensor_id,metric,value
2026-03-01T10:00:05Z,s-7,temp_c,21.5
```

Timestamps are UTC in exactly that format. Convert them to Unix epoch seconds (`ts`).
""",
    "parts": [
        {
            "title": "Parse and validate",
            "description": """
```python
def parse_readings(lines: list[str]) -> dict: ...
# -> {"readings": [{"ts": 1772359205, "sensor": "s-7", "metric": "temp_c", "value": 21.5}, ...],
#     "errors": [[line_number, reason], ...]}
```

- Ignore blank lines, lines starting with `#`, and the header line. Strip whitespace
  around lines and fields.
- Valid metrics: `temp_c`, `humidity`, `pressure_kpa`. `value` must be a finite number.
- Report invalid lines as `[line number (1-based), reason]`, in line order, using the first
  reason that applies, checked in this order: `"fields"` (not exactly 4 fields, or an
  empty sensor id), `"timestamp"`, `"metric"`, `"value"`.
- Return readings sorted by `(ts, sensor, metric)`.
""",
        },
        {
            "title": "Real-world data",
            "description": """
The field sends more than the spec says:

- **Duplicates.** The same `(ts, sensor, metric)` can arrive more than once. Keep the
  **last** one in input order. It isn't an error.
- **Fahrenheit.** Older sensors send `temp_f`. Convert to `temp_c`, rounded to 2 decimals.
- **Impossible values** are errors with reason `"range"` (checked after conversion):
  `temp_c` -50..60, `humidity` 0..100, `pressure_kpa` 80..110 (inclusive).
""",
        },
        {
            "title": "Aggregates and gaps",
            "description": """
```python
def summarize(readings: list[dict], window_s: int = 60) -> list[dict]: ...
def find_gaps(readings: list[dict], max_gap_s: int) -> list[list]: ...
```

- `summarize`: group readings by sensor, metric and time window (`window_start = ts - ts % window_s`).
  For each group return `{"sensor", "metric", "window_start", "count", "min", "max", "avg"}`,
  with `avg` rounded to 2 decimals, sorted by `(sensor, metric, window_start)`.
- `find_gaps`: for each sensor (any metric), find consecutive reading times more than
  `max_gap_s` apart. Return `[sensor, earlier_ts, later_ts]`, sorted by sensor then time.
""",
        },
    ],
    "discussion": [
        "Readings arrive as a live stream instead of a file. What changes, especially for late or out-of-order data?",
        "The site's network drops for hours at a time. How do you avoid losing data?",
        "Who should see the validation errors, and how do you stop bad sensors from silently corrupting the model's input?",
        "How would you store a year of readings from 50,000 sensors, and query them for the forecasting model?",
        "What would you monitor once this pipeline is live at the client?",
    ],
    "java_tip": """
*This tab names Python tools, which can hint at an approach.*

- `time.strptime(s, "%Y-%m-%dT%H:%M:%SZ")` parses (raising `ValueError` on bad input); `calendar.timegm(...)` turns that into UTC epoch seconds.
- `float("abc")` raises `ValueError`; `float("nan")` doesn't, so check with `math.isfinite`.
- `enumerate(lines, start=1)` gives 1-based line numbers.
- A dict keyed by a tuple `(ts, sensor, metric)` naturally keeps the last value written.
- `zip(ts, ts[1:])` walks consecutive pairs.
""",
    "starter": '''def parse_readings(lines: list[str]) -> dict:
    pass
''',
    "solution": SENSOR_SOLUTION,
    "tests": [
        T(1, """
            lines = [
                "timestamp,sensor_id,metric,value",
                "2026-03-01T10:00:05Z,s-7,temp_c,21.5",
                "2026-03-01T10:00:00Z,s-2,humidity,40",
                "2026-03-01T10:00:00Z,s-1,pressure_kpa,101.3",
            ]
            result = parse_readings(lines)
        """, {"readings": [
            {"ts": T0, "sensor": "s-1", "metric": "pressure_kpa", "value": 101.3},
            {"ts": T0, "sensor": "s-2", "metric": "humidity", "value": 40.0},
            {"ts": T0 + 5, "sensor": "s-7", "metric": "temp_c", "value": 21.5},
        ], "errors": []}, label="sorted, epoch seconds"),
        T(1, """
            lines = [
                "# exported from gateway 3",
                "",
                "  2026-03-01T10:00:00Z , s-1 , temp_c , 20  ",
                "2026-03-01T10:00:00Z,s-1,temp_c",
                "2026-03-01 10:00:00,s-1,temp_c,20",
                "2026-03-01T10:00:00Z,s-1,wind,3",
                "2026-03-01T10:00:00Z,s-1,humidity,high",
                "2026-03-01T10:00:00Z,,humidity,5",
                "2026-03-01T10:00:00Z,s-1,humidity,nan",
                "2026-02-30T10:00:00Z,s-1,humidity,5",
                "2026-03-01T10:00:00Z,s-1,humidity,5,extra",
            ]
            result = parse_readings(lines)
        """, {"readings": [{"ts": T0, "sensor": "s-1", "metric": "temp_c", "value": 20.0}],
              "errors": [[4, "fields"], [5, "timestamp"], [6, "metric"], [7, "value"], [8, "fields"],
                         [9, "value"], [10, "timestamp"], [11, "fields"]]}, label="errors and whitespace"),
        T(1, 'result = parse_readings([])', {"readings": [], "errors": []}),
        T(2, """
            lines = [
                "2026-03-01T10:00:00Z,s-1,temp_c,20",
                "2026-03-01T10:00:00Z,s-1,temp_c,21",
                "2026-03-01T10:00:00Z,s-1,humidity,30",
                "2026-03-01T10:00:00Z,s-1,temp_c,22",
            ]
            result = parse_readings(lines)
        """, {"readings": [{"ts": T0, "sensor": "s-1", "metric": "humidity", "value": 30.0},
                           {"ts": T0, "sensor": "s-1", "metric": "temp_c", "value": 22.0}],
              "errors": []}, label="duplicates: last one wins"),
        T(2, """
            lines = ["2026-03-01T10:00:00Z,old-3,temp_f,98.6", "2026-03-01T10:01:00Z,old-3,temp_f,-40"]
            result = parse_readings(lines)
        """, {"readings": [{"ts": T0, "sensor": "old-3", "metric": "temp_c", "value": 37.0},
                           {"ts": T0 + 60, "sensor": "old-3", "metric": "temp_c", "value": -40.0}],
              "errors": []}, label="fahrenheit"),
        T(2, """
            lines = [
                "2026-03-01T10:00:00Z,s-1,temp_c,60",
                "2026-03-01T10:00:00Z,s-2,temp_c,60.01",
                "2026-03-01T10:00:00Z,s-3,humidity,-1",
                "2026-03-01T10:00:00Z,s-4,pressure_kpa,79.9",
                "2026-03-01T10:00:00Z,s-5,temp_f,300",
                "2026-03-01T10:00:00Z,s-6,humidity,100",
            ]
            result = parse_readings(lines)
        """, {"readings": [{"ts": T0, "sensor": "s-1", "metric": "temp_c", "value": 60.0},
                           {"ts": T0, "sensor": "s-6", "metric": "humidity", "value": 100.0}],
              "errors": [[2, "range"], [3, "range"], [4, "range"], [5, "range"]]}, label="range checks"),
        T(3, f"""
            readings = [
                {{"ts": {T0}, "sensor": "s-1", "metric": "temp_c", "value": 20.0}},
                {{"ts": {T0 + 30}, "sensor": "s-1", "metric": "temp_c", "value": 22.0}},
                {{"ts": {T0 + 59}, "sensor": "s-1", "metric": "temp_c", "value": 21.0}},
                {{"ts": {T0 + 60}, "sensor": "s-1", "metric": "temp_c", "value": 25.0}},
                {{"ts": {T0 + 10}, "sensor": "s-1", "metric": "humidity", "value": 40.0}},
                {{"ts": {T0 + 5}, "sensor": "a-9", "metric": "temp_c", "value": 18.333}},
            ]
            result = summarize(readings)
        """, [
            {"sensor": "a-9", "metric": "temp_c", "window_start": T0, "count": 1, "min": 18.333, "max": 18.333, "avg": 18.33},
            {"sensor": "s-1", "metric": "humidity", "window_start": T0, "count": 1, "min": 40.0, "max": 40.0, "avg": 40.0},
            {"sensor": "s-1", "metric": "temp_c", "window_start": T0, "count": 3, "min": 20.0, "max": 22.0, "avg": 21.0},
            {"sensor": "s-1", "metric": "temp_c", "window_start": T0 + 60, "count": 1, "min": 25.0, "max": 25.0, "avg": 25.0},
        ], label="1-minute windows"),
        T(3, f"""
            readings = [{{"ts": {T0} + s, "sensor": "s-1", "metric": "temp_c", "value": 20.0}} for s in (0, 100, 400, 700)]
            result = [summarize(readings, window_s=300)[1]["window_start"] - {T0}, len(summarize(readings, window_s=300))]
        """, [300, 3], label="custom window"),
        T(3, f"""
            readings = [
                {{"ts": {T0}, "sensor": "s-2", "metric": "temp_c", "value": 1.0}},
                {{"ts": {T0 + 600}, "sensor": "s-2", "metric": "humidity", "value": 1.0}},
                {{"ts": {T0 + 60}, "sensor": "s-1", "metric": "temp_c", "value": 1.0}},
                {{"ts": {T0}, "sensor": "s-1", "metric": "temp_c", "value": 1.0}},
                {{"ts": {T0 + 400}, "sensor": "s-1", "metric": "humidity", "value": 1.0}},
                {{"ts": {T0 + 700}, "sensor": "s-1", "metric": "temp_c", "value": 1.0}},
                {{"ts": {T0 + 760}, "sensor": "s-1", "metric": "temp_c", "value": 1.0}},
            ]
            result = [[s, a - {T0}, b - {T0}] for s, a, b in find_gaps(readings, 120)]
        """, [["s-1", 60, 400], ["s-1", 400, 700], ["s-2", 0, 600]], label="gaps across metrics"),
        T(3, f"""
            readings = [{{"ts": {T0} + s, "sensor": "s-1", "metric": "temp_c", "value": 1.0}} for s in (0, 120, 240)]
            result = [find_gaps(readings, 120), find_gaps([], 60)]
        """, [[], []], label="exactly max_gap is fine"),
    ],
}


PROBLEMS = [LLM_CLIENT, AGENT, RAG, SENSOR]
