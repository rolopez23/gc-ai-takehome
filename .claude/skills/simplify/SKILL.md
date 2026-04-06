---
name: simplify
description: >
  Reviews staged changes or a branch diff and simplifies the code following XP Simple Design,
  Clean Code, and Martin Fowler refactoring principles. Applies clear improvements directly and
  suggests uncertain ones for human review. Biases toward silence — if a change isn't clearly
  better, don't make it or suggest it.
  Trigger when the user says "simplify", "clean this up", "refactor this", "is this the simplest
  solution", or when invoked as a subagent after staging and before committing. Also trigger when
  the plan dashboard's Simplify column needs to be updated.
---

# Simplify

You are reviewing code that is staged for commit (or on a branch) and asking one question: is
this the simplest correct solution? You are not adding features. You are not gold-plating. You
are removing everything that doesn't need to be there.

# Important

This skill can never touch tests. You can only refactor code covered by the tests.

## Verification Gate

Before running simplify, check that verification has been completed:

1. Look for a plan at `docs/<feature>/plan.md`. If one exists, check the Verify column for
   the current step — it must be ✅ or ➖ (N/A).
2. Look for a verification report at `docs/<feature>/verify/<step>-*.md`. If the plan shows
   Verify should have run, a report must exist.

**If the plan exists and Verify is still ⬜ (pending) with no report:**
Stop and say: "Verification has not been run for this step. Run `/verify` first — simplify
runs after verify in the workflow (make it work → make it work well → make it beautiful)."
Do not proceed with the simplify pass.

**If no plan exists** (ad-hoc simplify, not part of a step workflow): skip this gate.

## Sub-Skills

If the diff touches React components (`.tsx` files that export JSX), also run the frontend
cleanup sub-skill after the main simplify pass:
- [`sub-skills/frontend-cleanup.md`](sub-skills/frontend-cleanup.md) — component extraction,
  semantic HTML, accessibility, readable class names, data transformations, style constants

## Get the Diff

```bash
git diff --cached          # staged changes
# or for a branch:
git diff main...HEAD
```

Read the diff. Then read the full context of every file touched — don't judge code from a diff
alone, you need to see how it fits into the surrounding code.

## The Bias

**Prefer no changes.** A suggestion that turns out to be wrong wastes time and erodes trust.
Only flag something if you're confident it's better. If you're unsure whether a change is an
improvement, it isn't — leave it alone.

Applied to each candidate change, ask: "Would a skilled developer reading this code tomorrow
clearly agree this is better?" If the answer is yes, apply the change. If the answer is probably, flag, if the answer is maybe skip it.

## What to Look For

These are the categories worth catching, roughly in order of impact:

### 1. Dead Code

Unused variables, unreachable branches, commented-out code, methods that are never called.
Remove without hesitation — dead code has no defenders.

### 2. Duplication (DRY)

Identical or near-identical logic in two places. Extract it. The threshold: if you'd have to
make the same change in two places when requirements shift, it's worth extracting. One-time
similarity is fine — three or more is always worth addressing.

### 3. Unclear Names

A name that requires the reader to look at the implementation to understand what it does.
Rename to reveal intent. This includes variables, methods, classes, and parameters.
Good names make comments unnecessary.

### 4. Functions Doing Too Much (Single Responsibility)

A method that does setup, computation, and side effects. Split it. The heuristic: if you can't
describe what a function does without using "and", it should be split.

### 5. YAGNI Violations

Code that handles a case not required by the current tests or spec. Remove it. Future
requirements will arrive with tests; don't speculate.

### 6. Unnecessary Complexity

Abstraction for one use case. Indirection that adds layers without clarity. Configuration
where a constant would do. Inheritance where composition would be simpler. Simplify toward
the concrete.

### 7. Long Parameter Lists

More than 3 parameters is a smell. Consider a parameter object, or whether the method is
doing too much.

### 8. Conditional Complexity

Nested conditionals, repeated nil checks, boolean flag parameters. Consider guard clauses,
early returns, or (only when genuinely clearer) polymorphism.

### 9. Magic Numbers and Strings

Literals that appear without explanation. Replace with named constants.

### 10. Good naming

Make names human readable and the code should look like prose.

### 11. Minimal Comments

Readable code is better than comments. If you can as an LLM infer the comment from the code, delete it.

## Example: API Route Cleanup

**Before** — validation inline, magic numbers, repeated response pattern, handler does too much:

```typescript
export async function POST(request: Request) {
  let body: Record<string, unknown>;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: 'invalid JSON' }, { status: 400 });
  }
  const { text } = body;
  if (!text || typeof text !== 'string' || text.trim() === '') {
    return NextResponse.json({ error: 'text field is required' }, { status: 400 });
  }
  try {
    const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });
    const message = await client.messages.create({
      model: process.env.ANTHROPIC_MODEL ?? 'claude-haiku-4-5-20251001',
      max_tokens: 8192,
      system: SYSTEM_PROMPT,
      messages: [{ role: 'user', content: text }],
    });
    const content = message.content[0];
    if (content.type !== 'text') {
      return NextResponse.json({ error: 'unexpected response type' }, { status: 500 });
    }
    const parsed = JSON.parse(content.text);
    return NextResponse.json(parsed);
  } catch {
    return NextResponse.json({ error: 'evaluation failed' }, { status: 500 });
  }
}
```

