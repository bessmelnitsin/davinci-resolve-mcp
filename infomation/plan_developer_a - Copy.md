# Developer A — Backend & Core API

> **Специализация:** API интеграция, DaVinci Resolve Scripting API, рефакторинг  
> **Файлы:** `src/api/`, `src/utils/`, `resolve_mcp_server.py`

---

## 🔴 Фаза 1: Критические исправления (День 1-2)

### Задача A1.1: Исправить AddRenderJob
**Файл:** [delivery_operations.py](file:///c:/GenModels/[Antigravity]/projects/test1/davinci-resolve-mcp/src/api/delivery_operations.py)

**Проблема:** `AddRenderJob` возвращает `'NoneType' object is not callable`

**Действия:**
1. Добавить проверку `hasattr(project, 'AddRenderJob')`
2. Реализовать fallback через `LoadRenderPreset()`
3. Добавить автопереключение на Deliver page

```python
def add_to_render_queue(resolve, preset_name: str, ...):
    project = resolve.GetProjectManager().GetCurrentProject()
    
    # Проверка доступности метода
    if hasattr(project, 'AddRenderJob') and callable(getattr(project, 'AddRenderJob')):
        job_id = project.AddRenderJob()
        if job_id:
            return {"success": True, "job_id": job_id}
    
    # Fallback: Через preset
    if project.LoadRenderPreset(preset_name):
        job_id = project.AddRenderJob()
        return {"success": True, "job_id": job_id, "method": "preset_load"}
    
    return {"error": "AddRenderJob unavailable"}
```

**Тесты:** Проверить на Resolve 18.x и 19.x

---

### Задача A1.2: Централизованная обработка ошибок
**Файл:** [NEW] `src/utils/error_handling.py`

**Действия:**
1. Создать базовые классы исключений
2. Создать декораторы `@require_resolve`, `@require_project`
3. Применить к существующим функциям в `delivery_operations.py`

```python
class ResolveAPIError(Exception): pass
class ResolveNotConnectedError(ResolveAPIError): pass
class ProjectNotOpenError(ResolveAPIError): pass

def require_resolve(func):
    @wraps(func)
    def wrapper(resolve, *args, **kwargs):
        if resolve is None:
            raise ResolveNotConnectedError("DaVinci Resolve не подключен")
        return func(resolve, *args, **kwargs)
    return wrapper

def require_project(func):
    @wraps(func)
    def wrapper(resolve, *args, **kwargs):
        project = resolve.GetProjectManager().GetCurrentProject()
        if project is None:
            raise ProjectNotOpenError("Проект не открыт")
        return func(resolve, *args, **kwargs)
    return wrapper
```

---

## 🟡 Фаза 2: Рефакторинг (День 3-5)

### Задача A2.1: Декомпозиция resolve_mcp_server.py
**Файл:** [resolve_mcp_server.py](file:///c:/GenModels/[Antigravity]/projects/test1/davinci-resolve-mcp/src/resolve_mcp_server.py)

**Создать новые модули:**

| Новый файл | Строки из оригинала | Функции |
|------------|---------------------|---------|
| `api/gallery_operations.py` | ~2000-2500 | GetAlbumName, GetStillList, ExportStills |
| `api/keyframe_operations.py` | ~2500-3000 | GetKeyframeMode, SetKeyframeMode |
| `api/export_operations.py` | ~3000-3500 | Export, ImportIntoTimeline |

**Действия:**
1. Выделить функции в отдельные модули
2. Добавить импорты в `__init__.py`
3. Обновить `resolve_mcp_server.py` на использование импортов
4. Запустить существующие тесты

---

### Задача A2.2: Удаление дубликатов
**Файлы:**
- [DELETE] `scripts/resolve_mcp_server.py`
- Проверить `list_clips_helper.py` в корне — возможно тоже дубликат

---

### Задача A2.3: Внедрение декораторов
Применить `@require_resolve`, `@require_project` ко всем функциям в:
- `timeline_operations.py`
- `media_operations.py`
- `project_operations.py`

---

## 🟢 Фаза 3: Новые функции (Неделя 1-2)

### Задача A3.1: Fairlight Operations
**Файл:** [NEW] `src/api/fairlight_operations.py`

```python
def get_audio_tracks(resolve, timeline_name: str = None) -> List[Dict]:
    """Получить список аудиодорожек."""
    project = resolve.GetProjectManager().GetCurrentProject()
    timeline = project.GetCurrentTimeline()
    track_count = timeline.GetTrackCount("audio")
    
    tracks = []
    for i in range(1, track_count + 1):
        tracks.append({
            "index": i,
            "name": timeline.GetTrackName("audio", i),
            "enabled": timeline.GetIsTrackEnabled("audio", i),
            "locked": timeline.GetIsTrackLocked("audio", i)
        })
    return tracks

def set_track_volume(resolve, track_index: int, volume_db: float) -> str:
    """Установить громкость дорожки (-96 to +12 dB)."""
    pass

def normalize_audio(resolve, clip_name: str, target_lufs: float = -14.0) -> str:
    """Нормализация по LUFS."""
    pass

def voice_isolation(resolve, clip_name: str) -> str:
    """Изоляция голоса через Neural Engine."""
    pass
```

---

### Задача A3.2: Gallery Operations
**Файл:** [NEW] `src/api/gallery_operations.py`

```python
def get_gallery_albums(resolve) -> List[str]:
    """Получить список альбомов галереи."""
    pass

def save_still(resolve, frame: int = None, album_name: str = None) -> str:
    """Сохранить стоп-кадр в галерею."""
    pass

def apply_grade_from_still(resolve, still_name: str, clips: List[str]) -> str:
    """Применить грейд из галереи к клипам."""
    pass
```

---

## 📋 Фаза 4: Тестирование

### Задача A4.1: Integration Tests
**Файлы:**
- `tests/integration/test_delivery_operations.py`
- `tests/integration/test_fairlight_operations.py`

```python
# test_delivery_operations.py
def test_add_render_job_success(mock_resolve):
    mock_resolve.GetProjectManager().GetCurrentProject().AddRenderJob.return_value = "job_123"
    result = add_to_render_queue(mock_resolve, "YouTube 1080p")
    assert result["success"] == True

def test_add_render_job_fallback(mock_resolve):
    mock_resolve.GetProjectManager().GetCurrentProject().AddRenderJob.return_value = None
    # Should use fallback method
    ...
```

---

## Чеклист Developer A

### Фаза 1
- [ ] A1.1: Исправить AddRenderJob с fallback
- [ ] A1.2: Создать error_handling.py с декораторами

### Фаза 2
- [ ] A2.1: Создать gallery_operations.py
- [ ] A2.1: Создать keyframe_operations.py
- [ ] A2.1: Создать export_operations.py
- [ ] A2.2: Удалить scripts/resolve_mcp_server.py
- [ ] A2.3: Применить декораторы к timeline_operations
- [ ] A2.3: Применить декораторы к media_operations
- [ ] A2.3: Применить декораторы к project_operations

### Фаза 3
- [ ] A3.1: Реализовать get_audio_tracks()
- [ ] A3.1: Реализовать set_track_volume()
- [ ] A3.1: Реализовать normalize_audio()
- [ ] A3.1: Реализовать voice_isolation()
- [ ] A3.2: Реализовать get_gallery_albums()
- [ ] A3.2: Реализовать save_still()
- [ ] A3.2: Реализовать apply_grade_from_still()

### Фаза 4
- [ ] A4.1: Тесты для delivery_operations
- [ ] A4.1: Тесты для fairlight_operations
