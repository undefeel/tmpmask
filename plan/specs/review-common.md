
---

## REVIEW RULES (read-only review stage)

You only read. Do not edit, create, or commit anything; do not run the application or tests.

1. Texts: for each file in `drafts/<TASK ID>/` compare its body with the file named in its `<!-- target: ... -->` line, using `diff` (or `git diff --no-index`). Classify every mismatch as one of: **искажение** (meaning changed), **выдумка** (text added that is not in the draft), **потеря** (draft text missing), **косметика** (whitespace, punctuation, formatting).
2. Implementation: compare the code with `docs/design/<topic>.md` and with the `DEVIATIONS` list in the implementation commit/report; check names, paths, formats, edge cases, and verification criteria.
3. Send `worker_done --outcome succeeded` (the review itself is complete even when it finds problems) with:
   - table «тексты»: `файл | вид | в черновике | в итоге`;
   - table «реализация»: `что | проблема | где в коде | что исправить`;
   - verdict on the last line: `замечаний нет` or `замечаний: N (критичных: K)`.
   Use `--outcome failed` only if you could not perform the review.

Safety: work only inside your worktree; no sudo, installs, profile/git config/SSH/system changes, no network; if anything requires more, send an `escalation`.
