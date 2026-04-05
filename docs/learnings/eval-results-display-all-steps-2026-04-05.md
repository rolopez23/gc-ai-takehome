# Learnings: eval-results-display / all steps — 2026-04-05

## Post-Human Additions

**New loggable events:** 5

1. `simplify-missed-frontend-cleanup` — Simplify said "clean" but human drove 9 refactors (component extraction, semantic HTML, named classes, reduce, aria, style constants, test assertions). **Fix applied:** created `sub-skills/frontend-cleanup.md` for simplify skill.

2. `brittle-style-assertions` — Tests asserted raw Tailwind classes. Human pushed to test against semantic `COLORS.fail`/`COLORS.warning`/`COLORS.pass` constants instead. Covered in new frontend-cleanup sub-skill §7.

3. `committed-to-main` — 20+ feature commits went to main. **Fix applied:** added "Feature branch required" rule to AGENTS.md.

4. `verify-not-automatic` (3rd occurrence) — Verification skipped on steps 2 and 3. Shimmer flicker bug found by user, not agent. User notes their "run independently" instruction may have been partial cause. Logging but sitting on it.

5. `accessibility-not-reviewed` (2nd occurrence) — Missing aria-label, aria-expanded, ul/li semantics. Covered in new frontend-cleanup sub-skill §3.

## Patterns Checked

| Tag | Count | Threshold? |
|---|---|---|
| `simplify-missed-frontend-cleanup` | 1 (new) | No |
| `brittle-style-assertions` | 1 (new) | No |
| `committed-to-main` | 1 (new) | No |
| `verify-not-automatic` | 3 | **Yes** — already addressed in AGENTS.md |
| `accessibility-not-reviewed` | 2 | Not yet |
| `simplify-missed-readability` | 2 (prior) | Not yet — but frontend-cleanup sub-skill may address |

## Actions Taken

- **AGENTS.md**: Added "Feature branch required" rule
- **simplify/SKILL.md**: Added sub-skills section pointing to frontend-cleanup
- **simplify/sub-skills/frontend-cleanup.md**: Created — covers component extraction, semantic HTML, accessibility, readable class names, data transformations, style constants, test assertion patterns
