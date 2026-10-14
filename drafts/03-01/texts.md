<!-- target: tmpmask/texts.toml -->
# Все русские тексты tmpmask. Подстановки — имена для str.format: {name}.
# Литеральные фигурные скобки писать как {{ и }}. Знак % в справке CLI допустим
# только как %(default)s (argparse раскрывает его сам).
# Таблицы: app, filters, cli, cli_errors, messages, errors.

[app]
title = "tmpmask — портал фильтров"

[filters]
purple = "Фиолетовый"
thermal = "Тепловизор"
invert = "Негатив"
gray = "Чёрно-белый"
ocean = "Океан"
sepia = "Сепия"
pixelate = "Пиксели"
edges = "Контуры"

[cli]
description = "Портал фильтров: сложите большие и указательные пальцы обеих рук в рамку — внутри неё появится выбранный фильтр."
help = "Показать эту справку и выйти."
camera = "Номер камеры (индекс устройства). По умолчанию: %(default)s."
width = "Запрашиваемая ширина кадра в пикселях. По умолчанию: %(default)s."
height = "Запрашиваемая высота кадра в пикселях. По умолчанию: %(default)s."
mirror = "Зеркально отражать картинку, как в зеркале (--no-mirror — выключить). По умолчанию: %(default)s."
filter = "Фильтр при запуске. Доступно: {filters}. По умолчанию: %(default)s."
output_dir = "Папка для скриншотов и видео. По умолчанию: %(default)s."
model = "Путь к файлу модели распознавания рук (hand_landmarker.task). По умолчанию: %(default)s."

[cli_errors]
not_an_int = "нужно целое число, получено «{value}»"
negative = "число не может быть отрицательным: {value}"
not_positive = "число должно быть больше нуля: {value}"
unknown_filter = "неизвестный фильтр «{value}»; доступно: {filters}"

[messages]
startup_hint = """
tmpmask запущен. Сложите большие и указательные пальцы обеих рук в рамку — внутри появится фильтр.
Управление:
  N / P      следующий / предыдущий фильтр
  1–8        выбрать фильтр по номеру
  щипок      (все пальцы одной руки вместе) следующий фильтр
  S          скриншот
  R          начать / остановить запись видео
  Q или Esc  выход
Фильтр сейчас: {filter}. Файлы сохраняются в: {output_dir}"""
filter_switched = "Фильтр: {name}"
screenshot_saved = "Скриншот сохранён: {path}"
recording_started = "Запись начата: {path}"
recording_stopped = "Запись остановлена, файл сохранён: {path}"
exit = "Выход. До встречи!"

[errors]
camera_open = "Не удалось открыть камеру с номером {index}. Проверьте, что камера подключена и не занята другой программой, попробуйте другой номер через --camera. На macOS разрешите доступ к камере: Системные настройки → Конфиденциальность и безопасность → Камера."
camera_no_frame = "Камера не вернула кадр (возможно, её отключили или она занята). Подключите камеру и запустите программу снова."
model_missing = """
Не найден файл модели: {path}
Скачайте его командой (из корня проекта):
  mkdir -p models && curl -L -o models/hand_landmarker.task https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task
или укажите свой файл через --model."""
output_dir = "Нельзя записывать в папку {path}: {error}. Укажите другую папку через --output-dir."
screenshot_failed = "Не удалось сохранить скриншот: {error}"
recording_failed = "Не удалось начать запись видео: {error}"
