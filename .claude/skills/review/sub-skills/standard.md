# Standard Review

Correctness-focused review. Looks for bugs, missed edge cases, unhandled error conditions,
and contract violations. Does not editorialize — only raises issues it can fully articulate.

**A clean bill of health is a valid and common output.** Do not manufacture findings.

Only raise an issue if you can state: what the bug is, under what conditions it occurs,
and what the incorrect behavior would be.

## What to Look For

### Bugs
Logic that produces the wrong result for valid inputs:
- Off-by-one errors (boundary conditions, zero vs. empty, first vs. last)
- Wrong operator (`<` vs `<=`, `&&` vs `||`)
- Mutation where a copy was intended (or vice versa)
- Order-dependent operations not guaranteed to run in order
- State not reset between uses

### Missed Edge Cases
Valid inputs or states not handled correctly. Ask what happens when:
- Input is empty, nil, zero, or negative
- Input is at the maximum or minimum boundary
- A collection has one element vs. many
- A dependent record doesn't exist
- The same operation is called twice (idempotency)
- Concurrent requests arrive simultaneously

### Unhandled Error Conditions
- External calls (network, DB, filesystem) with no error handling
- Exceptions bubbling to the wrong layer
- Partial writes that can fail halfway, leaving inconsistent state
- Missing auth checks on new endpoints
- Input validation gaps
- Async operations without cleanup (abort controllers, unsubscribe, cancel tokens)
- Silent failures — catch blocks that swallow errors with no log or rethrow

### Infrastructure Side Effects
- Test setup/teardown that corrupts live state (e.g. `drop_all` leaving migration markers)
- Migrations that are irreversible or leave orphaned state
- Shared resources (DB connections, file handles, event loops) not properly scoped

### Contract Violations
- API response shape differs from the documented contract (check field names AND casing)
- A required side effect isn't atomic
- A spec guarantee isn't upheld in the implementation
- Spec fields that are accepted in requests but never persisted or returned

## Output Format

```markdown
### Bugs
- **<file>:<line>** — <what, when, what goes wrong>

### Edge Cases
- **<file>:<line>** — <trigger, what happens>

### Error Handling
- **<file>:<line>** — <what can fail, what happens>

### Contract Violations
- **<file>:<line>** — <which contract, how violated>
```

Omit empty sections. If nothing found, output: `Clean bill of health.`
