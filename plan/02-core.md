# 02 — Ядро

Перед стартом этапа координатор кладёт `models/hand_landmarker.task` в репо (коммит в main).
Все задачи независимы, файлы не пересекаются. 02-06 ждёт свободного слота (лимит 5).

| ID | Описание | Критерии готовности | Зависимости | Файлы | Исполнитель | Статус | task_id | dispatch_id |
|----|----------|---------------------|-------------|-------|-------------|--------|---------|-------------|
| 02-01 | Реестр 8 фильтров | тесты: форма/dtype сохраняются, каждый фильтр меняет кадр, порядок id | 01-01 | `tmpmask/filters.py`, `tests/test_filters.py` | gemini | done | task_53a09b189800 | ctx_84bb7ed81375 |
| 02-02 | Портал: полигон из рук, маска, применение фильтра с прозрачностью, рамка | тесты на порядок точек, пиксели внутри/снаружи, opacity 0/1 | 01-01 | `tmpmask/portal.py`, `tests/test_portal.py` | gemini | done | task_23fd72983613 | ctx_181e166c5ea7; ctx_66193ea4df14 |
| 02-03 | Сглаживание и fade портала | тесты EMA, fade-in/out, удержание и сброс | 01-01 | `tmpmask/smoothing.py`, `tests/test_smoothing.py` | gemini | done | task_a974bb80e5f2 | ctx_078294e98e5e |
| 02-04 | Жест щепоти с фронтом и кулдауном | тесты: одно срабатывание на щепоть, кулдаун, раскрытая рука не срабатывает | 01-01 | `tmpmask/gestures.py`, `tests/test_gestures.py` | gemini | done | task_4813d6757988 | ctx_5adbb2fdddfc |
| 02-05 | Трекер MediaPipe → `list[Hand]` | тесты: пустой кадр → [], конвертация landmark → пиксели | 01-01 | `tmpmask/tracker.py`, `tests/test_tracker.py` | gemini | done | task_9388e5b3efb4 | ctx_b3483b333820 |
| 02-06 | Скриншоты и запись MP4 | тесты во временной папке: PNG читается, MP4 непустой, имена по времени | 01-01 | `tmpmask/capture.py`, `tests/test_capture.py` | gemini | done | task_64cc70401c36 | ctx_efffe9885970 |
