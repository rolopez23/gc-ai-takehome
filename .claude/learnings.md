# Learnings Log

### 2026-04-04 · contract-upload-ui/file-validation

**Category**: Human correction
**Error class**: Context
**What happened**: After completing auto tests for Step 1, skipped simplify/review/understand/human sign-off and jumped directly into Step 2 implementation. User had to intervene: "Can we respect the workflow?"
**Where it surfaced**: Human review
**Pattern tag**: `workflow-steps-skipped`

### 2026-04-04 · contract-upload-ui/file-validation

**Category**: Human correction
**Error class**: Context
**What happened**: After human sign-off, attempted to move directly to Step 2 without running /learn-from-mistakes. User corrected: the order is sign-off → learn → next step.
**Where it surfaced**: Human review
**Pattern tag**: `workflow-steps-skipped`

### 2026-04-04 · contract-upload-ui/file-validation

**Category**: Human correction
**Error class**: Context
**What happened**: Plan dashboard was not updated after completing auto tests. User had to point out the plan showed all ⬜ despite Step 1 being done.
**Where it surfaced**: Human review
**Pattern tag**: `plan-not-updated`

### 2026-04-04 · contract-upload-ui/file-validation

**Category**: Human correction
**Error class**: Prompt
**What happened**: Used explicit `: boolean` return types on obvious validation functions. User preferred implicit types when the return is self-evident, and wanted a rule added to AGENTS.md.
**Where it surfaced**: PR walkthrough (human review)
**Pattern tag**: `typescript-style-mismatch`

### 2026-04-04 · contract-upload-ui/file-drop-zone

**Category**: Human correction
**Error class**: Skill
**What happened**: Tests used `document.querySelector('input[type="file"]')` instead of RTL's `screen.getByLabelText`. Neither simplify nor review caught this anti-pattern.
**Where it surfaced**: PR walkthrough (human review)
**Pattern tag**: `rtl-query-antipattern`

### 2026-04-04 · contract-upload-ui/file-drop-zone

**Category**: Human correction
**Error class**: Skill
**What happened**: Tests had unnecessary `as HTMLInputElement` type casts on RTL queries where the consuming API accepts `HTMLElement`. Simplify and review did not flag this.
**Where it surfaced**: PR walkthrough (human review)
**Pattern tag**: `unnecessary-type-cast`

### 2026-04-04 · contract-upload-ui/file-drop-zone

**Category**: Human correction
**Error class**: Context
**What happened**: Test comments explained what the code already showed (e.g., "Use fireEvent to bypass the accept attribute filtering"). User flagged as noise — and noted that walkthrough questions matching comments aren't real comprehension tests.
**Where it surfaced**: PR walkthrough (human review)
**Pattern tag**: `unnecessary-comments`

### 2026-04-04 · contract-upload-ui/upload-page

**Category**: Implementation hole
**Error class**: Specification
**What happened**: Spec and plan did not mention clearing form state after submit. User caught during sign-off that handleSubmit should reset file and instructions. Neither review nor simplify flagged this gap.
**Where it surfaced**: Human sign-off
**Pattern tag**: `missing-reset-after-action`

### 2026-04-04 · contract-upload-ui/upload-page

**Category**: Skill gap
**Error class**: Skill
**What happened**: After adding form reset, a mixed controlled/uncontrolled pattern was introduced in FileDropZone (both internal stagedFile state and external file prop). The first simplify pass did not run on this change — user had to explicitly request a re-run. The re-run correctly identified and fixed the dead state.
**Where it surfaced**: Human-requested simplify re-run
**Pattern tag**: `simplify-not-rerun-after-fix`

### 2026-04-04 · mvp-contract-eval/eval-schema + eval-prompt

**Category**: Human correction
**Error class**: Context
**What happened**: Plan dashboard marked all workflow columns (Verify, Simplify, Review, Understand, Human) as ✅ for steps 1-3 when none of that work had been done. User caught it immediately.
**Where it surfaced**: Human review
**Pattern tag**: `plan-not-updated`

### 2026-04-04 · mvp-contract-eval/eval-schema

**Category**: Human correction
**Error class**: Skill
**What happened**: User disliked `as` type casts in type guards. Neither simplify nor review flagged the cast pattern as a smell — simplify only changed from `as EvalSuccess` to `as { error: unknown }`, still using casts. User drove the Zod migration which eliminated casts entirely.
**Where it surfaced**: PR walkthrough (human review)
**Pattern tag**: `unnecessary-type-cast`

### 2026-04-04 · eval-results-display/topline-score

