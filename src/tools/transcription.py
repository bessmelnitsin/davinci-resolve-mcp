
"""
Transcription Tools for DaVinci Resolve MCP
"""
import os
import json
from typing import Dict, Any, Optional

from src.server_instance import mcp
from src.context import get_resolve
from src.api.whisper_node import transcribe_with_whisper_node
from src.api import transcription_operations

@mcp.tool()
def transcribe(
    file_path: str,
    language: str = "auto",
    output_format: str = "json"
) -> str:
    """
    Transcribe audio/video file using Whisper.
    
    Uses Whisper-WebUI server if available (fastest, model already in GPU),
    otherwise falls back to local whisper installation.
    
    Args:
        file_path: Absolute path to audio/video file
        language: Language code ('en', 'ru', 'auto' for detection)
        output_format: Output format ('json', 'srt', 'text')
    
    Returns:
        Transcription in requested format
    
    Example:
        transcribe("C:/videos/podcast.mp4", language="en", output_format="srt")
    """
    if not os.path.exists(file_path):
        return f"Error: File not found: {file_path}"
    
    # Get transcription
    result = transcribe_with_whisper_node(file_path)
    
    if "error" in result:
        return f"Transcription error: {result['error']}"
    
    # Format output based on requested format
    if output_format == "text":
        return result.get("text", "")
    
    elif output_format == "srt":
        # Generate SRT format
        srt_lines = []
        segments = result.get("segments", [])
        for i, seg in enumerate(segments, 1):
            start = seg.get("start", 0)
            end = seg.get("end", 0)
            text = seg.get("text", "").strip()
            
            # Format timestamps as HH:MM:SS,mmm
            def format_ts(seconds):
                h = int(seconds // 3600)
                m = int((seconds % 3600) // 60)
                s = int(seconds % 60)
                ms = int((seconds % 1) * 1000)
                return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
            
            srt_lines.append(f"{i}")
            srt_lines.append(f"{format_ts(start)} --> {format_ts(end)}")
            srt_lines.append(text)
            srt_lines.append("")
        
        return "\n".join(srt_lines)
    
    else:  # json
        return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
def transcribe_clip(
    clip_name: str,
    language: str = "auto",
    output_format: str = "json"
) -> str:
    """
    Transcribe a clip from DaVinci Resolve Media Pool.
    
    Args:
        clip_name: Name of the clip in Media Pool
        language: Language code ('en', 'ru', 'auto')
        output_format: Output format ('json', 'srt', 'text')
    
    Returns:
        Transcription in requested format
    """
    resolve = get_resolve()
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    from src.api.media_operations import get_all_media_pool_clips
    
    # Safely get project and media pool
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
        
    project = project_manager.GetCurrentProject()
    if not project:
        return "Error: No project open"
    
    media_pool = project.GetMediaPool()
    if not media_pool:
        return "Error: Failed to get Media Pool"

    clips = get_all_media_pool_clips(media_pool)
    target_clip = next((c for c in clips if c.GetName() == clip_name), None)
    
    if not target_clip:
        return f"Error: Clip '{clip_name}' not found in Media Pool"
    
    file_path = target_clip.GetClipProperty("File Path")
    if not file_path:
        return "Error: Could not determine file path"
    
    # Use the transcribe function
    return transcribe(file_path, language, output_format)


@mcp.resource("whisper://status")
def get_whisper_status() -> Dict[str, Any]:
    """
    Check Whisper-WebUI server status and configuration.
    
    Returns:
        Dictionary with server status, URL, and available methods
    """
    import requests
    
    # Try to get config from transcription_operations or whisper_node
    config = {}
    if hasattr(transcription_operations, 'get_whisper_config'):
        config = transcription_operations.get_whisper_config()
    else:
        from src.api.whisper_node import get_whisper_config as get_config
        config = get_config()
    
    webui_url = config.get("whisper_webui_url", "http://127.0.0.1:7860")
    
    # Check WebUI status
    webui_available = False
    try:
        response = requests.get(webui_url, timeout=2)
        webui_available = response.status_code == 200
    except:
        pass
    
    # Check local whisper
    local_whisper = False
    try:
        from faster_whisper import WhisperModel
        local_whisper = True
    except ImportError:
        try:
            import whisper
            local_whisper = True
        except ImportError:
            pass
    
    return {
        "whisper_webui": {
            "url": webui_url,
            "available": webui_available,
            "priority": 0 if webui_available else -1
        },
        "local_whisper": {
            "available": local_whisper,
            "priority": 1 if local_whisper else -1
        },
        "recommended": "whisper_webui" if webui_available else ("local" if local_whisper else "none"),
        "config": {
            "model_size": config.get("model_size", "large-v3"),
            "cache_enabled": config.get("cache_transcriptions", True)
        }
    }

@mcp.tool()
def transcribe_clip_to_cache(clip_name: str, model_size: str = "large-v3", force_retranscribe: bool = False) -> str:
    """Run Whisper transcription and save result to a .json file next to the media.
    
    Args:
        clip_name: Name of the clip to transcribe
        model_size: Whisper model size
        force_retranscribe: If True, ignore existing cache
    """
    resolve = get_resolve()
    return transcription_operations.transcribe_clip_to_cache(resolve, clip_name, model_size, force_retranscribe)


@mcp.tool()
def get_cached_transcription(clip_name: str) -> str:
    """Read transcription from cache without running Whisper.
    
    Args:
        clip_name: Name of the clip in Media Pool
    """
    resolve = get_resolve()
    return transcription_operations.get_cached_transcription(resolve, clip_name)

@mcp.tool()
def get_clip_transcription(clip_name: str, model_size: str = "large-v3") -> str:
    """Helper that transcribes OR loads from cache and returns text.
    """
    resolve = get_resolve()
    return transcription_operations.get_clip_transcription(resolve, clip_name, model_size)

@mcp.tool()
def transcribe_folder_tool(folder_name: str) -> Dict[str, Any]:
    """Transcribe all audio clips in a specific Media Pool folder using Native AI.
    
    Args:
        folder_name: Name of the folder to transcribe
    """
    from src.api.audio_operations import transcribe_folder as transcribe_func
    resolve = get_resolve()
    return transcribe_func(resolve, folder_name)

@mcp.tool()
def transcribe_clip_tool(clip_name: str, model_size: str = "base") -> Dict[str, Any]:
    """Transcribe audio from a specific clip using Whisper.
    
    Args:
        clip_name: Name of the clip to transcribe
        model_size: Whisper model size (tiny, base, small, medium, large)
    """
    from src.api.audio_operations import transcribe_clip as transcribe_func
    resolve = get_resolve()
    return transcribe_func(resolve, clip_name, model_size)
