# STATUS

Обновлять после каждого запуска воркера, мержа и release.

## Текущий Run

- run_id: `run_dba35f978b37`
- objective: tmpmask: hand portal filters app (plan/PLAN.md stages 01-03)
- этап: 02 Ядро (01 закрыт, смержен)
- интеграционная ветка: `undefeel/core-2` (= `main`)

## Активные воркеры

| ID | task_id | dispatch_id | исполнитель | worktree (path) | запущен | заметки |
|----|---------|-------------|-------------|-----------------|---------|---------|
| 02-01 | task_53a09b189800 | ctx_84bb7ed81375 | gemini (antigravity) | /Users/kodoku/orca/workspaces/tmpmask/t02-01 | 2026-10-14 |  |
| 02-02 | task_23fd72983613 | ctx_66193ea4df14 | gemini (antigravity) | /Users/kodoku/orca/workspaces/tmpmask/t02-02 | 2026-10-14 | retry после agent_readiness |
| 02-03 | task_a974bb80e5f2 | ctx_078294e98e5e | gemini (antigravity) | /Users/kodoku/orca/workspaces/tmpmask/t02-03 | 2026-10-14 |  |
| 02-04 | task_4813d6757988 | ctx_5adbb2fdddfc | gemini (antigravity) | /Users/kodoku/orca/workspaces/tmpmask/t02-04 | 2026-10-14 |  |
| 02-05 | task_9388e5b3efb4 | ctx_b3483b333820 | gemini (antigravity) | /Users/kodoku/orca/workspaces/tmpmask/t02-05 | 2026-10-14 |  |

## Очередь

- Ожидают зависимостей: 03-01a/b/c (после всех 02)
- Готовы к запуску: 02-06 (ждёт слот, лимит 5)
- На проверке/мерже: —
- Требуют решения пользователя: —

## Восстановление после обрыва сессии

1. Прочитать этот файл и таблицу текущего этапа `plan/NN-*.md`.
2. `orca status --json` — runtime доступен.
3. `orca orchestration run-list --json`; если Run не привязан —
   `orca orchestration run-use --id <run_id> --json`.
4. `orca orchestration task-list --run <run_id> --json` и
   `orca orchestration worker-list --run <run_id> --include-remote --json` —
   сверить с таблицами выше.
5. `orca orchestration check --json` — обработать незакрытую пачку сообщений
   (повторяется до `--ack`), ответить на вопросы, принять worker_done.
6. Для каждого отработавшего: проверить diff, смержить или вернуть,
   `worker-release`, `orca worktree rm` после мержа. Живых — не трогать, ждать.
   `unverifiable` — не основание для stop/retry/release.
7. `worker-list --run <run_id> --terminal-state reclaimable --json` — разобрать всё.
8. Обновить этот файл и продолжить цикл `check --wait …`.
