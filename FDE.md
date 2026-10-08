# Forward-deployed & applied AI interviews

Deployed / forward-deployed engineering (FDE), applied AI and product engineering roles
are judged on more than code. Expect to be evaluated on:

- **Building fast and pragmatically:** working code under time pressure, often full stack, often against an API or messy data.
- **Applied AI fluency:** calling LLM APIs, tool use/agents, RAG, structured output, and above all **evals** (how you know it works).
- **Customer judgement:** turning a vague request into a scoped, measurable project; saying no well; handling incidents in front of the client.
- **Ownership:** you're the one on site when it breaks.

[TOC]

## Brain Co.: what their postings say

From Brain Co.'s public job postings for *AI Product Engineer, Deployed* and *AI/ML Engineer, Deployed*
(details vary by posting, so check the one you applied to):

- Applied AI company building AI platforms and applications for **governments and large institutions**.
  Their published case studies include **construction permitting** for a government, **supply-chain costs**
  for an energy company, and **hospital care** for national health systems.
- You **work directly with the customer to develop the product spec and build from zero**.
- Full stack: **React, TypeScript, RESTful APIs, databases**, microservices, cloud platforms.
- **Integrating data pipelines and sensor networks**; **monitoring and maintaining deployed applications**.
- **Travel and on-site work**: one posting mentions willingness to travel globally for 6+ months and work
  directly with subject-matter experts and end users.

What that suggests to practise here:

| Theme | Where in this app |
|---|---|
| LLM API client, retries, structured extraction, concurrency | Problems → Applied AI → *LLM API Client* |
| Agents with tools | *Agent Tool-Use Loop* |
| Retrieval over regulations + evals | *RAG: Chunk, Retrieve, Evaluate* |
| Sensor/field data | *Sensor Data Pipeline* |
| Government / hospital / enterprise system design | System Design → Applied AI prompts |
| Discovery, scoping, incidents, stakeholders | The scenarios below |
| React / TypeScript | Not covered by this Python app. Practise building a small full-stack feature (form + list + REST API + DB) in under an hour |

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
