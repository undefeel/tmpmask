# Приложение tmpmask: CLI, тексты, управление, главный цикл

Документ для реализатора (03-01b) и ревьюера (03-01c). Готовые модули не менять:
`handtypes`, `tracker`, `portal`, `smoothing`, `gestures`, `filters`, `capture`.
Русские тексты — в `drafts/03-01/texts.md` (→ `tmpmask/texts.toml`) и
`drafts/03-01/readme.md` (→ `README.md`); переносить дословно, первую строку
`<!-- target: ... -->` не копировать.

## 1. Файлы

| Файл | Содержимое |
|------|-----------|
| `tmpmask/texts.toml` | все русские строки (из черновика) |
| `tmpmask/texts.py` | загрузчик, `t(key, **kwargs)` |
| `tmpmask/config.py` | `Config`, `build_parser()`, `parse_args(argv)` |
| `tmpmask/app.py` | `run(...)`, `main(argv=None) -> int`, исключения, константы |
| `tmpmask/__main__.py` | `from tmpmask.app import main` + `raise SystemExit(main())` |
| `README.md` | из черновика |
| `tests/test_texts.py`, `tests/test_config.py`, `tests/test_app.py` | см. раздел 9 |

`pyproject.toml` уже включает `*.toml` в package-data — не менять.

## 2. Тексты

### 2.1 `tmpmask/texts.py`

- Читает `texts.toml` рядом с модулем через `tomllib` (stdlib), один раз, кэш `functools.cache`.
- `t(key: str, **kwargs) -> str`: ключ — путь через точку, `"messages.filter_switched"`,
  `"filters.purple"`, `"cli.camera"`. Значение обязано быть строкой.
- Возвращает `value.format(**kwargs)`. Строки без подстановок тоже проходят `format`
  (поэтому `%(default)s` в справке безопасен, а литеральные `{`/`}` пишутся `{{`/`}}`).
- Отсутствует ключ (или путь ведёт в таблицу, не в строку) → `KeyError(f"Нет текста: {key}")`.
  Не подставлять заглушку молча. Нет нужного kwarg → `KeyError` от `str.format` (не гасить).
- `filter_name(filter_id) -> str` = `t(f"filters.{filter_id}")`.

### 2.2 Структура `texts.toml`

Таблицы: `app` (`title`), `filters` (8 ключей = `FILTER_IDS`), `cli` (описание и справка
каждой опции), `cli_errors`, `messages`, `errors`. Точный список ключей и подстановок:

| Ключ | Подстановки |
|------|-------------|
| `app.title` | — |
| `filters.<id>` | — |
| `cli.description`, `cli.help` | — |
| `cli.camera`, `cli.width`, `cli.height`, `cli.mirror`, `cli.output_dir`, `cli.model` | `%(default)s` (argparse) |
| `cli.filter` | `{filters}` + `%(default)s` |
| `cli_errors.not_an_int` | `{value}` |
| `cli_errors.negative`, `cli_errors.not_positive` | `{value}` |
| `cli_errors.unknown_filter` | `{value}`, `{filters}` |
| `messages.startup_hint` | `{filter}` (русское имя), `{output_dir}` |
| `messages.filter_switched` | `{name}` |
| `messages.screenshot_saved`, `messages.recording_started`, `messages.recording_stopped` | `{path}` |
| `messages.exit` | — |
| `errors.camera_open` | `{index}` |
| `errors.camera_no_frame` | — |
| `errors.model_missing` | `{path}` |
| `errors.output_dir` | `{path}`, `{error}` |
| `errors.screenshot_failed`, `errors.recording_failed` | `{error}` |

Тест `test_texts.py` проверяет: все ключи из таблицы есть; `filters` содержит ровно `FILTER_IDS`;
все значения — непустые строки; `t("messages.filter_switched", name="X") == "Фильтр: X"`;
отсутствующий ключ → `KeyError`.

## 3. CLI (`tmpmask/config.py`)

```python
@dataclass(frozen=True)
class Config:
    camera: int = 0
    width: int = 1280
    height: int = 720
    mirror: bool = True
    filter: str = "purple"
    output_dir: Path = Path("captures")
    model: Path = DEFAULT_MODEL_PATH
```

`parse_args(argv: Sequence[str] | None = None) -> Config`; `build_parser() -> ArgumentParser`.
`prog="tmpmask"`, `description=t("cli.description")`, `add_help=False` и вручную
`-h/--help` с `help=t("cli.help")` (чтобы строка справки была русской).
Заголовки `usage:` / `options:` выдаёт argparse сам — это допустимо.

