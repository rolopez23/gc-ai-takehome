---
name: pr-interactive-walkthrough
description: Guides an interactive, file-by-file PR walkthrough in run order (startup then request path). Accepts two commit hashes to diff a specific range, or defaults to staged/branch diff. At the start, asks whether to use code snippets per file or summaries-only; skips tests, Markdown, and shell scripts by default; pauses after every question and after each file’s restate/walk-through prompt—never bundling the next file or §3 assessment with a pending question; ends with a calibrated understanding assessment (repo-hygiene files excluded from rubric) and follow-up questions for low-understanding areas. Use when the user asks for a PR walkthrough, to go through a PR together, file-by-file review, to check their understanding of a branch, or when the plan dashboard’s Understand column needs to be updated.
---

# Interactive PR Code Walkthrough

## Purpose

Run a **file-by-file** walkthrough of PR changes so the user builds and confirms their understanding. **Format is chosen up front** (see **Choose format** below): either **snippets** (short PR code excerpts + walk-through) or **summaries only** (prose per file, no code blocks). Always end with an understanding assessment and follow-up questions for any areas of low understanding.

## When to Use

- User asks for a "PR walkthrough," "go through the PR," "file by file review," or "walk me through the changes."
- User wants to verify or deepen their understanding of a branch before merging or presenting.

## Workflow

### 0. Choose format (required at walkthrough start)

**Before** listing files or diving into the first file, ask the user which mode they want (unless they **already stated** it in the same message, e.g. “walkthrough with summaries only”):

- **Snippets** — For each file: short summary **plus** a **10–20 line** PR excerpt (see §2); user walks through the code (control flow, data in/out). Best for deep review and onboarding.
- **Summaries only** — For each file: **2–4 sentence** summary only (**no** fenced code block); user restates concepts, behavior, and how it connects to the prior step; follow-ups reference **functions/types/file names**, not line numbers. Faster, good for high-level passes.

If they do not answer before you must proceed (e.g. single-shot request), **default to snippets** and state that default once.

**On request mid-walkthrough:** If they say **“summaries only”**, **“no code”**, or **“snippets”**, **switch mode** from the next file onward (or re-do the current file in the new mode if they ask).

**Optional escape hatch (summaries mode):** If they type **show code** (or **snippet**) for the current file, paste **one** focused excerpt for that file, then return to summaries-only for subsequent files unless they ask again.

### 1. Determine scope and run order

Determine the diff source. Three modes, checked in this order:

- **Commit range (if two hashes provided):** `git diff <commit-a> <commit-b> --name-only`
  The user may provide hashes, refs, or tags. Use them directly. Example: `/pr-interactive-walkthrough abc123 def456`
- **Staged files:** `git diff --cached --name-only`
- **Branch vs main:** First `git fetch origin main` then `git diff origin/main...HEAD --name-only` (or `main...HEAD` if no origin/main)
- **Exclude by default** (unless the user explicitly asks to include them), same spirit as skipping tests:
  - **Tests:** `*_test.go` (and other `*_test.*` if relevant to the stack).
  - **Markdown:** `*.md`.
  - **Scripts:** shell and similar helpers—e.g. `*.sh`, `*.bash`, `*.zsh` (dev/curl/Makefile-adjacent scripts, not application source).
- **Repo hygiene (optional skip):** `.github/CODEOWNERS`, `.github/labeler.yml`, `codecov.yml` (and similar ownership/label/coverage-only edits) may be **named once** in the preamble (“skipped” or “listed only”) since they are rarely deep-reviewed like product code. If you do cover them briefly, **do not** grade them in the understanding rubric (see §3).
- **Order files by run order** when possible:
  1. **Startup / build:** Entrypoint (e.g. `main.go`), config or env templates, dependency files (e.g. `go.mod`). Order: process starts → config loaded → deps resolved.
  2. **Request path:** In execution/call order. Example: HTTP handler (request enters) → code the handler calls (e.g. render, service layer) → code those call (actions, utils). Trace the main code path: "when a request hits X, it calls Y, which uses Z."
  3. **New or shared code** used along that path appears where it is first invoked (e.g. feature-flag helper before the action that uses it).
  4. If run order is unclear (e.g. unrelated files), use a logical grouping (config → bootstrap → handlers → feature code → utils) and say so briefly.

### 2. For each included file (code / config that is not test, markdown, or script—see scope above), in run order

1. **Agent gives a short summary** (2–4 sentences):
   - **What this file is:** role in the codebase (e.g. "API layer," "builds starter-actions SDUI").
   - **What this PR changed:** concrete edits (new args, new behavior, new files, deprecations).

