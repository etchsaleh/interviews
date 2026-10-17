"""Real-world problems: grounded scenarios instead of puzzles (multi-part, script tests).

Each one is the kind of task a deployed engineer gets on site: messy inputs, business
rules stated by a customer, edge cases that matter, and data big enough that the obvious
O(n²) approach is too slow.
"""
from problems.multipart import T

T0 = 1772359200  # 2026-03-01T10:00:00Z


# ================================================================ log triage
LOG_SOLUTION = '''import calendar
import math
import re
import time
from collections import defaultdict

LINE = re.compile(r"(\\S+) (GET|POST|PUT|PATCH|DELETE) (\\S+) (\\d{3}) (\\d+)ms(?:\\s.*)?")


def parse_log(lines: list[str]) -> dict:
    entries, skipped = [], 0
    for line in lines:
        line = line.strip()
        if not line:
            continue
        match = LINE.fullmatch(line)
        try:
            ts = calendar.timegm(time.strptime(match.group(1), "%Y-%m-%dT%H:%M:%SZ")) if match else None
        except ValueError:
            ts = None
        if ts is None:
            skipped += 1
            continue
        entries.append({"ts": ts, "method": match.group(2), "path": match.group(3),
                        "status": int(match.group(4)), "ms": int(match.group(5))})
    return {"entries": entries, "skipped": skipped}


def _template(path: str) -> str:
    path = path.split("?", 1)[0]
    return "/".join(":id" if part.isdigit() else part for part in path.split("/"))


def endpoint_stats(entries: list[dict]) -> dict:
    groups = defaultdict(list)
    for e in entries:
        groups[f"{e['method']} {_template(e['path'])}"].append(e)
    stats = {}
    for key, group in groups.items():
        durations = sorted(e["ms"] for e in group)
        errors = sum(e["status"] >= 500 for e in group)
        stats[key] = {
            "count": len(group),
            "errors": errors,
            "error_rate": round(errors / len(group), 3),
            "p95_ms": durations[math.ceil(0.95 * len(durations)) - 1],
        }
    return stats


def find_incidents(entries: list[dict], window_s: int = 60, threshold: float = 0.5,
                   min_requests: int = 5) -> list[dict]:
    windows = defaultdict(lambda: [0, 0])          # window start -> [requests, errors]
    for e in entries:
        counts = windows[e["ts"] - e["ts"] % window_s]
        counts[0] += 1
        counts[1] += e["status"] >= 500
    incidents = []
    for start in sorted(windows):
        requests, errors = windows[start]
        if requests < min_requests or errors / requests < threshold:
            continue
        if incidents and incidents[-1]["end"] == start:      # continues the previous incident
            incidents[-1]["end"] = start + window_s
            incidents[-1]["requests"] += requests
            incidents[-1]["errors"] += errors
        else:
            incidents.append({"start": start, "end": start + window_s, "requests": requests, "errors": errors})
    return incidents
'''


def _e(offset, status, ms=10, method="GET", path="/api/permits/1"):
    return {"ts": T0 + offset, "method": method, "path": path, "status": status, "ms": ms}


INCIDENT_ENTRIES = (
    [_e(s, 500) for s in (1, 2, 3, 4)] + [_e(s, 200) for s in (5, 6)]          # minute 0: 6 req, 4 errors
    + [_e(60 + s, 503) for s in (1, 2, 3)] + [_e(70, 200), _e(71, 200)]        # minute 1: 5 req, 3 errors
    + [_e(120 + s, 200) for s in range(9)] + [_e(130, 500)]                    # minute 2: 10 req, 1 error
    + [_e(180 + s, 500) for s in range(3)]                                     # minute 3: too few requests
    + [_e(240 + s, 502) for s in range(5)]                                     # minute 4: 5 req, 5 errors
)

