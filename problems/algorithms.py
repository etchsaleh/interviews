"""LeetCode-style fundamentals (plus a graph and a caching classic).

Each problem is a dict:
  id, title, difficulty, category, tags
  description  - markdown shown to the user
  java_tip     - markdown: what is different from Java for this problem
  entry        - function (or class) name the tests call
  mode         - "function" (default) or "class" for design problems
  starter      - code placed in the editor
  solution     - reference solution (also used by the test suite)
  tests        - list of {"args": [...], "expected": ...}
  compare      - "exact" (default), "unordered", "unordered_nested", "float"
  followups    - optional list of extra twists to try after the tests pass
"""

PROBLEMS = [
    {
        "id": "two-sum",
        "title": "Two Sum",
        "difficulty": "Easy",
        "category": "Fundamentals",
        "tags": ["dict", "hash map"],
        "entry": "two_sum",
        "followups": ['Return *all* index pairs that sum to target, without duplicates.', 'The input is sorted — can you do it in O(1) extra space?'],
        "description": """
Given a list of integers `nums` and an integer `target`, return the **indices** of the two
numbers that add up to `target`, as a list `[i, j]` with `i < j`.

Exactly one solution exists, and you may not use the same element twice.

```
two_sum([2, 7, 11, 15], 9)  ->  [0, 1]
two_sum([3, 2, 4], 6)       ->  [1, 2]
```
""",
        "java_tip": """
- `HashMap<Integer, Integer>` becomes a plain `dict`: `seen = {}`.
- `map.containsKey(x)` → `x in seen`; `map.get(x)` → `seen[x]` (raises `KeyError` if missing) or `seen.get(x)` (returns `None`).
- `for (int i = 0; i < nums.length; i++)` → `for i, num in enumerate(nums):`
""",
        "starter": """def two_sum(nums: list[int], target: int) -> list[int]:
    # Your code here
    pass
""",
        "solution": """def two_sum(nums: list[int], target: int) -> list[int]:
    seen = {}  # value -> index
    for i, num in enumerate(nums):
        if target - num in seen:
            return [seen[target - num], i]
        seen[num] = i
    return []
""",
        "tests": [
            {"args": [[2, 7, 11, 15], 9], "expected": [0, 1]},
            {"args": [[3, 2, 4], 6], "expected": [1, 2]},
            {"args": [[3, 3], 6], "expected": [0, 1]},
            {"args": [[-1, -2, -3, -4, -5], -8], "expected": [2, 4]},
            {"args": [[0, 4, 3, 0], 0], "expected": [0, 3]},
        ],
    },
    {
        "id": "valid-anagram",
        "title": "Valid Anagram",
        "difficulty": "Easy",
        "category": "Fundamentals",
        "tags": ["string", "Counter"],
        "entry": "is_anagram",
        "description": """
Return `True` if string `t` is an anagram of string `s` (same letters, same counts), else `False`.

```
is_anagram("anagram", "nagaram") -> True
is_anagram("rat", "car")         -> False
```
""",
        "java_tip": """
- Booleans are `True` / `False` (capitalised).
- `collections.Counter` counts things for you: `Counter("aab") == {'a': 2, 'b': 1}`. Two Counters compare with `==`.
- Strings are iterable directly: `for ch in s:` — no `toCharArray()` needed.
""",
        "starter": """def is_anagram(s: str, t: str) -> bool:
    pass
""",
        "solution": """from collections import Counter


def is_anagram(s: str, t: str) -> bool:
    return Counter(s) == Counter(t)
""",
        "tests": [
            {"args": ["anagram", "nagaram"], "expected": True},
            {"args": ["rat", "car"], "expected": False},
            {"args": ["", ""], "expected": True},
            {"args": ["a", "ab"], "expected": False},
            {"args": ["aacc", "ccac"], "expected": False},
        ],
    },
    {
        "id": "valid-palindrome",
        "title": "Valid Palindrome",
        "difficulty": "Easy",
        "category": "Fundamentals",
        "tags": ["string", "two pointers", "slicing"],
        "entry": "is_palindrome",
        "description": """
A phrase is a palindrome if, after lower-casing it and removing every non-alphanumeric
character, it reads the same forward and backward.

```
is_palindrome("A man, a plan, a canal: Panama") -> True
is_palindrome("race a car")                     -> False
```
""",
        "java_tip": """
- `Character.isLetterOrDigit(c)` → `c.isalnum()`; `toLowerCase()` → `.lower()`.
- Build strings with `"".join(...)` instead of `StringBuilder`.
- Reverse anything with slicing: `s[::-1]`.
- A *generator expression* like `"".join(c.lower() for c in s if c.isalnum())` replaces a whole loop.
""",
        "starter": """def is_palindrome(s: str) -> bool:
    pass
""",
        "solution": """def is_palindrome(s: str) -> bool:
    cleaned = "".join(c.lower() for c in s if c.isalnum())
    return cleaned == cleaned[::-1]
""",
        "tests": [
            {"args": ["A man, a plan, a canal: Panama"], "expected": True},
            {"args": ["race a car"], "expected": False},
            {"args": [" "], "expected": True},
            {"args": ["0P"], "expected": False},
            {"args": ["No 'x' in Nixon"], "expected": True},
        ],
    },
    {
        "id": "valid-parentheses",
        "title": "Valid Parentheses",
        "difficulty": "Easy",
        "category": "Fundamentals",
        "tags": ["stack"],
        "entry": "is_valid",
        "followups": ['Also allow `*` as a wildcard for any single bracket or nothing.', 'Return the index of the first invalid character instead of a bool.'],
        "description": """
Given a string containing only `()[]{}`, return `True` if every bracket is closed by the
same type of bracket in the correct order.

```
is_valid("()[]{}") -> True
is_valid("(]")     -> False
is_valid("([])")   -> True
```
""",
        "java_tip": """
- There is no `Stack` / `Deque` class needed: a `list` is a stack. `push` → `append`, `pop` → `pop()`, `peek` → `stack[-1]`.
- An empty list is *falsy*: `if not stack:` replaces `stack.isEmpty()`.
- Dict literals make a nice lookup table: `pairs = {")": "(", "]": "[", "}": "{"}`.
""",
        "starter": """def is_valid(s: str) -> bool:
    pass
""",
        "solution": """def is_valid(s: str) -> bool:
    pairs = {")": "(", "]": "[", "}": "{"}
    stack = []
    for ch in s:
        if ch in pairs:
            if not stack or stack.pop() != pairs[ch]:
                return False
        else:
            stack.append(ch)
    return not stack
""",
        "tests": [
            {"args": ["()"], "expected": True},
            {"args": ["()[]{}"], "expected": True},
            {"args": ["(]"], "expected": False},
            {"args": ["([)]"], "expected": False},
            {"args": ["{[]}"], "expected": True},
            {"args": ["("], "expected": False},
            {"args": [")"], "expected": False},
        ],
    },
    {
        "id": "binary-search",
        "title": "Binary Search",
        "difficulty": "Easy",
        "category": "Fundamentals",
        "tags": ["binary search"],
        "entry": "search",
        "description": """
Given a sorted list `nums` and a `target`, return the index of `target`, or `-1` if it is
not present. Your solution should run in O(log n).

```
search([-1, 0, 3, 5, 9, 12], 9) -> 4
search([-1, 0, 3, 5, 9, 12], 2) -> -1
```
""",
        "java_tip": """
- Integer division is `//`. A single `/` **always** returns a float in Python 3 (`7 / 2 == 3.5`).
- Python ints never overflow, so `(lo + hi) // 2` is safe — no `lo + (hi - lo) / 2` trick required.
- `while lo <= hi:` — no parentheses around conditions.
- The standard library has `bisect.bisect_left` if you want the one-liner afterwards.
""",
        "starter": """def search(nums: list[int], target: int) -> int:
    pass
""",
        "solution": """def search(nums: list[int], target: int) -> int:
    lo, hi = 0, len(nums) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if nums[mid] == target:
            return mid
        if nums[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1
""",
        "tests": [
            {"args": [[-1, 0, 3, 5, 9, 12], 9], "expected": 4},
            {"args": [[-1, 0, 3, 5, 9, 12], 2], "expected": -1},
            {"args": [[5], 5], "expected": 0},
            {"args": [[], 1], "expected": -1},
            {"args": [[1, 3, 5, 7, 9, 11, 13], 1], "expected": 0},
            {"args": [[1, 3, 5, 7, 9, 11, 13], 13], "expected": 6},
        ],
    },
    {
        "id": "max-subarray",
        "title": "Maximum Subarray",
        "difficulty": "Medium",
        "category": "Fundamentals",
        "tags": ["dynamic programming", "Kadane"],
        "entry": "max_sub_array",
        "description": """
Find the contiguous, non-empty subarray with the largest sum and return that sum.

```
max_sub_array([-2, 1, -3, 4, -1, 2, 1, -5, 4]) -> 6   # [4, -1, 2, 1]
max_sub_array([-3, -1, -2])                    -> -1
```
""",
        "java_tip": """
- `Integer.MIN_VALUE` → `float("-inf")` (or just start from `nums[0]`).
- `Math.max(a, b)` → built-in `max(a, b)` (also takes any number of args or an iterable).
- Tuple unpacking swaps / updates several variables at once: `a, b = b, a + b`.
""",
        "starter": """def max_sub_array(nums: list[int]) -> int:
    pass
""",
        "solution": """def max_sub_array(nums: list[int]) -> int:
    best = current = nums[0]
    for num in nums[1:]:
        current = max(num, current + num)
        best = max(best, current)
    return best
""",
        "tests": [
            {"args": [[-2, 1, -3, 4, -1, 2, 1, -5, 4]], "expected": 6},
            {"args": [[1]], "expected": 1},
            {"args": [[5, 4, -1, 7, 8]], "expected": 23},
            {"args": [[-3, -1, -2]], "expected": -1},
        ],
    },
    {
        "id": "group-anagrams",
        "title": "Group Anagrams",
        "difficulty": "Medium",
        "category": "Fundamentals",
        "tags": ["dict", "defaultdict", "sorting"],
        "entry": "group_anagrams",
        "description": """
Group the words that are anagrams of each other. Return a list of groups; the order of
the groups and of the words inside each group does not matter.

```
group_anagrams(["eat", "tea", "tan", "ate", "nat", "bat"])
  -> [["eat", "tea", "ate"], ["tan", "nat"], ["bat"]]
```
""",
        "java_tip": """
- `map.computeIfAbsent(k, x -> new ArrayList<>()).add(v)` → `groups = defaultdict(list)` then `groups[k].append(v)`.
- Lists can't be dict keys (they're mutable) but **tuples** can: `key = tuple(sorted(word))`. Or `"".join(sorted(word))`.
- `sorted(...)` returns a new list; `list.sort()` sorts in place and returns `None` (a classic bug!).
- `list(groups.values())` converts the dict view into a list.
""",
        "starter": """def group_anagrams(words: list[str]) -> list[list[str]]:
    pass
""",
        "solution": """from collections import defaultdict


def group_anagrams(words: list[str]) -> list[list[str]]:
    groups = defaultdict(list)
    for word in words:
        groups["".join(sorted(word))].append(word)
    return list(groups.values())
""",
        "compare": "unordered_nested",
        "tests": [
            {"args": [["eat", "tea", "tan", "ate", "nat", "bat"]],
             "expected": [["bat"], ["nat", "tan"], ["ate", "eat", "tea"]]},
            {"args": [[""]], "expected": [[""]]},
            {"args": [["a"]], "expected": [["a"]]},
            {"args": [["abc", "bca", "xyz", "zyx", "q"]], "expected": [["abc", "bca"], ["xyz", "zyx"], ["q"]]},
        ],
    },
    {
        "id": "top-k-frequent",
        "title": "Top K Frequent Elements",
        "difficulty": "Medium",
        "category": "Fundamentals",
        "tags": ["Counter", "heap"],
        "entry": "top_k_frequent",
        "followups": ['Break frequency ties by smallest value and return them in order.', 'Numbers arrive as a stream: support `add(x)` and `top(k)`.'],
        "description": """
Return the `k` most frequent elements of `nums`. Any order is accepted; the answer is
guaranteed to be unique.

```
top_k_frequent([1, 1, 1, 2, 2, 3], 2) -> [1, 2]
```
""",
        "java_tip": """
- `Counter(nums).most_common(k)` returns `[(value, count), ...]` — check out what's in `collections`!
- A list comprehension builds a list in one line: `[value for value, count in pairs]`.
- `PriorityQueue` → the `heapq` module operating on a plain list (`heapq.heappush`, `heapq.heappop`, `heapq.nlargest`). It's a **min**-heap.
""",
        "starter": """def top_k_frequent(nums: list[int], k: int) -> list[int]:
    pass
""",
        "solution": """from collections import Counter


def top_k_frequent(nums: list[int], k: int) -> list[int]:
    return [value for value, _count in Counter(nums).most_common(k)]
""",
        "compare": "unordered",
        "tests": [
            {"args": [[1, 1, 1, 2, 2, 3], 2], "expected": [1, 2]},
            {"args": [[1], 1], "expected": [1]},
            {"args": [[4, 4, 5, 5, 5, 6, 7, 7, 7, 7], 3], "expected": [7, 5, 4]},
        ],
    },
    {
        "id": "product-except-self",
        "title": "Product of Array Except Self",
        "difficulty": "Medium",
        "category": "Fundamentals",
        "tags": ["prefix sums"],
        "entry": "product_except_self",
        "description": """
Return a list `answer` where `answer[i]` is the product of every element of `nums`
except `nums[i]`. Do it in O(n) **without using division**.

```
product_except_self([1, 2, 3, 4]) -> [24, 12, 8, 6]
```
""",
        "java_tip": """
- `new int[n]` filled with 1s → `[1] * n`.
- Iterate backwards with `range(n - 1, -1, -1)` or `reversed(range(n))`.
- **Careful:** `[[0] * 3] * 3` creates three references to the *same* inner list. Use `[[0] * 3 for _ in range(3)]` for 2D arrays.
""",
        "starter": """def product_except_self(nums: list[int]) -> list[int]:
    pass
""",
        "solution": """def product_except_self(nums: list[int]) -> list[int]:
    n = len(nums)
    answer = [1] * n
    prefix = 1
    for i in range(n):
        answer[i] = prefix
        prefix *= nums[i]
    suffix = 1
    for i in reversed(range(n)):
        answer[i] *= suffix
        suffix *= nums[i]
    return answer
""",
        "tests": [
            {"args": [[1, 2, 3, 4]], "expected": [24, 12, 8, 6]},
            {"args": [[-1, 1, 0, -3, 3]], "expected": [0, 0, 9, 0, 0]},
            {"args": [[2, 3]], "expected": [3, 2]},
        ],
    },
    {
        "id": "longest-substring",
        "title": "Longest Substring Without Repeating Characters",
        "difficulty": "Medium",
        "category": "Fundamentals",
        "tags": ["sliding window", "set"],
        "entry": "length_of_longest_substring",
        "description": """
Return the length of the longest substring of `s` that contains no repeated characters.

```
length_of_longest_substring("abcabcbb") -> 3   # "abc"
length_of_longest_substring("bbbbb")    -> 1
length_of_longest_substring("pwwkew")   -> 3   # "wke"
```
""",
        "java_tip": """
- `HashSet<Character>` → `set()`; `add` / `remove` / `in` work like you'd expect. A set literal is `{1, 2}` but an empty one must be `set()` (`{}` is an empty dict).
- `s.charAt(i)` → `s[i]`. Negative indexes count from the end: `s[-1]` is the last char.
""",
        "starter": """def length_of_longest_substring(s: str) -> int:
    pass
""",
        "solution": """def length_of_longest_substring(s: str) -> int:
    last_seen = {}
    start = best = 0
    for i, ch in enumerate(s):
        if last_seen.get(ch, -1) >= start:
            start = last_seen[ch] + 1
        last_seen[ch] = i
        best = max(best, i - start + 1)
    return best
""",
        "tests": [
            {"args": ["abcabcbb"], "expected": 3},
            {"args": ["bbbbb"], "expected": 1},
            {"args": ["pwwkew"], "expected": 3},
            {"args": [""], "expected": 0},
            {"args": ["dvdf"], "expected": 3},
            {"args": ["abba"], "expected": 2},
        ],
    },
    {
        "id": "merge-intervals",
        "title": "Merge Intervals",
        "difficulty": "Medium",
        "category": "Fundamentals",
        "tags": ["sorting", "lambda"],
        "entry": "merge",
        "followups": ['Insert one new interval into an already-merged list.', 'Return the total length covered instead of the intervals.'],
        "description": """
Given a list of intervals `[start, end]`, merge all overlapping intervals and return the
result sorted by start.

```
merge([[1, 3], [2, 6], [8, 10], [15, 18]]) -> [[1, 6], [8, 10], [15, 18]]
merge([[1, 4], [4, 5]])                    -> [[1, 5]]
```
""",
        "java_tip": """
- `Arrays.sort(arr, (a, b) -> a[0] - b[0])` → `intervals.sort(key=lambda iv: iv[0])`. Python sorts by a *key function*, not a comparator.
- Lists sort lexicographically by default, so `sorted(intervals)` already orders by start then end.
- Unpack inside the loop: `for start, end in intervals:`.
""",
        "starter": """def merge(intervals: list[list[int]]) -> list[list[int]]:
    pass
""",
        "solution": """def merge(intervals: list[list[int]]) -> list[list[int]]:
    merged = []
    for start, end in sorted(intervals, key=lambda iv: iv[0]):
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged
""",
        "tests": [
            {"args": [[[1, 3], [2, 6], [8, 10], [15, 18]]], "expected": [[1, 6], [8, 10], [15, 18]]},
            {"args": [[[1, 4], [4, 5]]], "expected": [[1, 5]]},
            {"args": [[[4, 7], [1, 4]]], "expected": [[1, 7]]},
            {"args": [[[1, 4], [2, 3]]], "expected": [[1, 4]]},
            {"args": [[[5, 6]]], "expected": [[5, 6]]},
        ],
    },
    {
        "id": "climbing-stairs",
        "title": "Climbing Stairs",
        "difficulty": "Easy",
        "category": "Fundamentals",
        "tags": ["dynamic programming", "memoization"],
        "entry": "climb_stairs",
        "description": """
You can climb 1 or 2 steps at a time. In how many distinct ways can you reach the top of a
staircase with `n` steps?

```
climb_stairs(2) -> 2   # 1+1, 2
climb_stairs(3) -> 3   # 1+1+1, 1+2, 2+1
```
""",
        "java_tip": """
- Memoization without a `HashMap`: decorate a recursive function with `@functools.cache` (or `@lru_cache(maxsize=None)`).
- Functions can be defined inside functions — handy for recursive helpers that close over local variables.
- Python's default recursion limit is ~1000, so a memoised recursive solution crashes for n = 1,000 (`RecursionError`). Use a loop for big inputs.
""",
        "starter": """def climb_stairs(n: int) -> int:
    pass
""",
        "solution": """def climb_stairs(n: int) -> int:
    a, b = 1, 2  # ways to reach steps 1 and 2
    for _ in range(n - 1):
        a, b = b, a + b
    return a
""",
        "tests": [
            {"args": [1], "expected": 1},
            {"args": [2], "expected": 2},
            {"args": [3], "expected": 3},
            {"args": [5], "expected": 8},
            {"args": [45], "expected": 1836311903},
        ],
    },
    {
        "id": "number-of-islands",
        "title": "Number of Islands",
        "difficulty": "Medium",
        "category": "Graphs",
        "tags": ["BFS", "grid", "deque"],
        "entry": "num_islands",
        "followups": ['Return the size of the largest island.', 'Cells turn to land one by one — report the island count after each (union-find).'],
        "description": """
Given a 2D grid of `"1"` (land) and `"0"` (water), count the islands. An island is land
connected horizontally or vertically.

```
num_islands([
  ["1","1","0","0","0"],
  ["1","1","0","0","0"],
  ["0","0","1","0","0"],
  ["0","0","0","1","1"],
]) -> 3
```
""",
        "java_tip": """
- `Queue<int[]> q = new LinkedList<>()` → `q = deque()` from `collections`; `offer` → `append`, `poll` → `popleft()`. (Don't use `list.pop(0)` — it's O(n).)
- Tuples make great coordinates and set members: `seen.add((r, c))`.
- Chained comparisons work: `0 <= r < rows`.
""",
        "starter": """def num_islands(grid: list[list[str]]) -> int:
    pass
""",
        "solution": """from collections import deque


def num_islands(grid: list[list[str]]) -> int:
    if not grid:
        return 0
    rows, cols = len(grid), len(grid[0])
    seen = set()
    islands = 0
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] != "1" or (r, c) in seen:
                continue
            islands += 1
            queue = deque([(r, c)])
            seen.add((r, c))
            while queue:
                cr, cc = queue.popleft()
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = cr + dr, cc + dc
                    if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == "1" and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        queue.append((nr, nc))
    return islands
""",
        "tests": [
            {"args": [[["1", "1", "1", "1", "0"], ["1", "1", "0", "1", "0"],
                       ["1", "1", "0", "0", "0"], ["0", "0", "0", "0", "0"]]], "expected": 1},
            {"args": [[["1", "1", "0", "0", "0"], ["1", "1", "0", "0", "0"],
                       ["0", "0", "1", "0", "0"], ["0", "0", "0", "1", "1"]]], "expected": 3},
            {"args": [[["0"]]], "expected": 0},
            {"args": [[["1", "0", "1"], ["0", "1", "0"], ["1", "0", "1"]]], "expected": 5},
        ],
    },
    {
        "id": "lru-cache",
        "title": "LRU Cache",
        "difficulty": "Medium",
        "category": "Caching",
        "tags": ["class design", "OrderedDict"],
        "entry": "LRUCache",
        "followups": ['Implement it without `OrderedDict` (dict + doubly linked list).', 'Add per-key TTL — see *LRU Cache with Expiry*.'],
        "mode": "class",
        "description": """
Design a Least-Recently-Used cache with a fixed `capacity`:

- `get(key)` returns the value, or `-1` if absent. Reading a key marks it as recently used.
- `put(key, value)` inserts/updates. If this exceeds capacity, evict the least recently used key.

Both operations should be O(1).

Tests are LeetCode-style: a list of operations and their arguments, e.g.
`["LRUCache", "put", "put", "get"]` with `[[2], [1, 1], [2, 2], [1]]` →
expected outputs `[None, None, None, 1]` (`None` for the constructor and for `put`).
""",
        "java_tip": """
- Constructor is `def __init__(self, capacity):` and every method takes `self` explicitly as its first parameter.
- Fields are created by assigning `self.capacity = capacity` — no declarations.
- `LinkedHashMap` with access order → `collections.OrderedDict` with `move_to_end(key)` and `popitem(last=False)`.
- No `private`: a leading underscore (`self._data`) is the convention for "internal".
""",
        "starter": """class LRUCache:
    def __init__(self, capacity: int):
        pass

    def get(self, key: int) -> int:
        pass

    def put(self, key: int, value: int) -> None:
        pass
""",
        "solution": """from collections import OrderedDict


class LRUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self._data = OrderedDict()

    def get(self, key: int) -> int:
        if key not in self._data:
            return -1
        self._data.move_to_end(key)
        return self._data[key]

    def put(self, key: int, value: int) -> None:
        self._data[key] = value
        self._data.move_to_end(key)
        if len(self._data) > self.capacity:
            self._data.popitem(last=False)
""",
        "tests": [
            {"args": [["LRUCache", "put", "put", "get", "put", "get", "put", "get", "get", "get"],
                      [[2], [1, 1], [2, 2], [1], [3, 3], [2], [4, 4], [1], [3], [4]]],
             "expected": [None, None, None, 1, None, -1, None, -1, 3, 4]},
            {"args": [["LRUCache", "put", "put", "put", "get", "get"],
                      [[1], [1, 1], [1, 10], [2, 2], [1], [2]]],
             "expected": [None, None, None, None, -1, 2]},
            {"args": [["LRUCache", "get", "put", "get"], [[1], [5], [5, 50], [5]]],
             "expected": [None, -1, None, 50]},
        ],
    },
]
