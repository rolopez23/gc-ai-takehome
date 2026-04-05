# Step: api-route

> Part of: [plan.md](../plan.md) · Spec: [spec.md](../spec.md)

## What This Step Delivers

A thin Next.js API route at `/api/evaluate` that receives contract text via POST, imports the system prompt from `frontend/prompt/`, calls Anthropic's Messages API server-side, and returns the structured evaluation JSON. The API key stays server-side. The model is configurable via `ANTHROPIC_MODEL` env var.

## Done When

- `POST /api/evaluate` with `{ text: "..." }` body calls Claude and returns a valid `EvalResponse`
- Missing or empty `text` field returns 400
- Anthropic SDK errors return 500
- Malformed Claude JSON responses return 500
- Model is read from `ANTHROPIC_MODEL` env var with `claude-haiku-4-5-20251001` as default
- All tests pass

## Cycles

### route-validation

**Test** — write these tests in `frontend/__tests__/api-evaluate.test.ts` and confirm they fail:
- **returns 400 when text is missing**: POST with `{}` body → 400 status
- **returns 400 when text is empty string**: POST with `{ text: "" }` → 400 status

Setup: import the `POST` function from the route module directly. Create a mock `NextRequest` with the appropriate JSON body.

**Code** — Create `frontend/app/api/evaluate/route.ts` with the `POST` handler. Parse the JSON body, validate `text` exists and is non-empty, return 400 if not. Add `@anthropic-ai/sdk` to `package.json`.

**Refactor** — none

**Commit**: `Add /api/evaluate route with input validation`

---

### anthropic-call

**Test** — write these tests and confirm they fail:
- **calls Anthropic with system prompt and returns parsed response**: POST with `{ text: "sample contract" }` → mock `messages.create` to return a message with valid `EvalSuccess` JSON → assert 200 and response body matches shape
- **passes contract text as user message**: assert `messages.create` was called with `messages: [{ role: 'user', content: 'sample contract' }]`
- **uses SYSTEM_PROMPT from prompt module**: assert `messages.create` was called with `system` containing the imported prompt

Setup: mock `@anthropic-ai/sdk`. Set `process.env.ANTHROPIC_API_KEY`.

**Code** — Import `SYSTEM_PROMPT` from `@/prompt`. Create an Anthropic client, call `messages.create` with the system prompt and user text, parse the text response as JSON, return it.

**Refactor** — none

**Commit**: `Wire /api/evaluate to Anthropic Messages API`

---

### error-handling

**Test** — write these tests and confirm they fail:
- **returns 500 when Anthropic SDK throws**: mock `messages.create` to throw → assert 500 with error in body
- **returns 500 when response JSON is malformed**: mock response with `text: 'not json'` → assert 500

**Code** — Wrap the Anthropic call and JSON parse in try/catch. Return 500 with `{ error: "evaluation failed" }`.

**Refactor** — none

**Commit**: `Handle Anthropic SDK and JSON parse errors`

---

### model-configuration

**Test** — write these tests and confirm they fail:
- **uses ANTHROPIC_MODEL env var when set**: set env var to `claude-sonnet-4-5-20241022` → assert `messages.create` called with that model
- **defaults to haiku when ANTHROPIC_MODEL is not set**: delete env var → assert called with `claude-haiku-4-5-20251001`

**Code** — already implemented via `process.env.ANTHROPIC_MODEL ?? 'claude-haiku-4-5-20251001'`. These tests validate.

**Refactor** — none

**Commit**: `Test model configuration for /api/evaluate`

---

## LLM Verification

With the dev server running:

```bash
# Success case — use a training contract
curl -X POST http://localhost:3000/api/evaluate \
  -H "Content-Type: application/json" \
  -d "{\"text\": \"$(cat docs/gc-ai-takehome/contract_2_egregious.txt)\"}"
```

Expected: 200 with JSON matching `EvalSuccess` schema, `overall_fairness` should be `"egregious"`.

```bash
# Non-contract case
curl -X POST http://localhost:3000/api/evaluate \
  -H "Content-Type: application/json" \
  -d '{"text": "Chocolate chip cookie recipe: preheat oven to 350, mix flour and sugar..."}'
```

Expected: 200 with `{ "error": true, "reason": "..." }`.

```bash
# Validation case
curl -X POST http://localhost:3000/api/evaluate \
  -H "Content-Type: application/json" \
  -d '{}'
```

Expected: 400.
