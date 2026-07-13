---
name: commit-with-emoji
description: Review repository changes and create focused Git commits whose messages use an emoji prefix paired with a Conventional Commits type. Use when Codex is asked to commit, record, or checkpoint changes in this repository, including requests mentioning feat, fix, perf, chore, or another commit type.
---

# Commit with Emoji

Create focused, reviewable commits. Do not push unless the user explicitly asks.

## Commit Granularity

Before staging, group the diff into a short commit plan. A good commit has one
intent, can be described by one imperative subject, and leaves the repository in
a usable state. Prefer a small sequence of coherent commits over one broad
"update everything" commit.

| Keep together | Split apart |
| --- | --- |
| Production change and the tests required to prove it. | Unrelated features or bug fixes. |
| A metadata or version change and every file that must match it. | Documentation-only changes unrelated to the implementation. |
| A packaging behavior change and its packaging test or verification. | Build/package tooling changes and add-on runtime behavior. |
| A narrowly scoped feature and its directly necessary user documentation. | Repository skills, process instructions, or refactors unrelated to the requested behavior. |

Use separate commits when the files serve distinct purposes, even if they were
edited in the same working session. Do not split a change when either resulting
commit would fail its relevant tests, contain inconsistent metadata, or leave a
broken workflow. Stage individual paths or hunks as needed; never use `git add
-A` merely for convenience.

When more than one commit is appropriate, state the proposed order before
staging. Use dependency order: runtime behavior first, then tests and docs that
cannot stand alone; tooling or independent documentation may be separate.

## Workflow

1. Inspect `git status --short`, the staged diff, and the unstaged diff.
2. Make a commit plan when more than one focused commit is appropriate, following the granularity rules above.
3. Separate unrelated changes. Preserve user-owned edits and stage only the paths or hunks that belong to the current commit.
4. Run the smallest relevant validation available for the current commit. If validation cannot run or fails for a pre-existing reason, state that clearly instead of concealing it.
5. Choose the type and its matching emoji from the table below.
6. Write the subject in imperative mood, keep it concise, and describe the outcome rather than the implementation mechanics.
7. Commit with the format `<emoji> <type>(optional-scope): <summary>`.
8. Verify the result with `git status --short` and `git log -1 --oneline`, then continue with the next planned commit or report the commit hash, subject, validation, and remaining changes.

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