**Category**: Skill gap
**Error class**: Skill
**What happened**: Inherited `as EvalSuccess | undefined` cast from M1 stub was not flagged during initial page read. The cast silently skipped the `EvalError` variant, meaning error responses would render broken UI instead of the fallback. Correctness review caught it, but I should have noticed it when first reading the file — this is the same `as` cast anti-pattern flagged twice before.
**Where it surfaced**: Review step (correctness reviewer)
**Pattern tag**: `unnecessary-type-cast`

### 2026-04-04 · mvp-contract-eval/eval-schema

**Category**: Human correction
**Error class**: Specification
**What happened**: User proposed migrating hand-rolled type guards to Zod schemas for cleaner validation and single-source-of-truth types. No automated step suggested this architectural improvement despite it being a natural fit for parsing untrusted LLM output.
**Where it surfaced**: PR walkthrough (human review)
**Pattern tag**: `missed-architectural-improvement`

### 2026-04-04 · mvp-contract-eval/eval-prompt

**Category**: Human correction
**Error class**: Specification
**What happened**: User changed prompt scoring language from fair/unfair/egregious to fair/non-standard/dealbreaker to avoid biasing the LLM toward plain-English interpretations. Also added death-by-paper-cuts rule and expanded dealbreaker definition. No automated step considered prompt-level LLM bias.
**Where it surfaced**: Human review (user edited file directly)
**Pattern tag**: `prompt-bias-not-considered`

### 2026-04-04 · mvp-contract-eval/eval-prompt

**Category**: Human correction
**Error class**: Context
**What happened**: /learn-from-mistakes skipped again after eval-prompt sign-off. User had to remind: "two things one we missed the learning step again." This is the third occurrence of this pattern.
**Where it surfaced**: Human review
**Pattern tag**: `workflow-steps-skipped`

### 2026-04-04 · mvp-contract-eval/eval-prompt

**Category**: Skill gap
**Error class**: Skill
**What happened**: Verification script took 5+ failed attempts — wrong import paths, CJS vs ESM issues, env var quoting, wrong working directory. Should have been a single well-tested script run from the right directory with correct module resolution.
**Where it surfaced**: Verify step
**Pattern tag**: `verify-script-thrashing`

### 2026-04-04 · mvp-contract-eval/eval-prompt

**Category**: Bad assumption
**Error class**: Context
**What happened**: Used claude-haiku-4-5-20251001 without checking its max_tokens limit (8192 output), then switched to claude-3-haiku which caps at 4096 output tokens. Did not research model constraints before running verification, wasting turns and API spend on a model that couldn't produce full contract evaluations.
**Where it surfaced**: Verify step
**Pattern tag**: `model-constraints-not-researched`

### 2026-04-04 · mvp-contract-eval/api-route

**Category**: Skill gap
**Error class**: Skill
**What happened**: Simplify pass fixed correctness issues (fence stripping, Zod validation, truncation check) but missed readability: inline validation, magic numbers (400, 422, 500, 8192), repeated `NextResponse.json({ error }, { status })` pattern ×6, and handler doing too much. User had to drive extraction of `errorResponse()`, `parseRequestBody()`, `buildMessages()`, and named constants.
**Where it surfaced**: PR walkthrough (human review)
**Pattern tag**: `simplify-missed-readability`

### 2026-04-04 · mvp-contract-eval/api-route

**Category**: Human correction
**Error class**: Context
**What happened**: Asked user "want me to run verify?" and "skip straight to walkthrough?" multiple times across steps. User corrected: "Always verify! Use the simple contract on haiku!" Verify should never be optional — always run it when there is a verifiable surface.
**Where it surfaced**: Human review
**Pattern tag**: `verify-not-automatic`

### 2026-04-04 · mvp-contract-eval/api-route

**Category**: Human correction
**Error class**: Context
**What happened**: Verification was run after Simplify and Review, but it should run immediately after tests pass (make it work → verify it works → make it clean → make it beautiful). The workflow order in the plan says Verify before Simplify, but the agent kept deferring verification to later or asking if it should be skipped. Prime directive: make it work, make it work well, make it beautiful.
**Where it surfaced**: Human review
**Pattern tag**: `verify-out-of-order`

### 2026-04-04 · mvp-contract-eval/api-route (self-reflection)

**Category**: Skill gap
**Error class**: Context
**What happened**: Verification script thrashed through 5+ attempts due to ESM/CJS confusion, wrong import paths, env var quoting, and wrong working directory. Should have used a simple `node -e` from the `frontend/` dir with `require()` from the start, since the SDK is a CJS dependency installed there. Wasted ~10 turns and API spend.
**Where it surfaced**: Self-review of conversation history
**Pattern tag**: `verify-script-thrashing`

