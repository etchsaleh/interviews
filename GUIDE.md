# Java → Python: the interview survival guide

This guide is for Java engineers who need to answer coding interviews in Python. It skips
what you already know (algorithms, OOP, HTTP) and focuses on **how to say it in Python**,
plus the traps that catch Java developers.

[TOC]

---

## 1. The 60-second mental model

| Java | Python |
|---|---|
| Compiled, statically typed | Interpreted, dynamically typed (type hints are optional and **not enforced**) |
| `{ }` blocks, `;` line endings | **Indentation** is the block (use 4 spaces), no semicolons |
| `public static void main(...)` | Code runs top to bottom. Use `if __name__ == "__main__":` for a script's entry point |
| Everything lives in a class | Free functions are normal. Use classes only when you need state |
| `null` | `None` |
| `true` / `false` | `True` / `False` |
| `&&`, `||`, `!` | `and`, `or`, `not` |
| `// comment`, `/* */` | `# comment`, `"""docstring"""` |
| `x++` | `x += 1` (there is no `++`) |
| `cond ? a : b` | `a if cond else b` |
| `this` | `self` (and you write it as the first parameter of every method) |

```python
def greet(name: str, excited: bool = False) -> str:
    message = f"Hello, {name}"          # f-string = String.format / concatenation
    if excited:
        message += "!"
    return message


if __name__ == "__main__":
    print(greet("Ada", excited=True))   # keyword arguments!
```

---

## 2. Numbers

```python
7 / 2      # 3.5   ← always float division!
7 // 2     # 3     ← integer (floor) division, what Java's / does for ints
-7 // 2    # -4    ← floors toward -infinity (Java gives -3)
-7 % 3     # 2     ← result has the sign of the divisor (Java gives -1)
2 ** 10    # 1024  ← power operator
abs(-3), min(1, 2, 3), max([4, 5]), sum([1, 2, 3])
divmod(17, 5)       # (3, 2)
int("42"), str(42), float("1.5")
float("inf"), float("-inf")   # or math.inf - replaces Integer.MAX_VALUE / MIN_VALUE
```

- **Ints never overflow.** `2 ** 100` just works. No `long`, no `BigInteger`, no `(lo + hi) >>> 1` tricks.
- If you need truncation toward zero like Java: `int(a / b)` (careful with huge numbers) or `math.trunc`.

---

## 3. Strings

Strings are immutable like Java's, but much more convenient.

```python
s = "hello world"
len(s)                 # 11          (not s.length())
s[0], s[-1]            # 'h', 'd'    (negative index = from the end)
s[0:5], s[:5], s[6:]   # 'hello', 'hello', 'world'   (slicing: [start:stop:step])
s[::-1]                # 'dlrow olleh'  reverse
s.upper(), s.lower(), s.strip(), s.split(), s.split(",")
s.startswith("he"), "wor" in s, s.find("o"), s.replace("l", "L")
s.isdigit(), s.isalpha(), s.isalnum()
"-".join(["a", "b", "c"])   # 'a-b-c'  ← StringBuilder replacement
ord("a"), chr(97)           # 97, 'a'
f"{name} is {age} years old, pi={3.14159:.2f}"
```

- There is **no `char` type** — a character is a string of length 1.
- Compare strings with `==` (it compares content — see §9).
- Building in a loop: append pieces to a list and `"".join(parts)` at the end.
- Count letters: `ord(ch) - ord("a")` gives 0–25, just like `ch - 'a'` in Java.

---

## 4. Collections cheat sheet

