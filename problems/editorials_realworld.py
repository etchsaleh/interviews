"""Per-part editorials for the Real-world and Product Engineering problems."""

PART_EDITORIALS = {
    # ------------------------------------------------------------ log triage
    "rw-log-triage": [
        """
**Idea:** one compiled regex decides whether a line fits; anything that fails (regex or date)
is counted as skipped.

**Steps:** compile once at module level, e.g.
`(\\S+) (GET|POST|PUT|PATCH|DELETE) (\\S+) (\\d{3}) (\\d+)ms(?:\\s.*)?`, and use `fullmatch` on
the stripped line. Convert the timestamp with
`calendar.timegm(time.strptime(s, "%Y-%m-%dT%H:%M:%SZ"))`, catching `ValueError` for impossible
dates like month 13. Skip blank lines without counting them.

**Complexity:** O(n) lines; 50,000 lines must parse in a few seconds, so don't recompile per line.

**Pitfalls:** `match` or `search` instead of `fullmatch` (accepts `12msx`); `time.mktime`, which
uses local time instead of UTC; letting `get`, a 4-digit status `2000`, `-1ms` or a duration
without `ms` through; counting blank lines as skipped.
""",
        """
**Idea:** turn each path into a template, group with `defaultdict(list)`, then compute each
group's numbers.

**Steps:** template = `path.split("?", 1)[0]`, then replace every segment where
`part.isdigit()` with `:id`. Key is `f"{method} {template}"`. Per group: `count`, `errors` =
`sum(status >= 500)`, `error_rate = round(errors / count, 3)`, and
`p95 = sorted(ms)[math.ceil(0.95 * n) - 1]`.

**Complexity:** O(n log n) for the per-group sorts.

**Pitfalls:** counting a 404 as an error; using the max, or `statistics.quantiles` (which
interpolates), instead of nearest rank; the off-by-one when `0.95 × n` is whole (20 values gives
the 19th, not the 20th); templating `v2` (only all-digit segments become `:id`); forgetting to
drop the query string.
""",
        """
**Idea:** one pass buckets entries into aligned windows; then walk the sorted window starts and
merge bad windows that touch.

**Steps:** `windows = defaultdict(lambda: [0, 0])` keyed by `ts - ts % window_s`, counting
requests and 5xx. For each `start in sorted(windows)`: skip if `requests < min_requests` or
`errors / requests < threshold`. If the last incident's `end == start`, extend it and add the
counts; otherwise open a new incident.

**Complexity:** O(n + w log w) for w non-empty windows. Order of the input doesn't matter.

**Pitfalls:** scanning all entries once per window (the 200,000-entry test times out); merging
across a low-volume window (it breaks the chain even if every request failed); `>` instead of
"at least" for the threshold; summing only the first window's counts into a merged incident.
""",
    ],
    # ------------------------------------------------------------ reconciliation
    "rw-reconcile": [
        """
**Idea:** let `csv` handle quoting and let `Decimal` handle money; convert to integer cents once.

**Steps:** `csv.DictReader(io.StringIO(text))` gives dicts and copes with quoted commas. Number
rows with `enumerate(..., start=2)`. Dates: `datetime.strptime(s.strip(), "%d/%m/%Y").date().isoformat()`.
Amounts: strip, remove `,`, unwrap `(...)` as negative, then `Decimal(text) * 100`; reject it if
it isn't integral, else `int(...)`. Catch `ValueError` and `decimal.InvalidOperation` and record
the row number. The ledger reuses the same cents helper.

**Pitfalls:** `float("1.005") * 100` is `100.49999...`, which is why `Decimal` is the right tool;
splitting on commas by hand; accepting 3 decimals instead of erroring; not stripping `" 0.5 "`;
`31/02/2026` must be an error; a headers-only file returns empty results.
""",
        """
**Idea:** index the ledger by `(date, amount_cents)` so each bank record finds its candidates in
O(1) instead of scanning the ledger.

**Steps:** build `dict[(date, cents)] -> list of entries` in ledger order (a `deque` makes taking
the front O(1)). For each bank record in order, take the first unused candidate and record
`[bank_index, ledger_id]`; otherwise add the index to `unmatched_bank`. Keep a `used` set of
ledger ids, and build `unmatched_ledger` by walking the ledger in its original order.

**Complexity:** O(n + m) instead of O(n · m).

**Pitfalls:** a nested loop over 20,000 × 20,000 rows times out; matching two bank duplicates to
the same ledger entry; returning unmatched ledger ids in index order rather than ledger order;
an empty bank list.
""",
        """
**Idea:** extend part 2's function with a second pass over only the leftovers, ranking each
candidate with a tuple.

**Steps:** run the exact pass over all bank records first. Group the unused ledger entries by
amount, keeping each entry's ledger position. For each leftover bank record in order, consider
entries with the same amount and `abs((date.fromisoformat(a) - date.fromisoformat(b)).days) <= tol`.
Rank by `(not ref_in_description, gap, ledger_order)` and take the minimum; mark it used and add
it to `probable`.

**Pitfalls:** interleaving exact and tolerant matching (a probable match can steal an entry that
another record matches exactly); a case-sensitive reference check; subtracting day numbers from
the strings, which breaks across month ends (`03-28` to `04-01` is 4 days); leaving out
`probable` when tolerance is 0.
""",
    ],
    # ------------------------------------------------------------ clinic
    "rw-clinic-scheduler": [
        """
**Idea:** convert every `"HH:MM"` to minutes once, do integer maths, and test each candidate
start against the bookings.

**Steps:** sort the blocks. For each block, round its start up to a 15-minute mark with
`-(-start // 15) * 15`, then step by 15 while `start + duration <= block_end`. Keep a start
if no booking overlaps, where `[a, b)` and `[c, d)` overlap exactly when `a < d and c < b`.
Format back with `f"{m // 60:02d}:{m % 60:02d}"`.

**Complexity:** O(slots × bookings), tiny for one day.

**Pitfalls:** starting at `09:10` instead of `09:15`; `<=` in the overlap test (a slot may
start exactly when a booking ends); forgetting to sort blocks given out of order. Overlapping
or out-of-hours bookings need no special handling: the overlap test covers them.
""",
        """
**Idea:** a class holding each doctor's sorted hours and a dict of bookings; reuse part 1's
slot logic for `earliest`.

**Steps:** `itertools.count(1)` gives `B1, B2, ...` (never reused). `book` returns `None` for an
unknown doctor, a time not fully inside one block (`a <= begin and end <= b`), or an overlap with
that doctor's bookings. `cancel` is `self.bookings.pop(id, None) is not None`. `earliest` loops
doctors in `sorted` order, takes each one's first free mark at or after `after`, and keeps a new
best only if it is strictly earlier.

**Pitfalls:** requiring booked starts on 15-minute marks (`10:07` is allowed); accepting a
booking that runs past the block end (`11:45` for 30 minutes); `<=` when comparing doctors,
which breaks the alphabetical tie-break; `cancel` returning `True` twice.
""",
        """
**Idea:** store the patient on each booking; the patient's own bookings become extra busy time
in the same earliest-slot search.

**Steps:** extend the booking record with a `patient` field (`None` for plain `book`). In
`book_patient`, collect that patient's intervals and add them to each doctor's busy list while
searching, exactly like `earliest`. Then call `book` for the winner so the id counter and rules
are shared, and return `[booking_id, doctor, start]`.

**Pitfalls:** checking only the chosen doctor's calendar, so a patient lands with Dr B at the
same 09:00 they already have with Dr A; keeping a separate patient calendar that `cancel` forgets
to clear (deriving it from the bookings dict avoids that); a second id counter. `after=` and
other bookings on the shared calendar still apply.
""",
    ],
    # ------------------------------------------------------------ inventory
    "rw-inventory-reorder": [
        """
**Idea:** replay the events in order into a dict of SKU to quantity.

**Steps:** `current = on_hand.get(sku, 0)`. `receive` and `adjust` add `qty`, `issue` subtracts
it, `count` sets it to `qty`. Anything else raises `ValueError`. At the end,
`negative = sorted(s for s, q in on_hand.items() if q < 0)`.

**Complexity:** O(n + k log k) for n events and k SKUs; 200,000 events must run in well under
2 seconds, so no per-event sorting or copying.

**Pitfalls:** treating `count` as an addition (it overwrites); clamping stock at 0 (negative
stock is data the planners need to see); an `issue` for an unseen SKU must start from 0;
silently ignoring an unknown type.
""",
        """
**Idea:** apply the planners' three rules per SKU, in exact arithmetic so boundaries behave.

**Steps:** for each `sku in sorted(usage)`: `history = usage[sku][-30:]`; skip if empty.
`average = Fraction(sum(history), len(history))`. Reorder when
`on_hand.get(sku, 0) <= average * (lead + safety)`. Then
`qty = math.ceil(average * (lead + safety + 30) - on_hand)`, round up to packs with
`-(-qty // pack) * pack`, and list it only if `qty > 0`.

**Pitfalls:** floats: `7/3 × 51` should be exactly 119 but a float average gives 120, which is
why `Fraction` is the right tool; `<` instead of "at or below"; averaging all history instead of
the last 30 days; `round` instead of `ceil`; a SKU missing from `on_hand` counts as 0, and
negative stock still triggers a reorder.
""",
        """
**Idea:** extend part 2's function: replace on hand with the stock position, and apply the
minimum before pack rounding.

**Steps:** `position = on_hand.get(sku, 0) + open_orders.get(sku, 0)`, used for both the
reorder-point check and the quantity. After `ceil`, `qty = max(qty, min_order.get(sku, 0))`,
then round up to packs. Default both new arguments to `None` and replace them with `{}`
(never a mutable default).

**Pitfalls:** using open orders only in the trigger but not in the quantity (or the reverse);
rounding to packs before applying the minimum (100 then packs of 12 is 108); letting a minimum
create an order for a SKU that isn't at its reorder point; a minimum smaller than the quantity
must change nothing.
""",
    ],
    # ------------------------------------------------------------ permit tracker
    "product-permit-tracker": [
        """
**Idea:** routes defined inside `create_app` close over that app's storage, so each test gets
fresh state. Validate everything, then create.

**Steps:** `body = request.get_json(silent=True)`; if it isn't a `dict`, return 400 with
`fields: []`. Collect bad fields: `applicant` and `address` must be strings with
`.strip()`; `type` must be a string in the allowed set; `description`, if present, must be a
string. Return `sorted(bad)`. Otherwise store with the next id, status `"submitted"`, and return
it with 201. `GET` returns 404 with an `"error"` key when missing.

**Pitfalls:** module-level globals leak between tests; `["solar"] in TYPES` raises `TypeError`
(lists are unhashable), so check `isinstance` first; stopping at the first bad field; a
whitespace-only address must fail.
""",
        """
**Idea:** the workflow is data: `TRANSITIONS = {status: set_of_allowed_next}`. Every accepted
move updates the status and appends a history entry.

**Steps:** extend part 1's create to write the first entry (`from` `None`, `to` `"submitted"`,
actor = applicant, note `""`). In the transition route check, in order: unknown application
→ 404; `to` not a known status, or `actor` missing or empty, or `note` not a string → 400; `to`
not in `TRANSITIONS[current]` → 409. Then update and append. History returns entries oldest first.

**Pitfalls:** writing history or changing status before validation finishes (rejected moves must
change nothing); 400 vs 409 mixed up; terminal states (`approved`, `rejected`) must allow nothing;
history for an unknown id must be 404, not `[]`.
""",
        """
**Idea:** filter, count, then slice. `total` comes from the filtered set before paging.

**Steps:** parse `limit` (default 20) and `offset` (default 0) with `int()` inside
`try/except ValueError` → 400; also 400 unless `1 <= limit <= 100` and `offset >= 0`. Apply
`status` and `type` as exact filters and `q` as `q.lower()` in either `applicant.lower()` or
`address.lower()`, all combined with AND. Order by id, then return `items[offset:offset + limit]`
and `total`.

**Pitfalls:** counting `total` after slicing; a case-sensitive search (`PALM` must find
`palm grove`); `?limit=abc` raising a 500; an offset past the end should return `[]` with the
real total, not an error.
""",
        """
**Idea:** move all state into SQLite at `db_path`; the database, not the Python process, is the
source of truth.

**Steps:** in `create_app`, run `executescript` with `CREATE TABLE IF NOT EXISTS` for
applications and history. Use `INTEGER PRIMARY KEY AUTOINCREMENT` so ids continue after a
restart. Open one connection per request on Flask's `g` with `row_factory = sqlite3.Row`, close it
in `teardown_appcontext`, and `commit()` after every write. Always use `?` placeholders.

**Pitfalls:** keeping a Python dict cache in front of the database (a second app on the same file
won't see changes); forgetting `commit()`; sharing one connection across threads; `from` is an SQL
keyword, so store `from_status` and alias it (`from_status AS "from"`); a different `db_path` must
see no data.
""",
        """
**Idea:** cache summaries in the database keyed by `(application_id, status)`, so a status change
is automatically a cache miss and the cache survives restarts.

**Steps:** add a `summaries` table with that primary key. Load the application (404 first, no LLM
call). Return a cached row if one exists. Otherwise build a prompt with applicant, address, type,
status and description, and `requests.post(f"{llm_base_url}/llm/v1/messages", headers=...,
json=..., timeout=...)`. On `requests.RequestException` or a non-200 status return 503. On
success join the `text` blocks of `content`, insert, commit, and return it.

**Pitfalls:** caching by id only (stale after a status change); caching the failure, so a later
request never retries; an in-memory cache that a restart loses; no timeout on the HTTP call.
""",
    ],
}
