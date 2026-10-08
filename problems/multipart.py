"""Multi-part interview questions, modelled on real question-bank prompts.

Each problem has `parts`. Only Part 1 is visible at first; the next part unlocks when
every test so far passes (tests are cumulative, so later parts must not break earlier
ones). Prompts state *what* to build, never *how*. Approach discussion lives in
`discussion`, which is shown only after the last part passes.

Tests are snippets (mode "script"): they run with the solution's names in scope plus a
fresh `tmpdir`, and must store their answer in `result`.
"""
import textwrap


def T(part, code, expected, **extra):
    return {"part": part, "args": [textwrap.dedent(code).strip()], "expected": expected, **extra}


# ============================================================ in-memory cache
CACHE_STARTER = '''from collections import OrderedDict


class LRUCache:
    """Memoizes func(*args, **kwargs) results, evicting the least recently used entry."""

    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache = OrderedDict()

    def generate_key(self, func, *args, **kwargs):
        return (func.__name__,) + args + tuple(kwargs.values())

    def call(self, func, *args, **kwargs):
        key = self.generate_key(func, *args, **kwargs)
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        value = func(*args, **kwargs)
        self.cache[key] = value
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)
        return value
'''

CACHE_SOLUTION = '''import json
import os
from collections import OrderedDict


class LRUCache:
    """Memoizes func(*args, **kwargs) results, evicting the least recently used entry.

    With a log_path, every access is appended to a JSON-lines log so the cache (values and
    LRU order) survives a crash; compact() rewrites the log down to the live entries.
    """

    def __init__(self, capacity: int, log_path: str | None = None):
        self.capacity = capacity
        self.cache = OrderedDict()
        self.log_path = log_path
        self._log = None
        if log_path:
            self._replay()
            self._log = open(log_path, "a", encoding="utf-8")

    def generate_key(self, func, *args, **kwargs):
        # JSON with sorted keys: hashable, independent of kwarg order, works for lists/dicts,
        # and keeps positional and keyword arguments apart.
        return (
            func.__name__,
            json.dumps(args, sort_keys=True, default=repr),
            json.dumps(kwargs, sort_keys=True, default=repr),
        )

    def call(self, func, *args, **kwargs):
        key = self.generate_key(func, *args, **kwargs)
        if key in self.cache:
            self.cache.move_to_end(key)
            self._append({"k": list(key)})  # a hit only needs to record recency
            return self.cache[key]
        value = func(*args, **kwargs)
        self._store(key, value)
        self._append({"k": list(key), "v": value})
        return value

    def compact(self) -> None:
        """Rewrite the log so it only holds the live entries, in LRU -> MRU order."""
        if not self.log_path:
            return
        tmp = self.log_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            for key, value in self.cache.items():
                f.write(json.dumps({"k": list(key), "v": value}) + "\\n")
            f.flush()
            os.fsync(f.fileno())
        self._log.close()
        os.replace(tmp, self.log_path)
        self._log = open(self.log_path, "a", encoding="utf-8")

    # -- internals ---------------------------------------------------------------
    def _store(self, key, value):
        self.cache[key] = value
        self.cache.move_to_end(key)
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)

    def _append(self, record):
        if self._log:
            self._log.write(json.dumps(record) + "\\n")
            self._log.flush()
            os.fsync(self._log.fileno())

    def _replay(self):
        if not os.path.exists(self.log_path):
            return
        with open(self.log_path, encoding="utf-8") as f:
            for line in f:
                try:
                    record = json.loads(line)
                    key = tuple(record["k"])
                except (ValueError, KeyError, TypeError):
                    continue  # torn write from a crash
                if "v" in record:
                    self._store(key, record["v"])
                elif key in self.cache:
                    self.cache.move_to_end(key)
'''

# Test preludes are indented to match the snippet bodies they're prepended to.
CACHE_COUNTER = textwrap.indent(textwrap.dedent('''
    calls = []
    def f(x):
        calls.append(x)
        return f"v{len(calls)}"
'''), " " * 12)