| Java | Python | Notes |
|---|---|---|
| `int[]`, `ArrayList<T>` | `list` → `[1, 2, 3]` | `append`, `pop()`, `pop(i)`, `insert(i, x)`, `len(a)` |
| `new int[n]` | `[0] * n` | 2D: `[[0] * cols for _ in range(rows)]` (**not** `[[0]*cols]*rows`) |
| `HashMap<K,V>` | `dict` → `{"a": 1}` | `d[k]`, `d.get(k, default)`, `k in d`, `del d[k]` |
| `map.getOrDefault(k, 0) + 1` | `d[k] = d.get(k, 0) + 1` | or `Counter` / `defaultdict(int)` |
| `computeIfAbsent(k, ArrayList::new)` | `defaultdict(list)` | `from collections import defaultdict` |
| `HashSet<T>` | `set` → `{1, 2}` / `set()` | `add`, `remove`, `discard`, `in`, `|` union, `&` intersection, `-` difference |
| `LinkedHashMap` | `dict` | dicts keep insertion order. For LRU use `OrderedDict` |
| `Stack<T>` / `Deque` as stack | `list` | `append` = push, `pop()` = pop, `a[-1]` = peek |
| `Queue` / `ArrayDeque` | `collections.deque` | `append`, `popleft()`, `appendleft`, `pop` — all O(1) |
| `PriorityQueue<T>` | `heapq` on a `list` | **min-heap**; for max-heap push negated values |
| `TreeMap` / `TreeSet` | no built-in | sorted list + `bisect`, or `sortedcontainers` (3rd party, usually not allowed) |
| `Arrays.asList(...)` / `List.of` | `[...]` literal | `tuple` `(1, 2)` is the immutable version |
| `Pair<A,B>` / `int[]{r, c}` | tuple `(r, c)` | tuples are hashable → usable as dict keys and set members |

### Lists

```python
nums = [3, 1, 2]
nums.append(4)            # add
nums.pop()                # remove & return last  → 4
nums.pop(0)               # remove first — O(n)! use deque for queues
nums[1:3]                 # slice (copy)
nums.copy() or nums[:]    # shallow copy
nums.sort()               # in place, returns None (!)
sorted(nums)              # new sorted list
nums.reverse() / nums[::-1]
nums.index(2), nums.count(2), 2 in nums   # in = linear search
a + b                     # concatenation
for i, x in enumerate(nums): ...
for a, b in zip(list1, list2): ...
```

### Dicts

```python
ages = {"ada": 36, "linus": 54}
ages["grace"] = 85
ages.get("bob")           # None (no exception)
ages["bob"]               # KeyError!
for name, age in ages.items(): ...
for name in ages: ...     # iterates keys
list(ages.keys()), list(ages.values())
ages.pop("ada")           # remove & return
```

### The `collections` power tools

```python
from collections import Counter, defaultdict, deque

Counter("banana")                    # Counter({'a': 3, 'n': 2, 'b': 1})
Counter(nums).most_common(2)         # [(value, count), (value, count)]

graph = defaultdict(list)
graph["a"].append("b")               # no "if key not in map" dance

q = deque([start])
while q:
    node = q.popleft()
```

### Heaps (`PriorityQueue`)

```python
import heapq

heap = []
heapq.heappush(heap, (priority, item))   # tuples compare element by element
priority, item = heapq.heappop(heap)     # smallest first
heap[0]                                  # peek
heapq.heapify(lst)                       # O(n) build in place
heapq.nlargest(3, nums), heapq.nsmallest(3, nums, key=len)
heapq.heappush(heap, -x)                 # max-heap trick: negate on the way in and out
```

If two tuples tie on priority, Python compares the *next* element — if that is an object
without `<`, you get a `TypeError`. Add a tie-breaker: `(priority, counter, item)`.

---

## 5. Control flow

```python
for i in range(5):            # 0..4         for (int i = 0; i < 5; i++)
for i in range(2, 10, 2):     # 2,4,6,8
for i in range(n - 1, -1, -1):  # n-1 down to 0   (or: for i in reversed(range(n)))

while lo <= hi:
    ...

if x > 0:
    ...
elif x < 0:                   # "elif", not "else if"
    ...
else:
    ...

if 0 <= r < rows:             # chained comparisons!
    ...

for item in items:
    if matches(item):
        break
else:                          # runs only if the loop did NOT break
    print("not found")

match command:                 # Python 3.10+ "switch"
    case "start":
        ...
    case "stop" | "halt":
        ...
    case _:
        ...
```