LOG = {
    "id": "rw-log-triage",
    "title": "Log Triage: Why Is the App Slow?",
    "difficulty": "Medium",
    "category": "Real-world",
    "tags": ["parsing", "regex", "aggregation", "percentiles", "time windows"],
    "entry": "parse_log",
    "mode": "script",
    "target_minutes": 40,
    "timeout": 25,
    "description": """
You're on site at a client. Their permit portal "has been slow and flaky since this
morning", and you have the web server's access log. Build the tools to find out what's
wrong. Each line looks like this (anything after the duration is extra and ignored):

```
2026-03-01T10:00:05Z GET /api/permits/17 200 123ms user=u42
```

Timestamps are UTC. Convert them to Unix epoch seconds (`ts`).
""",
    "parts": [
        {
            "title": "Parse",
            "description": """
```python
def parse_log(lines: list[str]) -> dict: ...
# -> {"entries": [{"ts": 1772359205, "method": "GET", "path": "/api/permits/17", "status": 200, "ms": 123}, ...],
#     "skipped": 2}
```

- Strip whitespace around lines; ignore blank lines.
- Methods are `GET`, `POST`, `PUT`, `PATCH`, `DELETE`. The status is a 3-digit number and the
  duration is digits followed by `ms`.
- Lines that don't fit (missing fields, a bad timestamp, an unknown method, a bad status or
  duration) are **skipped and counted**. Keep valid entries in input order.
""",
        },
        {
            "title": "Per-endpoint stats",
            "description": """
```python
def endpoint_stats(entries: list[dict]) -> dict: ...
# -> {"GET /api/permits/:id": {"count": 3, "errors": 1, "error_rate": 0.333, "p95_ms": 300}, ...}
```

- Group by method and **endpoint template**: drop any query string (`?...`) and replace path
  segments made only of digits with `:id` (`/api/permits/17` → `/api/permits/:id`).
- `errors` counts **5xx** responses (a 404 is not a server error). `error_rate` is
  `errors / count` rounded to 3 decimals.
- `p95_ms` uses the nearest-rank method: sort the durations and take the value at position
  `ceil(0.95 × n)`, counting from 1.
""",
        },
        {
            "title": "Find the incidents",
            "description": """
```python
def find_incidents(entries, window_s=60, threshold=0.5, min_requests=5) -> list[dict]: ...
# -> [{"start": 1772359200, "end": 1772359320, "requests": 11, "errors": 7}, ...]
```

- Split time into windows aligned to `window_s` (`window_start = ts - ts % window_s`).
- A window is **bad** when it has at least `min_requests` requests and at least `threshold`
  of them are 5xx.
- Consecutive bad windows (each starting where the previous one ends) form **one incident**:
  `start` is its first window's start, `end` is its last window's end, and `requests` and
  `errors` are totals over the incident.
- Entries may be out of order. Return incidents sorted by `start`. A full day of logs is
  hundreds of thousands of lines, so keep it fast.
""",
        },
    ],
    "discussion": [
        "The client asks what caused the incident. What else would you look at besides this log?",
        "How would you turn this into an alert that pages someone, without paging on every blip?",
        "Why p95 instead of the average? When would you look at p99 or the max?",
        "The log is 50 GB and still growing. How do you process it, and how do you keep the stats live?",
    ],
    "java_tip": """
*This tab names Python tools, which can hint at an approach.* See also [Python Reference](/reference) §15–17.

- `re.compile(r"...").fullmatch(line)` returns `None` when the line doesn't fit; `m.group(1)` gets a capture.
- `calendar.timegm(time.strptime(s, "%Y-%m-%dT%H:%M:%SZ"))` gives UTC epoch seconds; bad dates raise `ValueError`.
- `defaultdict(list)` groups; `sorted(...)` + `math.ceil` computes the percentile index.
- `True` counts as 1 when you add it: `errors += status >= 500`.
""",
    "starter": '''def parse_log(lines: list[str]) -> dict:
    pass
''',
    "solution": LOG_SOLUTION,
    "tests": [
        T(1, """
            lines = [
                "2026-03-01T10:00:05Z GET /api/permits/17 200 123ms",
                "2026-03-01T10:00:06Z POST /api/permits 201 87ms user=u42",
                "",
                "garbage line",
                "2026-03-01T10:00:07Z GET /api/permits/17 abc 12ms",
                "2026-03-01T10:00:08Z FETCH /x 200 1ms",
                "2026-13-01T10:00:08Z GET /x 200 1ms",
                "2026-03-01T10:00:09Z GET /health 200 3",
                "  2026-03-01T10:00:10Z DELETE /api/permits/9 500 1500ms  ",
            ]
            result = parse_log(lines)
        """, {"entries": [
            {"ts": T0 + 5, "method": "GET", "path": "/api/permits/17", "status": 200, "ms": 123},
            {"ts": T0 + 6, "method": "POST", "path": "/api/permits", "status": 201, "ms": 87},
            {"ts": T0 + 10, "method": "DELETE", "path": "/api/permits/9", "status": 500, "ms": 1500},
        ], "skipped": 5}, label="valid, extra fields, and five kinds of bad line"),
        T(1, 'result = parse_log([])', {"entries": [], "skipped": 0}, label="empty log"),
        T(1, """
            result = parse_log(["2026-03-01T10:00:05Z GET /a 200 12msx", "2026-03-01T10:00:05Z GET /a 2000 1ms",
                                "2026-03-01T10:00:05Z get /a 200 1ms", "2026-03-01T10:00:05Z GET /a 200 -1ms"])["skipped"]
        """, 4, label="near misses are skipped"),
        T(1, """
            lines = [f"2026-03-01T{h:02d}:{m:02d}:00Z GET /api/permits/{i} 200 {i % 900}ms"
                     for i in range(50_000) for h, m in [divmod(i % 1440, 60)]]
            out = parse_log(lines)
            result = [len(out["entries"]), out["skipped"], out["entries"][-1]["ms"]]
        """, [50_000, 0, 49_999 % 900], label="50,000 lines", time_limit_ms=4000),
        T(2, """
            entries = [
                {"ts": 1, "method": "GET", "path": "/api/permits/17", "status": 200, "ms": 100},
                {"ts": 2, "method": "GET", "path": "/api/permits/18", "status": 500, "ms": 300},
                {"ts": 3, "method": "GET", "path": "/api/permits/19?expand=docs", "status": 200, "ms": 200},
                {"ts": 4, "method": "POST", "path": "/api/permits", "status": 201, "ms": 50},
                {"ts": 5, "method": "GET", "path": "/health", "status": 200, "ms": 5},
            ]
            result = endpoint_stats(entries)
        """, {"GET /api/permits/:id": {"count": 3, "errors": 1, "error_rate": 0.333, "p95_ms": 300},
              "POST /api/permits": {"count": 1, "errors": 0, "error_rate": 0.0, "p95_ms": 50},
              "GET /health": {"count": 1, "errors": 0, "error_rate": 0.0, "p95_ms": 5}}, label="templates and query strings"),
        T(2, """
            entries = [{"ts": i, "method": "GET", "path": "/a", "status": 200, "ms": ms} for i, ms in enumerate(range(20, 0, -1))]
            entries += [{"ts": 99, "method": "GET", "path": "/a", "status": 404, "ms": 1}]
            stats = endpoint_stats(entries)["GET /a"]
            result = [stats["p95_ms"], stats["errors"]]
        """, [19, 0], label="p95 by nearest rank (not the max); 404 is not an error"),
        T(2, """
            twenty = [{"ts": i, "method": "GET", "path": "/b", "status": 200, "ms": i} for i in range(1, 21)]
            one = [{"ts": 0, "method": "GET", "path": "/c", "status": 200, "ms": 7}]
            result = [endpoint_stats(twenty)["GET /b"]["p95_ms"], endpoint_stats(one)["GET /c"]["p95_ms"]]
        """, [19, 7], label="p95 when 0.95 × n is a whole number; a single request"),
        T(2, """
            entries = [{"ts": 1, "method": "GET", "path": "/api/v2/users/42/docs/7", "status": 503, "ms": 9}]
            result = endpoint_stats(entries)
        """, {"GET /api/v2/users/:id/docs/:id": {"count": 1, "errors": 1, "error_rate": 1.0, "p95_ms": 9}},
          label="only all-digit segments become :id"),
        T(3, """
            import random
            entries = INCIDENT_ENTRIES[:]
            random.Random(4).shuffle(entries)
            result = find_incidents(entries)
        """.replace("INCIDENT_ENTRIES", repr(INCIDENT_ENTRIES)), [
            {"start": T0, "end": T0 + 120, "requests": 11, "errors": 7},
            {"start": T0 + 240, "end": T0 + 300, "requests": 5, "errors": 5},
        ], label="merging, minimum volume, out-of-order input"),
        T(3, """
            result = [find_incidents([]), find_incidents(ENTRIES, window_s=300), find_incidents(ENTRIES, threshold=0.9)]
        """.replace("ENTRIES", repr(INCIDENT_ENTRIES)), [
            [], [{"start": T0, "end": T0 + 300, "requests": 29, "errors": 16}],
            [{"start": T0 + 240, "end": T0 + 300, "requests": 5, "errors": 5}],
        ], label="window size and threshold"),
        T(3, """
            entries = [{"ts": 1772359200 + m * 60 + i, "method": "GET", "path": "/a",
                        "status": 500 if 500 <= m < 510 else 200, "ms": 5}
                       for m in range(4000) for i in range(50)]
            result = find_incidents(entries)
        """, [{"start": T0 + 30_000, "end": T0 + 30_600, "requests": 500, "errors": 500}],
          label="200,000 entries: one pass, not a scan per window", time_limit_ms=2000),
    ],
}


