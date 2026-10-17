"""Per-part editorials for the Applied AI problems."""

PART_EDITORIALS = {
    # ------------------------------------------------------------ LLM client
    "ai-llm-client": [
        """
**Idea:** one `POST {base_url}/llm/v1/messages` with the three headers, then pull the text out of
the reply's `content` list.

**Steps:** build `{"model": ..., "max_tokens": 1024, "messages": [{"role": "user", "content": prompt}]}`
and add `"system": system` only when it's given. Send it with
`requests.post(url, headers=..., json=body, timeout=30)`: `json=` serialises and sets the encoding,
and `timeout=` stops a hung server hanging your caller. Return
`"".join(b["text"] for b in content if b["type"] == "text")`.

**Pitfalls:** a missing `x-api-key` is a 401 and a missing `anthropic-version` is a 400. The mock's
reply starts with a `thinking` block and splits the text over two `text` blocks, so
`content[0]["text"]` fails. Putting the system prompt in `messages` as `role: "system"` is rejected.
""",
        """
**Idea:** split status codes into retryable (429, 500, 529: the server's problem, likely transient)
and everything else (your request is wrong, so retrying can't help).

**Steps:** move the `requests.post` into a loop of `MAX_RETRIES + 1` attempts. Stop on success, on a
non-retryable status, or on the last attempt. Between attempts sleep
`float(resp.headers["retry-after"])` if the header exists, else exponential backoff
`0.05 * 2 ** attempt` (0.05, 0.1, 0.2, 0.4 s). After the loop, raise if the status isn't 200, using
the error body's `error.type` and `error.message`.

**Pitfalls:** retrying the 400 (the test expects exactly 1 request); an off-by-one that makes 4 or 6
attempts instead of 5 (`[overloaded:10]`); returning `None` instead of raising when every attempt
fails; long sleeps that blow the time budget. `retry-after` is a string, so convert it.
""",
        """
**Idea:** don't trust the model's output: find the JSON, parse it, validate every field, and if it's
wrong, tell the model what's wrong in the same conversation.

**Steps:** a helper returns `(invoice, problem)`. Find the object with
`re.search(r"\\{.*\\}", reply, re.DOTALL)` (handles code fences and surrounding prose), `json.loads`
it, then check: `vendor` non-empty `str`; `total` an int or float but not a `bool`, and >= 0;
`due_date` passes `date.fromisoformat` and matches `\\d{4}-\\d{2}-\\d{2}`. Return `float(total)`. On
failure append `{"role": "assistant", "content": reply}` and a user message naming the problem, then
call again. You need a lower-level call that takes a `messages` list, built on part 2's retrying
`_post`.

**Pitfalls:** starting a fresh conversation for the re-ask (the missing-field case only gets fixed on
the second user turn, and must take exactly 2 requests); `json.loads` on the raw reply; a 4th
request before raising `ValueError`.
""",
        """
**Idea:** the work is I/O-bound (waiting on HTTP), so threads give real concurrency.
`ThreadPoolExecutor(max_workers=max_concurrency)` is both the pool and the concurrency cap.

**Steps:** `with ThreadPoolExecutor(max_workers=max_concurrency) as pool:` then
`return list(pool.map(lambda p: complete(base_url, api_key, p), prompts))`. `map` returns results
in input order whatever order they finish in. Reusing `complete` means retries still apply.

**Complexity:** about `ceil(n / max_concurrency)` request durations: 12 prompts at 0.25 s with 4
workers is ~0.75 s, versus 3 s sequentially.

**Pitfalls:** collecting with `as_completed` and returning finish order; starting one thread per
prompt (12 in flight breaks the cap); ignoring `max_concurrency` (the `max_concurrency=1` test
checks a peak of exactly 1). A `threading.Semaphore` around the call also caps it, but the pool is
simpler.
""",
    ],
    # ------------------------------------------------------------ agent loop
    "ai-agent-loop": [
        """
**Idea:** an agent is a loop: call the model; if it asks for a tool (`stop_reason == "tool_use"`),
run it and send the result back; repeat until it answers with text.

**Steps:** start with `messages = [{"role": "user", "content": task}]` and pass `tool_specs` as the
request's `tools`. When the reply wants a tool, append
`{"role": "assistant", "content": reply["content"]}` unchanged, call
`handlers[block["name"]](**block["input"])`, and append a **user** message whose content is
`[{"type": "tool_result", "tool_use_id": block["id"], "content": output}]`. When `stop_reason` is
anything else, return the joined text of all `text` blocks.

**Pitfalls:** OpenAI-style `role: "tool"` messages (rejected: only user and assistant); a
`tool_use_id` that doesn't match the block's `id`; dropping the assistant turn so roles stop
alternating. With no tool needed, the reply has a `thinking` block and split text: join the text
blocks, in 1 request.
""",
        """
**Idea:** generalise part 1: handle *every* `tool_use` block in a reply, and keep looping, because
each new round sees the whole history.

**Steps:** `tool_uses = [b for b in reply["content"] if b["type"] == "tool_use"]`; build one
`tool_result` per block and send them **all in a single user message**. Convert dict results with
`json.dumps(output)` (keep strings as they are), since `content` must be a string. The chained task
then takes 3 requests: permit lookup, inspector lookup, final answer.

**Pitfalls:** answering only the first `tool_use` (the API returns 400 because an id has no result);
one user message per result (two user turns in a row breaks alternation); `str(dict)`, which gives
single-quoted Python, not JSON, so the model can't read the permit record.
""",
        """
**Idea:** a production agent must survive bad tools and bad models. A failing tool becomes
information for the model; a model that never stops is cut off.

**Steps:** wrap only the handler call in `try/except Exception as exc` and on failure return
`{"type": "tool_result", "tool_use_id": ..., "content": str(exc), "is_error": True}`, so the model
can explain the problem ("unknown city: Atlantis"). Turn the loop into
`for _ in range(max_steps):`, one model request per iteration, and `raise RuntimeError` after it.

**Pitfalls:** an off-by-one that makes `max_steps + 1` requests (the tests count exactly 8, and 3 with
`max_steps=3`); returning a string instead of raising; `"is_error": "true"` (it must be the boolean);
a try/except around the whole loop that swallows the `RuntimeError` or API errors.
""",
    ],
    # ------------------------------------------------------------------- RAG
    "ai-rag-retrieval": [
        """
**Idea:** a sliding window over the word list that advances by `step = max_words - overlap`.

**Steps:** validate first: `max_words > 0` and `0 <= overlap < max_words`, else `ValueError`.
`words = text.split()`. From `start = 0`, append `" ".join(words[start:start + max_words])`; if
`start + max_words >= len(words)` that chunk reached the end, so stop; otherwise `start += step`.

**Complexity:** O(total words emitted), roughly O(n * max_words / step).

**Pitfalls:** `split(" ")` (empty strings from runs of spaces, tabs and newlines kept); a stray
tail chunk: `"a b c d e", 3, 1` must give `["a b c", "c d e"]`, not a third `"e"`; `overlap ==
max_words` (step 0, an infinite loop) and negative overlap must raise; empty text gives `[]`.
""",
        """
**Idea:** TF-IDF. Score a document by `sum(tf(term, doc) * log(N / df(term)))` over the query's
terms. A term in all N documents gets `log(1) = 0`, so it adds nothing.

**Steps:** tokenize with `re.findall(r"[a-z0-9]+", text.lower())`. In `__init__`, keep a
`Counter` per doc (tf) and a `Counter` of document frequency, and precompute `idf`. In `search`,
score each doc over `set(query tokens)` using `idf.get(t, 0.0)` for unknown words, keep only
`score > 0`, sort by `(-score, original order)`, and slice `[:k]`. `heapq.nlargest(k, ...)` with the
same key avoids a full sort on large corpora.

**Complexity:** O(total tokens) to build; O(docs * query terms) per search.

**Pitfalls:** raw counts without IDF (the doc saying "permit" five times beats "solar"); returning
zero-score docs for "the" or "helicopter"; `str.split` keeping `"barrier!!"`; an unstable tie order.
""",
        """
**Idea:** two standard retrieval metrics. recall@k asks "did we find the relevant docs?"; MRR asks
"how high was the first one?".

**Steps:** for each `(query, relevant)`, take `results = search(query, k)[:k]`. Recall is
`len({r for r in results if r in relevant}) / len(relevant)`. The first hit's rank comes from
`next((i for i, r in enumerate(results, start=1) if r in relevant), None)`; reciprocal rank is
`1 / rank`, or 0 with no hit. Average each list over all queries, then `round(..., 3)`.

**Complexity:** O(queries * k) plus the search calls.

**Pitfalls:** trusting `search` to respect `k` (the test's search ignores it, so slice yourself);
dividing recall by `k` instead of `len(relevant)`; 0-based ranks; rounding each query's score
before averaging.
""",
    ],
    # ------------------------------------------------------------ sensor pipeline
    "ai-sensor-pipeline": [
        """
**Idea:** a per-line validator that returns either a reading or the first failing reason, checked
in the spec's order.

**Steps:** `for number, line in enumerate(lines, start=1)`; strip, then skip blanks, `#` comments and
the header. `fields = [f.strip() for f in line.split(",")]`; need exactly 4 and a non-empty sensor
(`"fields"`). Parse with `time.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ")` and convert with
`calendar.timegm` (`"timestamp"` on `ValueError`). Then the metric set, then `float(raw)` plus
`math.isfinite` (`"value"`). Sort readings by `(ts, sensor, metric)`.

**Complexity:** O(n log n) for the sort.

**Pitfalls:** `time.mktime` (local time, not UTC); numbering only non-skipped lines (numbers count
every line); `float("nan")` parses, so it needs the finite check; `2026-02-30` must fail as
`"timestamp"`; a 5th field is `"fields"`; `"40"` must become `40.0`.
""",
        """
**Idea:** extend part 1's parser with three rules: dedupe, unit conversion, and range checks.

**Steps:** store valid readings in a dict keyed by `(ts, sensor, metric)`: later lines overwrite
earlier ones, so the last one wins for free; at the end, emit `[latest[k] for k in sorted(latest)]`.
Accept `temp_f` as a metric, and after the value check convert it with
`metric, value = "temp_c", round((value - 32) * 5 / 9, 2)`. Then look up the `(low, high)` range
for the metric and report `"range"` unless `low <= value <= high`.

**Pitfalls:** keeping the first duplicate; reporting duplicates as errors; checking the range before
converting (`300` F is 148.89 C, out of range; `-40` F is a valid -40.0); exclusive bounds (60 and
100 are valid, 60.01 is not); keying on `temp_f` so it doesn't dedupe against `temp_c`.
""",
        """
**Idea:** both are group-by problems. Bucket with `defaultdict(list)`, then compute per bucket.

**Steps:** `summarize`: key each value by `(sensor, metric, ts - ts % window_s)`, then build rows from
`sorted(groups.items())` with `count`, `min`, `max` and `avg = round(sum(v) / len(v), 2)`.
`find_gaps`: collect a `set` of timestamps per sensor across all metrics, sort them, and walk
consecutive pairs with `zip(ts, ts[1:])`, keeping those where `b - a > max_gap_s`. Iterate sensors
in sorted order.

**Complexity:** O(n log n) for the sorts.

**Pitfalls:** an off-by-one at the boundary (second 59 is in the first window, 60 starts the next);
rounding `min`/`max` (only `avg` is rounded, so 18.333 stays); gaps per `(sensor, metric)` instead
of per sensor; `>=` instead of `>` (exactly `max_gap_s` apart is fine); empty input gives `[]`.
""",
    ],
}
