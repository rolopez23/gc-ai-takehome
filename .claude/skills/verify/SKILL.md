---
name: verify
description: >
  Runs end-to-end verification of implemented code against a live system. For APIs, fires real
  curl requests. For web UIs, runs browser automation. Reports what passed, what failed, and
  what could not be verified. Returns "verification incomplete" when the system cannot be reached
  or the verification cannot be run — this is distinct from a failure.
  Trigger when the user says "verify this", "test this end to end", "run the E2E", "check it
  works", or when the plan dashboard's LLM Verify column needs to be updated.
---

# Verify

You are verifying that implemented code works against a live, running system. This is not a unit
test run — it is an end-to-end check of real behavior: real HTTP requests, real browser
interactions, real database state. You are the last line of defense before the human signs off.

## The Core Rule

```
NO COMPLETION CLAIMS WITHOUT EVIDENCE
```

Run the command. Read the output. Then report the result. Never say "should work", "looks good",
or "verified" before you have actually run the verification and read the output. Confidence is
not evidence.

| Claim | Requires |
|---|---|
| "Verified" | Command output showing expected behavior |
| "Tests pass" | Test runner output: 0 failures |
| "Fixed" | Re-run the original failing check: now passes |
| "No regressions" | Full suite output, not just the changed path |

If you haven't run it in this response, you cannot claim it.

## Before You Start

Determine what needs to be verified. In order of preference:

1. Read the step plan (`docs/<feature>/steps/<step-name>.md`) — the LLM Verification section
   describes exactly what to run and what a passing result looks like.
2. Read the spec (`docs/<feature>/spec.md`) — the Success Criteria section defines what must be
   true when the work is done.
3. If neither exists, infer from the code what the observable behavior should be.

If you cannot determine what to verify, say so and return verification incomplete.

**Do not mark N/A too eagerly.** If any verification is possible — connecting to a database,
inspecting a file, querying a queue, checking logs — do it. N/A means there is genuinely no
observable effect to check, not "there's no HTTP endpoint." A schema migration can be verified
by inspecting the live database. A background job can be verified by checking its side effects.
Only mark ➖ when you have exhausted all verification paths.

## Check the System is Running

Before running any verification, confirm the system is up:

```bash
lsof -i :3000 2>/dev/null | grep LISTEN
# or
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/health 2>/dev/null
```

If the system is not running, return verification incomplete — not a failure. Note what was
needed and how to start it.

## API Verification

For each behavior to verify, construct a real curl request:

```bash
# Unauthenticated request (expect 401)
curl -s -w "\nHTTP %{http_code}" http://localhost:3000/api/endpoint

# Authenticated request
curl -s -w "\nHTTP %{http_code}" \
  -H "Authorization: Bearer <token>" \
  http://localhost:3000/api/endpoint

# POST with body
curl -s -w "\nHTTP %{http_code}" \
  -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"key": "value"}' \
  http://localhost:3000/api/endpoint
```

For each request, record the command run, the response body, the HTTP status code, and whether
it matches the expected result. If auth tokens are needed and unavailable, return incomplete.

## Web / Browser Verification

For frontend verification, use the webapp-testing sub-skill — it handles server lifecycle,
static vs dynamic detection, and the reconnaissance-then-action pattern:

> **Sub-skill:** `sub-skills/webapp-testing/SKILL.md`

Quick path when Playwright tests already exist:

```bash
npx playwright test --reporter=line 2>/dev/null
```

If tests don't exist yet, follow the decision tree in `webapp-testing/SKILL.md` to write a
minimal inline script against the running app. Use `sub-skills/webapp-testing/scripts/with_server.py`
to manage server lifecycle if the server isn't already running.

If Playwright is not installed and the UI cannot be verified another way, return incomplete.

## Outcomes

- **Verified** — the system behaved as expected
- **Failed** — the system is running but the behavior is wrong
- **Incomplete** — the check could not be run (system not running, auth unavailable, tooling
  missing, behavior not observable this way)

Failed blocks the plan dashboard update. Incomplete flags for human follow-up but does not
block Simplify/Review.

## Save the Output

Save the report to `docs/verify/<branch-name>-<YYYY-MM-DD>.md` (`git branch --show-current`
for the branch name). If no `docs/` directory exists, save to `.claude/verify/` instead.
Tell the user where the file was saved.

## Output Format

```markdown
## Verify: <step name>
## Date: <date>

### Verified ✅
- **<what was checked>** — `<command run>` → <what was returned / observed>

### Failed ❌
- **<what was checked>** — `<command run>` → <what was returned> (expected: <what was expected>)

### Incomplete ⚠️
- **<what was checked>** — <reason>

---
Overall: Verified / Failed / Incomplete
```

## Update the Plan

Update the Verify column in plan.md:
- **Verified** → ✅
- **Failed** → ❌ — needs fixes before Simplify or Review. Fix and re-verify, or update the
  plan if scope changed.
- **Incomplete** → ⚠️ — flag for human follow-up; does not block Simplify/Review but must be
  resolved before Human sign-off.
