"""Per-part editorials for the Multi-part (question-bank) problems."""

PART_EDITORIALS = {
    # ------------------------------------------------------------ durable cache
    "mp-durable-cache": [
        """
**Idea:** the key `(func.__name__,) + args + tuple(kwargs.values())` has three bugs. It drops
the keyword names (`x=1` and `y=1` collide), it mixes positional and keyword values (`f(1, 2)` vs
`f(1, x=2)`), and it puts lists and dicts in a tuple, so hashing raises `TypeError`. It also
depends on kwarg order.

**Steps:** build a canonical, hashable key: `(func.__name__, json.dumps(args, sort_keys=True,
default=repr), json.dumps(kwargs, sort_keys=True, default=repr))`. `sort_keys` makes dict order
irrelevant at every nesting level, and serialising args and kwargs separately keeps them apart.
A recursive "freeze" (dicts to sorted item tuples, lists to tuples) works too.

**Pitfalls:** `frozenset(kwargs.items())` still crashes on unhashable values; sorting only the
top-level kwargs misses nested dicts (`{"x": [1, {"y": 2}]}`). Eviction must keep working.
""",
        """
**Idea:** an append-only log (write-ahead log). Each `call()` appends one small JSON line, so
the cost per call is constant. On startup, replay the log through the same store/evict logic to
rebuild the values and the LRU order.

**Steps:** on a miss append `{"k": key, "v": value}`; on a **hit** append `{"k": key}` too, since
recency changes the next eviction. Open with `"a"`, then `f.flush()` and `os.fsync(f.fileno())`
before returning. On replay, a record with `"v"` stores (and evicts past capacity), one without
it does `move_to_end` if the key is present. JSON turns the key tuple into a list: convert back
with `tuple()`.

**Pitfalls:** skip lines `json.loads` rejects (truncated tail). Don't rewrite the whole cache per
call (the size test fails). Evicted entries must stay evicted. No `log_path` means no file at all.
""",
        """
**Idea:** snapshot the live entries into a fresh log, then swap it in atomically, so a crash at
any point leaves either the old log or the new one, never half of each.

**Steps:** write one `{"k", "v"}` line per entry, iterating the `OrderedDict` from LRU to MRU,
so replaying the snapshot rebuilds the same order. Write to `log_path + ".tmp"`, `flush` and
`fsync`, close the current append handle, `os.replace(tmp, log_path)`, then reopen `log_path`
in append mode.

**Complexity:** O(entries) time and file size, regardless of how many calls were made.

**Pitfalls:** forgetting to reopen the handle: after `os.replace` the old handle still points at
the replaced file, so later calls are lost (the "logging continues after compaction" test).
Writing straight over `log_path` is not crash-safe.
""",
    ],
    # --------------------------------------------------------------- IP iterator
    "mp-ip-iterator": [
        """
**Idea:** treat the address as one 32-bit integer. Incrementing an int handles every carry
(`192.168.0.255` to `192.168.1.0`) for free; per-octet carry logic is where bugs hide.

**Steps:** parse with `a, b, c, d = map(int, ip.split("."))` and `(a << 24) | (b << 16) | (c << 8) | d`.
Format back with `".".join(str((n >> s) & 255) for s in (24, 16, 8, 0))`. `__iter__` returns
`self`; `__next__` raises `StopIteration` once the value passes `0xFFFFFFFF`, otherwise formats
the current value, advances, and returns it.

**Complexity:** O(1) per `next()`, O(1) memory.

**Pitfalls:** the start address is included; `255.255.255.255` yields only itself. Multi-octet
carry (`10.255.255.255` to `11.0.0.0`). `iter(it) is it` is tested. The `ipaddress` module isn't
banned, but bit arithmetic is what this round expects.
""",
        """
**Idea:** the same walk with a signed step: `delta = -1 if reverse else 1`, and a lower bound of
`0` next to the upper bound `0xFFFFFFFF`.

**Steps:** store `self.low, self.high = 0, 0xFFFFFFFF` and `self.delta`. In `__next__`, check
`if not self.low <= self.current <= self.high: raise StopIteration` before yielding, then
`self.current += self.delta`. Keeping both bounds as attributes makes the boundary check one line.

**Pitfalls:** `0.0.0.0` with `reverse=True` yields exactly one address. Borrow across octets
(`192.168.1.0` to `192.168.0.255`) comes free with integers. Forward iteration must still stop
at `255.255.255.255`.
""",
        """
**Idea:** a CIDR block is just a tighter `[low, high]`. Compute it from the prefix and reuse the
existing bounds check.

**Steps:** `ip, _, prefix = s.partition("/")`. If there's a prefix, `host_bits = 32 - int(prefix)`,
`mask = (0xFFFFFFFF << host_bits) & 0xFFFFFFFF`, `low = ip_int & mask`,
`high = low + (1 << host_bits) - 1`. Without one, keep the full range. Start at the given
address, not at `low`.

**Pitfalls:** Python ints don't wrap, so mask the shift to 32 bits. `/32` (zero host bits) yields
one address, `/31` yields two. A seed at the broadcast address going forward, or at the network
address going backward, yields only itself.
""",
        """
**Idea:** `step` only changes the delta; `next_batch` is a loop over `next(self)`, so both share
one cursor.

**Steps:** validate in `__init__`: `if step <= 0: raise ValueError(...)`, then
`delta = -step if reverse else step`. `next_batch(size)` appends `next(self)` up to `size` times
and stops early on `StopIteration`, returning what it has (`[]` when exhausted).

**Pitfalls:** raise in the constructor: the test never iterates, so a lazy check (or a generator
`__iter__`) misses it. Check bounds before yielding, so `255.255.255.250` with `step=4` gives
`.250, .254` and stops, with no wrap-around. Mixing `next()` and `next_batch()` must continue
from the same position.
""",
        """
**Idea:** greedy. From the current low address, take the largest block that is both aligned at
`low` and fits in what remains, then move past it.

**Steps:** with integers `low, high`: the largest aligned size is the lowest set bit,
`low & -low` (use `1 << 32` when `low == 0`). Halve it while it exceeds `high - low + 1`. Emit
`f"{int_to_ip(low)}/{32 - (size.bit_length() - 1)}"` and do `low += size`. Loop while `low <= high`.

**Complexity:** at most about 62 blocks, each found in O(32) steps.

**Pitfalls:** the whole space must be `0.0.0.0/0` (the `low == 0` case). A single address is
`/32`, and `255.255.255.254-255.255.255.255` is one `/31`. Aligned blocks only:
`10.0.0.1-10.0.1.0` needs nine blocks.
""",
    ],
    # ------------------------------------------------------------ monster battle
    "mp-monster-battle": [
        """
**Idea:** keep each rule in one place. `Monster` owns health, `Team` answers "who's first alive?"
and "am I defeated?", and `battle` only runs the turn loop and writes the log.

**Steps:** `get_first_alive` is `next((m for m in self.monsters if m.is_alive()), None)`;
`is_defeated` is `not any(m.is_alive() for m in self.monsters)`. Loop while neither team is
defeated: pick both first-alive monsters, apply damage, log, then swap
`attacking, defending = defending, attacking`. The winner is whichever team is not defeated.

**Pitfalls:** `is_alive` is `health > 0`, so exactly 0 HP is eliminated (tested). The log strings
must match exactly, punctuation included. Team B can win. `get_first_alive` returns `None`
on a wiped team, not an exception.
""",
        """
**Idea:** a lookup table beats a chain of `if`s: `TYPE_CHART = {(MonsterType.FIRE,
MonsterType.GRASS): 2.0, ...}` keyed by `(attacker type, defender type)`, with
`.get(pair, 1.0)` covering every other pair, including untyped monsters (`None`).

**Steps:** add `monster_type=None` as an optional fourth argument. `calculate_damage` returns
`int(self.attack * multiplier)`. In the log, compare damage with the base attack: greater adds
` (Super effective!)`, smaller adds ` (Not very effective...)`, both right after `damage`.

**Pitfalls:** `int()` truncates (`3 * 0.5` is `1`); `round()` gives different numbers. The chart
isn't symmetric: Electric to Water is 2x, Water to Electric is 1x. Fire to Grass is 2x, Grass to
Fire 0.5x. Untyped monsters must still work with no type argument.
""",
        """
**Idea:** only the attacker choice changes. Add `Team.get_best_attacker(defender)` and pick it
when the flag is on; the defender is still the first alive.

**Steps:** `max(alive, key=lambda m: m.calculate_damage(defender), default=None)`. `max` returns
the **first** maximal item, which is exactly the tie-break required. In `battle`, choose the
defender first, then `attacker = best if smart_targeting else first_alive`.

**Pitfalls:** a manual loop with `>=` picks the last of tied monsters (the "ties go to the
earliest monster" test). Keep `smart_targeting=False` as the default so earlier logs are
unchanged. Compute damage against the current defender, not the attacker's raw `attack`.
""",
    ],
    # ---------------------------------------------------------- file dedup
    "mp-file-dedup": [
        """
**Idea:** identical files have identical content hashes. Group every file path by a digest of
its bytes and keep the groups with two or more members.

**Steps:** `os.walk(root)` gives `(dirpath, dirnames, filenames)` for every directory; join with
`os.path.join`. For each file, open in `"rb"` and feed `hashlib.sha256()` in chunks
(`while chunk := f.read(65536): h.update(chunk)`), so a large file never sits in memory at once.
Collect into `defaultdict(list)` keyed by `hexdigest()`, then return
`[g for g in groups.values() if len(g) > 1]`.

**Pitfalls:** empty files are duplicates of each other. Same size does not mean same content.
Hash the whole file, not a prefix: the binary test differs only in the last byte. Read in binary
mode, not text.
""",
        """
**Idea:** decide what a path is before you open it, and treat any I/O error as "skip this file".

**Steps:** `os.walk` already doesn't descend into symlinked directories (`followlinks=False`),
but symlinks to files and broken links still show up in `filenames`, so skip any path where
`os.path.islink(path)` is true. Wrap the per-file `open`/hash in `try: ... except OSError:
continue`; `PermissionError` is a subclass.

**Pitfalls:** `os.path.isfile` follows links, so it doesn't filter them out; `pathlib`'s
`is_file()` doesn't either, check `is_symlink()` first. Loops (`loop -> .`, `up -> ..`) and the
broken link must not be reported or followed. Catch the error per file, so one unreadable file
doesn't abort the whole walk.
""",
        """
**Idea:** filter cheapest first. Size comes from metadata (no read), then a 1 KB prefix, then
the full content, and each stage only looks at files still tied after the one before.

**Steps:** group by `os.path.getsize` (a `stat`, the file is never opened); drop singleton sizes.
Size 0 groups are duplicates already. Within each size group, hash `f.read(1024)` and drop
singletons again. If the size is at most 1 KB, the prefix was the whole file; otherwise
full-hash the survivors in chunks.

**Complexity:** one `stat` per file; full reads only for files that share both size and prefix.

**Pitfalls:** opening every file "just to check" breaks the never-opened rule. A file with a
unique prefix must not reach the full hash (64 KB limit). Same prefix, different tail still needs
the full hash. Keep part 2's symlink and `OSError` handling at every stage.
""",
    ],
    # ---------------------------------------------------------- cluster messages
    "mp-cluster-messages": [
        """
**Idea:** scatter-gather down the tree. Each node asks its children, waits for every reply, and
sends `1 + sum(replies)` to its parent. A leaf answers `1` at once; the root prints instead of
replying.

**Steps:** on `fromNodeId is None`, the root starts a job. On a request, a node with no children
replies immediately; otherwise it records which children it is waiting for and forwards the
request. On a reply, add the number and remove that child from the waiting set; when it's empty,
finish. Use a simple string protocol such as `"REQ|count"` and `"RES|count|5"`.

**Pitfalls:** delivery order is arbitrary (LIFO, random), so never assume replies arrive in
order. A lone root must print `1` with no messages. Clear per-job state when a job finishes so a
second `"count"` starts fresh. No stray prints.
""",
        """
**Idea:** the same scatter-gather with a different combine step, so make the job kind part of
every message and share one code path for both jobs.

**Steps:** messages carry the kind, e.g. `"REQ|topology"` and `"RES|topology|<payload>"`. Store
each reply in a dict keyed by child id. When all children have answered, a leaf's answer is its
id and an inner node's is `f"{id}({','.join(results[c] for c in self.children)})"`. Count keeps
its `1 + sum` combine.

**Pitfalls:** build the string in `children` list order, not reply-arrival order. The payload
contains commas and parentheses, so split with a `maxsplit` (`message.split("|", 2)`) and keep
the payload last. Ids can be non-numeric strings. Count and topology jobs alternate on the same
cluster.
""",
        """
**Idea:** make every handler idempotent. Give each job a unique id, and let nodes remember which
requests they have started and which children they are still waiting for.

**Steps:** the root assigns an id from a counter (`f"{kind}-{n}"`) and every message carries it.
A node keeps `self._seen` (job ids already started) and ignores a request whose id is in it. Per
job it keeps a `waiting` set of child ids; a reply counts only if the sender is still in that set.
When the set empties, delete the job's pending state but keep its id in `_seen`.

**Pitfalls:** an integer "replies received" counter double-counts duplicates and finishes early
with a wrong answer. A duplicate request arriving after the job finished must not restart it (and
print again). Job ids must differ between repeated jobs of the same kind.
""",
    ],
    # --------------------------------------------------------------- GPU credits
    "mp-gpu-credits": [
        """
**Idea:** with no usage yet, the balance at `t` is just the sum of the grants active at `t`.
Store every grant and answer each query from that list, so call order doesn't matter.

**Steps:** `add_credit` appends `(timestamp, timestamp + expiration, amount)`. `get_balance(t)`
collects the amounts with `start <= t <= end`; return `None` if there are none, otherwise their
sum.

**Complexity:** O(grants) per query, which is fine here.

**Pitfalls:** both ends are inclusive: a grant from 10 with expiration 20 is active at 30, gone
at 31. `expiration` is a duration, not an end time. A zero-length grant is active only at its
own timestamp. A query made before an earlier grant was recorded must not be cached.
""",
        """
**Idea:** usage depends on history, so replay all events up to `t` in time order, with a
min-heap of live grants keyed by expiry.

**Steps:** keep every event; on a query, sort the events with `timestamp <= t` and walk them.
Before each event, pop grants whose end is `< now`. A grant first pays off any debt, then pushes
`[end, remaining]` onto a `heapq`. A usage burns from `heap[0]` (soonest expiry) across grants;
any shortfall becomes debt. Track the latest end among applied grants, since a fully burnt grant
leaves the heap but is still active. After expiring at `t`, the balance is
`sum(remaining) - debt`: `None` if no grant is active or it's negative, else the number.

**Pitfalls:** grants that haven't started, or have expired, can't be burnt. Usage recorded before
its grant still applies. A balance of 0 is `0`. Events recorded after a later query must change
the answer.
""",
        """
**Idea:** the workload arrives in time order, so don't replay from the start on every query.
Keep the replay state (cursor, heap, debt) and only apply the new events since the last query.

**Steps:** keep events sorted with `bisect.insort` (appending at the end in this workload). Store
the time the replay has reached. A query at or after it advances the cursor over events
`<= t`. Reset the state and replay from scratch only when an event is inserted at or before the
replayed time, or a query goes back in time.

**Complexity:** O(log n) heap work per event for in-order traffic, instead of O(n log n) per
query.

**Pitfalls:** forgetting to invalidate on out-of-order inserts breaks every part 2 test. Keep a
running total of remaining credit instead of summing the heap on each query.
""",
    ],
}