| Опция | type | default | Ограничения / ошибка |
|-------|------|---------|----------------------|
| `--camera` | `_int_min(0)` | `0` | не целое → `cli_errors.not_an_int`; <0 → `negative` |
| `--width` | `_int_min(1)` | `1280` | не целое → `not_an_int`; ≤0 → `not_positive` |
| `--height` | `_int_min(1)` | `720` | то же |
| `--mirror` / `--no-mirror` | `argparse.BooleanOptionalAction` | `True` | один `help=t("cli.mirror")` |
| `--filter` | `_filter_id` | `"purple"` | нет в `FILTER_IDS` → `unknown_filter` (без `choices=`, чтобы сообщение было русским) |
| `--output-dir` | `Path` | `Path("captures")` | проверка записи — в `main`, не в парсере |
| `--model` | `Path` | `DEFAULT_MODEL_PATH` | существование проверяется в `main` |

Валидаторы бросают `argparse.ArgumentTypeError(t(...))`. Ошибка парсинга → argparse печатает
`usage` + сообщение в stderr и завершает процесс с кодом 2 (`SystemExit(2)`); `main` не перехватывает.
`--help` → код 0. Для `--filter` в справке `t("cli.filter", filters=", ".join(FILTER_IDS))`.
В `help=` для остальных опций использовать `%(default)s` как в тексте.

## 4. Управление

Клавиши берутся как `key = cv2.waitKey(1) & 0xFF` (−1 → 255, считать «нет клавиши»: `0xFF` не
сопоставлять). Стрелки не используются. Регистр не важен (`N` и `n` одинаково).

| Клавиша | Действие |
|---------|----------|
| `n` | следующий фильтр (`next_filter_id(cur, +1)`) |
| `p` | предыдущий (`next_filter_id(cur, -1)`) |
| `1`…`8` | `FILTER_IDS[int(ch) - 1]` — прямой выбор |
| `s` | скриншот |
| `r` | старт/стоп записи |
| `q`, `Esc` (27) | выход |

Жест: `PinchTrigger.update(hands, now_s)` истинен → как `n`. Работает при любом числе рук.
Любое переключение (клавиша или жест) печатает `messages.filter_switched` с русским именем;
повторный выбор того же фильтра (`3`, когда уже 3) не печатает ничего.

Индикатор записи: красная заливка круга, BGR `(0, 0, 255)`, `cv2.LINE_AA`; радиус
`r = max(6, round(h / 72))`, центр `(w - 3*r, 3*r)` (правый верхний угол). Текста на кадре нет.
Рисуется на копии кадра только для показа; в скриншоты и видео точка **не** попадает.

## 5. Главный цикл (`tmpmask/app.py`)

### 5.1 Константы и исключения

```python
KEY_NONE = -1           # show вернул "клавиши нет"
KEY_WINDOW_CLOSED = -2  # show вернул "окно закрыто мышью"
EXIT_OK = 0; EXIT_USAGE = 2; EXIT_CAMERA_OPEN = 3
EXIT_CAMERA_LOST = 4; EXIT_MODEL_MISSING = 5; EXIT_OUTPUT_DIR = 6

class FrameReadError(Exception): ...   # камера не вернула кадр
```

### 5.2 `run`

```python
def run(
    frames: Iterable[np.ndarray],            # BGR uint8
    tracker,                                 # объект с detect(frame, ts_ms) -> list[Hand]
    config: Config,
    clock: Callable[[], float] = time.monotonic,       # секунды
    show: Callable[[np.ndarray], int] | None = None,   # показывает кадр, возвращает код клавиши
    say: Callable[[str], None] = print,                # консольные сообщения
    recorder: Recorder | None = None,                  # по умолчанию Recorder(config.output_dir, 30.0)
    now: Callable[[], datetime] = datetime.now,        # для имён файлов
) -> int
```

`show is None` — headless: ничего не показывается, клавиш нет (`KEY_NONE`). `show(frame)` в
реальном `main` делает `cv2.imshow` + `cv2.waitKey(1)` и возвращает `key & 0xFF` (или `KEY_NONE`),
либо `KEY_WINDOW_CLOSED`, если `cv2.getWindowProperty(title, cv2.WND_PROP_VISIBLE) < 1`.

Инициализация: `current = config.filter`; `smoother = PortalSmoother()`; `trigger = PinchTrigger()`;
`t0 = clock()`. `run` **не** печатает startup_hint (это делает `main`).

Порядок на каждый кадр:

1. **read** — взять следующий кадр из `frames`. `StopIteration` (источник кончился) → выход, код 0.
   `FrameReadError` → `say(t("errors.camera_no_frame"))`, код `EXIT_CAMERA_LOST`.