### Truthiness

Empty containers, `0`, `""` and `None` are *falsy*. Idiomatic Python leans on this:

```python
if not stack:        # stack.isEmpty()
if nums:             # !nums.isEmpty()
if node is None:     # node == null   (use "is" for None)
```

---

## 6. Comprehensions & generators

The single biggest readability win over Java. Replaces most `stream()` pipelines.

```python
squares = [x * x for x in nums]                      # map
evens = [x for x in nums if x % 2 == 0]              # filter
pairs = [(i, j) for i in range(3) for j in range(3)] # nested loops
index = {name: i for i, name in enumerate(names)}    # dict comprehension
unique = {word.lower() for word in words}            # set comprehension
total = sum(x * x for x in nums)                     # generator: no list built
any(x < 0 for x in nums), all(x > 0 for x in nums)
```

| Java stream | Python |
|---|---|
| `list.stream().map(f).collect(toList())` | `[f(x) for x in lst]` |
| `.filter(p)` | `[x for x in lst if p(x)]` |
| `.mapToInt(f).sum()` | `sum(f(x) for x in lst)` |
| `.anyMatch(p)` / `.allMatch(p)` | `any(...)` / `all(...)` |
| `Collectors.groupingBy(f)` | `defaultdict(list)` loop, or `itertools.groupby` on sorted data |
| `Collectors.joining(",")` | `",".join(strs)` |
| `.max(Comparator.comparing(f))` | `max(lst, key=f)` |

---

## 7. Functions

```python
def area(width, height=1):          # default argument
    return width * height

area(3), area(3, 4), area(height=4, width=3)

def total(*nums):                   # varargs → tuple
    return sum(nums)

def configure(**options):           # keyword varargs → dict
    print(options)

square = lambda x: x * x            # one-expression anonymous function

def outer():
    count = 0
    def inc():                      # nested function (closure)
        nonlocal count              # needed to *rebind* an outer variable
        count += 1
    inc()
    return count
```

- **No overloading.** Use default arguments instead.
- **Functions return `None`** if they don't `return` anything.
- Return several values as a tuple and unpack: `def min_max(a): return min(a), max(a)` → `lo, hi = min_max(a)`.
- ⚠️ **Mutable default trap:** `def f(acc=[])` shares *one* list across all calls. Use `acc=None` then `if acc is None: acc = []`.
- Memoize recursion with `@functools.cache`.

---

## 8. Classes

```python
from dataclasses import dataclass


class BankAccount:
    interest_rate = 0.02                  # class attribute (like static)

    def __init__(self, owner: str, balance: float = 0):   # constructor
        self.owner = owner                # fields are created by assignment
        self._balance = balance           # _ prefix = "private" by convention

    def deposit(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("amount must be positive")
        self._balance += amount

    @property
    def balance(self) -> float:           # getter, accessed as acct.balance
        return self._balance

    @staticmethod
    def validate(owner: str) -> bool:
        return bool(owner)

    def __repr__(self) -> str:            # toString()
        return f"BankAccount({self.owner!r}, {self._balance})"


class SavingsAccount(BankAccount):        # extends
    def __init__(self, owner: str):
        super().__init__(owner)


@dataclass                                # record-like: generates __init__, __repr__, __eq__
class Point:
    x: int
    y: int
```

| Java | Python dunder method |
|---|---|
| `toString()` | `__repr__` / `__str__` |
| `equals()` / `hashCode()` | `__eq__` / `__hash__` (or `@dataclass(frozen=True)`) |
| `compareTo()` | `__lt__` (enough for `sorted` and `heapq`) |
| `size()` | `__len__` → `len(obj)` |
| `Iterable` | `__iter__` (or write a generator with `yield`) |

Interview data structures (LeetCode style):

```python
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val, self.left, self.right = val, left, right
```

---

## 9. Equality, identity and `None` — opposite of Java!

| Meaning | Java | Python |
|---|---|---|
| Same contents | `a.equals(b)` | `a == b` |
| Same object | `a == b` | `a is b` |

