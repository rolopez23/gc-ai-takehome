---
name: problem-spec
description: >
  First step for solving any complex coding problem. Defines what is and is not being solved,
  identifies all existing interfaces and contracts touched, and produces a structured spec doc.
  Trigger this skill whenever a user asks to build, implement, add, or solve something non-trivial.
  Do NOT trigger for small changes, refactors of a single function, or bug fixes. If there is any
  doubt about whether the problem is complex enough to warrant a spec, trigger it anyway — it is
  much cheaper to over-spec than to under-spec.
---

# Problem Specification Skill

Your job is to define the problem clearly before any solution is considered. You are not designing
the implementation. You are not suggesting technologies. You are figuring out exactly what needs to
be true when this work is done — and exactly what is out of scope.

## Ground Rules

- **Never assume.** If anything is ambiguous, ask. A wrong assumption here costs far more than a
  clarifying question.
- **No solution talk.** If the user starts describing how they want to build it, redirect:
  "Let's lock down the what before the how."
- **No partial specs.** Do not write the spec file until you have answers to every open question.

---

## Step 1: Understand the Problem

Ask the user to describe what they want to achieve. Listen for:

- The goal — what changes in the world when this is done?
- The actors — who or what initiates this? who or what receives the result?
- The trigger — what causes this to happen?
- The success condition — how will we know it worked?

Do not move on until you can restate the problem back in your own words and the user confirms it.

---

## Step 2: Clarify Until There Is No Ambiguity

Go through every noun and verb in the problem statement and ask: "Is this fully defined?" If not,
ask the user. Common sources of ambiguity:

- Vague quantities ("some", "a few", "many", "fast")
- Undefined entities ("the user", "the system", "the data" — which one?)
- Implicit behaviors ("it should update X" — when? how? what if X doesn't exist?)
- Edge cases ("what if there's nothing to process?", "what if it fails halfway?")
- Ownership ("who calls this?", "who owns the output?")

Ask one or two questions at a time — don't batch them.

---

## Step 3: Define the Boundary

Explicitly define what is and is not included:

**In scope**: What must be true when this work is complete? Keep this tight.

**Out of scope**: What are we explicitly not solving? Name adjacent, tempting, or frequently
assumed items and mark them out of scope. If the user is unsure whether something is in or out,
it needs a decision now.

---

## Step 4: Define Interfaces

Identify every connection point between this work and anything that already exists. Document:

- **Schemas** — data structures read or written; field names, types, constraints; before/after if changing
- **API contracts** — what is called or exposed; expected inputs/outputs; auth, rate limits, error shapes
- **System boundaries** — external systems, services, or processes that touch this work
- **Shared state** — anything read or written that another part of the system also owns

If the user doesn't know what a schema looks like — that is a blocker. Help them find it first.

---

## Step 5: Identify Current Code

Document all code likely to be touched and any prior art that is similar. Define the interfaces
above and describe how they interact. This is not a design doc — just what exists and how it
relates to the problem.

---

## Step 6: Write a Draft Spec

Write a draft to `docs/<feature-name>/spec.md`. Use this structure:

```markdown
# Spec: <Feature Name>

## Problem Statement
One to three sentences. What is broken or missing, and why does it matter?

## What We Are Solving
Bullet list. Each item is a concrete, verifiable outcome.

## What We Are NOT Solving
Bullet list. Each item is something explicitly excluded.

## Actors & Triggers
Who or what initiates this work, and under what conditions.

## Success Criteria
How will we know this is done? What can be checked or observed?

## Interfaces

### Schemas
For each schema touched: name, relevant fields (with types), and any changes being made.

### Contracts
For each external system or API: what we call, what we pass, what we get back.

### Shared State
Anything this work reads or writes that is also owned by another part of the system.

### Existing Code
Reference code expected to be touched and how it relates to the interfaces above.

## Open Questions
Questions that came up but are deferred. Note who needs to answer each.
```

Omit empty sections. Tell the user this is a draft — you will stress-test it before finalizing.

---

## Step 7: Stress-Test the Draft

Dispatch three subagents in parallel against the draft. Each gets the full spec draft text and
its sub-skill instructions from `sub-skills/`:

- `sub-skills/pre-mortem.md` — assumes failure and works backwards to surface hidden risks
- `sub-skills/red-team.md` — steelmans the strongest objections to scope, criteria, and interfaces
- `sub-skills/socratic.md` — probes unvalidated assumptions with targeted questions

**Subagent prompt template:**

```
You are stress-testing a problem spec. Follow the sub-skill instructions exactly.

## Sub-skill instructions
<contents of sub-skills/<reviewer>.md>

## Spec draft
<full spec content>
```

Do not pre-filter the findings. Surface everything.

---

## Step 8: Re-Interview the User

Synthesize the three sets of findings into a prioritized set of questions and challenges.
Do not present all three outputs raw — distill them:

1. **Group by theme** — multiple reviewers often surface the same gap from different angles;
   merge these into one question
2. **Rank by impact** — lead with findings that would change the spec materially if answered;
   put speculative or minor ones at the end
3. **Frame as questions** — even findings from the red team and pre-mortem should be presented
   as questions to the user, not verdicts

Present to the user:

```
The spec looks solid, but the stress-test raised some things worth resolving before we lock it in:

**[Theme]**: <question or challenge>
**[Theme]**: <question or challenge>
...

Any of these change your thinking?
```

Wait for responses. Update the spec draft with each answer. If an answer surfaces new ambiguity,
ask a follow-up before moving on.

---

## Step 9: Finalize the Spec

Once the re-interview is complete and all stress-test findings are resolved:

- Update `docs/<feature-name>/spec.md` with the final answers
- Move any unresolved items to the Open Questions section with an owner
- Tell the user where the file was saved and ask them to review it before any implementation begins

The spec is done when the user signs off. Then run `/plan`.
