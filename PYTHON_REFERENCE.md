# Python fundamentals: data structures & the standard library

A working reference for writing real-world Python fast: **which tool to reach for, why, and
how to use it**. Every example on this page is executed automatically, so the outputs shown
are real. Lines starting with `>>>` are code; the line after is what Python prints.

Read section 1 first. It's the decision guide for everything else.

[TOC]

---

## 1. Choosing a data structure

Ask what you need to do with the data most often, then pick the structure that makes that
operation cheap.

| You need to… | Use | Why | Java equivalent |
|---|---|---|---|
| Keep items in order, index by position, append | `list` | O(1) append and index | `ArrayList` |
| Look up a value by a key | `dict` | O(1) average lookup, keeps insertion order | `LinkedHashMap` |
| Check "have I seen this?" / remove duplicates | `set` | O(1) average membership | `HashSet` |
| Count things | `collections.Counter` | a dict that defaults to 0 and has `most_common` | `Map<T, Integer>` + merge |
| Group things by a key | `collections.defaultdict(list)` | no "if key not in d" boilerplate | `computeIfAbsent` |
| Add/remove at **both** ends (queue, sliding window, BFS) | `collections.deque` | O(1) at both ends; `list.pop(0)` is O(n) | `ArrayDeque` |
| Always get the smallest (or largest) next | `heapq` on a list | O(log n) push/pop | `PriorityQueue` |
| Keep a sorted list and search it | `list` + `bisect` | O(log n) search | `TreeSet` (sort of) |
| A fixed record of a few fields | `tuple`, `namedtuple`, or `@dataclass` | readable fields, hashable if frozen | a record / POJO |
| A fixed set of named choices | `enum.Enum` | no magic strings | `enum` |
| Money and exact decimals | `decimal.Decimal` | floats can't represent 0.1 exactly | `BigDecimal` |

### Complexity cheat sheet

| Operation | `list` | `dict` / `set` | `deque` | `heapq` |
|---|---|---|---|---|
| Access by index | O(1) | — | O(n) in the middle | — |
| `x in container` | **O(n)** | O(1) avg | O(n) | O(n) |
| Append / add | O(1) amortized | O(1) avg | O(1) both ends | O(log n) push |
| Pop from the end | O(1) | `popitem` O(1) | O(1) both ends | O(log n) pop smallest |
| Insert / delete at the front | **O(n)** | — | O(1) | — |
| Sort | O(n log n) | — | — | — |

The single most common performance bug: `if x in some_list` inside a loop. Turn the list into
a `set` once, then check membership in O(1).

---

## 2. Built-in functions you'll use constantly

No imports needed. These replace a lot of hand-written loops.

```python
>>> nums = [4, 1, 7, 3]
>>> len(nums), sum(nums), min(nums), max(nums)
(4, 15, 1, 7)
>>> sorted(nums)                      # new list; the original is unchanged
[1, 3, 4, 7]
>>> sorted(nums, reverse=True)
[7, 4, 3, 1]
>>> list(reversed(nums))              # reversed() returns an iterator
[3, 7, 1, 4]
>>> any(n > 5 for n in nums), all(n > 0 for n in nums)
(True, True)
```

**`enumerate` and `zip`**: use them instead of index variables.

```python
>>> for i, name in enumerate(["ada", "bob"], start=1):
...     print(i, name)
1 ada
2 bob
>>> list(zip(["a", "b", "c"], [1, 2, 3]))
[('a', 1), ('b', 2), ('c', 3)]
>>> dict(zip(["a", "b"], [1, 2]))       # build a dict from two lists
{'a': 1, 'b': 2}
>>> list(zip([1, 2, 3], ["x", "y"]))    # zip stops at the shortest input
[(1, 'x'), (2, 'y')]
```

Pass `zip(a, b, strict=True)` when the lists *must* be the same length: it raises instead of
silently dropping data.

**`min` / `max` / `sorted` with `key`**: the key function says what to compare.

```python
>>> people = [{"name": "Ada", "age": 36}, {"name": "Bob", "age": 25}]
>>> min(people, key=lambda p: p["age"])["name"]
'Bob'
>>> max([], default=0)                  # without default, max([]) raises ValueError
0
>>> sorted(["banana", "Apple", "cherry"], key=str.lower)
['Apple', 'banana', 'cherry']
```

**Numbers**

```python
>>> divmod(17, 5)                       # quotient and remainder together
(3, 2)
>>> pow(2, 10), pow(2, 10, 1000)        # optional third argument: modulo
(1024, 24)
>>> abs(-3.5), round(3.14159, 2)
(3.5, 3.14)
>>> round(2.5), round(3.5)              # "banker's rounding": halves go to the even number!
(2, 4)
>>> int("42"), float("1.5"), int(3.99), int("ff", 16)
(42, 1.5, 3, 255)
```

**Type checks and conversions**

```python
>>> isinstance(3, int), isinstance(True, int)   # bool is a subclass of int!
(True, True)
>>> isinstance(3.0, (int, float))
True
>>> bool(""), bool([]), bool(0), bool(None), bool("0")
(False, False, False, False, True)
>>> str(42), repr("hi")
('42', "'hi'")
```

**`print`**

```python
>>> print("a", "b", sep=", ", end="!\n")
a, b!
```

**`iter` / `next`**: pull one item at a time; `next(it, default)` avoids `StopIteration`.

```python
>>> it = iter([10, 20])
>>> next(it), next(it), next(it, "done")
(10, 20, 'done')
>>> next((n for n in [3, 8, 11] if n > 5), None)    # first match, or None
8
```

---

## 3. Strings

Strings are **immutable** sequences of characters. There is no `char` type: a character is a
string of length 1. Every method returns a *new* string.

### Indexing and slicing (works on lists and tuples too)

`s[start:stop:step]`: `start` is included, `stop` is not, and negative numbers count from the end.

