---
name: commit-with-emoji
description: Review repository changes and create focused Git commits whose messages use an emoji prefix paired with a Conventional Commits type. Use when Codex is asked to commit, record, or checkpoint changes in this repository, including requests mentioning feat, fix, perf, chore, or another commit type.
---

# Commit with Emoji

Create one focused commit at a time. Do not push unless the user explicitly asks.

## Workflow

1. Inspect `git status --short`, the staged diff, and the unstaged diff.
2. Separate unrelated changes. Preserve user-owned edits and stage only the paths or hunks that belong to the requested commit; do not use `git add -A` indiscriminately.
3. Run the smallest relevant validation available for the changed files. If validation cannot run or fails for a pre-existing reason, state that clearly instead of concealing it.
4. Choose the type and its matching emoji from the table below.
5. Write the subject in imperative mood, keep it concise, and describe the outcome rather than the implementation mechanics.
6. Commit with the format `<emoji> <type>(optional-scope): <summary>`.
7. Verify the result with `git status --short` and `git log -1 --oneline`, then report the commit hash, subject, validation, and any remaining changes.

## Prefix table

| Type | Emoji | Use for |
| --- | --- | --- |
| `feat` | ✨ | Add user-visible behavior or capability. |
| `fix` | 🐛 | Correct a defect or unintended behavior. |
| `perf` | ⚡ | Improve runtime speed, memory use, or responsiveness. |
| `refactor` | ♻️ | Restructure code without changing behavior. |
| `docs` | 📝 | Change documentation only. |
| `test` | ✅ | Add or revise tests without changing production behavior. |
| `style` | 🎨 | Change formatting or style without changing behavior. |
| `build` | 📦 | Change packaging, dependencies, or the build system. |
| `ci` | 👷 | Change continuous-integration configuration or scripts. |
| `chore` | 🔧 | Perform repository maintenance not covered above. |
| `revert` | ⏪ | Revert an earlier commit. |

Prefer the most specific type. Use `chore` only when no more precise row applies. For a breaking change, append `!` after the type or scope, such as `✨ feat!: remove legacy sync mode`, and include a `BREAKING CHANGE:` footer when useful.

## Message examples

```text
✨ feat(sync): add clipboard retry controls
🐛 fix: preserve links containing spaces
⚡ perf(capture): reuse window lookup results
🔧 chore: refresh repository metadata
```

Add a commit body only when the subject cannot explain important motivation or constraints. Never place secrets, generated archives, or unrelated files in the commit.