# ============================================================= reconciliation
RECON_SOLUTION = '''import csv
import io
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation


def _cents(text: str) -> int:
    text = text.strip().replace(",", "")
    negative = text.startswith("(") and text.endswith(")")
    if negative:
        text = text[1:-1]
    value = Decimal(text) * 100            # raises InvalidOperation for junk
    if value != value.to_integral_value():
        raise ValueError("more than 2 decimals")
    return -int(value) if negative else int(value)


def parse_bank(csv_text: str) -> dict:
    records, errors = [], []
    for row_number, row in enumerate(csv.DictReader(io.StringIO(csv_text)), start=2):
        try:
            day = datetime.strptime(row["Date"].strip(), "%d/%m/%Y").date()
            cents = _cents(row["Amount"])
        except (ValueError, InvalidOperation, AttributeError):
            errors.append(row_number)
            continue
        records.append({"date": day.isoformat(), "description": row["Description"].strip(), "amount_cents": cents})
    return {"records": records, "errors": errors}


def parse_ledger(csv_text: str) -> list[dict]:
    return [{"id": row["id"], "date": row["date"], "amount_cents": _cents(row["amount"]),
             "reference": row["reference"]}
            for row in csv.DictReader(io.StringIO(csv_text))]


def reconcile(bank: list[dict], ledger: list[dict], date_tolerance_days: int = 0) -> dict:
    # Exact pass: index unmatched ledger entries by (date, amount), in ledger order.
    by_key = {}
    for entry in ledger:
        by_key.setdefault((entry["date"], entry["amount_cents"]), []).append(entry)
    used = set()
    matched, leftover = [], []
    for i, record in enumerate(bank):
        candidates = by_key.get((record["date"], record["amount_cents"]), [])
        while candidates and candidates[0]["id"] in used:
            candidates.pop(0)
        if candidates:
            entry = candidates.pop(0)
            used.add(entry["id"])
            matched.append([i, entry["id"]])
        else:
            leftover.append(i)

    # Tolerance pass: same amount, date within N days. Prefer a reference match, then the
    # closest date, then ledger order.
    probable, unmatched_bank = [], []
    by_amount = {}
    for order, entry in enumerate(ledger):
        if entry["id"] not in used:
            by_amount.setdefault(entry["amount_cents"], []).append((order, entry))
    for i in leftover:
        record = bank[i]
        day = date.fromisoformat(record["date"])
        best = None
        for order, entry in by_amount.get(record["amount_cents"], []) if date_tolerance_days else []:
            if entry["id"] in used:
                continue
            gap = abs((date.fromisoformat(entry["date"]) - day).days)
            if gap > date_tolerance_days:
                continue
            ref_match = entry["reference"].lower() in record["description"].lower()
            rank = (not ref_match, gap, order)
            if best is None or rank < best[0]:
                best = (rank, entry)
        if best:
            used.add(best[1]["id"])
            probable.append([i, best[1]["id"]])
        else:
            unmatched_bank.append(i)

    return {
        "matched": matched,
        "probable": probable,
        "unmatched_bank": unmatched_bank,
        "unmatched_ledger": [e["id"] for e in ledger if e["id"] not in used],
    }
'''


def _b(day, cents, desc="x"):
    return {"date": day, "description": desc, "amount_cents": cents}


def _l(id_, day, cents, ref="R"):
    return {"id": id_, "date": day, "amount_cents": cents, "reference": ref}


