# DaVinci Resolve MCP Server - Справочник API

Полная документация по всем доступным инструментам и ресурсам.

---

## 📖 Содержание

1. [Транскрибация (Transcription)](#транскрибация-transcription)
2. [Операции с Timeline](#операции-с-timeline)
3. [Медиа Пул (Media Pool)](#медиа-пул-media-pool)
4. [Управление Проектом](#управление-проектом)
5. [Умный Монтаж / AI](#умный-монтаж--ai)
6. [Страница Color](#страница-color)
7. [Рендер и Экспорт (Delivery)](#рендер-и-экспорт-delivery)

---

## Транскрибация (Transcription)

Транскрибация аудио с использованием Whisper AI.

### Инструменты (Tools)

| Инструмент | Описание | Аргументы |
|------------|----------|-----------|
| `transcribe` | Транскрибировать аудио/видео файл | `file_path`, `language`, `output_format` |
| `transcribe_clip` | Транскрибировать клип из Медиа Пула | `clip_name`, `language`, `output_format` |
| `transcribe_clip_to_cache` | Транскрибировать и кэшировать | `clip_name`, `model_size`, `force_retranscribe` |
| `get_cached_transcription` | Читать из кэша | `clip_name` |
| `get_clip_transcription` | Авто-транскрибация или загрузка из кэша | `clip_name`, `model_size` |
| `transcribe_folder_tool` | Транскрибировать папку (Native AI) | `folder_name` |
| `transcribe_clip_tool` | Транскрибировать через Whisper | `clip_name`, `model_size` |

### Ресурсы (Resources)

| Ресурс | Описание |
|--------|----------|
| `whisper://status` | Статус сервера Whisper |

---

## Операции с Timeline

Создание и управление таймлайнами.

### Инструменты (Tools)

| Инструмент | Описание | Аргументы |
|------------|----------|-----------|
| `create_timeline` | Создать новый таймлайн | `name` |
| `create_empty_timeline` | Создать с настройками | `name`, `frame_rate`, `resolution_width` и др. |
| `delete_timeline` | Удалить таймлайн | `name` |
| `set_current_timeline` | Переключиться на таймлайн | `name` |
| `add_marker` | Добавить маркер | `frame`, `color`, `note` |
| `append_clips_to_timeline` | Добавить клипы на таймлайн | `clip_names`, `timeline_name` |
| `create_timeline_from_clips` | Создать таймлайн из клипов | `name`, `clip_names` |
| `create_trendy_timeline` | Создать монтаж с музыкой | `edits`, `timeline_name` |
| `assemble_viral_reels` | Создать вертикальные Reels | `clip_name`, `segments` |
| `set_timeline_item_transform` | Изменить трансформ (Zoom, Pan) | `item_id`, `property_name`, `value` |
| `set_timeline_item_crop` | Изменить кроп | `item_id`, `crop_type`, `value` |

### Ресурсы (Resources)

| Ресурс | Описание |
|--------|----------|
| `resolve://timelines` | Список всех таймлайнов |
| `resolve://current-timeline` | Информация о текущем таймлайне |
| `resolve://timeline-tracks` | Структура треков |
| `resolve://timeline-items` | Все клипы на таймлайне |
| `resolve://timeline-item/{id}` | Свойства клипа |
| `resolve://timeline-clips` | Имена клипов на таймлайне |

---

## Медиа Пул (Media Pool)

Управление файлами и папками проекта.

### Инструменты (Tools)

| Инструмент | Описание | Аргументы |
|------------|----------|-----------|
| `import_media` | Импорт файла | `file_path` |
| `create_bin` | Создать папку (bin) | `name` |
| `delete_media` | Удалить клип | `clip_name` |
| `move_media_to_bin` | Переместить клип | `clip_name`, `bin_name` |
| `auto_sync_audio` | Синхронизация звука | `clip_names`, `sync_method`, `target_bin` |
| `unlink_clips` | Отлинковать (Unlink) | `clip_names` |
| `relink_clips` | Перелинковать (Relink) | `clip_names`, `media_paths`, `folder_path` |
| `create_sub_clip` | Создать сабклип | `clip_name`, `start_frame`, `end_frame` |
| `add_clip_to_timeline` | Добавить на таймлайн | `clip_name`, `timeline_name` |
| `link_proxy_media` | Привязать прокси | `clip_name`, `proxy_file_path` |
| `unlink_proxy_media` | Отвязать прокси | `clip_name` |
| `replace_clip` | Заменить файл клипа | `clip_name`, `replacement_path` |
| `transcribe_audio_native` | Native AI транскрибация | `clip_name`, `language` |
| `clear_transcription_native` | Очистить транскрибацию | `clip_name` |
| `export_folder` | Экспорт в DRB | `folder_name`, `export_path` |
| `transcribe_folder_audio` | Транскрибировать папку | `folder_name`, `language` |

### Ресурсы (Resources)

| Ресурс | Описание |
|--------|----------|
| `resolve://media-pool-clips` | Все клипы |
| `resolve://media-pool-bins` | Все папки |
| `resolve://media-pool-bin/{name}` | Содержимое папки |

---

## Управление Проектом

Настройки проекта и метаданные.

### Инструменты (Tools)

| Инструмент | Описание | Аргументы |
|------------|----------|-----------|
| `open_project` | Открыть проект | `name` |
| `create_project` | Создать проект | `name` |
| `save_project` | Сохранить проект | — |
| `set_project_property_tool` | Задать свойство | `property_name`, `property_value` |
| `set_timeline_format_tool` | Формат таймлайна | `width`, `height`, `frame_rate` |
| `set_superscale_settings_tool` | Настройки SuperScale | `enabled`, `quality` |
| `set_color_science_mode_tool` | Режим цвета (YRGB/ACES) | `mode` |
| `set_color_space_tool` | Цветовое пространство | `color_space`, `gamma` |
| `set_cache_mode` | Режим кэша | `mode` |
| `set_optimized_media_mode` | Режим оптим. медиа | `mode` |
| `set_proxy_mode` | Режим прокси | `mode` |
| `set_proxy_quality` | Качество прокси | `quality` |
| `set_cache_path` | Путь к кэшу | `path_type`, `path` |
| `generate_optimized_media` | Создать оптим. медиа | `clip_names` |

### Ресурсы (Resources)

| Ресурс | Описание |
|--------|----------|
| `resolve://projects` | Все проекты |
| `resolve://current-project` | Текущий проект |
| `resolve://project/properties` | Все свойства |
| `resolve://project/timeline-format` | Формат таймлайна |
| `resolve://project/superscale` | Настройки SuperScale |
| `resolve://project/color-settings` | Настройки цвета |
| `resolve://project/info` | Информация о проекте |

---

## Умный Монтаж / AI

Автоматизация на основе ИИ.

### Инструменты (Tools)

| Инструмент | Описание | Аргументы |
|------------|----------|-----------|
| `smart_jump_cut` | Удалить тишину | `clip_name`, `silence_threshold` |
| `viral_reels_factory` | Генератор Reels (9:16) | `clip_name` |
| `podcast_to_clips` | Подкаст в клипы | `clip_name`, `max_clips`, `content_style` |
| `analyze_content` | Анализ виральности | `file_path`, `content_style` |
| `find_viral_segments` | Поиск лучших моментов | `clip_name`, `max_segments` |
| `create_viral_clips` | Создать виральные клипы | `clip_name`, `segments`, `auto_detect` |

---

## Страница Color

Цветокоррекция.

### Инструменты (Tools)

| Инструмент | Описание | Аргументы |
|------------|----------|-----------|
| `apply_lut` | Применить LUT | `lut_path`, `node_index` |
| `set_color_wheel_param` | Параметры колес | `wheel`, `param`, `value` |
| `add_node` | Добавить ноду | `node_type`, `label` |
| `copy_grade` | Скопировать грейд | `source_clip_name`, `target_clip_name` |

### Ресурсы (Resources)

| Ресурс | Описание |
|--------|----------|
| `resolve://color/current-node` | Текущая нода |
| `resolve://color/wheels/{index}` | Параметры колес |

---

## Рендер и Экспорт (Delivery)

Рендеринг и очередь рендера.

### Инструменты (Tools)

| Инструмент | Описание | Аргументы |
|------------|----------|-----------|
| `add_to_render_queue` | Добавить в очередь | `preset_name`, `timeline_name` |
| `start_render` | Запустить рендер | — |
| `clear_render_queue` | Очистить очередь | — |

### Ресурсы (Resources)

| Ресурс | Описание |
|--------|----------|
| `resolve://delivery/render-presets` | Список пресетов |
| `resolve://delivery/render-queue/status` | Статус очереди |
