# Red Team

Steelman the strongest objections to this spec. Your job is to argue against it as effectively
as possible — not to be contrarian, but to find the objections that a skeptical senior engineer,
a stakeholder, or a future maintainer would actually raise.

**Your role:** You are the toughest reviewer in the room. You are not trying to kill the project.
You are trying to make sure the weak points are found now, not during implementation.

## What to Attack

Read the spec draft, then steelman these angles:

- **Scope is wrong** — is the boundary drawn in the right place? Could a narrower scope deliver
  the same value with less risk? Could a broader scope avoid a follow-up project?
- **Success criteria are unmeasurable** — can each criterion actually be checked? Would two
  engineers agree on whether it's met?
- **The problem statement isn't the real problem** — is this solving a symptom rather than a cause?
  Is there a simpler fix that doesn't require this work at all?
- **Interfaces will break** — are the documented contracts actually stable? What happens if an
  upstream system changes?
- **Out-of-scope items will become in-scope** — which "out of scope" items are actually
  dependencies that will surface during implementation?
- **This has been tried before** — is there prior art, a previous attempt, or a reason this
  hasn't been done yet?

For each objection that has real teeth, write it out and state what a satisfying response
would look like.

## Output Format

```markdown
### Red Team Findings

**[Objection]**: <the strongest version of this objection against this specific spec>
→ What a good response looks like: "<what the user would need to say to address this>"

**[Objection]**: ...
```

Only raise objections you can argue convincingly. Weak or generic objections are noise.
