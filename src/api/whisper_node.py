#!/usr/bin/env python3
"""
Whisper Transcription Module for DaVinci Resolve MCP

Supports (in order of priority):
1. Whisper-WebUI Server (Gradio API at localhost:7860)
2. External Whisper installation (configurable path)
3. Built-in whisper Python package (faster-whisper, openai-whisper)
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
    1. Environment variables (WHISPER_WEBUI_URL, WHISPER_PYTHON, WHISPER_SCRIPT)
    2. Config file (config/whisper_config.json)
    3. Built-in defaults
    """
    defaults = {
        "whisper_webui_url": "http://127.0.0.1:7860",  # Whisper-WebUI Gradio server
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
    if os.environ.get("WHISPER_WEBUI_URL"):
        defaults["whisper_webui_url"] = os.environ["WHISPER_WEBUI_URL"]
    if os.environ.get("WHISPER_PYTHON"):
        defaults["whisper_python"] = os.environ["WHISPER_PYTHON"]
    if os.environ.get("WHISPER_SCRIPT"):
        defaults["whisper_script"] = os.environ["WHISPER_SCRIPT"]
    if os.environ.get("WHISPER_MODEL"):
        defaults["model_size"] = os.environ["WHISPER_MODEL"]
    
    return defaults


def _transcribe_with_webui(file_path: str, config: Dict[str, Any]) -> Optional[Dict]:
    """Transcribe using Whisper-WebUI Gradio server.
    
    This is the fastest method as the model is already loaded in GPU memory.
    Whisper-WebUI runs at http://127.0.0.1:7860 by default.
    
    Args:
        file_path: Path to the audio/video file
        config: Configuration dictionary
        
    Returns:
        Transcription dict or None if server unavailable
    """
    webui_url = config.get("whisper_webui_url", "http://127.0.0.1:7860")
    
    # First check if server is available
    try:
        import requests
        health_url = f"{webui_url}/"
        response = requests.get(health_url, timeout=2)
        if response.status_code != 200:
            logger.debug(f"Whisper-WebUI not available at {webui_url}")
            return None
    except Exception as e:
        logger.debug(f"Whisper-WebUI not reachable: {e}")
        return None
    
    # Try using gradio_client if available
    try:
        from gradio_client import Client, handle_file
        
        logger.info(f"Connecting to Whisper-WebUI at {webui_url}")
        client = Client(webui_url, verbose=False)
        try:
            # Prepare arguments for the 54-parameter API
            # Based on inspection of running server 2026-01-01
            
            model_size = config.get("model_size", "large-v3")
            language = "Automatic Detection"
            
            inputs = [
                # [0] Upload File
                handle_file(file_path),
                # [1] Input Folder Path
                "",
                # [2] Include Subdirectory Files
                False,
                # [3] Save outputs at same directory
                False,
                # [4] File Format
                "SRT",
                # [5] Add timestamp to filename
                False,
                # [6] Model
                model_size,
                # [7] Language
                language,
                # [8] Translate to English
                False,
                # [9] Beam Size
                5,
                # [10] Log Probability Threshold
                -1.0,
                # [11] No Speech Threshold
                0.6,
                # [12] Compute Type
                "float16",
                # [13] Best Of
                5,
                # [14] Patience
                1.0,
                # [15] Condition On Previous Text
                True,
                # [16] Prompt Reset On Temperature
                0.1,
                # [17] Initial Prompt
                "",
                # [18] Temperature
                0,
                # [19] Compression Ratio Threshold
                2.4,
                # [20] Length Penalty
                1.0,
                # [21] Repetition Penalty
                1.0,
                # [22] No Repeat N-gram Size
                0,
                # [23] Prefix
                "",
                # [24] Suppress Blank
                True,
                # [25] Suppress Tokens
                "-1",
                # [26] Max Initial Timestamp
                1.0,
                # [27] Word Timestamps
                True,
                # [28] Prepend Punctuations
                "\"'“¿([{-",
                # [29] Append Punctuations
                "\"'.。,，!！?？:：”)]}、",
                # [30] Max New Tokens
                0,
                # [31] Chunk Length (s)
                30,
                # [32] Hallucination Silence Threshold (sec)
                2,
                # [33] Hotwords
                "",
                # [34] Language Detection Threshold
                0.5,
                # [35] Language Detection Segments
                1,
                # [36] Batch Size
                16,
                # [37] Offload sub model when finished
                False,
                # [38] Enable Silero VAD Filter
                True,
                # [39] Speech Threshold
                0.6,
                # [40] Minimum Speech Duration (ms)
                250,
                # [41] Maximum Speech Duration (s)
                0,
                # [42] Minimum Silence Duration (ms)
                2000,
                # [43] Speech Padding (ms)
                400,
                # [44] Enable Diarization
                False,
                # [45] Device
                "cuda",
                # [46] HuggingFace Token
                "",
                # [47] Offload sub model when finished (duplicate in UI?)
                False,
                # [48] Enable Background Music Remover Filter
                False,
                # [49] Model (UVR)
                "UVR-MDX-NET-Inst_HQ_4",
                # [50] Device (UVR)
                "cuda",
                # [51] Segment Size
                256,
                # [52] Save separated files to output
                False,
                # [53] Offload sub model when finished (UVR)
                False
            ]
            
            result = client.predict(
                *inputs,
                api_name="/transcribe_file"
            )
            
            logger.debug(f"Whisper-WebUI raw result type: {type(result)}")
            
            # Parse result based on Whisper-WebUI output format
            if isinstance(result, str):
                # Simple text output - parse as SRT or plain text
                text = result.strip()
                
                # Try to parse SRT format
                if "-->" in text:
                    segments = _parse_srt_to_segments(text)
                    return {
                        "text": " ".join(s["text"] for s in segments),
                        "segments": segments,
                        "language": "auto"
                    }
                else:
                    return {
                        "text": text,
                        "segments": [{"start": 0, "end": 0, "text": text}],
                        "language": "auto"
                    }
                    
            elif isinstance(result, tuple):
                # Multiple outputs (common in Gradio)
                # Usually: (transcription_text, srt_content, json_content, ...)
                for item in result:
                    if isinstance(item, str) and item.strip():
                        # Try JSON first
                        if item.strip().startswith("{") or item.strip().startswith("["):
                            try:
                                data = json.loads(item)
                                if isinstance(data, dict) and ("segments" in data or "text" in data):
                                    return data
                            except:
                                pass
                        # Then try SRT
                        if "-->" in item:
                            segments = _parse_srt_to_segments(item)
                            return {
                                "text": " ".join(s["text"] for s in segments),
                                "segments": segments,
                                "language": "auto"
                            }
                        # Otherwise plain text
                        return {
                            "text": item.strip(),
                            "segments": [{"start": 0, "end": 0, "text": item.strip()}],
                            "language": "auto"
                        }
                    # Check for file path result (Gradio returns file paths sometimes)
                    elif isinstance(item, str) and (item.endswith('.srt') or item.endswith('.txt') or item.endswith('.json')):
                        if os.path.exists(item):
                            try:
                                with open(item, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                if item.endswith('.json'):
                                    data = json.loads(content)
                                    if isinstance(data, dict):
                                        return data
                                elif item.endswith('.srt') and '-->' in content:
                                    segments = _parse_srt_to_segments(content)
                                    return {
                                        "text": " ".join(s["text"] for s in segments),
                                        "segments": segments,
                                        "language": "auto"
                                    }
                                else:
                                    return {
                                        "text": content.strip(),
                                        "segments": [{"start": 0, "end": 0, "text": content.strip()}],
                                        "language": "auto"
                                    }
                            except Exception as read_err:
                                logger.warning(f"Could not read result file {item}: {read_err}")
                        
            elif isinstance(result, dict):
                return result
            
            logger.warning(f"Unexpected result format from Whisper-WebUI: {type(result)}")
            if result:
                logger.debug(f"Result content: {str(result)[:500]}")
            return None
            
        except Exception as e:
            logger.warning(f"Whisper-WebUI /transcribe_file failed: {e}")
            # Try alternative API endpoint if exists
            try:
                # Some Whisper-WebUI versions have simpler API
                result = client.predict(
                    handle_file(file_path),
                    fn_index=0
                )
                if result:
                    if isinstance(result, str):
                        if "-->" in result:
                            segments = _parse_srt_to_segments(result)
                            return {
                                "text": " ".join(s["text"] for s in segments),
                                "segments": segments,
                                "language": "auto"
                            }
                        return {"text": result, "segments": [], "language": "auto"}
            except Exception as e2:
                logger.warning(f"Alternative Whisper-WebUI call also failed: {e2}")
            return None
        
    except ImportError:
        logger.debug("gradio_client not installed. Install with: pip install gradio_client")
        return None
    except Exception as e:
        logger.debug(f"Whisper-WebUI connection failed: {e}")
        return None


def _parse_srt_to_segments(srt_content: str) -> list:
    """Parse SRT subtitle format to segments list."""
    import re
    segments = []
    
    # SRT pattern: index\ntimestamp --> timestamp\ntext\n
    pattern = r'(\d+)\n(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})\n(.+?)(?=\n\n|\Z)'
    
    for match in re.finditer(pattern, srt_content, re.DOTALL):
        start_h, start_m, start_s, start_ms = int(match.group(2)), int(match.group(3)), int(match.group(4)), int(match.group(5))
        end_h, end_m, end_s, end_ms = int(match.group(6)), int(match.group(7)), int(match.group(8)), int(match.group(9))
        text = match.group(10).strip().replace('\n', ' ')
        
        start = start_h * 3600 + start_m * 60 + start_s + start_ms / 1000
        end = end_h * 3600 + end_m * 60 + end_s + end_ms / 1000
        
        segments.append({
            "start": start,
            "end": end,
            "text": text
        })
    
    return segments


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
    
    # GPU Support: Load NVIDIA DLLs if installed
    try:
        import nvidia.cudnn
        import nvidia.cublas
        import os
        import sys
        
        # Add DLL directories for Windows
        if sys.platform.startswith("win"):
            for lib in [nvidia.cudnn, nvidia.cublas]:
                paths = getattr(lib, "__path__", [])
                for p in paths:
                    possible_paths = [
                        p,
                        os.path.join(p, "bin"),
                        os.path.join(p, "lib")
                    ]
                    for pp in possible_paths:
                        if os.path.exists(pp):
                            logger.debug(f"Adding DLL path: {pp}")
                            os.add_dll_directory(pp)
                            os.environ["PATH"] = pp + os.pathsep + os.environ["PATH"]
            logger.info("Loaded NVIDIA cuDNN/cuBLAS DLL paths")
    except ImportError:
        logger.warning("NVIDIA libraries not found via pip, GPU might fail if system libs are missing")
    except Exception as e:
        logger.warning(f"Failed to load NVIDIA DLLs: {e}")

    model_size = config.get("model_size", "large-v3")
    
    # Check for zlibwapi.dll (critical for cuDNN on Windows)
    import ctypes
    target_device = "auto"
    try:
        if sys.platform.startswith("win"):
            ctypes.CDLL("zlibwapi.dll")
            logger.debug("Found zlibwapi.dll")
    except Exception as e:
        logger.warning(f"Could not load zlibwapi.dll ({e}). GPU acceleration requires this DLL on Windows.")
        logger.warning("Falling back to CPU using 'int8' to prevent runtime crash.")
        target_device = "cpu"

    try:
        logger.info(f"Loading faster-whisper model: {model_size} on {target_device}")
        # Use float16 for GPU to avoid cuBLAS errors with int8 on some cards
        compute_type = "float16" if target_device == "auto" else "int8"
        model = WhisperModel(model_size, device=target_device, compute_type=compute_type)
        
        logger.info(f"Transcribing with faster-whisper ({target_device} - {compute_type}): {file_path}")
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
    
    # Try transcription methods in order of priority
    result = None
    temp_fd, temp_path = tempfile.mkstemp(suffix=".json")
    os.close(temp_fd)
    
    try:
        # Method 0: Whisper-WebUI Server (fastest - model already in GPU memory)
        webui_url = config.get("whisper_webui_url")
        if webui_url:
            logger.info(f"Trying Method 0: Whisper-WebUI at {webui_url}")
            result = _transcribe_with_webui(file_path, config)
            if result:
                logger.info("Transcription completed via Whisper-WebUI")
        
        # Method 1: External script
        if result is None and config.get("whisper_script"):
            logger.info("Trying Method 1: External Whisper script")
            result = _transcribe_with_external_script(file_path, config, temp_path)
        
        # Method 2: faster-whisper (local)
        if result is None:
            logger.info("Trying Method 2: faster-whisper (local)")
            result = _transcribe_with_faster_whisper(file_path, config)
        
        # Method 3: openai-whisper (local)
        if result is None:
            logger.info("Trying Method 3: openai-whisper (local)")
            result = _transcribe_with_builtin_whisper(file_path, config)
        
        # No method worked
        if result is None:
            return {
                "error": "No transcription method available",
                "suggestions": [
                    "Start Whisper-WebUI: python app.py (runs at http://127.0.0.1:7860)",
                    "Install faster-whisper: pip install faster-whisper",
                    "Install openai-whisper: pip install openai-whisper", 
                    "Configure external script in config/whisper_config.json"
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
