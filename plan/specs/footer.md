
---

## GENERAL RULES

- Project context: tmpmask is a Python 3.12 desktop app: a webcam window where two hands form a quadrilateral "portal" (thumb and index fingertips of each hand) and an image filter is applied inside it. Package `tmpmask/` with small, camera-free testable modules (handtypes, tracker, portal, smoothing, gestures, filters, capture, config, texts, app). Stack: opencv-python, mediapipe (Tasks API `HandLandmarker`, never the legacy `mp.solutions`), numpy, pytest, ruff; packaging via `pyproject.toml` with a `dev` extra.
- Environment: if `.venv` is missing in your worktree, create it with `/opt/homebrew/bin/python3.12 -m venv .venv && .venv/bin/pip install -e '.[dev]'`. `.venv` is git-ignored; never commit it. Full check: `.venv/bin/ruff check . && .venv/bin/pytest -q` — it must stay green, including tests you did not write.
- Tests must not need a camera, a display, or network access.
- This spec is everything you get. Do not edit `CLAUDE.md` or anything under `plan/`.
- Identifiers and code comments in English; user-facing texts (UI strings, docs for people) in Russian.
- Edit only the files listed under **Ownership**. If another file must change, do not edit it — explain why in `worker_done`.
- When finished: run every command from **Observable acceptance**; commit to the current branch with the message `"<TASK ID>: <summary>"` (TASK ID is the plan ID at the top of this spec, e.g. `01-02`). No push, no merge, no branch switching.
- Send `worker_done` listing the commands you ran and their results. Use `--outcome failed` if any acceptance check does not pass; never hide failure in prose.

## SAFETY RULES

- Work only inside your own worktree.
- No sudo, no global installs, no edits to shell profiles, `git config`, SSH, or system settings.
- No destructive commands; no force operations on other branches or worktrees.
- Docker: only your own objects with a unique prefix (`t<TASK ID>-`); remove them when done; no `prune`; never touch anything else.
- Network: package registries and documentation only.
- If the task requires breaking any of these rules, stop and send an `escalation` instead.
