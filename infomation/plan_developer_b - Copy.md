# Developer B — AI/ML & Automation Features

> **Специализация:** Whisper интеграция, AI Director, Smart Editing, Fusion  
> **Файлы:** `src/api/ai_director.py`, `src/api/whisper_node.py`, `src/api/smart_editing.py`, `config/`

---

## 🔴 Фаза 1: Критические исправления (День 1-2)

### Задача B1.1: Конфигурация Whisper
**Файлы:**
- [MODIFY] [whisper_node.py](file:///c:/GenModels/[Antigravity]/projects/test1/davinci-resolve-mcp/src/api/whisper_node.py)
- [NEW] `config/whisper_config.json`

**Проблема:** Захардкоженные пути:
```python
WHISPER_VENV_PYTHON = r"c:\GenModels\Whisper-WebUI\venv\Scripts\python.exe"
WHISPER_GEN_SCRIPT = r"C:\Users\Black\.gemini\whisper_to_json.py"
```

**Решение:**

1. Создать `config/whisper_config.json`:
```json
{
  "whisper_python": "",
  "whisper_script": "",
  "model_size": "large-v3",
  "use_native_resolve_ai": true,
  "cache_transcriptions": true,
  "fallback_to_system_whisper": true
}
```

2. Модифицировать `whisper_node.py`:
```python
import json
from pathlib import Path

def get_whisper_config() -> dict:
    """Load Whisper configuration with fallbacks."""
    config_path = Path(__file__).parent.parent.parent / "config" / "whisper_config.json"
    
    defaults = {
        "whisper_python": os.environ.get("WHISPER_PYTHON", "python"),
        "whisper_script": os.environ.get("WHISPER_SCRIPT", ""),
        "model_size": "large-v3",
        "use_native_resolve_ai": True,
        "fallback_to_system_whisper": True
    }
    
    if config_path.exists():
        try:
            with open(config_path, encoding="utf-8") as f:
                user_config = json.load(f)
                return {**defaults, **user_config}
        except Exception as e:
            logger.warning(f"Failed to load whisper config: {e}")
    
    return defaults

# Использование:
config = get_whisper_config()
WHISPER_PYTHON = config["whisper_python"]
WHISPER_SCRIPT = config["whisper_script"]
```

---

### Задача B1.2: Реализовать parse_ai_segments()
**Файл:** [ai_director.py](file:///c:/GenModels/[Antigravity]/projects/test1/davinci-resolve-mcp/src/api/ai_director.py)

**Проблема:** Функция пустая (только `pass`)

**Решение — поддержка 3 форматов:**

```python
import re
import json
from typing import List, Dict, Any

def parse_ai_segments(ai_selection_text: str, whisper_data: dict) -> List[Dict[str, Any]]:
    """Parse AI-suggested segments from multiple formats.
    
    Supported formats:
    1. JSON array: [{"start": 12.5, "end": 45.0, "title": "Hook"}]
    2. Text lines: "Reel 1: 12.5 - 45.0 (Hook about coding)"
    3. Segment indices: "Use segments: 0, 3, 5-8, 12"
    
    Args:
        ai_selection_text: Raw text from AI assistant
        whisper_data: Whisper transcription JSON for index resolution
        
    Returns:
        List of segment dicts with start, end, title
    """
    segments = []
    
    # === Format 1: JSON ===
    try:
        # Try parsing as JSON array
        text = ai_selection_text.strip()
        if text.startswith('['):
            parsed = json.loads(text)
            if isinstance(parsed, list):
                for item in parsed:
                    if "start" in item and "end" in item:
                        segments.append({
                            "start": float(item["start"]),
                            "end": float(item["end"]),
                            "title": item.get("title", f"Segment {len(segments)+1}")
                        })
                if segments:
                    return segments
    except json.JSONDecodeError:
        pass
    
    # === Format 2: Text "Reel N: start - end (description)" ===
    reel_pattern = r"(?:Reel\s*\d*:?)?\s*(\d+\.?\d*)\s*[-–—]\s*(\d+\.?\d*)\s*(?:s(?:ec)?)?(?:\s*\(([^)]*)\))?"
    matches = re.findall(reel_pattern, ai_selection_text, re.IGNORECASE)
    
    for match in matches:
        start_time = float(match[0])
        end_time = float(match[1])
        title = match[2].strip() if match[2] else f"Segment {len(segments)+1}"
        
        if end_time > start_time:
            segments.append({
                "start": start_time,
                "end": end_time,
                "title": title
            })
    
    if segments:
        return segments
    
    # === Format 3: Segment indices "0, 3, 5-8" ===
    whisper_segments = whisper_data.get("segments", []) if whisper_data else []
    
    if whisper_segments:
        # Match patterns like "segments: 0, 3, 5-8" or just "0, 3, 5-8"
        index_text = re.sub(r"(?:use\s+)?segments?\s*:?\s*", "", ai_selection_text, flags=re.IGNORECASE)
        index_pattern = r"(\d+)(?:\s*[-–—]\s*(\d+))?"
        
        for match in re.findall(index_pattern, index_text):
            start_idx = int(match[0])
            end_idx = int(match[1]) if match[1] else start_idx
            
            for idx in range(start_idx, min(end_idx + 1, len(whisper_segments))):
                seg = whisper_segments[idx]
                segments.append({
                    "start": float(seg.get("start", 0)),
                    "end": float(seg.get("end", 0)),
                    "title": seg.get("text", "")[:50].strip()
                })
    
    return segments
```

---

### Задача B1.3: Fallback на Native Resolve AI
**Файл:** `whisper_node.py`

Добавить использование встроенного транскриптора DaVinci:

```python
def transcribe_with_native_ai(resolve, clip_name: str) -> dict:
    """Fallback: Use DaVinci Resolve's built-in transcription."""
    project = resolve.GetProjectManager().GetCurrentProject()
    media_pool = project.GetMediaPool()
    
    # Find clip
    clip = find_clip_by_name(media_pool, clip_name)
    if not clip:
        return {"error": f"Clip not found: {clip_name}"}
    
    # Trigger transcription (Resolve 18.5+)
    if hasattr(clip, 'TranscribeAudio'):
        result = clip.TranscribeAudio()
        if result:
            # Get transcription text
            transcription = clip.GetMetadata("Transcription")
            return {"text": transcription, "source": "native_resolve_ai"}
    
    return {"error": "Native transcription not available"}
```

---

## 🟡 Фаза 2: Рефакторинг (День 3-5)

### Задача B2.1: Рефакторинг whisper_node.py
**Цель:** Сделать модуль универсальным

```python
class WhisperProvider:
    """Abstract base for transcription providers."""
    
    def transcribe(self, file_path: str) -> dict:
        raise NotImplementedError

class ExternalWhisperProvider(WhisperProvider):
    """Uses external Whisper installation."""
    pass

class NativeResolveProvider(WhisperProvider):
    """Uses DaVinci Resolve Neural Engine."""
    pass

class OpenAIWhisperProvider(WhisperProvider):
    """Uses OpenAI Whisper API (cloud)."""
    pass

def get_transcription_provider(config: dict) -> WhisperProvider:
    """Factory for transcription providers."""
    if config.get("use_native_resolve_ai"):
        return NativeResolveProvider()
    elif config.get("openai_api_key"):
        return OpenAIWhisperProvider(config["openai_api_key"])
    else:
        return ExternalWhisperProvider(config)
```

---

### Задача B2.2: Рефакторинг jump_cut.py
Улучшить алгоритм определения тишины:

```python
def generate_jump_cut_edits(
    whisper_data: dict, 
    clip_name: str, 
    silence_threshold: float = 0.5,
    min_speech_duration: float = 0.3,  # NEW
    add_handles: float = 0.1           # NEW
) -> List[dict]:
    """Generate edit points removing silence."""
    pass
```

---

### Задача B2.3: Документация AI функций
Создать `docs/AI_FEATURES.md`:
- Как работает Whisper интеграция
- Форматы для parse_ai_segments
- Примеры промптов для AI Director

---

## 🟢 Фаза 3: Новые функции (Неделя 1-2)

### Задача B3.1: Smart Reframe
**Файл:** [smart_editing.py](file:///c:/GenModels/[Antigravity]/projects/test1/davinci-resolve-mcp/src/api/smart_editing.py)

```python
def smart_reframe(
    resolve, 
    clip_name: str, 
    aspect_ratio: str = "9:16",
    tracking_target: str = "face"  # "face", "body", "center"
) -> str:
    """Умное кадрирование с отслеживанием объекта.
    
    Использует DaVinci Neural Engine для определения позиции лица/объекта
    и автоматического кадрирования под вертикальный формат.
    """
    project = resolve.GetProjectManager().GetCurrentProject()
    timeline = project.GetCurrentTimeline()
    
    # Найти клип на таймлайне
    clip = find_timeline_item(timeline, clip_name)
    if not clip:
        return f"Clip not found on timeline: {clip_name}"
    
    # Включить Smart Reframe (Resolve 17+)
    clip.SetProperty("SmartReframe", 1)
    clip.SetProperty("SmartReframeAspect", aspect_ratio)
    
    if tracking_target == "face":
        clip.SetProperty("SmartReframeTrackFace", 1)
    
    return f"Smart Reframe applied to {clip_name} ({aspect_ratio})"
```

---

### Задача B3.2: Auto Subtitles
```python
def auto_subtitle(
    resolve, 
    timeline_name: str = None,
    style: str = "default",
    position: str = "bottom"
) -> str:
    """Создать субтитры из транскрипции.
    
    Args:
        style: "default", "tiktok", "youtube", "cinematic"
        position: "bottom", "center", "top"
    """
    project = resolve.GetProjectManager().GetCurrentProject()
    timeline = project.GetCurrentTimeline()
    
    # Получить транскрипцию с тайлайна
    # Создать субтитры через Fusion Text+
    pass
```

---

### Задача B3.3: Scene Detection
```python
def detect_scenes(
    resolve, 
    clip_name: str, 
    sensitivity: float = 0.5
) -> List[Dict]:
    """Определить точки смены сцен.
    
    Returns:
        List of {"frame": int, "timecode": str, "confidence": float}
    """
    # Использовать DaVinci Scene Cut Detection
    pass
```

---

### Задача B3.4: Music Sync (Beat Detection)
```python
def auto_music_sync(
    resolve, 
    video_clips: List[str], 
    music_clip: str,
    sync_mode: str = "beat"  # "beat", "bar", "phrase"
) -> str:
    """Синхронизировать нарезку видео под ритм музыки.
    
    1. Анализирует BPM музыкального трека
    2. Создает маркеры на каждый бит
    3. Нарезает видео по маркерам
    """
    pass
```

---

### Задача B3.5: Fusion Operations
**Файл:** [NEW] `src/api/fusion_operations.py`

```python
def add_text_overlay(
    resolve, 
    text: str, 
    position: tuple = (0.5, 0.1),
    font: str = "Arial",
    size: int = 72,
    color: str = "#FFFFFF",
    duration: float = None  # None = entire clip
) -> str:
    """Добавить текстовый оверлей через Fusion."""
    pass

def create_lower_third(
    resolve,
    name: str,
    title: str,
    subtitle: str = "",
    template: str = "modern"  # "modern", "minimal", "news"
) -> str:
    """Создать плашку с именем/титулом."""
    pass

def apply_transition_effect(
    resolve,
    effect: str = "fade",  # "fade", "zoom", "slide", "glitch"
    duration: int = 30  # frames
) -> str:
    """Применить переход между клипами."""
    pass
```

---

## 📋 Фаза 4: Тестирование

### Задача B4.1: Unit Tests для AI модулей
**Файлы:**
- `tests/unit/test_ai_director.py`
- `tests/unit/test_whisper_node.py`
- `tests/unit/test_jump_cut.py`

```python
# test_ai_director.py
import pytest
from src.api.ai_director import parse_ai_segments, prepare_transcription_for_ai

class TestParseAiSegments:
    
    def test_parse_json_format(self):
        text = '[{"start": 0, "end": 10, "title": "Intro"}]'
        result = parse_ai_segments(text, {})
        assert len(result) == 1
        assert result[0]["start"] == 0
        assert result[0]["end"] == 10
    
    def test_parse_text_format(self):
        text = "Reel 1: 12.5 - 45.0 (Hook about coding)"
        result = parse_ai_segments(text, {})
        assert len(result) == 1
        assert result[0]["start"] == 12.5
        assert result[0]["end"] == 45.0
        assert "Hook" in result[0]["title"]
    
    def test_parse_segment_indices(self, sample_whisper_data):
        text = "Use segments: 0, 2"
        result = parse_ai_segments(text, sample_whisper_data)
        assert len(result) == 2
    
    def test_empty_input(self):
        result = parse_ai_segments("", {})
        assert result == []
```

---

### Задача B4.2: Mock для Whisper
**Файл:** `tests/mocks/whisper_mock.py`

```python
def mock_whisper_transcription(file_path: str) -> dict:
    """Mock transcription for testing without actual Whisper."""
    return {
        "text": "This is a mock transcription for testing purposes.",
        "segments": [
            {"start": 0.0, "end": 2.0, "text": "This is a mock"},
            {"start": 2.5, "end": 5.0, "text": "transcription for testing"},
            {"start": 10.0, "end": 12.0, "text": "purposes."}
        ],
        "language": "en"
    }
```

---

## Чеклист Developer B

### Фаза 1
- [ ] B1.1: Создать config/whisper_config.json
- [ ] B1.1: Модифицировать whisper_node.py для загрузки конфига
- [ ] B1.2: Реализовать parse_ai_segments() — JSON формат
- [ ] B1.2: Реализовать parse_ai_segments() — текстовый формат
- [ ] B1.2: Реализовать parse_ai_segments() — индексы сегментов
- [ ] B1.3: Добавить fallback на Native Resolve AI

### Фаза 2
- [ ] B2.1: Рефакторинг whisper_node.py (providers)
- [ ] B2.2: Улучшить jump_cut.py (min_duration, handles)
- [ ] B2.3: Создать docs/AI_FEATURES.md

### Фаза 3
- [ ] B3.1: Реализовать smart_reframe()
- [ ] B3.2: Реализовать auto_subtitle()
- [ ] B3.3: Реализовать detect_scenes()
- [ ] B3.4: Реализовать auto_music_sync()
- [ ] B3.5: Создать fusion_operations.py
- [ ] B3.5: Реализовать add_text_overlay()
- [ ] B3.5: Реализовать create_lower_third()

### Фаза 4
- [ ] B4.1: Unit тесты для ai_director.py
- [ ] B4.1: Unit тесты для whisper_node.py
- [ ] B4.1: Unit тесты для jump_cut.py
- [ ] B4.2: Создать whisper_mock.py
