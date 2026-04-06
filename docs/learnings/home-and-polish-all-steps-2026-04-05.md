# Learnings: home-and-polish/all-steps

## Post-Human Additions (2026-04-05)

### Human Corrections

1. **Deferred VSR** (`workflow-steps-skipped` ×5) — Treated Verify/Simplify/Review as deferrable. Only Understand/Human can be deferred.
2. **Shortcutted skills** (`skills-shortcutted-as-lists`) — Ran simplify/review as summary lists, not actual sub-skills with parallel agents.
3. **Agents skipped workflow** (`agents-skip-workflow`) — Background/worktree agents only implemented, didn't run full VSR cycle.
4. **Plan not updated** (`plan-not-updated` ×3) — Forgot to update dashboard after steps completed.
5. **CSS animation misplacement** (`css-animation-misplacement`) — animationDelay on wrapper, animate-pulse on child. No review caught it.
6. **CORS/portless friction** (`env-config-mismatch`) — Didn't flag portless incompatibility proactively.
7. **Prompt token bloat** (`prompt-output-not-optimized`) — User identified token limit as root cause, not agent.
8. **CSS cleanups in walkthrough** (`simplify-missed-frontend-cleanup`) — Multiple class/spacing fixes found during understand, should have been caught by simplify.
9. **Broken app committed** (`broken-app-committed`) — App was non-functional at points and commits were made. User rule: never commit if E2E is broken.

### Self-Reflection

1. Wasted turns on portless debugging (`overcomplicating-env-setup`)
2. User only trusts verification as proof (`verification-is-proof`) — review/simplify passing ≠ confidence

### Patterns Crossing Threshold

- `workflow-steps-skipped` — 5 occurrences (rule already in AGENTS.md, needs strengthening)
- `plan-not-updated` — 3 occurrences (needs AGENTS.md rule)
- `unnecessary-type-cast` — 3 occurrences (existing rule covers this)
