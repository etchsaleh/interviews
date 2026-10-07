# System design: running the interview end to end

System design rounds are open-ended on purpose. You're judged less on the "right" diagram
and more on **how you get there**: asking good questions, pinning down requirements,
making reasonable assumptions out loud, and explaining trade-offs. Your Java/backend
background is an advantage here — lean on it.

[TOC]

## 1. The 45-minute flow

| Time | Step | What you do |
|---|---|---|
| 0–5 | **Clarify** | Restate the problem. Ask who the users are, what the core use cases are, what's out of scope. |
| 5–10 | **Requirements** | Write down functional + non-functional requirements (scale, latency, availability, consistency). Get the interviewer to agree. |
| 10–13 | **Estimate** | Rough numbers: requests/sec, storage/year, read:write ratio. Only as deep as it changes the design. |
| 13–18 | **API & data model** | The main endpoints and the core tables/entities. |
| 18–30 | **High-level design** | Boxes and arrows for the main flows. Walk one request end to end. |
| 30–40 | **Deep dive** | Pick 1–2 hard parts (often the interviewer picks): scaling the hot path, consistency, failure handling. |
| 40–45 | **Wrap up** | Bottlenecks, what you'd monitor, what you'd do with more time. Summarise the trade-offs you made. |

**Drive the conversation.** Say what you're about to do ("I'll spend a few minutes on
requirements, then sketch the high level, then go deep on the write path — sound good?").
Check in at each transition.

## 2. Clarifying questions — a checklist

When the prompt is vague, it's deliberate. Work through these out loud:

- **Users & use cases:** Who uses it? What are the top 2–3 things they do? What's explicitly out of scope?
- **Scale:** How many users / requests per second / items stored? Growth over 1–3 years? Spiky traffic?
- **Latency:** What must feel instant? What can be async?
- **Consistency:** Is it OK if a user briefly sees stale data? Where is it *not* OK (money, inventory)?
- **Availability:** What happens if it's down for 5 minutes? Multi-region needed?
- **Data:** How big are the items? Retention? PII / compliance?
- **Integrations & constraints:** Existing systems, cloud provider, team size, deadline, budget.

If the interviewer says "you decide", **state an assumption and move on**:
"I'll assume 10M daily users and that a few seconds of staleness in the feed is fine."

## 3. Back-of-the-envelope numbers

| Thing | Rough number |
|---|---|
| Seconds per day | ~86,400 ≈ 10⁵ → 1M requests/day ≈ 12 req/s |
| Peak vs average | ×2 to ×10 |
| Memory read / SSD read / same-DC round trip / cross-continent | ~100 ns / ~100 µs / ~0.5 ms / ~150 ms |
| One Postgres/MySQL box | thousands of simple queries/s; a few TB comfortably |
| One Redis node | ~100k ops/s, data must fit in RAM |
| One app server | hundreds to a few thousand req/s depending on work |
| Kafka partition | ~10 MB/s |

## 4. Building blocks

| Block | What it's for | Watch out for |
|---|---|---|
| **Load balancer** (L4/L7) | Spread traffic over stateless servers, health checks, TLS termination | Sticky sessions break statelessness; LB itself needs redundancy |
| **API gateway** | Single entry point: auth, rate limiting, routing, request validation, API keys, versioning | Can become a bottleneck / god-service; keep business logic out |
| **Stateless app servers** | Horizontal scaling — any server handles any request | Keep sessions in a shared store or tokens (JWT) |
| **Cache** (Redis/Memcached, CDN) | Cut latency and DB load for hot reads | Invalidation, stampedes on expiry, stale data, memory limits |
| **Message queue** (SQS, RabbitMQ) | Decouple producers from consumers, absorb spikes, retries, async work | At-least-once delivery → consumers must be idempotent; DLQs; ordering |
| **Event log / pub-sub** (Kafka, SNS) | Fan-out events to many consumers, replay, streaming | Partitioning decides ordering and parallelism; consumer lag |
| **Relational DB** (Postgres, MySQL) | Transactions, joins, strong consistency — the default choice | Vertical limits → read replicas, then sharding |
| **NoSQL** (DynamoDB, Cassandra, Mongo) | Massive scale on simple access patterns, flexible schema | Design tables around queries; limited joins/transactions |
| **Object storage** (S3) | Files, images, backups, data lake | Use pre-signed URLs; not for small hot random reads |
| **CDN** | Serve static/edge-cacheable content close to users | Cache keys and purge strategy |
| **Search index** (Elasticsearch/OpenSearch) | Full-text search, faceting | It's a secondary index — keep the DB as source of truth |
| **Workers / schedulers** | Background and periodic jobs | Retries, idempotency, monitoring stuck jobs |
| **Observability** | Metrics, logs, traces, alerts | Mention it in every design — it shows ownership |

### Caching patterns
- **Cache-aside** (most common): read cache → on miss read DB and populate. Write DB then delete the cache key.
- **Write-through:** write to cache and DB together — fresher cache, slower writes.
- **Write-behind:** write to cache, flush to DB async — fast, risk of loss.
- Eviction: **LRU** (default), LFU, TTL. Protect against **stampedes** with request coalescing or jittered TTLs.

### Queue patterns
- Work queue (one consumer per message) vs pub/sub (every subscriber gets it).
- **At-least-once + idempotency keys** is the practical default; "exactly once" is usually an illusion.
- Retries with exponential backoff + jitter → **dead-letter queue** after N attempts.
- Back-pressure: autoscale consumers on queue depth.

## 5. Trade-offs to have ready

| Decision | Option A | Option B |
|---|---|---|
| Consistency | Strong (simpler reasoning, higher latency, less available) | Eventual (fast, available, users may see stale data) |
| Sync vs async | Sync request/response (simple, immediate result) | Queue + workers (resilient, smooths spikes, harder to debug) |
| SQL vs NoSQL | Flexible queries, transactions | Scale and predictable latency on known access patterns |
| Push vs pull | Push (real-time, server must track clients) | Pull/polling (simple, wasteful, delayed) |
| Monolith vs services | Fast to build, one deploy | Independent scaling/teams, network + ops complexity |
| Fan-out on write vs read (feeds) | Fast reads, expensive for celebrity users | Cheap writes, slower reads — hybrid is common |
| Build vs buy | Control, cost at scale | Speed to market — often right for a small team |

**How to say a trade-off:** "I'm choosing X because of requirement R. The cost is Y;
if Z turns out to matter more, I'd switch to W." That sentence is most of the grade.

## 6. Common mistakes

- Jumping to boxes before agreeing what you're building.
- Designing for Google scale when the requirement is 100 req/s — over-engineering is a negative signal.
- Naming technologies without saying *why*.
- Going silent. Think out loud; the interviewer can only grade what they hear.
- Ignoring failure: what happens when the DB, a queue, or a third-party API is down?
- Never checking in — ask "Does this match what you had in mind? Where would you like me to go deeper?"

## 7. Practising with the prompts below

1. Pick a prompt and press **Start 45-min mock**. Read only the brief.
2. Write your clarifying questions and assumptions in the notes box *before* designing. Say them out loud.
3. Follow the flow above. Sketch on paper or excalidraw.
4. When the timer ends, open the reveal sections and compare: which questions did you miss? Which trade-offs did you not mention?
