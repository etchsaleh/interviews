"""System design practice prompts.

Briefs are intentionally vague, like the real thing: the point is to practise asking
clarifying questions, pinning down requirements and talking through trade-offs.
Each prompt's reveal sections are what a strong candidate would cover - read them
*after* you've done a timed attempt.
"""

PROMPTS = [
    {
        "id": "url-shortener",
        "title": "URL shortener",
        "level": "Warm-up",
        "brief": "We want short links for our marketing emails. Design it.",
        "clarify": [
            "Who creates links — internal marketers only, or the public? (abuse, auth)",
            "Expected scale: links created per day? clicks per day? (read:write ratio is usually ~100:1)",
            "Custom aliases? Expiry? Do links ever change destination?",
            "Do we need click analytics, and how fresh (real-time vs daily)?",
            "Latency target for the redirect?",
        ],
        "requirements": """
- **Functional:** create short link (optional custom alias, expiry), redirect, basic click counts.
- **Non-functional:** redirect p99 < 50 ms, highly available reads, links never collide.
- **Estimate:** 1M new links/day ≈ 12 writes/s; 100M clicks/day ≈ 1.2k reads/s (peak ×5).
""",
        "design": """
- **API:** `POST /links {url, alias?, expires_at?} → {code}`; `GET /{code} → 301/302`.
- **ID generation:** base62 of a counter (ranges handed out per app server) or random 7 chars + uniqueness check. 62⁷ ≈ 3.5T codes.
- **Storage:** key-value (DynamoDB/Cassandra) or Postgres `code → url, expires_at, owner`. Simple lookups by primary key.
- **Read path:** load balancer → stateless app servers → **cache (Redis)** in front of the DB; hot links served from cache, plus CDN edge for the most popular.
- **Analytics:** don't write to the DB on every click — emit a click event to a **queue** (Kafka/SQS) and aggregate asynchronously.
""",
        "tradeoffs": [
            "301 (cacheable by browsers, fewer hits, worse analytics) vs 302 (every click reaches you).",
            "Counter-based IDs (no collisions, but guessable/enumerable) vs random IDs (need a collision check).",
            "SQL (simple, consistent, fine at this scale) vs NoSQL (easier horizontal scaling).",
        ],
    },
    {
        "id": "notifications",
        "title": "Notification service",
        "level": "Core",
        "brief": "Several of our products need to notify users. Build the thing they all use.",
        "clarify": [
            "Which channels: email, SMS, push, in-app? All at launch?",
            "Transactional (password reset — must be fast and reliable) vs marketing (bulk, can be slow)?",
            "User preferences / opt-outs / quiet hours?",
            "Volume and burstiness — e.g. a campaign to 10M users at once?",
            "Is at-least-once OK (possible duplicates) or do we need de-duplication?",
        ],
        "requirements": """
- **Functional:** `send(user, template, data, channels, priority)`; preferences & unsubscribe; delivery status.
- **Non-functional:** transactional p95 < 5 s; bulk can take minutes; no lost messages; tolerate provider outages.
""",
        "design": """
- **API gateway → Notification API** validates, renders templates, checks preferences, writes a record, enqueues.
- **Queues per channel and priority** (e.g. `email-high`, `email-bulk`) so a campaign can't delay password resets.
- **Workers** per channel call providers (SES, Twilio, APNs/FCM) with **retries + exponential backoff**, then a **dead-letter queue**.
- **Idempotency key** per notification so retries don't double-send.
- **Status store** (notification id → queued/sent/failed/delivered) fed by provider webhooks.
- Rate limit per provider and per user (no 50 pushes in a minute).
""",
        "tradeoffs": [
            "One queue (simple) vs per-channel/priority queues (isolation, more ops).",
            "Push vs pull for in-app notifications (websocket vs polling).",
            "At-least-once + idempotency vs exactly-once (expensive, rarely truly needed).",
        ],
    },
    {
        "id": "rate-limiter",
        "title": "API rate limiting",
        "level": "Core",
        "brief": "A client hammered our public API and took it down last week. Make sure that can't happen again.",
        "clarify": [
            "Limit by what — API key, user, IP, endpoint? Different tiers per plan?",
            "Hard reject (429) or queue/throttle? Should clients see remaining quota (headers)?",
            "How many API servers / regions? Must limits be exact globally or is approximate OK?",
            "Was the outage really volume, or one expensive endpoint? (maybe needs per-endpoint cost)",
        ],
        "requirements": """
- **Functional:** per-key limits by plan, 429 with `Retry-After` and `X-RateLimit-*` headers, config without deploys.
- **Non-functional:** < 1–2 ms added latency; limiter failure must not take the API down (fail open?).
""",
        "design": """
- Enforce at the **API gateway** (or a middleware) before requests reach services.
- **Algorithm:** token bucket (allows bursts, smooth) or sliding-window counter; store counters in **Redis** with atomic `INCR`/Lua and TTLs.
- Local in-memory pre-check per node to shed obvious abuse without a Redis round trip.
- Limits config in a DB/config service, cached in the gateway.
- Separate **load shedding** / circuit breakers protect the backend even from in-quota traffic.
""",
        "tradeoffs": [
            "Exact global counts (central Redis, extra latency) vs per-node approximate limits.",
            "Fail open (availability) vs fail closed (protection) when Redis is down.",
            "Fixed window (cheap, edge bursts) vs sliding log (exact, memory heavy) vs token bucket.",
        ],
    },
    {
        "id": "file-processing",
        "title": "Client file uploads + processing",
        "level": "Core",
        "brief": "Clients upload files and we process them. Design it.",
        "clarify": [
            "What files and how big? CSVs of 10 MB or videos of 10 GB changes everything.",
            "What is 'processing' — parse/validate, transcode, run a model? How long does it take?",
            "Does the client wait for the result (sync) or get notified later?",
            "How many uploads per day? Spiky (end of month)?",
            "Retention, PII, encryption, per-client isolation requirements?",
        ],
        "requirements": """
- **Functional:** upload, track status, get results/errors, notify on completion.
- **Non-functional:** large files must not go through our app servers; processing scales with backlog; failures are retried and visible.
""",
        "design": """
- Client asks API for a **pre-signed URL** and uploads **directly to object storage** (S3/GCS); multipart for big files.
- Storage event → **queue** → **worker pool** (autoscaled on queue depth) processes and writes results back to object storage.
- **Job table** (id, client, status, attempts, error) drives the status API; webhook or email when done.
- Retries with backoff, poison files to a **DLQ**, idempotent workers (same file processed twice is harmless).
""",
        "tradeoffs": [
            "Direct-to-storage uploads (scales, more client logic) vs proxy through API (simple, bottleneck).",
            "Queue + workers (decoupled, buffers spikes) vs synchronous processing (simple, timeouts).",
            "Serverless functions (no ops, time limits) vs container workers (long jobs, more control).",
        ],
    },
    {
        "id": "slow-dashboard",
        "title": "Our dashboard is slow",
        "level": "Core",
        "brief": "Customers say the analytics dashboard is slow. Fix it — design what you'd build.",
        "clarify": [
            "Slow where — first load, specific widgets, at certain times? Do we have metrics/traces?",
            "How fresh must the numbers be — real-time, 1 minute, daily?",
            "How much data per customer, and what queries — aggregates over months?",
            "Is the DB shared with the transactional app?",
        ],
        "requirements": """
- **Functional:** same dashboards, same numbers.
- **Non-functional:** p95 page load < 1 s; data at most N minutes stale (agree N!); no impact on the main app's DB.
""",
        "design": """
- **Measure first:** tracing shows where time goes (DB query, N+1 calls, payload size, frontend).
- **Caching layers:** CDN for static assets → API response cache in **Redis** keyed by (customer, widget, params) with TTL → DB.
- **Pre-aggregation:** move heavy aggregates to rollup tables or a materialized view / OLAP store (ClickHouse, BigQuery), refreshed by a scheduled or streaming job.
- **Read replica** so dashboards don't load the primary.
- Invalidation: TTL for most widgets; event-driven invalidation for the few that must be fresh.
""",
        "tradeoffs": [
            "TTL caching (simple, briefly stale) vs explicit invalidation (fresh, easy to get wrong).",
            "Cache-aside vs write-through vs pre-computing everything.",
            "Read replicas (cheap, replication lag) vs a separate analytics store (fast, pipeline to own).",
        ],
    },
    {
        "id": "job-scheduler",
        "title": "Job scheduler",
        "level": "Core",
        "brief": "Teams keep writing their own cron boxes. Give them one service for scheduled and background jobs.",
        "clarify": [
            "One-off delayed jobs, recurring cron jobs, or both?",
            "How precise must timing be (seconds vs minutes)? How many jobs/sec at peak?",
            "What happens if a job runs twice? Or is missed while we're down?",
            "Who runs the job code — our workers or callbacks to their services?",
        ],
        "requirements": """
- **Functional:** create/cancel/list jobs, cron syntax, retries, history and logs.
- **Non-functional:** no job silently lost; at-least-once execution; no single point of failure.
""",
        "design": """
- **Jobs table** (`next_run_at` indexed). Scheduler instances poll for due jobs using `SELECT … FOR UPDATE SKIP LOCKED` (or leader election) and push them to a **queue**.
- **Workers** consume, execute (or call the team's webhook), record results, compute the next run for cron jobs.
- Visibility timeouts + heartbeats detect crashed workers; retries with backoff; DLQ.
- Jobs must be **idempotent** (we guarantee at-least-once).
""",
        "tradeoffs": [
            "DB polling (simple, limited throughput) vs time-bucketed queues / delayed messages.",
            "Leader-elected single scheduler (simple) vs partitioned schedulers (scale).",
            "At-least-once + idempotency vs exactly-once.",
        ],
    },
    {
        "id": "webhooks",
        "title": "Webhook delivery",
        "level": "Core",
        "brief": "Enterprise clients want to be told when things happen in our platform. Design it.",
        "clarify": [
            "Which events? Do clients subscribe per event type?",
            "Ordering guarantees per resource?",
            "What if the client's endpoint is down for hours?",
            "Security: how do clients verify it's us?",
            "Volume per client — can one big client slow down the others?",
        ],
        "requirements": """
- **Functional:** subscriptions per event type, signed payloads, retries, delivery log + manual replay.
- **Non-functional:** one slow client must not affect others; deliveries survive our deploys and their outages.
""",
        "design": """
- Services publish domain events to an **event bus** (Kafka/SNS).
- **Dispatcher** matches subscriptions and enqueues deliveries — **per-client queues/partitions** for isolation.
- **Delivery workers:** POST with **HMAC signature** + timestamp, timeouts, exponential backoff for ~24 h, then disable the endpoint and alert the client.
- Delivery log (attempts, status codes) in a DB; dashboard + replay endpoint for clients.
""",
        "tradeoffs": [
            "Per-resource ordering (partitioning, head-of-line blocking) vs unordered (simpler, faster).",
            "Thin events (client fetches details, always fresh) vs fat payloads (fewer calls, stale/PII risk).",
        ],
    },
    {
        "id": "chat",
        "title": "Real-time chat / support widget",
        "level": "Stretch",
        "brief": "Add live chat between our clients' customers and their support agents.",
        "clarify": [
            "1:1 only or group rooms? Typing indicators, read receipts, attachments?",
            "Concurrent connections at peak?",
            "Message history retention and search?",
            "Offline agents — queueing and routing of conversations?",
        ],
        "requirements": """
- **Functional:** send/receive in real time, history, presence, assignment of chats to agents.
- **Non-functional:** < 200 ms delivery, no lost or reordered messages within a conversation.
""",
        "design": """
- **WebSocket gateway** servers behind a load balancer (sticky connections); connection registry in Redis (user → gateway).
- Messages: persist first (DB partitioned by conversation id), then fan out via **pub/sub** to the gateways holding recipients.
- Per-conversation sequence numbers for ordering; clients ack and re-sync on reconnect.
- Routing service assigns conversations to available agents (a queue per team).
""",
        "tradeoffs": [
            "WebSockets vs long polling vs SSE.",
            "Write-then-fanout (durable) vs fanout-then-write (lower latency, risk of loss).",
        ],
    },
    {
        "id": "llm-assistant",
        "title": "LLM-powered assistant for a client",
        "level": "Stretch",
        "brief": "A client wants an AI assistant that answers questions over their internal documents. Design it.",
        "clarify": [
            "Which documents, how many, how often do they change? Permissions per document?",
            "Who uses it and how many queries/day? Latency expectations (streaming OK)?",
            "Accuracy needs — must answers cite sources? What's the cost budget per query?",
            "Data residency / can data leave their cloud?",
        ],
        "requirements": """
- **Functional:** ingest docs, answer with citations, respect per-user permissions, feedback (thumbs up/down).
- **Non-functional:** first token < 2 s, cost per query bounded, no data leaking across users.
""",
        "design": """
- **Ingestion pipeline:** connectors → chunk → embed → **vector index** with ACL metadata; queue-driven, incremental on doc change.
- **Query path:** API gateway (auth, rate limit) → retrieve top-k chunks filtered by user ACL → build prompt → LLM (streaming) → answer + citations.
- **Caching:** cache embeddings and frequent question answers; prompt caching for shared context.
- **Eval & observability:** log queries/retrievals, offline eval set, feedback loop.
""",
        "tradeoffs": [
            "Retrieval (fresh, cheap) vs fine-tuning (style/format, stale knowledge).",
            "Bigger model (quality) vs smaller/faster (latency, cost); route by question difficulty.",
            "Filter ACLs at retrieval time (secure) vs post-filtering (can leak or return empty results).",
        ],
    },
]