- `"abc" == "abc"` is `True` in Python. `[1, 2] == [1, 2]` is `True`. `==` on lists/dicts compares deeply.
- Use `is` **only** for `None` (and `True`/`False` singletons): `if x is None`.

---

## 10. Sorting

Python sorts with a **key function** rather than a comparator, and sorting is stable.

```python
words.sort()                                     # natural order, in place
sorted(words, key=len)                           # by length
sorted(words, key=str.lower)                     # case-insensitive
sorted(people, key=lambda p: p.age, reverse=True)
sorted(people, key=lambda p: (p.age, p.name))    # multi-key: compare tuples
sorted(nums, key=lambda x: (-freq[x], x))        # desc by freq, then asc by value

# Need a real comparator (rare)? Wrap it:
from functools import cmp_to_key
sorted(nums, key=cmp_to_key(lambda a, b: a - b))
```

---

## 11. Exceptions

```python
try:
    value = int(text)
except ValueError as e:              # catch
    print(f"bad input: {e}")
except (KeyError, IndexError):       # multi-catch
    ...
else:                                # runs if no exception
    ...
finally:
    ...

raise ValueError("negative amount")  # throw new IllegalArgumentException(...)

class InsufficientFunds(Exception):  # custom exception
    pass

with open("data.txt") as f:          # try-with-resources
    text = f.read()
```

- No checked exceptions and no `throws` clause.
- Common mapping: `IllegalArgumentException` → `ValueError`, `NullPointerException` → `AttributeError`/`TypeError` on `None`, `IndexOutOfBoundsException` → `IndexError`, missing map key → `KeyError`, `UnsupportedOperationException` → `NotImplementedError`.

---

## 12. HTTP: GET and POST with `requests`

`requests` is the de-facto HTTP library (`pip install requests`). Compare with Java 11's `HttpClient`:

```java
// Java
HttpClient client = HttpClient.newHttpClient();
HttpRequest req = HttpRequest.newBuilder(URI.create(base + "/users?team=platform"))
        .header("Accept", "application/json").GET().build();
HttpResponse<String> resp = client.send(req, HttpResponse.BodyHandlers.ofString());
List<User> users = mapper.readValue(resp.body(), new TypeReference<>() {});
```

```python
# Python
import requests

resp = requests.get(f"{base}/users", params={"team": "platform"}, timeout=5)
resp.raise_for_status()          # throw on 4xx / 5xx
users = resp.json()              # list[dict] — no POJOs needed
```

### Cheat sheet

```python
# GET with query params and headers
resp = requests.get(url, params={"page": 2}, headers={"Authorization": f"Bearer {token}"}, timeout=5)

# POST JSON (sets Content-Type: application/json for you)
resp = requests.post(url, json={"title": "Buy milk"}, timeout=5)

# POST a form instead
resp = requests.post(url, data={"username": "ada"}, timeout=5)

# PUT / PATCH / DELETE
requests.put(url, json=body); requests.patch(url, json=body); requests.delete(url)

resp.status_code      # 200, 201, 404 ...
resp.ok               # True if status < 400
resp.json()           # parsed body
resp.text             # raw body as str
resp.headers["Content-Type"]
resp.raise_for_status()   # raises requests.HTTPError for 4xx/5xx

# Reuse connection + default headers (like a configured HttpClient)
with requests.Session() as s:
    s.headers.update({"Authorization": f"Bearer {token}"})
    s.get(f"{base}/profile", timeout=5)

# Errors
try:
    resp = requests.get(url, timeout=2)
    resp.raise_for_status()
except requests.Timeout:
    ...
except requests.HTTPError as e:
    print(e.response.status_code)
except requests.RequestException:     # base class of everything above
    ...
```

### Common API interview tasks — patterns

