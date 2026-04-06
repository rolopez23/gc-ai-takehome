# Review: failure-message-mapping

**Date**: 2026-04-05
**Verdict**: PASS -- no issues found

## Simplify

- **No duplication**: Single map, single function, no redundant logic.
- **Minimal logic**: `getFailureMessage` is 2 lines -- null guard + nullish coalesce fallback. Cannot be simpler.
- **Clean typing**: `Record<string, string>` is correct; no over-engineering with enums or branded types.

## Correctness Review

| Check | Result |
|-------|--------|
| `null` handled | Yes -- `!code` guard returns fallback |
| `undefined` handled | Yes -- same guard |
| Unknown string code handled | Yes -- `??` falls back to `FAILURE_MESSAGES.unknown` |
| Empty string `""` handled | Yes -- falsy, caught by `!code` guard |
| Zod schema matches backend `ReviewOut` | Yes -- both `str | None` / `z.string().nullable()` |
| Messages are user-facing quality | Yes -- clear, actionable, no jargon |

## Notes

- `getFailureMessage("")` returns the generic fallback, which is correct behavior (empty string is not a valid failure code).
- The `unknown` key serves double duty as both a real backend code and the default fallback. This is fine -- if the backend ever sends `"unknown"`, the user sees the same generic message either way.