2. **mirror** — если `config.mirror`: `frame = cv2.flip(frame, 1)`.
3. **detect** — `hands = tracker.detect(frame, int((clock() - t0) * 1000))`.
4. **pinch** — `if trigger.update(hands, clock()): switch(+1)`.
5. **portal_quad** — `quad = portal_quad(hands)` (`None`, если рук не ровно две).
6. **smoother** — `smoothed, opacity = smoother.update(quad)`.
7. **render_portal** — если `smoothed is not None`:
   `clean = render_portal(frame, smoothed, get_filter(current), opacity)`, иначе `clean = frame`.
8. **recording dot** — `shown = clean.copy()` + точка, только если `recorder.is_recording`; иначе `shown = clean`.
9. **record** — если пишем: `recorder.write(clean)`.
10. **show** — `key = show(shown)` (если `show` задан).
11. **keys** — `KEY_WINDOW_CLOSED`, `q`, `Esc` → выход, код 0. Остальное по таблице раздела 4.
    Скриншот: `save_screenshot(clean, config.output_dir, now())`, затем `say(t("messages.screenshot_saved", path=path))`.
    Запись `r`: если не пишем → `path = recorder.start((w, h), now())` (`w, h` из `clean.shape`),
    `say(recording_started)`; если пишем → `path = recorder.stop()`, `say(recording_stopped)`.
    Сменили фильтр клавишей — применится со следующего кадра.

`switch(step)` / прямой выбор: меняет `current`; печатает сообщение, если фильтр изменился.

Завершение (`try/finally` вокруг цикла, в т.ч. при исключении и `KeyboardInterrupt`): если
`recorder.is_recording` → `path = recorder.stop()`, `say(recording_stopped)`. Файл всегда
финализируется. `run` ничего не закрывает кроме рекордера. Ошибки `OSError`/`RuntimeError` от
`save_screenshot` и `recorder.start` не роняют цикл: `say(screenshot_failed / recording_failed, error=exc)`,
работа продолжается.

### 5.3 `main(argv=None) -> int`

1. `config = parse_args(argv)` (ошибки парсинга — `SystemExit(2)`).
2. Модель: если не `config.model.is_file()` → `print(t("errors.model_missing", path=config.model), file=sys.stderr)`, вернуть 5.
3. Папка вывода: `config.output_dir.mkdir(parents=True, exist_ok=True)`, затем реальная проба записи
   (создать и удалить временный файл `.tmpmask_write_test`). Любой `OSError` →
   `errors.output_dir` (stderr), вернуть 6.
4. Камера: `cap = cv2.VideoCapture(config.camera)`; не `isOpened()` → `errors.camera_open` (stderr), 3.
   Затем `cap.set(CAP_PROP_FRAME_WIDTH, width)`, `cap.set(CAP_PROP_FRAME_HEIGHT, height)`.
5. `tracker = HandTracker(config.model)`; окно `cv2.namedWindow(t("app.title"))`.
6. `print(t("messages.startup_hint", filter=filter_name(config.filter), output_dir=config.output_dir))`.
7. `frames` — генератор над `cap`: `ok, f = cap.read()`; при `not ok or f is None` повторять до
   30 раз подряд с паузой `time.sleep(0.03)`, потом `raise FrameReadError`. Успех сбрасывает счётчик.
8. `code = run(frames, tracker, config, show=show)`.
9. `finally`: `tracker.close()`, `cap.release()`, `cv2.destroyAllWindows()`.
10. При коде 0 печатает `messages.exit`. `KeyboardInterrupt` → считается нормальным выходом (0).

Коды выхода: **0** нормальный выход (q/Esc/окно/Ctrl+C/конец источника); **2** неверные
аргументы (argparse); **3** камера не открылась; **4** камера перестала отдавать кадры
(и на старте, и на ходу); **5** нет файла модели; **6** папка вывода недоступна для записи.
Все сообщения об ошибках — в stderr; информационные — в stdout.

## 6. Граничные случаи

| Ситуация | Поведение |
|----------|-----------|
| 0 рук | `portal_quad → None`; сглаживатель плавно гасит портал, затем показывается чистый кадр |
| 1 рука / 3 руки | `portal_quad → None` — портала нет (как 0 рук); щипок всё равно работает |
| Руки пропали на несколько кадров | fade-out `PortalSmoother` (6 кадров), без мерцания |
| Камера отключена на ходу | 30 неудачных чтений подряд → `FrameReadError` → код 4, запись финализируется |
| Нет модели | код 5 до открытия камеры (камера не включается зря) |
| Папка вывода недоступна | код 6 на старте; ошибка скриншота/записи в середине сессии — сообщение и продолжение |
| `--filter` неизвестный | код 2, русская ошибка с перечнем допустимых |
| Закрыли окно мышью | `KEY_WINDOW_CLOSED` → выход 0, запись финализируется |
| Выход во время записи | `finally` в `run` вызывает `recorder.stop()`, печатает путь |
| Камера дала размер, отличный от запрошенного | используется фактический размер кадра; рекордер получает размер из первого кадра записи |
| Размер кадра сменился во время записи | `Recorder.write` сам ресайзит |
| Второй `s` в ту же секунду | `capture` сам добавляет `_1`, `_2`… |
| Нажат `r` дважды подряд | старт, затем стоп; разных файлов два |
| Кадры пустые/None | `main` генератор их не отдаёт (см. 5.3 п.7) |