```python
# Pagination
items, page = [], 1
while page is not None:
    body = requests.get(f"{base}/orders", params={"page": page}, timeout=5).json()
    items.extend(body["data"])
    page = body["next_page"]

# Retry with backoff
import time
for attempt in range(5):
    resp = requests.get(url, timeout=5)
    if resp.status_code not in (429, 500, 502, 503, 504):
        break
    time.sleep(0.1 * 2 ** attempt)
resp.raise_for_status()

# Join data from two endpoints
users = {u["id"]: u for u in requests.get(f"{base}/users", timeout=5).json()}
for order in orders:
    print(users[order["user_id"]]["name"], order["total"])
```

Using only the standard library (if `requests` isn't allowed):

```python
import json
import urllib.request

with urllib.request.urlopen(f"{base}/users", timeout=5) as resp:
    users = json.loads(resp.read())

req = urllib.request.Request(f"{base}/todos", data=json.dumps({"title": "x"}).encode(),
                             headers={"Content-Type": "application/json"}, method="POST")
with urllib.request.urlopen(req, timeout=5) as resp:
    created = json.loads(resp.read())
```

---

## 13. Interview pattern snippets

```python
# Two pointers
lo, hi = 0, len(a) - 1
while lo < hi:
    ...

# Sliding window
counts, left = {}, 0
for right, ch in enumerate(s):
    counts[ch] = counts.get(ch, 0) + 1
    while counts[ch] > 1:
        counts[s[left]] -= 1
        left += 1

# Binary search with the stdlib
import bisect
i = bisect.bisect_left(sorted_nums, target)   # first index >= target
found = i < len(sorted_nums) and sorted_nums[i] == target

# BFS on a graph
from collections import deque
seen, q = {start}, deque([start])
while q:
    node = q.popleft()
    for nxt in graph[node]:
        if nxt not in seen:
            seen.add(nxt)
            q.append(nxt)

# DFS (recursive) on a grid
def dfs(r, c):
    if not (0 <= r < rows and 0 <= c < cols) or grid[r][c] != "1":
        return
    grid[r][c] = "#"
    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        dfs(r + dr, c + dc)

# Top-down DP
from functools import cache
@cache
def dp(i, j):
    ...

# Bottom-up DP table
dp = [[0] * (m + 1) for _ in range(n + 1)]

# Trie with nested dicts
trie = {}
for word in words:
    node = trie
    for ch in word:
        node = node.setdefault(ch, {})
    node["$"] = True

# Union-Find
parent = list(range(n))
def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x
```

### Graphs, queues and caching: the focus areas

```python
# Build an adjacency list from an edge list
from collections import defaultdict
graph = defaultdict(list)
for a, b in edges:
    graph[a].append(b)
    graph[b].append(a)          # omit for directed graphs

# Topological sort (Kahn) + cycle detection
from collections import deque
indegree = {node: 0 for node in nodes}
for a, b in edges:              # a before b
    indegree[b] += 1
q = deque(n for n, d in indegree.items() if d == 0)
order = []
while q:
    node = q.popleft()
    order.append(node)
    for nxt in graph[node]:
        indegree[nxt] -= 1
        if indegree[nxt] == 0:
            q.append(nxt)
has_cycle = len(order) < len(nodes)

# Dijkstra (weighted shortest path)
import heapq
dist, heap = {}, [(0, source)]
while heap:
    d, node = heapq.heappop(heap)
    if node in dist:
        continue
    dist[node] = d
    for nxt, w in graph[node]:          # graph[node] = [(neighbour, weight), ...]
        if nxt not in dist:
            heapq.heappush(heap, (d + w, nxt))

# Sliding window over a time-ordered stream
window = deque()
def record(t):
    window.append(t)
    while window[0] <= t - WINDOW:
        window.popleft()

# Max-priority queue with FIFO tie-breaking
import itertools
counter = itertools.count()
heapq.heappush(heap, (-priority, next(counter), item))

# LRU cache in ~10 lines
from collections import OrderedDict
class LRU:
    def __init__(self, capacity):
        self.capacity, self.data = capacity, OrderedDict()
    def get(self, key):
        if key not in self.data:
            return -1
        self.data.move_to_end(key)
        return self.data[key]
    def put(self, key, value):
        self.data[key] = value
        self.data.move_to_end(key)
        if len(self.data) > self.capacity:
            self.data.popitem(last=False)      # evict least recently used

# Memoize any pure function
from functools import lru_cache
@lru_cache(maxsize=1024)
def expensive(x): ...
expensive.cache_info()                     # hits, misses, size

# TTL: store the expiry next to the value
cache[key] = (value, now + ttl)
value, expires_at = cache[key]
if now >= expires_at: ...                  # expired
```

Other stdlib helpers worth knowing: `itertools.permutations`, `combinations`, `product`,
`accumulate` (prefix sums), `math.gcd`, `math.isqrt`, `zip(*matrix)` (transpose),
`str.maketrans`.

---

## 14. Gotchas that bite Java developers

1. `/` is float division. Use `//` for integers.
2. `list.sort()` returns `None`. `nums = nums.sort()` wipes your list.
3. `[[0] * n] * m` makes *m references to the same row*. Use a comprehension.
4. `{}` is an empty **dict**, not a set. Use `set()`.
5. Mutable default arguments (`def f(x=[])`) are shared between calls.
6. Variables in loops/ifs are visible after the block (function scope, not block scope).
7. To assign to a variable from an enclosing function use `nonlocal`; for a module global use `global`.
8. Modifying a dict/set while iterating it raises `RuntimeError`. Iterate over `list(d)` instead.
9. `is` vs `==` — see §9. `x == None` works but `x is None` is the idiom.
10. Recursion limit is ~1000 frames. Deep DFS on big inputs → iterative with an explicit stack, or `sys.setrecursionlimit`.
11. Strings are immutable: `s[0] = "x"` fails. Convert to `list(s)`, edit, then `"".join(...)`.
12. Integer caching makes `a is b` work for small ints and then mysteriously fail for big ones. Never use `is` for numbers.
13. Indentation errors: don't mix tabs and spaces. (The editor here inserts 4 spaces for Tab.)

---

## 15. Writing Python fast under time pressure

Candidates who don't use Python tend not to finish on time, so speed is the point of the switch.
These save the most minutes:

- **Reach for the stdlib first:** `Counter`, `defaultdict`, `deque`, `heapq`, `OrderedDict`,
  `bisect`, `itertools`, `functools.cache`. Memorise the imports:

  ```python
  from collections import Counter, defaultdict, deque, OrderedDict
  import heapq, bisect, itertools, math
  from functools import cache
  ```

- **No boilerplate:** no classes unless the problem is about state, no type declarations,
  no getters. A function and a couple of local variables is the norm.
- **Unpack everything:** `for i, (a, b) in enumerate(pairs):`, `lo, hi = 0, len(a) - 1`, `x, y = y, x`.
- **Comprehensions** for building lists, sets and dicts in one line.
- **Tuples as composite keys:** `seen.add((r, c))`, `memo[(i, j)]`, sorting by `(-score, name)`.
- **`float("inf")`** for min/max sentinels; `max(..., default=0)` for possibly-empty input.
- **Debug with `print()`.** It's fast and it shows up per test in this app.
- **Write, run, fix.** Python has no compile step; run the tests early and often.
- **Know the edge cases Python handles for you:** big ints, negative indexes, slicing past
  the end (`a[5:100]` is fine), and `==` on lists and dicts.

---

## 16. How to use this app

1. Follow the **Study Plan**. Start each problem and the timer starts on your first keystroke. Targets: Easy 10 min, Medium 20 min.
2. Read the problem, then the **Coming from Java** tab for the Python idioms that problem exercises.
3. Write your solution and press **Run tests** (or `Ctrl/⌘ + Enter`). `print()` output is shown per test.
4. Once it passes, try one of the **Twists to try**. The real questions are familiar problems with a twist.
5. Stuck? **Show solution** loads the reference answer (and your time isn't recorded). Read it, reset, and solve again from a blank editor later.
6. Use the **Playground** for quick experiments ("what does `-7 // 2` return?").
7. API problems hit a mock server bundled with the app; open its URLs in your browser to see the JSON.
