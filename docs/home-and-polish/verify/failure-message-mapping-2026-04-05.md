# Verify: failure-message-mapping

**Date**: 2026-04-05
**Status**: PASS

## Tests

All 5 tests pass (`npm run test -- --reporter=verbose`):

| Test | Result |
|------|--------|
| all 5 failure codes have entries | PASS |
| known code returns correct message | PASS |
| unknown code falls back to generic message | PASS |
| null falls back to generic message | PASS |
| undefined falls back to generic message | PASS |

## File Checks

- **failure-messages.ts**: All 5 codes present (`too_large`, `timeout`, `anthropic_error`, `parse_error`, `unknown`). `getFailureMessage()` handles `string | null | undefined` and falls back via `??`.
- **types.ts**: `failure_code: z.string().nullable()` added to `ReviewFailedSchema` at line 42. Matches backend `ReviewOut.failure_code: str | None`.
- **failure-messages.test.ts**: 5 tests covering known code, unknown code, null, undefined, and completeness check.

## Verdict

All "Done When" criteria met. No issues.