RECON = {
    "id": "rw-reconcile",
    "title": "Payment Reconciliation",
    "difficulty": "Medium",
    "category": "Real-world",
    "tags": ["CSV", "Decimal", "dates", "matching rules"],
    "entry": "reconcile",
    "mode": "script",
    "target_minutes": 45,
    "description": """
A government finance office reconciles its bank statement against its accounting ledger
by hand every month. They want a tool that does the matching, and shows the accountants
only what's left.

Amounts are money: work in **integer cents**, never floats.
""",
    "parts": [
        {
            "title": "Parse both exports",
            "description": """
```python
def parse_bank(csv_text: str) -> dict: ...
# -> {"records": [{"date": "2026-03-01", "description": "ACME STEEL INV-1001", "amount_cents": -125000}, ...],
#     "errors": [4, 5]}
def parse_ledger(csv_text: str) -> list[dict]: ...
# -> [{"id": "L-1", "date": "2026-03-01", "amount_cents": -125000, "reference": "INV-1001"}, ...]
```

**Bank export** (from the bank's website): header `Date,Description,Amount`.

- Dates are `DD/MM/YYYY`; return them as ISO `YYYY-MM-DD`.
- Amounts may have thousands separators (`1,250.00`), a leading minus, or **parentheses
  for negatives** (`(45.10)` means -45.10). At most 2 decimal places.
- Descriptions may contain commas (the export quotes them). Strip whitespace around fields.
- A row with an invalid date or amount isn't returned. Its number goes in `errors`, where
  the header is line 1 and the first data row is line 2.

**Ledger export** (from the accounting system, always clean): header
`id,date,amount,reference`, ISO dates, plain decimal amounts.
""",
        },
        {
            "title": "Exact matching",
            "description": """
```python
def reconcile(bank: list[dict], ledger: list[dict]) -> dict: ...
# -> {"matched": [[bank_index, ledger_id], ...], "unmatched_bank": [bank_index, ...],
#     "unmatched_ledger": [ledger_id, ...]}
```

- A bank record matches a ledger entry with the **same date and same amount**. Each
  record and entry is used at most once.
- Go through bank records in order; when several ledger entries fit, take the earliest in
  ledger order.
- `matched` is in bank order, `unmatched_bank` lists bank indexes, and `unmatched_ledger`
  lists ids in ledger order.
- A month can have tens of thousands of transactions.
""",
        },
        {
            "title": "Probable matches",
            "description": """
Bank dates often lag the ledger by a day or two. Add a parameter:

```python
def reconcile(bank, ledger, date_tolerance_days: int = 0) -> dict: ...
# adds: "probable": [[bank_index, ledger_id], ...]   (always present; [] when tolerance is 0)
```

- Exact matches (Part 2) are made first, across **all** records.
- Then, for each still-unmatched bank record in order: candidates are unmatched ledger
  entries with the **same amount** and a date at most `date_tolerance_days` away.
- Prefer, in order: a candidate whose `reference` appears in the bank description
  (case-insensitive); then the smallest date difference; then ledger order.
- These pairs go in `probable` (the accountants confirm them), not `matched`.
""",
        },
    ],
    "discussion": [
        "The accountants want to see *why* a probable match was made. How would you report that?",
        "Some bank lines are one payment covering three invoices. How would you extend the matching?",
        "Why integer cents (or Decimal) rather than floats? Give a concrete example of what goes wrong.",
        "How would you make reruns safe after an accountant manually confirms or rejects matches?",
    ],
    "java_tip": """
*This tab names Python tools, which can hint at an approach.* See also [Python Reference](/reference) §15, §16, §18.

- `csv.DictReader(io.StringIO(text))` handles quoted commas; values are strings.
- `datetime.strptime(s, "%d/%m/%Y").date().isoformat()`; invalid dates raise `ValueError`.
- `Decimal("1250.50") * 100` is exact (`BigDecimal`); `Decimal("ten")` raises `decimal.InvalidOperation`.
- `date.fromisoformat(a) - date.fromisoformat(b)` is a `timedelta`; `.days` gives the gap.
- Index the ledger in a dict keyed by `(date, amount)` instead of scanning it for every bank row.
""",
    "starter": '''def parse_bank(csv_text: str) -> dict:
    pass


def parse_ledger(csv_text: str) -> list[dict]:
    pass
''',
    "solution": RECON_SOLUTION,
    "tests": [
        T(1, """
            bank_csv = (
                "Date,Description,Amount\\n"
                "01/03/2026,ACME STEEL INV-1001,\\"-1,250.00\\"\\n"
                "02/03/2026,\\"Refund, Desert Co\\",(45.10)\\n"
                "31/02/2026,Bad date,10.00\\n"
                "03/03/2026,Bad amount,ten\\n"
                "04/03/2026,  Bank fee  , 0.5 \\n"
            )
            result = parse_bank(bank_csv)
        """, {"records": [
            {"date": "2026-03-01", "description": "ACME STEEL INV-1001", "amount_cents": -125000},
            {"date": "2026-03-02", "description": "Refund, Desert Co", "amount_cents": -4510},
            {"date": "2026-03-04", "description": "Bank fee", "amount_cents": 50},
        ], "errors": [4, 5]}, label="quoted commas, negatives, bad rows"),
        T(1, """
            bank_csv = "Date,Description,Amount\\n05/03/2026,Tiny,1.005\\n06/03/2026,Big,\\"12,345,678.90\\"\\n"
            result = parse_bank(bank_csv)
        """, {"records": [{"date": "2026-03-06", "description": "Big", "amount_cents": 1234567890}], "errors": [2]},
          label="too many decimals; millions"),
        T(1, """
            ledger_csv = "id,date,amount,reference\\nL-1,2026-03-01,-1250.00,INV-1001\\nL-2,2026-03-02,-45.1,REF-9\\n"
            result = parse_ledger(ledger_csv)
        """, [{"id": "L-1", "date": "2026-03-01", "amount_cents": -125000, "reference": "INV-1001"},
              {"id": "L-2", "date": "2026-03-02", "amount_cents": -4510, "reference": "REF-9"}], label="ledger"),
        T(1, """
            result = [parse_bank("Date,Description,Amount\\n"), parse_ledger("id,date,amount,reference\\n")]
        """, [{"records": [], "errors": []}, []], label="headers only"),
        T(2, f"""
            bank = [{_b("2026-03-01", -125000)!r}, {_b("2026-03-02", 999)!r}, {_b("2026-03-03", 500)!r}]
            ledger = [{_l("L-1", "2026-03-03", 500)!r}, {_l("L-2", "2026-03-01", -125000)!r}, {_l("L-3", "2026-03-09", 1)!r}]
            r = reconcile(bank, ledger)
            result = [r["matched"], r["unmatched_bank"], r["unmatched_ledger"]]
        """, [[[0, "L-2"], [2, "L-1"]], [1], ["L-3"]], label="basic matching"),
        T(2, f"""
            bank = [{_b("2026-03-01", 100)!r}] * 3
            ledger = [{_l("L-1", "2026-03-01", 100)!r}, {_l("L-2", "2026-03-01", 100)!r}]
            r = reconcile(bank, ledger)
            result = [r["matched"], r["unmatched_bank"], r["unmatched_ledger"]]
        """, [[[0, "L-1"], [1, "L-2"]], [2], []], label="duplicates are used once each"),
        T(2, f"""
            r = reconcile([], [{_l("L-1", "2026-03-01", 100)!r}])
            result = [r["matched"], r["unmatched_bank"], r["unmatched_ledger"]]
        """, [[], [], ["L-1"]], label="empty bank"),
        T(2, """
            import random
            n = 20_000
            bank = [{"date": f"2026-03-{1 + i % 28:02d}", "description": "x", "amount_cents": 100 + i} for i in range(n)]
            order = list(range(n))
            random.Random(9).shuffle(order)
            ledger = [{"id": f"L-{j}", "date": f"2026-03-{1 + j % 28:02d}", "amount_cents": 100 + j, "reference": "R"}
                      for j in order]
            r = reconcile(bank, ledger)
            result = [r["matched"] == [[i, f"L-{i}"] for i in range(n)], r["unmatched_bank"], r["unmatched_ledger"]]
        """, [True, [], []], label="20,000 transactions each: index, don't scan", time_limit_ms=2000),
        T(3, f"""
            bank = [{_b("2026-03-03", -125000, "ACME STEEL INV-1001")!r}]
            ledger = [{_l("L-1", "2026-03-02", -125000, "INV-7777")!r}, {_l("L-2", "2026-03-05", -125000, "inv-1001")!r}]
            r = reconcile(bank, ledger, date_tolerance_days=3)
            result = [r["matched"], r["probable"], r["unmatched_ledger"]]
        """, [[], [[0, "L-2"]], ["L-1"]], label="reference match beats a closer date"),
        T(3, f"""
            bank = [{_b("2026-03-10", 500, "fee")!r}]
            ledger = [{_l("L-1", "2026-03-07", 500, "A")!r}, {_l("L-2", "2026-03-12", 500, "B")!r}, {_l("L-3", "2026-03-15", 500, "C")!r}]
            r = reconcile(bank, ledger, date_tolerance_days=3)
            result = [r["probable"], r["unmatched_ledger"]]
        """, [[[0, "L-2"]], ["L-1", "L-3"]], label="closest date, within tolerance"),
        T(3, f"""
            bank = [{_b("2026-03-03", 100, "a")!r}, {_b("2026-03-04", 100, "b")!r}]
            ledger = [{_l("L-1", "2026-03-04", 100, "x")!r}, {_l("L-2", "2026-03-06", 100, "y")!r}]
            r = reconcile(bank, ledger, date_tolerance_days=3)
            result = [r["matched"], r["probable"], r["unmatched_bank"]]
        """, [[[1, "L-1"]], [[0, "L-2"]], []], label="exact matches first, across all records"),
        T(3, f"""
            bank = [{_b("2026-03-03", 100)!r}]
            ledger = [{_l("L-1", "2026-03-04", 100)!r}]
            r = reconcile(bank, ledger)
            result = [r["probable"], r["unmatched_bank"], r["unmatched_ledger"]]
        """, [[], [0], ["L-1"]], label="tolerance 0: no probable matches"),
        T(3, f"""
            bank = [{_b("2026-03-28", 700)!r}]
            ledger = [{_l("L-1", "2026-04-01", 700)!r}]
            result = [reconcile(bank, ledger, date_tolerance_days=3)["probable"],
                      reconcile(bank, ledger, date_tolerance_days=4)["probable"]]
        """, [[], [[0, "L-1"]]], label="date gaps across a month end"),
    ],
}


