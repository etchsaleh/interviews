"""Short editorials for the LeetCode-style problems, keyed by problem id.

Shown in the problem page's Editorial tab behind a reveal button. Each one is the idea,
the steps, complexity, and the mistakes people make, in that order.
"""

EDITORIALS = {
    # ------------------------------------------------------------ fundamentals
    "two-sum": """
**Idea:** for each number you need `target - num`. Remember every number you've seen and its
index in a dict, so "have I seen the complement?" is an O(1) lookup.

**Steps:** loop with `enumerate`; if `target - num` is in `seen`, return `[seen[target - num], i]`;
otherwise store `seen[num] = i`.

**Complexity:** O(n) time, O(n) space.

**Pitfalls:** storing before checking lets an element pair with itself (`[3]`, target 6). The
brute-force double loop is O(n²); say it, then improve it.
""",
    "valid-anagram": """
**Idea:** two strings are anagrams exactly when every character appears the same number of times.

**Steps:** `return Counter(s) == Counter(t)`. (Or `sorted(s) == sorted(t)` in O(n log n).)

**Complexity:** O(n) time, O(k) space for k distinct characters.

**Pitfalls:** checking only the set of letters (`"aacc"` vs `"ccac"`). A quick
`len(s) != len(t)` early exit is a nice touch.
""",
    "valid-palindrome": """
**Idea:** normalise first (keep only alphanumerics, lower-case), then compare with the reverse.

**Steps:** `cleaned = "".join(c.lower() for c in s if c.isalnum())`; `return cleaned == cleaned[::-1]`.

**Complexity:** O(n) time, O(n) space. The two-pointer version (skip non-alphanumerics from
both ends) is O(1) space: mention it as the follow-up.

**Pitfalls:** forgetting digits count (`"0P"` is not a palindrome); comparing before lower-casing.
""",
    "valid-parentheses": """
**Idea:** the most recently opened bracket must be the first one closed: that's a stack.

**Steps:** map each closer to its opener. Push openers. On a closer, the stack must be non-empty
and its top must be the matching opener (pop it). At the end, the stack must be empty.

**Complexity:** O(n) time, O(n) space.

**Pitfalls:** popping from an empty stack (`")"`), and forgetting the final emptiness check (`"("`).
""",
    "binary-search": """
**Idea:** keep an inclusive window `[lo, hi]` that must contain the target if it exists; halve it
each step.

**Steps:** `while lo <= hi`: `mid = (lo + hi) // 2`; return `mid` on a hit, else move `lo = mid + 1`
or `hi = mid - 1`. Return `-1` when the window is empty.

**Complexity:** O(log n) time, O(1) space.

**Pitfalls:** `/` instead of `//` (float index); `lo < hi` with an inclusive `hi` (misses the last
element); `lo = mid` (infinite loop).
""",
    "max-subarray": """
**Idea (Kadane):** the best subarray ending at `i` either extends the best one ending at `i-1`, or
starts fresh at `i`, whichever is larger.

**Steps:** `current = best = nums[0]`; for each next `num`: `current = max(num, current + num)`;
`best = max(best, current)`.

**Complexity:** O(n) time, O(1) space.

**Pitfalls:** starting `best` at 0 breaks all-negative input (answer is the largest single number).
""",
    "group-anagrams": """
**Idea:** anagrams share a canonical key, e.g. their sorted letters. Group words by that key.

**Steps:** `groups = defaultdict(list)`; `groups["".join(sorted(w))].append(w)`;
`return list(groups.values())`.

**Complexity:** O(n · k log k) for n words of length k. A 26-letter count tuple as the key makes it
O(n · k).

**Pitfalls:** using a list as a dict key (unhashable); use a string or tuple.
""",
    "top-k-frequent": """
**Idea:** count, then take the k largest counts.

**Steps:** `[v for v, _ in Counter(nums).most_common(k)]`. Without `Counter`: count in a dict,
then `heapq.nlargest(k, counts, key=counts.get)`.

**Complexity:** O(n log k) with a heap (`most_common(k)` uses one). Bucket sort by frequency gives
O(n): mention it if asked to beat n log n.

**Pitfalls:** sorting the input instead of the counts; returning `(value, count)` pairs instead of
values.
""",
    "product-except-self": """
**Idea:** `answer[i]` = (product of everything left of `i`) × (product of everything right of `i`).

**Steps:** first pass left→right writes the running prefix product into `answer[i]` *before*
multiplying `nums[i]` in. Second pass right→left multiplies in the running suffix product the same way.

**Complexity:** O(n) time, O(1) extra space (the output doesn't count).

**Pitfalls:** dividing the total product (forbidden, and breaks on zeros); including `nums[i]` in its
own prefix.
""",
    "longest-substring": """
**Idea:** sliding window. The window `[start, i]` never contains a repeat; when `s[i]` repeats inside
it, jump `start` past the previous occurrence.

**Steps:** keep `last_seen[ch] = index`. If `last_seen.get(ch, -1) >= start`, set
`start = last_seen[ch] + 1`. Update `last_seen`, track `best = max(best, i - start + 1)`.

**Complexity:** O(n) time, O(k) space.

**Pitfalls:** moving `start` backwards when the previous occurrence is *before* the window
(`"abba"`); that's why the check is `>= start`.
""",
    "merge-intervals": """
**Idea:** after sorting by start, overlapping intervals are adjacent, so one sweep merges them.

**Steps:** sort by start; for each `[s, e]`: if it overlaps the last merged one (`s <= last_end`),
extend `last_end = max(last_end, e)`; otherwise append a new interval.

**Complexity:** O(n log n) time for the sort, O(n) output.

**Pitfalls:** `last_end = e` instead of `max(...)` (breaks `[[1,4],[2,3]]`); treating touching
intervals (`[1,4],[4,5]`) as separate; mutating the input lists you return.
""",
    "climbing-stairs": """
**Idea:** to reach step `n` your last move was 1 or 2 steps, so `ways(n) = ways(n-1) + ways(n-2)`:
Fibonacci.

**Steps:** memoised recursion with `@cache`, or iteratively: `a, b = 1, 2`, then `a, b = b, a + b`.

**Complexity:** O(n) time; O(1) space iteratively.

**Pitfalls:** plain recursion without memoisation is exponential (n = 45 times out); deep recursion
can hit Python's ~1000 frame limit, so prefer the loop for big n.
""",
    # ----------------------------------------------------------------- graphs
    "number-of-islands": """
**Idea:** each unvisited land cell starts a new island; flood-fill (BFS/DFS) marks the whole island
so it isn't counted again.

**Steps:** scan the grid; on an unvisited `"1"`: `islands += 1`, BFS with a `deque`, visiting the 4
neighbours that are in bounds, land, and unseen.

**Complexity:** O(rows × cols) time and space.

**Pitfalls:** marking cells as seen when *popped* instead of when *pushed* (duplicates in the queue);
diagonal neighbours; `list.pop(0)` (O(n)) instead of `deque.popleft()`.
""",
    "build-order": """
**Idea:** topological sort (Kahn's algorithm). A task is ready when all its dependencies are done
(in-degree 0). The twist "smallest ready task first" means a **min-heap** instead of a FIFO queue.

**Steps:** build `graph[before] -> [after]` and `indegree`. Heapify all in-degree-0 tasks. Pop the
smallest, append it, decrement its neighbours, and push any that reach 0. If you output fewer than
`len(tasks)` names, there's a cycle: return `[]`.

**Complexity:** O((V + E) log V).

**Pitfalls:** a plain queue gives *a* valid order but not the alphabetical one; forgetting tasks
with no edges at all; detecting cycles with a separate DFS when the count check is enough.
""",
    "fewest-hops": """
**Idea:** unweighted shortest path = BFS. Down services are simply removed from the graph.

**Steps:** if start or target is down, return -1. Build an undirected adjacency list. BFS from
`start` with `(node, hops)` pairs, skipping down and seen nodes; return `hops` when you pop the target.

**Complexity:** O(V + E).

**Pitfalls:** adding edges in one direction only; DFS (finds *a* path, not the shortest); forgetting
`start == target` is 0.
""",
    "broadcast-time": """
**Idea:** single-source shortest paths with positive weights = **Dijkstra**. The answer is the
largest shortest-path distance, or -1 if some server is unreachable.

**Steps:** heap of `(time, node)` starting at `(0, source)`. Pop the smallest; if already finalised,
skip; otherwise record `dist[node]` and push neighbours with `time + ms`. At the end: `max(dist.values())`
if `len(dist) == n`.

**Complexity:** O(E log E).

**Pitfalls:** BFS (ignores weights); not skipping stale heap entries; forgetting unreachable nodes.
""",
    "team-groups": """
**Idea:** connected components. Union-Find merges people who worked together; then count roots and
the size of the biggest group.

**Steps:** `parent = list(range(n))`; `find` with path halving; `union` each pair. Then
`sizes = Counter(find(i) for i in range(n))` → `[len(sizes), max(sizes.values())]`.

**Complexity:** ~O((n + pairs) · α(n)), effectively linear.

**Pitfalls:** counting `parent[i] == i` *before* the final finds (fine) but reading `parent[i]` as
the group (it may not be the root); isolated people are groups of size 1.
""",
    # ----------------------------------------------------------------- queues
    "moving-average": """
**Idea:** keep only the last `size` values in a deque plus a running total, so each update is O(1).

**Steps:** if the deque is full, `popleft()` and subtract it from the total; append the new value,
add it to the total; return `total / len(window)`.

**Complexity:** O(1) per call, O(size) space.

**Pitfalls:** `sum(window)` every call (O(size)); dividing by `size` before the window is full.
""",
    "rate-limiter": """
**Idea:** sliding window log. Keep the timestamps of *accepted* requests; anything at or before
`t - window` has left the window.

**Steps:** pop from the left while `accepted[0] <= t - window`; if `len(accepted) < max_requests`,
append `t` and return `True`, else `False`.

**Complexity:** amortised O(1) per call; O(max_requests) space.

**Pitfalls:** storing rejected requests too; an off-by-one on the boundary (`<` vs `<=`): the window
is `(t - window, t]`.
""",
    "round-robin": """
**Idea:** simulate it directly with a deque of `[name, remaining]`.

**Steps:** pop left, run `min(quantum, remaining)`, advance the clock. If work remains, append it to
the back; otherwise record `[name, time]`.

**Complexity:** O(total_duration / quantum) iterations.

**Pitfalls:** advancing the clock by `quantum` when the job needed less; requeueing finished jobs.
""",
    "ticket-queue": """
**Idea:** a priority queue where ties break by arrival order. `heapq` is a min-heap, so push
`(-priority, counter, ticket_id)`.

**Steps:** `add` pushes with `next(itertools.count())` as the tie-breaker; `next` pops and returns the
id, or `None` when empty.

**Complexity:** O(log n) per operation.

**Pitfalls:** pushing `(-priority, ticket_id)` breaks ties alphabetically, not first-come; forgetting
to negate (lowest priority first).
""",
    # ---------------------------------------------------------------- caching
    "lru-cache": """
**Idea:** an `OrderedDict` keeps keys in recency order: move a key to the end on every use, evict
from the front.

**Steps:** `get`: if present, `move_to_end(key)` and return the value, else -1. `put`: set the value,
`move_to_end(key)`, and if over capacity `popitem(last=False)`.

**Complexity:** O(1) per operation.

**Pitfalls:** `put` on an existing key must also refresh its recency; evicting before inserting
when updating an existing key. Follow-up: implement with a dict + doubly linked list.
""",
    "cache-hit-rate": """
**Idea:** simulate the LRU cache and count.

**Steps:** for each key: if in the `OrderedDict`, it's a hit (`move_to_end`); else a miss, and
insert it, evicting `popitem(last=False)` when full. Handle `capacity == 0` (never store anything).

**Complexity:** O(n) for n requests.

**Pitfalls:** counting the inserted key as a hit; forgetting to refresh recency on hits (that's FIFO).
""",
    "ttl-cache": """
**Idea:** LRU (`OrderedDict`) where each value carries its expiry time. The twist: when over
capacity, drop **expired** entries first, and only then evict the least recently used.

**Steps:** store `key -> (value, now + ttl)`. `get`: missing or `now >= expires_at` → -1 (and
delete); else `move_to_end`. `put`: insert and `move_to_end`; if over capacity, delete every expired
entry (collect keys first, then delete), then evict LRU while still over.

**Complexity:** O(1) amortised for `get`; `put` is O(n) when it has to scan for expired entries
(follow-up: a heap of expiry times).

**Pitfalls:** `now > expires_at` instead of `>=`; deleting from the dict while iterating it; evicting
an LRU entry that's still valid while an expired one remains.
""",
    "cached-prices": """
**Idea:** memoise the slow lookup within the call: fetch each *distinct* SKU once, then rebuild the
answer in input order.

**Steps:** `cache = {}`; for each sku not in `cache`, GET `/price/{sku}` with
`params={"client": client_id}` and store `price`. Return `[cache[s] for s in skus]`.

**Complexity:** one HTTP call per distinct SKU.

**Pitfalls:** returning prices in a different order (e.g. iterating a set); forgetting the `client`
query parameter.
""",
    # -------------------------------------------------------------------- OOP
    "bank-accounts": """
**Idea:** one dict `account_id -> balance` is all the state; every method validates first, then mutates.

**Steps:** `open` rejects existing ids and negative balances. `deposit` / `withdraw` return -1 on
unknown accounts, non-positive amounts, or insufficient funds. `transfer` checks the destination
exists, then reuses `withdraw` and `deposit`.

**Complexity:** O(1) per operation.

**Pitfalls:** `transfer` that withdraws before checking the destination exists (money disappears);
allowing zero or negative amounts.
""",
    "leaderboard": """
**Idea:** keep totals in a `defaultdict(int)`; rank with a sort key of `(-score, name)` so higher
scores come first and ties go alphabetically.

**Steps:** `add_score` adds; `reset` does `pop(player, None)`; `top(k)` returns
`heapq.nsmallest(k, scores, key=lambda p: (-scores[p], p))` (or a full sort and slice).

**Complexity:** `top` is O(n log k) with `nsmallest`, O(n log n) with a sort.

**Pitfalls:** `sorted(..., reverse=True)` on `(score, name)` reverses the name tie-break too; `reset`
raising `KeyError` for unknown players.
""",
}