```python
>>> s = "permit-2026"
>>> s[0], s[-1], s[:6], s[7:], s[-4:]
('p', '6', 'permit', '2026', '2026')
>>> s[::-1]                          # reversed
'6202-timrep'
>>> s[100:]                          # slicing never raises IndexError
''
```

### Splitting and joining: the workhorses of parsing

```python
>>> "a,b,,c".split(",")               # keeps empty fields
['a', 'b', '', 'c']
>>> "  many   spaces here ".split()  # no argument: any whitespace, drops empties
['many', 'spaces', 'here']
>>> "key=value=more".split("=", 1)  # maxsplit
['key', 'value=more']
>>> "2026-03-01T10:00".rsplit(":", 1)
['2026-03-01T10', '00']
>>> "user@example.com".partition("@")   # always 3 parts, never raises
('user', '@', 'example.com')
>>> "line1\nline2\r\nline3".splitlines()
['line1', 'line2', 'line3']
>>> ", ".join(["a", "b", "c"])          # join is a method on the separator
'a, b, c'
>>> "-".join(str(n) for n in [1, 2, 3])  # join needs strings: convert first
'1-2-3'
```

Build strings in a loop by collecting pieces in a list and calling `"".join(parts)` once:
repeated `+=` in a loop can be quadratic.

### Cleaning

```python
>>> "  hello\n".strip(), "xxhixx".strip("x"), "  hi".lstrip()
('hello', 'hi', 'hi')
>>> "INV-1001".removeprefix("INV-"), "report.csv".removesuffix(".csv")
('1001', 'report')
>>> "Hello World".lower(), "hello".upper(), "hello world".title()
('hello world', 'HELLO', 'Hello World')
>>> "Straße".casefold() == "STRASSE".casefold()    # casefold: for case-insensitive comparison
True
>>> "a-b-c".replace("-", "/"), "a-b-c".replace("-", "", 1)
('a/b/c', 'ab-c')
```

### Searching and testing

```python
>>> s = "the permit was approved"
>>> "permit" in s, s.startswith("the"), s.endswith(("ed", "ing"))   # tuple = any of
(True, True, True)
>>> s.find("was"), s.find("nope")      # find returns -1 when missing
(11, -1)
>>> s.count("e")
3
>>> "123".isdigit(), "abc".isalpha(), "a1".isalnum(), "  ".isspace()
(True, True, True, True)
```

`s.index("nope")` is like `find` but raises `ValueError`. Use `find` (or `in`) when missing is normal.

### Formatting with f-strings

```python
>>> name, amount, ratio = "Ada", 1234567.891, 0.4567
>>> f"{name} owes ${amount:,.2f}"            # thousands separator, 2 decimals
'Ada owes $1,234,567.89'
>>> f"{ratio:.1%}", f"{42:05d}", f"{7:>4}|", f"{'x':<3}|"
('45.7%', '00042', '   7|', 'x  |')
>>> f"{name=}"                               # debugging shorthand
"name='Ada'"
>>> "7".zfill(3), "ab".center(6, "*")
('007', '**ab**')
```

### Characters, bytes and encodings

```python
>>> ord("a"), chr(98)
(97, 'b')
>>> "café".encode("utf-8")                   # str -> bytes
b'caf\xc3\xa9'
>>> b"caf\xc3\xa9".decode("utf-8")           # bytes -> str
'café'
```

Text from files and HTTP is bytes underneath. Always say which encoding (`utf-8`) when you
open files.

---

## 4. Lists

An ordered, mutable sequence: Python's `ArrayList`. Use it when order matters and you mostly
append and iterate.

```python
>>> items = [3, 1, 2]
>>> items.append(4)             # add one item at the end: O(1)
>>> items.extend([5, 6])        # add many (any iterable)
>>> items
[3, 1, 2, 4, 5, 6]
>>> items.insert(0, 0)          # O(n): shifts everything
>>> items.pop()                 # remove and return the last: O(1)
6
>>> items.pop(0)                # remove and return the first: O(n)
0
>>> items.remove(2)             # remove the first matching VALUE (ValueError if missing)
>>> items
[3, 1, 4, 5]
>>> items.index(4), items.count(4)
(2, 1)
>>> items.sort()                # in place, returns None
>>> items
[1, 3, 4, 5]
>>> items.reverse(); items
[5, 4, 3, 1]
>>> del items[0]; items
[4, 3, 1]
>>> items[1:3] = [9, 9, 9]; items     # slice assignment can change the length
[4, 9, 9, 9]
```

**`append` vs `extend`**: `append([5, 6])` adds one element (a list); `extend([5, 6])` adds two.

### Copies

```python
>>> a = [[1, 2], [3]]
>>> b = a                 # same list, two names
>>> c = a.copy()          # new outer list, same inner lists (shallow copy); also list(a), a[:]
>>> import copy
>>> d = copy.deepcopy(a)  # fully independent
>>> a[0].append(99)
>>> b[0], c[0], d[0]
([1, 2, 99], [1, 2, 99], [1, 2])
```

### Building lists: comprehensions

```python
>>> [n * n for n in range(5)]
[0, 1, 4, 9, 16]
>>> [n for n in range(10) if n % 3 == 0]
[0, 3, 6, 9]
>>> ["even" if n % 2 == 0 else "odd" for n in range(3)]   # if/else goes BEFORE the for
['even', 'odd', 'even']
>>> [[0] * 3 for _ in range(2)]    # 2D grid: each row is a new list
[[0, 0, 0], [0, 0, 0]]
>>> grid = [[0] * 3] * 2           # WRONG: two references to one row
>>> grid[0][0] = 1; grid
[[1, 0, 0], [1, 0, 0]]
>>> [x for row in [[1, 2], [3]] for x in row]    # flatten: loops in the same order as nested fors
[1, 2, 3]
```

### Sorting real records

