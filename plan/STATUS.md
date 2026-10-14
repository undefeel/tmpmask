# STATUS

Обновлять после каждого запуска воркера, мержа и release.

## Текущий Run

- run_id: — (не создан; ждём «ок» по плану)
- objective: —
- этап: план готов, ждём «ок» (этапы 01 → 02 → 03 → 04)
- интеграционная ветка: `undefeel/core-2` (= `main`)

## Активные воркеры

| ID | task_id | dispatch_id | исполнитель | worktree (path) | запущен | заметки |
|----|---------|-------------|-------------|-----------------|---------|---------|
| — | | | | | | |

## Очередь

- Ожидают зависимостей: 02-01…02-06 (после 01-01 и модели), 03-01a/b/c (после 02)
- Готовы к запуску: 01-01 (после «ок»)
- На проверке/мерже: —
- Требуют решения пользователя: «ок» по плану

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