CACHE = {
    "id": "mp-durable-cache",
    "title": "In-Memory Cache: Bug Fix + Durability",
    "difficulty": "Medium",
    "category": "Multi-part",
    "tags": ["caching", "*args/**kwargs", "persistence", "OrderedDict"],
    "entry": "LRUCache",
    "mode": "script",
    "target_minutes": 45,
    "timeout": 20,
    "description": """
You're handed an existing `LRUCache` class (it's in the editor). It memoizes calls:
`cache.call(func, *args, **kwargs)` returns `func(*args, **kwargs)`, computing it only
on a cache miss, and evicts the least recently used entry when it's over `capacity`.

Function names are unique, so `func.__name__` identifies a function.
""",
    "parts": [
        {
            "title": "Bug hunt",
            "description": """
Users report that `call()` sometimes returns the **wrong cached value**, and sometimes
**crashes**. The eviction logic is fine; the problem is in `generate_key`.

Fix it. Calls with equal arguments must share a cache entry, and calls with different
arguments must not. It has to work for any positional and keyword arguments, including
unhashable ones like lists and dicts.
""",
        },
        {
            "title": "Survive a crash",
            "description": """
The process running the cache can crash at any moment. Make the cache durable:

```python
cache = LRUCache(capacity, log_path)   # log_path is optional; None = in-memory only
```

- A new `LRUCache` created with the same `log_path` (after a crash, no clean shutdown)
  must come back with **exactly the same entries and values**, and the **same LRU order**,
  so the next eviction is the one that would have happened without the crash.
- Persist before `call()` returns.
- A crash can happen in the middle of a write: the tail of the file may be truncated.
  Recovery must not fail because of it.
- The cost of persisting one `call()` must **not grow with the number of entries**
  in the cache.
""",
        },
        {
            "title": "Compaction",
            "description": """
The file on disk keeps growing forever. Add:

```python
cache.compact() -> None
```

After `compact()`, the file's size must be proportional to the number of entries in
the cache, not to the number of calls ever made. Recovery after compaction (and after
further calls) must behave exactly as before.
""",
        },
    ],
    "discussion": [
        "Durability vs throughput: fsync on every write vs group commit. What does \"no data loss\" actually promise?",
        "Is this system CPU-bound or IO-bound? How would you measure it?",
        "Should evictions be written to the log? What changes about recovery time and file size?",
        "Two processes share the same cache file: file locks, or a single writer with a queue?",
        "When should compaction run automatically, and what happens if you crash halfway through it?",
    ],
    "java_tip": """
*This tab names Python tools, which can hint at an approach.*

- `def f(*args, **kwargs)`: `args` is a **tuple**, `kwargs` is a **dict** (like Java varargs plus a `Map<String, Object>`).
- Dict keys must be hashable: tuples and strings are, lists and dicts aren't (`TypeError: unhashable type: 'list'`).
- `json.dumps(obj, sort_keys=True)` / `json.loads(s)`; JSON turns tuples into lists.
- Files: `open(path, "a")` appends; `f.flush()` pushes Python's buffer to the OS; `os.fsync(f.fileno())` pushes the OS buffer to disk; `os.replace(tmp, path)` is an atomic rename.
- `OrderedDict.move_to_end(k)` and `popitem(last=False)`. Note: assigning to an existing key does **not** move it.
""",
    "starter": CACHE_STARTER,
    "solution": CACHE_SOLUTION,
    "tests": [
        # ---- part 1
        T(1, """
            calls = []
            def f(a=0, b=0):
                calls.append((a, b))
                return a * 10 + b
            c = LRUCache(4)
            result = [c.call(f, a=1, b=2), c.call(f, b=2, a=1), len(calls)]
        """, [12, 12, 1], label="kwarg order doesn't matter"),
        T(1, """
            def f(x=0, y=0):
                return x * 10 + y
            c = LRUCache(4)
            result = [c.call(f, x=1), c.call(f, y=1)]
        """, [10, 1], label="kwarg names matter"),
        T(1, """
            def f(a, b=0, x=0):
                return a + 10 * b + 100 * x
            c = LRUCache(4)
            result = [c.call(f, 1, 2), c.call(f, 1, x=2)]
        """, [21, 201], label="positional vs keyword"),
        T(1, """
            calls = []
            def total(nums, weights=None):
                calls.append(1)
                return sum(nums) + sum((weights or {}).values())
            c = LRUCache(4)
            result = [
                c.call(total, [1, 2, 3]),
                c.call(total, [1, 2, 3]),
                c.call(total, [1, 2], weights={"a": 1, "b": 2}),
                c.call(total, [1, 2], weights={"b": 2, "a": 1}),
                len(calls),
            ]
        """, [6, 6, 6, 6, 2], label="unhashable arguments"),
        T(1, """
            calls = []
            def deep(cfg):
                calls.append(1)
                return len(str(cfg))
            c = LRUCache(4)
            a = c.call(deep, {"x": [1, {"y": 2}], "z": (3, 4)})
            b = c.call(deep, {"z": (3, 4), "x": [1, {"y": 2}]})
            c.call(deep, {"x": [1, {"y": 3}], "z": (3, 4)})
            result = [a == b, len(calls)]
        """, [True, 2], label="nested structures"),
        T(1, """
            def square(x):
                return x * x
            def cube(x):
                return x ** 3
            c = LRUCache(4)
            result = [c.call(square, 3), c.call(cube, 3)]
        """, [9, 27], label="different functions"),
        T(1, CACHE_COUNTER + """
            c = LRUCache(2)
            c.call(f, 1); c.call(f, 2); c.call(f, 1); c.call(f, 3); c.call(f, 1); c.call(f, 2)
            result = calls
        """, [1, 2, 3, 2], label="LRU eviction still works"),
        # ---- part 2
        T(2, CACHE_COUNTER + """
            import os
            p = os.path.join(tmpdir, "cache.log")
            c1 = LRUCache(3, p)
            before = [c1.call(f, 1), c1.call(f, 2)]
            c2 = LRUCache(3, p)            # crash: c1 is never closed
            after = [c2.call(f, 1), c2.call(f, 2)]
            result = [before, after, calls]
        """, [["v1", "v2"], ["v1", "v2"], [1, 2]], label="values survive a crash"),
        T(2, CACHE_COUNTER + """
            import os
            p = os.path.join(tmpdir, "cache.log")
            c1 = LRUCache(2, p)
            c1.call(f, 1); c1.call(f, 2); c1.call(f, 1)
            c2 = LRUCache(2, p)
            values = [c2.call(f, 3), c2.call(f, 1), c2.call(f, 2)]
            result = [values, calls]
        """, [["v3", "v1", "v4"], [1, 2, 3, 2]], label="LRU order survives a crash"),
        T(2, CACHE_COUNTER + """
            import os
            p = os.path.join(tmpdir, "cache.log")
            c1 = LRUCache(2, p)
            c1.call(f, 1); c1.call(f, 2); c1.call(f, 3)
            c2 = LRUCache(2, p)
            c2.call(f, 1); c2.call(f, 3)
            result = calls
        """, [1, 2, 3, 1], label="evicted entries stay evicted"),
        T(2, """
            import os
            calls = []
            def g(nums, opt=None):
                calls.append(1)
                return [sum(nums), sorted(opt)]
            p = os.path.join(tmpdir, "cache.log")
            c1 = LRUCache(4, p)
            a = c1.call(g, [1, 2], opt={"k": [3], "j": 1})
            c2 = LRUCache(4, p)
            b = c2.call(g, [1, 2], opt={"j": 1, "k": [3]})
            result = [a, b, len(calls)]
        """, [[3, ["j", "k"]], [3, ["j", "k"]], 1], label="list/dict arguments survive"),
        T(2, CACHE_COUNTER + """
            import os
            p = os.path.join(tmpdir, "cache.log")
            c1 = LRUCache(5, p)
            c1.call(f, 1); c1.call(f, 2); c1.call(f, 3)
            with open(p, "r+b") as fh:          # crash in the middle of the last write
                fh.truncate(os.path.getsize(p) - 3)
            c2 = LRUCache(5, p)
            result = [c2.call(f, 1), c2.call(f, 2), calls[:3]]
        """, ["v1", "v2", [1, 2, 3]], label="truncated tail is tolerated"),
        T(2, CACHE_COUNTER + """
            import os
            p = os.path.join(tmpdir, "cache.log")
            c = LRUCache(1000, p)
            for i in range(10):
                c.call(f, i)
            s10 = os.path.getsize(p)
            for i in range(10, 200):
                c.call(f, i)
            s200 = os.path.getsize(p)
            result = [s10 > 0, s200 < 40 * s10]
        """, [True, True], label="write cost doesn't grow with cache size"),
        T(2, CACHE_COUNTER + """
            import os
            c = LRUCache(2)
            c.call(f, 1); c.call(f, 1)
            result = [calls, os.listdir(tmpdir)]
        """, [[1], []], label="no log_path = in-memory only"),
        # ---- part 3
        T(3, CACHE_COUNTER + """
            import os
            p = os.path.join(tmpdir, "cache.log")
            c1 = LRUCache(3, p)
            for i in range(300):
                c1.call(f, i % 10)
            s_before = os.path.getsize(p)
            c1.compact()
            s_after = os.path.getsize(p)
            c2 = LRUCache(3, p)
            values = [c2.call(f, 7), c2.call(f, 0), c2.call(f, 9), c2.call(f, 8)]
            result = [s_after * 20 < s_before, values, calls[300:]]
        """, [True, ["v298", "v301", "v300", "v302"], [0, 8]], label="compaction keeps state and order"),
        T(3, CACHE_COUNTER + """
            import os
            p = os.path.join(tmpdir, "cache.log")
            c1 = LRUCache(3, p)
            for x in [1, 2, 3, 4]:
                c1.call(f, x)
            c1.compact()
            c1.call(f, 5)
            c3 = LRUCache(3, p)
            for x in [3, 4, 5, 2]:
                c3.call(f, x)
            result = calls
        """, [1, 2, 3, 4, 5, 2], label="logging continues after compaction"),
    ],
}


# ================================================================ IP iterator
IP_SOLUTION = '''def ip_to_int(ip: str) -> int:
    a, b, c, d = (int(x) for x in ip.split("."))
    return (a << 24) | (b << 16) | (c << 8) | d


def int_to_ip(n: int) -> str:
    return ".".join(str((n >> shift) & 255) for shift in (24, 16, 8, 0))


class IPV4Iterator:
    def __init__(self, ip_or_cidr: str, reverse: bool = False, step: int = 1) -> None:
        if step <= 0:
            raise ValueError("step must be positive")
        ip, _, prefix = ip_or_cidr.partition("/")
        self.current = ip_to_int(ip)
        if prefix:
            host_bits = 32 - int(prefix)
            network = self.current & ((0xFFFFFFFF << host_bits) & 0xFFFFFFFF)
            self.low, self.high = network, network + (1 << host_bits) - 1
        else:
            self.low, self.high = 0, 0xFFFFFFFF
        self.delta = -step if reverse else step

    def __iter__(self) -> "IPV4Iterator":
        return self

    def __next__(self) -> str:
        if not self.low <= self.current <= self.high:
            raise StopIteration
        ip = int_to_ip(self.current)
        self.current += self.delta
        return ip

    def next_batch(self, size: int) -> list[str]:
        batch = []
        for _ in range(size):
            try:
                batch.append(next(self))
            except StopIteration:
                break
        return batch


def range_to_cidrs(start_ip: str, end_ip: str) -> list[str]:
    low, high = ip_to_int(start_ip), ip_to_int(end_ip)
    blocks = []
    while low <= high:
        size = low & -low if low else 1 << 32   # largest block aligned at `low`
        while size > high - low + 1:
            size >>= 1
        blocks.append(f"{int_to_ip(low)}/{33 - size.bit_length()}")
        low += size
    return blocks
'''

