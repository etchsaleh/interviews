"""Extra edge-case and performance tests, merged into the problems by problems/__init__.py.

Performance tests use `gen`: a snippet run inside the sandbox that builds `args` (and
`expected`, when the answer is easier to construct than to write out). Expected answers
come from how the input is built, never from running a reference solution. Each
performance test has a `time_limit_ms`; the harness stops a test that runs over.
"""
import textwrap


def E(args, expected, label=None):
    """An edge-case test."""
    test = {"args": args, "expected": expected}
    if label:
        test["label"] = label
    return test


def P(gen, label, limit_ms=1000, expected=None):
    """A performance test with a generated input."""
    test = {"gen": textwrap.dedent(gen).strip(), "label": label, "time_limit_ms": limit_ms}
    if expected is not None:
        test["expected"] = expected
    return test


def _fib_ways(n):
    a, b = 1, 2
    for _ in range(n - 1):
        a, b = b, a + b
    return a


EXTRA_TESTS = {
    # ------------------------------------------------------------ fundamentals
    "two-sum": [
        E([[5, 1000000000, -999999995], 5], [1, 2], "large values"),
        E([[1, 2], 3], [0, 1], "minimum length"),
        P("""
            n = 100_000
            args = [list(range(n)), 2 * n - 3]
            expected = [n - 2, n - 1]
        """, "n = 100,000: needs O(n), not nested loops"),
    ],
    "valid-anagram": [
        E(["ab", "a"], False, "different lengths"),
        E(["café", "éfac"], True, "unicode"),
        E(["a", "A"], False, "case matters"),
        P("""
            args = ["ab" * 50_000, "ba" * 50_000]
            expected = True
        """, "100,000 characters: O(n), not .count() per character"),
        P("""
            args = ["a" * 99_999 + "b", "a" * 100_000]
            expected = False
        """, "100,000 characters, one difference"),
    ],
    "valid-palindrome": [
        E([""], True, "empty string"),
        E([".,"], True, "only punctuation"),
        E(["ab_a"], True, "underscore isn't alphanumeric"),
        E(["Was it a car or a cat I saw?"], True),
        E(["0P0"], True, "digits count"),
        P("""
            args = ["a" * 100_000 + "b" + "a" * 100_000]
            expected = True
        """, "200,001 characters"),
        P("""
            args = ["a" * 100_000 + "bc" + "a" * 100_000]
            expected = False
        """, "200,002 characters, not a palindrome"),
    ],
    "valid-parentheses": [
        E([""], True, "empty string"),
        E(["(("], False, "only openers"),
        E(["]"], False, "starts with a closer"),
        E(["([{}])"], True, "nested"),
        E(["){"], False),
        P("""
            args = ["(" * 50_000 + ")" * 50_000]
            expected = True
        """, "100,000 characters: O(n), not repeated replace()"),
        P("""
            args = ["([{" * 30_000 + "}])" * 30_000]
            expected = True
        """, "180,000 characters, mixed brackets"),
    ],
    "binary-search": [
        E([[2, 5], 5], 1, "last element"),
        E([[2, 5], 1], -1, "smaller than everything"),
        E([[2, 5], 9], -1, "larger than everything"),
        E([[-10, -5, 0, 3], -10], 0, "negative numbers"),
        P("""
            from practice_helpers import ProbedList
            args = [ProbedList(range(0, 2_000_000, 2), max_reads=64), 1_234_568]
            expected = 617_284
        """, "1,000,000 elements, at most 64 reads (O(log n))"),
        P("""
            from practice_helpers import ProbedList
            args = [ProbedList(range(0, 2_000_000, 2), max_reads=64), 777_777]
            expected = -1
        """, "1,000,000 elements, missing target, at most 64 reads"),
    ],
    "max-subarray": [
        E([[0]], 0),
        E([[-1, 0, -2]], 0, "zero beats negatives"),
        E([[2, -1, 2]], 3, "crossing a negative"),
        E([[-2, -3, 4, -1, -2, 1, 5, -3]], 7),
        P("""
            args = [[3, -1] * 50_000]
            expected = 100_001
        """, "n = 100,000: O(n), not all subarrays"),
    ],
    "group-anagrams": [
        E([["a", "a"]], [["a", "a"]], "duplicates"),
        E([["", ""]], [["", ""]], "empty strings"),
        E([["Ab", "bA", "ab"]], [["Ab", "bA"], ["ab"]], "case matters"),
        P("""
            words, expected = [], []
            for i in range(10_000):
                w = "a" * (i % 100 + 1) + "b" * (i // 100 + 1)
                words += [w, w[::-1]]
                expected.append([w, w[::-1]])
            args = [words]
        """, "20,000 words: group by key, don't compare pairs", limit_ms=2000),
    ],
    "top-k-frequent": [
        E([[-1, -1, 2], 1], [-1], "negative numbers"),
        E([[1, 2, 3, 1, 2, 1], 3], [1, 2, 3], "k = number of distinct values"),
        E([[5, 5, 5, 5], 1], [5]),
        P("""
            import random
            nums = [i for i in range(1000) for _ in range(i + 1)]
            random.Random(7).shuffle(nums)
            args = [nums, 3]
            expected = [999, 998, 997]
        """, "500,500 numbers: count once, not .count() per value", limit_ms=1500),
    ],
    "product-except-self": [
        E([[0, 0]], [0, 0], "two zeros"),
        E([[0, 4, 5]], [20, 0, 0], "one zero"),
        E([[-1, -2, -3]], [6, 3, 2], "negatives"),
        P("""
            n = 100_000
            nums = [1] * n
            nums[n // 2] = 2
            expected = [2] * n
            expected[n // 2] = 1
            args = [nums]
        """, "n = 100,000: O(n)"),
    ],
    "longest-substring": [
        E([" "], 1, "a space is a character"),
        E(["au"], 2),
        E(["tmmzuxt"], 5, "repeat before the window"),
        E(["abcdefg"], 7, "no repeats"),
        P("""
            alphabet = "".join(chr(0x4E00 + i) for i in range(1000))
            args = [alphabet * 100]
            expected = 1000
        """, "100,000 characters, answer 1,000: sliding window, not every start"),
    ],
    "merge-intervals": [
        E([[[1, 4], [0, 0]]], [[0, 0], [1, 4]], "unsorted input"),
        E([[[2, 3], [4, 5], [6, 7], [8, 9], [1, 10]]], [[1, 10]], "one interval covers all"),
        E([[[1, 4], [0, 4]]], [[0, 4]], "same end"),
        E([[[1, 4], [5, 6]]], [[1, 4], [5, 6]], "adjacent but not touching"),
        P("""
            import random
            n = 100_000
            intervals = [[2 * i, 2 * i + 1] for i in range(n)]
            expected = [list(iv) for iv in intervals]
            random.Random(3).shuffle(intervals)
            args = [intervals]
        """, "100,000 disjoint intervals, shuffled: O(n log n)", limit_ms=1500),
        P("""
            n = 100_000
            args = [[[0, i + 1] for i in range(n)]]
            expected = [[0, n]]
        """, "100,000 overlapping intervals", limit_ms=1500),
    ],
    "climbing-stairs": [
        E([4], 5),
        E([10], 89),
        E([1000], _fib_ways(1000), "n = 1,000: deep recursion fails, use a loop"),
    ],
    # ----------------------------------------------------------------- graphs
    "number-of-islands": [
        E([[]], 0, "empty grid"),
        E([[["1"]]], 1, "single cell"),
        E([[["1", "1", "1"]]], 1, "one row"),
        E([[["1"], ["0"], ["1"]]], 2, "one column"),
        P("""
            args = [[["1"] * 300 for _ in range(300)]]
            expected = 1
        """, "300×300 all land: recursion depth 90,000, so iterate", limit_ms=2000),
        P("""
            args = [[["1" if (r + c) % 2 == 0 else "0" for c in range(200)] for r in range(200)]]
            expected = 20_000
        """, "200×200 checkerboard: 20,000 islands", limit_ms=2000),
    ],
    "build-order": [
        E([["a"], []], ["a"], "single task"),
        E([["d", "c", "b", "a"], [["a", "b"], ["a", "c"], ["b", "d"], ["c", "d"]]], ["a", "b", "c", "d"], "diamond"),
        E([["a", "b"], [["a", "a"]]], [], "self-dependency is a cycle"),
        P("""
            import random
            names = [f"t{i:05d}" for i in range(20_000)]
            deps = [[names[i], names[i + 1]] for i in range(len(names) - 1)]
            tasks = names[:]
            random.Random(5).shuffle(tasks)
            args = [tasks, deps]
            expected = names
        """, "chain of 20,000 tasks", limit_ms=1500),
        P("""
            import random
            names = [f"t{i:05d}" for i in range(30_000)]
            tasks = names[:]
            random.Random(6).shuffle(tasks)
            args = [tasks, []]
            expected = names
        """, "30,000 tasks ready at once: a heap, not min() or sort() every step", limit_ms=1500),
    ],
    "fewest-hops": [
        E([[["a", "b"]], [], "a", "z"], -1, "target not in the network"),
        E([[["a", "b"]], [], "x", "x"], 0, "start == target, not in the network"),
        E([[["a", "b"], ["b", "a"]], [], "a", "b"], 1, "duplicate links"),
        P("""
            n = 100_000
            args = [[[f"n{i}", f"n{i + 1}"] for i in range(n - 1)], [], "n0", f"n{n - 1}"]
            expected = n - 1
        """, "path of 100,000 services: BFS, not recursion", limit_ms=1500),
    ],
    "broadcast-time": [
        E([3, [[1, 2, 1], [1, 2, 5], [2, 3, 1]], 1], 2, "duplicate links: the fastest counts"),
        E([2, [[1, 1, 5], [1, 2, 3]], 1], 3, "self-loop"),
        E([3, [[1, 2, 1]], 1], -1, "unreachable server"),
        P("""
            n = 20_000
            links = [[i, i + 1, 1] for i in range(n - 1, 0, -1)] + [[1, i, 2 * i] for i in range(3, n + 1)]
            args = [n, links, 1]
            expected = n - 1
        """, "20,000 servers, 40,000 links: Dijkstra, not Bellman-Ford", limit_ms=1500),
    ],
    "team-groups": [
        E([3, [[0, 1], [1, 2], [0, 2]]], [1, 3], "triangle"),
        E([2, [[0, 0], [1, 1]]], [2, 1], "self-pairs"),
        E([5, []], [5, 1], "no pairs"),
        P("""
            n = 100_000
            args = [n, [[i, i + 1] for i in range(n - 1)]]
            expected = [1, n]
        """, "chain of 100,000: needs path compression (or iteration)", limit_ms=1500),
    ],
    # ----------------------------------------------------------------- queues
    "moving-average": [
        E([["MovingAverage", "next", "next"], [[2], [1.5], [2.5]]], [None, 1.5, 2.0], "floats"),
        E([["MovingAverage", "next", "next"], [[5], [10], [20]]], [None, 10.0, 15.0], "fewer values than size"),
        P("""
            n, size = 100_000, 10_000
            args = [["MovingAverage"] + ["next"] * n, [[size]] + [[5]] * n]
            expected = [None] + [5.0] * n
        """, "100,000 values, window 10,000: O(1) per value, not sum()", limit_ms=1500),
    ],
    "rate-limiter": [
        E([["RateLimiter", "allow", "allow", "allow", "allow", "allow", "allow"],
           [[2, 1], [0], [0], [0], [1], [1], [1]]], [None, True, True, False, True, True, False], "bursts at one timestamp"),
        P("""
            n = 200_000
            args = [["RateLimiter"] + ["allow"] * n, [[60_000, 50_000]] + [[t] for t in range(n)]]
            expected = [None] + [True] * n
        """, "200,000 requests: deque.popleft(), not list.pop(0)", limit_ms=1500),
    ],
    "round-robin": [
        E([[["A", 1], ["B", 1]], 5], [["A", 1], ["B", 2]], "quantum bigger than every job"),
        E([[["A", 4]], 1], [["A", 4]], "one job, many slices"),
        P("""
            jobs = [[f"j{i}", 30] for i in range(3000)]
            args = [jobs, 1]
            expected = [[f"j{i}", 3000 * 29 + i + 1] for i in range(3000)]
        """, "3,000 jobs × 30 slices", limit_ms=2000),
    ],
    "ticket-queue": [
        E([["TicketQueue", "add", "add", "next", "next"], [[], ["a", -5], ["b", -1], [], []]],
          [None, None, None, "b", "a"], "negative priorities"),
        P("""
            n = 50_000
            ops = ["TicketQueue"] + ["add"] * n + ["next"] * n
            arguments = [[]] + [[f"t{i}", i % 10] for i in range(n)] + [[] for _ in range(n)]
            order = [f"t{i}" for p in range(9, -1, -1) for i in range(n) if i % 10 == p]
            args = [ops, arguments]
            expected = [None] * (n + 1) + order
        """, "50,000 tickets: a heap, not max() per call", limit_ms=1500),
    ],
    # ---------------------------------------------------------------- caching
    "lru-cache": [
        E([["LRUCache", "put", "put", "get", "get"], [[1], [1, 1], [2, 2], [1], [2]]],
          [None, None, None, -1, 2], "capacity 1"),
        E([["LRUCache", "put", "put", "put", "put", "get", "get"], [[2], [1, 1], [2, 2], [1, 10], [3, 3], [1], [2]]],
          [None, None, None, None, None, 10, -1], "updating a key refreshes it"),
        E([["LRUCache", "get"], [[2], [5]]], [None, -1], "get on an empty cache"),
        P("""
            cap, n = 20_000, 100_000
            keys = [(i * 7919) % cap for i in range(n)]
            ops = ["LRUCache"] + ["put"] * cap + ["get"] * n + ["put", "get"]
            arguments = [[cap]] + [[k, k * 2] for k in range(cap)] + [[k] for k in keys] + [[cap, 1], [-1]]
            expected = [None] * (cap + 1) + [k * 2 for k in keys] + [None, -1]
            args = [ops, arguments]
        """, "100,000 gets on a full cache of 20,000: O(1) per operation, not list.remove()", limit_ms=1500),
    ],
    "cache-hit-rate": [
        E([[1, 1, 1], 1], [2, 1], "same key"),
        E([[1, 2, 1, 2], 1], [0, 4], "capacity 1 thrashing"),
        E([[1, 2, 3, 4], 4], [0, 4], "all distinct"),
        P("""
            args = [list(range(10_000)) * 20, 10_000]
            expected = [190_000, 10_000]
        """, "200,000 requests, capacity 10,000: O(1) per request", limit_ms=1500),
    ],
    "ttl-cache": [
        E([["TTLCache", "put", "get"], [[2], ["a", 1, 0, 5], ["a", 5]]], [None, None, -1], "ttl 0 expires immediately"),
        E([["TTLCache", "put", "put", "get"], [[2], ["a", 1, 5, 0], ["a", 2, 10, 3], ["a", 10]]],
          [None, None, None, 2], "put refreshes the expiry"),
    ],
    # -------------------------------------------------------------------- OOP
    "bank-accounts": [
        E([["Bank", "open", "withdraw", "balance"], [[], ["a", 10], ["a", 10], ["a"]]], [None, True, 0, 0],
          "withdraw everything"),
        E([["Bank", "open", "transfer", "transfer", "deposit"], [[], ["a", 10], ["ghost", "a", 5], ["a", "a", 0], ["ghost", 5]]],
          [None, True, False, False, -1], "unknown source, zero amount, unknown account"),
    ],
    "leaderboard": [
        E([["Leaderboard", "add_score", "add_score", "top"], [[], ["a", -5], ["b", 3], [2]]],
          [None, None, None, ["b", "a"]], "negative points"),
        E([["Leaderboard", "add_score", "top"], [[], ["a", 1], [0]]], [None, None, []], "k = 0"),
        E([["Leaderboard", "add_score", "add_score", "add_score", "top"], [[], ["c", 5], ["a", 5], ["b", 5], [3]]],
          [None, None, None, None, ["a", "b", "c"]], "all tied"),
    ],
    # ------------------------------------------------------------------ APIs
    "api-user-email": [
        E([0], None, "id 0 doesn't exist"),
        E([6], "barbara@example.com", "last user"),
    ],
    "api-team-filter": [
        E(["Platform"], [], "team names are case-sensitive"),
    ],
    "api-auth-profile": [
        E(["nobody", "x"], None, "unknown user"),
        E(["ada", ""], None, "empty password"),
    ],
    "api-retry": [
        E(["k"], 7, "short key"),
    ],
    "api-create-todo": [
        {"args": ["Café ☕ — permit #42"], "expected_label": "id of a todo with that exact unicode title",
         "label": "unicode title"},
    ],
}


