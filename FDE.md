# AI product engineering & forward-deployed interviews

Deployed / forward-deployed engineering (FDE), applied AI and product engineering roles
are judged on more than code. Expect to be evaluated on:

- **Building fast and pragmatically:** working code under time pressure, often full stack, often against an API or messy data.
- **Applied AI fluency:** calling LLM APIs, tool use/agents, RAG, structured output, and above all **evals** (how you know it works).
- **Customer judgement:** turning a vague request into a scoped, measurable project; saying no well; handling incidents in front of the client.
- **Ownership:** you're the one on site when it breaks.

[TOC]

## Brain Co.: the AI Product Engineer, Deployed role

From Brain Co.'s public postings for **AI Product Engineer, Deployed** (details vary by
posting, so check the one you applied to):

- Applied AI company building AI platforms and applications for **governments and large institutions**.
  Their published case studies include **construction permitting** for a government, **supply-chain costs**
  for an energy company, and **hospital care** for national health systems.
- You **work directly with the customer to develop the product spec and build from zero**.
- **Front end and back end:** React, TypeScript, RESTful APIs, database management, microservices, cloud platforms.
- **Integrating data pipelines and sensor networks**; **monitoring and maintaining deployed applications**.
- **Travel and on-site work**: one posting mentions willingness to travel globally for 6+ months and work
  directly with subject-matter experts and end users.

So the bar is a **product engineer who ships whole features**: spec → API → UI → AI
feature → deploy → support, with the customer in the room. Practise in this order:

| Skill | Where |
|---|---|
| Build a backend product in stages, with an AI feature | Problems → Product Engineering → *Build a Permit Tracker* |
| Build the UI for it in React + TypeScript | The drills below (outside this app) |
| Write a spec with a customer, prioritise, demo | Scenarios: *Write the spec*, *Prioritise the backlog*, *Discovery*, *Scope creep* |
| LLM features done properly (retries, structured output, caching) | Applied AI → *LLM API Client*, then *Agent* and *RAG* |
| Messy field data | Applied AI → *Sensor Data Pipeline* |
| Product system design | System Design → *AI-assisted building permits*, *Clinical documentation* |

## React + TypeScript drills (do these outside this app)

Build a UI on top of the Permit Tracker API you wrote. Save your solution as
`permits.py` and run it with `flask --app 'permits:create_app("permits.db")' run` (port 5000
is taken by this app, so add `--port 5001`). Create the UI with
`npm create vite@latest permits-ui -- --template react-ts`, and point Vite's dev proxy
(`server.proxy` in `vite.config.ts`) at `http://127.0.0.1:5001` so the browser doesn't hit
CORS errors. Time each drill and aim for the targets.

| # | Drill | Done when | Target |
|---|---|---|---|
| 1 | **List page** | Fetch `/applications`, show a table, with loading and error states | 20 min |
| 2 | **Filters + pagination** | Status/type dropdowns, search box (debounced), next/prev; state in the URL | 25 min |
| 3 | **Create form** | Controlled inputs, client-side validation, show the API's 400 `fields` next to inputs | 25 min |
| 4 | **Detail + workflow** | Detail page with history timeline; buttons only for allowed transitions; handle 409 | 25 min |
| 5 | **AI summary panel** | Load the summary lazily, spinner, retry button on 503, "AI-generated" label | 15 min |
| 6 | **Streaming text** | Render an LLM reply token by token (fake it with a timer if needed); cancel button | 20 min |
| 7 | **Polish** | Empty states, disabled buttons while saving, optimistic status update with rollback on error | 20 min |

### TypeScript for Java developers (one screen)

```typescript
type Status = "submitted" | "under_review" | "approved" | "rejected" | "needs_info";  // union of literals ≈ enum

interface Application {            // structural typing: any object with these fields matches
  id: number;
  applicant: string;
  description?: string;            // optional field
  status: Status;
}

const apps: Application[] = [];    // const = final reference; let = mutable variable
const byId = new Map<number, Application>();
const names = apps.filter(a => a.status === "approved").map(a => a.applicant);  // streams, without .stream()

async function load(page: number): Promise<{ items: Application[]; total: number }> {
  const res = await fetch(`/applications?limit=20&offset=${page * 20}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}
```

- `===` compares without type coercion (always use it). `null` and `undefined` both exist; `a?.b ?? "default"` handles both.
- Types disappear at runtime, so validate API responses at the boundary if they matter.

### React essentials

```tsx
function ApplicationList() {
  const [items, setItems] = useState<Application[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {                          // runs after render; [] = only once on mount
    load(0).then(r => setItems(r.items)).catch(e => setError(String(e))).finally(() => setLoading(false));
  }, []);

  if (loading) return <p>Loading…</p>;
  if (error) return <p role="alert">{error}</p>;
  return <ul>{items.map(a => <li key={a.id}>{a.applicant} — {a.status}</li>)}</ul>;
}
```

- State is immutable: `setItems([...items, newItem])`, never `items.push(...)`.
- Every list item needs a stable `key`. Effects that depend on props or state list them in the dependency array.

## Running a customer conversation

1. **Problem first.** Ask for one real case and follow it end to end. Who does what, with which data, how long it takes.
2. **Play it back** in one sentence and get a "yes, exactly".
3. **Success metric.** "In 3 months, what number has moved?" Write it down with the baseline.
4. **Data and constraints.** Where the data lives, who owns it, residency, security, integration points.
5. **Options**, ranked by value × feasibility. Recommend one, and say what you'd not do yet.
6. **Next step** with a date: data sample, user session, pilot plan.

## Scoping a pilot

- One user group, one workflow, one metric. Weeks, not months.
- Week 1 is baseline and data access. Shadow mode before live. Weekly demos.
- Keep a written in/out list and a risk log. Make trade-offs the client's decision, with your recommendation.

## Behavioural stories to prepare (STAR, ~2 minutes each)

- Built something **from zero with a customer**, where the spec changed as you learned.
- Owned a feature **end to end**: UI, API, data, deploy, and what you learned from users.
- A **production incident** you owned: detection, fix, follow-up.
- **Pushed back** on a stakeholder and kept the relationship.
- Worked in an **unfamiliar domain** quickly (learned from subject-matter experts).
- Shipped under a **hard deadline**, far from your usual team, or on site.
- Used **AI tools to move faster**: what you delegate, how you verify.

## Questions to ask them

- What does the first month on a deployment look like? How big is the team on site?
- How do you evaluate quality before and after launch at a client?
- How much is shared platform vs custom per client?
- What's the hardest constraint you've hit at a government client, and how did you handle it?

## The scenarios

Each one is a short role-play. Start the timer, answer out loud (write notes as you go),
then open the sections underneath and compare.
