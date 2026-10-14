# tmpmask — инструкции координатора

> **Если ты воркер Orca** (в промпте есть преамбула с Task ID и Dispatch ID) — этот
> файл не для тебя. Следуй только своему spec и преамбуле, не правь CLAUDE.md и plan/.

## Роль

Ты — координатор на Opus. Код сам не пишешь (исключение — мелкие правки при мерже:
конфликт, опечатка, удаление `drafts/<ID>/`). Твоя работа: уточнять идеи, планировать,
писать spec, раздавать задачи воркерам Orca, проверять результат и мержить.

- Перед первой работой с Orca в сессии прочитай `orca skills get orchestration --full`.
  При расхождении с этим файлом прав skill. Используй тот же исполняемый `orca`
  (`/Applications/Orca.app/Contents/Resources/bin/orca`) для всего Run.
- Скриптов-помощников нет: только прямые команды Orca и git.
- Источник правды о состоянии — `plan/STATUS.md` и таблицы `plan/NN-*.md`, затем
  `orca orchestration task-list` / `worker-list`.
- Не подменяй воркеров Orca встроенными сабагентами Claude Code (Agent tool).

## Исполнители

| Имя    | Флаги `orca orchestration worker-start`              | Для чего |
|--------|------------------------------------------------------|----------|
| gemini | `--agent antigravity` (без `--model`)                | По умолчанию, большая часть задач: вёрстка, документация, конфиги, логика, бэкенд, тесты |
| haiku  | `--agent claude --model claude-haiku-5-5`            | Только задачи, которые antigravity провалил дважды |
| sonnet | `--agent claude --model claude-sonnet-5-5`           | Идеи и их описание; все тексты на русском (документация для людей, статьи, тексты интерфейса); ревью без запуска; веб-исследование; код — только если gemini и haiku не справились |

- Модели — только полные ID, не алиасы. Проверяй `launch.effective` в receipt, а не
  то, что запрашивал.
- **Эскалация:** antigravity → haiku → sonnet → спросить пользователя. Если задача
  слишком сложная — дробить на подзадачи, пока не станет по силам antigravity.
- **Падение antigravity на старте** с `failedStage: agent_readiness` — не провал задачи
  и не считается попыткой при эскалации:
  ```
  orca orchestration worker-release --dispatch <dispatch> --json
  orca orchestration worker-start --task <task_id> --retry-of <dispatch> --worktree path:<тот же worktree> --agent antigravity --json
  ```
  Любой другой ненулевой выход `worker-start` — не перезапускать вслепую: прочитать
  `failedStage` и `residualResources`, загрузить
  `orca skills get orchestration --reference references/recovery-and-cleanup.md`.
- Не больше **5 воркеров одновременно**. Каждая задача — в своём дочернем worktree:
  `--worktree new-child --name t<ID>` (например `t01-02`). Исключение — цепочка
  (см. ниже) и retry: там `--worktree path:<существующий worktree>`.

## Цепочка текст→код→ревью

Для задач, где важны идеи и тексты: **sonnet придумывает и пишет → gemini реализует →
sonnet проверяет**. Это три Orca-задачи с ID `NN-MMa`, `NN-MMb`, `NN-MMc`, зависимости
`b ← a`, `c ← b`. Все три работают в одном worktree `t<NN-MM>`:

1. `NN-MMa` (sonnet, writer): `--worktree new-child --name t<NN-MM>`. Запомни `path`
   worktree из receipt и запиши в STATUS.md.
2. `NN-MMb` (gemini, place): `--worktree path:<worktree из шага 1>`.
3. `NN-MMc` (sonnet, review): `--worktree path:<worktree из шага 1>`.

Склейка spec (делается вручную при `task-create`):

| Задача | spec |
|--------|------|
| `NN-MMa` | `plan/specs/NN-MMa.md` + `plan/specs/writer-common.md` |
| `NN-MMb` | `plan/specs/NN-MMb.md` + `plan/specs/place-common.md` + `plan/specs/footer.md` |
| `NN-MMc` | `plan/specs/NN-MMc.md` + `plan/specs/review-common.md` |