# ------------------------------------------------- multi-part / applied / product
from problems.multipart import T  # noqa: E402  (script-mode tests: part, snippet, expected)

EXTRA_TESTS.update({
    "mp-ip-iterator": [
        T(3, """
            import time
            start = time.perf_counter()
            count = sum(1 for _ in IPV4Iterator("10.0.0.0/14"))
            result = count
        """, 262_144, label="262,144 addresses in a /14", time_limit_ms=3000),
        T(5, 'result = [range_to_cidrs("0.0.0.0", "0.0.0.0"), range_to_cidrs("10.0.0.0", "10.0.0.7")]',
          [["0.0.0.0/32"], ["10.0.0.0/29"]], label="single address / exact block"),
        T(5, 'result = range_to_cidrs("10.0.0.255", "10.0.1.1")', ["10.0.0.255/32", "10.0.1.0/31"],
          label="crossing an octet boundary"),
    ],
    "mp-monster-battle": [
        T(1, """
            result = battle(Team("A", [Monster("Giant", 10, 100)]), Team("B", [Monster("Ant", 1, 1)]))
        """, ["Battle begins: A vs B", "Giant attacks Ant for 100 damage. Ant is eliminated!", "Battle ends: A wins!"],
          label="one hit"),
        T(3, """
            a = Team("A", [Monster("Ember", 30, 12, MonsterType.FIRE), Monster("Spark", 30, 10, MonsterType.ELECTRIC)])
            b = Team("B", [Monster("Moss", 15, 1, MonsterType.GRASS), Monster("Puddle", 15, 1, MonsterType.WATER)])
            log = battle(a, b, smart_targeting=True)
            result = [log[1], log[3], log[-1]]
        """, ["Ember attacks Moss for 24 damage (Super effective!). Moss is eliminated!",
              "Spark attacks Puddle for 20 damage (Super effective!). Puddle is eliminated!",
              "Battle ends: A wins!"], label="best attacker changes with the defender"),
    ],
    "mp-gpu-credits": [
        T(2, """
            gpu = GPUCredit()
            gpu.add_credit("a", 5, 0, 10)
            gpu.add_credit("b", 5, 1, 9)
            gpu.subtract(10, 5)
            result = [gpu.get_balance(5), gpu.get_balance(10), gpu.get_balance(11)]
        """, [0, 0, None], label="usage exactly drains two grants with the same expiry"),
    ],
    "mp-file-dedup": [
        T(1, """
            from practice_helpers import make_tree, rel_groups
            make_tree(tmpdir, {"a b.txt": "x", "ünï.txt": "x", "c/d.txt": "yy", "c/e.txt": "yy", "f": "zzz", "g": "zzz"})
            result = rel_groups(find_duplicate_files(tmpdir), tmpdir)
        """, [["a b.txt", "ünï.txt"], ["c/d.txt", "c/e.txt"], ["f", "g"]], label="spaces, unicode, several groups"),
    ],
    "mp-cluster-messages": [
        T(1, """
            from practice_helpers import run_cluster
            tree = {str(i): [str(i + 1)] for i in range(1, 2000)}
            result = run_cluster(Node, tree, triggers=["count"], order="random", seed=11)
        """, ["2000"], label="chain of 2,000 machines", time_limit_ms=3000),
    ],
    "ai-rag-retrieval": [
        T(1, 'result = chunk_text("a b c", 1, 0)', ["a", "b", "c"], label="one word per chunk"),
        T(2, """
            import random
            rng = random.Random(1)
            vocab = [f"w{i}" for i in range(5000)]
            docs = {f"d{i}": " ".join(rng.choice(vocab) for _ in range(60)) + f" unique{i}" for i in range(2000)}
            r = Retriever(docs)
            hits = [r.search(f"unique{i}", 1) for i in range(0, 2000, 20)]
            result = all(h == [f"d{i}"] for h, i in zip(hits, range(0, 2000, 20)))
        """, True, label="2,000 documents, 100 queries: index once, not per query", time_limit_ms=2000),
    ],
    "ai-sensor-pipeline": [
        T(1, """
            lines = ["timestamp,sensor_id,metric,value\\r\\n", "2026-03-01T10:00:00Z,s-1,temp_c,20\\r\\n"]
            result = parse_readings(lines)["readings"][0]["value"]
        """, 20.0, label="Windows line endings"),
        T(1, """
            lines = [f"2026-03-01T10:{m:02d}:{s:02d}Z,s-{i % 50},temp_c,{i % 40}" for i in range(20_000)
                     for m, s in [divmod(i % 3600, 60)]]
            out = parse_readings(lines)
            result = [len(out["errors"]), len(out["readings"]) > 0]
        """, [0, True], label="20,000 lines", time_limit_ms=3000),
    ],
    "product-permit-tracker": [
        T(2, """
            import os
            db_path = os.path.join(tmpdir, "permits.db")
            client = create_app(db_path).test_client()
            client.post("/applications", json={"applicant": "A", "address": "1 St", "type": "solar"})
            r = client.post("/applications/1/transitions", json={"to": "under_review", "actor": "x", "note": 5})
            result = [r.status_code, client.get("/applications/1").get_json()["status"]]
        """, [400, "submitted"], label="non-string note is rejected"),
        T(3, """
            import os
            client = create_app(os.path.join(tmpdir, "permits.db")).test_client()
            for i in range(150):
                client.post("/applications", json={"applicant": f"P{i}", "address": "1 St", "type": "solar"})
            page = client.get("/applications?limit=100&offset=100").get_json()
            result = [page["total"], len(page["items"]), page["items"][0]["id"]]
        """, [150, 50, 101], label="last page of 150", time_limit_ms=5000),
    ],
})
