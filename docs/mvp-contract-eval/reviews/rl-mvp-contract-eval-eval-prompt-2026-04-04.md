## Review: eval-prompt (commit f244be0 + simplify changes)
## Date: 2026-04-04

---

### Standard Review

#### Bugs
- **route.ts:35** — `JSON.parse` failure on non-JSON LLM response collapses into generic 500, indistinguishable from network/API errors · `[Dismissed — belongs to api-route step, not eval-prompt]`
- **route.ts:30** — `message.content[0]` accessed without bounds check · `[Dismissed — belongs to api-route step]`

#### Contract Violations
- **route.ts:35-36** — `EvalResponseSchema` never applied to validate model output before returning to client · `[Dismissed — belongs to api-route step; noted for that review]`
- **prompt/system-prompt.ts** — Success schema emits `"type": "null"` for error field vs `"const": null` — minor LLM legibility asymmetry with error schema's `"const": true` · `[Speculative — z.toJSONSchema output is correct JSON Schema; model quality risk is low]`

#### Edge Cases
- **prompt** — "Death by paper cuts" rule (>10% non-standard) is prompt-only, not enforced deterministically · `[Dismissed — inherent to prompt-engineering approach; deterministic override is out of MVP scope]`

---

### Edge Case Hunter

- **system-prompt.ts:4** — `z.toJSONSchema()` unavailable or throws at module load → server crashes · `[Dismissed — z.toJSONSchema is stable in Zod v4 (4.3.6 installed); these schemas use standard Zod primitives]`
- **system-prompt.ts:4** — `z.toJSONSchema` returns circular reference → `JSON.stringify` throws · `[Dismissed — Zod JSON Schema output does not produce circular refs for flat object schemas]`
- **system-prompt.ts:42-43** — `z.toJSONSchema` returns undefined → template interpolates "undefined" · `[Dismissed — z.toJSONSchema returns an object or throws; it does not return undefined]`

---

### Adversarial

1. **route.ts:35-36** — No Zod validation on model output before returning · `[Dismissed — api-route step]`
2. **route.ts:35** — JSON.parse failure indistinguishable from other errors · `[Dismissed — api-route step]`
3. **route.ts:37** — Bare catch swallows errors with no logging · `[Dismissed — api-route step]`
4. **system-prompt.ts:4-5** — z.toJSONSchema baked at module load; HMR may not refresh · `[Dismissed — module-level constants are standard Next.js pattern; schema changes require restart which is expected]`
5. **system-prompt.ts:25** — Dealbreaker definition references user-flagged preferences that don't exist yet · `[Valid — the prompt references a feature (user flagging clause importance) that has no mechanism in the current flow]`
6. **route.ts:13-16** — No token-count guard on input · `[Dismissed — api-route step]`
7. **route.ts:23-28** — max_tokens: 4096 may truncate large contracts · `[Dismissed — api-route step]`
8. **system-prompt.ts:31** — Death by paper cuts rule is prompt-only · `[Dismissed — same as edge case above]`
9. **types.ts:5-12** — section_number has no format constraint · `[Dismissed — free-form string by design; sorting/dedup is M2]`
10. **types.ts:14-19** — LLMs may omit `error` key rather than set to null · `[Speculative — valid concern but prompt explicitly shows the schema with error:null; Zod validation at api-route layer (when added) will catch this]`
11. **system-prompt.ts:7** — "Customer perspective" framing not disclosed to user · `[Speculative — UI disclaimer is M2 scope; the prompt is correct for the intended use case]`
12. **route.ts:20-21** — No startup check for ANTHROPIC_API_KEY · `[Dismissed — api-route step]`

---

## Summary

**One valid finding for eval-prompt scope:**

The dealbreaker definition (line 25) says "if the user flagged really wanting standard or beneficial terms for a clause, or flagged a clause as very important" — but there's no mechanism for users to flag clause importance. This could confuse the model by referencing nonexistent input.

Many findings (1-3, 6-7, 12) belong to the api-route step and will be addressed in that review.

---

## Reviewer Validity

| Reviewer | Findings | Unique | Overlap | Verdict |
|---|---|---|---|---|
| Standard | 5 | 1 (null vs const asymmetry) | 3 | Useful — but mostly flagged api-route issues |
| Edge Case Hunter | 4 | 3 (module-load paths) | 0 | Low value — all dismissed; z.toJSONSchema concerns unfounded for Zod v4 |
| Adversarial | 12 | 2 (user-flagging gap, customer framing) | 5 | Useful — found the valid prompt-content issue; high noise from api-route scope bleed |

**Notes:** Scope bleed was the dominant pattern — reviewers flagged route.ts issues that belong to the api-route step. The one valid eval-prompt finding (user-flagging reference) was unique to the adversarial reviewer.