2. **Snippets mode only — PR excerpt.** Skip this step in **summaries-only** mode (unless the user invoked **show code** for this file).
   - Paste **one focused excerpt** from this file’s **PR diff** (use `git diff` / triple-dot against mainline), **10–20 lines** when possible (a few more only if a branch is unintelligible without context). Prefer the **heart of the change** (new function body, new branch, new struct fields, critical call site)—not imports-only noise.
   - **Code-first excerpts (required in snippets mode):** The excerpt must be **mostly executable/source structure**, not comments. Avoid blocks that are **only or predominantly** Swagger/godoc, license headers, or `//` narration—those are hard to “walk through” as code. If this file’s diff is **comment-only** (e.g. `@Param` lines), **summarize** that in 1–2 sentences and place the **10–20 line excerpt in the next file down the call stack** that **implements** the change (e.g. query/schema struct, decode function, handler body). Say so explicitly (e.g. “`handler.go` only adds Swagger; excerpt is where the param is parsed”). If one file mixes a tiny doc tweak with real code, show **at most 2–3** comment lines plus the **rest** as non-comment code.
   - Show the excerpt in a fenced code block; prefer the repo’s **line-range + path** citation style when available (so the user can jump to the file).
   - Ask the user to **walk through** the snippet: control flow, data in/out, what breaks if inputs are wrong, and how it connects to the prior step in the run order.
   - **End the turn here (snippets mode):** After the excerpt, your message must close with the **restate / walk-through prompt** for this file (step 3 below) and **nothing else**—no next file, no affirmations, no assessment, no optional tangents in the same message.
   - **Exception—when you may omit a full 10–20 line block for _this file_:** only if the user has **already fully engaged** on **this same file** earlier in the walkthrough via **multiple** probing follow-ups (several back-and-forth exchanges that reference the implementation). Then a **short** recap plus a **smaller** pointer (or a repeat of 3–5 key lines) is enough before moving on or going deeper.

3. **User restates** in their own words (concise):
   - **Snippets mode:** file changes **and** walk through what the **snippet** is doing.
   - **Summaries-only:** file changes and how they connect to the **previous** step—**no** line-by-line unless they asked for **show code**.

   **Treat the step-3 prompt as a blocking question:** The “Restate in your own words…” / “walk through…” request is **not** decorative—the user must answer (or **`skip`** / **`next file`**) before you continue. **Never** put step 3’s prompt in the same message as step 4’s reaction, the next file, or §3 assessment.

4. **Agent response:**
   - If the restate is **derivative** (mostly parroting): ask a follow-up that forces rephrasing or connection (e.g. "Why does X need Y at this point?" or "What would break if we didn't do Z?"). In **snippets** mode, **point at specific lines** when helpful; in **summaries-only**, point at **symbols / responsibilities**.
   - If the restate is **excellent:** affirm briefly and optionally ask one clarifying/deeper question (e.g. "Why support BOTH instead of only one path?").
   - If the restate misses major issues or the point, ask follow-up questions.
   - If the restate is solid but needs **any** correction or precision fix, give that correction clearly; optional follow-up only if useful.
   - **Pause after every question:** If you ask **any** question (required follow-up, optional deepening, or clarification), **end the assistant message there**. Do **not** in the **same** message introduce the next file, paste the next summary, continue the walkthrough, or add unrelated sections (e.g. do not bundle “next file” with a pending question). Advance only after the user answers, **`skip`s**, or uses **`next file`** as allowed below. If you **only** affirm or correct with **no** question, you **may** move to the next file in that same message.
   - **After any follow-up question:** **wait** for the user to answer—or **`skip`**. Do **not** advance to the next file until they respond or skip (see **Rules**).

### 3. Understanding assessment (required)

After all files are covered, **always** produce an understanding assessment.

**Timing:** Do **not** output §3 (assessment table) or §4 (low-understanding follow-ups) in the **same** message as a **still-open** prompt from §2—whether that is the **step-3 “Restate in your own words…”** ask or **any** follow-up/deepening question for the **current or final** file. Wait until the user has answered, **`skip`ped**, or **`next file`**d (per rules) **before** emitting assessment.

**Files to exclude from the rubric:** Do **not** assign High/Medium/Low to pure **repo hygiene** paths (e.g. `.github/CODEOWNERS`, `.github/labeler.yml`, `codecov.yml` ownership/component lines) unless the user explicitly asked to drill into them. Mention them once if needed (“omitted from rubric—ownership/labels/coverage wiring”) instead of inflating the table.

**Calibration (use consistently):**

- **High:** **Highly accurate** restatement in the user’s own words—either a **simple, precise** summary (including a **terse one-liner** when it is genuinely strong: correct mechanism, not vague) **or** that accuracy **plus** edge cases, failure modes, or non-obvious connections (or a probing follow-up answered with that depth). **Either** path can be High; length is not the criterion—**accuracy and specificity** are.
- **Medium:** **Any** correction from you was needed (imprecise terms, wrong mechanism, missing nuance)—even a small fix—or the grasp is **hand-wavy / generic** (correct direction but could apply to anything). **Early wiring files** (`go.work`, `go.mod` / `replace` blocks): default **Medium** when vague; use **High** if even a short answer nails **what** changed and **why it matters** for the build.
- **Low:** Mostly **copying/parroting** your wording, **major** errors, or repeated confusion about the main idea.

Produce a short table: file (or file group), level, and one-line note—**only for files that belong in the rubric** (product code, shared libraries, request path, meaningful config).

