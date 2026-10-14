# 03 — Приложение (цепочка текст→код→ревью)

Все три задачи — в одном worktree `t03-01`.

| ID | Описание | Критерии готовности | Зависимости | Файлы | Исполнитель | Статус | task_id | dispatch_id |
|----|----------|---------------------|-------------|-------|-------------|--------|---------|-------------|
| 03-01a | Документ идей UX/CLI/главного цикла + черновики всех русских текстов (texts.toml, README) | `docs/design/app.md` и `drafts/03-01/*.md` закоммичены | 02-* | `docs/design/app.md`, `drafts/03-01/` | sonnet | todo | task_2bbce068c613 | — |
| 03-01b | Реализация: config, загрузчик текстов, app-цикл, `__main__`, README по документу | ruff+pytest зелёные; `--help` на русском; headless-тест цикла; DEVIATIONS перечислены | 03-01a | `tmpmask/config.py`, `tmpmask/texts.py`, `tmpmask/texts.toml`, `tmpmask/app.py`, `tmpmask/__main__.py`, `tests/test_config.py`, `tests/test_texts.py`, `tests/test_app.py`, `README.md` | gemini | todo | task_55c5fb5cf41a | — |
| 03-01c | Ревью текстов и реализации | вердикт «замечаний нет» или список замечаний | 03-01b | — (только чтение) | sonnet | todo | task_a24c42c3a904 | — |