```python
>>> rows = [("ada", "ops", 90), ("bob", "eng", 75), ("cy", "eng", 90)]
>>> sorted(rows, key=lambda r: r[2])                     # by score
[('bob', 'eng', 75), ('ada', 'ops', 90), ('cy', 'eng', 90)]
>>> sorted(rows, key=lambda r: (-r[2], r[0]))            # score desc, then name asc
[('ada', 'ops', 90), ('cy', 'eng', 90), ('bob', 'eng', 75)]
>>> from operator import itemgetter
>>> sorted(rows, key=itemgetter(1, 0))                   # team, then name
[('bob', 'eng', 75), ('cy', 'eng', 90), ('ada', 'ops', 90)]
```

Python's sort is **stable**: equal items keep their original order, so you can sort by the
secondary key first, then by the primary key.

### Lists as stacks

`append` = push, `pop()` = pop, `stack[-1]` = peek, `if not stack` = empty. For queues use
`deque` (section 8.3).

---

## 5. Tuples and unpacking

A tuple is an **immutable** list. Use it for a fixed group of values that belong together (a
coordinate, a row, a return value with several parts). Tuples are hashable (if their contents
are), so they can be dict keys and set members, unlike lists.

```python
>>> point = (3, 4)
>>> x, y = point                         # unpacking
>>> x, y
(3, 4)
>>> first, *rest = [1, 2, 3, 4]          # star unpacking
>>> first, rest
(1, [2, 3, 4])
>>> *start, last = "a b c".split()
>>> last
'c'
>>> a, b = 1, 2
>>> a, b = b, a                          # swap
>>> a, b
(2, 1)
>>> seen = {(0, 0), (1, 2)}              # tuples as set members (grid cells)
>>> (1, 2) in seen
True
>>> (1,)                                 # one-element tuple needs the comma
(1,)
>>> def min_max(values):
...     return min(values), max(values)  # returning several values = returning a tuple
>>> lo, hi = min_max([4, 9, 1])
>>> lo, hi
(1, 9)
```

Tuples compare element by element, which is why `(priority, name)` tuples sort and heap so nicely:

```python
>>> (1, "b") < (1, "c") < (2, "a")
True
```

---

## 6. Dictionaries

A mapping from keys to values with O(1) average lookup. **The** most used structure in
real-world Python: JSON objects, records, indexes, caches, counters and lookup tables are all
dicts. Since Python 3.7, dicts keep **insertion order**.

Keys must be hashable: strings, numbers, tuples, frozensets. Not lists or dicts.

### Creating

```python
>>> {"a": 1, "b": 2} == dict(a=1, b=2) == dict([("a", 1), ("b", 2)])
True
>>> dict.fromkeys(["x", "y"], 0)
{'x': 0, 'y': 0}
>>> {n: n * n for n in range(4)}                 # dict comprehension
{0: 0, 1: 1, 2: 4, 3: 9}
```

### Reading safely

```python
>>> user = {"name": "Ada", "team": "ops"}
>>> user["name"]
'Ada'
>>> user.get("email")                  # None instead of KeyError
>>> user.get("email", "n/a")
'n/a'
>>> "team" in user                     # `in` checks KEYS
True
>>> list(user.keys()), list(user.values()), list(user.items())
(['name', 'team'], ['Ada', 'ops'], [('name', 'Ada'), ('team', 'ops')])
```

### Writing

```python
>>> d = {"a": 1}
>>> d["b"] = 2                          # add or overwrite
>>> d.setdefault("c", []).append("x")  # get, inserting a default first if missing
>>> d.update({"a": 10, "z": 26})        # merge in another dict (overwrites)
>>> d
{'a': 10, 'b': 2, 'c': ['x'], 'z': 26}
>>> d.pop("z"), d.pop("missing", None)  # remove and return (default avoids KeyError)
(26, None)
>>> {"a": 1, "b": 2} | {"b": 3, "c": 4}  # merge into a NEW dict; right side wins
{'a': 1, 'b': 3, 'c': 4}
>>> del d["c"]; d
{'a': 10, 'b': 2}
```

### Iterating

```python
>>> scores = {"ada": 90, "bob": 75, "cy": 82}
>>> for name, score in scores.items():
...     print(f"{name}: {score}")
ada: 90
bob: 75
cy: 82
>>> sorted(scores, key=scores.get, reverse=True)       # keys sorted by value
['ada', 'cy', 'bob']
>>> max(scores.items(), key=lambda kv: kv[1])          # the (key, value) with the top value
('ada', 90)
>>> {v: k for k, v in scores.items()}                  # invert
{90: 'ada', 75: 'bob', 82: 'cy'}
>>> {k: v for k, v in scores.items() if v >= 80}        # filter
{'ada': 90, 'cy': 82}
```

**Don't add or delete keys while iterating** a dict (`RuntimeError`). Iterate over
`list(d)` instead, or build a new dict.

### Common real-world patterns

```python
>>> orders = [("ada", 30), ("bob", 5), ("ada", 12)]
>>> totals = {}
>>> for name, amount in orders:
...     totals[name] = totals.get(name, 0) + amount       # accumulate
>>> totals
{'ada': 42, 'bob': 5}
>>> by_id = {u["id"]: u for u in [{"id": 7, "name": "Ada"}, {"id": 9, "name": "Bob"}]}
>>> by_id[9]["name"]                                       # index a list of records by id
'Bob'
>>> config = {"db": {"host": "localhost"}}
>>> config.get("db", {}).get("port", 5432)                 # safe nested access
5432
```

For counting and grouping, `Counter` and `defaultdict` (section 8) are even shorter.

---

## 7. Sets

