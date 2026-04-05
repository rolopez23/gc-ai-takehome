# Plan: MVP Contract Evaluation

> Spec: [docs/mvp-contract-eval/spec.md](spec.md)

## Status Dashboard

| Step                                                       | Blocks                          | Branch / Commit | Auto Tests | Verify | Simplify | Review | Understand | Human |
| ---------------------------------------------------------- | ------------------------------- | --------------- | :--------: | :----: | :------: | :----: | :--------: | :---: |
| [eval-schema](steps/eval-schema.md)                        | eval-prompt, api-route          | `2a41d33`       |     ✅     |   ➖   |    ✅    |   ✅   |     ✅     |  ✅   |
| [eval-prompt](steps/eval-prompt.md)                        | api-route                       | `f244be0`       |     ✅     |   ✅   |    ✅    |   ✅   |     ✅     |  ✅   |
| [api-route](steps/api-route.md)                            | loading-shimmer, error-display  | `c018cdf`       |     ✅     |   ✅   |    ✅    |   ✅   |     ✅     |  ✅   |
| [loading-shimmer](steps/loading-shimmer.md)                | success-navigation              | —               |     ✅     |   ✅   |    ✅    |   ✅   |     ✅     |  ✅   |
| [error-display](steps/error-display.md)                    | —                               | —               |     ✅     |   ✅   |    ✅    |   ✅   |     ✅     |  ✅   |
| [success-navigation](steps/success-navigation.md)          | cancel-on-unmount               | —               |     ⬜     |   ⬜   |    ⬜    |   ⬜   |     ⬜     |  ⬜   |
| [cancel-on-unmount](steps/cancel-on-unmount.md)            | —                               | —               |     ⬜     |   ➖   |    ⬜    |   ⬜   |     ⬜     |  ⬜   |

**Legend:** ⬜ pending · ✅ passed · ❌ failed · ⚠️ incomplete · ➖ N/A

**Workflow order per step:** Auto Tests → Verify → Simplify → Review → Understand → Human

- **Auto Tests**: unit/integration tests passing (red-green-refactor, committed clean)
- **Verify**: E2E check — real curl or browser automation against a live system; ➖ if no external surface
- **Simplify**: code has been through a simplify/refactor pass
- **Review**: correctness review — bugs, edge cases, error handling
- **Understand**: human passes `/pr-interactive-walkthrough` — all files rated Medium or High
- **Human**: developer has manually signed off

**On failure:** ❌ in any column requires fixes before proceeding.

---

## Branching Strategy

Single feature branch. Steps are tightly sequential and small — commits per step, no need for per-step branches. Each step ends with a green commit.

---

## File Map

```
Create:  frontend/app/evaluate-contract/types.ts                — Shared TypeScript types for eval response schema
Create:  frontend/prompt/system-prompt.ts                       — Evaluation system prompt (own folder, will move later)
Create:  frontend/prompt/index.ts                               — Barrel export
Create:  frontend/app/api/evaluate/route.ts                     — Next.js API route: proxy to Anthropic Messages API
Create:  frontend/app/evaluate-contract/eval-result-context.tsx  — React context for storing eval results by UUID
Create:  frontend/app/contract/[id]/page.tsx                    — Minimal results page (success/error display)
Create:  frontend/__tests__/types.test.ts                       — Type guard tests
Create:  frontend/__tests__/prompt.test.ts                      — Prompt structure/content tests
Create:  frontend/__tests__/api-evaluate.test.ts                — API route unit tests
Create:  frontend/__tests__/loading-shimmer.test.tsx            — Loading state tests
Create:  frontend/__tests__/error-display.test.tsx              — Error display tests
Create:  frontend/__tests__/success-navigation.test.tsx         — Navigation + results page tests
Create:  frontend/__tests__/cancel-on-unmount.test.tsx          — Request cancellation tests
Modify:  frontend/app/evaluate-contract/validation.ts           — Narrow ALLOWED_EXTENSIONS to .txt
Modify:  frontend/app/evaluate-contract/FileDropZone.tsx        — Update accepted extensions display
Modify:  frontend/app/evaluate-contract/page.tsx                — Wire submit, loading, error, navigation
Modify:  frontend/app/layout.tsx                                — Wrap with EvalResultContext provider
Modify:  frontend/package.json                                  — Add @anthropic-ai/sdk
Modify:  .env                                                   — Add ANTHROPIC_MODEL
```

---

## Steps

### eval-schema

TypeScript types for the evaluation response schema (success and error shapes), type guard functions, and narrowing `ALLOWED_EXTENSIONS` to `.txt` only. No API calls, no UI changes. Foundation everything else imports.

[→ Detailed plan](steps/eval-schema.md)

### eval-prompt

The evaluation system prompt in its own folder at `frontend/prompt/`. Instructs Claude to return structured JSON matching the output schema, detect non-contract input (biasing toward accepting), and apply the fairness tier system. Tested for structure and key content. Uses the existing prompt at `docs/gc-ai-takehome/contract_eval_prompt.md` as reference only.

[→ Detailed plan](steps/eval-prompt.md)

### api-route

Thin Next.js API route at `/api/evaluate`. Receives contract text via POST, imports the prompt from `frontend/prompt/`, calls Anthropic's Messages API server-side, returns structured JSON. Configurable model via `ANTHROPIC_MODEL` env var. Tested with mocked Anthropic SDK.

[→ Detailed plan](steps/api-route.md)

### loading-shimmer

Skeleton shimmer loading state on the evaluate-contract page while the API call is in flight. The Evaluate button is disabled during the call. First step that modifies the page — wires up the real `fetch` to `/api/evaluate` and manages `isLoading` state.

[→ Detailed plan](steps/loading-shimmer.md)

### error-display

"Something went wrong. Try again." shown inline on the evaluate-contract page when the API call fails for any reason (network error, 500, non-contract detection). Error clears on retry.

[→ Detailed plan](steps/error-display.md)

### success-navigation

On successful evaluation: generate a UUID, store the result in a React context, and navigate to `/contract/[uuid]`. Creates the `EvalResultContext` provider and the minimal results page that reads from it.

[→ Detailed plan](steps/success-navigation.md)

### cancel-on-unmount

Cancel the in-flight `/api/evaluate` request when the user navigates away from the evaluate-contract page. Uses `AbortController` with the existing fetch call.

[→ Detailed plan](steps/cancel-on-unmount.md)