### 2026-04-04 · mvp-contract-eval/api-route (self-reflection)

**Category**: Bad assumption
**Error class**: Context
**What happened**: Asked "want me to run verify?" and "skip to walkthrough?" instead of just doing it. The workflow order is explicit — verify comes after tests, always. Asking permission for a mandatory step wastes a turn and signals uncertainty about the process.
**Where it surfaced**: Self-review of conversation history
**Pattern tag**: `asking-permission-for-mandatory-steps`

### 2026-04-04 · mvp-contract-eval/loading-shimmer

**Category**: Human correction
**Error class**: Context
**What happened**: Verification returned 500 because ANTHROPIC_API_KEY wasn't in frontend/.env.local. Agent said "the 500 is expected" — user corrected: "a 500 is never expected." Environment must be properly configured before verification.
**Where it surfaced**: Verify step
**Pattern tag**: `env-not-configured`

### 2026-04-04 · mvp-contract-eval/loading-shimmer

**Category**: Human correction
**Error class**: Context
**What happened**: Ran /frontend-design to improve shimmer visually but marked Simplify as done. User caught it: "we did a frontend design not sure about true simplify." Frontend-design and simplify are different skills with different goals.
**Where it surfaced**: Human review
**Pattern tag**: `skills-conflated`

### 2026-04-04 · mvp-contract-eval/loading-shimmer

**Category**: Skill gap
**Error class**: Skill
**What happened**: isLoading was checked twice — once for role="status" text, once for shimmer/form swap. User identified the duplication and suggested moving accessibility into LoadingShimmer itself. Neither simplify nor review caught this.
**Where it surfaced**: PR walkthrough (human review)
**Pattern tag**: `simplify-missed-readability`

### 2026-04-04 · mvp-contract-eval/loading-shimmer (self-reflection)

**Category**: Bad assumption
**Error class**: Context
**What happened**: Attempted useActionState refactor without verifying jsdom compatibility. Tests broke, tried useTransition, still broke — burned ~8 turns before user said "lets just undo." Should have validated the testing story in isolation before rewriting production code.
**Where it surfaced**: Self-review of conversation history
**Pattern tag**: `refactor-without-testing-validation`

### 2026-04-04 · mvp-contract-eval/loading-shimmer (self-reflection)

**Category**: Human correction
**Error class**: Context
**What happened**: Got derailed into useActionState experiment mid-walkthrough. Understand step was never completed. User had to point out: "We never completed understand uncheck it."
**Where it surfaced**: Human review
**Pattern tag**: `workflow-steps-skipped`

### 2026-04-04 · mvp-contract-eval/loading-shimmer

**Category**: Skill gap
**Error class**: Skill
**What happened**: No automated step considered ARIA/accessibility patterns. The review caught the live region mounting issue but only because the adversarial reviewer was casting a wide net. Simplify, standard review, and edge-case hunter all ignored accessibility. User noted this as a general gap — not a blocker for MVP but should be part of the review checklist.
**Where it surfaced**: Human review
**Pattern tag**: `accessibility-not-reviewed`

### 2026-04-05 · eval-results-display/all-steps (post-human)

**Category**: Skill gap
**Error class**: Skill
**What happened**: Simplify pass said "code is clean" on all three steps, but the human walkthrough drove 9 significant refactors: NoClauses extraction, ExpandableClauses (state-down), NoEvaluation/EvaluationResults extraction, semantic HTML (h4, section, article, ul/li), named class constants (BADGE_STYLING, SECTION_BORDER, etc.), semantic COLORS (fail/warning/pass), reduce instead of for-loop, aria-label/aria-expanded, and less brittle test assertions. The simplify skill has no frontend-specific checklist.
**Where it surfaced**: PR walkthrough (human review)
**Pattern tag**: `simplify-missed-frontend-cleanup`

### 2026-04-05 · eval-results-display/all-steps (post-human)

**Category**: Skill gap
**Error class**: Skill
**What happened**: Tests asserted on raw Tailwind class names (e.g., `toContain('text-red-600')`). Human flagged as brittle — should test against semantic constant names (`COLORS.fail`) or roles (`getByRole('list')`), not implementation details. Neither review nor simplify caught this.
**Where it surfaced**: PR walkthrough (human review)
**Pattern tag**: `brittle-style-assertions`

### 2026-04-05 · eval-results-display/all-steps (post-human)