# ================================================================== clinic
CLINIC_SOLUTION = '''from itertools import count

SLOT = 15  # candidate start times are on 15-minute marks


def _minutes(hhmm: str) -> int:
    hours, minutes = hhmm.split(":")
    return int(hours) * 60 + int(minutes)


def _hhmm(minutes: int) -> str:
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def _overlaps(start, end, intervals):
    return any(start < b_end and b_start < end for b_start, b_end in intervals)


def _free(hours, busy, duration):
    """Aligned start minutes where [start, start + duration) fits a block and avoids `busy`."""
    starts = []
    for block_start, block_end in hours:
        start = -(-block_start // SLOT) * SLOT          # round up to the next 15-minute mark
        while start + duration <= block_end:
            if not _overlaps(start, start + duration, busy):
                starts.append(start)
            start += SLOT
    return starts


def free_slots(hours: list[list[str]], bookings: list[list[str]], duration: int) -> list[str]:
    blocks = sorted((_minutes(a), _minutes(b)) for a, b in hours)
    busy = [(_minutes(a), _minutes(b)) for a, b in bookings]
    return [_hhmm(m) for m in _free(blocks, busy, duration)]


class Clinic:
    def __init__(self):
        self.hours = {}          # doctor -> [(start, end)]
        self.bookings = {}       # booking id -> (doctor, start, end, patient)
        self._ids = count(1)

    def add_doctor(self, name: str, hours: list[list[str]]) -> None:
        self.hours[name] = sorted((_minutes(a), _minutes(b)) for a, b in hours)

    def _busy(self, doctor):
        return [(s, e) for d, s, e, _ in self.bookings.values() if d == doctor]

    def _patient_busy(self, patient):
        return [(s, e) for _, s, e, p in self.bookings.values() if p == patient]

    def book(self, name: str, start: str, duration: int, patient: str | None = None) -> str | None:
        if name not in self.hours:
            return None
        begin = _minutes(start)
        end = begin + duration
        inside = any(a <= begin and end <= b for a, b in self.hours[name])
        if not inside or _overlaps(begin, end, self._busy(name)):
            return None
        booking_id = f"B{next(self._ids)}"
        self.bookings[booking_id] = (name, begin, end, patient)
        return booking_id

    def cancel(self, booking_id: str) -> bool:
        return self.bookings.pop(booking_id, None) is not None

    def _earliest(self, duration, after, extra_busy=()):
        best = None
        for name in sorted(self.hours):
            for start in _free(self.hours[name], self._busy(name) + list(extra_busy), duration):
                if start >= after:
                    if best is None or start < best[1]:
                        best = (name, start)
                    break
        return best

    def earliest(self, duration: int, after: str = "00:00") -> list | None:
        best = self._earliest(duration, _minutes(after))
        return [best[0], _hhmm(best[1])] if best else None

    def book_patient(self, patient: str, duration: int, after: str = "00:00") -> list | None:
        best = self._earliest(duration, _minutes(after), self._patient_busy(patient))
        if not best:
            return None
        booking_id = self.book(best[0], _hhmm(best[1]), duration, patient)
        return [booking_id, best[0], _hhmm(best[1])]
'''

