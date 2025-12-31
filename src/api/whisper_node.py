#!/usr/bin/env python3
"""
Whisper Transcription Module for DaVinci Resolve MCP

Supports:
1. External Whisper installation (configurable path)
2. Built-in whisper Python package
3. DaVinci Resolve Native AI (fallback)
"""

import os
import sys
import subprocess
import json
import logging
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger("davinci-resolve-mcp.whisper_node")

# Configuration file path
CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "whisper_config.json"


def get_whisper_config() -> Dict[str, Any]:
    """Load Whisper configuration from file or environment variables.
    
    Priority:
    1. Environment variables (WHISPER_PYTHON, WHISPER_SCRIPT)
    2. Config file (config/whisper_config.json)
    3. Built-in defaults
    """
    defaults = {
        "whisper_python": "",
        "whisper_script": "",
        "model_size": "large-v3",
        "use_native_resolve_ai": True,
        "cache_transcriptions": True,
        "supported_languages": ["en", "ru", "auto"],
        "word_timestamps": True,
        "output_format": "json"
    }
    
    # Try to load from config file
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                file_config = json.load(f)
                # Remove notes section if present
                file_config.pop("notes", None)
                defaults.update(file_config)
        except Exception as e:
            logger.warning(f"Failed to load config from {CONFIG_PATH}: {e}")
    
    # Override with environment variables if set
    if os.environ.get("WHISPER_PYTHON"):
        defaults["whisper_python"] = os.environ["WHISPER_PYTHON"]
    if os.environ.get("WHISPER_SCRIPT"):
        defaults["whisper_script"] = os.environ["WHISPER_SCRIPT"]
    if os.environ.get("WHISPER_MODEL"):
        defaults["model_size"] = os.environ["WHISPER_MODEL"]
    
    return defaults