**Category**: Human correction
**Error class**: Context
**What happened**: All M2 feature commits (20+) went directly to main instead of a feature branch. User had to point this out. AGENTS.md had main branch push protection but no rule requiring a feature branch before writing code.
**Where it surfaced**: Human review
**Pattern tag**: `committed-to-main`

### 2026-04-05 · eval-results-display/all-steps (post-human)

**Category**: Skill gap
**Error class**: Context
**What happened**: Verification was skipped on steps 2 and 3 despite both having browser-verifiable surfaces. The shimmer flicker bug was found by the user during manual E2E, not by the agent. AGENTS.md already had a rule that verify always runs after tests, but the "run independently" instruction was interpreted as license to skip it.
**Where it surfaced**: Human review
**Pattern tag**: `verify-not-automatic`

### 2026-04-05 · eval-results-display/all-steps (post-human)

**Category**: Skill gap
**Error class**: Skill
**What happened**: Missing aria-label on section elements, missing aria-expanded on toggle buttons, div-based clause list instead of ul/li. Neither simplify nor review flagged accessibility gaps. This is the second time accessibility has been missed across features.
**Where it surfaced**: PR walkthrough (human review)
**Pattern tag**: `accessibility-not-reviewed`

### 2026-04-05 · backend-eval-pipeline/all-steps

**Category**: Skill gap
**Error class**: Skill
**What happened**: Agent ran unit tests for all steps but skipped live verification (curl, DB inspection, browser) until user called it out: "are you doing independent verification?" This was immediately after updating the verify skill to say "never skip."
**Where it surfaced**: Human review
**Pattern tag**: `verification-skipped`

### 2026-04-05 · backend-eval-pipeline/step-9

**Category**: Missed edge case
**Error class**: Context
**What happened**: CORS used exact origin match. Frontend runs on random ports via portless. All 67 backend tests passed — test client bypasses CORS middleware. Only caught by browser verification.
**Where it surfaced**: Browser E2E verification
**Pattern tag**: `cors-not-tested`

### 2026-04-05 · backend-eval-pipeline/step-9

**Category**: Bad assumption
**Error class**: Context
**What happened**: Route path mismatch — spec said `/api/contracts/{id}/review` but implementation put endpoint on reviews router at `/api/reviews/contracts/{id}/review`. Frontend and backend tested independently.
**Where it surfaced**: Browser E2E verification
**Pattern tag**: `cross-boundary-contract-mismatch`

### 2026-04-05 · backend-eval-pipeline/step-9

**Category**: Bad assumption
**Error class**: Context
**What happened**: API key in root `.env` but not `backend/.env`. Agent's E2E worked (manually exported), user hit "auth failed" in normal usage.
**Where it surfaced**: Human review (user screenshot)
**Pattern tag**: `env-config-mismatch`

### 2026-04-05 · backend-eval-pipeline/step-2

**Category**: Missed edge case
**Error class**: Skill
**What happened**: `datetime.now(UTC)` (timezone-aware) vs `TIMESTAMP WITHOUT TIME ZONE`. SQLite tests passed, PostgreSQL rejected. Only caught by live DB verification.
**Where it surfaced**: Live DB verification
**Pattern tag**: `sqlite-vs-postgres-divergence`

### 2026-04-05 · backend-eval-pipeline/simplify

**Category**: Large refactor
**Error class**: Skill
**What happened**: Used synchronous `anthropic.Anthropic` inside `async` function, blocking event loop for up to 90s. Should have used `AsyncAnthropic`. Only caught by simplify.
**Where it surfaced**: Simplify (efficiency review)
**Pattern tag**: `sync-in-async`

### 2026-04-05 · backend-eval-pipeline/simplify

**Category**: Implementation hole
**Error class**: Context
**What happened**: DOC/DOCX converted at upload time AND again in background task. Double LibreOffice invocation.
**Where it surfaced**: Simplify (code reuse review)
**Pattern tag**: `duplicate-work`

### 2026-04-05 · backend-eval-pipeline/walkthrough

**Category**: Skill gap
**Error class**: Skill
**What happened**: Walkthrough rated Python concepts as High when user needed corrections on core mechanisms (deferred, from_attributes, selectinload). User flagged ratings as too generous.
**Where it surfaced**: Human review
**Pattern tag**: `walkthrough-calibration-inflated`

### 2026-04-05 · backend-eval-pipeline/walkthrough

**Category**: Skill gap
**Error class**: Skill
**What happened**: PR walkthrough covered 18 file groups across full milestone. Too large for deep comprehension — skill works better at step-level granularity.
**Where it surfaced**: Human review
**Pattern tag**: `walkthrough-scope-too-large`
