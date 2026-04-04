# Spec: Contract Upload UI

## Problem Statement

The app has no way for a user to submit a contract for evaluation. Before wiring up any backend or LLM call, we need a polished upload page where a user can select a contract file, optionally provide custom instructions, and confirm everything is staged correctly. This is the entry point for the entire M1 flow.

## What We Are Solving

- A Next.js page at route `/evaluate-contract`
- Drag-and-drop zone that accepts a single contract file
- File picker button ("Browse") as an alternative to drag-and-drop
- Accepted formats: `.pdf`, `.txt`, `.doc`, `.docx` — validated by file extension (not MIME type)
- Max file size: 5 MB, with a clear error if exceeded
- Upload feedback: file name, file size, and a remove/replace action
- A text input (textarea) for user-specific evaluation instructions (e.g., "Focus on IP ownership clauses")
- A submit handler that console.logs a summary for now — extracted as a standalone handler so backend wiring replaces only the handler logic, not the component
- File and instructions state are independent — removing/replacing a file does not clear the textarea, and vice versa
- Replacing a file clears only the previous file selection (single file only)

## What We Are NOT Solving

- Backend API endpoint (`/api/evaluate` or similar)
- Anthropic API call or any LLM evaluation
- Contract parsing, text extraction, or file processing
- Results display, clause index, or detail drawer (Milestone 2)
- Agentic evaluation loop (Milestone 3)
- Authentication or user sessions
- Multiple file upload
- Persistent storage of uploaded files

## Actors & Triggers

- **Actor:** A user visiting the app in a browser
- **Trigger:** User navigates to `/evaluate-contract`
- **Action:** User selects a file (drag-drop or picker), optionally types instructions, clicks submit

## Success Criteria

1. Navigating to `/evaluate-contract` renders the upload page
2. Dragging a `.pdf`, `.txt`, `.doc`, or `.docx` file onto the drop zone stages it with visible feedback (name + size)
3. Clicking "Browse" opens the native file picker filtered to accepted types
4. Dropping/selecting a file > 5 MB shows an error message and does not stage the file
5. Dropping/selecting a file without an allowed extension (`.pdf`, `.txt`, `.doc`, `.docx`) shows an error message and does not stage the file — validation is by file extension, not MIME type
6. A staged file can be removed, returning to the empty drop zone state
7. Selecting a new file replaces the previously staged file
8. The text input accepts freeform text for custom instructions
9. Clicking the submit button logs `{ fileName, fileSize, fileType, instructions }` to the console via an extracted handler function
10. Removing/replacing a file does not clear the instructions textarea
11. The page uses standard UI patterns — clean layout, no custom design system required

## Interfaces

### Schemas

**Staged file state (client-side only):**

```typescript
interface StagedFile {
  file: File;          // browser File object
  name: string;        // e.g. "contract_v2.pdf"
  size: number;        // bytes
  type: string;        // MIME type
}
```

**Submit handler signature (extracted for future backend wiring):**

```typescript
interface SubmitPayload {
  file: File;
  fileName: string;
  fileSize: number;
  fileType: string;
  instructions: string;  // empty string if none provided
}

// Current implementation: console.log(payload)
// Future: POST to backend API
function handleSubmit(payload: SubmitPayload): void
```

**Allowed extensions (validation by extension, not MIME type):**

```typescript
const ALLOWED_EXTENSIONS = ['.pdf', '.txt', '.doc', '.docx'] as const;
const MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024; // 5 MB
```

### Contracts

None. No backend calls in this scope.

### Shared State

None. All state is local to the page component. The `File` object and instructions text will need to be accessible to a future parent component or API call when the backend is wired up, but that wiring is out of scope.

### Existing Code

- `frontend/app/page.tsx` — current landing page; the new route will be a sibling
- `frontend/app/layout.tsx` — shared layout with Inter font and base styles
- `frontend/app/globals.css` — Tailwind v4 base styles
- New file needed: `frontend/app/evaluate-contract/page.tsx`

## Resolved During Stress-Test

1. **File type validation** — validate by file extension, not MIME type. MIME is unreliable across browsers for `.doc`/`.docx`. Backend can do deeper validation later.
2. **Submit handler** — extracted as a standalone handler so backend integration swaps only the handler, not the component.
3. **Navigation** — no nav link needed for now; direct URL navigation to `/evaluate-contract` is sufficient for testing.
4. **Instructions on file replace** — file and textarea state are independent. Removing a file does not clear instructions.

## Open Questions

None at this time.
