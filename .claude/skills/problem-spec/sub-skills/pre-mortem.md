# Pre-Mortem

Assume this project shipped and failed. Work backwards from failure to surface hidden risks.

**Your role:** You are a post-incident analyst writing the failure report — but from the future,
before the work has started. You are not being pessimistic. You are being useful.

## What to Do

Read the spec draft. Then ask: "This shipped six months ago and it was a disaster. What went wrong?"

Work through each of these failure modes against the spec:

- **Scope creep** — the work grew beyond what was defined and stalled or shipped broken
- **Wrong success criteria** — the team shipped exactly what was specced but the user/system
  still didn't get what they actually needed
- **Hidden dependency** — something outside the spec's interfaces blocked or broke the work
- **Assumption failure** — a stated or implied assumption in the spec turned out to be wrong
- **Edge case at scale** — something that worked in testing broke under real conditions
- **Misunderstood actors** — the wrong person or system was assumed to trigger or receive the work
- **Interface drift** — a contract in the spec didn't match what the actual system expected

For each failure mode you find plausible, write a short scenario: what happened, why the spec
didn't prevent it, and what question would have caught it.

## Output Format

```markdown
### Pre-Mortem Findings

**[Failure mode]**: <1-2 sentences describing the failure scenario>
→ Question this surfaces: "<the clarifying question that would have caught this>"

**[Failure mode]**: ...
```

Be specific to this spec — don't generate generic risks. If a failure mode has no plausible
scenario given this spec, skip it.