CLINIC = {
    "id": "rw-clinic-scheduler",
    "title": "Clinic Appointment Scheduling",
    "difficulty": "Medium",
    "category": "Real-world",
    "tags": ["time arithmetic", "intervals", "class design"],
    "entry": "free_slots",
    "mode": "script",
    "target_minutes": 45,
    "description": """
A hospital outpatient clinic books appointments by phone, and patients wait days for a
call back. You're building the booking engine behind a new self-service page. All times
are `"HH:MM"` on a single day, and durations are in minutes.

A time range `["09:30", "10:00"]` includes 09:30 and ends at 10:00 (exclusive), so an
appointment can start exactly when another ends.
""",
    "parts": [
        {
            "title": "Free slots for one doctor",
            "description": """
```python
def free_slots(hours: list[list[str]], bookings: list[list[str]], duration: int) -> list[str]: ...
```

- `hours`: the doctor's working blocks, e.g. `[["09:00", "12:00"], ["13:00", "17:00"]]`.
- `bookings`: existing appointments. They may be unsorted, overlap each other, or even
  extend outside working hours.
- Return every start time on a **15-minute mark** (:00, :15, :30, :45) where an appointment of
  `duration` fits entirely inside one working block without overlapping any booking.
  Return them in time order.
""",
        },
        {
            "title": "The clinic",
            "description": """
```python
class Clinic:
    def add_doctor(self, name: str, hours: list[list[str]]) -> None: ...
    def book(self, name: str, start: str, duration: int) -> str | None: ...
    def cancel(self, booking_id: str) -> bool: ...
    def earliest(self, duration: int, after: str = "00:00") -> list | None: ...
```

- `book` returns a new booking id (`"B1"`, `"B2"`, … in creation order), or `None` if the
  doctor is unknown, the appointment isn't fully inside one working block, or it overlaps
  one of that doctor's bookings. Booked start times don't have to be on 15-minute marks.
- `cancel` frees the slot. It returns `False` for unknown or already-cancelled ids.
- `earliest` returns `[doctor, "HH:MM"]` for the earliest free 15-minute-mark slot starting
  at or after `after`, across all doctors (ties go to the alphabetically first doctor), or
  `None`.
""",
        },
        {
            "title": "Patients",
            "description": """
```python
def book_patient(self, patient: str, duration: int, after: str = "00:00") -> list | None: ...
# -> ["B7", "Dr Haddad", "10:15"]
```

Book the earliest slot (same rules as `earliest`) that also **doesn't overlap any of this
patient's existing bookings**. Bookings made with `book_patient` belong to the patient;
cancelling one frees the patient too. Return `[booking_id, doctor, start]`, or `None`.
""",
        },
    ],
    "discussion": [
        "Two people click the same slot at the same moment on the website. How do you prevent a double booking?",
        "How would you extend this to a full week and to recurring schedules (\"every Tuesday 9–12\")?",
        "What would you store in the database, and what would you compute on the fly?",
        "Patients cancel late and slots go unused. What product features might help, and how would you measure them?",
    ],
    "java_tip": """
*This tab names Python tools, which can hint at an approach.* See also [Python Reference](/reference) §3, §16.

- Convert `"HH:MM"` to minutes once (`h, m = s.split(":")`), do all the maths in integers, and format back with `f"{m // 60:02d}:{m % 60:02d}"`.
- Two intervals `[a, b)` and `[c, d)` overlap exactly when `a < d and c < b`.
- `-(-x // 15) * 15` rounds `x` up to a multiple of 15.
- `itertools.count(1)` gives increasing ids; `dict.pop(key, None)` removes without raising.
""",
    "starter": '''def free_slots(hours: list[list[str]], bookings: list[list[str]], duration: int) -> list[str]:
    pass
''',
    "solution": CLINIC_SOLUTION,
    "tests": [
        T(1, """
            hours = [["09:00", "12:00"], ["13:00", "17:00"]]
            bookings = [["16:30", "17:30"], ["09:30", "10:00"], ["11:00", "11:45"]]
            result = free_slots(hours, bookings, 30)
        """, ["09:00", "10:00", "10:15", "10:30", "13:00", "13:15", "13:30", "13:45", "14:00", "14:15", "14:30",
              "14:45", "15:00", "15:15", "15:30", "15:45", "16:00"], label="a normal day"),
        T(1, 'result = free_slots([["09:10", "10:00"]], [], 45)', ["09:15"], label="slots start on 15-minute marks"),
        T(1, """
            result = [free_slots([], [], 15), free_slots([["09:00", "09:30"]], [], 45),
                      free_slots([["09:00", "10:00"]], [["08:00", "12:00"]], 15)]
        """, [[], [], []], label="no hours / too long / fully booked"),
        T(1, """
            result = free_slots([["09:00", "10:30"]], [["09:00", "09:45"], ["09:15", "09:30"], ["10:15", "10:30"]], 15)
        """, ["09:45", "10:00"], label="overlapping bookings"),
        T(1, 'result = free_slots([["13:00", "14:00"], ["08:00", "09:00"]], [], 60)', ["08:00", "13:00"],
          label="blocks given out of order"),
        T(2, """
            c = Clinic()
            c.add_doctor("Dr B", [["09:00", "12:00"]])
            c.add_doctor("Dr A", [["10:00", "12:00"]])
            result = [c.book("Dr B", "09:00", 30), c.book("Dr B", "09:15", 30), c.book("Dr B", "09:30", 30),
                      c.book("Dr A", "11:45", 30), c.book("Dr Z", "10:00", 15), c.book("Dr A", "10:07", 20)]
        """, ["B1", None, "B2", None, None, "B3"], label="booking rules"),
        T(2, """
            c = Clinic()
            c.add_doctor("Dr B", [["09:00", "12:00"]])
            c.add_doctor("Dr A", [["10:00", "12:00"]])
            first = c.earliest(30)
            c.book("Dr B", "09:00", 60)
            second = c.earliest(30)
            third = c.earliest(30, after="10:20")
            result = [first, second, third, c.earliest(180)]
        """, [["Dr B", "09:00"], ["Dr A", "10:00"], ["Dr A", "10:30"], None], label="earliest across doctors, tie-break"),
        T(2, """
            c = Clinic()
            c.add_doctor("Dr A", [["09:00", "10:00"]])
            b = c.book("Dr A", "09:00", 60)
            before = c.earliest(15)
            result = [before, c.cancel(b), c.cancel(b), c.cancel("nope"), c.earliest(15)]
        """, [None, True, False, False, ["Dr A", "09:00"]], label="cancel frees the slot"),
        T(3, """
            c = Clinic()
            c.add_doctor("Dr A", [["09:00", "12:00"]])
            c.add_doctor("Dr B", [["09:00", "12:00"]])
            result = [c.book_patient("pat-1", 30), c.book_patient("pat-1", 30), c.book_patient("pat-2", 30)]
        """, [["B1", "Dr A", "09:00"], ["B2", "Dr A", "09:30"], ["B3", "Dr B", "09:00"]],
          label="a patient can't be in two places at once"),
        T(3, """
            c = Clinic()
            c.add_doctor("Dr A", [["09:00", "10:00"]])
            c.add_doctor("Dr B", [["09:00", "10:00"]])
            first = c.book_patient("pat-1", 60)
            blocked = c.book_patient("pat-1", 60)
            c.cancel(first[0])
            again = c.book_patient("pat-1", 60)
            result = [first, blocked, again]
        """, [["B1", "Dr A", "09:00"], None, ["B2", "Dr A", "09:00"]], label="cancelling frees the patient"),
        T(3, """
            c = Clinic()
            c.add_doctor("Dr A", [["09:00", "12:00"]])
            c.book("Dr A", "09:00", 30)
            result = [c.book_patient("pat-1", 30, after="09:10"), c.earliest(30)]
        """, [["B2", "Dr A", "09:30"], ["Dr A", "10:00"]], label="after= and shared calendar"),
    ],
}