## 7. README

Из `drafts/03-01/readme.md` дословно. Команды установки: `python3.12 -m venv .venv`,
`source .venv/bin/activate`, `pip install -e .`.

## 8. Стиль кода

Python 3.12, `ruff` (line-length 100, правила E,F,I,UP,B) без замечаний. Типы в сигнатурах.
Комментарии — только где неочевидно. Все пользовательские строки — только через `t(...)`;
русские литералы в `.py` запрещены.

## 9. Критерии проверки

Автоматические (команды из корня worktree, с активным venv):

1. `ruff check .` — без ошибок.
2. `pytest -q` — зелёный.
3. `python -m tmpmask --help` — код 0; в выводе есть «Портал фильтров», «Номер камеры»,
   `--camera`, `--width`, `--height`, `--mirror`, `--no-mirror`, `--filter`, `--output-dir`, `--model`.
4. `python -m tmpmask --filter nope; echo $?` — код 2, русская ошибка с перечнем фильтров.
5. `python -m tmpmask --model /nonexistent; echo $?` — код 5, сообщение содержит путь и команду `curl`.

`tests/test_config.py`: значения по умолчанию; `--no-mirror`; `--camera -1` → `SystemExit(2)`;
`--width 0` → `SystemExit(2)`; `--filter nope` → `SystemExit(2)`, в stderr — русский текст;
`--filter gray` → `Config.filter == "gray"`; `--help` → `SystemExit(0)`.

`tests/test_app.py` (без камеры и окна, `cv2.imshow` не вызывается; `output_dir=tmp_path`):
фейковый трекер возвращает заранее заданные списки рук (хелпер строит `Hand` из 21 точки),
кадры — `np.zeros((120, 160, 3), uint8)`, `clock` — счётчик +1/30 с на вызов, `say` — `list.append`.

- два фейковых руки на всём протяжении, `show=None`, 10 кадров → `run == 0`, трекер вызван 10 раз,
  таймстемпы строго возрастают.
- `show`, возвращающий скриптовые клавиши: `n` → сообщение «Фильтр: Тепловизор»; `p` → обратно;
  `5` → «Фильтр: Океан»; повторное `5` → без нового сообщения; `q` → выход на этом кадре
  (источник не дочитан).
- `Esc` (27) и `KEY_WINDOW_CLOSED` завершают с кодом 0.
- `s` → в `tmp_path` появился ровно один `tmpmask_*.png`, в `say` есть «Скриншот сохранён».
- `r`, несколько кадров, `r` → один `.mp4` ненулевого размера; сообщения о старте и остановке.
- `r` и затем `q` (запись не остановлена вручную) → файл финализирован (`.mp4` существует,
  `recorder.is_recording` ложно), напечатано «Запись остановлена».
- пока идёт запись, кадр, переданный в `show`, содержит красные пиксели в районе точки
  (`(0,0,255)` в правом верхнем углу), а переданный в `recorder.write` — нет; без записи точки нет.
- щипок (фейковая рука со сведёнными кончиками) → фильтр сменился ровно один раз.
- источник бросает `FrameReadError` → `run == 4`, в `say` — «Камера не вернула кадр».
- 0, 1 и 3 руки → `run == 0`, ошибок нет; с фейковыми двумя руками и `show`-колбэком кадр на
  выходе отличается от входа внутри портала (фильтр применён).
- `mirror=True` отражает кадр (трекер получает отражённый кадр: сравнить с `np.fliplr`).

Ручные проверки для ревьюера (с камерой): окно открывается, заголовок «tmpmask — портал
фильтров»; портал появляется при двух руках; `n`/`p`/`1`–`8` меняют фильтр, имя печатается в консоли;
`s` создаёт PNG, `r` — MP4, во время записи в углу красная точка, в файлах её нет; закрытие окна
мышью во время записи оставляет воспроизводимый MP4; русских литералов в `.py` нет
(`grep -nP "[А-Яа-яЁё]" tmpmask/*.py` — пусто, кроме, возможно, комментариев).

## 10. Ревью текстов

Ревьюер проверяет: все 8 фильтров названы; в `texts.toml` нет лишних/потерянных подстановок;
README совпадает с реальными опциями и клавишами; нет англицизмов там, где есть русский
вариант; терминология единая («фильтр», «портал», «запись», «скриншот»).