IP = {
    "id": "mp-ip-iterator",
    "title": "IPv4 / CIDR Iterator",
    "difficulty": "Medium",
    "category": "Multi-part",
    "tags": ["iterator protocol", "bit manipulation", "string"],
    "entry": "IPV4Iterator",
    "mode": "script",
    "target_minutes": 45,
    "description": """
Build an iterator over IPv4 addresses. Each part extends the same class, and the
next part unlocks only when the current one passes. Work fast: in the real round
there's a hard stop, and only working code counts.

Iteration always **includes the starting address**. Inputs are valid; you don't
need to validate them.
""",
    "parts": [
        {
            "title": "Forward iteration",
            "description": """
```python
class IPV4Iterator:
    def __init__(self, ip: str) -> None: ...
    def __iter__(self): ...
    def __next__(self) -> str: ...
```

Starting at the dotted-quad `ip` (e.g. `"192.168.0.254"`), yield successive addresses
up to and including `255.255.255.255`, then stop (`StopIteration`).

```python
list(IPV4Iterator("255.255.255.250"))
# ["255.255.255.250", "255.255.255.251", ..., "255.255.255.255"]
```
""",
        },
        {
            "title": "Reverse",
            "description": """
Add an optional `reverse: bool = False` parameter. When `True`, iterate **downwards**
to and including `0.0.0.0`, then stop.

```python
list(IPV4Iterator("0.0.0.5", reverse=True))
# ["0.0.0.5", "0.0.0.4", "0.0.0.3", "0.0.0.2", "0.0.0.1", "0.0.0.0"]
```
""",
        },
        {
            "title": "CIDR blocks",
            "description": """
The input may also be in CIDR form, `"a.b.c.d/prefix"`. Then iteration is restricted to
that block, from its network address (all host bits 0) to its broadcast address (all
host bits 1), inclusive. Iteration starts from the given address, which may be
anywhere inside the block, and honours `reverse`.

```python
list(IPV4Iterator("192.168.1.5/29"))                # block is 192.168.1.0 - 192.168.1.7
# ["192.168.1.5", "192.168.1.6", "192.168.1.7"]
list(IPV4Iterator("192.168.1.5/29", reverse=True))
# ["192.168.1.5", "192.168.1.4", ..., "192.168.1.0"]
list(IPV4Iterator("192.168.1.100/32"))              # ["192.168.1.100"]
```
""",
        },
        {
            "title": "Step and batches",
            "description": """
Two throughput knobs, staying backwards compatible:

```python
IPV4Iterator(ip_or_cidr, reverse=False, step=1)   # advance `step` addresses per item
it.next_batch(size) -> list[str]                  # up to `size` next addresses; [] when exhausted
```

- `step <= 0` raises `ValueError`.
- Iteration stops at the same boundaries as before, and never yields an address past them.
""",
        },
        {
            "title": "Range to CIDR blocks",
            "description": """
Write a function (next to the class):

```python
range_to_cidrs(start_ip: str, end_ip: str) -> list[str]
```

Return the **fewest** CIDR blocks that exactly cover the inclusive range
`start_ip .. end_ip`, in ascending order.

```python
range_to_cidrs("192.168.1.5", "192.168.1.10")
# ["192.168.1.5/32", "192.168.1.6/31", "192.168.1.8/31", "192.168.1.10/32"]
```
""",
        },
    ],
    "discussion": [
        "How much memory does your iterator use while walking a /8? What's the cost per `next()`?",
        "How would you make iterating millions of addresses faster?",
        "Two clarifying questions worth asking up front: must inputs be validated, and must a CIDR seed lie inside its block?",
        "How would you check whether one CIDR block contains another, or whether two ranges overlap?",
    ],
    "java_tip": """
*This tab names Python tools, which can hint at an approach.*

- Iterator protocol: `__iter__` returns the iterator (usually `self`), and `__next__` returns the next item or `raise StopIteration`. There's no `hasNext()`.
- Python ints are unbounded: `~x` and `<<` don't wrap at 32 bits, so mask with `& 0xFFFFFFFF` when you need 32-bit behaviour.
- `s.partition("/")` → `(before, "/", after)`, or `(s, "", "")` if there's no `/`.
- `itertools.islice(it, n)` takes the first `n` items without exhausting the iterator.
""",
    "starter": '''class IPV4Iterator:
    def __init__(self, ip: str) -> None:
        pass

    def __iter__(self):
        pass

    def __next__(self) -> str:
        pass
''',
    "solution": IP_SOLUTION,
    "tests": [
        T(1, 'result = list(IPV4Iterator("255.255.255.250"))',
          ["255.255.255.250", "255.255.255.251", "255.255.255.252", "255.255.255.253", "255.255.255.254",
           "255.255.255.255"]),
        T(1, 'result = list(IPV4Iterator("255.255.255.255"))', ["255.255.255.255"]),
        T(1, """
            from itertools import islice
            result = list(islice(IPV4Iterator("0.0.0.0"), 3))
        """, ["0.0.0.0", "0.0.0.1", "0.0.0.2"]),
        T(1, """
            from itertools import islice
            result = list(islice(IPV4Iterator("192.168.0.254"), 3))
        """, ["192.168.0.254", "192.168.0.255", "192.168.1.0"], label="rollover"),
        T(1, """
            from itertools import islice
            result = list(islice(IPV4Iterator("10.255.255.255"), 2))
        """, ["10.255.255.255", "11.0.0.0"], label="multi-octet carry"),
        T(1, """
            it = IPV4Iterator("1.2.3.4")
            result = [iter(it) is it, next(it), next(it)]
        """, [True, "1.2.3.4", "1.2.3.5"], label="iterator protocol"),
        T(2, 'result = list(IPV4Iterator("0.0.0.5", reverse=True))',
          ["0.0.0.5", "0.0.0.4", "0.0.0.3", "0.0.0.2", "0.0.0.1", "0.0.0.0"]),
        T(2, 'result = list(IPV4Iterator("0.0.0.0", reverse=True))', ["0.0.0.0"]),
        T(2, """
            from itertools import islice
            result = list(islice(IPV4Iterator("192.168.1.1", reverse=True), 3))
        """, ["192.168.1.1", "192.168.1.0", "192.168.0.255"], label="underflow"),
        T(2, """
            from itertools import islice
            result = list(islice(IPV4Iterator("255.255.255.255", reverse=True), 2))
        """, ["255.255.255.255", "255.255.255.254"]),
        T(3, 'result = list(IPV4Iterator("192.168.1.5/29"))', ["192.168.1.5", "192.168.1.6", "192.168.1.7"]),
        T(3, 'result = list(IPV4Iterator("192.168.1.5/29", reverse=True))',
          ["192.168.1.5", "192.168.1.4", "192.168.1.3", "192.168.1.2", "192.168.1.1", "192.168.1.0"]),
        T(3, 'result = list(IPV4Iterator("192.168.1.100/32"))', ["192.168.1.100"]),
        T(3, 'result = [list(IPV4Iterator("10.0.0.0/31")), list(IPV4Iterator("10.0.0.1/31", reverse=True))]',
          [["10.0.0.0", "10.0.0.1"], ["10.0.0.1", "10.0.0.0"]], label="/31"),
        T(3, """
            ips = list(IPV4Iterator("10.1.2.0/24"))
            result = [len(ips), ips[0], ips[-1]]
        """, [256, "10.1.2.0", "10.1.2.255"]),
        T(3, 'result = list(IPV4Iterator("172.16.255.255/16"))', ["172.16.255.255"], label="seed at broadcast"),
        T(3, 'result = list(IPV4Iterator("172.16.0.0/16", reverse=True))', ["172.16.0.0"], label="seed at network"),
        T(4, """
            from itertools import islice
            result = list(islice(IPV4Iterator("10.0.0.0", step=64), 3))
        """, ["10.0.0.0", "10.0.0.64", "10.0.0.128"]),
        T(4, 'result = [list(IPV4Iterator("10.0.0.0/29", step=3)), list(IPV4Iterator("10.0.0.7/29", reverse=True, step=3))]',
          [["10.0.0.0", "10.0.0.3", "10.0.0.6"], ["10.0.0.7", "10.0.0.4", "10.0.0.1"]]),
        T(4, 'result = [list(IPV4Iterator("255.255.255.250", step=4)), list(IPV4Iterator("0.0.0.5", reverse=True, step=2))]',
          [["255.255.255.250", "255.255.255.254"], ["0.0.0.5", "0.0.0.3", "0.0.0.1"]], label="step near the edges"),
        T(4, """
            errors = []
            for bad in (0, -1):
                try:
                    IPV4Iterator("1.1.1.1", step=bad)
                except ValueError:
                    errors.append("ValueError")
            result = errors
        """, ["ValueError", "ValueError"]),
        T(4, """
            it = IPV4Iterator("192.168.1.250/29")
            result = [it.next_batch(4), it.next_batch(4), it.next_batch(4)]
        """, [["192.168.1.250", "192.168.1.251", "192.168.1.252", "192.168.1.253"],
              ["192.168.1.254", "192.168.1.255"], []]),
        T(4, """
            it = IPV4Iterator("10.0.0.10/28", reverse=True, step=5)
            result = [next(it), it.next_batch(5)]
        """, ["10.0.0.10", ["10.0.0.5", "10.0.0.0"]], label="next() and next_batch() share position"),
        T(5, 'result = range_to_cidrs("192.168.1.5", "192.168.1.10")',
          ["192.168.1.5/32", "192.168.1.6/31", "192.168.1.8/31", "192.168.1.10/32"]),
        T(5, 'result = [range_to_cidrs("10.0.0.0", "10.0.0.255"), range_to_cidrs("1.1.1.1", "1.1.1.1")]',
          [["10.0.0.0/24"], ["1.1.1.1/32"]]),
        T(5, 'result = range_to_cidrs("0.0.0.0", "255.255.255.255")', ["0.0.0.0/0"]),
        T(5, 'result = range_to_cidrs("10.0.0.1", "10.0.1.0")',
          ["10.0.0.1/32", "10.0.0.2/31", "10.0.0.4/30", "10.0.0.8/29", "10.0.0.16/28", "10.0.0.32/27",
           "10.0.0.64/26", "10.0.0.128/25", "10.0.1.0/32"]),
        T(5, 'result = range_to_cidrs("255.255.255.254", "255.255.255.255")', ["255.255.255.254/31"]),
    ],
}