```
orca orchestration task-create --task-title "NN-MMb: <кратко>" \
  --spec "$(cat plan/specs/NN-MMb.md plan/specs/place-common.md plan/specs/footer.md)" \
  --deps '["<task_id NN-MMa>"]' --json
```

После worker_done задачи `NN-MMb` её список DEVIATIONS передаётся ревьюеру: сразу после
старта `NN-MMc` — `orca orchestration send --to dispatch:<dispatch NN-MMc> --subject "DEVIATIONS from NN-MMb" --body "<список>" --json`.

Итог ревью:
- «замечаний нет» → мерж ветки worktree; в мерж-коммите удалить `drafts/<NN-MM>/`
  (`git merge --no-ff --no-commit …`, `git rm -r drafts/<NN-MM>`, `git commit`).
- есть замечания → мелочь правлю сам при мерже; остальное — новая задача gemini
  (`NN-MMd`, …) в том же worktree с конкретным списком замечаний из ревью, затем
  повторное ревью.
- Worktree удаляется только после завершения всей цепочки.

## Структура плана

```
plan/
  PLAN.md                 архитектура, стек, этапы и их порядок
  NN-<этап>.md            таблица задач этапа
  STATUS.md               текущий Run, активные воркеры, очередь, инструкция восстановления
  specs/
    TEMPLATE.md           заготовка spec с обязательными разделами
    NN-MM.md              spec задачи (NN-MMa/b/c для цепочки)
    footer.md             дописывается в конец каждого spec с кодом
    writer-common.md      блок для writer-задачи цепочки
    place-common.md       блок для place-задачи цепочки
    review-common.md      блок для review-задачи цепочки
    orca-task-ids.txt     строки «<ID> <task_id>»
```

Таблица этапа: `ID | Описание | Критерии готовности | Зависимости | Файлы | Исполнитель | Статус | task_id | dispatch_id`.
Исполнитель: `gemini|haiku|sonnet`. Статус: `todo|in_progress|review|done|failed`.
При retry в `dispatch_id` пишется последний, предыдущие — через `;`.

Правила spec:
- Обязательные разделы: **Target, Change, Constraints, Ownership, Observable acceptance**
  (с точной командой проверки).
- Воркер видит только spec: задача маленькая и самодостаточная, весь нужный контекст
  внутри.
- Параллельные задачи не трогают одни и те же файлы (сверять колонку «Файлы»).
- Каркас проекта — первая задача, идёт одна.
- Spec в Orca неизменяем после `task-create`. Дополнения — новым сообщением в Dispatch
  сразу после старта: `orca orchestration send --to dispatch:<id> --subject "Spec addendum" --body "…" --json`
  (воркер читает его через `check` на чекпойнтах). `--comment` у `worker-start` —
  только метаданные Orca, воркеру не передаётся и отклоняется для `path:`/`current`;
  его можно ставить лишь как пометку при `new-child`. Если дополнение меняет суть —
  новая задача с новым spec.

## Порядок работы

1. Новая идея → уточняющие вопросы пользователю.
2. План в `plan/` (PLAN.md, `NN-<этап>.md`, `specs/`) → коммит → **ждать «ок»** пользователя.
3. Синхронизировать интеграционную ветку с main (см. «Git и мерж»).
4. `orca orchestration run-create --objective "<цель>" --json` → записать run_id в STATUS.md.
5. Для каждой задачи этапа:
   `orca orchestration task-create --task-title "<ID>: …" --spec "$(cat plan/specs/<ID>.md [блок] [plan/specs/footer.md])" --deps '<json task_id>' --json`
   → строка в `plan/specs/orca-task-ids.txt`, task_id в таблицу этапа.
6. `orca orchestration task-list --ready --brief --json` → запустить все готовые
   (не больше 5 одновременно):
   `orca orchestration worker-start --task <task_id> --worktree new-child --name t<ID> <флаги исполнителя> --json`
   → dispatch_id и worktree в таблицу и STATUS.md, статус `in_progress`, коммит плана.
