---
name: btw-pull-request
description: >
  Commits unrelated files to a clean PR without disrupting the current branch. Creates a
  temporary worktree off the base branch, copies specified files in, commits, pushes, and
  optionally opens a PR — then cleans up. Use when you have changes (README updates, config
  fixes, env templates, CI tweaks) that should land independently of the feature branch
  you're working on. Trigger when the user says "push this to a clean branch", "make a
  separate PR for this", "btw PR", or when you notice unrelated changes mixed into feature
  work that should be split out.
---

# BTW Pull Request

You are splitting unrelated changes out of the current working branch into a clean PR off
the base branch. The goal is zero disruption to in-progress work.

## When to Use

- Config, README, env, CI, or tooling changes made while working on a feature branch
- Any files that should land independently and not be blocked by the feature PR
- Quick fixes noticed during feature work that belong on their own

## Inputs

The user provides (or you identify from context):
- **Files to include** — specific file paths to commit
- **Branch name** — e.g., `chore/readme-update` (suggest one if not provided)
- **Base branch** — defaults to `main`
- **Whether to open a PR** — defaults to yes

## Workflow

### Step 1: Validate

- Confirm which files to include. List them and ask the user to confirm if ambiguous.
- Verify the files exist in the current working directory.
- Pick a branch name (or use the user's).

### Step 2: Create Worktree

```bash
git worktree add /tmp/<branch-name> <base-branch> -b <branch-name>
```

This creates an isolated copy off the base branch. The current branch is untouched.

### Step 3: Copy Files

Copy each file from the current working directory to the worktree, preserving directory
structure. Create any necessary parent directories.

```bash
mkdir -p /tmp/<branch-name>/<parent-dirs>/
cp <source-path> /tmp/<branch-name>/<same-path>
```

**Important:** Only copy the specified files. Do not copy unrelated changes.

### Step 4: Commit

```bash
cd /tmp/<branch-name>
git add <files...>
git commit -m "<message>

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

Draft a concise commit message based on what the files do. Show the full `git diff` to
the user before committing so they can confirm.

### Step 5: Push

```bash
cd /tmp/<branch-name>
git push -u origin <branch-name>
```

### Step 6: Create PR (if requested)

```bash
gh pr create --title "<title>" --body "$(cat <<'EOF'
## Summary
<bullets>

## Notes
Split from feature branch — these changes are independent.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

### Step 7: Clean Up

```bash
git worktree remove /tmp/<branch-name>
```

Report the PR URL and confirm the current branch is unchanged.

## Safety Rules

- **Never stash, checkout, or modify the current branch.** All work happens in the worktree.
- **Never include feature-branch commits.** Only copy files — do not cherry-pick or merge.
- If a file only exists on the feature branch (not on the base), it will be created fresh
  in the worktree. That's fine.
- If a file exists on both branches, the worktree copy starts from the base-branch version
  and your copy overwrites it. Show the diff so the user can verify.
- Always clean up the worktree when done, even if a step fails.

## Error Handling

- If `git worktree add` fails (branch exists), ask the user if they want to reuse or rename.
- If `git push` fails (branch exists on remote), ask before force-pushing.
- If any step fails, clean up the worktree before reporting the error.