# ============================================================= monster battle
BATTLE_SOLUTION = '''from enum import Enum


class MonsterType(Enum):
    FIRE = "Fire"
    WATER = "Water"
    GRASS = "Grass"
    ELECTRIC = "Electric"


# (attacker type, defender type) -> damage multiplier; anything missing is 1x
TYPE_CHART = {
    (MonsterType.FIRE, MonsterType.GRASS): 2.0,
    (MonsterType.FIRE, MonsterType.WATER): 0.5,
    (MonsterType.WATER, MonsterType.FIRE): 2.0,
    (MonsterType.WATER, MonsterType.GRASS): 0.5,
    (MonsterType.GRASS, MonsterType.WATER): 2.0,
    (MonsterType.GRASS, MonsterType.FIRE): 0.5,
    (MonsterType.ELECTRIC, MonsterType.WATER): 2.0,
}


class Monster:
    def __init__(self, name: str, health: int, attack: int, monster_type: MonsterType | None = None):
        self.name = name
        self.health = health
        self.attack = attack
        self.monster_type = monster_type

    def is_alive(self) -> bool:
        return self.health > 0

    def take_damage(self, damage: int) -> None:
        self.health -= damage

    def calculate_damage(self, defender: "Monster") -> int:
        multiplier = TYPE_CHART.get((self.monster_type, defender.monster_type), 1.0)
        return int(self.attack * multiplier)


class Team:
    def __init__(self, name: str, monsters: list[Monster]):
        self.name = name
        self.monsters = monsters

    def get_first_alive(self) -> Monster | None:
        return next((m for m in self.monsters if m.is_alive()), None)

    def get_best_attacker(self, defender: Monster) -> Monster | None:
        alive = [m for m in self.monsters if m.is_alive()]
        # max() keeps the first of equal elements, which is the tie-break we want
        return max(alive, key=lambda m: m.calculate_damage(defender), default=None)

    def is_defeated(self) -> bool:
        return not any(m.is_alive() for m in self.monsters)


def battle(team_a: Team, team_b: Team, smart_targeting: bool = False) -> list[str]:
    events = [f"Battle begins: {team_a.name} vs {team_b.name}"]
    attacking, defending = team_a, team_b
    while not team_a.is_defeated() and not team_b.is_defeated():
        defender = defending.get_first_alive()
        attacker = attacking.get_best_attacker(defender) if smart_targeting else attacking.get_first_alive()
        damage = attacker.calculate_damage(defender)
        defender.take_damage(damage)

        note = ""
        if damage > attacker.attack:
            note = " (Super effective!)"
        elif damage < attacker.attack:
            note = " (Not very effective...)"
        outcome = (f"{defender.name} has {defender.health} HP remaining." if defender.is_alive()
                   else f"{defender.name} is eliminated!")
        events.append(f"{attacker.name} attacks {defender.name} for {damage} damage{note}. {outcome}")
        attacking, defending = defending, attacking

    winner = team_a if team_b.is_defeated() else team_b
    events.append(f"Battle ends: {winner.name} wins!")
    return events
'''