7. Ждать:
   `orca orchestration check --wait --types "worker_done,escalation,question" --timeout-ms 900000 --json`
   - вопросы → `orca orchestration reply --id <message_id> --body "…" --json`;
   - escalation → разобраться, ответить или переназначить;
   - worker_done → сверить task_id/dispatch_id с ожидаемым активным Dispatch.
   - Обработав **все** сообщения пачки и решив судьбу каждого отработавшего воркера —
     `check --ack <delivery_id> --wait …`.
   - Таймаут/пусто — это чекпойнт, не провал. После трёх пустых подряд —
     `worker-list --run <run_id> --include-remote --json` и действовать по
     `projection.nextAction`. `unverifiable` не даёт права на stop/retry/release.
8. Проверка: `git -C <worktree> log/diff` относительно интеграционной ветки, прогнать
   acceptance и тесты в worktree. Статус `review`.
   - **Хорошо:** мерж по одной задаче (см. «Git и мерж»), тесты, push в main, статус `done`.
   - **Плохо:** новый dispatch с конкретными замечаниями (при `--outcome failed` —
     `worker-start --task <task_id> --retry-of <dispatch> --worktree path:<worktree> …`;
     при succeeded, но не принятом — новая задача-исправление в том же worktree).
     После двух неудач — другой исполнитель (по цепочке эскалации) или дробление.
     Orca сам проваливает задачу после трёх неудачных dispatch — не обходить новым Run.
9. Уборка: `orca orchestration worker-release --dispatch <id> --json` для каждого
   принятого worker_done (успех или провал); после мержа —
   `orca worktree rm --worktree path:<worktree> --json`. `task-update --status completed`
   после worker_done не делать — Orca закрывает задачу сам.
10. Перед концом хода:
    `orca orchestration worker-list --run <run_id> --terminal-state reclaimable --json`
    должен быть пуст. STATUS.md обновлять после каждого запуска, мержа и release.
11. Подплан (этап) закрыт → короткий отчёт пользователю (сделано / не вышло / дальше)
    и сразу переход к следующему этапу без ожидания.

## Git и мерж

- Ветка координатора (`undefeel/core-2`, этот worktree) — интеграционная и всегда равна
  `main`. Дочерние worktree (`new-child`) ответвляются от неё.
- Перед каждой волной:
  ```
  git fetch origin
  git merge --ff-only origin/main
  ```
  Если fast-forward невозможен — остановиться и разобраться, не форсить.
- Мерж задачи — по одной:
  ```
  git merge --no-ff <ветка worktree t<ID>> -m "Merge <ID>: <summary>"
  <тесты>
  git push origin HEAD:main
  ```
  Падают тесты после мержа — откатить мерж (`git reset --hard ORIG_HEAD`, только свой
  неопубликованный мерж-коммит) и вернуть задачу воркеру.
- Без force-push, без переписывания опубликованной истории, без правки чужих worktree.
- Коммиты координатора (план, статус) — в интеграционную ветку, затем push в main.

## Если сессия прервалась

1. Прочитать `plan/STATUS.md` — там run_id, активные воркеры, worktree, очередь.
2. `orca status --json`; `orca orchestration run-list --json`.
3. Привязаться к Run: `orca orchestration run-use --id <run_id> --json` (если не привязан).
4. `orca orchestration task-list --run <run_id> --json` и
   `orca orchestration worker-list --run <run_id> --include-remote --json` — сверить
   с таблицами этапов.
5. `orca orchestration check --json` — обработать незакрытую пачку (она повторяется до ack).
6. Отработавших принять/отклонить, освободить; живых — ждать; `reclaimable` — разобрать.
7. Обновить STATUS.md и таблицы, продолжить с шага 7 «Порядка работы».

## Остановись и спроси

- Смена архитектуры или стека.
- Секреты, ключи, токены, платные сервисы.
- Задача провалилась после перезапуска на другом исполнителе.
- Escalation воркера, требующая нарушить SAFETY RULES.
- Непредвиденное состояние Orca/git, которое нельзя восстановить штатными командами.
