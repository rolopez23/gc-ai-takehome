# Spec: MVP Contract Evaluation (M1 Remaining)

## Problem Statement

The frontend upload UI exists but does nothing — `handleSubmit` logs to console and returns. Users can select a contract file but cannot evaluate it. The remaining M1 work connects the upload to the Anthropic API via a thin Next.js proxy and renders the result, proving the full flow works and establishing a provisional output schema for downstream milestones.

## What We Are Solving

- A new evaluation prompt that instructs Claude to return structured JSON matching the output schema, and to detect non-contract input with a structured error response. The prompt should bias toward accepting borderline input rather than over-rejecting.
- A thin Next.js API route (`/api/evaluate`) that proxies the request to Anthropic's Messages API server-side. The API key stays server-side, never exposed to the browser.
- A configurable Claude model via `ANTHROPIC_MODEL` env var so cheap models can be used for testing.
- A skeleton shimmer loading state on the evaluate-contract page while the API call is in flight. The Evaluate button is disabled during the call.
- On success: generate a client-side UUID, store the structured result in React state, and redirect to `/contract/[uuid]`.
- On any failure (API error, network error, or Claude's non-contract detection): stay on `/evaluate-contract` and display "Something went wrong. Try again." All errors collapse to the same message.
- A minimal `/contract/[uuid]` results page that displays whether the evaluation returned error or success (no rich clause UI — that's M2).
- Cancel the in-flight request if the user navigates away.

## What We Are NOT Solving

- Python backend changes — no database writes, no FastAPI changes.
- `.doc` / `.docx` support — only `.txt` for MVP. PDF added only if trivially easy via the API's document support; otherwise deferred.
- Agentic multi-pass evaluation loop (M3).
- Clause index table, detail drawer, topline header UI (M2).
- Streaming / progressive rendering.
- Persistent storage of results (client state only, lost on refresh — this is acceptable for MVP).
- Rich error taxonomy or user-visible error reasons.
- Reliable non-contract detection — best-effort via prompt engineering is sufficient.

## Actors & Triggers

- **Actor:** A user on the `/evaluate-contract` page with a staged `.txt` file (or `.pdf` if trivially supported).
- **Trigger:** User clicks "Evaluate Contract."
- **System:** Browser sends the file to `/api/evaluate` → Next.js API route reads the file, constructs the prompt, calls Anthropic's Messages API server-side → returns structured JSON → frontend routes based on result.

## Success Criteria

1. Uploading a valid `.txt` contract and clicking Evaluate produces a structured JSON response matching the output schema below.
2. Uploading a non-contract file produces a structured error response from Claude; the UI shows "Something went wrong. Try again."
3. While the API call is in flight, the page shows a skeleton shimmer loading state and the button is disabled.
4. On success, the app navigates to `/contract/[uuid]` and displays a minimal confirmation that the evaluation succeeded.
5. On failure, the app stays on `/evaluate-contract` with the generic error message.
6. The Claude model is configurable via `ANTHROPIC_MODEL` env var (defaults to `claude-haiku-4-5-20251001` for cheap testing).
7. Navigating away while the call is in flight cancels the request.

## Interfaces

### Schemas

**Output schema (provisional — will be validated against training contracts before locking for M2):**

**Evaluation response (success):**

```json
{
  "error": null,
  "overall_fairness": "fair" | "unfair" | "egregious",
  "summary": "string — e.g. '1 dealbreaker, 2 negotiating points, 4 acceptable clauses.'",
  "call_to_action": [
    "§7.2 Data Processing — do not sign without resolving",
    "§12.1 Termination — push back"
  ],
  "clauses": [
    {
      "section_number": "§7.2",
      "clause_type": "Data Processing",
      "purpose": "Determines whether you can get your data back after termination.",
      "fairness": "fair" | "unfair" | "egregious",
      "market_standard": "DPA should be attached as a signed exhibit",
      "explanation": "The DPA is incorporated by hyperlink and can be changed unilaterally mid-contract."
    }
  ]
}
```

**Evaluation response (non-contract input):**

```json
{
  "error": true,
  "reason": "This does not appear to be a contract."
}
```

**Environment variables:**

| Variable | Purpose | Default |
|---|---|---|
| `ANTHROPIC_API_KEY` | Anthropic API key (server-side only) | (required) |
| `ANTHROPIC_MODEL` | Claude model ID | `claude-haiku-4-5-20251001` |

### Contracts

**Next.js API route (`/api/evaluate`):**

- Input: `POST` with the file contents (text string or base64 PDF) and optional instructions.
- Output: the evaluation JSON schema above.
- Internally calls Anthropic Messages API with the API key from server-side env vars.

**Anthropic Messages API** — called server-side from the Next.js API route.

- Input: system prompt + user message containing the contract text.
- Output: a single message whose text content is the JSON above.
- Auth: API key via `Authorization` header, never exposed to browser.

### Shared State

**Client-side result store** — holds the evaluation result keyed by UUID. Read by `/contract/[uuid]` to render the result. Written by `/evaluate-contract` after a successful API call. Not persisted — lost on page refresh. Implementation could be React Context, Zustand, or `sessionStorage`.

### Existing Code

| File | Role | Changes Expected |
|---|---|---|
| `frontend/app/evaluate-contract/page.tsx` | Upload page with stub `handleSubmit` | Replace stub with real API call to `/api/evaluate`, add loading shimmer, add error display, add navigation on success |
| `frontend/app/evaluate-contract/validation.ts` | File validation (extension + size) | Narrow `ALLOWED_EXTENSIONS` to `.txt` (and `.pdf` if supported) |
| `frontend/app/evaluate-contract/FileDropZone.tsx` | Drop zone component | Update accepted extensions display text |
| `frontend/app/api/evaluate/route.ts` | **(new)** Next.js API route | Proxy to Anthropic Messages API, keeps API key server-side |
| `frontend/app/contract/[id]/page.tsx` | **(new)** Results page | Reads evaluation result from client state, renders minimal success/error view |
| `frontend/.env.local` or root `.env` | Env config | Add `ANTHROPIC_API_KEY` and `ANTHROPIC_MODEL` |
| `docs/gc-ai-takehome/contract_eval_prompt.md` | Existing prompt (reference only) | Not modified — new prompt written for this feature |

## Open Questions

1. **PDF support** — Claude's API accepts PDF as a document type. If trivially easy to pass through from the API route, include it. If not, defer to a later milestone. **Owner: implementer.**
2. **Prompt refinement** — The new prompt will be tested against the 5 training contracts + at least 1 non-contract input. Exact wording is implementation detail, but must produce the schema above. **Owner: implementer.**