BATTLE = {
    "id": "mp-monster-battle",
    "title": "Monster Battle Simulator",
    "difficulty": "Medium",
    "category": "Multi-part",
    "tags": ["OOP design", "simulation", "Enum"],
    "entry": "battle",
    "mode": "script",
    "target_minutes": 40,
    "description": """
An object-oriented design problem: two teams of monsters fight in turn-based combat.
Each part extends the same code. Interviewers look for clean classes with clear
responsibilities, so keep it tidy as well as correct.
""",
    "parts": [
        {
            "title": "Basic battle",
            "description": """
```python
class Monster:
    def __init__(self, name: str, health: int, attack: int): ...
    def is_alive(self) -> bool: ...                 # health > 0
    def take_damage(self, damage: int) -> None: ...

class Team:
    def __init__(self, name: str, monsters: list[Monster]): ...
    def get_first_alive(self) -> Monster | None: ...
    def is_defeated(self) -> bool: ...

def battle(team_a: Team, team_b: Team) -> list[str]: ...
```

**Rules**

- Team A attacks first; the teams alternate, one attack per turn.
- The first living monster of the attacking team hits the first living monster of the
  defending team for `attack` damage. Attackers take no damage back.
- A monster at 0 HP or less is eliminated.
- The battle ends when one team has no living monsters.

**Log format** (returned as a list of strings, exactly):

```
Battle begins: {team A} vs {team B}
{attacker} attacks {defender} for {damage} damage. {defender} has {hp} HP remaining.
{attacker} attacks {defender} for {damage} damage. {defender} is eliminated!
Battle ends: {winning team} wins!
```
""",
        },
        {
            "title": "Elemental types",
            "description": """
Monsters get a type:

```python
class MonsterType(Enum):
    FIRE = "Fire"; WATER = "Water"; GRASS = "Grass"; ELECTRIC = "Electric"

Monster(name, health, attack, monster_type=None)   # keep it optional: None = no type
Monster.calculate_damage(self, defender) -> int
```

| Attacker → Defender | Multiplier |
|---|---|
| Fire → Grass, Water → Fire, Grass → Water, Electric → Water | 2x |
| Fire → Water, Water → Grass, Grass → Fire | 0.5x |
| anything else (including untyped monsters) | 1x |

Damage is `int(attack * multiplier)`. The turn order is unchanged. When the damage
differs from the attacker's base attack, the log adds a note right after `damage`:

```
Squirt attacks Charmer for 16 damage (Super effective!). Charmer has 24 HP remaining.
Charmer attacks Squirt for 5 damage (Not very effective...). Squirt has 25 HP remaining.
```
""",
        },
        {
            "title": "Smart targeting",
            "description": """
Add a parameter: `battle(team_a, team_b, smart_targeting=False)`. The default keeps
the behaviour from the earlier parts.

With `smart_targeting=True`, the defender is still the first living monster of the
defending team, but the attacking team picks **whichever living monster deals the most
damage to that defender**. On a tie, the one earliest in the team's list attacks.
""",
        },
    ],
    "discussion": [
        "Where would you add a new type, a status effect (poison), or healing? Which classes change?",
        "Should `battle` mutate the teams passed in? What are the alternatives?",
        "How would you make targeting strategies pluggable (Strategy pattern) without if/else in the loop?",
        "How would you test this deterministically if attacks had a random critical-hit chance?",
    ],
    "java_tip": """
*This tab names Python tools, which can hint at an approach.*

- `from enum import Enum` then `class MonsterType(Enum): FIRE = "Fire"`; use it as `MonsterType.FIRE`, with `.value` giving `"Fire"`.
- Tuples of enums make good dict keys: `chart[(a, b)]`, `chart.get((a, b), 1.0)`.
- `int(7.5) == 7` truncates, like a Java `(int)` cast.
- `max(items, key=fn)` returns the **first** maximal item.
- Forward references in type hints: write the class name in quotes, `"Monster"`.
""",
    "starter": '''class Monster:
    def __init__(self, name: str, health: int, attack: int):
        pass

    def is_alive(self) -> bool:
        pass

    def take_damage(self, damage: int) -> None:
        pass


class Team:
    def __init__(self, name: str, monsters: list[Monster]):
        pass

    def get_first_alive(self) -> Monster | None:
        pass

    def is_defeated(self) -> bool:
        pass


def battle(team_a: Team, team_b: Team) -> list[str]:
    pass
''',
    "solution": BATTLE_SOLUTION,
    "tests": [
        T(1, """
            a = Team("Heroes", [Monster("Knight", 30, 10)])
            b = Team("Slimes", [Monster("Slime", 15, 5)])
            result = battle(a, b)
        """, ["Battle begins: Heroes vs Slimes",
              "Knight attacks Slime for 10 damage. Slime has 5 HP remaining.",
              "Slime attacks Knight for 5 damage. Knight has 25 HP remaining.",
              "Knight attacks Slime for 10 damage. Slime is eliminated!",
              "Battle ends: Heroes wins!"]),
        T(1, """
            a = Team("Vermin", [Monster("Rat", 5, 1), Monster("Bat", 4, 2)])
            b = Team("Forest", [Monster("Bear", 20, 6)])
            result = battle(a, b)
        """, ["Battle begins: Vermin vs Forest",
              "Rat attacks Bear for 1 damage. Bear has 19 HP remaining.",
              "Bear attacks Rat for 6 damage. Rat is eliminated!",
              "Bat attacks Bear for 2 damage. Bear has 17 HP remaining.",
              "Bear attacks Bat for 6 damage. Bat is eliminated!",
              "Battle ends: Forest wins!"], label="team B wins"),
        T(1, """
            a = Team("Heroes", [Monster("Dragon", 100, 25), Monster("Griffin", 80, 20)])
            b = Team("Monsters", [Monster("Goblin", 30, 10), Monster("Orc", 50, 15), Monster("Troll", 70, 12)])
            log = battle(a, b)
            result = [len(log), log[7], log[-1]]
        """, [15, "Dragon attacks Orc for 25 damage. Orc is eliminated!", "Battle ends: Heroes wins!"],
          label="exactly 0 HP is eliminated"),
        T(1, """
            m = Monster("Blob", 3, 1)
            t = Team("Solo", [m])
            before = [m.is_alive(), t.is_defeated(), t.get_first_alive().name]
            m.take_damage(3)
            result = before + [m.is_alive(), t.is_defeated(), t.get_first_alive()]
        """, [True, False, "Blob", False, True, None], label="Monster / Team API"),
        T(2, """
            dragon = Monster("FireDragon", 100, 20, MonsterType.FIRE)
            serpent = Monster("WaterSerpent", 80, 15, MonsterType.WATER)
            eel = Monster("Eel", 50, 15, MonsterType.ELECTRIC)
            fern = Monster("Fern", 50, 15, MonsterType.GRASS)
            plain = Monster("Plain", 50, 15)
            result = [dragon.calculate_damage(serpent), serpent.calculate_damage(dragon),
                      eel.calculate_damage(fern), fern.calculate_damage(dragon), plain.calculate_damage(dragon),
                      eel.calculate_damage(serpent), serpent.calculate_damage(eel)]
        """, [10, 30, 15, 7, 15, 30, 15], label="type chart"),
        T(2, """
            a = Team("Blaze", [Monster("Charmer", 40, 10, MonsterType.FIRE)])
            b = Team("Tide", [Monster("Squirt", 30, 8, MonsterType.WATER)])
            result = battle(a, b)
        """, ["Battle begins: Blaze vs Tide",
              "Charmer attacks Squirt for 5 damage (Not very effective...). Squirt has 25 HP remaining.",
              "Squirt attacks Charmer for 16 damage (Super effective!). Charmer has 24 HP remaining.",
              "Charmer attacks Squirt for 5 damage (Not very effective...). Squirt has 20 HP remaining.",
              "Squirt attacks Charmer for 16 damage (Super effective!). Charmer has 8 HP remaining.",
              "Charmer attacks Squirt for 5 damage (Not very effective...). Squirt has 15 HP remaining.",
              "Squirt attacks Charmer for 16 damage (Super effective!). Charmer is eliminated!",
              "Battle ends: Tide wins!"]),
        T(2, """
            a = Team("Mixed", [Monster("Leaf", 10, 9, MonsterType.GRASS), Monster("Rock", 10, 4)])
            b = Team("Pond", [Monster("Frog", 20, 3, MonsterType.WATER)])
            result = battle(a, b)
        """, ["Battle begins: Mixed vs Pond",
              "Leaf attacks Frog for 18 damage (Super effective!). Frog has 2 HP remaining.",
              "Frog attacks Leaf for 1 damage (Not very effective...). Leaf has 9 HP remaining.",
              "Leaf attacks Frog for 18 damage (Super effective!). Frog is eliminated!",
              "Battle ends: Mixed wins!"], label="int() rounding"),
        T(3, """
            a = Team("A", [Monster("Fire", 50, 20, MonsterType.FIRE), Monster("Electric", 50, 15, MonsterType.ELECTRIC)])
            b = Team("B", [Monster("Water", 100, 10, MonsterType.WATER)])
            result = battle(a, b, smart_targeting=True)
        """, ["Battle begins: A vs B",
              "Electric attacks Water for 30 damage (Super effective!). Water has 70 HP remaining.",
              "Water attacks Fire for 20 damage (Super effective!). Fire has 30 HP remaining.",
              "Electric attacks Water for 30 damage (Super effective!). Water has 40 HP remaining.",
              "Water attacks Fire for 20 damage (Super effective!). Fire has 10 HP remaining.",
              "Electric attacks Water for 30 damage (Super effective!). Water has 10 HP remaining.",
              "Water attacks Fire for 20 damage (Super effective!). Fire is eliminated!",
              "Electric attacks Water for 30 damage (Super effective!). Water is eliminated!",
              "Battle ends: A wins!"]),
        T(3, """
            a = Team("Twins", [Monster("First", 10, 10), Monster("Second", 10, 10)])
            b = Team("Dummy", [Monster("Dummy", 25, 1)])
            result = battle(a, b, smart_targeting=True)
        """, ["Battle begins: Twins vs Dummy",
              "First attacks Dummy for 10 damage. Dummy has 15 HP remaining.",
              "Dummy attacks First for 1 damage. First has 9 HP remaining.",
              "First attacks Dummy for 10 damage. Dummy has 5 HP remaining.",
              "Dummy attacks First for 1 damage. First has 8 HP remaining.",
              "First attacks Dummy for 10 damage. Dummy is eliminated!",
              "Battle ends: Twins wins!"], label="ties go to the earliest monster"),
        T(3, """
            def teams():
                return (Team("A", [Monster("Weak", 30, 2), Monster("Strong", 30, 9)]),
                        Team("B", [Monster("Target", 20, 5)]))
            plain = battle(*teams())
            smart = battle(*teams(), smart_targeting=True)
            result = [plain[1], smart[1], len(plain), len(smart)]
        """, ["Weak attacks Target for 2 damage. Target has 18 HP remaining.",
              "Strong attacks Target for 9 damage. Target has 11 HP remaining.", 15, 7],
          label="default is unchanged"),
    ],
}


# ========================================================== file deduplication
DEDUP_SOLUTION = '''import hashlib
import os
from collections import defaultdict

PREFIX_BYTES = 1024
CHUNK_BYTES = 1 << 16


def _digest(path: str, limit: int | None = None) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        if limit is not None:
            h.update(f.read(limit))
        else:
            while chunk := f.read(CHUNK_BYTES):
                h.update(chunk)
    return h.hexdigest()


def _split(paths: list[str], key) -> list[list[str]]:
    """Group paths by key(path), dropping unreadable files and singleton groups."""
    groups = defaultdict(list)
    for path in paths:
        try:
            groups[key(path)].append(path)
        except OSError:
            continue
    return [g for g in groups.values() if len(g) > 1]


def find_duplicate_files(root_path: str) -> list[list[str]]:
    by_size = defaultdict(list)
    for dirpath, _dirnames, filenames in os.walk(root_path):
        for name in filenames:
            path = os.path.join(dirpath, name)
            if os.path.islink(path):
                continue
            try:
                by_size[os.path.getsize(path)].append(path)
            except OSError:
                continue

    duplicates = []
    for size, paths in by_size.items():
        if len(paths) < 2:
            continue
        if size == 0:
            duplicates.append(paths)
            continue
        for candidates in _split(paths, lambda p: _digest(p, PREFIX_BYTES)):
            if size <= PREFIX_BYTES:
                duplicates.append(candidates)       # the prefix was the whole file
            else:
                duplicates.extend(_split(candidates, _digest))
    return duplicates
'''

DEDUP_IMPORTS = "\n            from practice_helpers import make_tree, rel_groups, Symlink, track_file_reads\n"

