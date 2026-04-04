# Contract Benchmarking App — Build Milestones

---

## Tech Stack

**Frontend:** Next.js / React / TypeScript
**Backend:** Python / FastAPI
**AI:** Anthropic SDK + LangChain (agentic loop)
**Structured output:** Pydantic models via instructor
**Local only:** No deployment. Smooth local boot is a priority.

**Repo structure:**

```
/frontend   → Next.js app
/backend    → FastAPI server
Makefile    → `make install` and `make dev` boot both servers
.env.example → all required keys documented
```

---

## Build Sequence & Timeboxes

| Step | Focus                                                                       | Time    |
| ---- | --------------------------------------------------------------------------- | ------- |
| [1]  | MVP end-to-end: upload → direct Anthropic call → render structured response | 1 hr    |
| [2]  | UI: clause index, detail drawer, topline header                             | 3 hrs   |
| [3]  | Agentic loop: replace single call with multi-pass LangChain pipeline        | 5 hrs   |
| [4]  | Polish UX/UI                                                                | Overage |

**Critical constraint:** Lock the output schema in [1] and don't break it in [3]. The UI is built against the schema — if the loop changes it, you're doing rework.

---

## Milestone 0 — Training Data ✓

Generate 5 synthetic SaaS MSAs + `training_labels.json` via Cowork.

| File                          | Description                                                                            |
| ----------------------------- | -------------------------------------------------------------------------------------- |
| `contract_1_clean.txt`        | Market-standard baseline, no issues                                                    |
| `contract_2_egregious.txt`    | Single issue: hyperlinked DPA (severity: Egregious)                                    |
| `contract_3_nonstandard.txt`  | 1–2 non-standard but fair terms                                                        |
| `contract_4_minor_issues.txt` | 4+ accumulated minor issues, none individually alarming                                |
| `contract_5_mixed.txt`        | Hyperlinked DPA + minor issues + unilateral mod clause + vendor co-ownership of output |

`training_labels.json` schema per issue:

```json
{
  "clause": "Data Processing",
  "issue": "DPA incorporated by hyperlink rather than attached exhibit",
  "issue_type": "incorporated_by_reference",
  "severity": "egregious",
  "market_standard": "DPA should be attached as a signed exhibit or schedule",
  "explanation": "..."
}
```

---

## Milestone 1 — MVP End-to-End (1 hr)

Upload contract → single direct Anthropic API call → render structured response in UI.

Goal is proving the full flow works and locking the output schema. No agentic loop yet. The schema defined here is the contract everything downstream is built against.

**Output schema per clause:**

```json
{
  "section_number": "§7.2",
  "clause_type": "Data Processing",
  "purpose": "Determines whether you can get your data back after termination.",
  "fairness": "egregious",
  "market_standard": "DPA should be attached as a signed exhibit",
  "explanation": "The DPA is incorporated by hyperlink and can be changed unilaterally mid-contract."
}
```

**Topline output:**

```json
{
  "overall_fairness": "egregious",
  "summary": "1 dealbreaker, 2 negotiating points, 4 acceptable clauses.",
  "call_to_action": [
    "§7.2 Data Processing — do not sign without resolving",
    "§12.1 Termination — push back",
    "§9 Indemnification — worth negotiating"
  ],
  "clauses": [...]
}
```

---

## Milestone 2 — Core UX: Clause Index (3 hrs)

The clause index table is the app. Everything else supports it.

**Topline header:**

- Contract name / upload date
- Overall fairness badge (🔴 Egregious / 🟡 Unfair / 🟢 Fair)
- Call to action: "3 clauses need your attention — 1 is a dealbreaker"

**Clause index table — each row:**

| Section | Purpose                                       | Fairness     |
| ------- | --------------------------------------------- | ------------ |
| §7.2    | Determines whether you can get your data back | 🔴 Egregious |

**Interaction:**

- Click a row → detail drawer/panel opens
- Detail shows: clause type, market standard, what this contract does, why it's a problem, suggested fix

**Scoring tiers:**

- 🟢 **Fair** — market standard or better
- 🟡 **Unfair** — non-standard, worth negotiating
- 🔴 **Egregious** — dealbreaker, do not sign without resolving

**Topline score rule:** Topline = worst clause. One Egregious clause = Egregious contract. Never average.

**CTA format:** Prioritized and opinionated, not a flat checklist.

- Lead with dealbreakers
- Then negotiating points
- Then acceptable items

---

## Milestone 3 — Agentic Evaluation Loop (5 hrs)

Replace the single Anthropic call with a multi-pass LangChain pipeline. Schema stays identical — UI should not need changes.

**The core problem with one-shot structured output:** the model returns valid JSON but the judgments inside are unreliable. It will hallucinate market standards, miss clauses, or confidently mislabel severity. Structure is reliable, reasoning isn't. The loop fixes this by making each step narrow enough that the model can't bullshit its way through it.

**Pipeline passes:**

- **Extract** — "List every clause with its section number and one-sentence description." No judgment. Just inventory.
- **Classify** — For each clause independently: clause type + purpose from customer perspective. Still no judgment.
- **Benchmark** — For each clause independently: compare against market standard, assign fairness tier. Training labels used as grounding context here.
- **Verify** — Tool call that checks output against known red flag patterns from `training_labels.json`. Second pass that can contradict and override the benchmark pass.
- **Synthesize** — Topline score (worst clause wins), CTA, prioritized recommendations.

**Why the verify step matters:** The model doesn't know what it doesn't know. It fills gaps confidently. The verify pass uses your ground truth training data as a structured check — not just another LLM call, but pattern-matching against known issues.

**Risks to handle:**

- Section number not reliably extractable → fall back to clause type name
- Purpose field defaults to neutral legal paraphrase → prompt must force customer-perspective plain English ("Determines whether you can get your data back" not "Governs vendor data handling obligations")

---

## Milestone 4 — UX/UI Polish (overage)

Timebox hard. Use a component library, don't build from scratch.

- Clean upload screen (drag and drop)
- Loading/streaming state while evaluation runs
- Responsive layout: header → CTA → clause index → detail panel
- Consistent color coding for fairness tiers throughout

---

## Key Product Decisions (for write-up)

1. **Benchmarking not summarizing** — answers "is this normal?" not "what does this say?"
2. **Tier scoring not numeric** — avoids false precision, maps to how lawyers actually think
3. **Topline = worst clause** — one Egregious clause makes the contract Egregious, never average
4. **CTA is opinionated** — prioritized advice, not a checklist
5. **Clause index as primary UX** — mirrors how lawyers already read redline summaries and playbook outputs
6. **Section + purpose + fairness** — three columns, scannable, no brittle text highlighting
7. **Agentic loop over one-shot** — structured output is reliable, reasoning inside it isn't; multi-pass with verification fixes this

---

## Reference Sources

- GC AI product demo: https://gc.ai/blog/founder-and-ceo-cecilia-ziniti-s-under-nda-product-demo
- Above the Law case study: https://abovethelaw.com/2026/03/ai-vendor-contracts-the-terms-and-conditions-trap/
