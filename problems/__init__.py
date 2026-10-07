from problems.algorithms import PROBLEMS as ALGORITHMS
from problems.api import PROBLEMS as API_PROBLEMS

ALL_PROBLEMS = ALGORITHMS + API_PROBLEMS
BY_ID = {p["id"]: p for p in ALL_PROBLEMS}

assert len(BY_ID) == len(ALL_PROBLEMS), "duplicate problem ids"