DEDUP = {
    "id": "mp-file-dedup",
    "title": "File Deduplication",
    "difficulty": "Medium",
    "category": "Multi-part",
    "tags": ["filesystem", "hashing", "os.walk"],
    "entry": "find_duplicate_files",
    "mode": "script",
    "target_minutes": 30,
    "timeout": 20,
    "description": """
```python
def find_duplicate_files(root_path: str) -> list[list[str]]: ...
```

Walk the directory tree under `root_path` and return groups of files whose contents are
**byte-for-byte identical**. Each group has at least 2 paths; files without a duplicate
don't appear. Paths can be absolute or start with `root_path`. The order of groups and of
paths within a group doesn't matter.

The tests build their own directory trees, so write the walking and file reading yourself.
""",
    "parts": [
        {
            "title": "Find the duplicates",
            "description": "Get it working on ordinary files and nested directories.",
        },
        {
            "title": "Real-world filesystems",
            "description": """
The tree can contain:

- **Symbolic links** (to files, to directories, broken ones, even loops): ignore them,
  so they're never reported and never followed.
- **Unreadable files** (permission denied): skip them; the walk must not crash.
""",
        },
        {
            "title": "I/O budget",
            "description": """
The directories hold large files, and reading them is the bottleneck. Your solution
must stay within this I/O budget:

- A file whose size no other file shares must **never be opened**.
- A file whose first 1 KB differs from every other file of the same size must not have
  more than **64 KB** read from it.
""",
        },
    ],
    "discussion": [
        "Is this IO-bound or CPU-bound? How would you find out, and would you use threads or processes?",
        "Which hash would you use, and why? What's the real risk of a collision, and is a final byte-compare worth it?",
        "Every file is identical and 10 GB. What changes?",
        "The tree has a billion files across many machines. How do you distribute the work and merge results?",
        "How would you detect duplicates in real time as new files are written?",
    ],
    "java_tip": """
*This tab names Python tools, which can hint at an approach.*

- `os.walk(root)` yields `(dirpath, dirnames, filenames)` for every directory, recursively. Join with `os.path.join(dirpath, name)`.
- `os.path.getsize`, `os.path.islink`; or `pathlib.Path(root).rglob("*")` with `.is_file()`, `.stat().st_size`.
- Binary reads: `with open(path, "rb") as f: chunk = f.read(65536)`. An empty `bytes` means end of file.
- `hashlib.sha256()`, then `.update(chunk)` in a loop and `.hexdigest()` at the end.
- `while chunk := f.read(n):` is the walrus operator, the idiomatic read loop.
- Permission problems raise `PermissionError`, a subclass of `OSError`.
""",
    "starter": '''import os


def find_duplicate_files(root_path: str) -> list[list[str]]:
    pass
''',
    "solution": DEDUP_SOLUTION,
    "tests": [
        T(1, DEDUP_IMPORTS + """
            make_tree(tmpdir, {"a.txt": "hello", "b.txt": "hello", "c.txt": "world", "d/e.txt": "hello",
                               "d/f.txt": "world!", "g.txt": "bye", "x/y/z.txt": "world"})
            result = rel_groups(find_duplicate_files(tmpdir), tmpdir)
        """, [["a.txt", "b.txt", "d/e.txt"], ["c.txt", "x/y/z.txt"]]),
        T(1, DEDUP_IMPORTS + """
            make_tree(tmpdir, {"e1": "", "dir/e2": "", "solo": "x"})
            result = rel_groups(find_duplicate_files(tmpdir), tmpdir)
        """, [["dir/e2", "e1"]], label="empty files are duplicates of each other"),
        T(1, DEDUP_IMPORTS + """
            make_tree(tmpdir, {"a": "abc", "b": "abd", "c": "abcd"})
            result = rel_groups(find_duplicate_files(tmpdir), tmpdir)
        """, [], label="same size, different content"),
        T(1, DEDUP_IMPORTS + """
            blob = bytes(range(256)) * 400
            make_tree(tmpdir, {"bin/one.dat": blob, "two.dat": blob, "three.dat": blob[:-1] + b"x"})
            result = rel_groups(find_duplicate_files(tmpdir), tmpdir)
        """, [["bin/one.dat", "two.dat"]], label="binary files that differ only at the end"),
        T(1, DEDUP_IMPORTS + """
            make_tree(tmpdir, {"a/b/c/d/e/f.txt": "deep", "top.txt": "deep", "a/x.txt": "other"})
            result = rel_groups(find_duplicate_files(tmpdir), tmpdir)
        """, [["a/b/c/d/e/f.txt", "top.txt"]], label="deep nesting"),
        T(1, DEDUP_IMPORTS + """
            make_tree(tmpdir, {"only.txt": "lonely"})
            result = rel_groups(find_duplicate_files(tmpdir), tmpdir)
        """, []),
        T(2, DEDUP_IMPORTS + """
            make_tree(tmpdir, {"a": "same", "b": "same", "link_to_a": Symlink("a"), "broken": Symlink("missing"),
                               "sub/c": "other", "loop": Symlink("."), "sub/up": Symlink("..")})
            result = rel_groups(find_duplicate_files(tmpdir), tmpdir)
        """, [["a", "b"]], label="symlinks are ignored"),
        T(2, DEDUP_IMPORTS + """
            import os
            make_tree(tmpdir, {"secret": "abcde", "x": "zzzzz", "y": "zzzzz"})
            os.chmod(os.path.join(tmpdir, "secret"), 0)
            try:
                result = rel_groups(find_duplicate_files(tmpdir), tmpdir)
            finally:
                os.chmod(os.path.join(tmpdir, "secret"), 0o644)
        """, [["x", "y"]], label="unreadable file doesn't crash the walk"),
        T(3, DEDUP_IMPORTS + """
            make_tree(tmpdir, {"s1": "a", "s2": "bb", "s3": "ccc", "d1": "dddd", "d2": "dddd"})
            with track_file_reads(tmpdir) as (opened, _):
                groups = find_duplicate_files(tmpdir)
            result = [rel_groups(groups, tmpdir), sorted(opened)]
        """, [[["d1", "d2"]], ["d1", "d2"]], label="unique sizes are never opened"),
        T(3, DEDUP_IMPORTS + """
            mb = 1 << 20
            make_tree(tmpdir, {"diff_a": b"A" + bytes(mb - 1), "diff_b": b"B" + bytes(mb - 1),
                               "dup_1": b"C" * mb, "dup_2": b"C" * mb})
            with track_file_reads(tmpdir) as (_, read):
                groups = find_duplicate_files(tmpdir)
            result = [rel_groups(groups, tmpdir), read["diff_a"] <= 65536, read["diff_b"] <= 65536]
        """, [[["dup_1", "dup_2"]], True, True], label="differing prefixes are cheap"),
        T(3, DEDUP_IMPORTS + """
            mb = 1 << 20
            make_tree(tmpdir, {"p": bytes(mb) + b"1", "q": bytes(mb) + b"2", "r": bytes(mb) + b"1"})
            result = rel_groups(find_duplicate_files(tmpdir), tmpdir)
        """, [["p", "r"]], label="same prefix, different tail"),
    ],
}


# ============================================================ cluster messages
CLUSTER_SOLUTION = '''class Node:
    def __init__(self, node_id: str, children: list[str], parent: str | None):
        self.node_id = node_id
        self.children = children
        self.parent = parent
        self._runs = 0
        self._seen = set()     # request ids this node has already started
        self._pending = {}     # request id -> {"waiting": set of children, "results": {child: payload}}

    def sendAsyncMessage(self, node_id: str, message: str) -> None:
        """Provided by the cluster (the tests replace it)."""

    def receiveMessage(self, fromNodeId: str | None, message: str) -> None:
        if fromNodeId is None:                      # a request from outside, to the root
            self._runs += 1
            self._start(message, f"{message}-{self._runs}")
            return
        parts = message.split("|", 3)
        if parts[0] == "REQ":
            self._start(parts[1], parts[2])
            return
        _, kind, rid, payload = parts
        state = self._pending.get(rid)
        if state is None or fromNodeId not in state["waiting"]:
            return                                  # duplicate or stale reply
        state["waiting"].discard(fromNodeId)
        state["results"][fromNodeId] = payload
        if not state["waiting"]:
            del self._pending[rid]
            self._finish(kind, rid, state["results"])

    def _start(self, kind: str, rid: str) -> None:
        if rid in self._seen:                       # duplicate request
            return
        self._seen.add(rid)
        if not self.children:
            self._finish(kind, rid, {})
            return
        self._pending[rid] = {"waiting": set(self.children), "results": {}}
        for child in self.children:
            self.sendAsyncMessage(child, f"REQ|{kind}|{rid}")

    def _finish(self, kind: str, rid: str, results: dict) -> None:
        if kind == "count":
            answer = str(1 + sum(int(v) for v in results.values()))
        else:
            inner = ",".join(results[c] for c in self.children)
            answer = f"{self.node_id}({inner})" if self.children else self.node_id
        if self.parent is None:
            print(answer)
        else:
            self.sendAsyncMessage(self.parent, f"RES|{kind}|{rid}|{answer}")
'''

TREE_6 = '{"1": ["2", "3"], "2": ["4", "5"], "3": ["6"]}'
TREE_7 = '{"1": ["2", "3"], "2": ["4", "5"], "3": ["6", "7"]}'
RC = "from practice_helpers import run_cluster\n"