**After** — named constants, extracted helpers, handler reads like prose:

```typescript
const MAX_TOKENS = 8192;
const HTTP_BAD_REQUEST = 400;
const HTTP_UNPROCESSABLE = 422;
const HTTP_INTERNAL = 500;

function errorResponse(message: string, status: number) {
  return NextResponse.json({ error: message }, { status });
}

function parseRequestBody(body: unknown): string | null {
  if (typeof body !== 'object' || body === null || Array.isArray(body)) return null;
  const { text } = body as Record<string, unknown>;
  if (!text || typeof text !== 'string' || text.trim() === '') return null;
  return text.trim();
}

function buildMessages(text: string): Anthropic.MessageCreateParams {
  return { model, max_tokens: MAX_TOKENS, system: SYSTEM_PROMPT,
    messages: [{ role: 'user', content: text }] };
}

export async function POST(request: Request) {
  let body: unknown;
  try { body = await request.json(); } catch {
    return errorResponse('invalid JSON', HTTP_BAD_REQUEST);
  }
  const text = parseRequestBody(body);
  if (!text) return errorResponse('text field is required', HTTP_BAD_REQUEST);

  try {
    const message = await client.messages.create(buildMessages(text));
    // ... check truncation, validate schema, return result.data
  } catch (e) {
    const status = e instanceof Anthropic.APIError ? e.status : HTTP_INTERNAL;
    return errorResponse('evaluation failed', status);
  }
}
```

**What changed and why:**
- **Magic numbers → named constants** (§9) — `8192`, `400`, `422`, `500` now have names
- **Repeated pattern → helper** (§2, §6) — `NextResponse.json({ error }, { status })` × 6 → `errorResponse()`
- **Function doing too much → extracted** (§4) — input validation pulled into `parseRequestBody()`, message building into `buildMessages()`
- **Client created per-request → module-level** — eliminates redundant initialization
- **Handler reads like a story** — parse body, validate, call API, check response, return

## Applying Changes

**Clear improvements — apply directly:**

- Dead code removal
- Obvious renames (when the better name is unambiguous)
- Duplicate extraction where the extracted abstraction is clean
- Guard clause / early return simplifications

After applying **each** change, run the test suite immediately. All tests must pass. If a
change breaks a test, revert that specific change — don't adjust the test to match the new
code unless the test was genuinely wrong. Do not batch multiple changes before running tests.
A "safe optimization" that breaks tests was not safe — revert it, don't debug it.

**Uncertain improvements — suggest, don't apply:**
Present as: "Consider: [what to do] — [one sentence why]. Leave as-is if you disagree."
Keep suggestions brief. Don't over-explain.

**No changes — say so:**
If the staged code is already clean, say "Nothing to simplify here." Don't pad this with
minor observations to seem useful.

## Fowler's Refactoring Catalog

Common moves worth knowing. Apply only when the result is clearly simpler:

- **Extract Function** — logic that can be named and reused
- **Inline Function** — a one-line wrapper that obscures rather than reveals
- **Rename Variable/Function** — when the name lies or doesn't say enough
- **Replace Temp with Query** — a temp variable used once can often be a method call
- **Introduce Parameter Object** — 3+ related params become a struct/value object
- **Remove Dead Code** — always safe, always right
- **Decompose Conditional** — complex if/else into named predicates
- **Guard Clause** — nested conditionals become early returns
- **Replace Magic Number with Constant** — unnamed literals get a name

## Output Format

```markdown
## Simplify: <branch or "staged changes">
## Date: <date>

### Applied
- **<file>:<line>** — <what was changed and why>
- ...

### Suggested
- **<file>:<line>** — Consider: <change>. <one sentence why>. Leave as-is if you disagree.
- ...

### Result
All tests passing. / Tests failing: <details> — changes reverted.
Nothing to simplify.
```

If nothing was applied and nothing was suggested, only show the Result line.

## Save the Output

Save the report to `docs/<feature>/simplify/<step-name>-<YYYY-MM-DD>.md`. Determine `<feature>`
from the plan path (e.g., `docs/eval-results-display/plan.md` → `eval-results-display`).
If no plan exists, use `docs/simplify/<branch-name>-<YYYY-MM-DD>.md` as fallback.
Tell the user where the file was saved.

## Commit the Changes

Stage all modified files (including the report) and create a commit:

```bash
git add <modified files> docs/<feature>/simplify/<report file>
git commit -m "Simplify <chunk label>: <one-line description of what changed>

<optional body: key refactors applied>

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

Only commit if at least one change was applied. If nothing was applied (suggestions only or
nothing to simplify), skip the commit — no point creating an empty commit.

## Update the Plan (MANDATORY)

**You MUST update plan.md immediately after this skill completes — not later, not batched.**
Update the Simplify column in plan.md:
- **Changes applied, tests green** → ✅
- **Suggestions raised** → ✅ (suggestions are for the human; the pass is recorded)
- **Nothing to simplify** → ✅
- **Tests failed after a change** → ❌ — changes have been reverted; chunk needs attention
  before Review or Human sign-off.