### 4. Follow-up questions for low understanding

For **every file (or file group) rated Low**, provide 1–2 concrete follow-up questions the user can use to deepen understanding (e.g. "What does X do when Y is nil?", "Why do we need Z before W?"). If no file is rated Low, skip this step or offer one optional follow-up for the lowest-rated area if useful.

## Rules

- **Concise summaries.** Keep each file summary to a few sentences. In **snippets** mode, **pair** the summary with the **10–20 line PR excerpt** (see step 2) unless the **multi-exchange exception** applies for that file. In **summaries-only** mode, **do not** include a routine excerpt; prose carries the walkthrough (plus optional **show code** on demand).
- **Snippets mode — code, not comment walls.** Excerpts skew toward **statements and types**; do not default to long Swagger/godoc hunks. **Do not hide new code** in snippets mode: the user should **see** the change. Edge-case questions **add to** the snippet walkthrough; they do not replace showing the code first. **Summaries-only** trades visible code for speed; offer **show code** if they need to see a hunk.
- **Follow up when useful.** Ask one focused question when it would deepen understanding (e.g. semantics, rollout, failure behavior). If the user's restate is too close to your wording, ask a question that requires them to rephrase or reason.
- **One file at a time.** Do not batch multiple file summaries unless the user asks to "continue" through a list.
- **Pause on questions; do not continue in the same turn.** Whenever you ask **any** question (**including** optional deepening questions), **stop** and wait for the user. **Do not** append the next file, the next summary, or walkthrough progress to that same message. Tell them they can type **`skip`** to skip that question (and still continue the walkthrough). Do not present the next file or batch summaries until they answer or skip. **`next file`** can still skip the rest of the current file as below.
- **Skip markdown, scripts, and test files by default.** Omit `*.md`, `*_test.go` (and stack-typical `*_test.*`), and shell scripts (`*.sh`, `*.bash`, `*.zsh`, etc.) from the walkthrough unless the user explicitly asks to include them. Mention excluded paths once in the file list preamble so the user knows what was skipped.
- **User restates first.** Wait for the user's restate before asking follow-ups or moving on (unless they say **`skip`** or **`next file`**). Same rule for **§3 assessment**: no assessment block until the **last** restate or follow-up for the **last** file is resolved.
- **Run order.** Walk through files in execution order when possible: startup/build first, then request path in call order (handler → what it calls → what those use). If unclear, use logical grouping and note it.

At the **start of the walkthrough**, after **choose format** (§0), briefly mention that **`skip`** is available for follow-up questions (or mention it on the **first** follow-up if format was implicit).

## Example flow

**Agent:** "Do you want **snippets** (code excerpts per file) or **summaries only** (prose only, faster)?"

**User:** "Snippets."

**Agent:** "## File 3 of 12: `svc/coach/internal/api/handlers.go`  
This file is the HTTP layer for the Coach API. The PR builds a request-scoped feature client from `fvClient` and passes it plus `exchangeID` into `RenderStarterActions` so starter actions can use the migration flag and attach the exchange to events.

**PR excerpt (walk through this—what runs, what data flows in/out):**

```88:102:svc/coach/internal/api/handlers.go
	// ... illustrative: show the actual diff hunk from the branch ...
```

Restate in your own words (concise), tied to the lines above.

**Summaries-only variant (no code block):** Same summary paragraph, then: "Restate how this fits the request path and what would break if `exchangeID` were wrong—no line walk-through."

**User:** "API layer; we now use fvClient on chat-create like we did for stream so we can attach the right events."

**Agent:** "Right. One follow-up (type **skip** if you want to move on): on line 97 we pass `exchangeID` into `RenderStarterActions`. Why do we need it at that point in the flow?"

**User:** "So we're consistent across the conversation—same ID for the initial UI and later turns."

**Agent:** "Yes—that matches the intent." _(End message here; do not add the next file in the same turn.)_

**Agent (after user replies or skip):** "Next file: `svc/coach/internal/sdui/render/starteractions.go`..."

## Output format for assessment

**Table:** file (or file group), level, one-line note. Example:

```markdown
| File              | Level  | Note                                                                     |
| ----------------- | ------ | ------------------------------------------------------------------------ |
| go.work           | Medium | Generic “new package”; High would be a terse but precise workspace role. |
| handlers.go       | High   | Accurate restate; strong exchangeID / consistency answer.                |
| starteractions.go | Medium | Needed a small correction on what gets built.                            |
| sdlutils.go       | Low    | Parroted wording; confused mapping vs enums.                             |
```

**If any file is Low:** add a "Follow-up questions" section with 1–2 targeted questions per Low file so the user can revisit and solidify. Example:

```markdown
## Follow-up questions (low understanding)

- **sdlutils.go:** What does this file produce—full protobufs or only enum values? Where is that output used?
- **sdlutils.go:** If we add a new surface type in coach, what do we need to update?
```

Also in the case of low web search for learning resources to share with the user and search the codebase for similar patterns done.
