# 3-week study plan

[TOC]

## Priorities

1. **Python fluency + easy/medium DSA**, focused on **graphs, queues and caching**. Time
   pressure in the coding round is the real risk, and that's why you're switching to Python.
2. **System design fundamentals**: clarifying questions, requirements, trade-offs.
3. **Quick refresher** on API calls (GET/POST, params, reading JSON) and basic Python classes.

What *not* to do: grind hundreds of LeetCode problems or go deep on API edge cases.
Questions come from the company's own bank with a custom twist, so **solid fundamentals
and adaptability** beat memorised solutions.

## Track for FDE / applied AI roles (e.g. Brain Co.)

Deployed-engineer roles weigh practical AI building and customer judgement as much as
DSA. Read [FDE Scenarios](/fde) first: it summarises what Brain Co.'s postings ask for.
Then, on top of the plan below:

| When | Add |
|---|---|
| Week 1 | Guide §15 *LLM apps in Python*. [LLM API Client](/problem/ai-llm-client) parts 1–2 |
| Week 2 | Finish [LLM API Client](/problem/ai-llm-client), [Agent Tool-Use Loop](/problem/ai-agent-loop), [RAG: Chunk, Retrieve, Evaluate](/problem/ai-rag-retrieval). One FDE scenario every other day, out loud |
| Week 3 | [Sensor Data Pipeline](/problem/ai-sensor-pipeline) as a timed mock. The four *Applied AI* system design prompts (government permits, hospital, LLM gateway, eval & monitoring). Rehearse your behavioural stories |
| Outside this app | Build one small full-stack feature in React + TypeScript + a REST API + a database, timed. The postings list that stack, and this app only covers Python |

If time is short, cut Fundamentals and the API refresher before cutting these.

## How to practise a problem

1. **Time it.** The timer starts on your first keystroke. Targets: Easy 10 min, Medium 20 min.
2. **Say the approach before you code**: data structure, algorithm, complexity.
3. **Write Python, not Java-in-Python.** Check the *Coming from Java* tab afterwards and
   rewrite anything that could be more idiomatic.
4. When the tests pass, **do one "twist to try"** from the description tab without tests.
   This is the closest thing to their custom-twist questions.
5. Over target time? Put it on the redo list and solve it again from a blank editor 2–3
   days later.

## Week 1: Python fluency + first pass on the focus areas

| Day | Read | Solve |
|---|---|---|
| 1 | [Guide](/guide) §1–5. Play in the [Playground](/playground) | [Two Sum](/problem/two-sum), [Valid Anagram](/problem/valid-anagram), [Valid Palindrome](/problem/valid-palindrome) |
| 2 | Guide §6–10 | [Valid Parentheses](/problem/valid-parentheses), [Group Anagrams](/problem/group-anagrams), [Merge Intervals](/problem/merge-intervals) |
| 3 | Guide §4 (deque, heapq) | **Queues:** [Moving Average](/problem/moving-average), [Round-Robin](/problem/round-robin), [Ticket Queue](/problem/ticket-queue) |
| 4 | Guide §13 (BFS/DFS) | **Graphs:** [Number of Islands](/problem/number-of-islands), [Fewest Hops](/problem/fewest-hops) |
| 5 | Guide §8 (classes) | **Caching:** [LRU Cache](/problem/lru-cache), [Cache Hit Counter](/problem/cache-hit-rate). **OOP:** [Bank Accounts](/problem/bank-accounts) |
| Weekend | [System design](/system-design) §1–4 | Mock: *URL shortener*. Redo anything over target time |

## Week 2: Go deeper on the focus areas, start system design

| Day | Focus | Solve |
|---|---|---|
| 6 | Graphs: topological sort, union-find | [Build Order](/problem/build-order), [Team Groups](/problem/team-groups) |
| 7 | Graphs: weighted shortest paths | [Broadcast Time](/problem/broadcast-time) + redo *Number of Islands* blank in < 15 min |
| 8 | Queues: sliding windows | [Rate Limiter](/problem/rate-limiter) + twist: per-user limits |
| 9 | Caching: expiry, memoization | [TTL Cache](/problem/ttl-cache), [Cache Slow API Lookups](/problem/cached-prices) |
| 10 | OOP + API refresher (cap it at 1 hour) | [Leaderboard](/problem/leaderboard), [GET](/problem/api-active-users), [404](/problem/api-user-email), [params](/problem/api-team-filter), [POST](/problem/api-create-todo) |
| Weekend | System design §5–6 | Mocks, out loud: *Notification service*, *API rate limiting* |

## Week 3: Speed, twists and mocks

- **Every day:** 2 problems from a blank editor under the timer, each followed by a twist.
  Mix the categories; don't know in advance which technique is coming.
- **Every day:** one **multi-part** problem as a full mock round (≈45 min). Parts
  unlock one at a time like the real thing. Finish with the discussion follow-ups out loud:
  [Durable cache](/problem/mp-durable-cache), [IPv4 iterator](/problem/mp-ip-iterator),
  [Monster battle](/problem/mp-monster-battle), [File dedup](/problem/mp-file-dedup),
  [Cluster messages](/problem/mp-cluster-messages), [GPU credits](/problem/mp-gpu-credits).
- **Every other day:** one 45-minute system design mock: *File uploads*, *Slow dashboard*,
  *Job scheduler*, *Webhooks*. Record yourself or practise with a friend.
- Fill gaps: [Top K Frequent](/problem/top-k-frequent),
  [Longest Substring](/problem/longest-substring), [Product Except Self](/problem/product-except-self),
  [Climbing Stairs](/problem/climbing-stairs), [Max Subarray](/problem/max-subarray).
- **Last 2 days:** light. Re-read the [gotchas](/guide#14-gotchas-that-bite-java-developers),
  your redo list, and your behavioural stories.

## In the coding round (≈45 min)

| Minutes | Do |
|---|---|
| 0–5 | Restate the problem. Find **the twist**: what's different from the textbook version? Ask about input size, edge cases, return format. |
| 5–10 | Walk a small example by hand. Name the data structure and algorithm, state the complexity, and get a nod. |
| 10–30 | Code it in Python. Narrate briefly. Use the stdlib (`deque`, `heapq`, `Counter`, `defaultdict`, `OrderedDict`). |
| 30–40 | Trace a test by hand, then the edge cases: empty input, one element, duplicates, cycles, ties. |
| 40–45 | Discuss improvements and the follow-up twist they'll probably ask. |

If you're stuck: say the brute force out loud, code it if it's quick, then optimise.
A working O(n²) beats an unfinished O(n).

## Mindset and the conversation

The environment is fast, the team is small, and roles span full stack, infra and some
pre-sales. Prepare short (2-minute) stories in **Situation → Action → Result** form:

- **Ownership:** something you owned end to end, including a failure you fixed and what you changed afterwards.
- **Pressure / deadlines:** shipping under a real client deadline. What you cut, how you communicated.
- **Breadth:** times you worked outside your lane: frontend, infra/DevOps, talking directly to customers or helping close a deal.
- **Speed with AI tools:** how you use agentic coding tools (e.g. Claude Code) day to day. Be concrete: what you delegate, how you review, where they help or don't.
- **Client impact:** a time you worked close to the end user or the business outcome.

Questions worth asking them: what a typical week looks like across the hats; how client
work is scoped and prioritised; what "ownership" means on the team; how they use AI
tooling internally.
