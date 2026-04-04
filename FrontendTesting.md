# Frontend Testing Guide

Referenced from [AGENTS.md](AGENTS.md). Rules for writing frontend tests in this project.

---

## Stack

- **Vitest** — test runner
- **React Testing Library (RTL)** — component testing
- **@testing-library/user-event** — user interaction simulation
- **jsdom** — DOM environment

---

## RTL Query Rules

### Always use accessibility-driven queries

Query elements the way a user or assistive technology would find them. **Never** use `document.querySelector` — it bypasses RTL's philosophy and couples tests to DOM structure.

**Preferred query order** (per RTL docs):

1. `getByRole` — buttons, headings, inputs with roles
2. `getByLabelText` — form inputs with labels or aria-labels
3. `getByPlaceholderText` — inputs with placeholders
4. `getByText` — visible text content
5. `getByDisplayValue` — current value of form elements

**Avoid:**

- `document.querySelector` — DOM structure coupling
- `getByTestId` — use only as a last resort when no accessible query works
- `.closest('div')` — fragile DOM traversal; prefer a role or label query

### Hidden inputs

For hidden file inputs or similar, add an `aria-label` to the element and query with `getByLabelText`:

```tsx
// Component
<input type="file" aria-label="Upload contract file" className="hidden" />

// Test
const input = screen.getByLabelText(/upload contract file/i);
```

---

## Type Casting

### Avoid unnecessary `as` casts on RTL queries

RTL queries return `HTMLElement`. Most testing-library APIs (`userEvent.upload`, `fireEvent.change`, etc.) accept `HTMLElement` — no cast needed.

**Only cast when accessing element-specific properties** (e.g., `.accept`, `.value`, `.checked`). Use RTL's generic form:

```tsx
// Need .accept — use generic
const input = screen.getByLabelText<HTMLInputElement>(/upload/i);
expect(input.accept).toBe('.pdf,.txt');

// Just uploading — no cast needed
const input = screen.getByLabelText(/upload/i);
await userEvent.upload(input, file);
```

---

## fireEvent vs userEvent

- **`userEvent`** — default choice. Simulates real user behavior (typing, clicking, uploading). Respects browser constraints like the `accept` attribute on file inputs.
- **`fireEvent`** — use when you need to bypass browser behavior. For example, testing validation of a disallowed file type requires `fireEvent.change` because `userEvent.upload` respects the `accept` filter.

```tsx
// Happy path — userEvent respects accept attribute
await userEvent.upload(input, validFile);

// Error path — fireEvent bypasses accept to test validation
fireEvent.change(input, { target: { files: [invalidFile] } });
```

---

## Comments in Tests

- Do **not** add comments explaining what the code already shows
- Do **not** add comments that narrate the test steps ("// Stage a file", "// Click remove")
- **Do** add comments for non-obvious testing workarounds where the reason isn't clear from context

---

## Test Structure

- One behavior per test — "and" in the name means split it
- Use `vi.fn()` for callback spies
- Assert both the positive (what happened) and negative (what should not have happened) when testing error paths:

```tsx
expect(screen.getByText(/error message/i)).toBeInTheDocument();
expect(onCallback).not.toHaveBeenCalled();
```
