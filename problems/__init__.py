from problems.algorithms import PROBLEMS as ALGORITHMS
from problems.applied_ai import PROBLEMS as APPLIED_AI
from problems.editorials import EDITORIALS
from problems.editorials_applied_ai import PART_EDITORIALS as AI_EDITORIALS
from problems.editorials_multipart import PART_EDITORIALS as MP_EDITORIALS
from problems.editorials_realworld import PART_EDITORIALS as RW_EDITORIALS
from problems.extra_tests import EXTRA_TESTS
from problems.api import PROBLEMS as API_PROBLEMS
from problems.focus import PROBLEMS as FOCUS
from problems.multipart import PROBLEMS as MULTIPART
from problems.product import PROBLEMS as PRODUCT
from problems.realworld import PROBLEMS as REALWORLD

# Display order: grounded, real-world work first (what Brain Co.-style rounds test), then classic DSA as warm-up.
CATEGORY_ORDER = ["Real-world", "Product Engineering", "Applied AI", "Multi-part", "Graphs", "Queues", "Caching", "Python OOP", "Fundamentals", "APIs"]
CATEGORY_NOTES = {
    "Real-world": "grounded tasks from deployments: messy logs, CSV reconciliation, scheduling, inventory rules (start here)",
    "Product Engineering": "build a real product backend in stages: API, workflow, search, persistence, then an AI feature",
    "Applied AI": "LLM APIs, agents, RAG + evals and messy field data, as FDE / applied-AI rounds test them (multi-part)",
    "Multi-part": "real question-bank prompts; each part unlocks when the previous one passes",
    "Graphs": "warm-up DSA: BFS/DFS, topological sort, Dijkstra, union-find",
    "Queues": "warm-up DSA: deque, heaps, sliding windows, simulations",
    "Caching": "warm-up DSA: LRU, TTL, memoizing slow calls",
    "Python OOP": "a class with a few methods — usually all you need",
    "Fundamentals": "warm-ups for Python fluency: dicts, strings, sorting, DP",
    "APIs": "refresher — GET/POST, params, reading JSON. Don't over-index here",
}

ALL_PROBLEMS = sorted(REALWORLD + PRODUCT + APPLIED_AI + MULTIPART + ALGORITHMS + FOCUS + API_PROBLEMS, key=lambda p: CATEGORY_ORDER.index(p["category"]))
BY_ID = {p["id"]: p for p in ALL_PROBLEMS}
for problem_id, editorial in {**EDITORIALS, **AI_EDITORIALS, **MP_EDITORIALS, **RW_EDITORIALS}.items():
    BY_ID[problem_id]["editorial"] = editorial  # a string, or one string per part for multi-part problems
for problem_id, tests in EXTRA_TESTS.items():
    BY_ID[problem_id]["tests"].extend(tests)


assert len(BY_ID) == len(ALL_PROBLEMS), "duplicate problem ids"
