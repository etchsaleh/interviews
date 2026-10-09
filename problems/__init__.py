from problems.algorithms import PROBLEMS as ALGORITHMS
from problems.applied_ai import PROBLEMS as APPLIED_AI
from problems.editorials import EDITORIALS
from problems.extra_tests import EXTRA_TESTS
from problems.api import PROBLEMS as API_PROBLEMS
from problems.focus import PROBLEMS as FOCUS
from problems.multipart import PROBLEMS as MULTIPART
from problems.product import PROBLEMS as PRODUCT

# Display order: interview focus areas first, then fundamentals, then the API refresher.
CATEGORY_ORDER = ["Product Engineering", "Applied AI", "Multi-part", "Graphs", "Queues", "Caching", "Python OOP", "Fundamentals", "APIs"]
CATEGORY_NOTES = {
    "Product Engineering": "build a real product backend in stages: API, workflow, search, persistence, then an AI feature",
    "Applied AI": "LLM APIs, agents, RAG + evals and messy field data, as FDE / applied-AI rounds test them (multi-part)",
    "Multi-part": "real question-bank prompts; each part unlocks when the previous one passes",
    "Graphs": "BFS/DFS, topological sort, Dijkstra, union-find",
    "Queues": "deque, heaps, sliding windows, simulations",
    "Caching": "LRU, TTL, memoizing slow calls",
    "Python OOP": "a class with a few methods — usually all you need",
    "Fundamentals": "warm-ups for Python fluency: dicts, strings, sorting, DP",
    "APIs": "refresher — GET/POST, params, reading JSON. Don't over-index here",
}

ALL_PROBLEMS = sorted(PRODUCT + APPLIED_AI + MULTIPART + ALGORITHMS + FOCUS + API_PROBLEMS, key=lambda p: CATEGORY_ORDER.index(p["category"]))
BY_ID = {p["id"]: p for p in ALL_PROBLEMS}
for problem_id, editorial in EDITORIALS.items():
    BY_ID[problem_id]["editorial"] = editorial
for problem_id, tests in EXTRA_TESTS.items():
    BY_ID[problem_id]["tests"].extend(tests)

# Categories whose problems are LeetCode-style and must have an editorial.
EDITORIAL_CATEGORIES = {"Fundamentals", "Graphs", "Queues", "Caching", "Python OOP"}

assert len(BY_ID) == len(ALL_PROBLEMS), "duplicate problem ids"
