"""Forward-deployed / customer-facing scenarios for FDE, applied-AI and product-engineering rounds.

Same structure as system_design.PROMPTS so the page template can be shared:
brief (what the interviewer says), clarify (questions to ask), requirements (what's really
being tested), design (what a strong answer covers), tradeoffs (common pitfalls).
"""

LABELS = {
    "minutes": 20,
    "clarify": "Questions to ask first",
    "requirements": "What they're really testing",
    "design": "What a strong answer covers",
    "tradeoffs": "Pitfalls",
}

SCENARIOS = [
    {
        "id": "discovery",
        "title": "Discovery: \"We want AI\"",
        "level": "Discovery",
        "brief": "You meet a director at a government ministry. They say: \"We want to use AI to improve our citizen services. What can you do for us?\" Run the conversation.",
        "clarify": [
            "Which service is most painful today, for citizens and for staff? Can you walk me through one case end to end?",
            "Where does time go: waiting in queues, missing documents, manual review, back-and-forth?",
            "What data exists, where does it live, and who owns it?",
            "If this works brilliantly in 6 months, what number has changed? Who would notice?",
            "Who has to say yes: legal, IT security, procurement, the minister's office?",
            "What has been tried before, and why didn't it stick?",
        ],
        "requirements": """
- Can you turn a vague wish into **one concrete, valuable, measurable problem**?
- Do you **listen** more than you pitch? Do you ask about workflow and data before talking about models?
- Do you find the **decision makers and blockers** early?
""",
        "design": """
- Spend most of the time on **their workflow**, not on AI. Get a specific case and follow it end to end.
- Play back what you heard in one sentence: "So the biggest cost is X, it affects Y people, and success looks like Z."
- Propose 2-3 candidate use cases, ranked by **value x feasibility (data available, risk, time to impact)**, and recommend one.
- Close with a concrete next step: access to sample data, a session with front-line staff, a success metric to agree on.
""",
        "tradeoffs": [
            "Pitching a solution in the first five minutes.",
            "Picking the most impressive use case instead of the one with data and a clear owner.",
            "Leaving without a success metric or a next step.",
            "Ignoring the people who'll actually use it (front-line staff), not just the director.",
        ],
    },
    {
        "id": "pilot-scope",
        "title": "Scope a 6-week pilot",
        "level": "Scoping",
        "brief": "A hospital wants AI to reduce emergency-department wait times. You have 6 weeks and one other engineer. What do you build, and what do you say no to?",
        "clarify": [
            "Where in the ED journey is the delay: triage, waiting for beds, lab results, discharge?",
            "What data can we access in week 1, not week 5?",
            "Who will use the pilot daily, and who will judge if it succeeded?",
            "What can't change: clinical protocols, the EHR, staffing?",
        ],
        "requirements": """
- Can you **cut scope ruthlessly** to something that ships and proves value?
- Do you define **success before building**, and plan how to measure it?
- Do you manage **risk** (clinical safety, data access) explicitly?
""",
        "design": """
- Pick one bottleneck with data you can get now: for example, predicting discharges for the next 24 h so bed managers can plan, which is advisory only and low clinical risk.
- **Week plan:** week 1 data access and baseline metric; weeks 2-3 simplest model plus a usable screen; week 4 shadow mode beside current process; weeks 5-6 live with one team, measure, iterate.
- **Success metric:** e.g. "bed-wait time for admitted patients drops 15% on the pilot ward vs baseline", agreed with the client in week 1.
- Say no (for now) to: automating triage decisions, integrating every hospital system, a polished multi-ward rollout. Say what would be needed to do them later.
- Weekly demos to the sponsor; a written risk log (data delays, adoption).
""",
        "tradeoffs": [
            "Starting with the model instead of the baseline and the metric.",
            "Choosing a clinically risky use case for a 6-week pilot.",
            "No plan B if data access slips (it usually does).",
            "Building for every ward before one ward loves it.",
        ],
    },
    {
        "id": "demo-hallucination",
        "title": "It hallucinates in front of the client",
        "level": "Incident",
        "brief": "In the weekly demo, the assistant you deployed cites a building regulation that doesn't exist. The client's head of legal is in the room. What do you do, in the room and after?",
        "clarify": [
            "Is this a one-off, or does it happen on other questions? Do we have the trace (retrieved documents, prompt, model version)?",
            "Is the assistant live with real users, or only in the demo environment?",
            "What did the user see: a fake citation, or a wrong answer with a real citation?",
        ],
        "requirements": """
- **Ownership and composure:** do you acknowledge the problem plainly, without blaming the model or getting defensive?
- **Debugging method:** can you find the root cause from evidence (retrieval vs generation vs data)?
- **Prevention:** do you turn it into a systemic fix and a test?
""",
        "design": """
- **In the room:** acknowledge it directly ("That citation is wrong, and that's exactly what we must prevent"), note the input, and commit to a root cause and plan by a specific time. Don't improvise a fix live.
- **Contain:** if users are live, add a guardrail now (block answers whose citations aren't in the retrieved set, or show "unable to answer").
- **Root cause from the trace:** did retrieval return the right documents? Did the model cite something not in its context? Is the regulation missing from the index?
- **Fix:** constrain citations to retrieved chunk ids and verify them programmatically; improve retrieval if it missed; add the case and its variants to the eval set; re-run evals.
- **Report back:** a short written incident note: what happened, impact, fix, how we'll detect it next time.
""",
        "tradeoffs": [
            "Blaming \"LLMs hallucinate\" instead of owning the system.",
            "Promising it will never happen again; promise detection and mitigation instead.",
            "Fixing the prompt without adding a test, so it regresses next month.",
        ],
    },
    {
        "id": "air-gapped",
        "title": "Security says: nothing leaves the building",
        "level": "Constraints",
        "brief": "Two weeks into an engagement, the client's IT security team rules that no data may leave their on-prem network, and the servers have no internet access. Your design used a hosted LLM API. What now?",
        "clarify": [
            "Is the rule about the raw data, or about any derived data (embeddings, redacted text)?",
            "Are approved sovereign or in-country cloud regions an option, or strictly on-prem?",
            "What hardware is available on-prem (GPUs?), and how long does procurement take?",
            "Who can grant exceptions, and what evidence would they need?",
        ],
        "requirements": """
- Do you treat the constraint as **real**, not an obstacle to argue away?
- Do you know the **deployment options** for models and their trade-offs?
- Can you **re-plan** the project and communicate the impact clearly?
""",
        "design": """
- Lay out options with trade-offs: (1) an in-country managed model endpoint if policy allows; (2) open-weights models on on-prem GPUs; (3) a hybrid where only redacted or synthetic data leaves, if approved.
- For on-prem: model size vs available GPUs, an inference server, offline model and package delivery (artifact mirrors), updates through their change process.
- Re-run the eval set on the candidate model to quantify the quality gap before committing.
- Re-plan: timeline impact, what can proceed now (data pipeline, UI, evals), what's blocked. Communicate it to the sponsor in writing with a recommendation.
""",
        "tradeoffs": [
            "Trying to talk security out of the rule.",
            "Assuming a smaller local model performs the same, without measuring.",
            "Stalling the whole project instead of parallelizing unblocked work.",
        ],
    },
    {
        "id": "scope-creep",
        "title": "Five new features before Friday",
        "level": "Stakeholders",
        "brief": "The pilot launches next Friday. The client's director asks for five new features, \"must-haves for launch.\" Your team can do maybe one. How do you handle it?",
        "clarify": [
            "What's driving the request? Who asked for each feature, and what happens at launch without it?",
            "Is the date fixed by something external (a minister's visit, a contract)?",
            "Which of the five affect the agreed success metric?",
        ],
        "requirements": """
- Can you **say no constructively** while keeping the relationship strong?
- Do you tie decisions back to the **agreed goal**?
- Do you make the trade-off **explicit and the client's decision**?
""",
        "design": """
- Understand before answering: the underlying need behind each request is often smaller than the feature.
- Show the trade-off: "We can do one of these safely by Friday. Adding more puts the launch quality at risk. Here's what each costs."
- Recommend: the one feature that most affects the success metric, plus low-cost workarounds for others (a manual process, a config change), plus the rest scheduled for the next iteration with dates.
- Confirm in writing what's in and out for Friday.
""",
        "tradeoffs": [
            "Saying yes to everything and missing the date or shipping something broken.",
            "Flat no without understanding why they asked.",
            "Making the decision for the client instead of with them.",
        ],
    },
    {
        "id": "explain-accuracy",
        "title": "\"Is 92% accurate good enough?\"",
        "level": "Communication",
        "brief": "A minister asks you: \"Your system is 92% accurate. Is that good enough to go live?\" Answer for a non-technical audience.",
        "clarify": [
            "92% of what: documents, fields, decisions? Measured on which data?",
            "What happens in the 8%: a reviewer catches it, or a citizen is harmed?",
            "What's the accuracy of the current human process?",
        ],
        "requirements": """
- Can you explain **errors in terms of consequences**, not percentages?
- Do you compare to the **real baseline** (today's process), not to perfection?
- Do you propose **safeguards** that make the answer "yes, with conditions"?
""",
        "design": """
- Reframe: "It depends on what happens when it's wrong." Distinguish errors a reviewer catches from errors that reach citizens.
- Compare to today: "Today's manual process gets about X% right and takes Y days."
- Break down the 8%: which cases fail, and can those be routed to humans automatically (low confidence goes to manual review)?
- Recommend: go live in **assist mode** with human approval, monitor the error types weekly, expand automation where measured accuracy is high.
""",
        "tradeoffs": [
            "Answering with jargon (precision, F1) instead of consequences.",
            "Saying \"yes\" or \"no\" without conditions.",
            "Not knowing how the 92% was measured.",
        ],
    },
    {
        "id": "prove-roi",
        "title": "Prove it saved money",
        "level": "Impact",
        "brief": "Six months after deploying a supply-chain forecasting model at an energy company, the CFO asks: \"Did this actually save us money?\" How do you answer, and what should you have done at the start?",
        "clarify": [
            "What was the baseline before deployment, and was it recorded?",
            "What else changed in those six months (prices, demand, suppliers)?",
            "Were recommendations actually followed? Where, and where not?",
        ],
        "requirements": """
- Do you understand **attribution**: separating the model's effect from everything else?
- Do you know the **experiment designs** that make it measurable?
- Can you present a **credible, honest** number?
""",
        "design": """
- Compare like with like: sites or product lines that used the recommendations vs those that didn't, before vs after (difference in differences), controlling for price changes.
- Measure the mechanism too: forecast error vs the old method, stock-outs, excess inventory, expedited shipping costs.
- Present a range with assumptions stated, not one heroic number.
- At the start: agree the metric and baseline, roll out in stages (or A/B by site) so there's a comparison group, and log when recommendations are overridden.
""",
        "tradeoffs": [
            "Claiming all savings for the model.",
            "No baseline recorded at launch.",
            "Ignoring adoption: a model nobody follows saves nothing.",
        ],
    },
]
