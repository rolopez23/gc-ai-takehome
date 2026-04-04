# TDD Rules

Referenced by `plan-step.md`. Apply these rules during every implementation cycle.

## The Iron Law

```
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

If you wrote code before the test: delete it. Start over. Don't keep it as "reference" —
you'll adapt it and that's testing after. Delete means delete.

## Red-Green-Refactor

**RED** — Write one test for one behavior. Run it. It must fail for the right reason
(feature missing, not a typo or import error). If it passes immediately, it's testing
nothing — fix the test.

**GREEN** — Write the minimum code to make it pass. Not the clean version, not the
configurable version. The simplest thing that works.

**REFACTOR** — Clean up with tests green. Remove duplication, improve names, extract
helpers. Do not add behavior here.

**COMMIT** — Tests green, code and tests together in one commit. Never commit red.

## What a Good Test Looks Like

```typescript
// ✅ Tests real behavior, clear name, one thing
test('retries failed operations 3 times', async () => {
  let attempts = 0;
  const op = () => { attempts++; if (attempts < 3) throw new Error(); return 'ok'; };
  const result = await retryOperation(op);
  expect(result).toBe('ok');
  expect(attempts).toBe(3);
});

// ❌ Tests the mock, not the code; vague name
test('retry works', async () => {
  const mock = jest.fn()
    .mockRejectedValueOnce(new Error())
    .mockResolvedValueOnce('success');
  await retryOperation(mock);
  expect(mock).toHaveBeenCalledTimes(2);
});
```

One behavior per test. "and" in the test name means split it. Use real code — mocks only
when the dependency is truly external (network, clock, filesystem).

## Commit Rules

- All tests green → commit
- Any test red → do not commit; fix or ask for help
- Never skip, pend, or comment out a failing test to reach green
- Tests and implementation land in the same commit

## Rationalization Red Flags

Stop and return to Red when you catch yourself thinking:

| Thought | Reality |
|---|---|
| "Too simple to need a test" | Simple code breaks. Test takes 30 seconds. |
| "I'll write tests after to verify" | Tests after pass immediately — they prove nothing. |
| "I already manually tested this" | Manual is ad-hoc. No record, can't re-run. |
| "Keep code as reference, write tests first" | You'll adapt it. That's testing after. Delete it. |
| "Deleting X hours of work is wasteful" | Sunk cost. Keeping unverified code is the waste. |
| "Just this once" | No exceptions without explicit user permission. |

## When Stuck

| Problem | Solution |
|---|---|
| Don't know how to test it | Write the API you wish existed. Write the assertion first. |
| Test is too complicated to set up | The design is too coupled. Simplify the interface. |
| Must mock everything | Inject dependencies instead. |
| Test setup is enormous | Extract helpers. Still complex? The design needs work. |

## Verification Checklist

Before marking a cycle complete:

- [ ] Watched the test fail before writing any code
- [ ] Test failed for the expected reason (feature missing, not a typo)
- [ ] Wrote the minimum code to pass — nothing extra
- [ ] All tests green, including pre-existing ones
- [ ] No skipped, pending, or commented-out tests
- [ ] Tests use real code (mocks only where unavoidable)
