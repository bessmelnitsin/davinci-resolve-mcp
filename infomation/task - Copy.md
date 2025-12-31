# DaVinci Resolve MCP — Task Checklist (Parallel Work)

> **Developer A:** Backend & Core API (delivery, audio, galleries, refactoring)  
> **Developer B:** AI/ML & Automation (Whisper, AI Director, Smart Editing, Fusion)

---

## Фаза 1: Критические исправления 🔴

### Developer A
- [ ] **[A1.1]** Исправить AddRenderJob в delivery_operations.py
  - [ ] Добавить проверку hasattr для метода
  - [ ] Реализовать fallback через LoadRenderPreset
- [ ] **[A1.2]** Создать централизованную обработку ошибок
  - [ ] Создать `src/utils/error_handling.py`
  - [ ] Реализовать декораторы @require_resolve, @require_project

### Developer B
- [ ] **[B1.1]** Вынести пути Whisper в конфигурацию
  - [ ] Создать `config/whisper_config.json`
  - [ ] Модифицировать whisper_node.py для загрузки конфига
- [ ] **[B1.2]** Реализовать parse_ai_segments() в ai_director.py
  - [ ] Парсинг JSON формата
  - [ ] Парсинг текстового формата "Reel N: start - end"
  - [ ] Парсинг индексов сегментов Whisper
- [ ] **[B1.3]** Добавить fallback на Native Resolve AI транскрипцию

---

## Фаза 2: Рефакторинг 🟡

### Developer A
- [ ] **[A2.1]** Декомпозиция resolve_mcp_server.py
  - [ ] Создать `api/gallery_operations.py`
  - [ ] Создать `api/keyframe_operations.py`
  - [ ] Создать `api/export_operations.py`
  - [ ] Обновить импорты в главном файле
- [ ] **[A2.2]** Удалить дубликат `scripts/resolve_mcp_server.py`
- [ ] **[A2.3]** Применить декораторы ко всем модулям
  - [ ] timeline_operations.py
  - [ ] media_operations.py
  - [ ] project_operations.py

### Developer B
- [ ] **[B2.1]** Рефакторинг whisper_node.py
  - [ ] Создать базовый класс WhisperProvider
  - [ ] Реализовать ExternalWhisperProvider
  - [ ] Реализовать NativeResolveProvider
- [ ] **[B2.2]** Улучшить jump_cut.py
  - [ ] Добавить параметр min_speech_duration
  - [ ] Добавить параметр add_handles
- [ ] **[B2.3]** Создать docs/AI_FEATURES.md

---

## Фаза 3: Новые функции 🟢

### Developer A — Fairlight & Gallery
- [ ] **[A3.1]** Fairlight operations (audio)
  - [ ] get_audio_tracks()
  - [ ] set_track_volume()
  - [ ] normalize_audio()
  - [ ] voice_isolation()
- [ ] **[A3.2]** Gallery operations
  - [ ] get_gallery_albums()
  - [ ] save_still()
  - [ ] apply_grade_from_still()

### Developer B — Smart Editing & Fusion
- [ ] **[B3.1]** Smart Reframe
  - [ ] Реализовать smart_reframe() с face tracking
  - [ ] Поддержка aspect ratios: 9:16, 1:1, 4:5
- [ ] **[B3.2]** Auto Subtitles
  - [ ] Реализовать auto_subtitle()
  - [ ] Стили: default, tiktok, youtube, cinematic
- [ ] **[B3.3]** Scene Detection
  - [ ] Реализовать detect_scenes()
- [ ] **[B3.4]** Music Sync
  - [ ] Реализовать auto_music_sync()
  - [ ] BPM detection и маркеры
- [ ] **[B3.5]** Fusion operations
  - [ ] Создать fusion_operations.py
  - [ ] add_text_overlay()
  - [ ] create_lower_third()
  - [ ] apply_transition_effect()

---

## Фаза 4: Тестирование 📋

### Developer A — Integration Tests
- [ ] **[A4.1]** Integration тесты
  - [ ] test_delivery_operations.py
  - [ ] test_fairlight_operations.py
  - [ ] test_gallery_operations.py

### Developer B — Unit Tests
- [ ] **[B4.1]** Unit тесты AI модулей
  - [ ] test_ai_director.py
  - [ ] test_whisper_node.py
  - [ ] test_jump_cut.py
- [ ] **[B4.2]** Mocks
  - [ ] whisper_mock.py
  - [ ] resolve_mock.py (совместно с A)

---

## Точки синхронизации 🔄

| Момент | Developer A ждёт | Developer B ждёт |
|--------|------------------|------------------|
| Конец Фазы 1 | — | error_handling.py готов |
| Конец Фазы 2 | — | Provider pattern для тестов |
| Фаза 3 | voice_isolation() может использовать B3.1 | — |
| Фаза 4 | Mocks от B | Integration tests от A |

---

## Статусы

| Задача | Статус | Разработчик |
|--------|--------|-------------|
| A1.1 AddRenderJob | ⬜ TODO | A |
| A1.2 Error Handling | ⬜ TODO | A |
| B1.1 Whisper Config | ⬜ TODO | B |
| B1.2 parse_ai_segments | ⬜ TODO | B |
| B1.3 Native AI Fallback | ⬜ TODO | B |