CLUSTER = {
    "id": "mp-cluster-messages",
    "title": "Cluster Count & Topology via Messages",
    "difficulty": "Medium",
    "category": "Multi-part",
    "tags": ["tree", "message passing", "state machine", "idempotency"],
    "entry": "Node",
    "mode": "script",
    "target_minutes": 45,
    "description": """
Machines in a cluster form a **tree**. Each machine runs the same code, a `Node`, and
can only talk to its **parent and direct children**, by sending asynchronous messages:

```python
class Node:
    def __init__(self, node_id: str, children: list[str], parent: str | None): ...
    def sendAsyncMessage(self, node_id: str, message: str) -> None: ...   # PROVIDED
    def receiveMessage(self, fromNodeId: str | None, message: str) -> None: ...  # YOU WRITE THIS
```

- `sendAsyncMessage` is provided and reliable. Delivery is **asynchronous**: messages
  arrive later, in any order. When a message arrives, the receiver's `receiveMessage` runs.
- The root has `parent = None`; leaves have `children = []`.
- A job starts when the root receives a message from **outside** the cluster
  (`fromNodeId = None`). Each part says which message.
- **Only the root prints**, exactly once per job: just the answer. Any other print fails
  the tests, so remove debug prints before running.
- You choose the format of the messages the nodes send to each other (strings only).
""",
    "parts": [
        {
            "title": "Count the machines",
            "description": """
When the root receives `"count"` from outside, the cluster must work out how many
machines it has, and the root prints that number (e.g. `6`).

A cluster can be asked to count more than once.
""",
        },
        {
            "title": "Map the topology",
            "description": """
When the root receives `"topology"` from outside, the root prints the shape of the whole
tree in this format:

- a leaf is just its id: `4`
- a node with children is `id(child1,child2,...)`, with children in the same order as that
  node's `children` list

```
        1
       / \\
      2   3        ->   1(2(4,5),3(6))
     / \\   \\
    4   5   6
```

`"count"` must keep working, and jobs can come one after another on the same cluster.
""",
        },
        {
            "title": "Duplicate deliveries",
            "description": """
The network now sometimes delivers a message **twice**. The duplicate can arrive at
any later time, even after the job has finished.

The answers must still be exactly right, and each job must still print exactly once.
""",
        },
    ],
    "discussion": [
        "Messages can now also be lost. How do you detect and recover from that (timeouts, retries)?",
        "What happens if a machine crashes mid-job? Can the root ever know the answer is complete?",
        "How much state does each node hold per job, and when can it be cleaned up?",
        "The tree has 1M nodes and is 10k levels deep. How long does a count take, and how big do topology messages get?",
        "Strings vs JSON for messages: what are the trade-offs?",
    ],
    "java_tip": """
*This tab names Python tools, which can hint at an approach.*

- Instance state lives on `self`: `self.something = {}` in `__init__`.
- `message.split("|", 2)` splits at most twice; `"|".join(parts)` builds a message.
- `set()` / `dict` for bookkeeping; `str(n)` and `int(s)` to move numbers through string messages.
- f-strings build messages: `f"{kind}|{value}"`.
""",
    "starter": '''class Node:
    def __init__(self, node_id: str, children: list[str], parent: str | None):
        self.node_id = node_id
        self.children = children
        self.parent = parent

    def sendAsyncMessage(self, node_id: str, message: str) -> None:
        """Provided by the cluster - the tests replace this. Don't implement it."""

    def receiveMessage(self, fromNodeId: str | None, message: str) -> None:
        pass
''',
    "solution": CLUSTER_SOLUTION,
    "tests": [
        T(1, RC + f"result = run_cluster(Node, {TREE_6}, triggers=['count'])", ["6"]),
        T(1, RC + "result = run_cluster(Node, {}, triggers=['count'])", ["1"], label="single machine"),
        T(1, RC + "result = run_cluster(Node, {'1': ['2'], '2': ['3']}, triggers=['count'], order='lifo')", ["3"],
          label="chain, LIFO delivery"),
        T(1, RC + f"result = run_cluster(Node, {TREE_7}, triggers=['count'], order='random', seed=1)", ["7"],
          label="random delivery order"),
        T(1, RC + f"result = run_cluster(Node, {TREE_6}, triggers=['count', 'count'], order='random', seed=4)",
          ["6", "6"], label="asked twice"),
        T(1, RC + "result = run_cluster(Node, {'1': [str(i) for i in range(2, 52)]}, triggers=['count'], order='random', seed=2)",
          ["51"], label="wide tree"),
        T(2, RC + "result = run_cluster(Node, {'1': ['2', '3']}, triggers=['topology'])", ["1(2,3)"]),
        T(2, RC + "result = run_cluster(Node, {'1': ['2'], '2': ['3']}, triggers=['topology'], order='lifo')", ["1(2(3))"]),
        T(2, RC + f"result = run_cluster(Node, {TREE_7}, triggers=['topology'], order='random', seed=3)",
          ["1(2(4,5),3(6,7))"], label="children keep their order"),
        T(2, RC + "result = run_cluster(Node, {}, triggers=['topology'])", ["1"]),
        T(2, RC + "result = run_cluster(Node, {'a': ['c', 'b'], 'b': ['z']}, root='a', triggers=['topology'], order='random', seed=5)",
          ["a(c,b(z))"], label="non-numeric ids"),
        T(2, RC + f"result = run_cluster(Node, {TREE_6}, triggers=['count', 'topology', 'count'], order='random', seed=6)",
          ["6", "1(2(4,5),3(6))", "6"], label="mixed jobs"),
        T(3, RC + f"result = run_cluster(Node, {TREE_6}, triggers=['count'], order='random', duplicate=0.5, seed=7)",
          ["6"]),
        T(3, RC + f"result = run_cluster(Node, {TREE_7}, triggers=['topology'], order='random', duplicate=0.5, seed=8)",
          ["1(2(4,5),3(6,7))"]),
        T(3, RC + f"result = run_cluster(Node, {TREE_7}, triggers=['count', 'count', 'topology'], order='lifo', duplicate=0.7, seed=9)",
          ["7", "7", "1(2(4,5),3(6,7))"], label="repeated jobs with duplicates"),
        T(3, RC + "result = run_cluster(Node, {'1': ['2'], '2': ['3'], '3': ['4']}, triggers=['count', 'topology'], order='random', duplicate=0.9, seed=10)",
          ["4", "1(2(3(4)))"], label="heavy duplication"),
    ],
}


# ================================================================= GPU credits
GPU_SOLUTION = '''import bisect
import heapq
import itertools


class GPUCredit:
    def __init__(self):
        self._events = []                 # sorted (timestamp, seq, kind, payload)
        self._seq = itertools.count()
        self._reset()

    # -- public API ------------------------------------------------------------
    def add_credit(self, credit_id: str, amount: int, timestamp: int, expiration: int) -> None:
        self._insert(timestamp, "add", (credit_id, amount, timestamp + expiration))

    def subtract(self, amount: int, timestamp: int) -> None:
        self._insert(timestamp, "sub", amount)

    def get_balance(self, timestamp: int) -> int | None:
        if timestamp < self._time:
            self._reset()                 # going back in time: replay from scratch
        self._advance(timestamp)
        self._expire(timestamp)
        balance = self._total - self._debt
        if self._max_end < timestamp or balance < 0:
            return None
        return balance

    # -- incremental replay ------------------------------------------------------
    def _reset(self):
        self._pos = 0                     # next event to apply
        self._time = float("-inf")        # everything at or before this time is applied
        self._heap = []                   # [expires_at, seq, remaining] of live grants
        self._total = 0                   # sum of remaining credit in the heap
        self._debt = 0
        self._max_end = float("-inf")

    def _insert(self, timestamp, kind, payload):
        if timestamp <= self._time:
            self._reset()                 # an event in the past invalidates the replay
        bisect.insort(self._events, (timestamp, next(self._seq), kind, payload))

    def _advance(self, until):
        while self._pos < len(self._events) and self._events[self._pos][0] <= until:
            t, seq, kind, payload = self._events[self._pos]
            self._pos += 1
            self._expire(t)
            if kind == "add":
                _credit_id, amount, expires_at = payload
                self._max_end = max(self._max_end, expires_at)
                paid = min(self._debt, amount)        # new credit pays off old debt first
                self._debt -= paid
                heapq.heappush(self._heap, [expires_at, seq, amount - paid])
                self._total += amount - paid
            else:
                self._burn(payload)
        self._time = max(self._time, until)

    def _expire(self, now):
        while self._heap and self._heap[0][0] < now:
            self._total -= heapq.heappop(self._heap)[2]

    def _burn(self, amount):
        while amount and self._heap:
            grant = self._heap[0]
            used = min(grant[2], amount)
            grant[2] -= used
            self._total -= used
            amount -= used
            if grant[2] == 0:
                heapq.heappop(self._heap)
        self._debt += amount
'''

GPU_PERF = """
    import time
    gpu = GPUCredit()
    out = []
    start = time.perf_counter()
    for i in range(4000):
        t = i * 10
        gpu.add_credit(f"g{i}", 5, t, 25)
        gpu.subtract(3, t + 5)
        out.append(gpu.get_balance(t + 5))
        if time.perf_counter() - start > 1.5:
            result = f"too slow: only {i + 1} of 4000 rounds finished in 1.5 s"
            break
    else:
        result = [out[0], out[1], out[2], out[-1], len(out)]
"""