# =============================================================== inventory
INVENTORY_SOLUTION = '''import math
from fractions import Fraction


def stock(events: list[dict]) -> dict:
    on_hand = {}
    for event in events:
        sku, qty, kind = event["sku"], event["qty"], event["type"]
        current = on_hand.get(sku, 0)
        if kind == "receive":
            on_hand[sku] = current + qty
        elif kind == "issue":
            on_hand[sku] = current - qty
        elif kind == "adjust":
            on_hand[sku] = current + qty
        elif kind == "count":
            on_hand[sku] = qty
        else:
            raise ValueError(f"unknown event type: {kind!r}")
    return {"on_hand": on_hand, "negative": sorted(s for s, q in on_hand.items() if q < 0)}


def reorder(on_hand: dict, usage: dict, lead_time_days: int, safety_days: int, pack_size: int = 1,
            open_orders: dict | None = None, min_order: dict | None = None) -> list[list]:
    open_orders = open_orders or {}
    min_order = min_order or {}
    plan = []
    for sku in sorted(usage):
        history = usage[sku][-30:]
        if not history:
            continue
        average = Fraction(sum(history), len(history))           # exact: no float surprises
        position = on_hand.get(sku, 0) + open_orders.get(sku, 0)
        if position > average * (lead_time_days + safety_days):
            continue
        qty = math.ceil(average * (lead_time_days + safety_days + 30) - position)
        qty = max(qty, min_order.get(sku, 0))
        qty = -(-qty // pack_size) * pack_size                    # round up to whole packs
        if qty > 0:
            plan.append([sku, qty])
    return plan
'''

