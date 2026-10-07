from problems.algorithms import PROBLEMS as ALGORITHMS
from problems.api import PROBLEMS as API_PROBLEMS
from problems.focus import PROBLEMS as FOCUS

# Display order: interview focus areas first, then fundamentals, then the API refresher.
CATEGORY_ORDER = ["Graphs", "Queues", "Caching", "Python OOP", "Fundamentals", "APIs"]
CATEGORY_NOTES = {
    "Graphs": "BFS/DFS, topological sort, Dijkstra, union-find",
    "Queues": "deque, heaps, sliding windows, simulations",
    "Caching": "LRU, TTL, memoizing slow calls",
    "Python OOP": "a class with a few methods — usually all you need",
    "Fundamentals": "warm-ups for Python fluency: dicts, strings, sorting, DP",
    "APIs": "refresher — GET/POST, params, reading JSON. Don't over-index here",
}

ALL_PROBLEMS = sorted(ALGORITHMS + FOCUS + API_PROBLEMS, key=lambda p: CATEGORY_ORDER.index(p["category"]))
BY_ID = {p["id"]: p for p in ALL_PROBLEMS}

assert len(BY_ID) == len(ALL_PROBLEMS), "duplicate problem ids"
