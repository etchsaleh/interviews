"""Interview-focus problems: graphs, queues, caching and basic Python OOP.

These are deliberately *not* verbatim LeetCode problems: each has a small twist
(tie-breaking rules, extra constraints, a different return shape) so you practise
adapting a known technique rather than recalling a memorised answer.
`followups` lists further twists to try on your own once the tests pass.
"""
import mock_api
from runner import RUN_ID


def _prices_cached(test, actual, call_args):
    skus = test["args"][0]
    client = call_args[-1]
    if actual != [mock_api.price_for(s) for s in skus]:
        return False
    calls = mock_api.PRICE_CALLS.get(client, {})
    return all(calls.get(s, 0) == 1 for s in set(skus)) and set(calls) <= set(skus)


PROBLEMS = [
    # ------------------------------------------------------------------ graphs
    {
        "id": "build-order",
        "title": "Build Order",
        "difficulty": "Medium",
        "category": "Graphs",
        "tags": ["topological sort", "heapq", "cycle detection"],
        "entry": "build_order",
        "description": """
A CI system has `tasks` (unique names) and `deps`, where `[a, b]` means **`a` must finish
before `b` starts**. Return an order to run every task.

**Twist:** whenever several tasks are ready at the same time, run the alphabetically
smallest one first (so the answer is unique). If the dependencies contain a cycle, return `[]`.

```
build_order(["deploy", "build", "test", "lint"],
            [["build", "test"], ["lint", "test"], ["test", "deploy"]])
  -> ["build", "lint", "test", "deploy"]
```
""",
        "java_tip": """
- Adjacency list: `graph = defaultdict(list)`; in-degrees: `indegree = {t: 0 for t in tasks}`.
- "Smallest ready task first" = a min-heap instead of a FIFO queue: `heapq.heappush(ready, name)` — strings compare alphabetically.
- Cycle check: if you emitted fewer than `len(tasks)` names, something never reached in-degree 0.
""",
        "followups": [
            "Return the tasks grouped into parallel 'waves' (everything in a wave can run at once).",
            "Each task has a duration — what's the minimum total time with unlimited workers?",
            "Instead of `[]`, return one cycle so the user can fix their config.",
        ],
        "starter": """def build_order(tasks: list[str], deps: list[list[str]]) -> list[str]:
    pass
""",
        "solution": """import heapq
from collections import defaultdict


def build_order(tasks: list[str], deps: list[list[str]]) -> list[str]:
    graph = defaultdict(list)
    indegree = {t: 0 for t in tasks}
    for before, after in deps:
        graph[before].append(after)
        indegree[after] += 1

    ready = [t for t, d in indegree.items() if d == 0]
    heapq.heapify(ready)
    order = []
    while ready:
        task = heapq.heappop(ready)
        order.append(task)
        for nxt in graph[task]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                heapq.heappush(ready, nxt)
    return order if len(order) == len(tasks) else []
""",
        "tests": [
            {"args": [["deploy", "build", "test", "lint"], [["build", "test"], ["lint", "test"], ["test", "deploy"]]],
             "expected": ["build", "lint", "test", "deploy"]},
            {"args": [["c", "a", "b"], []], "expected": ["a", "b", "c"]},
            {"args": [["x", "y", "z", "w"], [["z", "x"]]], "expected": ["w", "y", "z", "x"]},
            {"args": [["a", "b", "c"], [["a", "b"], ["b", "c"], ["c", "a"]]], "expected": []},
            {"args": [["a", "b", "c", "d"], [["a", "b"], ["b", "c"], ["c", "b"]]], "expected": []},
        ],
    },
    {
        "id": "fewest-hops",
        "title": "Fewest Hops Around Outages",
        "difficulty": "Medium",
        "category": "Graphs",
        "tags": ["BFS", "shortest path", "set"],
        "entry": "fewest_hops",
        "description": """
Services talk over bidirectional `links` (`[a, b]` = a and b can call each other). Some
services are currently `down` and can't be routed through.

Return the minimum number of hops from `start` to `target` without touching a down
service, or `-1` if it's impossible (including when `start` or `target` is down).
`start == target` is 0 hops.

```
links = [["api", "auth"], ["api", "cache"], ["cache", "db"], ["auth", "db"]]
fewest_hops(links, [], "api", "db")                 -> 2
fewest_hops(links, ["cache", "auth"], "api", "db")  -> -1
```
""",
        "java_tip": """
- Unweighted shortest path = BFS. `deque([(start, 0)])` stores (node, distance) tuples.
- `down = set(down)` once, so membership checks are O(1).
- Undirected edge: add both directions — `graph[a].append(b); graph[b].append(a)`.
""",
        "followups": [
            "Return the actual path, not just its length (track a `parent` dict).",
            "Links now have latencies — return the lowest total latency (Dijkstra).",
            "Find which single service, if it went down, would disconnect start from target.",
        ],
        "starter": """def fewest_hops(links: list[list[str]], down: list[str], start: str, target: str) -> int:
    pass
""",
        "solution": """from collections import defaultdict, deque


def fewest_hops(links: list[list[str]], down: list[str], start: str, target: str) -> int:
    down = set(down)
    if start in down or target in down:
        return -1
    graph = defaultdict(list)
    for a, b in links:
        graph[a].append(b)
        graph[b].append(a)

    seen = {start}
    queue = deque([(start, 0)])
    while queue:
        node, hops = queue.popleft()
        if node == target:
            return hops
        for nxt in graph[node]:
            if nxt not in seen and nxt not in down:
                seen.add(nxt)
                queue.append((nxt, hops + 1))
    return -1
""",
        "tests": [
            {"args": [[["api", "auth"], ["api", "cache"], ["cache", "db"], ["auth", "db"]], [], "api", "db"], "expected": 2},
            {"args": [[["api", "auth"], ["api", "cache"], ["cache", "db"], ["auth", "db"]], ["cache"], "api", "db"], "expected": 2},
            {"args": [[["api", "auth"], ["api", "cache"], ["cache", "db"], ["auth", "db"]], ["cache", "auth"], "api", "db"], "expected": -1},
            {"args": [[["api", "auth"]], [], "api", "api"], "expected": 0},
            {"args": [[["api", "auth"]], ["auth"], "api", "auth"], "expected": -1},
            {"args": [[["a", "b"], ["b", "c"], ["c", "d"], ["d", "e"], ["a", "d"]], [], "a", "e"], "expected": 2},
            {"args": [[["a", "b"], ["b", "c"], ["c", "d"], ["d", "e"], ["a", "d"]], ["d"], "a", "e"], "expected": -1},
        ],
    },
    {
        "id": "broadcast-time",
        "title": "Config Broadcast Time",
        "difficulty": "Medium",
        "category": "Graphs",
        "tags": ["Dijkstra", "heapq", "weighted graph"],
        "entry": "broadcast_time",
        "description": """
There are `n` servers labelled `1..n`. `links[i] = [u, v, ms]` means server `u` can push
to server `v` (one direction) in `ms` milliseconds. A config change starts at `source`
and every server forwards it as soon as it arrives.

Return how long until **every** server has the config, or `-1` if some server never gets it.

```
broadcast_time(4, [[2, 1, 1], [2, 3, 1], [3, 4, 1]], 2) -> 2
```
""",
        "java_tip": """
- Dijkstra with `heapq`: push `(distance, node)` tuples; the heap orders by distance first.
- Skip stale heap entries: `if node in done: continue`.
- `max(dist.values())` once every node is in `dist`.
""",
        "followups": [
            "Return `[time, last_server]` — which server gets it last (smallest label on ties)?",
            "Each server needs `k` ms to apply the config before forwarding it.",
            "A link can be used at most once per second — does that change anything?",
        ],
        "starter": """def broadcast_time(n: int, links: list[list[int]], source: int) -> int:
    pass
""",
        "solution": """import heapq
from collections import defaultdict


def broadcast_time(n: int, links: list[list[int]], source: int) -> int:
    graph = defaultdict(list)
    for u, v, ms in links:
        graph[u].append((v, ms))

    dist = {}
    heap = [(0, source)]
    while heap:
        time, node = heapq.heappop(heap)
        if node in dist:
            continue
        dist[node] = time
        for nxt, ms in graph[node]:
            if nxt not in dist:
                heapq.heappush(heap, (time + ms, nxt))
    return max(dist.values()) if len(dist) == n else -1
""",
        "tests": [
            {"args": [4, [[2, 1, 1], [2, 3, 1], [3, 4, 1]], 2], "expected": 2},
            {"args": [2, [[1, 2, 1]], 1], "expected": 1},
            {"args": [2, [[1, 2, 1]], 2], "expected": -1},
            {"args": [4, [[1, 2, 4], [1, 3, 1], [3, 2, 1], [2, 4, 1]], 1], "expected": 3},
            {"args": [1, [], 1], "expected": 0},
        ],
    },
    {
        "id": "team-groups",
        "title": "Team Groups",
        "difficulty": "Medium",
        "category": "Graphs",
        "tags": ["union find", "connected components", "DFS"],
        "entry": "team_groups",
        "description": """
`n` engineers are numbered `0..n-1`. Each pair `[a, b]` means they have worked together;
"worked together" is transitive, so groups form.

**Twist:** return `[number_of_groups, size_of_largest_group]`.

```
team_groups(5, [[0, 1], [1, 2], [3, 4]]) -> [2, 3]
team_groups(4, [])                        -> [4, 1]
```
""",
        "java_tip": """
- Union-Find fits in a few lines with a list: `parent = list(range(n))`.
- `Counter(find(i) for i in range(n))` gives the size of every group in one go.
- Or DFS from every unvisited node — either is fine in an interview; pick the one you can write fastest.
""",
        "followups": [
            "Pairs arrive one at a time: after each, report the number of groups.",
            "Return the groups themselves, each sorted, largest group first.",
            "Which single pair, if removed, would split the biggest group?",
        ],
        "starter": """def team_groups(n: int, pairs: list[list[int]]) -> list[int]:
    pass
""",
        "solution": """from collections import Counter


def team_groups(n: int, pairs: list[list[int]]) -> list[int]:
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in pairs:
        parent[find(a)] = find(b)

    sizes = Counter(find(i) for i in range(n))
    return [len(sizes), max(sizes.values())]
""",
        "tests": [
            {"args": [5, [[0, 1], [1, 2], [3, 4]]], "expected": [2, 3]},
            {"args": [4, []], "expected": [4, 1]},
            {"args": [6, [[0, 1], [2, 3], [4, 5], [1, 3]]], "expected": [2, 4]},
            {"args": [1, []], "expected": [1, 1]},
            {"args": [3, [[0, 1], [1, 0], [0, 0]]], "expected": [2, 2]},
        ],
    },
    # ------------------------------------------------------------------ queues
    {
        "id": "moving-average",
        "title": "Moving Average of a Stream",
        "difficulty": "Easy",
        "category": "Queues",
        "tags": ["deque", "class design", "stream"],
        "entry": "MovingAverage",
        "mode": "class",
        "description": """
Implement `MovingAverage(size)` with a method `next(value) -> float` that returns the
average of the last `size` values seen (or of all values, if fewer than `size` so far).
Each call should be O(1).

```
m = MovingAverage(3)
m.next(1) -> 1.0
m.next(3) -> 2.0
m.next(5) -> 3.0
m.next(7) -> 5.0     # (3 + 5 + 7) / 3
```
""",
        "java_tip": """
- `deque(maxlen=size)` drops the oldest item automatically when full — but you still need the dropped value to keep a running sum. Check `len(q) == size` *before* appending.
- Keep a running `self.total` instead of `sum(q)` every call.
- `/` always returns a float, which is exactly what you want here.
""",
        "followups": [
            "Make the window time-based: average of values from the last `w` seconds.",
            "Also support `max()` over the current window in O(1) amortised (monotonic deque).",
        ],
        "starter": """class MovingAverage:
    def __init__(self, size: int):
        pass

    def next(self, value: int) -> float:
        pass
""",
        "solution": """from collections import deque


class MovingAverage:
    def __init__(self, size: int):
        self.size = size
        self.window = deque()
        self.total = 0

    def next(self, value: int) -> float:
        if len(self.window) == self.size:
            self.total -= self.window.popleft()
        self.window.append(value)
        self.total += value
        return self.total / len(self.window)
""",
        "tests": [
            {"args": [["MovingAverage", "next", "next", "next", "next"], [[3], [1], [3], [5], [7]]],
             "expected": [None, 1.0, 2.0, 3.0, 5.0]},
            {"args": [["MovingAverage", "next", "next", "next"], [[1], [4], [-2], [10]]],
             "expected": [None, 4.0, -2.0, 10.0]},
        ],
    },
    {
        "id": "rate-limiter",
        "title": "Sliding-Window Rate Limiter",
        "difficulty": "Medium",
        "category": "Queues",
        "tags": ["deque", "sliding window", "class design"],
        "entry": "RateLimiter",
        "mode": "class",
        "description": """
Implement `RateLimiter(max_requests, window)` with `allow(timestamp) -> bool`.

A request at time `t` is allowed if fewer than `max_requests` **allowed** requests happened
in the window `(t - window, t]`. Rejected requests don't count. Timestamps are integer
seconds and never decrease.

```
r = RateLimiter(3, 10)
r.allow(1)  -> True
r.allow(2)  -> True
r.allow(3)  -> True
r.allow(4)  -> False   # 3 requests already in (−6, 4]
r.allow(11) -> True    # the request at t=1 has left the window (1, 11]
```
""",
        "java_tip": """
- A `deque` of accepted timestamps: evict from the left while `q[0] <= t - window`.
- `while q and q[0] <= cutoff:` — an empty deque is falsy, so this is safe.
- Methods return a `bool` — Python's `True`/`False`.
""",
        "followups": [
            "Limit per user: `allow(user_id, timestamp)`.",
            "Memory is tight: implement a fixed-window counter instead, and explain the burst problem at window edges.",
            "Token bucket: `capacity` tokens, refilled at `rate` per second.",
        ],
        "starter": """class RateLimiter:
    def __init__(self, max_requests: int, window: int):
        pass

    def allow(self, timestamp: int) -> bool:
        pass
""",
        "solution": """from collections import deque


class RateLimiter:
    def __init__(self, max_requests: int, window: int):
        self.max_requests = max_requests
        self.window = window
        self.accepted = deque()

    def allow(self, timestamp: int) -> bool:
        while self.accepted and self.accepted[0] <= timestamp - self.window:
            self.accepted.popleft()
        if len(self.accepted) < self.max_requests:
            self.accepted.append(timestamp)
            return True
        return False
""",
        "tests": [
            {"args": [["RateLimiter", "allow", "allow", "allow", "allow", "allow", "allow", "allow"],
                      [[3, 10], [1], [2], [3], [4], [11], [12], [12]]],
             "expected": [None, True, True, True, False, True, True, False]},
            {"args": [["RateLimiter", "allow", "allow", "allow", "allow", "allow"],
                      [[1, 5], [0], [4], [5], [9], [10]]],
             "expected": [None, True, False, True, False, True]},
        ],
    },
    {
        "id": "round-robin",
        "title": "Round-Robin Job Runner",
        "difficulty": "Medium",
        "category": "Queues",
        "tags": ["deque", "simulation"],
        "entry": "round_robin",
        "description": """
A single worker runs `jobs` (`[name, duration]`, in arrival order) round-robin with a time
slice of `quantum`: the job at the front runs for `min(quantum, remaining)`; if it isn't
finished it goes to the **back** of the queue. Time starts at 0.

Return `[name, finish_time]` for every job, in the order they **finish**.

```
round_robin([["A", 5], ["B", 2], ["C", 4]], 2)
  -> [["B", 4], ["C", 10], ["A", 11]]
```
""",
        "java_tip": """
- `deque` of `[name, remaining]` pairs; `popleft()` to run, `append()` to requeue.
- Unpack in one line: `name, remaining = queue.popleft()`.
- Simulation problems are where Python's brevity saves the most time — write it directly.
""",
        "followups": [
            "Jobs have arrival times — a job can't run before it arrives (the worker may idle).",
            "Two workers pull from the same queue. What's the finish order now?",
            "Jobs have priorities: higher priority always runs first; round-robin among equals.",
        ],
        "starter": """def round_robin(jobs: list[list], quantum: int) -> list[list]:
    pass
""",
        "solution": """from collections import deque


def round_robin(jobs: list[list], quantum: int) -> list[list]:
    queue = deque([name, duration] for name, duration in jobs)
    time = 0
    finished = []
    while queue:
        name, remaining = queue.popleft()
        run = min(quantum, remaining)
        time += run
        if remaining - run > 0:
            queue.append([name, remaining - run])
        else:
            finished.append([name, time])
    return finished
""",
        "tests": [
            {"args": [[["A", 5], ["B", 2], ["C", 4]], 2], "expected": [["B", 4], ["C", 10], ["A", 11]]},
            {"args": [[["X", 1]], 3], "expected": [["X", 1]]},
            {"args": [[["A", 3], ["B", 3]], 3], "expected": [["A", 3], ["B", 6]]},
            {"args": [[], 1], "expected": []},
            {"args": [[["A", 2], ["B", 1], ["C", 2]], 1], "expected": [["B", 2], ["A", 4], ["C", 5]]},
        ],
    },
    {
        "id": "ticket-queue",
        "title": "Support Ticket Priority Queue",
        "difficulty": "Medium",
        "category": "Queues",
        "tags": ["heapq", "tie-breaking", "class design"],
        "entry": "TicketQueue",
        "mode": "class",
        "description": """
Implement `TicketQueue` with:

- `add(ticket_id, priority)` — higher number = more urgent
- `next()` — remove and return the most urgent ticket id; among equal priorities, the one
  added **first** wins. Return `None` if the queue is empty.

```
q = TicketQueue()
q.add("t1", 1); q.add("t2", 5); q.add("t3", 5); q.add("t4", 3)
q.next() -> "t2"
q.next() -> "t3"
q.next() -> "t4"
q.next() -> "t1"
q.next() -> None
```
""",
        "java_tip": """
- `heapq` is a **min**-heap: store `(-priority, counter, ticket_id)` to get max-priority first.
- The increasing `counter` gives FIFO among ties — Java's `PriorityQueue` isn't stable either.
- `itertools.count()` is a tidy infinite counter: `next(self._counter)`.
""",
        "followups": [
            "Add `cancel(ticket_id)` in O(log n) or better (hint: lazy deletion).",
            "Tickets waiting longer than `t` seconds get bumped one priority level.",
        ],
        "starter": """class TicketQueue:
    def __init__(self):
        pass

    def add(self, ticket_id: str, priority: int) -> None:
        pass

    def next(self) -> str | None:
        pass
""",
        "solution": """import heapq
import itertools


class TicketQueue:
    def __init__(self):
        self._heap = []
        self._counter = itertools.count()

    def add(self, ticket_id: str, priority: int) -> None:
        heapq.heappush(self._heap, (-priority, next(self._counter), ticket_id))

    def next(self) -> str | None:
        if not self._heap:
            return None
        return heapq.heappop(self._heap)[2]
""",
        "tests": [
            {"args": [["TicketQueue", "add", "add", "add", "add", "next", "next", "next", "next", "next"],
                      [[], ["t1", 1], ["t2", 5], ["t3", 5], ["t4", 3], [], [], [], [], []]],
             "expected": [None, None, None, None, None, "t2", "t3", "t4", "t1", None]},
            {"args": [["TicketQueue", "next", "add", "add", "next", "add", "next", "next"],
                      [[], [], ["a", 2], ["b", 2], [], ["c", 9], [], []]],
             "expected": [None, None, None, None, "a", None, "c", "b"]},
        ],
    },
    # ----------------------------------------------------------------- caching
    {
        "id": "cache-hit-rate",
        "title": "Cache Hit Counter",
        "difficulty": "Easy",
        "category": "Caching",
        "tags": ["OrderedDict", "LRU", "simulation"],
        "entry": "cache_stats",
        "description": """
Simulate an **LRU** cache of size `capacity` over a stream of key `requests`. A request is a
*hit* if the key is in the cache; otherwise it's a *miss* and the key gets inserted
(evicting the least recently used key if the cache is full).

Return `[hits, misses]`.

```
cache_stats([1, 2, 1, 3, 2, 4, 1], 2) -> [1, 6]
```
""",
        "java_tip": """
- `OrderedDict` remembers order: `move_to_end(key)` on access, `popitem(last=False)` evicts the oldest.
- A plain `dict` keeps insertion order too; `del d[k]; d[k] = v` moves a key to the end.
- Watch the `capacity == 0` edge case.
""",
        "followups": [
            "Same stream, but FIFO eviction instead of LRU — which gets more hits here?",
            "Find the smallest capacity that achieves at least a 50% hit rate.",
        ],
        "starter": """def cache_stats(requests: list[int], capacity: int) -> list[int]:
    pass
""",
        "solution": """from collections import OrderedDict


def cache_stats(requests: list[int], capacity: int) -> list[int]:
    cache = OrderedDict()
    hits = misses = 0
    for key in requests:
        if key in cache:
            hits += 1
            cache.move_to_end(key)
            continue
        misses += 1
        if capacity == 0:
            continue
        if len(cache) >= capacity:
            cache.popitem(last=False)
        cache[key] = True
    return [hits, misses]
""",
        "tests": [
            {"args": [[1, 2, 1, 3, 2, 4, 1], 2], "expected": [1, 6]},
            {"args": [[1, 1, 1], 0], "expected": [0, 3]},
            {"args": [[1, 1, 1, 2], 3], "expected": [2, 2]},
            {"args": [[], 5], "expected": [0, 0]},
            {"args": [[1, 2, 3, 1, 2, 3], 3], "expected": [3, 3]},
        ],
    },
    {
        "id": "ttl-cache",
        "title": "LRU Cache with Expiry",
        "difficulty": "Medium",
        "category": "Caching",
        "tags": ["OrderedDict", "TTL", "class design"],
        "entry": "TTLCache",
        "mode": "class",
        "description": """
Implement `TTLCache(capacity)`:

- `put(key, value, ttl, now)` — store `value`, expiring at `now + ttl`. An entry is
  expired when the current time is `>= now + ttl`.
- `get(key, now)` — the value, or `-1` if missing or expired. A successful get marks the key
  as recently used.

**Twist on eviction:** when a `put` would exceed `capacity`, first drop *all expired*
entries; only if still over capacity, evict the least recently used one.

```
c = TTLCache(2)
c.put("a", 1, 2, 0)     # expires at 2
c.put("b", 2, 100, 0)
c.get("a", 1)  -> 1     # "a" is now most recently used
c.put("c", 3, 100, 5)   # "a" has expired -> drop it, keep "b"
c.get("b", 6)  -> 2
```
""",
        "java_tip": """
- Store `key -> (value, expires_at)` tuples in an `OrderedDict`.
- Build a list of expired keys first, then delete — you can't delete from a dict while iterating it.
- Since `now` is passed in, no `time.time()` needed; that also makes it testable.
""",
        "followups": [
            "Make expired-entry cleanup O(1) amortised instead of a scan (hint: a heap of expiry times).",
            "Add `stats()` returning hits, misses and evictions.",
            "Multiple threads use the cache — what needs a lock?",
        ],
        "starter": """class TTLCache:
    def __init__(self, capacity: int):
        pass

    def get(self, key: str, now: int) -> int:
        pass

    def put(self, key: str, value: int, ttl: int, now: int) -> None:
        pass
""",
        "solution": """from collections import OrderedDict


class TTLCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self._data = OrderedDict()  # key -> (value, expires_at)

    def get(self, key: str, now: int) -> int:
        entry = self._data.get(key)
        if entry is None:
            return -1
        value, expires_at = entry
        if now >= expires_at:
            del self._data[key]
            return -1
        self._data.move_to_end(key)
        return value

    def put(self, key: str, value: int, ttl: int, now: int) -> None:
        self._data[key] = (value, now + ttl)
        self._data.move_to_end(key)
        if len(self._data) > self.capacity:
            expired = [k for k, (_, exp) in self._data.items() if now >= exp]
            for k in expired:
                del self._data[k]
        while len(self._data) > self.capacity:
            self._data.popitem(last=False)
""",
        "tests": [
            {"args": [["TTLCache", "put", "put", "get", "get", "put", "get", "get"],
                      [[2], ["a", 1, 10, 0], ["b", 2, 5, 0], ["a", 3], ["b", 6], ["c", 3, 10, 6], ["a", 7], ["c", 7]]],
             "expected": [None, None, None, 1, -1, None, 1, 3]},
            {"args": [["TTLCache", "put", "put", "get", "put", "get", "get", "get"],
                      [[2], ["a", 1, 100, 0], ["b", 2, 100, 1], ["a", 2], ["c", 3, 100, 3], ["b", 4], ["a", 4], ["c", 4]]],
             "expected": [None, None, None, 1, None, -1, 1, 3]},
            {"args": [["TTLCache", "put", "put", "get", "put", "get", "get", "get"],
                      [[2], ["a", 1, 2, 0], ["b", 2, 100, 0], ["a", 1], ["c", 3, 100, 5], ["b", 6], ["c", 6], ["a", 6]]],
             "expected": [None, None, None, 1, None, 2, 3, -1]},
            {"args": [["TTLCache", "put", "put", "get"], [[1], ["k", 1, 10, 0], ["k", 2, 10, 1], ["k", 2]]],
             "expected": [None, None, None, 2]},
        ],
    },
    {
        "id": "cached-prices",
        "title": "Cache Slow API Lookups",
        "difficulty": "Medium",
        "category": "Caching",
        "tags": ["GET", "memoization", "dict"],
        "entry": "get_prices",
        "needs_base_url": True,
        "validator": _prices_cached,
        "description": """
`GET {base_url}/price/<sku>?client=<client_id>` returns `{"sku": "A1", "price": 33.99}`,
but it's slow. Given a list of `skus` (with repeats), return their prices **in the same
order** as the input — calling the endpoint **at most once per distinct SKU**.

Always pass the given `client_id` as the `client` query parameter: the grader uses it to
count how many times you hit the endpoint.

```
get_prices(base_url, ["A1", "B2", "A1"], client_id) -> [33.99, 35.99, 33.99]   # 2 HTTP calls
```
""",
        "java_tip": """
- A dict as a cache: `if sku not in cache: cache[sku] = fetch(sku)`.
- Or decorate a helper with `@functools.cache` — Python's built-in memoization.
- `[cache[s] for s in skus]` rebuilds the answer in input order.
""",
        "followups": [
            "The endpoint also has a batch form: `GET /prices?skus=A1,B2` — how would you use it?",
            "Prices change: cache them for at most 60 seconds.",
            "Fetch the distinct SKUs concurrently (`concurrent.futures.ThreadPoolExecutor`).",
        ],
        "starter": """import requests


def get_prices(base_url: str, skus: list[str], client_id: str) -> list[float]:
    pass
""",
        "solution": """import requests


def get_prices(base_url: str, skus: list[str], client_id: str) -> list[float]:
    cache = {}
    for sku in skus:
        if sku not in cache:
            resp = requests.get(f"{base_url}/price/{sku}", params={"client": client_id}, timeout=5)
            resp.raise_for_status()
            cache[sku] = resp.json()["price"]
    return [cache[sku] for sku in skus]
""",
        "tests": [
            {"args": [["A1", "B2", "A1", "A1", "C3", "B2"], RUN_ID],
             "expected_label": f"{[mock_api.price_for(s) for s in ['A1', 'B2', 'A1', 'A1', 'C3', 'B2']]} with exactly 3 HTTP calls"},
            {"args": [["Z9"] * 5, RUN_ID], "expected_label": f"{[mock_api.price_for('Z9')] * 5} with exactly 1 HTTP call"},
            {"args": [[], RUN_ID], "expected_label": "[] with no HTTP calls"},
        ],
    },
    # --------------------------------------------------------------------- OOP
    {
        "id": "bank-accounts",
        "title": "Bank Accounts",
        "difficulty": "Easy",
        "category": "Python OOP",
        "tags": ["class design", "dict", "validation"],
        "entry": "Bank",
        "mode": "class",
        "description": """
Implement a `Bank` class:

| Method | Returns |
|---|---|
| `open(account_id, initial)` | `True`, or `False` if the id exists or `initial < 0` |
| `deposit(account_id, amount)` | new balance, or `-1` if the account is unknown or `amount <= 0` |
| `withdraw(account_id, amount)` | new balance, or `-1` if unknown, `amount <= 0`, or insufficient funds |
| `transfer(src, dst, amount)` | `True` if it succeeded, else `False` (and no money moves) |
| `balance(account_id)` | the balance, or `-1` if unknown |
""",
        "java_tip": """
- One `dict` of `account_id -> balance` is all the state you need: `self.accounts = {}`.
- Every method takes `self` first; there's no `private`, `final` or getters/setters ceremony.
- Reuse your own methods: `transfer` can validate, then call `withdraw` and `deposit`.
- Interviews rarely need more OOP than this — a class, `__init__`, a few methods.
""",
        "followups": [
            "Keep a transaction history per account and add `statement(account_id)`.",
            "Add an overdraft limit per account.",
            "Rewrite with an `Account` class (a `@dataclass`) and discuss which design you prefer.",
        ],
        "starter": """class Bank:
    def __init__(self):
        pass

    def open(self, account_id: str, initial: int) -> bool:
        pass

    def deposit(self, account_id: str, amount: int) -> int:
        pass

    def withdraw(self, account_id: str, amount: int) -> int:
        pass

    def transfer(self, src: str, dst: str, amount: int) -> bool:
        pass

    def balance(self, account_id: str) -> int:
        pass
""",
        "solution": """class Bank:
    def __init__(self):
        self.accounts = {}

    def open(self, account_id: str, initial: int) -> bool:
        if account_id in self.accounts or initial < 0:
            return False
        self.accounts[account_id] = initial
        return True

    def deposit(self, account_id: str, amount: int) -> int:
        if account_id not in self.accounts or amount <= 0:
            return -1
        self.accounts[account_id] += amount
        return self.accounts[account_id]

    def withdraw(self, account_id: str, amount: int) -> int:
        if account_id not in self.accounts or amount <= 0 or self.accounts[account_id] < amount:
            return -1
        self.accounts[account_id] -= amount
        return self.accounts[account_id]

    def transfer(self, src: str, dst: str, amount: int) -> bool:
        if dst not in self.accounts or self.withdraw(src, amount) == -1:
            return False
        self.deposit(dst, amount)
        return True

    def balance(self, account_id: str) -> int:
        return self.accounts.get(account_id, -1)
""",
        "tests": [
            {"args": [["Bank", "open", "open", "open", "deposit", "withdraw", "withdraw", "transfer", "transfer",
                       "balance", "balance", "deposit"],
                      [[], ["alice", 100], ["bob", 50], ["alice", 10], ["alice", 25], ["bob", 80], ["bob", 20],
                       ["alice", "bob", 100], ["alice", "bob", 500], ["alice"], ["bob"], ["carol", 5]]],
             "expected": [None, True, True, False, 125, -1, 30, True, False, 25, 130, -1]},
            {"args": [["Bank", "open", "open", "deposit", "transfer", "balance", "withdraw", "balance"],
                      [[], ["x", -5], ["x", 10], ["x", -3], ["x", "nobody", 5], ["x"], ["x", 10], ["x"]]],
             "expected": [None, False, True, -1, False, 10, 0, 0]},
        ],
    },
    {
        "id": "leaderboard",
        "title": "Leaderboard",
        "difficulty": "Medium",
        "category": "Python OOP",
        "tags": ["class design", "sorting", "heapq"],
        "entry": "Leaderboard",
        "mode": "class",
        "description": """
Implement a `Leaderboard`:

- `add_score(player, points)` — add `points` to the player's total (new players start at 0)
- `top(k)` — the names of the top `k` players by total, highest first; **ties broken by
  name alphabetically**. If there are fewer than `k` players, return all of them.
- `reset(player)` — remove the player from the board

```
b = Leaderboard()
b.add_score("ann", 50); b.add_score("bob", 80); b.add_score("cat", 50); b.add_score("ann", 40)
b.top(2) -> ["ann", "bob"]     # ann 90, bob 80
b.reset("bob")
b.top(2) -> ["ann", "cat"]
```
""",
        "java_tip": """
- Sort by two keys with a tuple: `sorted(scores, key=lambda p: (-scores[p], p))` — negate for descending.
- `heapq.nsmallest(k, scores, key=...)` avoids sorting everything when `k` is small.
- `self.scores.pop(player, None)` removes without raising if the player is absent.
""",
        "followups": [
            "Add `rank(player)` — what data structure makes it fast?",
            "Only the last 7 days of scores count (each score has a timestamp).",
        ],
        "starter": """class Leaderboard:
    def __init__(self):
        pass

    def add_score(self, player: str, points: int) -> None:
        pass

    def top(self, k: int) -> list[str]:
        pass

    def reset(self, player: str) -> None:
        pass
""",
        "solution": """import heapq
from collections import defaultdict


class Leaderboard:
    def __init__(self):
        self.scores = defaultdict(int)

    def add_score(self, player: str, points: int) -> None:
        self.scores[player] += points

    def top(self, k: int) -> list[str]:
        return heapq.nsmallest(k, self.scores, key=lambda p: (-self.scores[p], p))

    def reset(self, player: str) -> None:
        self.scores.pop(player, None)
""",
        "tests": [
            {"args": [["Leaderboard", "add_score", "add_score", "add_score", "add_score", "top", "reset", "top",
                       "add_score", "top"],
                      [[], ["ann", 50], ["bob", 80], ["cat", 50], ["ann", 40], [2], ["bob"], [2], ["dan", 90], [3]]],
             "expected": [None, None, None, None, None, ["ann", "bob"], None, ["ann", "cat"], None,
                          ["ann", "dan", "cat"]]},
            {"args": [["Leaderboard", "top", "add_score", "reset", "reset", "top"],
                      [[], [3], ["zed", 1], ["zed"], ["ghost"], [1]]],
             "expected": [None, [], None, None, None, []]},
        ],
    },
]
