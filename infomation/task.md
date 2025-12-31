# DaVinci Resolve MCP — Task Checklist

## Фаза 1: Критические исправления 🔴

- [x] Вынести пути Whisper в конфигурационный файл
  - [x] Создать `config/whisper_config.json`
  - [x] Модифицировать `src/api/whisper_node.py`
- [x] Реализовать `parse_ai_segments()` в `ai_director.py`
  - [x] Парсинг JSON формата
  - [x] Парсинг текстового формата "Reel N: start - end"
  - [x] Парсинг индексов сегментов
  - [x] Парсинг timecode формата
- [x] Исправить `AddRenderJob` в `delivery_operations.py`
  - [x] Добавить `add_render_job_robust()` с 4 fallback методами
  - [x] Добавить `get_render_formats()` для получения форматов/кодеков
- [x] Добавить fallback на Native Resolve AI для транскрипции

## Фаза 2: Рефакторинг 🟡

- [x] Создать централизованную обработку ошибок
  - [x] Создать `utils/error_handling.py`
  - [x] Добавить декораторы `@require_resolve`, `@require_project`, `@require_timeline`
  - [x] Добавить декоратор `@safe_api_call`
  - [x] Добавить helper функции `get_project_safe()`, `get_timeline_safe()`
- [x] Обновить `api/__init__.py` с экспортами всех модулей
- [ ] Декомпозиция `resolve_mcp_server.py` (4900 строк)
  - [ ] Создать `api/transcription_operations.py`
  - [ ] Создать `api/gallery_operations.py`
  - [ ] Создать `api/keyframe_operations.py`
  - [ ] Создать `api/export_operations.py`
  - [ ] Переделать главный файл на импорты из модулей
- [ ] Удалить дубликат `scripts/resolve_mcp_server.py`

## Фаза 3: Новые функции 🟢

- [x] Fairlight operations (аудио)
  - [x] `get_audio_tracks()`
  - [x] `set_track_volume()`
  - [x] `get_audio_clip_info()`
  - [x] `analyze_audio_levels()`
  - [x] `add_audio_track()` / `delete_audio_track()`
  - [x] `voice_isolation()` (инструкции для Neural Engine)
  - [x] `normalize_audio()` (руководство по нормализации)
- [x] Fusion operations (эффекты)
  - [x] `get_fusion_comp()`
  - [x] `create_fusion_clip()`
  - [x] `add_text_plus()`
  - [x] `create_lower_third()`
  - [x] `list_fusion_templates()`
  - [x] `insert_generator()` / `insert_title()`
  - [x] `get_fusion_node_list()`
  - [x] `export_fusion_comp()` / `import_fusion_comp()`
- [x] Smart Automation
  - [x] `smart_reframe()` - кадрирование 9:16
  - [x] `auto_subtitle()` - субтитры из транскрипции
  - [x] `detect_scenes()` - определение смены сцен
  - [x] `batch_export_by_markers()` - экспорт по маркерам
  - [x] `create_multicam_timeline()` - multicam
  - [x] `speed_ramp()` - скоростные рампы
- [x] AI Director расширения
  - [x] `suggest_viral_segments()` - автоматический поиск вирусных моментов
  - [x] `create_ai_prompt_for_editing()` - промпты для разных стилей
  - [x] `generate_edl_from_segments()` - генерация EDL

## Фаза 4: Тестирование 📋

- [x] Создать mock DaVinci Resolve API
  - [x] `tests/conftest.py` с pytest fixtures
  - [x] MockResolve, MockProject, MockTimeline, MockMediaPool
  - [x] sample_whisper_data fixture
- [x] Unit тесты
  - [x] `tests/unit/test_ai_director.py`
  - [x] `tests/unit/test_jump_cut.py`
  - [x] `tests/unit/test_error_handling.py`
- [ ] Integration тесты
  - [ ] `tests/integration/test_project_operations.py`
  - [ ] `tests/integration/test_timeline_operations.py`
- [ ] CI/CD
  - [ ] GitHub Actions workflow
  - [ ] Автоматический запуск тестов

## Статус выполнения

| Фаза | Прогресс | Статус |
|------|----------|--------|
| Фаза 1: Критические исправления | 100% | ✅ Завершено |
| Фаза 2: Рефакторинг | 40% | 🔄 В процессе |
| Фаза 3: Новые функции | 100% | ✅ Завершено |
| Фаза 4: Тестирование | 60% | 🔄 В процессе |