An unordered collection of unique, hashable items with O(1) membership. Use it to
**deduplicate**, to answer "**have I seen this?**", and for **set algebra** (what's in A but not B?).

```python
>>> s = {3, 1, 3, 2}
>>> sorted(s)                         # duplicates gone; sets have no order, so sort to display
[1, 2, 3]
>>> s.add(4); s.discard(10)           # discard: no error if missing (remove() raises)
>>> 4 in s
True
>>> a, b = {1, 2, 3}, {2, 3, 4}
>>> a | b, a & b, a - b, a ^ b         # union, intersection, difference, symmetric difference
({1, 2, 3, 4}, {2, 3}, {1}, {1, 4})
>>> {1, 2} <= a, a.isdisjoint({9})      # subset, no overlap
(True, True)
>>> empty = set()                       # NOT {} (that's an empty dict)
>>> list(dict.fromkeys(["b", "a", "b", "c"]))   # dedupe while KEEPING order
['b', 'a', 'c']
```

Real-world example: which expected records are missing from an export?

```python
>>> expected_ids = {"P-1", "P-2", "P-3"}
>>> received_ids = {"P-2", "P-3", "P-9"}
>>> sorted(expected_ids - received_ids), sorted(received_ids - expected_ids)
(['P-1'], ['P-9'])
```

`frozenset` is an immutable set, so it can be a dict key or live inside another set.

---

## 8. `collections`: the upgraded containers

```python
from collections import Counter, defaultdict, deque, OrderedDict, namedtuple, ChainMap
```

### 8.1 `Counter`: counting things

A dict subclass whose missing keys count as 0. Use it for frequencies, tallies, "top N", and
comparing multisets.

```python
>>> from collections import Counter
>>> c = Counter(["solar", "pool", "solar", "fence", "solar"])
>>> c
Counter({'solar': 3, 'pool': 1, 'fence': 1})
>>> c["solar"], c["garage"]                  # missing -> 0, no KeyError
(3, 0)
>>> c.most_common(2)                         # list of (item, count), highest first
[('solar', 3), ('pool', 1)]
>>> c["pool"] += 5                           # works even for new keys
>>> c.update(["fence", "fence"])             # ADD counts from an iterable (dict.update would replace)
>>> c.total()                                # sum of all counts (3.10+)
12
>>> Counter("aab") == Counter("aba")         # same letters, same counts
True
>>> Counter(a=3, b=1) - Counter(a=1, b=5)    # subtraction drops counts <= 0
Counter({'a': 2})
>>> Counter(word.lower() for word in "The cat the hat".split())["the"]
2
```

### 8.2 `defaultdict`: grouping without boilerplate

Calls a factory to create a value the first time a key is used.

```python
>>> from collections import defaultdict
>>> by_status = defaultdict(list)
>>> for permit_id, status in [("P1", "open"), ("P2", "closed"), ("P3", "open")]:
...     by_status[status].append(permit_id)
>>> dict(by_status)
{'open': ['P1', 'P3'], 'closed': ['P2']}
>>> graph = defaultdict(set)                 # adjacency sets
>>> graph["a"].add("b"); graph["b"].add("a")
>>> sorted(graph["a"])
['b']
>>> nested = defaultdict(lambda: defaultdict(int))   # two-level counter
>>> nested["2026-03"]["solar"] += 1
>>> nested["2026-03"]["solar"]
1
```

**Gotcha:** just *reading* `d[key]` inserts the key. Use `key in d` or `d.get(key)` to check
without creating it.

### 8.3 `deque`: queues and sliding windows

A double-ended queue with O(1) append and pop at **both** ends. Use it for BFS, FIFO
queues, undo history, and "last N items".

```python
>>> from collections import deque
>>> q = deque(["a", "b"])
>>> q.append("c"); q.appendleft("z")
>>> q
deque(['z', 'a', 'b', 'c'])
>>> q.popleft(), q.pop()                     # FIFO from the left, LIFO from the right
('z', 'c')
>>> q[0], q[-1], len(q)                      # peek both ends
('a', 'b', 2)
>>> recent = deque(maxlen=3)                 # keeps only the last 3; old items fall off
>>> for reading in [10, 11, 12, 13]:
...     recent.append(reading)
>>> list(recent)
[11, 12, 13]
>>> d = deque([1, 2, 3, 4]); d.rotate(1); d   # rotate right by 1
deque([4, 1, 2, 3])
```

Use a `list` when you only touch the end; use a `deque` the moment you need the front.

### 8.4 `OrderedDict`: order you can rearrange

Plain dicts already keep insertion order. `OrderedDict` adds `move_to_end` and
`popitem(last=False)`, exactly what an LRU cache needs.

```python
>>> from collections import OrderedDict
>>> cache = OrderedDict(a=1, b=2, c=3)
>>> cache.move_to_end("a")                   # mark "a" as most recently used
>>> list(cache)
['b', 'c', 'a']
>>> cache.popitem(last=False)                # evict the oldest
('b', 2)
```

### 8.5 `namedtuple`: lightweight read-only records

```python
>>> from collections import namedtuple
>>> Reading = namedtuple("Reading", ["sensor", "value"])
>>> r = Reading("s-1", 21.5)
>>> r.sensor, r[1]                           # by name or by position
('s-1', 21.5)
>>> r._replace(value=22.0)                   # immutable: returns a modified copy
Reading(sensor='s-1', value=22.0)
>>> r._asdict()
{'sensor': 's-1', 'value': 21.5}
```

For records you'll add methods or defaults to, prefer `@dataclass` (section 13).

### 8.6 `ChainMap`: layered lookups

Looks keys up in several dicts in order, e.g. CLI flags, then environment, then defaults.

```python
>>> from collections import ChainMap
>>> defaults = {"region": "eu", "retries": 3}
>>> overrides = {"retries": 5}
>>> settings = ChainMap(overrides, defaults)
>>> settings["retries"], settings["region"]
(5, 'eu')
```

---

## 9. `heapq`: always get the smallest next

A **min-heap** stored in a plain list. Use it for priority queues, scheduling ("which job is
due next?"), Dijkstra, and "top k" over large data.

```python
>>> import heapq
>>> jobs = []
>>> heapq.heappush(jobs, (3, "send report"))     # (priority, item): tuples compare in order
>>> heapq.heappush(jobs, (1, "restart server"))
>>> heapq.heappush(jobs, (2, "reply to client"))
>>> jobs[0]                                      # peek at the smallest: O(1)
(1, 'restart server')
>>> heapq.heappop(jobs)                          # O(log n)
(1, 'restart server')
>>> nums = [5, 1, 8, 3]
>>> heapq.heapify(nums)                          # turn a list into a heap in place: O(n)
>>> heapq.nlargest(2, [5, 1, 8, 3]), heapq.nsmallest(2, [5, 1, 8, 3])
([8, 5], [1, 3])
>>> heapq.nlargest(1, [{"n": "a", "v": 2}, {"n": "b", "v": 9}], key=lambda d: d["v"])
[{'n': 'b', 'v': 9}]
```

- **Max-heap:** push `-priority` and negate it when you pop.
- **Ties:** if two priorities are equal Python compares the next tuple element. Add a
  counter (`itertools.count()`) as a tie-breaker to keep FIFO order, and so it never tries
  to compare two dicts.
- `heapq.merge(*sorted_lists)` lazily merges already-sorted inputs.

---

## 10. `bisect`: searching sorted lists

Binary search over a list that's already sorted: O(log n).

```python
>>> import bisect
>>> limits = [0, 1000, 5000, 20000]           # fee bands by project value
>>> fees = ["free", "small", "medium", "large"]
>>> fees[bisect.bisect_right(limits, 4999) - 1]   # which band does 4,999 fall in?
'small'
>>> sorted_ts = [10, 20, 20, 30]
>>> bisect.bisect_left(sorted_ts, 20), bisect.bisect_right(sorted_ts, 20)
(1, 3)
>>> bisect.bisect_right(sorted_ts, 25) - bisect.bisect_left(sorted_ts, 15)   # how many in [15, 25]
2
>>> bisect.insort(sorted_ts, 25); sorted_ts    # insert, keeping it sorted (the insert itself is O(n))
[10, 20, 20, 25, 30]
```

`bisect_left` gives the first position where `x` could go (before equal items);
`bisect_right` gives the position after them. Both accept `key=` (3.10+).

---

## 11. `itertools`: loops you don't have to write

```python
>>> import itertools
>>> list(itertools.chain([1, 2], (3,), [4]))           # concatenate iterables
[1, 2, 3, 4]
>>> list(itertools.chain.from_iterable([[1, 2], [3]]))  # flatten one level
[1, 2, 3]
>>> list(itertools.islice(itertools.count(10, 5), 3))   # first 3 of an infinite counter
[10, 15, 20]
>>> list(itertools.accumulate([3, 1, 4]))               # running totals (prefix sums)
[3, 4, 8]
>>> list(itertools.pairwise([1, 4, 9]))                 # consecutive pairs (3.10+)
[(1, 4), (4, 9)]
>>> list(itertools.product("ab", [1, 2]))               # nested loops
[('a', 1), ('a', 2), ('b', 1), ('b', 2)]
>>> list(itertools.combinations("abc", 2))
[('a', 'b'), ('a', 'c'), ('b', 'c')]
>>> len(list(itertools.permutations("abc")))
6
>>> list(itertools.zip_longest([1, 2, 3], "ab", fillvalue="-"))
[(1, 'a'), (2, 'b'), (3, '-')]
```

### `groupby`: group **consecutive** items

It only groups items that are next to each other, so **sort by the same key first**.

```python
>>> rows = [("ops", "ada"), ("eng", "bob"), ("ops", "cy")]
>>> rows.sort(key=lambda r: r[0])
>>> for team, members in itertools.groupby(rows, key=lambda r: r[0]):
...     print(team, [name for _, name in members])
eng ['bob']
ops ['ada', 'cy']
```

For grouping unsorted data, `defaultdict(list)` is usually simpler. `itertools.batched(it, n)`
(3.12+) chunks an iterable into tuples of `n`, which is handy for batching API calls.

---

## 12. `functools` and `operator`

```python
>>> from functools import cache, lru_cache, partial, reduce, cmp_to_key
>>> @cache                                  # memoize: remembers results per argument
... def fib(n):
...     return n if n < 2 else fib(n - 1) + fib(n - 2)
>>> fib(80)
23416728348467685
>>> @lru_cache(maxsize=128)                 # bounded memoization (evicts least recently used)
... def lookup(code):
...     return code.upper()
>>> lookup("eu"), lookup.cache_info().misses
('EU', 1)
>>> int_from_hex = partial(int, base=16)    # pre-fill arguments
>>> int_from_hex("ff")
255
>>> reduce(lambda acc, n: acc * n, [1, 2, 3, 4], 1)    # fold; often sum()/math.prod is clearer
24
>>> sorted([3, 1, 2], key=cmp_to_key(lambda a, b: b - a))   # use a Java-style comparator
[3, 2, 1]
```

`@cache` needs hashable arguments (no lists or dicts) and keeps everything forever. Use
`lru_cache(maxsize=…)` for long-running processes.

```python
>>> from operator import itemgetter, attrgetter
>>> rows = [{"name": "b", "age": 3}, {"name": "a", "age": 9}]
>>> [r["name"] for r in sorted(rows, key=itemgetter("name"))]
['a', 'b']
>>> itemgetter(0, 2)(["x", "y", "z"])
('x', 'z')
```

`attrgetter("field")` does the same for object attributes. Both are faster and more readable
than the equivalent lambda.

### Decorators in one example

```python
>>> import functools, time
>>> def timed(fn):
...     @functools.wraps(fn)                 # keeps fn's name and docstring
...     def wrapper(*args, **kwargs):
...         start = time.perf_counter()
...         try:
...             return fn(*args, **kwargs)
...         finally:
...             wrapper.last_ms = (time.perf_counter() - start) * 1000
...     return wrapper
>>> @timed
... def work(n):
...     return sum(range(n))
>>> work(1000), work.__name__, work.last_ms >= 0
(499500, 'work', True)
```

---

## 13. `dataclasses`, `enum` and type hints

### `@dataclass`: classes for data

Generates `__init__`, `__repr__` and `__eq__` from the field list. This is the Python answer
to Java POJOs and records.

```python
>>> from dataclasses import dataclass, field, asdict, replace
>>> @dataclass
... class Permit:
...     permit_id: str
...     applicant: str
...     status: str = "submitted"                          # default value
...     tags: list[str] = field(default_factory=list)      # mutable default: use a factory!
...
...     def approve(self):
...         self.status = "approved"
>>> p = Permit("P-17", "Layla")
>>> p
Permit(permit_id='P-17', applicant='Layla', status='submitted', tags=[])
>>> p.approve(); p.status
'approved'
>>> p == Permit("P-17", "Layla", "approved")              # field-by-field equality
True
>>> asdict(p)                                             # ready for json.dumps
{'permit_id': 'P-17', 'applicant': 'Layla', 'status': 'approved', 'tags': []}
>>> @dataclass(frozen=True, order=True)                   # immutable + hashable + sortable
... class Version:
...     major: int
...     minor: int
>>> sorted([Version(1, 10), Version(1, 2)])
[Version(major=1, minor=2), Version(major=1, minor=10)]
>>> replace(Version(1, 2), minor=3)                       # copy with changes
Version(major=1, minor=3)
```

Use `__post_init__(self)` for validation after the generated `__init__` runs.

### `enum`: a fixed set of named values

```python
>>> from enum import Enum
>>> class Status(Enum):
...     SUBMITTED = "submitted"
...     APPROVED = "approved"
>>> Status.APPROVED.value, Status("submitted"), Status["APPROVED"]
('approved', <Status.SUBMITTED: 'submitted'>, <Status.APPROVED: 'approved'>)
>>> [s.name for s in Status]
['SUBMITTED', 'APPROVED']
```

`Status("nope")` raises `ValueError`, which makes it good for validating input. `StrEnum`
(3.11+) members also behave like plain strings.

### Type hints you'll actually write

Hints are documentation plus editor and type-checker support. **Python doesn't enforce them at
runtime.**

```python
from typing import Callable, Iterable, TypedDict


def total(amounts: list[float]) -> float: ...
def find(users: dict[str, int], name: str) -> int | None: ...    # may return None
def apply(fn: Callable[[int], str], items: Iterable[int]) -> list[str]: ...


class UserRow(TypedDict):          # the shape of a JSON object
    id: int
    email: str
```

---

## 14. Files, paths and directories

Use `pathlib.Path` for paths (it's the modern API) and **always** open files with `with`,
so they're closed even if an error happens (Java's try-with-resources).

```python
>>> import tempfile
>>> from pathlib import Path
>>> root = Path(tempfile.mkdtemp())
>>> data_dir = root / "exports" / "2026"            # `/` joins path parts
>>> data_dir.mkdir(parents=True, exist_ok=True)     # like mkdir -p
>>> report = data_dir / "report.txt"
>>> report.write_text("line 1\nline 2\n", encoding="utf-8")
14
>>> report.read_text(encoding="utf-8").splitlines()
['line 1', 'line 2']
>>> report.name, report.stem, report.suffix, report.parent.name
('report.txt', 'report', '.txt', '2026')
>>> report.exists(), report.is_file(), data_dir.is_dir()
(True, True, True)
>>> report.stat().st_size
14
>>> [p.name for p in root.rglob("*.txt")]           # recursive search; glob() is one level
['report.txt']
```

### Reading and writing with `open`

```python
>>> with open(report, "a", encoding="utf-8") as f:   # "r" read, "w" overwrite, "a" append, "rb"/"wb" bytes
...     _ = f.write("line 3\n")
>>> with open(report, encoding="utf-8") as f:
...     for line_number, line in enumerate(f, start=1):   # iterates lazily: fine for huge files
...         print(line_number, line.rstrip("\n"))
1 line 1
2 line 2
3 line 3
```

- `f.read()` loads everything; iterate line by line for big files; `f.read(65536)` reads in chunks (binary files, hashing).
- `os.walk(root)` yields `(dirpath, dirnames, filenames)` for every directory, the classic recursive walk.
- `shutil.copy`, `shutil.move`, `shutil.rmtree` handle copying, moving and deleting trees.

---

## 15. CSV and JSON

### `csv`: always use the module, never `line.split(",")`

Real CSV has quoted fields with commas inside them. The `csv` module handles that.

```python
>>> import csv, io
>>> raw = 'id,name,amount\n1,"Acme, Inc.",1250.50\n2,Desert Co,980\n'
>>> rows = list(csv.DictReader(io.StringIO(raw)))     # each row is a dict keyed by the header
>>> rows[0]
{'id': '1', 'name': 'Acme, Inc.', 'amount': '1250.50'}
>>> sum(float(r["amount"]) for r in rows)              # values are ALWAYS strings: convert
2230.5
```

With a real file: `with open(path, newline="", encoding="utf-8") as f: reader = csv.DictReader(f)`.
The `newline=""` is required by the csv module.

```python
>>> out = io.StringIO()
>>> writer = csv.DictWriter(out, fieldnames=["id", "total"])
>>> _ = writer.writeheader()             # returns the number of characters written
>>> writer.writerows([{"id": 1, "total": 9.5}, {"id": 2, "total": 3}])
>>> out.getvalue().splitlines()
['id,total', '1,9.5', '2,3']
```

### `json`

```python
>>> import json
>>> payload = json.loads('{"id": 7, "tags": ["a", "b"], "active": true, "manager": null}')
>>> payload["active"], payload["manager"]       # true -> True, null -> None
(True, None)
>>> json.dumps({"b": 1, "a": [1, 2]}, sort_keys=True)
'{"a": [1, 2], "b": 1}'
>>> print(json.dumps({"id": 7}, indent=2))
{
  "id": 7
}
>>> json.dumps({"when": Path("x")}, default=str)     # default= handles types json doesn't know
'{"when": "x"}'
>>> json.loads(json.dumps({"point": (1, 2)}))        # tuples come back as lists
{'point': [1, 2]}
>>> json.loads(json.dumps({1: "a"}))                 # keys always come back as strings
{'1': 'a'}
```

Files: `json.load(f)` / `json.dump(obj, f, indent=2)` (no "s"). Invalid JSON raises
`json.JSONDecodeError`, a subclass of `ValueError`. **JSON Lines** (one object per line) is
common for logs: `[json.loads(line) for line in f if line.strip()]`.

---

## 16. Dates and times: `datetime`

```python
>>> from datetime import date, datetime, timedelta, timezone
>>> d = date(2026, 3, 1)
>>> d + timedelta(days=30), d.weekday(), d.isoformat()     # weekday: Monday is 0
(datetime.date(2026, 3, 31), 6, '2026-03-01')
>>> date(2026, 12, 25) - date(2026, 3, 1)                  # subtracting gives a timedelta
datetime.timedelta(days=299)
>>> ts = datetime.strptime("2026-03-01 14:30", "%Y-%m-%d %H:%M")   # parse with a format
>>> ts.strftime("%d %b %Y, %H:%M")                                  # format
'01 Mar 2026, 14:30'
>>> datetime.fromisoformat("2026-03-01T10:00:00+04:00")             # ISO 8601, with offset
datetime.datetime(2026, 3, 1, 10, 0, tzinfo=datetime.timezone(datetime.timedelta(seconds=14400)))
>>> utc = datetime(2026, 3, 1, 6, 0, tzinfo=timezone.utc)
>>> int(utc.timestamp())                                            # to Unix epoch seconds
1772344800
>>> datetime.fromtimestamp(1772344800, tz=timezone.utc)
datetime.datetime(2026, 3, 1, 6, 0, tzinfo=datetime.timezone.utc)
>>> (timedelta(hours=1, minutes=30)).total_seconds()
5400.0
```

Format codes you'll use: `%Y` year, `%m` month, `%d` day, `%H` hour (24h), `%M` minute,
`%S` second, `%b` short month name, `%a` short weekday, `%z` UTC offset.

**Time zones:** a datetime without `tzinfo` is *naive* (no zone). Comparing naive with aware
datetimes raises `TypeError`. Store and compare in UTC; convert for display with
`zoneinfo.ZoneInfo("Asia/Dubai")`:

```python
>>> from zoneinfo import ZoneInfo
>>> utc.astimezone(ZoneInfo("Asia/Dubai")).strftime("%H:%M %Z")
'10:00 +04'
```

Use `time.perf_counter()` (not `datetime.now()`) to measure how long code takes.

---

## 17. Regular expressions: `re`

Use regexes to validate and extract from text: IDs, dates, log lines. Always write patterns
as **raw strings** (`r"..."`) so backslashes aren't eaten.

```python
>>> import re
>>> line = "2026-03-01 10:00:05 ERROR [permits] request P-1043 failed in 812ms"
>>> m = re.search(r"(\d+)ms", line)              # search: anywhere in the string
>>> m.group(0), m.group(1), int(m.group(1))
('812ms', '812', 812)
>>> re.match(r"\d{4}-\d{2}-\d{2}", line) is not None   # match: only at the START
True
>>> re.fullmatch(r"P-\d+", "P-1043"), re.fullmatch(r"P-\d+", "P-1043x")   # whole string
(<re.Match object; span=(0, 6), match='P-1043'>, None)
>>> re.findall(r"P-\d+", "P-1, P-22 and P-333")
['P-1', 'P-22', 'P-333']
>>> pattern = re.compile(r"(?P<date>\S+) (?P<time>\S+) (?P<level>[A-Z]+) \[(?P<area>\w+)\]")
>>> pattern.match(line).groupdict()             # named groups -> a dict
{'date': '2026-03-01', 'time': '10:00:05', 'level': 'ERROR', 'area': 'permits'}
>>> re.sub(r"\d", "#", "card 4111-1111")         # replace
'card ####-####'
>>> re.sub(r"\s+", " ", "  too    many   spaces ").strip()
'too many spaces'
>>> re.split(r"[;,]\s*", "a, b;c")
['a', 'b', 'c']
>>> re.findall(r"error", "Error ERROR error", flags=re.IGNORECASE)
['Error', 'ERROR', 'error']
```

Building blocks: `\d` digit, `\w` word char, `\s` whitespace, `.` any char, `*` 0+, `+` 1+,
`?` optional, `{3}` exactly 3, `[abc]` one of, `^`/`$` start/end, `(...)` capture group,
`(?:...)` non-capturing group. If plain `split`, `startswith` or `in` can do the job, prefer
them: they're clearer.

---

## 18. Numbers: `math`, `statistics`, `decimal`, `random`

```python
>>> import math, statistics
>>> math.ceil(4.1), math.floor(4.9), math.isqrt(17), math.gcd(12, 18), math.prod([2, 3, 4])
(5, 4, 4, 6, 24)
>>> 0.1 + 0.2 == 0.3, math.isclose(0.1 + 0.2, 0.3)    # never compare floats with ==
(False, True)
>>> math.inf > 10**100, -math.inf < -10**100           # sentinels for min/max searches
(True, True)
>>> data = [12, 15, 15, 18, 40]
>>> statistics.mean(data), statistics.median(data), statistics.mode(data)
(20, 15, 15)
>>> round(statistics.pstdev(data), 2)                 # population standard deviation
10.18
>>> statistics.quantiles(range(1, 101), n=4)          # quartiles; n=100 for percentiles
[25.25, 50.5, 75.75]
```

### Money: use `Decimal`, not `float`

```python
>>> from decimal import Decimal, ROUND_HALF_UP
>>> 0.1 + 0.1 + 0.1
0.30000000000000004
>>> Decimal("0.1") + Decimal("0.1") + Decimal("0.1")   # construct from STRINGS
Decimal('0.3')
>>> Decimal("2.675").quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)   # round to cents
Decimal('2.68')
```

### `random`

```python
>>> import random
>>> rng = random.Random(42)            # seeded: reproducible runs (tests, simulations)
>>> rng.randint(1, 6), rng.choice(["a", "b", "c"]), rng.sample(range(100), 3)   # exact values can vary by Python version
(6, 'a', [3, 94, 35])
```

Also `rng.random()` (0–1 float), `rng.shuffle(lst)` (in place), and
`rng.choices(items, weights=..., k=n)` (with replacement). For tokens and passwords use the
`secrets` module, never `random`.

---

## 19. Errors and context managers

```python
>>> def parse_amount(text):
...     try:
...         value = float(text)
...     except ValueError:
...         raise ValueError(f"not a number: {text!r}") from None   # replace the message
...     else:
...         return value                    # runs only if no exception
...     finally:
...         pass                            # always runs (cleanup)
>>> parse_amount("12.5")
12.5
>>> try:
...     parse_amount("twelve")
... except ValueError as exc:
...     print(exc)
not a number: 'twelve'
>>> class PermitError(Exception):           # custom exception: subclass Exception
...     def __init__(self, permit_id, reason):
...         super().__init__(f"{permit_id}: {reason}")
...         self.permit_id = permit_id
>>> try:
...     raise PermitError("P-17", "missing survey")
... except PermitError as exc:
...     print(exc, exc.permit_id)
P-17: missing survey P-17
```

Built-in exceptions to know: `ValueError` (bad value), `TypeError` (wrong type), `KeyError`
(missing dict key), `IndexError`, `AttributeError` (often "this is None"),
`FileNotFoundError` / `PermissionError` (both `OSError`), `ZeroDivisionError`. Catch the
narrowest one you can. A bare `except:` also catches Ctrl-C.

### Context managers (`with`)

```python
>>> from contextlib import contextmanager, suppress
>>> @contextmanager
... def step(name):
...     print("start", name)
...     try:
...         yield                         # the body of the `with` block runs here
...     finally:
...         print("end", name)
>>> with step("import"):
...     print("working")
start import
working
end import
>>> with suppress(FileNotFoundError):       # ignore one specific error
...     Path("/no/such/file").unlink()
```

---

## 20. Iterators and generators

A **generator** produces values lazily, one at a time, so you can process data far bigger
than memory and build pipelines.

```python
>>> def read_records(lines):
...     for line in lines:
...         if line.strip() and not line.startswith("#"):
...             yield line.strip().split(",")        # pauses here until the next value is asked for
>>> records = read_records(["# header", "a,1", "", "b,2"])
>>> next(records)
['a', '1']
>>> list(records)                              # continues from where it paused
[['b', '2']]
>>> list(records)                              # a generator can only be consumed ONCE
[]
>>> sum(x * x for x in range(1_000_000))       # generator expression: no million-item list
333332833333500000
```

Chain small generators into a pipeline (read → parse → filter → aggregate), each step
`yield`ing to the next. `yield from other_iterable` delegates to another generator.

---

## 21. Concurrency in one page

| Work is… | Use | Why |
|---|---|---|
| Waiting on I/O (HTTP calls, files, DB) | `concurrent.futures.ThreadPoolExecutor` or `asyncio` | threads wait in parallel; the GIL is released during I/O |
| CPU-heavy pure Python (parsing, number crunching) | `ProcessPoolExecutor` | separate processes sidestep the GIL |

```python
>>> from concurrent.futures import ThreadPoolExecutor, as_completed
>>> def fetch(n):
...     return n * 10                        # imagine an HTTP call here
>>> with ThreadPoolExecutor(max_workers=4) as pool:
...     list(pool.map(fetch, [1, 2, 3]))      # results in INPUT order
[10, 20, 30]
>>> with ThreadPoolExecutor(max_workers=4) as pool:
...     futures = {pool.submit(fetch, n): n for n in [1, 2, 3]}
...     sorted(f.result() for f in as_completed(futures))   # as_completed: in FINISH order
[10, 20, 30]
>>> import asyncio
>>> async def fetch_async(n):
...     await asyncio.sleep(0)               # imagine `await client.get(...)`
...     return n * 10
>>> async def main():
...     return await asyncio.gather(*(fetch_async(n) for n in [1, 2, 3]))
>>> asyncio.run(main())
[10, 20, 30]
```

Shared mutable state across threads needs a `threading.Lock()` (`with lock:`). Limit
concurrency with `max_workers`, or with an `asyncio.Semaphore` in async code.

---

## 22. Logging, environment, and running scripts

```python
import logging
import os
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("permits")
log.info("imported %d rows", 120)         # lazy %-formatting: only built if the level is enabled
api_key = os.environ.get("API_KEY")       # configuration from the environment, None if unset
args = sys.argv[1:]                       # command-line arguments


def main() -> None:
    log.info("starting")


if __name__ == "__main__":                # runs only when executed directly, not when imported
    main()
```

Use `logging`, not `print`, in anything that will run on a server. Use `log.exception(...)`
inside an `except` block to include the traceback. For real CLIs, `argparse` parses flags and
generates `--help`.

---

## 23. Idioms checklist

| Instead of (Java habit) | Write |
|---|---|
| `for (int i = 0; i < xs.size(); i++)` | `for x in xs:` / `for i, x in enumerate(xs):` |
| looping two lists by index | `for a, b in zip(xs, ys):` |
| `if (map.containsKey(k)) v = map.get(k); else v = d;` | `v = d.get(k, default)` |
| counting with a map | `Counter(items)` |
| grouping with `computeIfAbsent` | `defaultdict(list)` |
| building a list with a loop and `add` | a list comprehension |
| `StringBuilder` | `"".join(parts)` |
| `x == null` | `x is None` |
| `list.size() == 0` | `if not items:` |
| checking a list in a loop | convert to a `set` first |
| getters and setters | plain attributes; `@property` if you later need logic |
| `Comparator` | `key=lambda r: (r.priority, r.name)` |
| `try { } finally { close(); }` | `with open(...) as f:` |
| `Integer.MAX_VALUE` | `math.inf` / `float("inf")` |
| `Arrays.fill(a, 0)` | `[0] * n` |
| `queue.poll()` on a `LinkedList` | `deque.popleft()` |