GPU = {
    "id": "mp-gpu-credits",
    "title": "GPU Credit Ledger",
    "difficulty": "Medium",
    "category": "Multi-part",
    "tags": ["simulation", "heap", "out-of-order events"],
    "entry": "GPUCredit",
    "mode": "script",
    "target_minutes": 30,
    "description": """
Customers receive **GPU credit grants** that expire, and their usage burns credit.
Build the ledger:

```python
class GPUCredit:
    def add_credit(self, credit_id: str, amount: int, timestamp: int, expiration: int) -> None: ...
    def get_balance(self, timestamp: int) -> int | None: ...
```

- A grant is active from `timestamp` through `timestamp + expiration`, **inclusive** at
  both ends (`expiration` is a duration).
- Calls can arrive **in any order**: an event at time 30 may be recorded after an event
  at time 50. `get_balance(t)` must reflect every event with timestamp `<= t`,
  whenever it was recorded.
- There's at most one event (grant or usage) per timestamp.
""",
    "parts": [
        {
            "title": "Grants and balances",
            "description": """
`get_balance(t)` returns the total credit of the grants active at `t`, or **`None` if no
grant is active** at `t`.
""",
        },
        {
            "title": "Usage",
            "description": """
```python
def subtract(self, amount: int, timestamp: int) -> None: ...
```

- Usage at time `t` burns credit from the grants active at `t`, starting with the grant that
  **expires soonest**, and can span several grants.
- If the active grants can't cover it, the shortfall becomes **debt**, and the balance
  goes negative. Credit granted later pays off the debt first.
- `get_balance` returns **`None` if the balance is negative**. A balance of exactly 0 is
  `0`, not `None`. No active grant at `t` still means `None`.

```python
gpu.add_credit("a", 4, 20, 40)    # active 20-60
gpu.add_credit("b", 3, 30, 10)    # active 30-40, expires sooner
gpu.subtract(2, 30)               # burns from b first
gpu.get_balance(30)  # 5
gpu.get_balance(41)  # 4  (b has expired)
```
""",
        },
        {
            "title": "Scale",
            "description": """
Customers now record thousands of events and check their balance after every one.
All earlier behaviour (out-of-order calls included) must keep working, but the
workload below (**4,000 grants, 4,000 usages and 4,000 balance checks, recorded in time
order**) must finish within the test's **1.5 s** budget.
""",
        },
    ],
    "discussion": [
        "Which data structure did you use to find the soonest-expiring grant, and what does each operation cost?",
        "How would you support out-of-order events without replaying everything from the beginning?",
        "How would this ledger be enforced in production, e.g. rate limiting GPU jobs per customer tier?",
        "Credits now come from many services concurrently. How do you keep the ledger consistent?",
    ],
    "java_tip": """
*This tab names Python tools, which can hint at an approach.*

- `heapq` (min-heap on a list): `heappush`, `heappop`, peek with `heap[0]`. Tuples or lists compare element by element.
- `bisect.insort(lst, item)` keeps a list sorted; `bisect.bisect_right(lst, x)` finds a position.
- `None` for "no value", checked with `is None`. Return type hint: `-> int | None`.
- `sorted(events, key=lambda e: e[0])` sorts by timestamp.
""",
    "starter": '''class GPUCredit:
    def __init__(self):
        pass

    def add_credit(self, credit_id: str, amount: int, timestamp: int, expiration: int) -> None:
        pass

    def get_balance(self, timestamp: int) -> int | None:
        pass
''',
    "solution": GPU_SOLUTION,
    "tests": [
        T(1, """
            gpu = GPUCredit()
            gpu.add_credit("a", 10, 10, 20)
            result = [gpu.get_balance(9), gpu.get_balance(10), gpu.get_balance(30), gpu.get_balance(31)]
        """, [None, 10, 10, None], label="inclusive expiry"),
        T(1, """
            gpu = GPUCredit()
            gpu.add_credit("a", 5, 0, 10)
            gpu.add_credit("b", 7, 5, 10)
            result = [gpu.get_balance(t) for t in (0, 5, 10, 11, 15, 16)]
        """, [5, 12, 12, 7, 7, None]),
        T(1, """
            gpu = GPUCredit()
            gpu.add_credit("b", 7, 5, 10)
            gpu.add_credit("a", 5, 0, 10)
            result = [gpu.get_balance(t) for t in (0, 5, 11)]
        """, [5, 12, 7], label="out-of-order grants"),
        T(1, """
            gpu = GPUCredit()
            gpu.add_credit("a", 1, 0, 10)
            gpu.add_credit("b", 2, 20, 10)
            gpu.add_credit("z", 3, 50, 0)
            result = [gpu.get_balance(t) for t in (15, 20, 50, 51)]
        """, [None, 2, 3, None], label="gaps and zero-length grants"),
        T(1, """
            gpu = GPUCredit()
            first = gpu.get_balance(100)
            gpu.add_credit("a", 9, 50, 100)
            result = [first, gpu.get_balance(100), gpu.get_balance(40)]
        """, [None, 9, None], label="query, then an earlier grant"),
        T(2, """
            gpu = GPUCredit()
            gpu.add_credit("a", 4, 20, 40)
            gpu.add_credit("b", 3, 30, 10)
            gpu.subtract(2, 30)
            result = [gpu.get_balance(30), gpu.get_balance(40), gpu.get_balance(41)]
        """, [5, 5, 4], label="soonest-expiring first"),
        T(2, """
            gpu = GPUCredit()
            gpu.add_credit("c1", 20, 10, 30)
            gpu.add_credit("c2", 20, 40, 30)
            gpu.add_credit("c3", 20, 20, 30)
            gpu.add_credit("c4", 20, 30, 30)
            gpu.subtract(45, 30)
            result = [gpu.get_balance(30), gpu.get_balance(55)]
        """, [15, 35], label="spanning three grants"),
        T(2, """
            gpu = GPUCredit()
            gpu.subtract(4, 30)
            gpu.add_credit("a", 4, 20, 30)
            result = [gpu.get_balance(20), gpu.get_balance(30), gpu.get_balance(50)]
        """, [4, 0, 0], label="usage recorded before its grant; zero is not None"),
        T(2, """
            gpu = GPUCredit()
            gpu.add_credit("openai", 10, 10, 30)
            gpu.subtract(100, 20)
            before = [gpu.get_balance(10), gpu.get_balance(20), gpu.get_balance(30)]
            gpu.add_credit("top", 100, 25, 100)
            result = before + [gpu.get_balance(25), gpu.get_balance(41)]
        """, [10, None, None, 10, 10], label="debt and top-up"),
        T(2, """
            gpu = GPUCredit()
            gpu.add_credit("a", 10, 0, 100)
            gpu.add_credit("b", 10, 50, 10)
            gpu.subtract(5, 40)
            result = [gpu.get_balance(55), gpu.get_balance(70)]
        """, [15, 5], label="grants that haven't started aren't used"),
        T(2, """
            gpu = GPUCredit()
            gpu.add_credit("a", 10, 0, 10)
            gpu.add_credit("b", 10, 0, 100)
            gpu.subtract(5, 20)
            result = gpu.get_balance(20)
        """, 5, label="expired grants aren't used"),
        T(2, """
            gpu = GPUCredit()
            gpu.subtract(5, 1)
            gpu.add_credit("a", 10, 5, 10)
            result = [gpu.get_balance(1), gpu.get_balance(5), gpu.get_balance(16)]
        """, [None, 5, None], label="usage with no grants is debt"),
        T(2, """
            gpu = GPUCredit()
            gpu.add_credit("a", 10, 0, 100)
            gpu.subtract(3, 10)
            mid = gpu.get_balance(50)
            gpu.subtract(4, 20)
            result = [mid, gpu.get_balance(15), gpu.get_balance(50)]
        """, [7, 7, 3], label="late usage changes later balances only"),
        T(2, """
            gpu = GPUCredit()
            gpu.add_credit("a", 10, 0, 100)
            gpu.subtract(3, 30)
            first = gpu.get_balance(50)
            gpu.subtract(4, 20)              # recorded after a query that covers t=20
            gpu.add_credit("b", 1, 10, 100)
            result = [first, gpu.get_balance(50), gpu.get_balance(25), gpu.get_balance(15)]
        """, [7, 4, 7, 11], label="events recorded after a later query"),
        T(3, GPU_PERF, [2, 4, 6, 12, 4000], label="4,000 rounds of grant + usage + balance in 1.5 s"),
    ],
}


PROBLEMS = [CACHE, IP, BATTLE, DEDUP, CLUSTER, GPU]
