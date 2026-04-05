# Step: eval-prompt

> Part of: [plan.md](../plan.md) · Spec: [spec.md](../spec.md)

## What This Step Delivers

The evaluation system prompt in its own folder at `frontend/prompt/`. This is the core instruction set sent to Claude. It tells the model to: (1) determine if the input is a contract (biasing toward accepting), (2) if not, return the `EvalError` schema, (3) if so, analyze each clause and return the `EvalSuccess` schema with fairness tiers. The existing prompt at `docs/gc-ai-takehome/contract_eval_prompt.md` is used as reference only — this is a new prompt designed for the M1 output schema.

## Done When

- `frontend/prompt/system-prompt.ts` exports `SYSTEM_PROMPT` as a string
- The prompt includes the full JSON schema for both success and error responses
- The prompt defines the three fairness tiers (fair / unfair / egregious)
- The prompt includes the "worst clause wins" topline rule
- The prompt instructs Claude to bias toward accepting borderline input
- The prompt requires customer-perspective plain English for the `purpose` field
- Unit tests verify the prompt contains required structural elements

## Cycles

### prompt-structure

**Test** — write these tests in `frontend/__tests__/prompt.test.ts` and confirm they fail:
- **SYSTEM_PROMPT is a non-empty string**: import `SYSTEM_PROMPT` from `@/prompt` → assert it is a string with length > 0
- **prompt contains JSON schema for success response**: assert `SYSTEM_PROMPT` includes `"overall_fairness"`, `"call_to_action"`, `"clauses"`
- **prompt contains JSON schema for error response**: assert `SYSTEM_PROMPT` includes `"error": true` and `"reason"`
- **prompt defines all three fairness tiers**: assert `SYSTEM_PROMPT` includes `fair`, `unfair`, `egregious`
- **prompt includes worst-clause-wins rule**: assert `SYSTEM_PROMPT` includes a reference to worst clause determining the topline score

**Code** — Create `frontend/prompt/system-prompt.ts` exporting `SYSTEM_PROMPT`. Create `frontend/prompt/index.ts` as barrel export.

The prompt should:
1. Open with role: "You are a senior in-house commercial lawyer reviewing a vendor contract."
2. **Gate check first**: "Before analyzing, determine if this text is a contract or legal agreement. If it clearly is not (e.g., a recipe, article, resume), return:" followed by the `EvalError` JSON example. "When in doubt, treat the input as a contract and proceed with analysis."
3. **Analysis instructions**: For each clause, produce the `EvalClause` fields. Require `purpose` to be written in plain English from the customer's perspective ("Determines whether you can get your data back" not "Governs vendor data handling obligations").
4. **Fairness tiers**: Define fair (market standard or better), unfair (non-standard, worth negotiating), egregious (dealbreaker, do not sign without resolving).
5. **Topline rule**: "The `overall_fairness` is the worst fairness tier among all clauses. One egregious clause makes the entire contract egregious. Never average."
6. **Output format**: Show the full `EvalSuccess` JSON schema with field descriptions.
7. **Constraint**: "Return only valid JSON. No text outside the JSON object."

**Refactor** — none

**Commit**: `Add evaluation system prompt in frontend/prompt/`

---

## LLM Verification

The prompt itself can be verified by inspection and by testing against training contracts in the api-route step. At this step, verification is limited to structural tests.

**N/A** — no external surface; prompt content tested via unit tests. Real contract testing happens in the api-route verify step.
