# Step: failure-message-mapping

> Part of: [plan.md](../plan.md) · Spec: [spec.md](../spec.md)

## What This Step Delivers

Creates the frontend `failure_code` → friendly message mapping and adds `failure_code` to the Zod `ReviewFailedSchema`. Pure data/types — no UI changes yet.

## Done When

1. `FAILURE_MESSAGES` map covers all 5 codes
2. `getFailureMessage()` returns correct message for known codes, falls back for unknown/null
3. `ReviewFailedSchema` includes `failure_code`

## Cycles

### message-map-and-schema

**Test** — write these tests and confirm they fail:
- **test_all_failure_codes_have_messages**: Assert `['too_large', 'timeout', 'anthropic_error', 'parse_error', 'unknown']` all exist in `FAILURE_MESSAGES`
- **test_get_failure_message_known_code**: `getFailureMessage("timeout")` → "The evaluation timed out. Please try again."
- **test_get_failure_message_unknown_code**: `getFailureMessage("new_code")` → generic fallback
- **test_get_failure_message_null**: `getFailureMessage(null)` → generic fallback

**Code** — Create `frontend/app/evaluate-contract/failure-messages.ts`:
```typescript
export const FAILURE_MESSAGES: Record<string, string> = {
  too_large: 'This contract is too large to evaluate. Try a shorter document.',
  timeout: 'The evaluation timed out. Please try again.',
  anthropic_error: "We couldn't reach our AI service. Please try again later.",
  parse_error: 'The AI returned an unexpected response. Please try again.',
  unknown: 'Something went wrong. Please try again.',
};

export function getFailureMessage(code: string | null | undefined): string {
  if (!code) return FAILURE_MESSAGES.unknown;
  return FAILURE_MESSAGES[code] ?? FAILURE_MESSAGES.unknown;
}
```

Add `failure_code: z.string().nullable()` to `ReviewFailedSchema` in `types.ts`.

**Refactor** — none

**Commit**: `add failure code to message mapping and Zod schema`

---

## Verification

```bash
cd frontend && npm run test -- failure-messages
cd frontend && npm run test -- types.test
```