def _transcribe_with_external_script(file_path: str, config: Dict[str, Any], temp_path: str) -> Optional[Dict]:
    """Transcribe using external Whisper script."""
    whisper_python = config.get("whisper_python") or sys.executable
    whisper_script = config.get("whisper_script")
    
    if not whisper_script or not os.path.exists(whisper_script):
        return None
    
    cmd = [
        whisper_python,
        whisper_script,
        "--file", file_path,
        "--model", config.get("model_size", "large-v3"),
        "--output", temp_path
    ]
    
    logger.info(f"Running external Whisper script: {' '.join(cmd)}")
    
    try:
        process = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=600)
        
        if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
            with open(temp_path, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            logger.warning(f"External script produced empty output. stdout: {process.stdout}, stderr: {process.stderr}")
            return None
    except subprocess.TimeoutExpired:
        logger.error("Whisper script timed out after 10 minutes")
        return None
    except subprocess.CalledProcessError as e:
        logger.error(f"External Whisper script failed: {e.stderr}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error running external script: {e}")
        return None


def _transcribe_with_builtin_whisper(file_path: str, config: Dict[str, Any]) -> Optional[Dict]:
    """Transcribe using built-in whisper Python package."""
    try:
        import whisper
    except ImportError:
        logger.info("Whisper package not installed. Install with: pip install openai-whisper")
        return None
    
    model_size = config.get("model_size", "large-v3")
    
    try:
        logger.info(f"Loading Whisper model: {model_size}")
        model = whisper.load_model(model_size)
        
        logger.info(f"Transcribing: {file_path}")
        result = model.transcribe(
            file_path,
            word_timestamps=config.get("word_timestamps", True),
            language=None  # Auto-detect
        )
        
        return {
            "text": result.get("text", ""),
            "segments": result.get("segments", []),
            "language": result.get("language", "unknown")
        }
    except Exception as e:
        logger.error(f"Built-in Whisper failed: {e}")
        return None


def _transcribe_with_faster_whisper(file_path: str, config: Dict[str, Any]) -> Optional[Dict]:
    """Transcribe using faster-whisper package (more efficient)."""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        logger.debug("faster-whisper not installed")
        return None
    
    model_size = config.get("model_size", "large-v3")
    
    try:
        logger.info(f"Loading faster-whisper model: {model_size}")
        model = WhisperModel(model_size, device="auto", compute_type="auto")
        
        logger.info(f"Transcribing with faster-whisper: {file_path}")
        segments, info = model.transcribe(
            file_path,
            word_timestamps=config.get("word_timestamps", True)
        )
        
        segments_list = []
        for segment in segments:
            seg_dict = {
                "start": segment.start,
                "end": segment.end,
                "text": segment.text
            }
            if hasattr(segment, "words") and segment.words:
                seg_dict["words"] = [
                    {"start": w.start, "end": w.end, "word": w.word}
                    for w in segment.words
                ]
            segments_list.append(seg_dict)
        
        return {
            "text": " ".join(s["text"] for s in segments_list),
            "segments": segments_list,
            "language": info.language
        }
    except Exception as e:
        logger.error(f"faster-whisper failed: {e}")
        return None


def transcribe_with_whisper_node(file_path: str, model_size: str = None, use_cache: bool = True) -> Dict[str, Any]:
    """Run Whisper transcription with caching and multiple fallback methods.
    
    Transcription methods (in order of priority):
    1. External Whisper script (if configured)
    2. faster-whisper package (if installed)
    3. openai-whisper package (if installed)
    4. Returns error with suggestions
    
    Args:
        file_path: Path to the audio/video file
        model_size: Whisper model size (tiny, base, small, medium, large-v3)
        use_cache: If True, use cached transcription if available
        
    Returns:
        Dictionary with 'text', 'segments', 'language' or 'error'
    """
    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}"}
    
    # Load configuration
    config = get_whisper_config()
    if model_size:
        config["model_size"] = model_size
    
    # Check cache first
    cache_path = file_path + ".whisper.json"
    if use_cache and config.get("cache_transcriptions", True):
        if os.path.exists(cache_path) and os.path.getsize(cache_path) > 0:
            try:
                logger.info(f"Loading cached transcription from {cache_path}")
                with open(cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load cache {cache_path}: {e}")
    
    # Try transcription methods in order
    result = None
    temp_fd, temp_path = tempfile.mkstemp(suffix=".json")
    os.close(temp_fd)
    
    try:
        # Method 1: External script
        if config.get("whisper_script"):
            logger.info("Trying Method 1: External Whisper script")
            result = _transcribe_with_external_script(file_path, config, temp_path)
        
        # Method 2: faster-whisper
        if result is None:
            logger.info("Trying Method 2: faster-whisper")
            result = _transcribe_with_faster_whisper(file_path, config)
        
        # Method 3: openai-whisper
        if result is None:
            logger.info("Trying Method 3: openai-whisper")
            result = _transcribe_with_builtin_whisper(file_path, config)
        
        # No method worked
        if result is None:
            return {
                "error": "No transcription method available",
                "suggestions": [
                    "Install faster-whisper: pip install faster-whisper",
                    "Install openai-whisper: pip install openai-whisper", 
                    "Configure external script in config/whisper_config.json",
                    "Use DaVinci Resolve's built-in transcription (requires Studio)"
                ]
            }
        
        # Save to cache
        if config.get("cache_transcriptions", True):
            try:
                with open(cache_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                logger.info(f"Transcription saved to cache: {cache_path}")
            except Exception as ce:
                logger.warning(f"Failed to save cache: {ce}")
        
        return result
        
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass


def clear_transcription_cache(file_path: str) -> bool:
    """Remove cached transcription for a file.
    
    Args:
        file_path: Path to the original media file
        
    Returns:
        True if cache was removed, False otherwise
    """
    cache_path = file_path + ".whisper.json"
    if os.path.exists(cache_path):
        try:
            os.remove(cache_path)
            logger.info(f"Removed cache: {cache_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to remove cache: {e}")
            return False
    return False


def get_transcription_from_cache(file_path: str) -> Optional[Dict[str, Any]]:
    """Get cached transcription without running Whisper.
    
    Args:
        file_path: Path to the original media file
        
    Returns:
        Transcription dict or None if not cached
    """
    cache_path = file_path + ".whisper.json"
    if os.path.exists(cache_path) and os.path.getsize(cache_path) > 0:
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")
    return None