INVENTORY = {
    "id": "rw-inventory-reorder",
    "title": "Inventory Reorder Planner",
    "difficulty": "Medium",
    "category": "Real-world",
    "tags": ["event replay", "business rules", "rounding"],
    "entry": "stock",
    "mode": "script",
    "target_minutes": 35,
    "description": """
An energy company's field warehouses keep running out of spare parts, which stops repair
crews. Their planners want a tool that tracks stock from warehouse events and says what to
reorder, and how much.
""",
    "parts": [
        {
            "title": "Stock on hand",
            "description": """
```python
def stock(events: list[dict]) -> dict: ...
# events: [{"sku": "VALVE-2", "type": "receive", "qty": 10}, ...]   (in time order)
# -> {"on_hand": {"VALVE-2": 7, ...}, "negative": ["PUMP-1"]}
```

| type | effect |
|---|---|
| `receive` | adds `qty` |
| `issue` | removes `qty` |
| `adjust` | adds `qty` (which may be negative), e.g. for damaged stock |
| `count` | a physical stock count: on hand **becomes** `qty` |

Any other type raises `ValueError`. Stock can go negative (data-entry problems); list
those SKUs, sorted, in `negative`.
""",
        },
        {
            "title": "What to reorder",
            "description": """
```python
def reorder(on_hand: dict, usage: dict, lead_time_days: int, safety_days: int,
            pack_size: int = 1) -> list[list]: ...
# usage: {"VALVE-2": [3, 0, 5, ...]}   daily quantities issued, oldest first
# -> [["VALVE-2", 310], ...]           sorted by SKU
```

The planners' rules, for each SKU in `usage`:

1. **Average daily usage** = the mean of its last 30 days (all of them if there are
   fewer). SKUs with no history are never reordered.
2. **Reorder point** = average × (lead time + safety days). Reorder when on hand (0 if the
   SKU isn't in `on_hand`) is **at or below** it.
3. **Order quantity** = enough to cover lead time + safety + 30 days:
   `ceil(average × (lead + safety + 30) − on_hand)`, then rounded **up** to a whole number
   of packs. Only list SKUs whose quantity is above 0.
""",
        },
        {
            "title": "Open orders and minimums",
            "description": """
```python
def reorder(..., open_orders: dict | None = None, min_order: dict | None = None) -> list[list]: ...
```

- **Open orders** (already ordered, not yet arrived) count as stock: use
  on hand + on order wherever Part 2 used on hand.
- **Supplier minimums:** if the quantity is below the SKU's `min_order`, order the minimum
  instead. Pack rounding happens last.
""",
        },
    ],
    "discussion": [
        "Usage is seasonal (more failures in summer). How would you change the average?",
        "Lead times vary by supplier and sometimes slip. How would you account for that?",
        "Why exact fractions or integers instead of floats here? What breaks at the boundary?",
        "The planners don't trust the numbers yet. How would you earn that trust in the first month?",
    ],
    "java_tip": """
*This tab names Python tools, which can hint at an approach.* See also [Python Reference](/reference) §6, §18.

- `d.get(key, 0)` for "0 if missing"; `sorted(d)` iterates keys in order.
- `history[-30:]` is the last 30 items (or all of them if fewer).
- `math.ceil(x)` rounds up; `-(-q // pack) * pack` rounds up to a multiple.
- Floats can land just above or below a boundary (`0.1 * 3 > 0.3`). `fractions.Fraction` keeps exact ratios.
""",
    "starter": '''def stock(events: list[dict]) -> dict:
    pass
''',
    "solution": INVENTORY_SOLUTION,
    "tests": [
        T(1, """
            events = [
                {"sku": "A", "type": "receive", "qty": 10}, {"sku": "A", "type": "issue", "qty": 3},
                {"sku": "B", "type": "receive", "qty": 5}, {"sku": "B", "type": "adjust", "qty": -1},
                {"sku": "A", "type": "count", "qty": 4}, {"sku": "A", "type": "issue", "qty": 6},
                {"sku": "C", "type": "issue", "qty": 1},
            ]
            result = stock(events)
        """, {"on_hand": {"A": -2, "B": 4, "C": -1}, "negative": ["A", "C"]}, label="all event types"),
        T(1, """
            try:
                stock([{"sku": "A", "type": "steal", "qty": 1}])
                result = "no error"
            except ValueError:
                result = "ValueError"
        """, "ValueError", label="unknown event type"),
        T(1, 'result = stock([])', {"on_hand": {}, "negative": []}, label="no events"),
        T(1, """
            events = [{"sku": f"S{i % 1000}", "type": "receive" if i % 2 else "issue", "qty": 1} for i in range(200_000)]
            out = stock(events)
            result = [len(out["on_hand"]), out["on_hand"]["S0"], out["negative"][:2]]
        """, [1000, -200, ["S0", "S10"]], label="200,000 events", time_limit_ms=2000),
        T(2, """
            on_hand = {"A": 60, "B": 20, "C": -1}
            usage = {"A": [10] * 30, "B": [1, 2, 3], "C": [0] * 10, "D": [5] * 40, "E": []}
            result = [reorder(on_hand, usage, 5, 2), reorder(on_hand, usage, 5, 2, pack_size=50)]
        """, [[["A", 310], ["C", 1], ["D", 185]], [["A", 350], ["C", 50], ["D", 200]]],
          label="the rules, with and without packs"),
        T(2, """
            result = reorder({"A": 70}, {"A": [10] * 30}, 5, 2)
        """, [["A", 300]], label="exactly at the reorder point"),
        T(2, """
            result = [reorder({"A": 3}, {"A": [100] * 10 + [1] * 30}, 3, 1), reorder({"A": 3}, {"A": [1] * 30}, 3, 1)]
        """, [[["A", 31]], [["A", 31]]], label="only the last 30 days count"),
        T(2, """
            result = reorder({"A": 1}, {"A": [1, 0, 0]}, 2, 1)
        """, [["A", 10]], label="fractional averages round up at the end"),
        T(2, """
            result = reorder({"A": 0}, {"A": [3, 2, 2]}, 14, 7)
        """, [["A", 119]], label="exact arithmetic: 7/3 × 51 days is exactly 119 (floats say 120)"),
        T(3, """
            usage = {"A": [10] * 30, "B": [10] * 30}
            result = [reorder({"A": 10, "B": 10}, usage, 5, 2, open_orders={"A": 100}),
                      reorder({"A": 10, "B": 10}, usage, 5, 2, open_orders={"A": 50})]
        """, [[["B", 360]], [["A", 310], ["B", 360]]], label="open orders count as stock"),
        T(3, """
            usage = {"A": [1] * 30, "B": [1] * 30}
            result = reorder({"A": 3, "B": 3}, usage, 3, 1, pack_size=12, min_order={"A": 100})
        """, [["A", 108], ["B", 36]], label="minimum order, then packs"),
        T(3, """
            result = reorder({}, {"A": [2] * 30}, 1, 1, open_orders={"A": 0}, min_order={"A": 1})
        """, [["A", 64]], label="minimum below the quantity changes nothing"),
    ],
}

PROBLEMS = [LOG, RECON, CLINIC, INVENTORY]
